"""
GET /api/traffic/dashboard - 获取仪表盘聚合数据
"""
from fastapi import APIRouter
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_session_factory
from models import TrafficRecord, Device
from utils import success_response, models_to_list

router = APIRouter(prefix="/api/traffic/dashboard", tags=["客流数据"])


@router.get("")
async def get_dashboard_data():
    """获取仪表盘聚合数据"""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    
    # 计算本周一
    day_of_week = today.weekday()  # 0=Monday
    monday = today - timedelta(days=day_of_week)
    monday_str = monday.strftime("%Y-%m-%d")
    
    # 本月第一天
    first_day_of_month = today.replace(day=1)
    first_day_str = first_day_of_month.strftime("%Y-%m-%d")
    
    SessionFactory = get_session_factory()
    with SessionFactory() as session:
        # ===== 今日数据 =====
        today_records = session.query(TrafficRecord).filter_by(date=today_str).all()
        today_in = sum(r.countIn for r in today_records)
        today_out = sum(r.countOut for r in today_records)
        current_in = today_in - today_out
        
        # ===== 本周数据 =====
        week_records = session.query(TrafficRecord).filter(
            TrafficRecord.date >= monday_str,
            TrafficRecord.date <= today_str,
        ).all()
        week_in = sum(r.countIn for r in week_records)
        week_out = sum(r.countOut for r in week_records)
        
        # ===== 本月数据 =====
        month_records = session.query(TrafficRecord).filter(
            TrafficRecord.date >= first_day_str,
            TrafficRecord.date <= today_str,
        ).all()
        month_in = sum(r.countIn for r in month_records)
        month_out = sum(r.countOut for r in month_records)
        
        # ===== 全部数据 =====
        all_records = session.query(TrafficRecord).all()
        total_in = sum(r.countIn for r in all_records)
        total_out = sum(r.countOut for r in all_records)
        
        # ===== 今日每小时数据 =====
        hourly_today = []
        for h in range(24):
            hour_records = [r for r in today_records if r.hour == h]
            hour_in = sum(r.countIn for r in hour_records)
            hour_out = sum(r.countOut for r in hour_records)
            hourly_today.append({"hour": h, "countIn": hour_in, "countOut": hour_out})
        
        # ===== 设备列表 =====
        devices = session.query(Device).order_by(Device.createdAt.desc()).all()
        
        return success_response({
            "todayIn": today_in,
            "todayOut": today_out,
            "currentIn": current_in,
            "weekIn": week_in,
            "weekOut": week_out,
            "monthIn": month_in,
            "monthOut": month_out,
            "totalIn": total_in,
            "totalOut": total_out,
            "hourlyToday": hourly_today,
            "devices": models_to_list(devices),
        })
