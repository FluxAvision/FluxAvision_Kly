"""
多路视频流测试 API 接口。

用于：
- 创建/移除测试设备（合成视频流）
- 查询测试状态
"""
import logging

from fastapi import APIRouter
from test_stream_harness import test_harness
from utils import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test/streams", tags=["测试工具"])


@router.get("/status")
async def get_test_status():
    """查询测试设备状态。"""
    return success_response(test_harness.get_status())


@router.post("/create")
async def create_test_devices(count: int = 2):
    """创建指定数量的测试设备。"""
    if count < 1 or count > 16:
        return error_response("数量范围为 1-16")
    devices = test_harness.create_test_devices(count)
    return success_response({
        "created": len(devices),
        "devices": devices,
        "totalActive": test_harness.device_count,
    })


@router.post("/remove/{device_id}")
async def remove_test_device(device_id: str):
    """移除指定测试设备。"""
    test_harness.remove_test_device(device_id)
    return success_response({"deviceId": device_id})


@router.post("/remove-all")
async def remove_all_test_devices():
    """移除所有测试设备。"""
    test_harness.remove_all()
    return success_response({"removed": True})
