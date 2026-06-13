# -*- coding: utf-8 -*-
"""
FluxaVision - 大华摄像头客流数据集成模块
基于 NetSDK 2.0.0.1 (Windows x64)

支持三种数据获取方式：
  方式一: AttachVideoStatSummary       — 实时推送进出人数统计（推荐，无年龄性别）
  方式二: RealLoadPictureEx NUMBERSTAT — IVS 数量统计事件（无年龄性别）
  方式三: RealLoadPictureEx FACEDETECT — 人脸检测事件（含年龄、性别、口罩等属性）✦
"""

import ctypes
import threading
import time
import queue
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Callable

# ─── pip install NetSDK-2_0_0_1-py3-none-win_amd64.whl ──────────────────────
from NetSDK.NetSDK import NetClient
from NetSDK.SDK_Struct import (
    NET_IN_ATTACH_VIDEOSTAT_SUM,
    NET_OUT_ATTACH_VIDEOSTAT_SUM,
    NET_VIDEOSTAT_SUMMARY,
    NETSDK_INIT_PARAM,
    NET_A_DEV_EVENT_NUMBERSTAT_INFO,
    DEV_EVENT_FACEDETECT_INFO,
    C_LLONG,
    C_LDWORD,
    C_DWORD,
)
from NetSDK.SDK_Enum import (
    EM_EVENT_IVS_TYPE,
    EM_LOGIN_SPAC_CAP_TYPE,
    EM_DEV_EVENT_FACEDETECT_SEX_TYPE,
    EM_AGE_SEG,
)
from NetSDK.SDK_Callback import (
    CB_FUNCTYPE,
    fAnalyzerDataCallBack,
    fDisConnect,
    fHaveReConnect,
)

logger = logging.getLogger("FluxaVision.Dahua")


# ─── 辅助：枚举转可读字符串 ──────────────────────────────────────────────────

def sex_label(em_sex: int) -> str:
    """EM_DEV_EVENT_FACEDETECT_SEX_TYPE → 'male' / 'female' / 'unknown'"""
    return {1: "male", 2: "female"}.get(em_sex, "unknown")


def age_seg_label(em_age_seg: int) -> str:
    """
    EM_AGE_SEG 枚举值 → 年龄段字符串
      0=unknown  2=baby  10=child  28=youth  50=middle  60=old
    """
    return {
        0:  "unknown",
        2:  "baby",    # 婴儿
        10: "child",   # 幼儿
        28: "youth",   # 青年
        50: "middle",  # 中年
        60: "old",     # 老年
    }.get(em_age_seg, "unknown")


def _mask_label(v: int) -> str:
    return {0: "unknown", 1: "no_mask", 2: "mask"}.get(v, "unknown")

def _eye_label(v: int) -> str:
    return {0: "unknown", 1: "no_distinguish", 2: "closed", 3: "open"}.get(v, "unknown")

def _mouth_label(v: int) -> str:
    return {0: "unknown", 1: "no_distinguish", 2: "closed", 3: "open"}.get(v, "unknown")


# ─── 数据模型 ─────────────────────────────────────────────────────────────────

@dataclass
class FaceRecord:
    """
    单次人脸检测记录（来自 FACEDETECT 事件）

    SDK 字段来源（DEV_EVENT_FACEDETECT_INFO）：
      emSex        → EM_DEV_EVENT_FACEDETECT_SEX_TYPE (0=unknown, 1=male, 2=female)
      nAge         → ubyte，具体年龄；255 / 0xFF 表示无效
      stuFaces[0]
        .stuFaceAttribute.emAgeSeg → EM_AGE_SEG 年龄段
      emMask       → EM_MASK_STATE_TYPE
      emEye        → EM_EYE_STATE_TYPE
      emMouth      → EM_MOUTH_STATE_TYPE
      nAttractive  → 魅力值 1~100，-1 无效
      nFaceQuality → 抓拍质量 0~10000，-1 无效
    """
    timestamp: datetime
    channel_id: int

    sex: str = "unknown"          # "male" / "female" / "unknown"
    age: int = -1                 # 精确年龄，-1 表示无效
    age_segment: str = "unknown"  # "baby/child/youth/middle/old/unknown"

    mask: str = "unknown"         # 口罩状态
    eye_state: str = "unknown"
    mouth_state: str = "unknown"
    attractive: int = -1          # 魅力值 1~100，-1 无效
    face_quality: int = -1        # 质量分 0~10000

    source: str = "facedetect"


@dataclass
class PeopleFlowSnapshot:
    """
    单次进出统计快照（来自 VideoStat 或 IVS NUMBERSTAT 事件）
    年龄/性别在 FaceRecord 里，此处仅做人数汇总。
    """
    timestamp: datetime
    channel_id: int
    rule_name: str

    # VideoStat 字段
    entered_total: int = 0    # 累计进入（设备启动后）
    entered_today: int = 0    # 今日进入
    entered_hour: int = 0     # 近1小时进入
    exited_total: int = 0     # 累计离开
    exited_today: int = 0     # 今日离开
    exited_hour: int = 0      # 近1小时离开
    inside_count: int = 0     # 当前在场人数

    # IVS NUMBERSTAT 字段
    ivs_area_count: int = 0
    ivs_entered: int = 0
    ivs_exited: int = 0
    ivs_passed: int = 0
    ivs_upper_limit: int = 0

    source: str = "videostat"   # "videostat" / "ivs_numberstat"


# ─── 核心采集器 ───────────────────────────────────────────────────────────────

class DahuaPeopleCounter:
    """
    大华摄像头客流 + 人脸属性采集器

    mode 参数：
      "videostat" — AttachVideoStatSummary 进出汇总（默认，稳定高效）
      "ivs"       — RealLoadPictureEx NUMBERSTAT 数量统计事件
      "face"      — RealLoadPictureEx FACEDETECT  人脸检测（含年龄、性别）

    回调：
      on_flow_update(snap: PeopleFlowSnapshot)  — videostat / ivs 模式触发
      on_face_detected(face: FaceRecord)         — face 模式，每张人脸触发一次
    """

    MODE_VIDEOSTAT = "videostat"
    MODE_IVS       = "ivs"
    MODE_FACE      = "face"

    def __init__(
        self,
        ip: str,
        port: int = 37777,
        username: str = "admin",
        password: str = "",
        channel: int = 0,
        mode: str = "videostat",
    ):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.channel = channel
        self.mode = mode

        self._sdk = NetClient()
        self._login_id: int = 0
        self._attach_handle: int = 0
        self._ivs_handle: int = 0
        self._face_handle: int = 0
        self._running = False

        self._flow_queue: queue.Queue[PeopleFlowSnapshot] = queue.Queue(maxsize=500)
        self._face_queue: queue.Queue[FaceRecord] = queue.Queue(maxsize=2000)

        # 外部回调钩子
        self.on_flow_update: Optional[Callable[[PeopleFlowSnapshot], None]] = None
        self.on_face_detected: Optional[Callable[[FaceRecord], None]] = None

        # 防 GC 引用
        self._cb_videostat = None
        self._cb_ivs = None
        self._cb_face = None
        self._cb_disconnect = None
        self._cb_reconnect = None

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self):
        logger.info(f"[DahuaCounter] 连接 {self.ip}:{self.port} mode={self.mode}")

        @fDisConnect
        def _dc(login_id, remote_host, port, user_data):
            logger.warning(f"[DahuaCounter] 设备断线 login_id={login_id}")
        self._cb_disconnect = _dc

        init_param = NETSDK_INIT_PARAM()
        if not self._sdk.InitEx(_dc, 0, init_param):
            raise RuntimeError(f"SDK 初始化失败: {self._sdk.GetLastErrorMessage()}")

        @fHaveReConnect
        def _rc(login_id, remote_host, port, user_data):
            logger.info(f"[DahuaCounter] 重连成功 login_id={login_id}")
            try:
                self._subscribe()
            except Exception as e:
                logger.error(f"[DahuaCounter] 重连后订阅失败: {e}")
        self._cb_reconnect = _rc
        self._sdk.SetAutoReconnect(_rc, 0)

        self._login()
        self._subscribe()

        self._running = True
        threading.Thread(target=self._consume_loop, daemon=True).start()
        logger.info("[DahuaCounter] 启动成功")

    def stop(self):
        self._running = False
        if self._attach_handle:
            self._sdk.DetachVideoStatSummary(self._attach_handle)
            self._attach_handle = 0
        for attr in ("_ivs_handle", "_face_handle"):
            h = getattr(self, attr)
            if h:
                self._sdk.StopLoadPic(h)
                setattr(self, attr, 0)
        if self._login_id:
            self._sdk.Logout(self._login_id)
            self._login_id = 0
        self._sdk.Cleanup()
        logger.info("[DahuaCounter] 已停止")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()

    # ── 登录 ──────────────────────────────────────────────────────────────────

    def _login(self):
        login_id, _, _err = self._sdk.LoginEx2(
            self.ip, self.port, self.username, self.password,
            EM_LOGIN_SPAC_CAP_TYPE.TCP,
        )
        if login_id == 0:
            raise ConnectionError(f"登录失败: {self._sdk.GetLastErrorMessage()}")
        self._login_id = login_id
        logger.info(f"[DahuaCounter] 登录成功 login_id={login_id}")

    def _subscribe(self):
        if self.mode == self.MODE_VIDEOSTAT:
            self._start_videostat()
        elif self.mode == self.MODE_IVS:
            self._start_ivs()
        elif self.mode == self.MODE_FACE:
            self._start_face()
        else:
            raise ValueError(f"未知 mode={self.mode!r}")

    # ── 方式一: VideoStat ─────────────────────────────────────────────────────

    def _start_videostat(self):
        @CB_FUNCTYPE(None, C_LLONG, ctypes.POINTER(NET_VIDEOSTAT_SUMMARY), C_DWORD, C_LDWORD)
        def _cb(attach_handle, summary_ptr, buf_size, user_data):
            try:
                s = summary_ptr.contents
                snap = PeopleFlowSnapshot(
                    timestamp=datetime.now(),
                    channel_id=s.nChannelID,
                    rule_name=s.szRuleName.decode("utf-8", errors="ignore").rstrip("\x00"),
                    entered_total=s.stuEnteredSubtotal.nTotal,
                    entered_today=s.stuEnteredSubtotal.nToday,
                    entered_hour=s.stuEnteredSubtotal.nHour,
                    exited_total=s.stuExitedSubtotal.nTotal,
                    exited_today=s.stuExitedSubtotal.nToday,
                    exited_hour=s.stuExitedSubtotal.nHour,
                    inside_count=s.nInsidePeopleNum,
                    source="videostat",
                )
                if not self._flow_queue.full():
                    self._flow_queue.put_nowait(snap)
            except Exception as e:
                logger.error(f"[VideoStat回调] {e}")

        self._cb_videostat = _cb

        in_p = NET_IN_ATTACH_VIDEOSTAT_SUM()
        in_p.dwSize = ctypes.sizeof(NET_IN_ATTACH_VIDEOSTAT_SUM)
        in_p.nChannel = self.channel
        in_p.cbVideoStatSum = _cb
        in_p.dwUser = 0

        out_p = NET_OUT_ATTACH_VIDEOSTAT_SUM()
        out_p.dwSize = ctypes.sizeof(NET_OUT_ATTACH_VIDEOSTAT_SUM)

        h = self._sdk.AttachVideoStatSummary(self._login_id, in_p, out_p, 5000)
        if h == 0:
            raise RuntimeError(f"AttachVideoStatSummary 失败: {self._sdk.GetLastErrorMessage()}")
        self._attach_handle = h
        logger.info(f"[DahuaCounter] VideoStat 订阅成功 handle={h}")

    # ── 方式二: IVS NUMBERSTAT ────────────────────────────────────────────────

    def _start_ivs(self):
        @fAnalyzerDataCallBack
        def _cb(analyzer_handle, login_id, event_type, info_buf, buf_size, user_data, reserved):
            try:
                if event_type != EM_EVENT_IVS_TYPE.NUMBERSTAT:
                    return
                evt = ctypes.cast(
                    info_buf, ctypes.POINTER(NET_A_DEV_EVENT_NUMBERSTAT_INFO)
                ).contents
                snap = PeopleFlowSnapshot(
                    timestamp=datetime.now(),
                    channel_id=evt.nChannelID,
                    rule_name=evt.szName.decode("utf-8", errors="ignore").rstrip("\x00"),
                    ivs_area_count=evt.nNumber,
                    ivs_entered=evt.nEnteredNumber,
                    ivs_exited=evt.nExitedNumber,
                    ivs_passed=evt.nPassedNumber,
                    ivs_upper_limit=evt.nUpperLimit,
                    source="ivs_numberstat",
                )
                if not self._flow_queue.full():
                    self._flow_queue.put_nowait(snap)
            except Exception as e:
                logger.error(f"[IVS回调] {e}")

        self._cb_ivs = _cb
        h = self._sdk.RealLoadPictureEx(
            self._login_id, self.channel,
            EM_EVENT_IVS_TYPE.NUMBERSTAT, False, _cb, 0, None,
        )
        if h == 0:
            raise RuntimeError(f"RealLoadPictureEx(IVS) 失败: {self._sdk.GetLastErrorMessage()}")
        self._ivs_handle = h
        logger.info(f"[DahuaCounter] IVS NUMBERSTAT 订阅成功 handle={h}")

    # ── 方式三: FACEDETECT（年龄 + 性别）──────────────────────────────────────

    def _start_face(self):
        """
        订阅 FACEDETECT 事件。
        摄像头需在 Web 管理界面开启 "人脸检测" 智能分析规则。

        DEV_EVENT_FACEDETECT_INFO 关键字段：
          nChannelID  — 通道号
          emSex       — 性别 (EM_DEV_EVENT_FACEDETECT_SEX_TYPE)
          nAge        — 年龄 ubyte，255 表示无效
          stuFaces    — 多张人脸数组（nFacesNum 有效）
            [0].stuFaceAttribute.emAgeSeg — 年龄段 (EM_AGE_SEG)
          emMask      — 口罩 (EM_MASK_STATE_TYPE)
          emEye       — 眼睛 (EM_EYE_STATE_TYPE)
          emMouth     — 嘴巴 (EM_MOUTH_STATE_TYPE)
          nAttractive — 魅力值 1~100
          nFaceQuality— 质量分 0~10000
        """
        @fAnalyzerDataCallBack
        def _cb(analyzer_handle, login_id, event_type, info_buf, buf_size, user_data, reserved):
            try:
                if event_type != EM_EVENT_IVS_TYPE.FACEDETECT:
                    return

                evt = ctypes.cast(
                    info_buf, ctypes.POINTER(DEV_EVENT_FACEDETECT_INFO)
                ).contents

                # 精确年龄（ubyte 255 = 无效）
                raw_age = int(evt.nAge)
                age = raw_age if raw_age not in (255, 0xFF) else -1

                # 年龄段（从第一张人脸的 FaceAttribute 取）
                age_seg = "unknown"
                if evt.nFacesNum > 0:
                    try:
                        age_seg = age_seg_label(
                            int(evt.stuFaces[0].stuFaceAttribute.emAgeSeg)
                        )
                    except Exception:
                        pass

                face_rec = FaceRecord(
                    timestamp=datetime.now(),
                    channel_id=evt.nChannelID,
                    sex=sex_label(int(evt.emSex)),
                    age=age,
                    age_segment=age_seg,
                    mask=_mask_label(int(evt.emMask)),
                    eye_state=_eye_label(int(evt.emEye)),
                    mouth_state=_mouth_label(int(evt.emMouth)),
                    attractive=int(evt.nAttractive),
                    face_quality=int(evt.nFaceQuality),
                )
                if not self._face_queue.full():
                    self._face_queue.put_nowait(face_rec)
            except Exception as e:
                logger.error(f"[FaceDetect回调] {e}")

        self._cb_face = _cb
        h = self._sdk.RealLoadPictureEx(
            self._login_id, self.channel,
            EM_EVENT_IVS_TYPE.FACEDETECT, False, _cb, 0, None,
        )
        if h == 0:
            raise RuntimeError(f"RealLoadPictureEx(FACE) 失败: {self._sdk.GetLastErrorMessage()}")
        self._face_handle = h
        logger.info(f"[DahuaCounter] FACEDETECT 订阅成功 handle={h}")

    # ── 消费循环（分发队列数据到回调） ───────────────────────────────────────

    def _consume_loop(self):
        """消费队列循环

        优化：
        - 使用 blocking get(timeout) 替代 get_nowait + sleep，减少空转 CPU
        - 队列有数据时立即处理，无数据时阻塞等待（最大 10ms）
        - 增加 timing 日志，方便诊断延迟
        """
        while self._running:
            consumed = False
            try:
                snap = self._flow_queue.get(timeout=0.01)
                t0 = time.perf_counter()
                if self.on_flow_update:
                    self.on_flow_update(snap)
                elapsed = time.perf_counter() - t0
                if elapsed > 0.1:  # >100ms 记录警告
                    logger.warning(
                        f"[Latency] flow_update 耗时 {elapsed*1000:.1f}ms"
                        f" 今日进={snap.entered_today} 出={snap.exited_today}"
                    )
                consumed = True
            except queue.Empty:
                pass
            try:
                face = self._face_queue.get(timeout=0.01)
                t0 = time.perf_counter()
                if self.on_face_detected:
                    self.on_face_detected(face)
                elapsed = time.perf_counter() - t0
                if elapsed > 0.05:  # >50ms 记录警告
                    logger.warning(
                        f"[Latency] face_detected 耗时 {elapsed*1000:.1f}ms"
                    )
                consumed = True
            except queue.Empty:
                pass
            if not consumed:
                time.sleep(0.002)  # 双队列都空时短暂休眠，降低 CPU


# ─── FluxaVision 多摄像头汇聚层 ──────────────────────────────────────────────

class FluxaVisionPeopleFlow:
    """
    FluxaVision 多摄像头集成入口。

    示例:
        fv = FluxaVisionPeopleFlow()
        fv.add_camera("entrance", "192.168.1.108", password="xxx", mode="face")
        fv.add_camera("lobby",    "192.168.1.109", password="yyy", mode="videostat")
        fv.on_flow = lambda cid, snap: print(f"[{cid}] 今日进={snap.entered_today}")
        fv.on_face = lambda cid, face: print(f"[{cid}] {face.sex} {face.age}岁")
        with fv:
            time.sleep(3600)
    """

    def __init__(self):
        self._counters: dict[str, DahuaPeopleCounter] = {}
        self.on_flow: Optional[Callable[[str, PeopleFlowSnapshot], None]] = None
        self.on_face: Optional[Callable[[str, FaceRecord], None]] = None

    def add_camera(
        self,
        camera_id: str,
        ip: str,
        port: int = 37777,
        username: str = "admin",
        password: str = "",
        channel: int = 0,
        mode: str = "videostat",
    ):
        c = DahuaPeopleCounter(ip, port, username, password, channel, mode)
        c.on_flow_update   = lambda s, cid=camera_id: self.on_flow and self.on_flow(cid, s)
        c.on_face_detected = lambda f, cid=camera_id: self.on_face and self.on_face(cid, f)
        self._counters[camera_id] = c

    def start_all(self):
        for cid, c in self._counters.items():
            try:
                c.start()
            except Exception as e:
                logger.error(f"[FluxaVision] {cid} 启动失败: {e}")

    def stop_all(self):
        for c in self._counters.values():
            c.stop()

    def __enter__(self):
        self.start_all()
        return self

    def __exit__(self, *_):
        self.stop_all()


# ─── 快速测试 ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    CAMERA_IP = "192.168.1.108"
    PORT      = 37777
    USER      = "admin"
    PWD       = "admin123"
    CHANNEL   = 0

    def on_flow(snap: PeopleFlowSnapshot):
        print(
            f"[FLOW {snap.timestamp:%H:%M:%S}] CH{snap.channel_id} "
            f"今日进={snap.entered_today} 今日出={snap.exited_today} "
            f"在场={snap.inside_count} 近1h进={snap.entered_hour} 出={snap.exited_hour} "
            f"时间={snap.timestamp} "
        )

    def on_face(face: FaceRecord):
        age_str = f"{face.age}岁" if face.age >= 0 else f"~{face.age_segment}"
        print(
            f"[FACE {face.timestamp:%H:%M:%S}] CH{face.channel_id} "
            f"性别={face.sex:<8} 年龄={age_str:<10} 年龄段={face.age_segment:<8} "
            f"口罩={face.mask:<10} 质量={face.face_quality}"
        )

    # 选择模式：videostat / ivs / face
    MODE = "videostat"

    counter = DahuaPeopleCounter(CAMERA_IP, PORT, USER, PWD, CHANNEL, mode=MODE)
    counter.on_flow_update   = on_flow
    counter.on_face_detected = on_face

    try:
        counter.start()
        print(f"采集中 mode={MODE}，Ctrl+C 停止...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        counter.stop()
