"""
FluxaVision 客流统计系统 - 工具函数
"""
import hashlib
import platform
import ctypes
import ctypes.wintypes
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_physical_disk_serial_win32() -> str:
    """
    通过 Win32 API (CreateFile + DeviceIoControl) 读取第一块物理硬盘序列号。

    绝不使用 WMI/wmic，直接调用 Windows 内核 API：
      CreateFile(\\.\\\\PhysicalDrive0) → DeviceIoControl(IOCTL_STORAGE_QUERY_PROPERTY)
      → STORAGE_DEVICE_DESCRIPTOR.SerialNumberOffset → serial number

    Returns:
        硬盘序列号字符串，失败返回空字符串
    """
    # 仅在 Windows 上执行
    if platform.system() != "Windows":
        return ""

    # --- Win32 常量 ---
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    # CTL_CODE(IOCTL_STORAGE_BASE, 0x0500, METHOD_BUFFERED, FILE_ANY_ACCESS)
    IOCTL_STORAGE_QUERY_PROPERTY = 0x002D1400

    kernel32 = ctypes.windll.kernel32

    # --- 打开 PhysicalDrive0 ---
    # 使用原始字符串避免转义问题: r"\\.\PhysicalDrive0"
    device_path = "\x5c\x5c\x2e\x5cPhysicalDrive0"

    handle = kernel32.CreateFileW(
        device_path,
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        logger.warning("无法打开 \\\\\\.PhysicalDrive0 (权限不足或不存在)")
        return ""

    try:
        # --- STORAGE_PROPERTY_QUERY (PropertyId=StorageDeviceProperty, QueryType=PropertyStandardQuery) ---
        class STORAGE_PROPERTY_QUERY(ctypes.Structure):
            _fields_ = [
                ("PropertyId", ctypes.wintypes.DWORD),
                ("QueryType", ctypes.wintypes.DWORD),
                ("AdditionalParameters", ctypes.c_byte * 1),
            ]

        query = STORAGE_PROPERTY_QUERY()
        query.PropertyId = 0  # StorageDeviceProperty
        query.QueryType = 0  # PropertyStandardQuery
        query.AdditionalParameters = (ctypes.c_byte * 1)(0)

        # --- 输出缓冲区 (足够大) ---
        out_buffer_size = 4096
        out_buffer = ctypes.create_string_buffer(out_buffer_size)
        bytes_returned = ctypes.wintypes.DWORD(0)

        # --- DeviceIoControl ---
        result = kernel32.DeviceIoControl(
            handle,
            IOCTL_STORAGE_QUERY_PROPERTY,
            ctypes.byref(query),
            ctypes.sizeof(query),
            out_buffer,
            out_buffer_size,
            ctypes.byref(bytes_returned),
            None,
        )

        if not result:
            logger.warning("DeviceIoControl 查询硬盘序列号失败")
            return ""

        # --- 解析 STORAGE_DEVICE_DESCRIPTOR ---
        class STORAGE_DEVICE_DESCRIPTOR(ctypes.Structure):
            _fields_ = [
                ("Version", ctypes.wintypes.DWORD),
                ("Size", ctypes.wintypes.DWORD),
                ("DeviceType", ctypes.c_byte),
                ("DeviceTypeModifier", ctypes.c_byte),
                ("RemovableMedia", ctypes.c_byte),
                ("CommandQueueing", ctypes.c_byte),
                ("VendorIdOffset", ctypes.wintypes.DWORD),
                ("ProductIdOffset", ctypes.wintypes.DWORD),
                ("ProductRevisionOffset", ctypes.wintypes.DWORD),
                ("SerialNumberOffset", ctypes.wintypes.DWORD),
                ("BusType", ctypes.wintypes.DWORD),
                ("RawPropertiesLength", ctypes.wintypes.DWORD),
                ("RawDeviceProperties", ctypes.c_byte * 1),
            ]

        descriptor = STORAGE_DEVICE_DESCRIPTOR.from_buffer(out_buffer)
        serial_offset = descriptor.SerialNumberOffset

        if serial_offset == 0:
            logger.warning("硬盘序列号偏移量为 0，无法获取序列号")
            return ""

        # 序列号在偏移位置，以 null 结尾的 ASCII/UTF-16LE 字符串
        raw_bytes = out_buffer.raw
        null_pos = raw_bytes.find(b"\x00", serial_offset)
        if null_pos == -1:
            serial_bytes = raw_bytes[serial_offset:]
        else:
            serial_bytes = raw_bytes[serial_offset:null_pos]

        serial = serial_bytes.decode("utf-8", errors="replace").strip()
        if serial:
            logger.info(f"硬盘物理序列号已读取: {serial[:8]}...")
            return serial

        logger.warning("硬盘序列号内容为空")
        return ""

    finally:
        kernel32.CloseHandle(handle)


def generate_hardware_fingerprint() -> str:
    """
    生成机器硬件指纹（方案B：硬盘物理序列号）。

    策略:
      Windows: 通过 Win32 API (CreateFile + DeviceIoControl) 读取
      \\.\\\\PhysicalDrive0 的序列号，SHA-256 哈希生成指纹
      绝不使用 WMI/wmic

      Linux/macOS: 回退到主机名+架构的组合

    Returns:
        64 字符 hex 字符串 (SHA-256 全长度)
    """
    if platform.system() == "Windows":
        serial = _get_physical_disk_serial_win32()
        if serial:
            fingerprint = hashlib.sha256(serial.encode("utf-8")).hexdigest()
            logger.info(f"硬件指纹已生成 (硬盘序列号) : {fingerprint[:16]}...")
            return fingerprint
        logger.warning("Win32 API 获取硬盘序列号失败，回退到主机名")

    # 回退：主机名 + 机器架构（跨平台兼容）
    raw = f"{platform.node() or 'unknown'}|{platform.machine() or 'unknown'}"
    fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    logger.warning(f"硬件指纹使用回退方案 : {fingerprint[:16]}...")
    return fingerprint


def generate_rtsp_url(model: str, ip: str, rtsp_port: int, username: str, password: str) -> str:
    """根据设备型号自动生成RTSP地址"""
    if model == "大华":
        return f"rtsp://{username}:{password}@{ip}:{rtsp_port}/cam/realmonitor?channel=1&subtype=0"
    elif model == "海康威视":
        return f"rtsp://{username}:{password}@{ip}:{rtsp_port}/Streaming/Channels/101"
    else:
        return f"rtsp://{username}:{password}@{ip}:{rtsp_port}/live"


def model_to_dict(model_instance) -> dict:
    """将 SQLAlchemy 模型实例转换为字典"""
    if model_instance is None:
        return None
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        result[column.name] = value
    return result


def models_to_list(model_instances) -> list:
    """将 SQLAlchemy 模型实例列表转换为字典列表"""
    return [model_to_dict(m) for m in model_instances]


def success_response(data=None, message: str = None, status_code: int = 200) -> dict:
    """构建成功响应"""
    response = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


def error_response(message: str, status_code: int = 400) -> dict:
    """构建错误响应"""
    return {"success": False, "message": message}
