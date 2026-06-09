#!/bin/bash
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "❌ 找不到 Python 3，请先安装 Python 3.10+"
    exit 1
fi

VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    echo "📦 使用虚拟环境: $VENV_DIR"
    source "$VENV_DIR/bin/activate"
    PYTHON_BIN="python"
fi

if ! $PYTHON_BIN -c "import fastapi" >/dev/null 2>&1; then
    echo "📥 首次启动，正在安装依赖包..."
    $PYTHON_BIN -m pip install --upgrade pip >/dev/null 2>&1 || true
    $PYTHON_BIN -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，请检查网络连接"
        exit 1
    fi
fi

echo ""
echo "🎨 图像风格转换服务启动中..."
echo "   首次启动需要加载 OpenCV/FastAPI 等依赖库"
echo "   预计等待时间: 20-40 秒，请耐心等待..."
echo ""
echo "🌐 服务地址: http://127.0.0.1:8605"
echo "🛑 停止服务: Ctrl + C"
echo ""

exec $PYTHON_BIN app.py
