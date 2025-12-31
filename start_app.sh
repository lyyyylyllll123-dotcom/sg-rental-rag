#!/bin/bash
# Streamlit 应用启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 正在启动 Singapore Rental RAG Assistant..."
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 错误: 虚拟环境不存在，请先运行 setup_and_run.sh"
    exit 1
fi

# 检查 Streamlit 是否安装
if [ ! -f "venv/bin/streamlit" ]; then
    echo "❌ 错误: Streamlit 未安装，请先运行 setup_and_run.sh"
    exit 1
fi

# 使用虚拟环境中的 Python 直接运行 Streamlit
echo "📦 使用虚拟环境启动应用..."
echo ""

# 直接使用 venv 中的 Python 运行，避免 source 权限问题
venv/bin/python -m streamlit run app.py




