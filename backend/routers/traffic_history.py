"""
GET /api/traffic/history - 查询历史客流数据

数据层次:
  默认 (无 deviceId): 门店汇总 (所有设备求和)
  按 deviceId 筛选: 单设备客流数据

维度 (dimension):
  hour:  按小时聚合 (仅单天)
  day:   按天聚合 (默认)
  week:  按周聚合
  month: 按月聚合
  year:  按年聚合
"""
from fastapi import APIRouter, Request
import re
from datetime import datetime, timedelta
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
      dimension: 聚合维度 (hour|day|week|month|year, 默认day)
    """
    start_date = request.query_params.get("startDate")
    end_date = request.query_params.get("endDate")
    device_id = request.query_params.get("deviceId")
    dimension = request.query_params.get("dimension", "day")

    if not start_date or not end_date:
        return error_response("缺少查询参数: startDate, endDate", 400)

    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_regex.match(start_date) or not date_regex.match(end_date):
        return error_response("日期格式不正确, 请使用 YYYY-MM-DD 格式", 400)

    if dimension not in ("hour", "day", "week", "month", "year"):
        return error_response(f"不支持的维度: {dimension}", 400)

    # hour 维度仅支持单天
    if dimension == "hour" and start_date != end_date:
        return error_response("按小时查询仅支持选择单一天", 400)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        query = session.query(TrafficRecord).filter(
            TrafficRecord.date >= start_date,
            TrafficRecord.date <= end_date,
        )

        if device_id:
            query = query.filter_by(deviceId=device_id)
        else:
            query = query.filter(TrafficRecord.deviceId.isnot(None))

        records = query.order_by(TrafficRecord.date, TrafficRecord.hour).all()

        # ==================== 按维度聚合 ====================
        if dimension == "hour":
            result = _aggregate_hourly(records, start_date)
        elif dimension == "day":
            result = _aggregate_daily(records, start_date, end_date)
        elif dimension == "week":
            result = _aggregate_weekly(records, start_date, end_date)
        elif dimension == "month":
            result = _aggregate_monthly(records, start_date, end_date)
        elif dimension == "year":
            result = _aggregate_yearly(records, start_date, end_date)
        else:
            result = []

        # ==================== 单天时: 各设备分栏明细 ====================
        daily_device_data = None
        if start_date == end_date and not device_id:
            devices = session.query(Device).order_by(Device.createdAt.desc()).all()
            day_records = records  # 已经是该天的所有记录
            day_total_in = sum(r.countIn for r in day_records)
            device_daily = []
            for dev in devices:
                dev_records = [r for r in day_records if r.deviceId == dev.id]
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

        return success_response({
            "dimension": dimension,
            "data": result,
            "dailyDeviceData": daily_device_data,
            "startDate": start_date,
            "endDate": end_date,
            "deviceId": device_id or None,
        })



@router.put("/correct")
async def correct_traffic_record(request: Request):
    """
    修正客流记录
    参数: date(YYYY-MM-DD), hour(0-23), countIn(修正值), countOut(修正值), deviceId(可选)
    如果记录存在则更新，不存在则创建
    """
    body = await request.json()
    date_str = body.get("date")
    hour = body.get("hour")
    count_in = body.get("countIn", 0)
    count_out = body.get("countOut", 0)
    device_id = body.get("deviceId")  # None = 门店汇总

    if not date_str or hour is None:
        return error_response("缺少必填参数: date, hour", 400)

    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_regex.match(date_str):
        return error_response("日期格式不正确", 400)

    if not isinstance(hour, int) or hour < 0 or hour > 23:
        return error_response("hour 必须为 0-23 的整数", 400)

    try:
        count_in_int = int(count_in)
        count_out_int = int(count_out)
    except (ValueError, TypeError):
        return error_response("countIn 和 countOut 必须为数字", 400)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        # 查找匹配的记录
        query = session.query(TrafficRecord).filter(
            TrafficRecord.date == date_str,
            TrafficRecord.hour == hour,
        )
        if device_id:
            query = query.filter(TrafficRecord.deviceId == device_id)
        else:
            query = query.filter(TrafficRecord.deviceId.is_(None))

        record = query.first()

        if record:
            record.countIn = count_in_int
            record.countOut = count_out_int
        else:
            record = TrafficRecord(
                id=None,  # auto-generate
                deviceId=device_id,
                date=date_str,
                hour=hour,
                countIn=count_in_int,
                countOut=count_out_int,
            )
            session.add(record)

        session.commit()
        session.refresh(record)

        return success_response({
            "id": record.id,
            "deviceId": record.deviceId,
            "date": record.date,
            "hour": record.hour,
            "countIn": record.countIn,
            "countOut": record.countOut,
        })


def _aggregate_hourly(records, date_str):
    """按小时聚合 (0-23), 无数据补0"""
    hour_map = {h: {"label": f"{h:02d}:00", "countIn": 0, "countOut": 0} for h in range(24)}
    for record in records:
        if record.date == date_str and 0 <= record.hour <= 23:
            hour_map[record.hour]["countIn"] += record.countIn
            hour_map[record.hour]["countOut"] += record.countOut
    return [hour_map[h] for h in range(24)]


def _aggregate_daily(records, start_date, end_date):
    """按天聚合, 无数据补0"""
    daily_map = {}
    for record in records:
        key = record.date
        if key not in daily_map:
            daily_map[key] = {"label": key, "countIn": 0, "countOut": 0}
        daily_map[key]["countIn"] += record.countIn
        daily_map[key]["countOut"] += record.countOut

    # 填充日期范围
    result = []
    cur = _parse_date(start_date)
    end = _parse_date(end_date)
    while cur <= end:
        key = cur.strftime("%Y-%m-%d")
        if key in daily_map:
            result.append(daily_map[key])
        else:
            result.append({"label": key, "countIn": 0, "countOut": 0})
        cur += timedelta(days=1)
    return result


def _aggregate_weekly(records, start_date, end_date):
    """按周聚合, 无数据补0"""
    week_map = {}
    for record in records:
        key = _get_iso_week_key(record.date)
        if key not in week_map:
            week_map[key] = {"label": key, "countIn": 0, "countOut": 0}
        week_map[key]["countIn"] += record.countIn
        week_map[key]["countOut"] += record.countOut

    # 填充周范围
    result = []
    cur = _parse_date(start_date)
    end = _parse_date(end_date)
    seen = set()
    while cur <= end:
        key = _get_iso_week_key(cur.strftime("%Y-%m-%d"))
        if key not in seen:
            seen.add(key)
            if key in week_map:
                result.append(week_map[key])
            else:
                result.append({"label": key, "countIn": 0, "countOut": 0})
        cur += timedelta(days=1)
    return result


def _aggregate_monthly(records, start_date, end_date):
    """按月聚合, 无数据补0"""
    month_map = {}
    for record in records:
        key = record.date[:7]  # YYYY-MM
        if key not in month_map:
            month_map[key] = {"label": key, "countIn": 0, "countOut": 0}
        month_map[key]["countIn"] += record.countIn
        month_map[key]["countOut"] += record.countOut

    # 填充月份范围
    result = []
    cur = _parse_date(start_date).replace(day=1)
    end = _parse_date(end_date).replace(day=1)
    while cur <= end:
        key = cur.strftime("%Y-%m")
        if key in month_map:
            result.append(month_map[key])
        else:
            result.append({"label": key, "countIn": 0, "countOut": 0})
        # 加一个月
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return result


def _aggregate_yearly(records, start_date, end_date):
    """按年聚合, 无数据补0"""
    year_map = {}
    for record in records:
        key = record.date[:4]  # YYYY
        if key not in year_map:
            year_map[key] = {"label": key, "countIn": 0, "countOut": 0}
        year_map[key]["countIn"] += record.countIn
        year_map[key]["countOut"] += record.countOut

    # 填充年份范围
    result = []
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    for year in range(start_year, end_year + 1):
        key = str(year)
        if key in year_map:
            result.append(year_map[key])
        else:
            result.append({"label": key, "countIn": 0, "countOut": 0})
    return result


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def _get_iso_week_key(date_str: str) -> str:
    """返回 ISO 周键值如 '2026-W21'"""
    d = _parse_date(date_str)
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"
