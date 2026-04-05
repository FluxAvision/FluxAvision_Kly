"""
FluxaVision 客流统计系统 - 大华SDK客流采集服务 (自动订阅 + 断线重连)

核心特性:
  1. 设备添加后自动订阅客流数据，无需手动触发
  2. 断线自动重连，指数退避策略 (3s → 6s → 12s → 24s → 30s)
  3. SDK层自动重连 + 自身重连线程双重保障
  4. 重连后自动恢复订阅 (重新 AttachVideoStatSummary)
  5. 服务重启后自动恢复所有设备采集
  6. 设备状态自动同步到数据库 (online/offline/warning)

技术架构:
  - 每个设备独立后台线程处理连接/重连
  - SDK回调在SDK内部线程执行，线程安全
  - login_id → device_id 双向映射，支持SDK回调查找设备
  - (ip, port) → device_id 辅助映射，处理SDK重连后login_id变化

SDK接口:
  - InitEx() → 初始化 + 设置断线回调
  - SetAutoReconnect() → 启用SDK内置TCP重连
  - LoginEx2() → 登录设备
  - AttachVideoStatSummary() → 订阅客流统计摘要
  - DetachVideoStatSummary() → 取消订阅
  - Logout() → 注销登录
  - Cleanup() → 释放SDK资源

依赖: NetSDK (大华官方SDK, 仅Windows)
  pip install upload/NetSDK-2.0.0.1-py3-none-win_amd64.whl
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入大华SDK (仅Windows环境可用)
_SDK_AVAILABLE = False
try:
    from NetSDK import NetClient, fDisConnect, fHaveReConnect
    from NetSDK.SDK_Callback import fVideoStatSumCallBack
    from NetSDK.SDK_Struct import (
        NET_IN_ATTACH_VIDEOSTAT_SUM,
        NET_OUT_ATTACH_VIDEOSTAT_SUM,
        NET_VIDEOSTAT_SUMMARY,
        NET_TIME_EX,
    )
    _SDK_AVAILABLE = True
except ImportError:
    logger.warning("大华NetSDK未安装, 客流采集功能不可用 (仅Windows环境支持)")


class DeviceConnection:
    """
    单设备的连接状态跟踪

    生命周期:
      disconnected → connecting → connected
                                 ↓ (断线)
                              reconnecting → connected (成功)
                                            → reconnecting (继续重试)

    线程安全: 通过 DahuaTrafficCollector._lock 保护所有字段读写
    """

    def __init__(self, device_id: str, ip: str, port: int,
                 username: str, password: str, channel: int = 0):
        self.device_id = device_id
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.channel = channel

        # SDK 连接句柄
        self.login_id: int = 0
        self.attach_handle: int = 0

        # 状态管理
        self.state: str = "disconnected"  # connecting | connected | reconnecting | disconnected | stopped
        self.reconnect_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.reconnect_attempts: int = 0
        self.last_error: str = ""
        self.last_connected_at: Optional[datetime] = None
        self.last_stat_time: Optional[datetime] = None

        # 回调引用 (防止被GC回收)
        self.stat_callback_ref = None


class DahuaTrafficCollector:
    """
    大华SDK客流数据采集器 (全局单例)

    设计要点:
      - 全局单例，一个SDK实例管理所有设备
      - 每个设备独立后台线程负责连接和重连
      - start() 是非阻塞的，立即返回，实际连接在后台线程执行
      - 断线后自动重连，指数退避 (3s → 6s → 12s → 24s → 30s max)
      - SDK内置重连 + 自身重连线程双重保障
    """

    # 重连参数
    INITIAL_BACKOFF = 3       # 初始等待秒数
    MAX_BACKOFF = 30           # 最大等待秒数
    BACKOFF_MULTIPLIER = 2     # 退避倍数
    MAX_RECONNECT_ATTEMPTS = 0 # 无限重试 (0=不限制)

    def __init__(self):
        self._initialized = False
        self._devices = {}           # device_id → DeviceConnection
        self._login_id_map = {}      # login_id → device_id (SDK回调查找)
        self._ip_port_map = {}       # (ip, port) → device_id (重连回调辅助查找)
        self._lock = threading.Lock()
        self._last_stat = {}         # device_id → 增量计算缓存
        self._sdk = None

    @property
    def available(self) -> bool:
        """SDK是否可用"""
        return _SDK_AVAILABLE

    # ==================== 公开接口 ====================

    def start(self, device_id: str, ip: str, port: int,
              username: str, password: str, channel: int = 0) -> bool:
        """
        启动指定设备的客流采集 (非阻塞)

        参数:
            device_id: 设备ID (对应数据库中的设备ID)
            ip: 设备IP地址
            port: SDK端口 (大华默认37777)
            username: 登录用户名
            password: 登录密码
            channel: 客流统计通道号 (从0开始)

        返回:
            True 已提交启动任务, False SDK不可用
        """
        if not self.available:
            logger.error(f"[{device_id}] SDK不可用, 无法启动采集")
            return False

        self._ensure_init()

        with self._lock:
            if device_id in self._devices:
                conn = self._devices[device_id]
                if conn.state in ("connected", "connecting"):
                    logger.info(f"[{device_id}] 已在采集中 (状态={conn.state}), 跳过")
                    return True
                # 旧连接处于重连/断线状态, 先停止旧的重连线程
                conn.stop_event.set()
                if conn.reconnect_thread and conn.reconnect_thread.is_alive():
                    conn.reconnect_thread.join(timeout=2)
                # 清理旧连接的登录状态
                self._cleanup_connection(conn)

            conn = DeviceConnection(device_id, ip, port, username, password, channel)
            self._devices[device_id] = conn
            self._ip_port_map[(ip, port)] = device_id

        # 后台线程执行实际连接
        thread = threading.Thread(
            target=self._connect_device,
            args=(device_id,),
            daemon=True,
            name=f"dahua-{device_id[:8]}",
        )
        thread.start()

        logger.info(f"[{device_id}] 已提交采集任务: {ip}:{port} (通道={channel})")
        return True

    def stop(self, device_id: str) -> bool:
        """
        停止指定设备的客流采集并清理所有资源

        返回:
            True 停止成功或未在采集中
        """
        with self._lock:
            conn = self._devices.pop(device_id, None)
            if not conn:
                logger.info(f"[{device_id}] 未在采集中")
                return True

            # 通知重连线程停止
            conn.state = "stopped"
            conn.stop_event.set()

            # 清理映射
            self._login_id_map.pop(conn.login_id, None)
            self._ip_port_map.pop((conn.ip, conn.port), None)

            login_id = conn.login_id
            attach_handle = conn.attach_handle
            stat_callback_ref = conn.stat_callback_ref

        # 停止重连线程
        if conn.reconnect_thread and conn.reconnect_thread.is_alive():
            conn.reconnect_thread.join(timeout=3)

        # 取消订阅 + 注销 (在锁外执行, 避免死锁)
        if self._initialized and self._sdk:
            if attach_handle:
                try:
                    self._sdk.DetachVideoStatSummary(attach_handle)
                except Exception as e:
                    logger.error(f"[{device_id}] 取消订阅失败: {e}")
            if login_id:
                try:
                    self._sdk.Logout(login_id)
                except Exception as e:
                    logger.error(f"[{device_id}] 注销失败: {e}")

        # 释放回调引用
        conn.stat_callback_ref = None

        self._last_stat.pop(device_id, None)
        logger.info(f"[{device_id}] 客流采集已停止, 资源已释放")
        return True

    def stop_all(self):
        """停止所有设备的客流采集"""
        device_ids = list(self._devices.keys())
        for device_id in device_ids:
            self.stop(device_id)

        if self._initialized and self._sdk:
            try:
                self._sdk.Cleanup()
            except Exception:
                pass
            self._initialized = False
            self._login_id_map.clear()
            self._ip_port_map.clear()
            logger.info("大华SDK已清理, 所有设备采集已停止")

    def start_all_from_db(self):
        """
        从数据库加载所有大华设备并自动启动采集

        在服务启动时调用, 恢复之前所有设备的采集状态
        """
        if not self.available:
            logger.warning("SDK不可用, 跳过自动启动设备采集")
            return

        try:
            from database import get_session_factory
            from models import Device

            SessionFactory = get_session_factory()
            with SessionFactory() as session:
                devices = session.query(Device).filter(
                    Device.model == "大华"
                ).all()

            if not devices:
                logger.info("无大华设备需要自动采集")
                return

            logger.info(f"自动启动 {len(devices)} 台大华设备客流采集...")
            for device in devices:
                self.start(
                    device_id=device.id,
                    ip=device.ip,
                    port=device.sdkPort or 37777,
                    username=device.username or "admin",
                    password=device.password or "",
                    channel=device.channel or 0,
                )

        except Exception as e:
            logger.error(f"自动启动设备采集失败: {e}", exc_info=True)

    def get_realtime_data(self, device_id: str) -> dict:
        """获取设备的实时客流数据 (内存缓存)"""
        with self._lock:
            conn = self._devices.get(device_id)
            collecting = conn is not None
            state = conn.state if conn else "unknown"
            stat = self._last_stat.get(device_id, {})

        return {
            "deviceId": device_id,
            "enteredToday": stat.get("entered_today", 0),
            "exitedToday": stat.get("exited_today", 0),
            "insideNow": stat.get("inside", 0),
            "lastUpdate": stat.get("time", datetime.min).isoformat() if stat.get("time") else None,
            "collecting": collecting,
            "state": state,
        }

    def get_all_realtime_data(self) -> list:
        """获取所有设备的实时客流数据"""
        result = []
        with self._lock:
            for device_id in self._devices:
                result.append(self.get_realtime_data(device_id))
        return result

    def get_device_collector_state(self, device_id: str) -> dict:
        """获取设备的采集器详细状态"""
        with self._lock:
            conn = self._devices.get(device_id)
            if not conn:
                return {"collecting": False, "state": "not_started"}

        return {
            "collecting": True,
            "state": conn.state,
            "reconnectAttempts": conn.reconnect_attempts,
            "lastError": conn.last_error,
            "lastConnectedAt": conn.last_connected_at.isoformat() if conn.last_connected_at else None,
            "lastStatTime": conn.last_stat_time.isoformat() if conn.last_stat_time else None,
        }

    # ==================== SDK 初始化 ====================

    def _ensure_init(self):
        """确保SDK已初始化 (单例)"""
        if not _SDK_AVAILABLE:
            raise RuntimeError("大华NetSDK未安装, 仅Windows环境支持")
        if not self._initialized:
            self._sdk = NetClient()
            # 设置断线回调
            disconnect_cb = fDisConnect(self._on_disconnect)
            self._sdk.InitEx(disconnect_cb)
            # 启用SDK内置TCP自动重连
            reconnect_cb = fHaveReConnect(self._on_reconnect)
            self._sdk.SetAutoReconnect(reconnect_cb)
            self._initialized = True
            logger.info("大华SDK初始化完成 (自动重连已启用)")

    # ==================== 连接管理 ====================

    def _connect_device(self, device_id: str):
        """
        执行设备登录和客流订阅 (在后台线程中运行)

        流程:
          1. LoginEx2() 登录
          2. AttachVideoStatSummary() 订阅客流
          3. 成功 → state=connected
          4. 失败 → 启动重连循环
        """
        with self._lock:
            conn = self._devices.get(device_id)
            if not conn or conn.state == "stopped":
                return

        conn.state = "connecting"
        self._update_device_status(device_id, "warning")

        try:
            # 1. 登录设备
            login_id, device_info, error_msg = self._sdk.LoginEx2(
                conn.ip, conn.port, conn.username, conn.password
            )

            if not login_id or login_id == 0:
                raise RuntimeError(f"登录失败: {error_msg or '未知错误'}")

            # 更新 login_id 映射
            with self._lock:
                if conn.state == "stopped":
                    self._sdk.Logout(login_id)
                    return
                conn.login_id = login_id
                self._login_id_map[login_id] = device_id

            logger.info(f"[{device_id}] 登录设备成功: {conn.ip}:{conn.port}")

            # 2. 订阅客流统计摘要
            attach_handle = self._attach_video_stat(conn)
            if not attach_handle:
                self._sdk.Logout(login_id)
                with self._lock:
                    self._login_id_map.pop(login_id, None)
                    conn.login_id = 0
                raise RuntimeError("订阅客流统计失败 (设备可能未配置NumberStat规则)")

            # 3. 标记为已连接
            with self._lock:
                if conn.state == "stopped":
                    self._sdk.DetachVideoStatSummary(attach_handle)
                    self._sdk.Logout(login_id)
                    return
                conn.attach_handle = attach_handle
                conn.state = "connected"
                conn.reconnect_attempts = 0
                conn.last_error = ""
                conn.last_connected_at = datetime.now()

            self._update_device_status(device_id, "online")
            logger.info(f"[{device_id}] 客流采集已启动 (通道={conn.channel})")

        except Exception as e:
            conn.last_error = str(e)
            logger.error(f"[{device_id}] 连接失败: {e}")
            # 启动断线重连循环
            if conn.state != "stopped":
                self._start_reconnect(device_id)

    def _start_reconnect(self, device_id: str):
        """
        启动断线重连循环 (指数退避)

        如果已有重连线程在运行, 会被停止后重新启动
        """
        with self._lock:
            conn = self._devices.get(device_id)
            if not conn or conn.state == "stopped":
                return
            if conn.state == "connected":
                return  # 已连接, 不需要重连

            # 停止旧的重连线程
            conn.stop_event.set()
            if conn.reconnect_thread and conn.reconnect_thread.is_alive():
                conn.reconnect_thread.join(timeout=2)

            conn.stop_event.clear()
            conn.state = "reconnecting"
            conn.reconnect_attempts += 1
            logger.info(
                f"[{device_id}] 启动重连 (第{conn.reconnect_attempts}次), "
                f"设备: {conn.ip}:{conn.port}"
            )

        self._update_device_status(device_id, "warning")

        thread = threading.Thread(
            target=self._reconnect_loop,
            args=(device_id,),
            daemon=True,
            name=f"reconnect-{device_id[:8]}",
        )
        thread.start()
        conn.reconnect_thread = thread

    def _reconnect_loop(self, device_id: str):
        """
        指数退避重连循环 (在后台守护线程中运行)

        策略:
          - 初始等待 3 秒
          - 每次失败等待时间翻倍 (3 → 6 → 12 → 24 → 30s)
          - 最大等待 30 秒
          - 无限重试直到成功或设备被停止
          - 每次重试前检查是否已被SDK自动重连
        """
        with self._lock:
            conn = self._devices.get(device_id)
            if not conn:
                return
            stop_event = conn.stop_event

        # 先清理旧连接
        with self._lock:
            self._cleanup_connection(conn)

        backoff = self.INITIAL_BACKOFF

        while not stop_event.is_set():
            # 检查是否已被SDK自动重连成功
            with self._lock:
                if conn.state in ("connected", "stopped") or device_id not in self._devices:
                    return

            logger.info(
                f"[{device_id}] 重连等待 {backoff}s "
                f"(第{conn.reconnect_attempts}次尝试, {conn.ip}:{conn.port})"
            )

            # 等待 (可被中断)
            if stop_event.wait(backoff):
                return  # 设备已被停止

            # 再次检查状态
            with self._lock:
                if conn.state in ("connected", "stopped") or device_id not in self._devices:
                    return

            # 尝试重新连接
            try:
                login_id, _, error_msg = self._sdk.LoginEx2(
                    conn.ip, conn.port, conn.username, conn.password
                )

                if not login_id or login_id == 0:
                    raise RuntimeError(f"登录失败: {error_msg or '连接被拒绝'}")

                with self._lock:
                    if conn.state == "stopped" or device_id not in self._devices:
                        self._sdk.Logout(login_id)
                        return
                    conn.login_id = login_id
                    self._login_id_map[login_id] = device_id

                # 重新订阅
                attach_handle = self._attach_video_stat(conn)
                if not attach_handle:
                    self._sdk.Logout(login_id)
                    with self._lock:
                        self._login_id_map.pop(login_id, None)
                        conn.login_id = 0
                    raise RuntimeError("重新订阅客流统计失败")

                # 重连成功
                with self._lock:
                    if conn.state == "stopped" or device_id not in self._devices:
                        self._sdk.DetachVideoStatSummary(attach_handle)
                        self._sdk.Logout(login_id)
                        return
                    conn.attach_handle = attach_handle
                    conn.state = "connected"
                    conn.reconnect_attempts = 0
                    conn.last_error = ""
                    conn.last_connected_at = datetime.now()

                self._update_device_status(device_id, "online")
                logger.info(f"[{device_id}] 断线重连成功! (ip={conn.ip}:{conn.port})")
                return  # 退出重连循环

            except Exception as e:
                conn.last_error = str(e)
                conn.reconnect_attempts += 1
                logger.warning(f"[{device_id}] 重连失败 (第{conn.reconnect_attempts}次): {e}")

            # 指数退避
            backoff = min(backoff * self.BACKOFF_MULTIPLIER, self.MAX_BACKOFF)

        # 循环退出 = 设备被停止
        logger.info(f"[{device_id}] 重连循环已退出 (设备被停止)")

    def _cleanup_connection(self, conn: DeviceConnection):
        """清理设备的旧连接资源 (必须在 _lock 内调用)"""
        if conn.login_id:
            self._login_id_map.pop(conn.login_id, None)
            conn.login_id = 0
        conn.attach_handle = 0
        conn.stat_callback_ref = None

    # ==================== SDK 回调 ====================

    def _on_disconnect(self, lLoginID, ip, port, user_data):
        """
        SDK断线回调 (在SDK内部线程执行)

        注意: 此回调只表示TCP连接断开, 不代表登录失效
        SDK可能会自动重连TCP并触发 _on_reconnect
        """
        with self._lock:
            device_id = self._login_id_map.get(lLoginID)
            if not device_id:
                # 尝试通过 ip:port 查找
                device_id = self._ip_port_map.get((ip, port))
                if not device_id:
                    logger.warning(f"未知设备断线: login_id={lLoginID} {ip}:{port}")
                    return

            conn = self._devices.get(device_id)
            if not conn or conn.state == "stopped":
                return

            logger.warning(f"[{device_id}] 设备断线: {ip}:{port} (login_id={lLoginID})")
            conn.state = "disconnected"
            conn.attach_handle = 0
            # 保留 login_id 映射, SDK重连可能复用

        self._update_device_status(device_id, "offline")
        # 启动重连 (如果SDK能自动重连, _on_reconnect会取消我们的重连)
        self._start_reconnect(device_id)

    def _on_reconnect(self, lLoginID, ip, port, user_data):
        """
        SDK自动重连成功回调 (在SDK内部线程执行)

        SDK在TCP层面重连成功后触发, 但客流订阅已失效
        需要重新执行 AttachVideoStatSummary
        """
        with self._lock:
            # 先尝试 login_id 查找 (可能已经更新过)
            device_id = self._login_id_map.get(lLoginID)
            if not device_id:
                # 通过 ip:port 查找
                device_id = self._ip_port_map.get((ip, port))
                if not device_id:
                    logger.info(f"未知设备SDK重连: login_id={lLoginID} {ip}:{port}")
                    return

            conn = self._devices.get(device_id)
            if not conn or conn.state == "stopped":
                return
            if conn.state == "connected":
                # 已连接 (可能我们的重连线程先成功了), 跳过
                logger.info(f"[{device_id}] SDK重连回调但已处于连接状态, 跳过")
                return

            logger.info(
                f"[{device_id}] SDK自动重连成功: {ip}:{port} "
                f"(旧login={conn.login_id} → 新login={lLoginID})"
            )

            # 更新 login_id 映射
            if conn.login_id and conn.login_id != lLoginID:
                self._login_id_map.pop(conn.login_id, None)
            conn.login_id = lLoginID
            self._login_id_map[lLoginID] = device_id
            conn.state = "connected"
            conn.reconnect_attempts = 0
            conn.last_error = ""
            conn.last_connected_at = datetime.now()

            # 通知我们的重连线程停止
            conn.stop_event.set()

        # 重新订阅客流统计
        try:
            attach_handle = self._attach_video_stat(conn)
            if attach_handle:
                with self._lock:
                    if conn.state == "stopped":
                        return
                    conn.attach_handle = attach_handle
                self._update_device_status(device_id, "online")
                logger.info(f"[{device_id}] SDK重连后客流订阅恢复成功")
            else:
                raise RuntimeError("AttachVideoStatSummary 返回空句柄")

        except Exception as e:
            logger.error(f"[{device_id}] SDK重连后重新订阅失败: {e}")
            conn.last_error = f"重连后订阅失败: {e}"
            conn.state = "reconnecting"
            conn.stop_event.clear()
            # 订阅失败, 启动手动重连
            self._start_reconnect(device_id)

    # ==================== 客流数据订阅 ====================

    def _attach_video_stat(self, conn: DeviceConnection) -> Optional[int]:
        """
        订阅客流统计摘要 (AttachVideoStatSummary)

        回调数据 NET_VIDEOSTAT_SUMMARY:
          - stuEnteredSubtotal.nToday: 今日进入累计
          - stuEnteredSubtotal.nHour:  本小时进入累计
          - stuExitedSubtotal.nToday:  今日离开累计
          - stuExitedSubtotal.nHour:   本小时离开累计
          - nInsidePeopleNum:          当前区域内人数
          - stuTime:                   统计时间 (NET_TIME_EX)
          - nChannelID:                通道号

        前置条件: 设备上需要配置好 NumberStat (人数统计) 规则
        """
        try:
            device_id = conn.device_id

            # 创建回调函数 — 必须保持引用防止GC回收
            def stat_callback(lAttachHandle, pStatBuf, dwBufLen, dwUser):
                try:
                    stat = pStatBuf.contents if pStatBuf else None
                    if stat:
                        self._on_stat_update(device_id, stat)
                except Exception as e:
                    logger.error(f"[{device_id}] 回调处理异常: {e}")

            # 保存回调引用
            callback_wrapper = fVideoStatSumCallBack(stat_callback)
            conn.stat_callback_ref = callback_wrapper

            # 构建输入参数
            in_param = NET_IN_ATTACH_VIDEOSTAT_SUM()
            in_param.dwSize = 20  # ctypes.sizeof(NET_IN_ATTACH_VIDEOSTAT_SUM)
            in_param.nChannel = conn.channel
            in_param.cbVideoStatSum = callback_wrapper
            in_param.dwUser = 0
            in_param.szSubClassID = b"NumberStat\x00"

            # 构建输出参数
            out_param = NET_OUT_ATTACH_VIDEOSTAT_SUM()
            out_param.dwSize = 4

            # 执行订阅
            handle = self._sdk.AttachVideoStatSummary(
                conn.login_id, in_param, out_param, 5000
            )
            return handle

        except Exception as e:
            logger.error(f"[{conn.device_id}] AttachVideoStatSummary 异常: {e}")
            return None

    def _on_stat_update(self, device_id: str, stat):
        """
        客流统计回调处理 (在SDK内部线程执行)

        增量计算逻辑:
          1. 获取本次回调的累计值 (nToday)
          2. 与上次回调的累计值做差, 得到增量
          3. 小时切换时, 使用 nHour (本小时累计) 作为增量
          4. 增量 > 0 时写入数据库 (upsert)
        """
        try:
            entered_today = stat.stuEnteredSubtotal.nToday
            exited_today = stat.stuExitedSubtotal.nToday
            inside_now = stat.nInsidePeopleNum
            entered_hour = stat.stuEnteredSubtotal.nHour
            exited_hour = stat.stuExitedSubtotal.nHour

            # 解析统计时间
            t = stat.stuTime
            stat_time = datetime(t.dwYear, t.dwMonth, t.dwDay,
                                 t.dwHour, t.dwMinute, t.dwSecond)

            # 计算增量
            last = self._last_stat.get(device_id, {})
            prev_entered_today = last.get("entered_today", 0)
            prev_exited_today = last.get("exited_today", 0)
            prev_hour = last.get("hour", -1)

            delta_in = max(0, entered_today - prev_entered_today) if prev_entered_today > 0 else 0
            delta_out = max(0, exited_today - prev_exited_today) if prev_exited_today > 0 else 0

            # 小时切换时, 重置使用小时累计值
            current_hour = stat_time.hour
            if current_hour != prev_hour and prev_hour >= 0:
                delta_in = entered_hour
                delta_out = exited_hour

            # 更新缓存
            self._last_stat[device_id] = {
                "entered_today": entered_today,
                "exited_today": exited_today,
                "inside": inside_now,
                "hour": current_hour,
                "time": stat_time,
            }

            # 更新连接的最后数据时间
            with self._lock:
                conn = self._devices.get(device_id)
                if conn:
                    conn.last_stat_time = stat_time

            # 有增量时写入数据库
            if delta_in > 0 or delta_out > 0:
                self._save_traffic_record(
                    device_id=device_id,
                    date_str=stat_time.strftime("%Y-%m-%d"),
                    hour=current_hour,
                    count_in=delta_in,
                    count_out=delta_out,
                )

            # 日志 (每分钟最多一条)
            now = datetime.now()
            last_log_time = last.get("last_log_time")
            if not last_log_time or (now - last_log_time).total_seconds() > 60:
                logger.debug(
                    f"[{device_id}] 客流: 进={entered_today} 出={exited_today} "
                    f"在场={inside_now} 时间={stat_time}"
                )
                self._last_stat[device_id]["last_log_time"] = now

        except Exception as e:
            logger.error(f"[{device_id}] 处理客流数据异常: {e}")

    def _save_traffic_record(self, device_id: str, date_str: str,
                              hour: int, count_in: int, count_out: int):
        """
        保存客流记录到数据库 (Upsert)

        同一设备同一天同一小时, 累加进入/离开人数
        """
        try:
            from database import get_session_factory
            from models import TrafficRecord

            SessionFactory = get_session_factory()
            with SessionFactory() as session:
                record = session.query(TrafficRecord).filter_by(
                    deviceId=device_id,
                    date=date_str,
                    hour=hour,
                ).first()

                if record:
                    record.countIn = (record.countIn or 0) + count_in
                    record.countOut = (record.countOut or 0) + count_out
                    record.updatedAt = datetime.utcnow()
                else:
                    record = TrafficRecord(
                        deviceId=device_id,
                        date=date_str,
                        hour=hour,
                        countIn=count_in,
                        countOut=count_out,
                    )
                    session.add(record)

                session.commit()

        except Exception as e:
            logger.error(f"[{device_id}] 保存客流记录失败: {e}")

    # ==================== 设备状态同步 ====================

    def _update_device_status(self, device_id: str, status: str):
        """
        更新设备在线状态到数据库

        状态映射:
          connected    → "online"   (在线采集中)
          connecting   → "warning"  (正在连接)
          reconnecting → "warning"  (断线重连中)
          disconnected → "offline"  (已断线)
          stopped      → "offline"  (已停止)
        """
        try:
            from database import get_session_factory
            from models import Device

            SessionFactory = get_session_factory()
            with SessionFactory() as session:
                device = session.query(Device).filter_by(id=device_id).first()
                if device and device.status != status:
                    device.status = status
                    session.commit()
                    logger.debug(f"[{device_id}] 设备状态更新: {status}")
        except Exception as e:
            logger.error(f"[{device_id}] 更新设备状态失败: {e}")

    def restart_device(self, device_id: str) -> bool:
        """
        重启设备的客流采集 (用于设备信息变更后)

        停止旧连接, 然后用新参数重新连接
        """
        with self._lock:
            conn = self._devices.get(device_id)
            if not conn:
                return False

            # 保存连接参数
            ip, port = conn.ip, conn.port
            username, password = conn.username, conn.password
            channel = conn.channel

        # 停止旧连接
        self.stop(device_id)

        # 用相同参数重新启动
        return self.start(device_id, ip, port, username, password, channel)


# ==================== 全局单例 ====================
dahua_collector = DahuaTrafficCollector()
