"""
POST /api/seed - 生成演示数据
"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from sqlalchemy.orm import Session
from database import get_session_factory
from models import Device, TrafficRecord
from utils import success_response, error_response, model_to_dict, generate_rtsp_url

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
    """生成演示数据"""
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
        
        # 生成客流数据
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
                base_traffic = 50
                hour_factor = HOURLY_PATTERN[hour]
                random_factor = 1 + (random.random() - 0.5) * 2 * random_range
                count = round(base_traffic * hour_factor * base_multiplier * random_factor)
                
                if count <= 0:
                    continue
                
                # 各设备的记录
                for device in devices:
                    device_ratio = 0.3 + random.random() * 0.4
                    device_in = round(count * device_ratio)
                    device_out = round(device_in * (0.8 + random.random() * 0.4))
                    records.append(TrafficRecord(
                        deviceId=device.id, date=date_str, hour=hour,
                        countIn=device_in, countOut=device_out,
                    ))
                
                # 汇总记录
                total_in = round(count)
                total_out = round(count * (0.75 + random.random() * 0.3))
                records.append(TrafficRecord(
                    deviceId=None, date=date_str, hour=hour,
                    countIn=total_in, countOut=total_out,
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
            "message": f"成功生成 {days} 天的演示数据",
            "totalRecords": len(records),
            "devices": len(devices),
            "dateRange": {"from": from_date, "to": to_date},
        })
