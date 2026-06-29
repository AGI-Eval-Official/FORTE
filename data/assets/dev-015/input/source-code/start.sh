#!/usr/bin/env bash
# ============================================================
# 评测平台一键启动脚本
# 用法：bash start.sh
# 启动后访问：http://localhost:8000
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ---- 颜色输出 ----
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---- 定位 Python 3.10 ----
info "检查 Python 环境..."
PYTHON=""
for candidate in python3.10 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    error "未找到 Python 3.10+，请先安装 Python 3.10 或更高版本"
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
info "使用 Python：$PYTHON ($PY_VERSION)"

# ---- 创建虚拟环境 ----
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    info "创建 Python 虚拟环境..."
    $PYTHON -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# ---- 安装后端依赖 ----
info "安装后端依赖..."
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"

# ---- 构建前端 ----
FRONTEND_DIR="$SCRIPT_DIR/frontend"
FRONTEND_DIST="$FRONTEND_DIR/dist"

if [ ! -d "$FRONTEND_DIST" ]; then
    info "构建前端..."

    if ! command -v node &>/dev/null; then
        warn "未找到 Node.js，跳过前端构建。后端 API 仍可正常访问（http://localhost:8000/docs）"
    else
        NODE_VERSION=$(node -v)
        info "Node.js 版本：$NODE_VERSION"
        cd "$FRONTEND_DIR"
        info "安装前端依赖..."
        npm install --silent
        info "构建前端..."
        npm run build
        cd "$SCRIPT_DIR"
    fi
else
    info "前端已构建，跳过（如需重新构建请删除 frontend/dist 目录）"
fi

# ---- 启动后端服务 ----
info "启动评测平台后端服务..."
info "访问地址：http://localhost:8000"
info "API 文档：http://localhost:8000/docs"
info "按 Ctrl+C 停止服务"
echo ""

cd "$SCRIPT_DIR"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
