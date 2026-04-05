"""
GET /api/devices - 获取所有设备列表
POST /api/devices - 创建新设备 (自动启动客流采集)
"""
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_session_factory
from models import Device
from utils import (
    success_response, error_response, model_to_dict, models_to_list,
    generate_rtsp_url,
)

router = APIRouter(prefix="/api/devices", tags=["设备管理"])


@router.get("")
async def list_devices():
    """获取所有设备列表 (含采集状态)"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        devices = session.query(Device).order_by(Device.createdAt.desc()).all()
        device_list = models_to_list(devices)

    # 附加采集器状态信息
    try:
        from dahua_collector import dahua_collector
        for dev in device_list:
            state_info = dahua_collector.get_device_collector_state(dev["id"])
            dev["collectorState"] = state_info.get("state", "not_started")
    except Exception:
        pass

    return success_response(device_list)


@router.post("")
async def create_device(request: Request):
    """
    创建新设备 (大华设备自动启动客流采集)

    对于大华设备, 创建后立即在后台启动SDK连接和客流订阅,
    无需手动触发。如果连接失败, 会自动重连。
    """
    body = await request.json()
    name = body.get("name")
    ip = body.get("ip")
    serial_number = body.get("serialNumber")
    location = body.get("location")
    model = body.get("model", "大华")
    rtsp_port = body.get("rtspPort", 554)
    sdk_port = body.get("sdkPort", 37777)
    channel = body.get("channel", 0)
    username = body.get("username", "admin")
    password = body.get("password", "")
    max_channels = body.get("maxChannels", 4)

    if not name or not ip or not serial_number or not location:
        return error_response("缺少必填字段: name, ip, serialNumber, location", 400)

    rtsp_url = generate_rtsp_url(model, ip, rtsp_port, username, password)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = Device(
            name=name, ip=ip, serialNumber=serial_number, location=location,
            model=model, rtspPort=rtsp_port, sdkPort=sdk_port, channel=channel,
            username=username, password=password,
            rtspUrl=rtsp_url, maxChannels=max_channels,
        )
        session.add(device)
        try:
            session.commit()
            session.refresh(device)
        except IntegrityError:
            session.rollback()
            return error_response("设备序列号已存在", 409)

    # 大华设备自动启动客流采集
    collector_started = False
    collector_message = ""
    if model == "大华":
        try:
            from dahua_collector import dahua_collector
            collector_started = dahua_collector.start(
                device_id=device.id,
                ip=ip,
                port=sdk_port,
                username=username,
                password=password,
                channel=channel,
            )
            collector_message = "客流采集已自动启动" if collector_started else "SDK不可用"
        except Exception as e:
            collector_message = f"启动采集失败: {str(e)}"

    result = model_to_dict(device)
    result["collectorStarted"] = collector_started
    result["collectorMessage"] = collector_message

    return success_response(result, status_code=201)
