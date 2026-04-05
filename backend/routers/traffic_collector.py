"""
客流采集管理 API

注意: 设备添加后已自动启动采集, 以下接口仅用于手动控制或调试。

GET  /api/traffic-collector/status   - 获取采集器状态 (含各设备详情)
GET  /api/traffic-collector/realtime - 获取实时客流数据
POST /api/traffic-collector/start    - 手动启动采集 (通常不需要)
POST /api/traffic-collector/stop     - 手动停止采集
POST /api/traffic-collector/restart  - 重启采集 (连接参数变更后)
"""
from fastapi import APIRouter, Request
from typing import Optional

router = APIRouter(prefix="/api/traffic-collector", tags=["客流采集"])


@router.get("/status")
async def get_collector_status():
    """
    获取客流采集器全局状态和所有设备的采集详情

    返回:
      {
        "sdkAvailable": true/false,
        "deviceCount": 2,
        "devices": [
          {
            "deviceId": "...",
            "state": "connected|connecting|reconnecting|disconnected|stopped",
            "reconnectAttempts": 0,
            "lastError": "",
            "lastConnectedAt": "...",
            "lastStatTime": "...",
            "enteredToday": 10,
            "exitedToday": 5,
            "insideNow": 3,
          }
        ]
      }
    """
    from dahua_collector import dahua_collector
    from utils import success_response

    devices = dahua_collector.get_all_realtime_data()

    # 附加详细的采集器状态
    for dev in devices:
        state_info = dahua_collector.get_device_collector_state(dev["deviceId"])
        dev.update({
            "state": state_info.get("state", "unknown"),
            "reconnectAttempts": state_info.get("reconnectAttempts", 0),
            "lastError": state_info.get("lastError", ""),
            "lastConnectedAt": state_info.get("lastConnectedAt"),
            "lastStatTime": state_info.get("lastStatTime"),
        })

    return success_response({
        "sdkAvailable": dahua_collector.available,
        "deviceCount": len(devices),
        "devices": devices,
    })


@router.get("/realtime")
async def get_realtime_data(deviceId: str = ""):
    """
    获取实时客流数据

    参数:
      deviceId: 设备ID (可选, 不传则返回所有设备)

    返回:
      [{
        "deviceId": "...",
        "enteredToday": 10,
        "exitedToday": 5,
        "insideNow": 3,
        "lastUpdate": "2026-04-05T10:30:00",
        "collecting": true,
        "state": "connected",
      }]
    """
    from dahua_collector import dahua_collector
    from utils import success_response

    if deviceId:
        data = dahua_collector.get_realtime_data(deviceId)
        return success_response(data)
    else:
        data = dahua_collector.get_all_realtime_data()
        return success_response(data)


@router.post("/start")
async def start_collector(request: Request):
    """
    手动启动指定设备的客流采集

    通常不需要手动调用 — 设备添加后会自动启动。
    此接口用于:
      1. 之前手动停止后重新启动
      2. SDK修复后重新启用
      3. 调试用途
    """
    from dahua_collector import dahua_collector
    from utils import success_response, error_response

    body = await request.json()
    device_id = body.get("deviceId", "")
    ip = body.get("ip", "")
    port = int(body.get("port", 37777))
    username = body.get("username", "admin")
    password = body.get("password", "")
    channel = int(body.get("channel", 0))

    if not device_id or not ip:
        return error_response("设备ID和IP地址不能为空")

    if not dahua_collector.available:
        return error_response(
            "大华NetSDK未安装或不支持当前平台. "
            "请确保在Windows环境下运行, 并安装NetSDK"
        )

    success = dahua_collector.start(
        device_id=device_id,
        ip=ip,
        port=port,
        username=username,
        password=password,
        channel=channel,
    )

    if success:
        return success_response({
            "deviceId": device_id,
            "message": f"客流采集已启动: {ip}:{port} 通道={channel}",
        })
    else:
        return error_response(f"启动客流采集失败: {ip}:{port}")


@router.post("/stop")
async def stop_collector(request: Request):
    """
    手动停止指定设备的客流采集

    注意: 设备添加后默认自动采集, 调用此接口会停止采集。
    删除设备时也会自动停止采集。
    """
    from dahua_collector import dahua_collector
    from utils import success_response, error_response

    body = await request.json()
    device_id = body.get("deviceId", "")

    if not device_id:
        return error_response("设备ID不能为空")

    success = dahua_collector.stop(device_id)
    return success_response({
        "deviceId": device_id,
        "message": "客流采集已停止",
    })


@router.post("/restart")
async def restart_collector(request: Request):
    """
    重启指定设备的客流采集

    使用设备当前的连接参数重新连接, 用于:
      1. 采集异常后强制重连
      2. 网络恢复后重新建立连接
    """
    from dahua_collector import dahua_collector
    from utils import success_response, error_response

    body = await request.json()
    device_id = body.get("deviceId", "")

    if not device_id:
        return error_response("设备ID不能为空")

    success = dahua_collector.restart_device(device_id)
    if success:
        return success_response({
            "deviceId": device_id,
            "message": "客流采集已重启",
        })
    else:
        return error_response("重启失败 (设备未在采集中或SDK不可用)")
