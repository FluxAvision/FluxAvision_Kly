"""
GET /api/settings - 获取系统设置
PUT /api/settings - 更新系统设置
"""
from fastapi import APIRouter, Request

from database import get_session_factory
from models import SystemSettings
from utils import model_to_dict, success_response

router = APIRouter(prefix="/api/settings", tags=["系统设置"])


@router.get("")
async def get_settings():
    """获取系统设置"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        settings = session.query(SystemSettings).filter_by(id="default").first()

        if not settings:
            settings = SystemSettings(id="default")
            session.add(settings)
            session.commit()
            session.refresh(settings)

        return success_response(model_to_dict(settings))


@router.put("")
async def update_settings(request: Request):
    """更新系统设置"""
    body = await request.json()

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        settings = session.query(SystemSettings).filter_by(id="default").first()

        if not settings:
            settings = SystemSettings(
                id="default",
                storeName=body.get("storeName", "我的门店"),
                storeLogo=body.get("storeLogo", ""),
                loginPassword=body.get("loginPassword", ""),
                storeMaxCapacity=int(body.get("storeMaxCapacity", 0) or 0),
                instantaneousMaxCapacity=int(body.get("instantaneousMaxCapacity", 0) or 0),
                dashboardMetrics=body.get("dashboardMetrics", "todayIn,todayOut,currentIn,weekIn"),
                dashboardMetricsLabels=body.get("dashboardMetricsLabels", ""),
            )
            session.add(settings)
        else:
            if "storeName" in body:
                settings.storeName = body["storeName"]
            if "storeLogo" in body:
                settings.storeLogo = body["storeLogo"]
            if "loginPassword" in body:
                settings.loginPassword = body["loginPassword"]
            if "storeMaxCapacity" in body:
                settings.storeMaxCapacity = int(body.get("storeMaxCapacity", 0) or 0)
            if "instantaneousMaxCapacity" in body:
                settings.instantaneousMaxCapacity = int(body.get("instantaneousMaxCapacity", 0) or 0)
            if "dashboardMetrics" in body:
                settings.dashboardMetrics = body["dashboardMetrics"]
            if "dashboardMetricsLabels" in body:
                settings.dashboardMetricsLabels = body["dashboardMetricsLabels"]

        session.commit()
        session.refresh(settings)
        return success_response(model_to_dict(settings))
