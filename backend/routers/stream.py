"""
视频流接口。

当前方案：
1. WebSocket 推送二进制 JPEG 帧，作为实时预览主路径。
2. Snapshot 提供单帧降级能力。
3. 保留 MJPEG HTTP 流，兼容旧调用。
"""

import asyncio
import logging
import time
import uuid

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse

from database import get_session_factory
from models import Device
from stream_manager import stream_manager
from utils import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/devices", tags=["视频流"])

MJPEG_BOUNDARY = b"--frameboundary"
WS_FRAME_INTERVAL = 1 / 15


def _get_device(device_id: str):
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        return session.query(Device).filter(Device.id == device_id).first()


def _ensure_stream_started(device_id: str, rtsp_url: str, client_id: str) -> bool:
    already_running = stream_manager.add_client(device_id, client_id)
    if already_running:
        return True

    started = stream_manager.start_camera(device_id, rtsp_url)
    if not started:
        stream_manager.remove_client(device_id, client_id)
        return False
    return True


@router.websocket("/{device_id}/stream/ws")
async def get_device_stream_ws(websocket: WebSocket, device_id: str):
    """通过 WebSocket 推送二进制 JPEG 帧。"""
    device = _get_device(device_id)
    if not device:
        await websocket.close(code=1008, reason="设备不存在")
        return

    await websocket.accept()
    client_id = f"ws_{uuid.uuid4().hex[:8]}_{int(time.time())}"

    if not _ensure_stream_started(device_id, device.rtspUrl, client_id):
        await websocket.close(code=1011, reason="无法连接摄像头")
        return

    logger.info(f"[视频流] WebSocket 已连接: 设备={device.name}({device_id}), 客户端={client_id}")
    last_frame_count = -1

    try:
        while True:
            jpeg_bytes, frame_count = await asyncio.get_event_loop().run_in_executor(
                None,
                stream_manager.get_jpeg_frame_with_meta,
                device_id,
            )

            if jpeg_bytes and frame_count != last_frame_count:
                await websocket.send_bytes(jpeg_bytes)
                last_frame_count = frame_count

            await asyncio.sleep(WS_FRAME_INTERVAL)
    except WebSocketDisconnect:
        logger.info(f"[视频流] WebSocket 已断开: 设备={device.name}({device_id}), 客户端={client_id}")
    except Exception as e:
        logger.error(f"[视频流] WebSocket 推流异常: 设备={device_id}, 错误={e}")
    finally:
        stream_manager.remove_client(device_id, client_id)


@router.get("/{device_id}/stream")
async def get_device_stream(device_id: str, request: Request):
    """兼容旧版 MJPEG 流接口。"""
    device = _get_device(device_id)
    if not device:
        return error_response("设备不存在", 404)

    client_id = f"http_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    if not _ensure_stream_started(device_id, device.rtspUrl, client_id):
        return error_response("无法连接摄像头", 500)

    logger.info(f"[视频流] MJPEG 已连接: 设备={device.name}({device_id}), 客户端={client_id}")

    async def generate_mjpeg():
        try:
            while True:
                if await request.is_disconnected():
                    break

                jpeg_bytes = await asyncio.get_event_loop().run_in_executor(
                    None,
                    stream_manager.get_jpeg_frame,
                    device_id,
                )

                if jpeg_bytes:
                    yield (
                        MJPEG_BOUNDARY + b"\r\n"
                        b"Content-Type: image/jpeg\r\n"
                        b"Content-Length: " + str(len(jpeg_bytes)).encode() + b"\r\n"
                        b"\r\n" + jpeg_bytes + b"\r\n"
                    )

                await asyncio.sleep(WS_FRAME_INTERVAL)
        finally:
            stream_manager.remove_client(device_id, client_id)

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
    """返回当前设备的单帧 JPEG。"""
    device = _get_device(device_id)
    if not device:
        return error_response("设备不存在", 404)

    if not stream_manager.is_streaming(device_id):
        client_id = f"snap_{uuid.uuid4().hex[:8]}"
        stream_manager.add_client(device_id, client_id)
        stream_manager.start_camera(device_id, device.rtspUrl)
        await asyncio.sleep(1.0)

    jpeg_bytes = await asyncio.get_event_loop().run_in_executor(
        None,
        stream_manager.get_jpeg_frame,
        device_id,
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
    """返回一个最小可显示的 JPEG。"""
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
    """返回当前设备流状态。"""
    info = stream_manager.get_stream_info(device_id)

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
