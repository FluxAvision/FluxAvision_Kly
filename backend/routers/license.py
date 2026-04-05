"""
GET /api/license - 获取License信息
POST /api/license - 激活License (Ed25519签名验证)
"""
from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from database import get_session_factory
from models import License
from utils import (
    success_response, error_response, model_to_dict,
    generate_hardware_fingerprint,
)
from license_crypto import verify_and_parse_activation_code, extract_code_info

router = APIRouter(prefix="/api/license", tags=["License管理"])


@router.get("")
async def get_license():
    """获取License信息（含当前硬件指纹）"""
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        license_record = session.query(License).filter_by(id="default").first()

        if not license_record:
            fingerprint = generate_hardware_fingerprint()
            license_record = License(
                id="default",
                hardwareFingerprint=fingerprint,
            )
            session.add(license_record)
            session.commit()
            session.refresh(license_record)

        # 每次获取都更新硬件指纹（硬件可能变化）
        current_fp = generate_hardware_fingerprint()
        if license_record.hardwareFingerprint != current_fp:
            license_record.hardwareFingerprint = current_fp
            session.commit()
            session.refresh(license_record)

        data = model_to_dict(license_record)

        # 检查是否过期
        if license_record.isActive and license_record.expiryDate:
            try:
                expiry = datetime.strptime(license_record.expiryDate, "%Y-%m-%d")
                if datetime.now() > expiry:
                    data["isExpired"] = True
                    data["expiredMessage"] = f"授权已于 {license_record.expiryDate} 到期"
                else:
                    remaining = (expiry - datetime.now()).days
                    data["isExpired"] = False
                    data["remainingDays"] = remaining
            except ValueError:
                pass

        return success_response(data)


@router.post("")
async def activate_license(request: Request):
    """
    激活License

    请求体:
      {
        "activationCode": "FLUXA.{payload}.{signature}"  // Ed25519签名激活码
      }

    验证流程:
      1. Ed25519 公钥验证签名（防伪造）
      2. 硬件指纹匹配（防跨机器）
      3. 解析路数、天数等参数
    """
    body = await request.json()
    activation_code = body.get("activationCode", "").strip()

    if not activation_code:
        return error_response("请输入授权码", 400)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        license_record = session.query(License).filter_by(id="default").first()

        if not license_record:
            fingerprint = generate_hardware_fingerprint()
            license_record = License(
                id="default",
                hardwareFingerprint=fingerprint,
            )
            session.add(license_record)
            session.commit()
            session.refresh(license_record)

        # 获取当前硬件指纹
        current_fingerprint = license_record.hardwareFingerprint or generate_hardware_fingerprint()

        # ====== Ed25519 签名验证 + 解析 ======
        result = verify_and_parse_activation_code(activation_code, current_fingerprint)

        if not result["valid"]:
            return error_response(result["error"], 400)

        max_channels = result["maxChannels"]
        expiry_days = result["expiryDays"]
        issued_at_ts = result["issuedAt"]

        # 计算到期日期
        expiry_date = datetime.now() + timedelta(days=expiry_days)

        # 写入数据库
        license_record.activationCode = activation_code
        license_record.maxChannels = max_channels
        license_record.maxDevices = max_channels  # 兼容旧字段
        license_record.expiryDays = expiry_days
        license_record.expiryDate = expiry_date.strftime("%Y-%m-%d")
        license_record.issuedAt = datetime.fromtimestamp(issued_at_ts) if issued_at_ts else None
        license_record.isActive = True
        license_record.activatedAt = datetime.now()

        session.commit()
        session.refresh(license_record)

        return success_response({
            **model_to_dict(license_record),
            "message": f"激活成功! 授权 {max_channels} 路, 有效 {expiry_days} 天, 到期: {expiry_date.strftime('%Y-%m-%d')}"
        })


@router.get("/parse")
async def parse_activation_code(code: str):
    """
    解析激活码信息 (不验证签名, 仅查看明文载荷)

    用于管理员/调试: 确认激活码内容是否正确
    注意: 此接口不验证签名, 返回的载荷信息不可信!
    """
    info = extract_code_info(code)
    if "error" in info:
        return error_response(f"解析失败: {info['error']}", 400)

    return success_response(info)
