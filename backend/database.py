"""
FluxaVision 客流统计系统 - SQLCipher 加密数据库连接

使用 SQLCipher 对 SQLite 数据库进行 AES-256 透明加密。
加密密钥由 config.py 管理，绑定硬件指纹。

安全架构：
- 数据库文件：AES-256 加密（SQLCipher 4）
- 加密密钥：通过硬件指纹 + 随机盐值派生，存储在加密密钥文件中
- 防拷贝：数据库和密钥文件均绑定到当前硬件，无法在其他机器使用
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import DB_PATH, DB_ENCRYPTION_KEY

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _set_sqlcipher_pragmas(dbapi_conn, connection_record):
    """连接后设置 SQLCipher 加密参数"""
    cursor = dbapi_conn.cursor()
    # 设置加密密钥（使用字符串密码方式）
    cursor.execute(f"PRAGMA key = '{DB_ENCRYPTION_KEY}'")
    # 3. 验证数据库是否可以正常解密
    try:
        cursor.execute("SELECT count(*) FROM sqlite_master")
    except Exception as e:
        raise RuntimeError(f"数据库解密失败: {e}")
    # 4. 性能和安全配置
    cursor.execute("PRAGMA cipher_page_size = 4096")
    cursor.execute("PRAGMA kdf_iter = 256000")
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.close()


def get_engine():
    """
    创建 SQLCipher 引擎
    
    使用 'sqlite://' 前缀（不是 pysqlcipher://）避免 SQLAlchemy 内置
    的 pysqlcipher 方言自动处理 PRAGMA key（与我们的自定义事件冲突）
    """
    import sqlcipher3
    
    # 使用 sqlite:// 前缀 + module=sqlcipher3 的方式
    # 这样 SQLAlchemy 不会自动处理 PRAGMA key，由我们的事件处理器统一管理
    connect_url = f"sqlite:///{DB_PATH}"
    
    engine = create_engine(
        connect_url,
        module=sqlcipher3,
        connect_args={"check_same_thread": False},
        echo=False,
        pool_pre_ping=True,
    )
    
    # 注册连接事件：每次连接时设置 SQLCipher 加密参数
    event.listen(engine, "connect", _set_sqlcipher_pragmas)
    
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
    logger.info(f"✓ 加密方式: SQLCipher AES-256 (密钥长度: {len(DB_ENCRYPTION_KEY)} hex chars)")
    return engine


def get_session_factory(engine=None):
    """获取 Session 工厂"""
    if engine is None:
        engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
