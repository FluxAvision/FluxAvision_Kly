"""
多路视频流测试工具。

在不依赖真实 RTSP 摄像头的情况下，生成模拟视频流。
每路生成不同的彩色测试图案（颜色条 + 设备编号 + 跳动数字），
通过 StreamManager 注入，使用相同的 WebSocket/Snapshot 接口提供。
"""
import logging
import threading
import time
import os

logger = logging.getLogger(__name__)

# 设备数量上限
MAX_TEST_DEVICES = 16

# 测试设备命名前缀
TEST_DEVICE_PREFIX = "test-cam-"


class TestStreamHarness:
    """向 StreamManager 注入模拟视频流。"""

    def __init__(self):
        self._active_devices = set()
        self._lock = threading.Lock()

    def create_test_devices(self, count: int) -> list[dict]:
        """
        创建 N 个模拟设备。
        每个设备的 RTSP URL 使用特殊标记 "test://" 前缀，
        StreamManager 检测到后会自动使用合成帧生成器。
        """
        from stream_manager import stream_manager

        result = []
        with self._lock:
            for i in range(count):
                device_id = f"{TEST_DEVICE_PREFIX}{i + 1:02d}"
                if device_id in self._active_devices:
                    continue

                # 用特殊 URL 标记测试流
                test_url = f"test://synthetic-camera-{i + 1:02d}"
                ok = stream_manager.start_camera(device_id, test_url)
                if ok:
                    self._active_devices.add(device_id)
                    result.append({
                        "id": device_id,
                        "name": f"测试摄像头 {i + 1:02d}",
                        "url": test_url,
                        "index": i + 1,
                    })
                    logger.info(f"[TestHarness] 创建测试设备: {device_id}")
                else:
                    logger.error(f"[TestHarness] 创建测试设备失败: {device_id}")

        return result

    def remove_test_device(self, device_id: str):
        """移除单个测试设备。"""
        from stream_manager import stream_manager

        with self._lock:
            if device_id in self._active_devices:
                stream_manager._release_camera(device_id)
                self._active_devices.discard(device_id)
                logger.info(f"[TestHarness] 移除测试设备: {device_id}")

    def remove_all(self):
        """移除所有测试设备。"""
        from stream_manager import stream_manager

        with self._lock:
            for device_id in list(self._active_devices):
                stream_manager._release_camera(device_id)
                self._active_devices.discard(device_id)
            logger.info("[TestHarness] 已移除所有测试设备")

    @property
    def device_count(self) -> int:
        return len(self._active_devices)

    def get_device_ids(self) -> list[str]:
        return sorted(self._active_devices)

    def get_status(self) -> dict:
        from stream_manager import stream_manager

        result = {
            "totalCameraSlots": 16,
            "usedSlots": len(self._active_devices),
            "activeTestDevices": self._active_devices.copy(),
        }
        result["streamInfos"] = {}
        for device_id in self._active_devices:
            result["streamInfos"][device_id] = stream_manager.get_stream_info(device_id)
        return result


# 全局实例
test_harness = TestStreamHarness()
