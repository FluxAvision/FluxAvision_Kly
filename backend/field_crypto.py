"""
FluxaVision 客流统计系统 - 字段级 AES-256 加密工具

用于对数据库中的敏感字段进行透明加解密：
- 设备密码 (Device.password)
- 登录密码 (SystemSettings.loginPassword)
- 激活码 (License.activationCode)

加密方式：AES-256-CBC + PKCS7 填充
密钥来源：config.DB_ENCRYPTION_KEY（硬件指纹派生）
"""
import base64
import os
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

logger = logging.getLogger(__name__)

CIPHER_PREFIX = "ENC:"


def _get_aes_key() -> bytes:
    """从 DB_ENCRYPTION_KEY 派生 AES-256 密钥"""
    from config import DB_ENCRYPTION_KEY
    key_hex = DB_ENCRYPTION_KEY[:64]
    return bytes.fromhex(key_hex)


def encrypt_field(plaintext: str) -> str:
    """加密字段值，返回 ENC:{base64(iv+ciphertext)} 格式"""
    if not plaintext:
        return plaintext
    try:
        key = _get_aes_key()
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        data = plaintext.encode("utf-8")
        padded_data = padder.update(data) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        encrypted_bytes = iv + ciphertext
        encoded = base64.b64encode(encrypted_bytes).decode("ascii")
        return f"{CIPHER_PREFIX}{encoded}"
    except Exception as e:
        logger.error(f"字段加密失败: {e}")
        return ""


def decrypt_field(encrypted: str) -> str:
    """解密字段值。非 ENC: 格式直接返回原文（向后兼容）"""
    if not encrypted:
        return encrypted
    if not encrypted.startswith(CIPHER_PREFIX):
        return encrypted
    try:
        key = _get_aes_key()
        encoded = encrypted[len(CIPHER_PREFIX):]
        encrypted_bytes = base64.b64decode(encoded)
        iv = encrypted_bytes[:16]
        ciphertext = encrypted_bytes[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        return plaintext.decode("utf-8")
    except Exception as e:
        logger.error(f"字段解密失败: {e}")
        return ""
