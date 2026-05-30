#!/bin/bash
# ================================================================
# 百工模拟考场 - 启动脚本
# ================================================================
# 用途:
#   - 本地开发: bash start.sh
#   - Render 部署: 不需要此脚本（直接使用 render.yaml 的 startCommand）
# ================================================================

set -e

# 获取项目根目录
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================"
echo "  百工模拟考场 - 启动"
echo "============================================"

# 1. 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[setup] 创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
echo "[setup] 安装依赖..."
pip install -r requirements.txt --quiet

# 4. 加载 .env（如果存在）
if [ -f ".env" ]; then
    echo "[setup] 加载 .env 环境变量..."
    export $(grep -v '^#' .env | xargs)
fi

# 5. 启动服务
PORT="${PORT:-5000}"
echo "[start] 启动服务 → http://0.0.0.0:$PORT"
echo ""

# 本地开发用 eventlet 驱动（支持 WebSocket）
python app.py
