"""
GET /api/large-screen/templates - 获取大屏模板列表
"""
from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import get_session_factory
from models import ScreenTemplate
from utils import success_response, models_to_list

router = APIRouter(prefix="/api/large-screen/templates", tags=["大屏模板"])


@router.get("")
async def get_templates():
    """获取大屏模板列表"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        templates = session.query(ScreenTemplate).order_by(
            ScreenTemplate.createdAt.desc()
        ).all()
        return success_response(models_to_list(templates))
