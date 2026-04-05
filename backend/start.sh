#!/bin/bash
# FluxaVision 后端启动脚本
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
