#!/bin/bash
# 启动脚本 - 自动激活虚拟环境并运行 Flask 应用

# 进入脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "正在安装依赖..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    # 激活虚拟环境
    source venv/bin/activate
fi

# 运行应用
python run.py
