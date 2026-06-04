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
import sys
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

# ===== 优化参数 =====
# 预览流缩放宽度。将 RTSP 原始帧缩放到此宽度（保持宽高比），
# 大幅减少 JPEG 尺寸（约 80-90%）、网络传输量和浏览器解码开销。
# 设为 None 则不缩放（保留原始分辨率）。
SCALE_WIDTH = 640

# 采集线程目标帧率。不再编码每一帧，仅按此帧率编码最新帧。
# 通常 15fps 即可满足监控预览需求，降低 CPU 占用约 40-60%。
CAPTURE_FPS = 15

# 激进低延迟模式。开启后增加更多 FFmpeg 低延迟参数，
# 进一步降低 RTSP 内部缓冲区带来的延迟。
AGGRESSIVE_LOW_LATENCY = True


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
    # 用于帧率控制：上次编码的时间戳
    last_encode_time: float = 0.0


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
        """
        持续采集 RTSP 流，缩放画面后预编码为 JPEG。

        优化点：
        - 分辨率缩放：SCALE_WIDTH 控制预览宽度，大幅降低 JPEG 尺寸
        - 帧率控制：CAPTURE_FPS 控制编码频率，避免过度编码
        - 低延迟 FFmpeg：增加 max_delay/probesize 等选项降低 RTSP 缓冲
        """
        logger.info(f"[DEBUG] _capture_loop 已进入: 设备={device_id}")
        try:
            import cv2
            logger.info(f"[DEBUG] cv2 import 成功, 版本={cv2.__version__}, 文件={cv2.__file__}")
        except Exception as e:
            logger.error(f"[DEBUG] cv2 import 失败: {e}")
            return

        session = self._sessions.get(device_id)
        if not session:
            logger.error(f"[DEBUG] session 不存在: 设备={device_id}")
            return

        logger.info(f"[DEBUG] RTSP URL={session.rtsp_url}")

        # 尽量降低 FFmpeg 内部缓冲，优先拿到最新画面。
        ffmpeg_opts = "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay"
        if AGGRESSIVE_LOW_LATENCY:
            ffmpeg_opts += (
                "|probesize;32"
                "|analyzeduration;0"
                "|max_delay;0"
                "|reorder_queue_size;0"
                "|fflags;discardcorrupt"
            )
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", ffmpeg_opts)
        logger.info(
            f"[DEBUG] OPENCV_FFMPEG_CAPTURE_OPTIONS="
            f"{os.environ.get('OPENCV_FFMPEG_CAPTURE_OPTIONS')}"
        )

        encode_params = [
            int(cv2.IMWRITE_JPEG_QUALITY), int(JPEG_QUALITY),
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,
        ]

        # 帧率控制：相邻两帧编码的最小间隔
        min_frame_interval = 1.0 / CAPTURE_FPS

        while session.is_running:
            if session.cap is not None:
                try:
                    session.cap.release()
                except Exception:
                    pass
                session.cap = None

            logger.info(f"[DEBUG] 正在调用 cv2.VideoCapture: url={session.rtsp_url[:80]}")
            try:
                cap = cv2.VideoCapture(session.rtsp_url, cv2.CAP_FFMPEG)
                logger.info(
                    f"[DEBUG] VideoCapture 返回: cap={cap}, "
                    f"isOpened={cap.isOpened() if cap else 'N/A'}"
                )
            except Exception as e:
                logger.error(f"[DEBUG] VideoCapture 抛出异常: {e}")
                session.reconnect_count += 1
                self._sleep_with_cancel(session, RECONNECT_INTERVAL)
                continue

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
            # OPEN_TIMEOUT / READ_TIMEOUT 在部分 OpenCV 版本不支持，用 try 保护
            try:
                cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
            except Exception:
                pass
            session.cap = cap
            session.reconnect_count = 0
            session.last_encode_time = 0.0
            logger.info(f"RTSP 连接成功: 设备={device_id}")

            frame_fail_count = 0
            while session.is_running:
                ret, frame = cap.read()
                if ret and frame is not None:
                    now = time.time()

                    # 帧率控制：距上次编码不足最小间隔则跳过编码
                    if now - session.last_encode_time < min_frame_interval:
                        # 只更新帧计数，不编码 JPEG（节省 CPU）
                        session.frame_count += 1
                        time.sleep(CAPTURE_IDLE_SLEEP)
                        continue

                    # 分辨率缩放：如果设置了 SCALE_WIDTH 且帧宽超过限制
                    jpeg_bytes = None
                    try:
                        scale_frame = frame
                        if SCALE_WIDTH is not None:
                            h, w = frame.shape[:2]
                            if w > SCALE_WIDTH:
                                ratio = SCALE_WIDTH / w
                                new_w = int(w * ratio)
                                new_h = int(h * ratio)
                                scale_frame = cv2.resize(
                                    frame, (new_w, new_h),
                                    interpolation=cv2.INTER_LINEAR
                                )

                        ok, jpeg_data = cv2.imencode(".jpg", scale_frame, encode_params)
                        if ok:
                            jpeg_bytes = jpeg_data.tobytes()
                    except Exception as e:
                        logger.error(f"JPEG 编码失败 (设备={device_id}): {e}")

                    with session.frame_lock:
                        session.latest_frame = frame
                        session.latest_jpeg = jpeg_bytes
                        session.last_frame_time = now
                        session.frame_count += 1

                    session.last_encode_time = now
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
            "scaleWidth": SCALE_WIDTH,
            "targetFps": CAPTURE_FPS,
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
