"""
POST /api/seed - 生成演示数据

数据存储策略:
  每个摄像头的客流数据独立存储 (deviceId = 摄像头ID)
  门店汇总 = 查询时对所有设备数据求和 (不单独存储汇总记录)
"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from database import get_session_factory
from models import Device, TrafficRecord
from utils import success_response, error_response, generate_rtsp_url

router = APIRouter(prefix="/api/seed", tags=["数据种子"])

# 模拟每小时客流系数 (8:00-22:00 高峰时段)
HOURLY_PATTERN = [
    0.02, 0.01, 0.01, 0.01, 0.01, 0.02,   # 0-5点
    0.05, 0.15, 0.35, 0.65, 0.85, 1.0,    # 6-11点 早高峰
    0.75, 0.55, 0.50, 0.60, 0.70, 0.95,  # 12-17点 午后到晚高峰
    0.80, 0.60, 0.40, 0.20, 0.10, 0.03,  # 18-23点 晚间衰减
]

DEFAULT_DEVICES = [
    {
        "name": "正门入口", "ip": "192.168.1.101", "serialNumber": "DH-IPC-001",
        "location": "一楼正门", "model": "大华", "rtspPort": 554,
        "username": "admin", "password": "admin123", "status": "online",
    },
    {
        "name": "侧门通道", "ip": "192.168.1.102", "serialNumber": "DH-IPC-002",
        "location": "二楼侧门", "model": "大华", "rtspPort": 554,
        "username": "admin", "password": "admin123", "status": "online",
    },
    {
        "name": "后门通道", "ip": "192.168.1.103", "serialNumber": "HK-DS-003",
        "location": "地下停车场入口", "model": "海康威视", "rtspPort": 554,
        "username": "admin", "password": "admin123", "status": "warning",
    },
]


@router.post("")
async def seed_data(request: Request):
    """
    生成演示数据

    每个摄像头独立记录客流, 门店汇总在查询时自动计算。
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    days = body.get("days", 30)

    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        # 检查是否已有数据
        existing_count = session.query(TrafficRecord).count()
        if existing_count > 0:
            return error_response(f"已有 {existing_count} 条记录, 请先清空数据", 400)

        # 获取或创建设备
        devices = session.query(Device).all()
        if not devices:
            for d in DEFAULT_DEVICES:
                device = Device(
                    name=d["name"], ip=d["ip"], serialNumber=d["serialNumber"],
                    location=d["location"], model=d["model"], rtspPort=d["rtspPort"],
                    username=d["username"], password=d["password"], status=d["status"],
                    rtspUrl=generate_rtsp_url(d["model"], d["ip"], d["rtspPort"], d["username"], d["password"]),
                    maxChannels=4,
                )
                session.add(device)
            session.flush()
            devices = session.query(Device).all()

        # 每个设备的客流权重 (模拟不同位置的流量差异)
        device_weights = [0.45, 0.30, 0.25]  # 正门最大, 侧门中等, 后门最小
        if len(devices) != len(device_weights):
            # 设备数量不匹配时, 均分权重
            device_weights = [1.0 / len(devices)] * len(devices)

        # 生成客流数据 (仅设备级记录, 不存储门店汇总)
        today = datetime.now()
        records = []
        weekend_multiplier = 1.4
        random_range = 0.7

        for day_offset in range(days - 1, -1, -1):
            date = today - timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")
            is_weekend = date.weekday() >= 5
            base_multiplier = weekend_multiplier if is_weekend else 1.0

            for hour in range(24):
                base_traffic = 80
                hour_factor = HOURLY_PATTERN[hour]
                random_factor = 1 + (random.random() - 0.5) * 2 * random_range
                store_total = round(base_traffic * hour_factor * base_multiplier * random_factor)

                if store_total <= 0:
                    continue

                # 各设备按权重分配门店总客流 (加随机波动)
                weights = [w * (0.8 + random.random() * 0.4) for w in device_weights]
                weights_sum = sum(weights)
                allocated = 0

                for i, device in enumerate(devices):
                    is_last = (i == len(devices) - 1)
                    if is_last:
                        device_in = max(0, store_total - allocated)
                    else:
                        device_in = round(store_total * weights[i] / weights_sum)
                        allocated += device_in

                    device_out = round(device_in * (0.75 + random.random() * 0.4))
                    records.append(TrafficRecord(
                        deviceId=device.id, date=date_str, hour=hour,
                        countIn=device_in, countOut=device_out,
                    ))

        # 批量写入
        batch_size = 100
        for i in range(0, len(records), batch_size):
            session.add_all(records[i:i + batch_size])
            session.flush()

        session.commit()

        from_date = (today - timedelta(days=days - 1)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")

        return success_response({
            "message": f"成功生成 {days} 天的演示数据 ({len(devices)} 台设备)",
            "totalRecords": len(records),
            "devices": len(devices),
            "dateRange": {"from": from_date, "to": to_date},
        })
