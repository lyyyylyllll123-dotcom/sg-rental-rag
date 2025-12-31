#!/bin/bash
# 安装依赖并运行项目的脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔧 步骤 1: 删除旧虚拟环境（如果存在）..."
rm -rf venv

echo "🔧 步骤 2: 创建新虚拟环境..."
python3 -m venv venv

echo "🔧 步骤 3: 激活虚拟环境..."
source venv/bin/activate

echo "🔧 步骤 4: 升级 pip..."
pip install --upgrade pip

echo "🔧 步骤 5: 安装依赖包..."
pip install -r requirements.txt

echo "✅ 安装完成！"
echo ""
echo "🚀 启动 Streamlit Web UI..."
streamlit run app.py







