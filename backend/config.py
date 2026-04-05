"""
FluxaVision 客流统计系统 - 后端配置

支持两种运行模式：
  1. 开发模式: 从源码运行，数据目录在项目根目录
  2. 打包模式(exe): PyInstaller打包后运行，数据目录在exe所在目录
"""
import os
import sys
import hashlib
import platform
import uuid
import logging

logger = logging.getLogger(__name__)

# ==================== 路径配置（自动适配打包/开发模式）====================
def _get_base_dir() -> str:
    """
    获取 backend 目录的绝对路径。
    
    - PyInstaller onefile: sys._MEIPASS 是临时解压目录
    - PyInstaller onedir: sys.executable 在 dist/FluxaVision/ 下
    - 开发模式: 直接使用源码目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后运行
        # onedir模式: exe在 dist/FluxaVision/FluxaVision.exe
        # 我们取 exe 所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发模式
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _get_base_dir()

def _get_project_dir() -> str:
    """获取项目根目录"""
    if getattr(sys, 'frozen', False):
        return BASE_DIR  # 打包后，exe目录就是项目目录
    else:
        return os.path.dirname(BASE_DIR)  # 开发模式，上级目录是项目根目录

PROJECT_DIR = _get_project_dir()
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "fluxavision.db")
KEY_FILE = os.path.join(DATA_DIR, ".key")
SALT_FILE = os.path.join(DATA_DIR, ".salt")
LOG_FILE = os.path.join(DATA_DIR, "fluxavision.log")

# 确保数据目录存在
os.makedirs(DATA_DIR, exist_ok=True)

# ==================== 静态前端文件路径 ====================
def get_static_dir() -> str:
    """
    获取静态前端文件目录。

    打包模式(PyInstaller onedir):
      - Windows: dist/FluxaVision/FluxaVision.exe + _internal/static/
      - Linux:   dist/FluxaVision/FluxaVision   + _internal/static/

    开发模式: 无静态文件（由Next.js dev server提供）
    """
    # 打包后: 静态文件在 _internal/static/ 目录（PyInstaller datas 路径）
    if getattr(sys, 'frozen', False):
        # PyInstaller onedir: _internal/ 与 exe 在同一目录
        internal_dir = os.path.join(PROJECT_DIR, "_internal")
        static_path = os.path.join(internal_dir, "static")
        if os.path.isdir(static_path):
            return static_path

        # 也检查 exe 同级的 static/ 目录
        static_path = os.path.join(PROJECT_DIR, "static")
        if os.path.isdir(static_path):
            return static_path

    # 开发模式下检查构建输出
    static_build = os.path.join(PROJECT_DIR, "frontend-build")
    if os.path.isdir(static_build):
        return static_build
    
    return ""


# ==================== 服务配置 ====================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "15678"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

# ==================== 加密密钥管理 ====================

def _get_machine_id() -> str:
    """获取稳定的机器唯一标识（硬件指纹）"""
    factors = [
        platform.node() or "unknown",
        platform.machine() or "unknown",
        platform.processor() or "unknown",
        str(uuid.getnode()),  # MAC地址
    ]
    raw = "|".join(factors)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _get_or_create_salt() -> str:
    """获取或创建应用随机盐值"""
    if os.path.exists(SALT_FILE):
        with open(SALT_FILE, "r") as f:
            return f.read().strip()
    import secrets
    salt = secrets.token_hex(32)
    with open(SALT_FILE, "w") as f:
        f.write(salt)
    return salt


def _get_or_create_db_key() -> str:
    """
    获取或创建数据库加密密钥。
    
    加密策略：
    1. 首次安装：生成随机密钥 + 硬件指纹 = 数据库密钥
    2. 密钥存储在 .key 文件中，以硬件指纹加密
    3. 解密时验证硬件指纹，确保数据库只能在原机器上使用
    
    安全性：
    - 数据库文件使用 SQLCipher AES-256 加密
    - 密钥文件使用硬件指纹派生密钥二次加密
    - 拷贝数据库到其他机器无法解密（硬件指纹不匹配）
    - 拷贝密钥文件到其他机器也无法解密（硬件指纹不匹配）
    """
    machine_id = _get_machine_id()
    
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            encrypted_key_data = f.read()
        
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding
        import hashlib as hl
        
        key_material = hl.sha256(machine_id.encode("utf-8")).digest()
        
        try:
            iv = encrypted_key_data[:16]
            encrypted_key = encrypted_key_data[16:]
            
            cipher = Cipher(algorithms.AES(key_material), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_key = decryptor.update(encrypted_key) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            db_key = unpadder.update(padded_key) + unpadder.finalize()
            
            return db_key.decode("utf-8")
        except Exception:
            # 密钥验证失败，可能是硬件环境变化（如容器迁移），重新生成
            logger.warning("数据库密钥验证失败，将重新生成密钥和数据库")
            # 清理旧的密钥文件和数据库
            os.remove(KEY_FILE)
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            if os.path.exists(DB_PATH + "-shm"):
                os.remove(DB_PATH + "-shm")
            if os.path.exists(DB_PATH + "-wal"):
                os.remove(DB_PATH + "-wal")
    
    import secrets
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    import hashlib as hl
    
    raw_key = secrets.token_hex(32)  # 64 hex chars = 256 bits
    
    key_material = hl.sha256(machine_id.encode("utf-8")).digest()
    iv = secrets.token_bytes(16)
    
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(raw_key.encode("utf-8")) + padder.finalize()
    
    cipher = Cipher(algorithms.AES(key_material), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted_key = encryptor.update(padded_data) + encryptor.finalize()
    
    with open(KEY_FILE, "wb") as f:
        f.write(iv + encrypted_key)
    
    return raw_key


# 初始化全局密钥
DB_ENCRYPTION_KEY = _get_or_create_db_key()
APP_SALT = _get_or_create_salt()
