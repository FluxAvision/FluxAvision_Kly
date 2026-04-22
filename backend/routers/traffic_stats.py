"""
客流统计 API

提供以下统计数据查询：
1. 累计客流统计
2. 小时客流统计（含去重）
3. 每日客流统计（含去重）
4. 实时客流数据
"""
from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from collections import defaultdict
import re

router = APIRouter(prefix="/api/traffic/stats", tags=["客流统计"])


@router.get("/cumulative")
async def get_cumulative_stats(request: Request):
    """
    获取累计客流统计

    参数:
      deviceId: 设备ID (可选, 不传则返回所有设备)

    返回:
      [{
        "deviceId": "...",
        "totalIn": 10000,
        "totalOut": 9500,
        "currentInside": 500,
        "lastResetAt": "...",
        "updatedAt": "..."
      }]
    """
    from database import get_session_factory
    from models import TrafficCumulative, Device
    from utils import success_response

    device_id = request.query_params.get("deviceId")

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        query = session.query(TrafficCumulative)
        if device_id:
            query = query.filter_by(deviceId=device_id)

        cumulative_records = query.all()

        # 获取设备名称
        device_ids = [r.deviceId for r in cumulative_records]
        devices = session.query(Device).filter(Device.id.in_(device_ids)).all()
        device_name_map = {d.id: d.name for d in devices}

        result = []
        for record in cumulative_records:
            result.append({
                "deviceId": record.deviceId,
                "deviceName": device_name_map.get(record.deviceId, "未知设备"),
                "totalIn": record.totalIn or 0,
                "totalOut": record.totalOut or 0,
                "currentInside": record.currentInside or 0,
                "lastResetAt": record.lastResetAt.isoformat() if record.lastResetAt else None,
                "updatedAt": record.updatedAt.isoformat() if record.updatedAt else None,
            })

        return success_response(result)


@router.get("/hourly")
async def get_hourly_stats(request: Request):
    """
    获取小时客流统计（含去重）

    参数:
      deviceId: 设备ID (可选, 不传则返回门店汇总)
      date: 日期 YYYY-MM-DD (默认今天)
      startHour: 开始小时 0-23 (可选)
      endHour: 结束小时 0-23 (可选)

    返回:
      [{
        "hour": 10,
        "countIn": 50,
        "countOut": 45,
        "countInUnique": 42,
        "countOutUnique": 38,
        "insideCount": 5
      }]
    """
    from database import get_session_factory
    from models import TrafficHourly, Device
    from utils import success_response, error_response

    device_id = request.query_params.get("deviceId")
    date_str = request.query_params.get("date", datetime.now().strftime("%Y-%m-%d"))
    start_hour = request.query_params.get("startHour")
    end_hour = request.query_params.get("endHour")

    # 验证日期格式
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_regex.match(date_str):
        return error_response("日期格式不正确, 请使用 YYYY-MM-DD 格式", 400)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        query = session.query(TrafficHourly).filter_by(date=date_str)

        if device_id:
            query = query.filter_by(deviceId=device_id)
        else:
            # 门店汇总：获取所有设备
            devices = session.query(Device).all()
            device_ids = [d.id for d in devices]
            query = query.filter(TrafficHourly.deviceId.in_(device_ids))

        if start_hour is not None:
            query = query.filter(TrafficHourly.hour >= int(start_hour))
        if end_hour is not None:
            query = query.filter(TrafficHourly.hour <= int(end_hour))

        records = query.order_by(TrafficHourly.hour).all()

        # 按小时聚合
        hourly_map = {h: {
            "hour": h,
            "countIn": 0,
            "countOut": 0,
            "countInUnique": 0,
            "countOutUnique": 0,
            "insideCount": 0,
        } for h in range(24)}

        for record in records:
            h = record.hour
            hourly_map[h]["countIn"] += record.countIn or 0
            hourly_map[h]["countOut"] += record.countOut or 0
            hourly_map[h]["countInUnique"] += record.countInUnique or 0
            hourly_map[h]["countOutUnique"] += record.countOutUnique or 0
            # 在场人数取最大值
            hourly_map[h]["insideCount"] = max(hourly_map[h]["insideCount"], record.insideCount or 0)

        result = [hourly_map[h] for h in sorted(hourly_map.keys())]

        return success_response({
            "date": date_str,
            "hourly": result,
        })


@router.get("/daily")
async def get_daily_stats(request: Request):
    """
    获取每日客流统计（含去重）

    参数:
      deviceId: 设备ID (可选, 不传则返回门店汇总)
      startDate: 开始日期 YYYY-MM-DD (必填)
      endDate: 结束日期 YYYY-MM-DD (必填)

    返回:
      [{
        "date": "2024-01-15",
        "countIn": 500,
        "countOut": 480,
        "countInUnique": 420,
        "countOutUnique": 400,
        "insideMax": 50,
        "insideMin": 5
      }]
    """
    from database import get_session_factory
    from models import TrafficDaily, Device
    from utils import success_response, error_response

    device_id = request.query_params.get("deviceId")
    start_date = request.query_params.get("startDate")
    end_date = request.query_params.get("endDate")

    if not start_date or not end_date:
        return error_response("缺少查询参数: startDate, endDate", 400)

    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_regex.match(start_date) or not date_regex.match(end_date):
        return error_response("日期格式不正确, 请使用 YYYY-MM-DD 格式", 400)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        query = session.query(TrafficDaily).filter(
            TrafficDaily.date >= start_date,
            TrafficDaily.date <= end_date,
        )

        if device_id:
            query = query.filter_by(deviceId=device_id)
        else:
            # 门店汇总
            devices = session.query(Device).all()
            device_ids = [d.id for d in devices]
            query = query.filter(TrafficDaily.deviceId.in_(device_ids))

        records = query.order_by(TrafficDaily.date).all()

        # 按日期聚合
        daily_map = defaultdict(lambda: {
            "countIn": 0,
            "countOut": 0,
            "countInUnique": 0,
            "countOutUnique": 0,
            "insideMax": 0,
            "insideMin": float('inf'),
        })

        for record in records:
            d = record.date
            daily_map[d]["date"] = d
            daily_map[d]["countIn"] += record.countIn or 0
            daily_map[d]["countOut"] += record.countOut or 0
            daily_map[d]["countInUnique"] += record.countInUnique or 0
            daily_map[d]["countOutUnique"] += record.countOutUnique or 0
            daily_map[d]["insideMax"] = max(daily_map[d]["insideMax"], record.insideMax or 0)
            if record.insideMin and record.insideMin > 0:
                daily_map[d]["insideMin"] = min(daily_map[d]["insideMin"], record.insideMin)

        result = []
        for d in sorted(daily_map.keys()):
            data = daily_map[d]
            if data["insideMin"] == float('inf'):
                data["insideMin"] = 0
            result.append(data)

        return success_response({
            "startDate": start_date,
            "endDate": end_date,
            "daily": result,
        })


@router.get("/realtime")
async def get_realtime_stats(request: Request):
    """
    获取实时客流数据

    参数:
      deviceId: 设备ID (可选, 不传则返回所有设备)

    返回:
      [{
        "deviceId": "...",
        "deviceName": "...",
        "enteredToday": 100,
        "exitedToday": 90,
        "insideNow": 10,
        "lastUpdate": "...",
        "collecting": true,
        "state": "connected"
      }]
    """
    from dahua_collector import dahua_collector
    from database import get_session_factory
    from models import Device
    from utils import success_response

    device_id = request.query_params.get("deviceId")

    if device_id:
        data = dahua_collector.get_realtime_data(device_id)
        devices_data = [data]
    else:
        devices_data = dahua_collector.get_all_realtime_data()

    # 补充设备名称
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device_ids = [d["deviceId"] for d in devices_data if d.get("deviceId")]
        devices = session.query(Device).filter(Device.id.in_(device_ids)).all()
        device_name_map = {d.id: d.name for d in devices}

    for d in devices_data:
        d["deviceName"] = device_name_map.get(d.get("deviceId"), "未知设备")

    return success_response(devices_data)


@router.post("/reset-cumulative")
async def reset_cumulative_stats(request: Request):
    """
    重置累计客流统计

    参数:
      deviceId: 设备ID (必填)

    说明:
      将该设备的累计客流数据重置为0，并记录重置时间。
      通常在门店重新开业、统计周期重置时使用。
    """
    from database import get_session_factory
    from models import TrafficCumulative
    from utils import success_response, error_response

    body = await request.json()
    device_id = body.get("deviceId")

    if not device_id:
        return error_response("设备ID不能为空")

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        cumulative = session.query(TrafficCumulative).filter_by(deviceId=device_id).first()

        if cumulative:
            cumulative.totalIn = 0
            cumulative.totalOut = 0
            cumulative.currentInside = 0
            cumulative.lastResetAt = datetime.utcnow()
            session.commit()
            return success_response({
                "deviceId": device_id,
                "message": "累计客流统计已重置",
                "resetAt": cumulative.lastResetAt.isoformat(),
            })
        else:
            return error_response("未找到该设备的累计统计数据")
