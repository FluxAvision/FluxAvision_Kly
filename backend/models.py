"""
FluxaVision 客流统计系统 - SQLAlchemy ORM 模型

与原 Prisma Schema 完全对应，使用 SQLCipher 加密数据库。
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Index,
)
from database import Base


def _utcnow():
    return datetime.utcnow()


# ==================== 设备管理 ====================
class Device(Base):
    __tablename__ = "devices"

    id           = Column(String(36), primary_key=True, default=lambda: _generate_cuid())
    name         = Column(String(100), nullable=False, comment="设备名称")
    ip           = Column(String(45), nullable=False, comment="IP地址")
    serialNumber = Column(String(100), nullable=False, unique=True, comment="序列号")
    location     = Column(String(200), nullable=False, comment="安装位置")
    model        = Column(String(50), default="大华", comment="型号")
    rtspPort     = Column(Integer, default=554, comment="RTSP端口")
    username     = Column(String(50), default="admin", comment="用户名")
    password     = Column(String(200), default="", comment="密码")
    rtspUrl      = Column(String(500), nullable=False, comment="RTSP地址")
    sdkPort      = Column(Integer, default=37777, comment="SDK端口 (大华默认37777)")
    channel      = Column(Integer, default=0, comment="客流统计通道号")
    status       = Column(String(20), default="offline", comment="状态: online/offline/warning")
    maxChannels  = Column(Integer, default=4, comment="最大通道数")
    createdAt    = Column(DateTime, default=_utcnow)
    updatedAt    = Column(DateTime, default=_utcnow, onupdate=_utcnow)


# ==================== 客流记录 ====================
class TrafficRecord(Base):
    __tablename__ = "traffic_records"

    id       = Column(String(36), primary_key=True, default=lambda: _generate_cuid())
    deviceId = Column(String(36), nullable=True, comment="设备ID (null表示汇总)")
    date     = Column(String(10), nullable=False, comment="日期 YYYY-MM-DD")
    hour     = Column(Integer, nullable=False, comment="小时 0-23")
    countIn  = Column(Integer, default=0, comment="进入人数")
    countOut = Column(Integer, default=0, comment="出去人数")
    createdAt = Column(DateTime, default=_utcnow)
    updatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("idx_traffic_date_hour", "date", "hour"),
        Index("idx_traffic_device_date", "deviceId", "date"),
    )


# ==================== 系统设置 ====================
class SystemSettings(Base):
    __tablename__ = "system_settings"

    id              = Column(String(20), primary_key=True, default="default")
    storeName       = Column(String(100), default="我的门店", comment="门店名称")
    storeLogo       = Column(String(500), default="", comment="门店Logo路径")
    loginPassword   = Column(String(200), default="", comment="登录密码")
    dashboardMetrics = Column(String(200), default="todayIn,todayOut,currentIn,weekIn", comment="仪表盘显示指标")
    createdAt       = Column(DateTime, default=_utcnow)
    updatedAt       = Column(DateTime, default=_utcnow, onupdate=_utcnow)


# ==================== 大屏设置 ====================
class LargeScreenSettings(Base):
    __tablename__ = "large_screen_settings"

    id              = Column(String(20), primary_key=True, default="default")
    title           = Column(String(200), default="客流统计大屏", comment="大屏标题")
    subtitle        = Column(String(200), default="实时客流数据展示", comment="大屏副标题")
    logo            = Column(String(500), default="", comment="大屏LOGO")
    backgroundImage = Column(String(500), default="", comment="大屏背景图")
    metrics         = Column(String(200), default="todayIn,todayOut,currentIn", comment="大屏数据指标(逗号分隔)")
    deviceIds       = Column(String(500), default="", comment="大屏显示的设备ID(逗号分隔)")
    templateId      = Column(String(36), default="", comment="模板ID(可随时更换)")
    createdAt       = Column(DateTime, default=_utcnow)
    updatedAt       = Column(DateTime, default=_utcnow, onupdate=_utcnow)


# ==================== 大屏模板 ====================
class ScreenTemplate(Base):
    __tablename__ = "screen_templates"

    id          = Column(String(36), primary_key=True, default=lambda: _generate_cuid())
    name        = Column(String(100), nullable=False, comment="模板名称")
    description = Column(String(500), default="", comment="模板描述")
    thumbnail   = Column(String(500), default="", comment="缩略图")
    layout      = Column(String(50), default="default", comment="布局类型")
    createdAt   = Column(DateTime, default=_utcnow)


# ==================== License管理 ====================
class License(Base):
    __tablename__ = "licenses"

    id                  = Column(String(20), primary_key=True, default="default")
    hardwareFingerprint = Column(String(64), default="", comment="硬件指纹 (32位)")
    activationCode      = Column(Text, default="", comment="Ed25519签名授权码")
    licenseFile         = Column(Text, default="", comment="授权文件内容")
    maxChannels         = Column(Integer, default=4, comment="最大路数(通道数)")
    maxDevices          = Column(Integer, default=4, comment="最大设备数(兼容旧字段)")
    expiryDays          = Column(Integer, default=0, comment="授权天数")
    expiryDate          = Column(String(10), default="", comment="到期日期")
    issuedAt            = Column(DateTime, nullable=True, comment="授权码签发时间")
    isActive            = Column(Boolean, default=False, comment="是否已激活")
    activatedAt         = Column(DateTime, nullable=True, comment="激活时间")
    createdAt           = Column(DateTime, default=_utcnow)
    updatedAt           = Column(DateTime, default=_utcnow, onupdate=_utcnow)


def _generate_cuid() -> str:
    """生成类似CUID的唯一ID (基于UUID4确保全局唯一)"""
    import uuid
    return uuid.uuid4().hex[:25]
