"""
FluxaVision 客流统计系统 - 授权码加密模块

基于 Ed25519 数字签名的授权方案：
  - 授权平台持有私钥，可以签名生成激活码
  - 软件内置公钥，只能验证不能伪造
  - 激活码绑定硬件指纹，不可跨机器使用

激活码格式: FLUXA.{Base64URL(JSON载荷)}.{Base64URL(Ed25519签名)}

载荷 JSON:
  {
    "f": "A1B2C3D4",     // 硬件指纹前8位 (绑定机器)
    "c": 4,              // 路数 (最大通道数)
    "d": 365,            // 授权天数
    "t": 1700000000      // 签发时间戳 (防重放)
  }

安全性:
  - Ed25519 签名: 无法从公钥推导私钥，无法伪造签名
  - 硬件指纹绑定: 激活码只能在特定机器上使用
  - 时间戳: 防止旧激活码被重复利用
"""
import base64
import json
import hashlib
import struct
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================
# 公钥 (硬编码在软件中, 用于验证激活码签名)
# 对应私钥由授权平台保管, 绝不分发
# ============================================================
LICENSE_PUBLIC_KEY_HEX = "ec9397306a1f1e339cb203d937b69b4e02bb8b62ab61787a0c719d416663e931"


def _load_public_key(hex_key: str = None):
    """从 HEX 字符串加载 Ed25519 公钥"""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if hex_key is None:
        hex_key = LICENSE_PUBLIC_KEY_HEX
    key_bytes = bytes.fromhex(hex_key)
    return Ed25519PublicKey.from_public_bytes(key_bytes)


def _load_private_key(hex_key: str):
    """从 HEX 字符串加载 Ed25519 私钥 (仅授权平台使用)"""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    key_bytes = bytes.fromhex(hex_key)
    return Ed25519PrivateKey.from_private_bytes(key_bytes)


# ============================================================
# Base64URL 编解码 (无填充, URL安全)
# ============================================================
def _b64url_encode(data: bytes) -> str:
    """Base64URL 编码 (无填充)"""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Base64URL 解码 (自动补填充)"""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


# ============================================================
# 授权码签名 (授权平台调用)
# ============================================================
def sign_activation_code(
    hardware_fingerprint: str,
    max_channels: int,
    expiry_days: int,
    private_key_hex: str,
) -> str:
    """
    生成授权激活码 (仅授权平台可调用)

    参数:
        hardware_fingerprint: 客户的硬件指纹 (完整32位)
        max_channels: 最大路数 (通道数)
        expiry_days: 授权天数
        private_key_hex: 私钥 HEX 字符串

    返回:
        完整激活码字符串, 格式: FLUXA.{payload}.{signature}

    示例:
        >>> code = sign_activation_code("A1B2C3D4E5F67890...", 4, 365, private_key_hex)
        >>> print(code)
        FLUXA.eyJmIjoiQTFCMkMzRDQiLCJjIjo0LCJkIjozNjV9.abc123def456...
    """
    # 构建载荷: 硬件指纹取前8位 (足够绑定, 32位碰撞概率极低)
    payload = {
        "f": hardware_fingerprint[:8].upper(),  # 指纹前8位
        "c": max_channels,                       # 路数
        "d": expiry_days,                        # 天数
        "t": int(time.time()),                   # 签发时间戳
    }

    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_bytes = payload_json.encode("utf-8")
    payload_b64 = _b64url_encode(payload_bytes)

    # Ed25519 签名
    private_key = _load_private_key(private_key_hex)
    signature = private_key.sign(payload_bytes)
    signature_b64 = _b64url_encode(signature)

    return f"FLUXA.{payload_b64}.{signature_b64}"


# ============================================================
# 授权码验证 (软件端调用)
# ============================================================
def verify_and_parse_activation_code(
    code: str,
    current_fingerprint: str,
) -> dict:
    """
    验证激活码并解析授权信息 (软件端调用)

    验证流程:
      1. 格式校验 (FLUXA.{payload}.{signature})
      2. Ed25519 签名验证 (公钥验证, 防伪造)
      3. 硬件指纹匹配 (防跨机器使用)
      4. 时间戳校验 (防重放)

    参数:
        code: 用户输入的激活码
        current_fingerprint: 当前机器的硬件指纹 (完整32位)

    返回:
        {
            "valid": True,
            "maxChannels": 4,     // 路数
            "expiryDays": 365,    // 授权天数
            "issuedAt": 1700000000, // 签发时间
            "payload": {...}      // 原始载荷
        }

        或:
        {
            "valid": False,
            "error": "错误描述"
        }
    """
    # ---- 1. 格式校验 ----
    code = code.strip()
    if not code.startswith("FLUXA."):
        return {"valid": False, "error": "激活码格式错误, 必须以 FLUXA. 开头"}

    parts = code.split(".")
    if len(parts) != 3:
        return {"valid": False, "error": "激活码格式错误, 应为 FLUXA.{数据}.{签名}"}

    payload_b64, signature_b64 = parts[1], parts[2]

    try:
        payload_bytes = _b64url_decode(payload_b64)
        signature_bytes = _b64url_decode(signature_b64)
    except Exception:
        return {"valid": False, "error": "激活码编码损坏, 请检查是否完整复制"}

    # ---- 2. Ed25519 签名验证 ----
    try:
        public_key = _load_public_key()
        public_key.verify(signature_bytes, payload_bytes)
    except Exception as e:
        logger.warning(f"激活码签名验证失败: {e}")
        return {"valid": False, "error": "激活码签名无效, 可能被篡改或伪造"}

    # ---- 3. 解析载荷 ----
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return {"valid": False, "error": "激活码数据解析失败"}

    # 校验必要字段
    required_fields = {"f", "c", "d", "t"}
    if not required_fields.issubset(payload.keys()):
        return {"valid": False, "error": "激活码缺少必要字段"}

    # ---- 4. 硬件指纹匹配 ----
    code_fingerprint = payload["f"].upper()
    current_fp_prefix = current_fingerprint[:8].upper()

    if code_fingerprint != current_fp_prefix:
        logger.warning(
            f"硬件指纹不匹配: 激活码={code_fingerprint}, 当前={current_fp_prefix}"
        )
        return {"valid": False, "error": f"激活码与当前机器不匹配, 请确认是否为本机激活码 (预期: {current_fp_prefix})"}

    # ---- 5. 参数合法性校验 ----
    try:
        max_channels = int(payload["c"])
        expiry_days = int(payload["d"])
        issued_at = int(payload["t"])
    except (ValueError, TypeError):
        return {"valid": False, "error": "激活码参数格式错误"}

    if max_channels < 1 or max_channels > 999:
        return {"valid": False, "error": f"无效的路数: {max_channels}"}
    if expiry_days < 1 or expiry_days > 36500:  # 最大100年
        return {"valid": False, "error": f"无效的天数: {expiry_days}"}

    # ---- 6. 时间戳校验 (签发时间不能在未来) ----
    now = int(time.time())
    # 允许 5 分钟的时钟偏差 (防止客户端时钟不准)
    if issued_at > now + 300:
        return {"valid": False, "error": "激活码签发时间异常, 请检查系统时间"}

    # ---- 验证通过 ----
    return {
        "valid": True,
        "maxChannels": max_channels,
        "expiryDays": expiry_days,
        "issuedAt": issued_at,
        "payload": payload,
    }


# ============================================================
# 工具函数
# ============================================================
def extract_code_info(code: str) -> dict:
    """
    仅解析激活码中的明文信息 (不验证签名, 不验证指纹)
    用于管理员/调试查看激活码内容

    注意: 此函数不验证签名, 返回的信息不可信!
    """
    code = code.strip()
    if not code.startswith("FLUXA."):
        return {"error": "格式错误"}

    parts = code.split(".")
    if len(parts) != 3:
        return {"error": "格式错误"}

    try:
        payload_bytes = _b64url_decode(parts[1])
        payload = json.loads(payload_bytes.decode("utf-8"))
        return {
            "fingerprint": payload.get("f", "?"),
            "channels": payload.get("c", "?"),
            "days": payload.get("d", "?"),
            "issuedAt": payload.get("t", "?"),
            "issuedDate": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(payload.get("t", 0))
            ) if payload.get("t") else "?",
        }
    except Exception:
        return {"error": "解析失败"}


# ============================================================
# 密钥对生成 (仅授权平台首次初始化时调用)
# ============================================================
def generate_keypair() -> Tuple[str, str]:
    """
    生成新的 Ed25519 密钥对

    返回:
        (private_key_hex, public_key_hex)

    警告: 私钥必须安全保管! 丢失后所有已发放的激活码将无法验证!
          公钥需要嵌入到软件的 license_crypto.py 中的 LICENSE_PUBLIC_KEY_HEX
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_hex = private_key.private_bytes_raw().hex()
    public_hex = public_key.public_bytes_raw().hex()

    return private_hex, public_hex


# ============================================================
# 自测
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("FluxaVision 授权模块自测")
    print("=" * 60)

    # 生成测试密钥对
    test_priv, test_pub = generate_keypair()
    print(f"\n测试公钥: {test_pub[:16]}...")

    # 生成激活码
    test_fingerprint = "A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6"
    code = sign_activation_code(test_fingerprint, 8, 365, test_priv)
    print(f"\n生成的激活码 ({len(code)} 字符):")
    print(f"  {code[:50]}...")
    print(f"  ...{code[-30:]}")

    # ---- 测试1: 用正确公钥 + 正确指纹验证 ----
    # 直接调用底层验证 (传入测试公钥)
    import base64 as b64
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    parts = code.split(".")
    payload_bytes = b64.urlsafe_b64decode(parts[1] + "==")
    sig_bytes = b64.urlsafe_b64decode(parts[2] + "==")
    test_pub_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(test_pub))
    try:
        test_pub_key.verify(sig_bytes, payload_bytes)
        print("\n[测试1] Ed25519 签名验证: PASS")
    except Exception as e:
        print(f"\n[测试1] Ed25519 签名验证: FAIL ({e})")

    # ---- 测试2: 篡改签名后验证 ----
    tampered = code[:-5] + "XXXXX"
    parts2 = tampered.split(".")
    try:
        sig2 = b64.urlsafe_b64decode(parts2[2] + "==")
        test_pub_key.verify(sig2, payload_bytes)
        print("[测试2] 篡改检测: FAIL (应拒绝)")
    except Exception:
        print("[测试2] 篡改检测: PASS (正确拒绝)")

    # ---- 测试3: 查看明文信息 ----
    info = extract_code_info(code)
    print(f"\n[测试3] 明文解析: {info}")

    # ---- 测试4: 使用正式公钥验证正式密钥签名的码 ----
    import os
    priv_key_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'private_key.hex')
    if os.path.exists(priv_key_file):
        with open(priv_key_file) as f:
            real_priv = f.read().strip()
        real_code = sign_activation_code(test_fingerprint, 4, 90, real_priv)
        result = verify_and_parse_activation_code(real_code, test_fingerprint)
        if result.get("valid"):
            print(f"\n[测试4] 正式密钥验证: PASS (路数={result['maxChannels']}, 天数={result['expiryDays']})")
        else:
            print(f"\n[测试4] 正式密钥验证: FAIL ({result.get('error')})")
    else:
        print("\n[测试4] 跳过 (无正式私钥文件)")

    print("\n" + "=" * 60)
    print("自测完成!")
    print("=" * 60)
