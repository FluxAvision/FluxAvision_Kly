"""
多路视频流性能测试脚本。

测试流程：
1. 启动后端（如果未启动）
2. 创建 N 路测试流（合成帧模式）
3. 连接 N 个 WebSocket 消费者（模拟前端客户端）
4. 持续采集 CPU/内存/帧率指标
5. 输出测试报告

用法：
    python run_multi_stream_test.py [--count 4] [--duration 60] [--no-backend]
"""
import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
import signal
import psutil
import websocket
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("MultiStreamTest")

# ==================== 配置 ====================
API_BASE = "http://127.0.0.1:15678"
WS_BASE = "ws://127.0.0.1:15678"
TEST_DEVICE_PREFIX = "test-cam-"
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


class StreamConsumer:
    """模拟一个 WebSocket 视频流消费者。"""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.ws = None
        self.frame_count = 0
        self.fps = 0.0
        self.byte_count = 0
        self.running = False
        self._thread = None
        self._start_time = 0
        self._frame_times = []
        self._errors = 0

    def _run(self):
        url = f"{WS_BASE}/api/devices/{self.device_id}/stream/ws"
        self._start_time = time.time()
        self.running = True

        while self.running:
            try:
                ws = websocket.WebSocket()
                ws.connect(url, timeout=10)
                ws.settimeout(5)
                self.ws = ws
                logger.info(f"  [Consumer {self.device_id}] 已连接")

                while self.running:
                    try:
                        data = ws.recv()
                        if isinstance(data, bytes):
                            self.frame_count += 1
                            self.byte_count += len(data)
                            now = time.time()
                            self._frame_times.append(now)
                            # 只保留最近 5 秒的帧时间用于 FPS 计算
                            cutoff = now - 5.0
                            self._frame_times = [t for t in self._frame_times if t > cutoff]
                            if len(self._frame_times) > 1:
                                self.fps = len(self._frame_times) / (
                                    self._frame_times[-1] - self._frame_times[0]
                                )
                    except websocket.WebSocketTimeoutException:
                        continue
                    except Exception as e:
                        self._errors += 1
                        logger.warning(f"  [Consumer {self.device_id}] 接收错误: {e}")
                        break
            except Exception as e:
                self._errors += 1
                logger.warning(f"  [Consumer {self.device_id}] 连接失败: {e}")

            if self.running:
                time.sleep(2)  # 重连等待

        logger.info(f"  [Consumer {self.device_id}] 已停止 (帧数={self.frame_count}, 错误={self._errors})")

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True, name=f"Consumer-{self.device_id[:8]}")
        self._thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=5)


class PerformanceMonitor:
    """后端性能和系统资源监控。"""

    def __init__(self):
        self._running = False
        self._thread = None
        self.snapshots = []
        self.process = psutil.Process()

    def _run(self):
        while self._running:
            try:
                cpu_percent = self.process.cpu_percent(interval=0.5)
                mem_info = self.process.memory_info()
                mem_mb = mem_info.rss / 1024 / 1024

                # 获取 Python 线程数
                thread_count = self.process.num_threads()

                # Open connections (approximation for WebSocket/stream threads)
                open_fds = self.process.num_handles() if hasattr(self.process, 'num_handles') else 0

                snapshot = {
                    "time": time.time(),
                    "cpu_percent": cpu_percent,
                    "mem_mb": round(mem_mb, 1),
                    "threads": thread_count,
                    "handles": open_fds,
                }
                self.snapshots.append(snapshot)
            except Exception as e:
                logger.warning(f"[Monitor] 采样错误: {e}")
            time.sleep(1)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="PerfMonitor")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_summary(self) -> dict:
        if not self.snapshots:
            return {"error": "无数据"}

        cpus = [s["cpu_percent"] for s in self.snapshots]
        mems = [s["mem_mb"] for s in self.snapshots]
        threads = [s["threads"] for s in self.snapshots]

        return {
            "samples": len(self.snapshots),
            "cpu": {
                "avg": round(sum(cpus) / len(cpus), 1),
                "min": round(min(cpus), 1),
                "max": round(max(cpus), 1),
            },
            "memory_mb": {
                "avg": round(sum(mems) / len(mems), 1),
                "min": round(min(mems), 1),
                "max": round(max(mems), 1),
            },
            "threads": {
                "avg": round(sum(threads) / len(threads), 1),
                "min": min(threads),
                "max": max(threads),
            },
        }


async def create_test_streams(count: int) -> bool:
    """通过 API 创建测试设备。"""
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{API_BASE}/api/test/streams/create",
                params={"count": count},
                timeout=10,
            )
            data = resp.json()
            if data.get("success"):
                created = data["data"]["created"]
                logger.info(f"✅ 已创建 {created} 路测试流")
                return True
            else:
                logger.error(f"❌ 创建失败: {data}")
                return False
        except Exception as e:
            logger.error(f"❌ 请求后端失败: {e}")
            return False


async def remove_all_streams():
    """清理所有测试设备。"""
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{API_BASE}/api/test/streams/remove-all", timeout=10)
            logger.info("✅ 测试流已清理")
        except Exception as e:
            logger.warning(f"清理失败: {e}")


def start_backend() -> subprocess.Popen | None:
    """启动后端服务。"""
    logger.info("正在启动后端服务...")
    try:
        proc = subprocess.Popen(
            [sys.executable, os.path.join(BACKEND_DIR, "main.py")],
            cwd=BACKEND_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # 等待后端启动
        for i in range(30):
            try:
                import httpx
                resp = httpx.get(f"{API_BASE}/api/health", timeout=2)
                if resp.status_code == 200:
                    logger.info("✅ 后端服务已启动")
                    return proc
            except Exception:
                pass
            time.sleep(1)
        logger.error("❌ 后端服务启动超时")
        proc.kill()
        return None
    except Exception as e:
        logger.error(f"❌ 启动后端失败: {e}")
        return None


async def run_test(count: int, duration: int, start_server: bool):
    """运行多路流测试。"""
    backend_proc = None
    if start_server:
        backend_proc = start_backend()
        if not backend_proc:
            return
        time.sleep(2)

    try:
        # 创建测试流
        ok = await create_test_streams(count)
        if not ok:
            return

        # 等待流完全启动
        logger.info("等待流完全启动 (3s)...")
        await asyncio.sleep(3)

        # 创建消费者
        consumers = []
        for i in range(count):
            device_id = f"{TEST_DEVICE_PREFIX}{i + 1:02d}"
            consumer = StreamConsumer(device_id)
            consumers.append(consumer)
            consumer.start()
            await asyncio.sleep(0.1)  # 错开连接

        logger.info(f"✅ 已连接 {len(consumers)} 个消费端")
        await asyncio.sleep(1)

        # 启动性能监控
        monitor = PerformanceMonitor()
        monitor.start()

        # 等待测试完成
        logger.info(f"⏳ 正在采集性能数据（共 {duration} 秒）...")
        for second in range(duration):
            await asyncio.sleep(1)
            if second % 5 == 0 and second > 0:
                # 每 5 秒输出实时状态
                total_frames = sum(c.frame_count for c in consumers)
                avg_fps = sum(c.fps for c in consumers) / max(len(consumers), 1)
                errors = sum(c._errors for c in consumers)
                logger.info(
                    f"  [{second}/{duration}s] 总帧数={total_frames}, "
                    f"平均FPS={avg_fps:.1f}, 错误={errors}"
                )

        monitor.stop()

        # 停止消费者
        for c in consumers:
            c.stop()

        # 输出测试结果
        logger.info("=" * 60)
        logger.info("📊 测试结果报告")
        logger.info("=" * 60)
        logger.info(f"测试路数: {count} 路")
        logger.info(f"测试时长: {duration} 秒")

        # 系统资源
        sys_summary = monitor.get_summary()
        logger.info(f"\n--- 系统资源 ---")
        logger.info(f"CPU占用: 平均 {sys_summary['cpu']['avg']}% "
                     f"(最小 {sys_summary['cpu']['min']}% / 最大 {sys_summary['cpu']['max']}%)")
        logger.info(f"内存占用: 平均 {sys_summary['memory_mb']['avg']} MB "
                     f"(最小 {sys_summary['memory_mb']['min']} MB / "
                     f"最大 {sys_summary['memory_mb']['max']} MB)")
        logger.info(f"线程数: 平均 {sys_summary['threads']['avg']} "
                     f"(最小 {sys_summary['threads']['min']} / "
                     f"最大 {sys_summary['threads']['max']})")

        # 流性能
        total_frames = sum(c.frame_count for c in consumers)
        total_bytes = sum(c.byte_count for c in consumers)
        total_errors = sum(c._errors for c in consumers)
        fps_values = [c.fps for c in consumers if c.fps > 0]
        if fps_values:
            avg_fps = sum(fps_values) / len(fps_values)
            min_fps = min(fps_values)
            max_fps = max(fps_values)
        else:
            avg_fps = min_fps = max_fps = 0

        logger.info(f"\n--- 流性能 ---")
        logger.info(f"总接收帧数: {total_frames}")
        logger.info(f"总数据量: {total_bytes / 1024 / 1024:.1f} MB")
        logger.info(f"平均FPS (每路): {avg_fps:.1f}")
        logger.info(f"最小FPS (每路): {min_fps:.1f}")
        logger.info(f"最大FPS (每路): {max_fps:.1f}")
        logger.info(f"总连接错误: {total_errors}")

        # 带宽估算
        if duration > 0:
            bandwidth = (total_bytes / duration) / 1024  # KB/s
            bw_per_stream = bandwidth / max(count, 1)
            logger.info(f"总带宽: {bandwidth:.1f} KB/s")
            logger.info(f"每路带宽: {bw_per_stream:.1f} KB/s")

        logger.info("=" * 60)

        return {
            "count": count,
            "duration": duration,
            "system": sys_summary,
            "streams": {
                "totalFrames": total_frames,
                "totalMB": round(total_bytes / 1024 / 1024, 1),
                "avgFps": round(avg_fps, 1),
                "minFps": round(min_fps, 1),
                "maxFps": round(max_fps, 1),
                "errors": total_errors,
                "bandwidthKbps": round(bandwidth, 1),
                "bandwidthPerStreamKbps": round(bw_per_stream, 1),
            },
        }

    finally:
        await remove_all_streams()
        if backend_proc:
            logger.info("正在停止后端服务...")
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                backend_proc.kill()
            logger.info("后端服务已停止")


async def run_multiple_tests(test_configs: list, start_server: bool):
    """运行多个测试场景并汇总。"""
    results = []
    for config in test_configs:
        logger.info("\n" + "=" * 60)
        logger.info(f"🏁 测试场景: {config['count']} 路 / {config['duration']} 秒")
        logger.info("=" * 60)
        result = await run_test(config["count"], config["duration"], start_server)
        if result:
            results.append(result)
        # 等待间隔
        await asyncio.sleep(3)

    # 输出汇总
    logger.info("\n" + "=" * 60)
    logger.info("📊 多场景汇总")
    logger.info("=" * 60)
    for r in results:
        logger.info(
            f"  {r['count']}路: CPU={r['system']['cpu']['avg']}% | "
            f"内存={r['system']['memory_mb']['avg']}MB | "
            f"线程={r['system']['threads']['avg']} | "
            f"FPS={r['streams']['avgFps']} | "
            f"带宽={r['streams']['bandwidthKbps']}KB/s"
        )
    logger.info("=" * 60)
    return results


def main():
    parser = argparse.ArgumentParser(description="多路视频流性能测试")
    parser.add_argument("--count", type=int, default=2, help="测试路数 (默认: 2)")
    parser.add_argument("--duration", type=int, default=30, help="测试时长秒数 (默认: 30)")
    parser.add_argument("--all", action="store_true", help="运行全部测试场景 (2/4/8路)")
    parser.add_argument("--no-backend", action="store_true", help="不启动后端 (使用已有后端)")
    args = parser.parse_args()

    start_server = not args.no_backend

    if args.all:
        test_configs = [
            {"count": 2, "duration": args.duration},
            {"count": 4, "duration": args.duration},
            {"count": 8, "duration": args.duration},
        ]
        asyncio.run(run_multiple_tests(test_configs, start_server))
    else:
        asyncio.run(run_test(args.count, args.duration, start_server))


if __name__ == "__main__":
    main()
