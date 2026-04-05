"""
FluxaVision 视频流管理器。

目标：
1. 使用 OpenCV 采集 RTSP。
2. 每路设备只保留一个采集线程，供多个前端客户端复用。
3. 在采集线程中完成 JPEG 编码，避免每个客户端重复编码。
4. 优先保留最新帧，尽量降低预览延时。
"""

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ==================== 配置 ====================
MAX_STREAMS = 16
STREAM_IDLE_TIMEOUT = 60
RECONNECT_INTERVAL = 5
MAX_RECONNECT = 5
JPEG_QUALITY = 70
CAPTURE_IDLE_SLEEP = 0.005
STALE_FRAME_SECONDS = 3.0


@dataclass
class CameraSession:
    """单路摄像头会话。"""

    device_id: str
    rtsp_url: str
    clients: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    last_client_at: float = field(default_factory=time.time)

    cap: Optional[object] = None
    capture_thread: Optional[threading.Thread] = None
    frame_lock: threading.Lock = field(default_factory=threading.Lock)
    latest_frame: Optional[object] = None
    latest_jpeg: Optional[bytes] = None
    last_frame_time: float = 0.0
    is_running: bool = False
    reconnect_count: int = 0
    frame_count: int = 0


class StreamManager:
    """负责管理所有设备的视频采集与 JPEG 缓存。"""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        with cls._instance_lock:
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
        logger.info("StreamManager 初始化完成 (OpenCV)")

    def start(self):
        """启动后台监控线程。"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="StreamMonitor",
            )
            self._monitor_thread.start()
            logger.info("StreamManager 后台监控线程已启动")

    def stop(self):
        """停止所有视频流。"""
        self._stop_event.set()
        with self._sessions_lock:
            for device_id in list(self._sessions.keys()):
                self._release_camera(device_id)
        logger.info("StreamManager 已停止所有视频流")

    def add_client(self, device_id: str, client_id: str) -> bool:
        """注册客户端，返回当前设备流是否已经启动。"""
        with self._sessions_lock:
            session = self._sessions.get(device_id)
            if session is None:
                session = CameraSession(device_id=device_id, rtsp_url="")
                self._sessions[device_id] = session

            session.clients.add(client_id)
            session.last_client_at = time.time()
            return session.is_running

    def remove_client(self, device_id: str, client_id: str):
        """移除客户端。"""
        with self._sessions_lock:
            session = self._sessions.get(device_id)
            if session:
                session.clients.discard(client_id)
                session.last_client_at = time.time()

    def start_camera(self, device_id: str, rtsp_url: str) -> bool:
        """按需启动摄像头采集线程。"""
        with self._sessions_lock:
            session = self._sessions.get(device_id)
            if session and session.is_running:
                return True

            if len(self._sessions) >= MAX_STREAMS and device_id not in self._sessions:
                logger.error(f"已达到最大摄像头数量限制: {MAX_STREAMS}")
                return False

            if session is None:
                session = CameraSession(device_id=device_id, rtsp_url=rtsp_url)
                self._sessions[device_id] = session

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
            logger.info(f"摄像头采集已启动: 设备={device_id}")
            return True

    def _capture_loop(self, device_id: str):
        """持续采集最新帧并预编码为 JPEG。"""
        import cv2

        session = self._sessions.get(device_id)
        if not session:
            return

        # 尽量降低 FFmpeg 内部缓冲，优先拿到最新画面。
        os.environ.setdefault(
            "OPENCV_FFMPEG_CAPTURE_OPTIONS",
            "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay",
        )
        encode_params = [
            int(cv2.IMWRITE_JPEG_QUALITY), int(JPEG_QUALITY),
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,
        ]

        while session.is_running:
            if session.cap is not None:
                try:
                    session.cap.release()
                except Exception:
                    pass
                session.cap = None

            cap = cv2.VideoCapture(session.rtsp_url, cv2.CAP_FFMPEG)
            if not cap or not cap.isOpened():
                logger.error(f"无法打开 RTSP 流: {session.rtsp_url[:80]}")
                session.reconnect_count += 1
                if session.reconnect_count >= MAX_RECONNECT:
                    logger.error(f"设备 {device_id} RTSP 重连失败次数已耗尽")
                    session.is_running = False
                    break
                self._sleep_with_cancel(session, RECONNECT_INTERVAL)
                continue

            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
            session.cap = cap
            session.reconnect_count = 0
            logger.info(f"RTSP 连接成功: 设备={device_id}")

            frame_fail_count = 0
            while session.is_running:
                ret, frame = cap.read()
                if ret and frame is not None:
                    jpeg_bytes = None
                    try:
                        ok, jpeg_data = cv2.imencode(".jpg", frame, encode_params)
                        if ok:
                            jpeg_bytes = jpeg_data.tobytes()
                    except Exception as e:
                        logger.error(f"JPEG 编码失败 (设备={device_id}): {e}")

                    with session.frame_lock:
                        session.latest_frame = frame
                        session.latest_jpeg = jpeg_bytes
                        session.last_frame_time = time.time()
                        session.frame_count += 1

                    frame_fail_count = 0
                    time.sleep(CAPTURE_IDLE_SLEEP)
                else:
                    frame_fail_count += 1
                    logger.warning(f"设备 {device_id} 读取帧失败 (连续 {frame_fail_count} 次)")
                    if frame_fail_count > 10:
                        logger.error(f"设备 {device_id} 连续读取失败过多，准备重连")
                        break
                    time.sleep(0.5)

            try:
                cap.release()
            except Exception:
                pass
            session.cap = None

            if session.is_running:
                session.reconnect_count += 1
                if session.reconnect_count >= MAX_RECONNECT:
                    logger.error(f"设备 {device_id} 重连次数已耗尽，停止采集")
                    session.is_running = False
                    break
                logger.info(
                    f"设备 {device_id} 将在 {RECONNECT_INTERVAL}s 后重连 "
                    f"({session.reconnect_count}/{MAX_RECONNECT})"
                )
                self._sleep_with_cancel(session, RECONNECT_INTERVAL)

    def _sleep_with_cancel(self, session: CameraSession, seconds: int):
        """可中断等待。"""
        for _ in range(int(seconds / 0.5)):
            if not session.is_running:
                break
            time.sleep(0.5)

    def get_jpeg_frame(self, device_id: str) -> Optional[bytes]:
        """返回最新 JPEG 帧。"""
        frame_bytes, _ = self.get_jpeg_frame_with_meta(device_id)
        return frame_bytes

    def get_jpeg_frame_with_meta(self, device_id: str) -> Tuple[Optional[bytes], int]:
        """返回最新 JPEG 帧以及帧序号，便于 WebSocket 仅发送新帧。"""
        session = self._sessions.get(device_id)
        if not session or not session.is_running:
            return None, 0

        with session.frame_lock:
            if session.latest_jpeg is None:
                return None, session.frame_count
            if time.time() - session.last_frame_time > STALE_FRAME_SECONDS:
                return None, session.frame_count
            return session.latest_jpeg, session.frame_count

    def _release_camera(self, device_id: str):
        """释放摄像头资源。"""
        session = self._sessions.get(device_id)
        if not session:
            return

        session.is_running = False
        if session.capture_thread and session.capture_thread.is_alive():
            session.capture_thread.join(timeout=5)

        if session.cap is not None:
            try:
                session.cap.release()
            except Exception:
                pass
            session.cap = None

        with session.frame_lock:
            session.latest_frame = None
            session.latest_jpeg = None

        logger.info(f"摄像头资源已释放: 设备={device_id}")

    def get_client_count(self, device_id: str) -> int:
        """返回当前设备的客户端数量。"""
        session = self._sessions.get(device_id)
        return len(session.clients) if session else 0

    def is_streaming(self, device_id: str) -> bool:
        """判断设备流是否正在采集。"""
        session = self._sessions.get(device_id)
        return session is not None and session.is_running

    def get_stream_info(self, device_id: str) -> dict:
        """返回设备流状态。"""
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
        """定期回收长时间无客户端的流。"""
        while not self._stop_event.is_set():
            try:
                time.sleep(STREAM_IDLE_TIMEOUT / 3)
                now = time.time()

                with self._sessions_lock:
                    for device_id in list(self._sessions.keys()):
                        session = self._sessions[device_id]
                        if session.clients:
                            continue

                        idle = now - session.last_client_at
                        if idle > STREAM_IDLE_TIMEOUT:
                            logger.info(f"设备 {device_id} 空闲 {idle:.0f}s，释放视频资源")
                            self._release_camera(device_id)
                            del self._sessions[device_id]
            except Exception as e:
                logger.error(f"视频监控循环异常: {e}")


stream_manager = StreamManager()
