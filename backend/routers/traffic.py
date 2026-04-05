"""
POST /api/traffic - 创建或更新客流记录
"""
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from database import get_session_factory
from models import TrafficRecord
from utils import success_response, error_response, model_to_dict

router = APIRouter(prefix="/api/traffic", tags=["客流数据"])


@router.post("")
async def create_traffic_record(request: Request):
    """创建或更新客流记录"""
    body = await request.json()
    record_date = body.get("date")
    hour = body.get("hour")
    device_id = body.get("deviceId")
    count_in = body.get("countIn", 0)
    count_out = body.get("countOut", 0)
    
    if not record_date or hour is None:
        return error_response("缺少必填字段: date, hour", 400)
    
    if not (0 <= hour <= 23):
        return error_response("hour 必须在 0-23 之间", 400)
    
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        # 查找已有记录
        existing = session.query(TrafficRecord).filter_by(
            deviceId=device_id, date=record_date, hour=hour
        ).first()
        
        if existing:
            existing.countIn = (existing.countIn or 0) + count_in
            existing.countOut = (existing.countOut or 0) + count_out
            session.commit()
            session.refresh(existing)
            record = existing
        else:
            record = TrafficRecord(
                deviceId=device_id, date=record_date, hour=hour,
                countIn=count_in, countOut=count_out,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
        
        return success_response(model_to_dict(record), status_code=201)
