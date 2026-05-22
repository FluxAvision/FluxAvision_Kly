"""
GET /api/large-screen - 获取大屏设置
PUT /api/large-screen - 更新大屏设置（模板可随时更换，指标最多4个）
"""
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from database import get_session_factory
from models import LargeScreenSettings
from utils import success_response, error_response, model_to_dict

router = APIRouter(prefix="/api/large-screen", tags=["大屏设置"])


@router.get("")
async def get_large_screen_settings():
    """获取大屏设置"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        settings = session.query(LargeScreenSettings).filter_by(id="default").first()
        
        if not settings:
            settings = LargeScreenSettings(id="default")
            session.add(settings)
            session.commit()
            session.refresh(settings)
        
        return success_response(model_to_dict(settings))


@router.put("")
async def update_large_screen_settings(request: Request):
    """
    更新大屏设置
    - 模板可随时更换（无限制）
    - 指标自由选择，最多4个
    """
    body = await request.json()
    
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        settings = session.query(LargeScreenSettings).filter_by(id="default").first()
        
        # 验证指标数量（最多4个）
        metrics = body.get("metrics", "")
        if metrics:
            metric_list = [m.strip() for m in metrics.split(",") if m.strip()]
            if len(metric_list) > 4:
                return error_response("大屏展示指标最多选择4个", 400)
        
        if not settings:
            settings = LargeScreenSettings(
                id="default",
                title=body.get("title", "客流统计大屏"),
                subtitle=body.get("subtitle", "实时客流数据展示"),
                logo=body.get("logo", ""),
                backgroundImage=body.get("backgroundImage", ""),
                metrics=body.get("metrics", "todayIn,todayOut,currentIn"),
                deviceIds=body.get("deviceIds", ""),
                templateId=body.get("templateId", ""),
            )
            session.add(settings)
        else:
            # 模板可随时更换 - 无任何限制
            if "title" in body:
                settings.title = body["title"]
            if "subtitle" in body:
                settings.subtitle = body["subtitle"]
            if "logo" in body:
                settings.logo = body["logo"]
            if "backgroundImage" in body:
                settings.backgroundImage = body["backgroundImage"]
            if "backgroundColor" in body:
                settings.backgroundColor = body["backgroundColor"]
            if "metrics" in body:
                settings.metrics = body["metrics"]
            if "deviceIds" in body:
                settings.deviceIds = body["deviceIds"]
            if "templateId" in body:
                settings.templateId = body["templateId"]
        
        session.commit()
        session.refresh(settings)
        return success_response(model_to_dict(settings))
