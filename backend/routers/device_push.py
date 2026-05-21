"""
双目客流相机 HTTP 推送接口

协议文档: docs/KLY_V1.2.md

接口：
  POST /klyun/kl/equipapi/binocular/heartBeat   — 心跳上传（每分钟一次）
  POST /klyun/kl/equipapi/binocular/dataUpload   — 数据上传（实时/间隔模式）

整合方案：
  - 推送 sn → 匹配现有 Device.serialNumber
  - 心跳 → 更新 Device.status = "online", updatedAt
  - 数据 → 写入/累加 TrafficRecord (按 deviceId + date + hour)
"""
import json
import time
import logging
from datetime import datetime

from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from database import get_session_factory
from models import Device, TrafficRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/klyun/kl/equipapi/binocular", tags=["设备推送"])


def _now_ts() -> int:
    """返回当前 Unix 时间戳（秒）"""
    return int(time.time())


def _success_response(sn: str) -> dict:
    return {
        "code": 0,
        "msg": "success",
        "data": {"sn": sn, "time": _now_ts()},
    }


def _error_response(msg: str = "failure") -> dict:
    return {"code": 1, "msg": msg, "data": {}}


def _find_device_by_sn(session: Session, sn: str):
    """通过 serialNumber 查找 Device"""
    return session.query(Device).filter_by(serialNumber=sn).first()


def _heartbeat_update_device(device: Device, body: dict):
    """心跳更新设备状态"""
    device.status = "online"
    # 可选更新基础信息
    if body.get("ipAddress"):
        device.ip = body["ipAddress"]
    if body.get("hostName") and not device.name or device.name == device.serialNumber:
        device.name = body["hostName"]


def _ensure_traffic_record(
    session: Session, device_id: str, date_str: str, hour: int,
) -> TrafficRecord:
    """查找或创建指定 deviceId+date+hour 的 TrafficRecord"""
    record = session.query(TrafficRecord).filter_by(
        deviceId=device_id, date=date_str, hour=hour,
    ).first()
    if not record:
        record = TrafficRecord(
            deviceId=device_id,
            date=date_str,
            hour=hour,
            countIn=0,
            countOut=0,
            passby=0,
            turnback=0,
            avgStayTime=0,
        )
        session.add(record)
    return record


def _parse_data_time(start_time: int, end_time: int):
    """将推送的 unix 时间戳(毫秒)转为 date(YYYY-MM-DD) 和 hour(0-23)
    
    协议中 startTime/endTime 是 unix 时间戳, 示例值为 161231947237 (13位, 毫秒)
    如果传入的是秒级(10位)也兼容处理。
    """
    def _ts_to_dt(ts: int):
        if ts > 1e12:  # 毫秒级
            return datetime.fromtimestamp(ts / 1000)
        return datetime.fromtimestamp(ts)

    dt = _ts_to_dt(end_time)
    return dt.strftime("%Y-%m-%d"), dt.hour


@router.post("/heartBeat")
async def heart_beat(request: Request):
    """心跳上传接口"""
    try:
        body = await request.json()
    except Exception:
        return _error_response("invalid json")

    sn = body.get("sn", "")
    if not sn:
        return _error_response("sn is required")

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = _find_device_by_sn(session, sn)
        if not device:
            logger.warning(f"心跳 | 未知设备 sn={sn}, 忽略")
            return _error_response("device not registered")

        device_id = device.id
        _heartbeat_update_device(device, body)
        session.commit()

    logger.info(f"心跳 | sn={sn} deviceId={device_id} ip={body.get('ipAddress', '')}")
    return _success_response(sn)


@router.post("/dataUpload")
async def data_upload(request: Request):
    """数据上传接口"""
    try:
        body = await request.json()
    except Exception:
        return _error_response("invalid json")

    sn = body.get("sn", "")
    if not sn:
        return _error_response("sn is required")

    start_time = body.get("startTime", 0)
    end_time = body.get("endTime", 0)
    if not end_time:
        return _error_response("endTime is required")

    date_str, hour = _parse_data_time(start_time, end_time)

    count_in = int(body.get("in", 0))
    count_out = int(body.get("out", 0))
    passby = int(body.get("passby", 0))
    turnback = int(body.get("turnback", 0))
    avg_stay = int(body.get("avgStayTime", 0))

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        device = _find_device_by_sn(session, sn)
        if not device:
            logger.warning(f"数据 | 未知设备 sn={sn}, 忽略")
            return _error_response("device not registered")

        device_id = device.id

        # 心跳同步: 更新设备在线
        _heartbeat_update_device(device, body)

        # 查找或创建 TrafficRecord, 累加计数
        record = _ensure_traffic_record(session, device_id, date_str, hour)
        record.countIn += count_in
        record.countOut += count_out
        record.passby += passby
        record.turnback += turnback
        record.avgStayTime = avg_stay  # 使用最新的 avgStayTime

        session.commit()

    logger.info(
        f"数据 | sn={sn} deviceId={device_id} "
        f"date={date_str} hour={hour} "
        f"in={count_in} out={count_out}"
    )
    return _success_response(sn)
