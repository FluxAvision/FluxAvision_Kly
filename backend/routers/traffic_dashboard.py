"""
GET /api/traffic/dashboard - 获取仪表盘聚合数据

数据层次:
  门店汇总 (storeTotal): 所有设备的客流求和 → 这是门店级数据
  设备明细 (devicesToday): 每个设备各自的今日客流 → 展示各摄像头贡献
"""
from fastapi import APIRouter
from datetime import datetime, timedelta
from collections import defaultdict
from database import get_session_factory
from models import TrafficRecord, Device, SystemSettings
from utils import success_response, models_to_list

router = APIRouter(prefix="/api/traffic/dashboard", tags=["客流数据"])


@router.get("")
async def get_dashboard_data():
    """
    获取仪表盘聚合数据

    返回结构:
      storeTotal: 门店级汇总数据 (所有设备求和)
      devicesToday: 各设备今日客流明细 (每个摄像头的独立数据)
      hourlyToday: 门店今日逐时趋势 (所有设备求和)
      peakHour: 今日客流高峰时段
      devices: 设备列表 (含状态)
      storeName: 门店名称
    """
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    # 计算时间范围
    day_of_week = today.weekday()
    monday = today - timedelta(days=day_of_week)
    monday_str = monday.strftime("%Y-%m-%d")
    first_day_of_month = today.replace(day=1)
    first_day_str = first_day_of_month.strftime("%Y-%m-%d")
    first_day_of_year = today.replace(month=1, day=1)
    first_day_of_year_str = first_day_of_year.strftime("%Y-%m-%d")

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        # 门店名称
        settings = session.query(SystemSettings).first()
        store_name = settings.storeName if settings else "我的门店"
        store_max_capacity = settings.storeMaxCapacity if settings and settings.storeMaxCapacity else 0
        instantaneous_max_capacity = (
            settings.instantaneousMaxCapacity if settings and settings.instantaneousMaxCapacity else 0
        )

        # ==================== 门店汇总 (所有设备求和) ====================

        # 今日汇总 (仅设备级记录, 不含旧版 deviceId=null 汇总记录)
        today_records = session.query(TrafficRecord).filter(
            TrafficRecord.date == today_str,
            TrafficRecord.deviceId.isnot(None),
        ).all()
        today_in = sum(r.countIn for r in today_records)
        today_out = sum(r.countOut for r in today_records)
        current_in = max(0, today_in - today_out)

        # 本周汇总
        week_records = session.query(TrafficRecord).filter(
            TrafficRecord.date >= monday_str,
            TrafficRecord.date <= today_str,
            TrafficRecord.deviceId.isnot(None),
        ).all()
        week_in = sum(r.countIn for r in week_records)
        week_out = sum(r.countOut for r in week_records)

        # 本月汇总
        month_records = session.query(TrafficRecord).filter(
            TrafficRecord.date >= first_day_str,
            TrafficRecord.date <= today_str,
            TrafficRecord.deviceId.isnot(None),
        ).all()
        month_in = sum(r.countIn for r in month_records)
        month_out = sum(r.countOut for r in month_records)

        # 本年汇总
        year_records = session.query(TrafficRecord).filter(
            TrafficRecord.date >= first_day_of_year_str,
            TrafficRecord.date <= today_str,
            TrafficRecord.deviceId.isnot(None),
        ).all()
        year_in = sum(r.countIn for r in year_records)
        year_out = sum(r.countOut for r in year_records)

        # 全部汇总
        all_records = session.query(TrafficRecord).filter(
            TrafficRecord.deviceId.isnot(None),
        ).all()
        total_in = sum(r.countIn for r in all_records)
        total_out = sum(r.countOut for r in all_records)
        available_capacity = max(0, store_max_capacity - current_in)

        # ==================== 门店今日逐时趋势 (所有设备求和) ====================
        # 初始化完整的24小时数据，没有数据的小时用0补全
        hourly_today = [{"hour": h, "countIn": 0, "countOut": 0} for h in range(24)]
        for r in today_records:
            if 0 <= r.hour < 24:
                hourly_today[r.hour]["countIn"] += r.countIn
                hourly_today[r.hour]["countOut"] += r.countOut

        # 今日高峰时段
        peak_hour_entry = max(hourly_today, key=lambda x: x["countIn"])
        peak_hour = peak_hour_entry["hour"] if peak_hour_entry["countIn"] > 0 else None

        # ==================== 各设备今日客流明细 ====================
        devices = session.query(Device).order_by(Device.createdAt.desc()).all()
        device_id_set = {d.id for d in devices}

        # 按设备分组今日数据
        device_records = defaultdict(list)
        for r in today_records:
            if r.deviceId in device_id_set:
                device_records[r.deviceId].append(r)

        devices_today = []
        for device in devices:
            recs = device_records.get(device.id, [])
            d_in = sum(r.countIn for r in recs)
            d_out = sum(r.countOut for r in recs)
            d_inside = max(0, d_in - d_out)
            devices_today.append({
                "deviceId": device.id,
                "deviceName": device.name,
                "deviceIp": device.ip,
                "deviceLocation": device.location,
                "deviceStatus": device.status,
                "todayIn": d_in,
                "todayOut": d_out,
                "currentInside": d_inside,
                "percentage": round(d_in / today_in * 100, 1) if today_in > 0 else 0,
            })

        return success_response({
            # 门店级汇总
            "storeName": store_name,
            "storeTotal": {
                "todayIn": today_in,
                "todayOut": today_out,
                "currentIn": current_in,
                "weekIn": week_in,
                "weekOut": week_out,
                "monthIn": month_in,
                "monthOut": month_out,
                "yearIn": year_in,
                "yearOut": year_out,
                "totalIn": total_in,
                "totalOut": total_out,
                "instantaneousMaxCapacity": instantaneous_max_capacity,
                "storeMaxCapacity": store_max_capacity,
                "availableCapacity": available_capacity,
            },
            # 各设备今日明细
            "devicesToday": devices_today,
            # 逐时趋势 (门店汇总)
            "hourlyToday": hourly_today,
            # 高峰时段
            "peakHour": peak_hour,
            # 设备列表
            "devices": models_to_list(devices),
        })
