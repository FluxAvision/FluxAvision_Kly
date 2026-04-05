"""
PUT /api/devices/{id}/status - 更新设备状态
"""
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from database import get_session_factory
from models import Device
from utils import success_response, error_response, model_to_dict

router = APIRouter(prefix="/api/devices", tags=["设备管理"])

VALID_STATUSES = ["online", "offline", "warning"]


@router.put("/{device_id}/status")
async def update_device_status(device_id: str, request: Request):
    """更新设备状态"""
    body = await request.json()
    status = body.get("status", "")
    
    if status not in VALID_STATUSES:
        return error_response(f"无效的状态值, 仅支持: {', '.join(VALID_STATUSES)}", 400)
    
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = session.query(Device).filter_by(id=device_id).first()
        if not device:
            return error_response("设备不存在", 404)
        
        device.status = status
        session.commit()
        session.refresh(device)
        
        return success_response(model_to_dict(device))
