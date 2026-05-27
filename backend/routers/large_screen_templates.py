"""
大屏模板管理 API

GET    /api/large-screen/templates          - 获取模板列表
GET    /api/large-screen/templates/{id}     - 获取模板详情
POST   /api/large-screen/templates          - 创建模板
PUT    /api/large-screen/templates/{id}     - 更新模板
DELETE /api/large-screen/templates/{id}     - 删除模板
POST   /api/large-screen/templates/{id}/duplicate - 复制模板
"""
import json
import logging
import uuid
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from database import get_session_factory
from models import ScreenTemplate
from utils import success_response, error_response, model_to_dict
import os

# 加载种子模板数据
_seed_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
with open(_seed_path, "r", encoding="utf-8") as _f:
    SEED_TEMPLATES = json.load(_f)

logger = logging.getLogger(__name__)


# ==================== 预置模板 ====================

BUILTIN_TEMPLATE_NAMES = ["通用模板", "简约模板", "标准模板", "视频模板"]


def seed_builtin_templates():
    """启动时初始化预置模板（数据库为空时创建4个默认模板）"""
    from sqlalchemy import func
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        count = session.query(func.count(ScreenTemplate.id)).scalar()
        if count > 0:
            logger.info(f"大屏模板已存在 ({count} 个)，跳过初始化")
            return

        for tpl in SEED_TEMPLATES:
            tid = uuid.uuid4().hex[:30]
            template = ScreenTemplate(
                id=tid,
                name=tpl["name"],
                description=tpl.get("description", ""),
                isSystem=False,
                isPublished=True,
                layout="custom",
                templateConfig=json.dumps(tpl["templateConfig"], ensure_ascii=False),
                canvasWidth=tpl.get("canvasWidth", 1920),
                canvasHeight=tpl.get("canvasHeight", 1080),
                backgroundColor=tpl.get("backgroundColor", "#0a192f"),
                backgroundImage="",
            )
            session.add(template)

        session.commit()
        logger.info(f"\u2713 已初始化 {len(SEED_TEMPLATES)} 个默认大屏模板")

router = APIRouter(prefix="/api/large-screen/templates", tags=["大屏模板"])


@router.get("")
async def get_templates():
    """获取大屏模板列表"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        templates = session.query(ScreenTemplate).order_by(
            ScreenTemplate.createdAt.desc()
        ).all()
        return success_response([model_to_dict(t) for t in templates])


@router.get("/{template_id}")
async def get_template(template_id: str):
    """获取单个模板详情"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        template = session.query(ScreenTemplate).filter_by(id=template_id).first()
        if not template:
            return error_response("模板不存在", 404)
        return success_response(model_to_dict(template))


@router.post("")
async def create_template(request: Request):
    """创建新模板"""
    body = await request.json()

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        template = ScreenTemplate(
            name=body.get("name", "未命名模板"),
            description=body.get("description", ""),
            thumbnail=body.get("thumbnail", ""),
            layout=body.get("layout", "custom"),
            templateConfig=json.dumps(body.get("templateConfig", {}), ensure_ascii=False),
            canvasWidth=body.get("canvasWidth", 1920),
            canvasHeight=body.get("canvasHeight", 1080),
            backgroundColor=body.get("backgroundColor", "#0a192f"),
            backgroundImage=body.get("backgroundImage", ""),
            isSystem=False,
            isPublished=True,
        )
        session.add(template)
        session.commit()
        session.refresh(template)
        return success_response(model_to_dict(template))


@router.put("/{template_id}")
async def update_template(template_id: str, request: Request):
    """更新模板"""
    body = await request.json()

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        template = session.query(ScreenTemplate).filter_by(id=template_id).first()
        if not template:
            return error_response("模板不存在", 404)

        # 更新字段
        if "name" in body:
            template.name = body["name"]
        if "description" in body:
            template.description = body["description"]
        if "thumbnail" in body:
            template.thumbnail = body["thumbnail"]
        if "layout" in body:
            template.layout = body["layout"]
        if "templateConfig" in body:
            template.templateConfig = json.dumps(body["templateConfig"], ensure_ascii=False)
        if "canvasWidth" in body:
            template.canvasWidth = body["canvasWidth"]
        if "canvasHeight" in body:
            template.canvasHeight = body["canvasHeight"]
        if "backgroundColor" in body:
            template.backgroundColor = body["backgroundColor"]
        if "backgroundImage" in body:
            template.backgroundImage = body["backgroundImage"]
        if "isPublished" in body:
            template.isPublished = body["isPublished"]

        session.commit()
        session.refresh(template)
        return success_response(model_to_dict(template))


@router.delete("/{template_id}")
async def delete_template(template_id: str):
    """删除模板"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        template = session.query(ScreenTemplate).filter_by(id=template_id).first()
        if not template:
            return error_response("模板不存在", 404)

        session.delete(template)
        session.commit()
        return success_response(message="删除成功")


@router.post("/{template_id}/duplicate")
async def duplicate_template(template_id: str, request: Request):
    """复制模板"""
    body = await request.json()
    new_name = body.get("name")

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        original = session.query(ScreenTemplate).filter_by(id=template_id).first()
        if not original:
            return error_response("模板不存在", 404)

        new_template = ScreenTemplate(
            name=new_name or f"{original.name} (副本)",
            description=original.description,
            thumbnail=original.thumbnail,
            layout=original.layout,
            templateConfig=original.templateConfig,
            canvasWidth=original.canvasWidth,
            canvasHeight=original.canvasHeight,
            backgroundColor=original.backgroundColor,
            backgroundImage=original.backgroundImage,
            isSystem=False,
            isPublished=True,
        )
        session.add(new_template)
        session.commit()
        session.refresh(new_template)
        return success_response(model_to_dict(new_template))
