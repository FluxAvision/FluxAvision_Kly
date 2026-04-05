"""
GET /api/traffic/history - 查询历史客流数据

数据层次:
  默认 (无 deviceId): 门店汇总 (所有设备求和)
  按 deviceId 筛选: 单设备客流数据
"""
from fastapi import APIRouter, Request
import re
from collections import defaultdict
from database import get_session_factory
from models import TrafficRecord, Device
from utils import success_response, error_response, models_to_list

router = APIRouter(prefix="/api/traffic/history", tags=["客流数据"])


@router.get("")
async def get_history_data(request: Request):
    """
    查询历史客流数据

    参数:
      startDate: 开始日期 (YYYY-MM-DD, 必填)
      endDate:   结束日期 (YYYY-MM-DD, 必填)
      deviceId:  设备ID (可选, 不传=门店汇总, 传=单设备)
    """
    start_date = request.query_params.get("startDate")
    end_date = request.query_params.get("endDate")
    device_id = request.query_params.get("deviceId")

    if not start_date or not end_date:
        return error_response("缺少查询参数: startDate, endDate", 400)

    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_regex.match(start_date) or not date_regex.match(end_date):
        return error_response("日期格式不正确, 请使用 YYYY-MM-DD 格式", 400)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        query = session.query(TrafficRecord).filter(
            TrafficRecord.date >= start_date,
            TrafficRecord.date <= end_date,
        )

        if device_id:
            # 单设备查询: 只看该设备的数据
            query = query.filter_by(deviceId=device_id)
        else:
            # 门店汇总: 仅查设备级记录 (排除旧版 deviceId=null 的汇总记录)
            query = query.filter(TrafficRecord.deviceId.isnot(None))

        records = query.order_by(TrafficRecord.date, TrafficRecord.hour).all()

        # ==================== 按日聚合 ====================
        daily_map = defaultdict(lambda: {"date": "", "countIn": 0, "countOut": 0})
        for record in records:
            daily_map[record.date]["date"] = record.date
            daily_map[record.date]["countIn"] += record.countIn
            daily_map[record.date]["countOut"] += record.countOut

        daily_data = sorted(daily_map.values(), key=lambda x: x["date"])

        # ==================== 单天时: 按小时 + 按设备分栏 ====================
        hourly_data = None
        daily_device_data = None  # 单天的各设备分栏明细

        if start_date == end_date:
            # 按小时聚合
            hourly_map = {h: {"hour": h, "countIn": 0, "countOut": 0} for h in range(24)}
            for record in records:
                if record.hour in hourly_map:
                    hourly_map[record.hour]["countIn"] += record.countIn
                    hourly_map[record.hour]["countOut"] += record.countOut
            hourly_data = sorted(hourly_map.values(), key=lambda x: x["hour"])

            # 门店汇总模式下, 额外返回各设备的当日分栏明细
            if not device_id:
                devices = session.query(Device).order_by(Device.createdAt.desc()).all()
                device_daily = []
                day_total_in = sum(d["countIn"] for d in daily_data)

                for dev in devices:
                    dev_records = [r for r in records if r.deviceId == dev.id]
                    dev_in = sum(r.countIn for r in dev_records)
                    dev_out = sum(r.countOut for r in dev_records)
                    if dev_in > 0 or dev_out > 0:
                        device_daily.append({
                            "deviceId": dev.id,
                            "deviceName": dev.name,
                            "deviceLocation": dev.location,
                            "deviceStatus": dev.status,
                            "deviceIp": dev.ip,
                            "countIn": dev_in,
                            "countOut": dev_out,
                            "currentInside": max(0, dev_in - dev_out),
                            "percentage": round(dev_in / day_total_in * 100, 1) if day_total_in > 0 else 0,
                        })
                daily_device_data = device_daily

        # ==================== 日期范围内: 返回每日各设备对比 ====================
        daily_device_comparison = None
        if not device_id and start_date != end_date:
            # 查该日期范围内的所有设备
            devices = session.query(Device).order_by(Device.createdAt.desc()).all()
            device_ids = {d.id for d in devices}

            # 按日期+设备聚合
            dd_map = defaultdict(lambda: {"date": "", "deviceId": "", "deviceName": "", "countIn": 0, "countOut": 0})
            for record in records:
                if record.deviceId in device_ids:
                    key = (record.date, record.deviceId)
                    dd_map[key]["date"] = record.date
                    dd_map[key]["deviceId"] = record.deviceId
                    dd_map[key]["countIn"] += record.countIn
                    dd_map[key]["countOut"] += record.countOut

            # 补充设备名称
            dev_name_map = {d.id: d.name for d in devices}
            for key, val in dd_map.items():
                val["deviceName"] = dev_name_map.get(val["deviceId"], "未知设备")

            # 按日期分组
            date_device_map = defaultdict(list)
            for val in dd_map.values():
                date_device_map[val["date"]].append(val)

            daily_device_comparison = dict(sorted(date_device_map.items()))

        return success_response({
            "daily": daily_data,
            "hourly": hourly_data,
            "dailyDeviceData": daily_device_data,          # 单天: 各设备分栏明细
            "dailyDeviceComparison": daily_device_comparison,  # 多天: 每天各设备对比
            "startDate": start_date,
            "endDate": end_date,
            "deviceId": device_id or None,
        })
