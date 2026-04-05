"""
RTSP 视频流 API 端点（基于 OpenCV + MJPEG）

提供三种接口：
  1. MJPEG 流:  GET /api/devices/{device_id}/stream
     - 返回 multipart/x-mixed-replace 格式的连续 JPEG 帧
     - 浏览器 <img> 标签可直接显示
     - 适用于实时监控和大屏展示

  2. 单帧快照:  GET /api/devices/{device_id}/snapshot
     - 返回单张 JPEG 图片
     - 适用于设备缩略图、状态检查
     - 支持缓存控制

  3. 流状态:   GET /api/devices/{device_id}/stream/status
     - 返回 JSON 格式的流状态信息

技术方案：
  OpenCV VideoCapture → JPEG编码 → HTTP响应

  相比 FFmpeg + mpegts.js 方案：
  - 不需要额外的 JS 库
  - 不需要 MSE (Media Source Extensions)
  - 浏览器原生支持 MJPEG（<img> 标签直接用）
  - 更简单、更稳定、更兼容
  - 延迟约 100-300ms（满足实时监控需求）

  注意事项：
  - MJPEG 不包含音频（客流统计系统不需要音频）
  - 带宽消耗略高于 H.264（但摄像头数量有限，可接受）
  - 需要安装 opencv-python-headless（无需 GUI 依赖）
"""
import asyncio
import logging
import time
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, Response

from database import get_session_factory
from models import Device
from utils import success_response, error_response
from stream_manager import stream_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/devices", tags=["视频流"])

# MJPEG 边界字符串
MJPEG_BOUNDARY = b"--frameboundary"


@router.get("/{device_id}/stream")
async def get_device_stream(device_id: str, request: Request):
    """
    获取设备 RTSP 实时视频流（MJPEG 格式）

    浏览器端使用方法：
      <img src="/api/devices/{deviceId}/stream" />

    该端点返回 multipart/x-mixed-replace 格式的连续 JPEG 帧，
    浏览器 <img> 标签会自动更新显示最新帧。
    """
    # 1. 查找设备信息
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = session.query(Device).filter(Device.id == device_id).first()
        if not device:
            return error_response("设备不存在", 404)
        rtsp_url = device.rtspUrl
        device_name = device.name

    # 2. 注册客户端
    client_id = f"{uuid.uuid4().hex[:8]}_{int(time.time())}"
    already_running = stream_manager.add_client(device_id, client_id)

    if not already_running:
        # 启动摄像头采集
        started = stream_manager.start_camera(device_id, rtsp_url)
        if not started:
            stream_manager.remove_client(device_id, client_id)
            return error_response("无法连接摄像头", 500)

    logger.info(f"[视频流] 新连接: 设备={device_name}({device_id}), 客户端={client_id}")

    async def generate_mjpeg():
        """生成 MJPEG 流（multipart/x-mixed-replace 格式）"""
        try:
            while True:
                # 检查客户端是否断开
                if await request.is_disconnected():
                    logger.info(f"[视频流] 客户端 {client_id} 断开连接")
                    break

                # 获取 JPEG 帧
                jpeg_bytes = await asyncio.get_event_loop().run_in_executor(
                    None, stream_manager.get_jpeg_frame, device_id
                )

                if jpeg_bytes:
                    # MJPEG 格式: boundary + Content-Type + 空行 + JPEG数据 + \r\n
                    yield (
                        MJPEG_BOUNDARY + b"\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(jpeg_bytes)).encode() + b"\r\n"
                        b"\r\n" + jpeg_bytes + b"\r\n"
                    )

                # 控制帧率 (~25fps)
                await asyncio.sleep(0.04)

        except asyncio.CancelledError:
            logger.info(f"[视频流] 生成器取消: 设备={device_name}")
        except Exception as e:
            logger.error(f"[视频流] 生成器异常: {e}")
        finally:
            stream_manager.remove_client(device_id, client_id)
            logger.info(f"[视频流] 客户端 {client_id} 已清理")

    return StreamingResponse(
        generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frameboundary",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{device_id}/snapshot")
async def get_device_snapshot(device_id: str):
    """
    获取设备当前画面快照（单张 JPEG）

    返回当前摄像头的最新一帧画面，用于：
    - 设备列表缩略图
    - 设备状态检查
    - 手动刷新画面
    """
    # 查找设备
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = session.query(Device).filter(Device.id == device_id).first()
        if not device:
            return error_response("设备不存在", 404)

    # 如果没有正在采集，临时启动
    if not stream_manager.is_streaming(device_id):
        client_id = f"snap_{uuid.uuid4().hex[:8]}"
        stream_manager.add_client(device_id, client_id)
        stream_manager.start_camera(device_id, device.rtspUrl)
        # 等待第一帧
        await asyncio.sleep(1.0)

    # 获取 JPEG 帧
    jpeg_bytes = await asyncio.get_event_loop().run_in_executor(
        None, stream_manager.get_jpeg_frame, device_id
    )

    if not jpeg_bytes:
        return Response(
            content=_create_minimal_jpeg(),
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"},
        )

    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "max-age=1"},
    )


def _create_minimal_jpeg() -> bytes:
    """创建一个最小的有效 JPEG 图片（1x1 黑色像素）"""
    return bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00,
        0x08, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
        0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00,
        0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01,
        0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03,
        0x04, 0x05, 0x06, 0x07, 0x08, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00,
        0x00, 0x3F, 0x00, 0x7B, 0x40, 0x01, 0xB7, 0x40, 0x00, 0x00, 0x00, 0x00,
        0xFF, 0xD9,
    ])


@router.get("/{device_id}/stream/status")
async def get_stream_status(device_id: str):
    """获取设备视频流状态"""
    info = stream_manager.get_stream_info(device_id)

    # 检查 OpenCV 是否可用
    try:
        import cv2
        opencv_version = cv2.__version__
    except ImportError:
        opencv_version = None

    return success_response({
        "deviceId": device_id,
        **info,
        "opencvVersion": opencv_version,
    })
