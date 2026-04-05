"""
GET /api/devices/{id} - 获取单个设备
PUT /api/devices/{id} - 更新设备 (凭证变更自动重连)
DELETE /api/devices/{id} - 删除设备 (自动停止采集)
"""
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_session_factory
from models import Device, TrafficRecord
from utils import (
    success_response, error_response, model_to_dict,
    generate_rtsp_url,
)

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


@router.get("/{device_id}")
async def get_device(device_id: str):
    """获取单个设备详情"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = session.query(Device).filter_by(id=device_id).first()
        if not device:
            return error_response("设备不存在", 404)
        result = model_to_dict(device)

    # 附加采集器状态
    try:
        from dahua_collector import dahua_collector
        state_info = dahua_collector.get_device_collector_state(device_id)
        result["collectorState"] = state_info.get("state", "not_started")
    except Exception:
        pass

    return success_response(result)


@router.put("/{device_id}")
async def update_device(device_id: str, request: Request):
    """
    更新设备

    如果大华设备的连接参数 (IP/端口/用户名/密码/通道) 发生变更,
    会自动停止旧连接并用新参数重新连接。
    """
    body = await request.json()

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = session.query(Device).filter_by(id=device_id).first()
        if not device:
            return error_response("设备不存在", 404)

        # 检查是否需要重新生成RTSP地址
        needs_rtsp = any([
            body.get("model") and body["model"] != device.model,
            body.get("ip") and body["ip"] != device.ip,
            body.get("rtspPort") and body["rtspPort"] != device.rtspPort,
            body.get("username") and body["username"] != device.username,
            "password" in body and body["password"] != device.password,
        ])

        # 检查是否需要重新连接SDK (大华设备连接参数变更)
        needs_reconnect = device.model == "大华" and any([
            body.get("ip") and body["ip"] != device.ip,
            body.get("sdkPort") and body["sdkPort"] != device.sdkPort,
            body.get("username") and body["username"] != device.username,
            "password" in body and body["password"] != device.password,
            body.get("channel") is not None and body["channel"] != device.channel,
        ])

        # 更新字段
        update_fields = [
            "name", "ip", "serialNumber", "location", "model",
            "rtspPort", "sdkPort", "channel", "username", "password", "maxChannels",
        ]
        for field in update_fields:
            if field in body:
                setattr(device, field, body[field])

        # 重新生成RTSP地址
        if needs_rtsp:
            device.rtspUrl = generate_rtsp_url(
                device.model, device.ip, device.rtspPort,
                device.username, device.password,
            )

        try:
            session.commit()
            session.refresh(device)
        except IntegrityError:
            session.rollback()
            return error_response("设备序列号已存在", 409)

        result = model_to_dict(device)

    # 大华设备连接参数变更, 自动重连
    reconnect_msg = ""
    if needs_reconnect:
        try:
            from dahua_collector import dahua_collector
            success = dahua_collector.restart_device(device_id)
            reconnect_msg = "SDK已自动重连" if success else "SDK重连失败"
        except Exception as e:
            reconnect_msg = f"SDK重连失败: {str(e)}"

    if reconnect_msg:
        result["reconnectMessage"] = reconnect_msg

    return success_response(result)


@router.delete("/{device_id}")
async def delete_device(device_id: str):
    """
    删除设备

    自动停止该设备的客流采集, 清理所有SDK资源
    """
    # 先停止客流采集
    try:
        from dahua_collector import dahua_collector
        dahua_collector.stop(device_id)
    except Exception:
        pass

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = session.query(Device).filter_by(id=device_id).first()
        if not device:
            return error_response("设备不存在", 404)

        # 删除关联的客流记录
        session.query(TrafficRecord).filter_by(deviceId=device_id).delete()
        session.delete(device)
        session.commit()

    return success_response(message="设备已删除, 采集已停止")
