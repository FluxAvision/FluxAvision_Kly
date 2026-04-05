"""
FluxaVision 客流统计系统 - 工具函数
"""
import hashlib
import platform
import uuid
import subprocess
from datetime import datetime


def _get_wmi_value(wmi_query: str, field: str, timeout: int = 5) -> str:
    """
    通过 WMI 查询获取硬件信息 (Windows 专用)

    参数:
        wmi_query: WMI 查询语句, 如 "SELECT UUID FROM Win32_ComputerSystemProduct"
        field: 要提取的字段名
        timeout: 超时秒数

    返回:
        查询结果字符串, 失败返回空字符串
    """
    try:
        result = subprocess.run(
            ["wmic", wmi_query],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            value = lines[1].strip()
            if value and value != field:
                return value
    except Exception:
        pass
    return ""


def _get_first_physical_disk_serial() -> str:
    """获取第一块物理硬盘序列号"""
    try:
        flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        result = subprocess.run(
            ["wmic", "diskdrive", "get", "SerialNumber"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=flags,
        )
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        # 跳过表头 "SerialNumber"
        if len(lines) >= 2:
            return lines[1]
    except Exception:
        pass
    return ""


def _get_primary_mac() -> str:
    """获取主网卡 MAC 地址 (通过 getmac 命令, 比 uuid.getnode() 更可靠)"""
    try:
        flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        result = subprocess.run(
            ["getmac", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=flags,
        )
        # CSV 格式: "设备名","MAC地址","传输类型"
        for line in result.stdout.strip().split("\n"):
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 2 and parts[1] != "N/A" and "-" in parts[1]:
                return parts[1].replace("-", "").upper()
    except Exception:
        pass
    return ""


def generate_hardware_fingerprint() -> str:
    """
    生成稳定的硬件指纹 (Windows 优化版)

    采集策略 (按稳定性排序):
      1. 主板 UUID (wmic csproduct get UUID) — 换主板才变
      2. BIOS 序列号 (wmic bios get SerialNumber) — 极少变
      3. CPU ProcessorId (wmic cpu get ProcessorId) — 换CPU才变
      4. 第一块物理硬盘序列号 — 换硬盘才变
      5. 主网卡 MAC (getmac) — 换网卡才变
      6. 主机名 (platform.node) — 可能被修改

    算法:
      所有采集到的非空因子用 | 连接
      SHA-256 → 取前 32 字符 → 大写

    稳定性保证:
      - 至少需要 2 个因子才生成有效指纹
      - 主板UUID + BIOS序列号 两个因子就能保证跨重启稳定
      - 更换个别硬件不影响指纹 (除非更换 >= 半数因子)
    """
    factors = []

    # === Windows WMI 查询 (最可靠) ===
    is_windows = platform.system() == "Windows"

    if is_windows:
        # 1. 主板 UUID (最稳定)
        board_uuid = _get_wmi_value("csproduct get UUID", "UUID")
        if board_uuid:
            factors.append(f"BOARD:{board_uuid}")

        # 2. BIOS 序列号
        bios_serial = _get_wmi_value("bios get SerialNumber", "SerialNumber")
        if bios_serial:
            factors.append(f"BIOS:{bios_serial}")

        # 3. CPU ProcessorId
        cpu_id = _get_wmi_value("cpu get ProcessorId", "ProcessorId")
        if cpu_id:
            factors.append(f"CPU:{cpu_id}")

        # 4. 硬盘序列号
        disk_serial = _get_first_physical_disk_serial()
        if disk_serial:
            factors.append(f"DISK:{disk_serial}")

        # 5. 主网卡 MAC
        mac = _get_primary_mac()
        if mac:
            factors.append(f"MAC:{mac}")

    # === 通用平台回退 (非 Windows 或 WMI 不可用) ===
    if not factors or len(factors) < 2:
        # 补充 platform 模块信息
        node = platform.node() or "unknown"
        machine = platform.machine() or "unknown"
        proc = platform.processor() or "unknown"
        mac_fallback = f"{uuid.getnode():012X}"

        if f"HOST:{node}" not in factors:
            factors.append(f"HOST:{node}")
        if f"ARCH:{machine}" not in factors:
            factors.append(f"ARCH:{machine}")
        if proc and f"PROC:{proc}" not in factors:
            factors.append(f"PROC:{proc}")
        if mac_fallback and f"MAC:{mac_fallback}" not in factors:
            factors.append(f"MAC:{mac_fallback}")

    # 去重并排序 (保证相同因子无论采集顺序如何都产生相同结果)
    factors = sorted(set(factors))

    if len(factors) < 2:
        # 极端情况: 所有硬件信息都获取不到
        factors = [f"FALLBACK:{platform.node()}", f"FALLBACK:{platform.machine()}"]

    # 带前缀 + SHA-256 + 截取32字符 + 大写
    raw = f"fluxavision-hw-{'|'.join(factors)}"
    fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32].upper()

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
