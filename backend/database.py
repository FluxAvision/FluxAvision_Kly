"""
FluxaVision 客流统计系统 - 数据库连接模块

使用 Python 内置 sqlite3 + 应用层 AES-256 字段加密。
加密密钥由 config.py 管理，绑定硬件指纹。

安全架构：
- 敏感字段：AES-256-CBC 加密（通过 field_crypto 模块）
- 加密密钥：通过硬件指纹 + 随机盐值派生，存储在加密密钥文件中
- 防拷贝：密钥文件绑定到当前硬件，无法在其他机器使用
- 数据库文件：标准 SQLite3（WAL模式），敏感字段均为密文存储
"""
import logging
import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DB_PATH, DB_ENCRYPTION_KEY

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """连接后设置 SQLite 优化参数"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.execute("PRAGMA cache_size = -8000")  # 8MB 缓存
    cursor.execute("PRAGMA busy_timeout = 5000")  # 5秒忙等待
    cursor.close()


def get_engine():
    """
    创建 SQLite3 引擎

    使用 Python 内置 sqlite3 模块（无需额外安装），配合
    field_crypto 模块实现敏感字段 AES-256 加密。
    """
    connect_url = f"sqlite:///{DB_PATH}"

    engine = create_engine(
        connect_url,
        module=sqlite3,
        connect_args={"check_same_thread": False},
        echo=False,
        pool_pre_ping=True,
    )

    # 注册连接事件：每次连接时设置优化参数
    event.listen(engine, "connect", _set_sqlite_pragmas)

    return engine


def _migrate_database(engine):
    """数据库迁移: 为已有表添加新字段"""
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    with engine.connect() as conn:
        # 获取 devices 表已有列名
        existing_cols = set()
        try:
            existing_cols = {col["name"] for col in inspector.get_columns("devices")}
        except Exception:
            pass

        migrations = []
        if "sdkPort" not in existing_cols:
            migrations.append("ALTER TABLE devices ADD COLUMN sdkPort INTEGER DEFAULT 37777")
        if "channel" not in existing_cols:
            migrations.append("ALTER TABLE devices ADD COLUMN channel INTEGER DEFAULT 0")

        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"  迁移: {sql}")
            except Exception as e:
                logger.warning(f"  迁移跳过 (可能已存在): {e}")


def init_database():
    """初始化数据库（创建所有表 + 运行迁移）"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    _migrate_database(engine)
    logger.info(f"✓ 数据库初始化完成: {DB_PATH}")
    logger.info(f"✓ 加密方式: AES-256 字段加密 (密钥长度: {len(DB_ENCRYPTION_KEY)} hex chars)")
    return engine


def get_session_factory(engine=None):
    """获取 Session 工厂"""
    if engine is None:
        engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
