"""
POST /api/auth - 登录密码验证
"""
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from database import get_session_factory
from models import SystemSettings
from utils import success_response, error_response, model_to_dict

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("")
async def login(request: Request):
    """验证登录密码"""
    body = await request.json()
    password = body.get("password", "")
    
    if not password:
        return error_response("请输入密码", 400)
    
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        settings = session.query(SystemSettings).filter_by(id="default").first()
        
        # 不存在则自动创建
        if not settings:
            settings = SystemSettings(id="default")
            session.add(settings)
            session.commit()
            session.refresh(settings)
        
        # 未设置密码则默认允许登录
        if not settings.loginPassword:
            return success_response({
                "authenticated": True,
                "storeName": settings.storeName,
                "isFirstLogin": True,
            })
        
        # 验证密码
        if password == settings.loginPassword:
            return success_response({
                "authenticated": True,
                "storeName": settings.storeName,
                "isFirstLogin": False,
            })
        
        return error_response("密码错误", 401)
