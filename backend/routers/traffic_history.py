"""
GET /api/traffic/history - 查询历史客流数据
"""
from fastapi import APIRouter, Request
import re
from collections import defaultdict
from sqlalchemy.orm import Session
from database import get_session_factory
from models import TrafficRecord
from utils import success_response, error_response

router = APIRouter(prefix="/api/traffic/history", tags=["客流数据"])


@router.get("")
async def get_history_data(request: Request):
    """查询历史客流数据"""
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
            query = query.filter_by(deviceId=device_id)
        
        records = query.order_by(TrafficRecord.date, TrafficRecord.hour).all()
        
        # 按日聚合
        daily_map = defaultdict(lambda: {"date": "", "countIn": 0, "countOut": 0})
        for record in records:
            key = record.date
            daily_map[key]["date"] = key
            daily_map[key]["countIn"] += record.countIn
            daily_map[key]["countOut"] += record.countOut
        
        daily_data = sorted(daily_map.values(), key=lambda x: x["date"])
        
        # 单天时返回按小时数据
        hourly_data = None
        if start_date == end_date:
            hourly_map = {h: {"hour": h, "countIn": 0, "countOut": 0} for h in range(24)}
            for record in records:
                if record.hour in hourly_map:
                    hourly_map[record.hour]["countIn"] += record.countIn
                    hourly_map[record.hour]["countOut"] += record.countOut
            hourly_data = sorted(hourly_map.values(), key=lambda x: x["hour"])
        
        return success_response({
            "daily": daily_data,
            "hourly": hourly_data,
            "startDate": start_date,
            "endDate": end_date,
            "deviceId": device_id or None,
        })
