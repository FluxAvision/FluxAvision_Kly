"""
FluxaVision 客流统计系统 - OpenCV 视频流管理器

使用 OpenCV (cv2) 连接 RTSP 摄像头，读取视频帧并编码为 JPEG。
通过 HTTP MJPEG (Motion JPEG) 流推送给前端，浏览器 <img> 标签原生支持。

架构：
  摄像头(RTSP) → OpenCV VideoCapture → JPEG帧 → HTTP multipart/x-mixed-replace → <img>

特性：
  - 按需启动：只在有客户端观看时才连接 RTSP
  - 多路复用：同一 RTSP 源只开启一个 VideoCapture，支持多个客户端同时观看
  - 自动回收：无客户端观看时自动断开 RTSP 连接
  - 断线重连：RTSP 连接断开时自动重试
  - 资源限制：最大并发连接数限制，防止系统资源耗尽

OpenCV 参数：
  - 传输协议: TCP（比 UDP 更稳定，防丢包）
  - 缓冲区: 最小化（降低延迟）
  - JPEG 质量: 70（平衡清晰度和带宽）
  - 帧率: 跟随源帧率（通常 20-25fps）
"""
import asyncio
import logging
import time
import threading
from typing import Dict, Optional, Set, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ==================== 配置 ====================
MAX_STREAMS = 16          # 最大同时连接的摄像头路数
STREAM_IDLE_TIMEOUT = 60  # 无客户端超时自动关闭（秒）
RECONNECT_INTERVAL = 5    # RTSP 断线重连间隔（秒）
MAX_RECONNECT = 5         # 最大重连次数
JPEG_QUALITY = 70         # JPEG 压缩质量 (0-100)
FRAME_INTERVAL = 0.04     # 帧间隔 (秒)，约 25fps


@dataclass
class CameraSession:
    """单路摄像头会话（OpenCV VideoCapture 线程）"""
    device_id: str
    rtsp_url: str
    clients: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    last_client_at: float = field(default_factory=time.time)

    # OpenCV 相关
    cap: Optional[object] = None        # cv2.VideoCapture 实例
    capture_thread: Optional[threading.Thread] = None
    frame_lock: threading.Lock = field(default_factory=threading.Lock)
    latest_frame: Optional[object] = None  # cv2 numpy array
    last_frame_time: float = 0.0
    is_running: bool = False
    reconnect_count: int = 0
    frame_count: int = 0


class StreamManager:
    """
    RTSP → MJPEG 视频流管理器（基于 OpenCV）

    管理所有摄像头的 OpenCV VideoCapture 生命周期：
    - 每个摄像头一个后台线程持续读取帧
    - 多个 HTTP 客户端共享同一个帧缓冲
    - 无客户端时自动释放资源
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sessions: Dict[str, CameraSession] = {}
        self._sessions_lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        logger.info("StreamManager (OpenCV) 初始化完成")

    def start(self):
        """启动后台监控线程"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop, daemon=True, name="StreamMonitor"
            )
            self._monitor_thread.start()
            logger.info("StreamManager 后台监控线程已启动")

    def stop(self):
        """停止所有摄像头连接"""
        self._stop_event.set()
        with self._sessions_lock:
            for device_id in list(self._sessions.keys()):
                self._release_camera(device_id)
        logger.info("StreamManager 已停止所有流")

    def add_client(self, device_id: str, client_id: str) -> bool:
        """添加客户端，返回是否已有活跃的采集线程"""
        with self._sessions_lock:
            if device_id not in self._sessions:
                self._sessions[device_id] = CameraSession(
                    device_id=device_id,
                    rtsp_url="",
                )
            session = self._sessions[device_id]
            session.clients.add(client_id)
            session.last_client_at = time.time()
            return session.is_running

    def remove_client(self, device_id: str, client_id: str):
        """移除客户端"""
        with self._sessions_lock:
            if device_id in self._sessions:
                session = self._sessions[device_id]
                session.clients.discard(client_id)
                session.last_client_at = time.time()

    def start_camera(self, device_id: str, rtsp_url: str) -> bool:
        """
        启动摄像头采集线程

        Args:
            device_id: 设备ID
            rtsp_url: RTSP 地址

        Returns:
            True 启动成功, False 启动失败
        """
        with self._sessions_lock:
            session = self._sessions.get(device_id)
            if session and session.is_running:
                return True  # 已在运行

            if len(self._sessions) >= MAX_STREAMS:
                logger.error(f"已达最大摄像头路数: {MAX_STREAMS}")
                return False

            if device_id not in self._sessions:
                self._sessions[device_id] = CameraSession(
                    device_id=device_id,
                    rtsp_url=rtsp_url,
                )

            session = self._sessions[device_id]
            session.rtsp_url = rtsp_url
            session.is_running = True
            session.reconnect_count = 0
            session.capture_thread = threading.Thread(
                target=self._capture_loop,
                args=(device_id,),
                daemon=True,
                name=f"Camera-{device_id[:8]}",
            )
            session.capture_thread.start()
            logger.info(f"✓ 摄像头采集已启动: 设备={device_id}, RTSP={rtsp_url[:60]}...")
            return True

    def _capture_loop(self, device_id: str):
        """OpenCV 帧采集循环（后台线程）"""
        import cv2

        session = self._sessions.get(device_id)
        if not session:
            return

        while session.is_running:
            # 释放旧的 VideoCapture
            if session.cap is not None:
                try:
                    session.cap.release()
                except Exception:
                    pass
                session.cap = None

            # 创建新的 VideoCapture
            cap = cv2.VideoCapture(session.rtsp_url, cv2.CAP_FFMPEG)
            if not cap or not cap.isOpened():
                logger.error(f"无法打开 RTSP 流: {session.rtsp_url[:80]}")
                session.reconnect_count += 1
                if session.reconnect_count >= MAX_RECONNECT:
                    logger.error(f"设备 {device_id} RTSP 重连失败 {MAX_RECONNECT} 次, 放弃")
                    session.is_running = False
                    break
                # 等待后重试
                for _ in range(int(RECONNECT_INTERVAL / 0.5)):
                    if not session.is_running:
                        break
                    time.sleep(0.5)
                continue

            # 设置 OpenCV 参数（降低延迟）
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)          # 最小缓冲
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5秒连接超时
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)  # 10秒读取超时
            session.cap = cap
            session.reconnect_count = 0
            logger.info(f"✓ RTSP 连接成功: 设备={device_id}")

            # 持续读取帧
            frame_fail_count = 0
            while session.is_running:
                ret, frame = cap.read()
                if ret and frame is not None:
                    with session.frame_lock:
                        session.latest_frame = frame
                        session.last_frame_time = time.time()
                        session.frame_count += 1
                    frame_fail_count = 0
                    # 控制帧率
                    time.sleep(FRAME_INTERVAL)
                else:
                    frame_fail_count += 1
                    logger.warning(f"设备 {device_id} 读取帧失败 (连续 {frame_fail_count} 次)")
                    if frame_fail_count > 10:
                        logger.error(f"设备 {device_id} 连续读取失败过多, 断开重连")
                        break
                    time.sleep(0.5)

            # 清理
            try:
                cap.release()
            except Exception:
                pass
            session.cap = None

            # 如果还需要运行，等待后重连
            if session.is_running:
                session.reconnect_count += 1
                if session.reconnect_count >= MAX_RECONNECT:
                    logger.error(f"设备 {device_id} 重连次数耗尽, 停止采集")
                    session.is_running = False
                    break
                logger.info(f"设备 {device_id} {RECONNECT_INTERVAL}s 后重连 ({session.reconnect_count}/{MAX_RECONNECT})")
                for _ in range(int(RECONNECT_INTERVAL / 0.5)):
                    if not session.is_running:
                        break
                    time.sleep(0.5)

    def get_jpeg_frame(self, device_id: str) -> Optional[bytes]:
        """
        获取指定设备的最新 JPEG 帧

        Returns:
            JPEG 字节数据，如果无可用帧返回 None
        """
        import cv2

        session = self._sessions.get(device_id)
        if not session or not session.is_running:
            return None

        with session.frame_lock:
            frame = session.latest_frame
            if frame is None:
                return None
            # 检查帧是否太旧（超过 3 秒没更新）
            if time.time() - session.last_frame_time > 3.0:
                return None
            try:
                ret, jpeg_data = cv2.imencode('.jpg', frame, [
                    cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY,
                    cv2.IMWRITE_JPEG_OPTIMIZE, True,
                ])
                if ret:
                    return jpeg_data.tobytes()
            except Exception as e:
                logger.error(f"JPEG 编码失败 (设备={device_id}): {e}")
            return None

    def _release_camera(self, device_id: str):
        """释放摄像头资源"""
        session = self._sessions.get(device_id)
        if not session:
            return

        session.is_running = False

        # 等待采集线程结束
        if session.capture_thread and session.capture_thread.is_alive():
            session.capture_thread.join(timeout=5)

        # 释放 VideoCapture
        if session.cap is not None:
            try:
                session.cap.release()
            except Exception:
                pass
            session.cap = None

        session.latest_frame = None
        logger.info(f"✓ 摄像头已释放: 设备={device_id}")

    def get_client_count(self, device_id: str) -> int:
        """获取指定设备的客户端数量"""
        session = self._sessions.get(device_id)
        return len(session.clients) if session else 0

    def is_streaming(self, device_id: str) -> bool:
        """检查指定设备是否正在采集"""
        session = self._sessions.get(device_id)
        return session is not None and session.is_running

    def get_stream_info(self, device_id: str) -> dict:
        """获取流的详细信息"""
        session = self._sessions.get(device_id)
        if not session:
            return {"streaming": False, "clients": 0}
        return {
            "streaming": session.is_running,
            "clients": len(session.clients),
            "frameCount": session.frame_count,
            "lastFrameTime": session.last_frame_time,
            "reconnectCount": session.reconnect_count,
        }

    def _monitor_loop(self):
        """后台监控循环（检查超时、清理资源）"""
        while not self._stop_event.is_set():
            try:
                time.sleep(STREAM_IDLE_TIMEOUT / 3)
                now = time.time()

                with self._sessions_lock:
                    for device_id in list(self._sessions.keys()):
                        session = self._sessions[device_id]

                        # 无客户端超时
                        if len(session.clients) == 0:
                            idle = now - session.last_client_at
                            if idle > STREAM_IDLE_TIMEOUT:
                                logger.info(f"设备 {device_id} 无客户端 {idle:.0f}s, 释放资源")
                                self._release_camera(device_id)
                                del self._sessions[device_id]

            except Exception as e:
                logger.error(f"监控循环异常: {e}")


# 全局单例
stream_manager = StreamManager()
