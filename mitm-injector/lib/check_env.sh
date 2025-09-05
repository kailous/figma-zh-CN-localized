#!/usr/bin/env bash
#
# 功能: 检查并准备项目运行所需的环境
# (这个版本可以独立运行)

# 确保脚本出错时立即退出
set -euo pipefail

# 引入颜色和样式
source ./lib/color.sh

VENV=".venv"
REQUIREMENTS_FILE="requirements.txt"

check_requirements() {
    # 这里的 log_info 现在可以被正确找到了
    log_info "检查 Python 版本..."
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 python3，请先安装 Python 3.8+"
        exit 1
    fi
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_error "Python 版本过低，需要 3.8+"
        exit 1
    fi
    log_success "Python 版本检查通过。"
}

setup_venv() {
    if [ ! -d "$VENV" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv "$VENV"
        log_success "虚拟环境创建成功。"
    else
        log_info "使用现有虚拟环境。"
    fi
    source "$VENV/bin/activate"
    python -m pip install --quiet --retries 0 --upgrade pip
    # python -m pip install --quiet --upgrade pip # 需要检查报错请恢复这一行代码
}

install_dependencies() {
    log_info "安装依赖包..."
    if python -m pip install --quiet -r "$REQUIREMENTS_FILE"; then
        log_success "依赖包安装成功。"
    else
        log_warning "默认源安装失败，尝试使用清华源..."
        if python -m pip install --quiet -i "https://pypi.tuna.tsinghua.edu.cn/simple" -r "$REQUIREMENTS_FILE"; then
            log_success "依赖包安装成功（使用清华源）。"
        else
            log_error "依赖包安装失败，请检查网络连接。"
            exit 1
        fi
    fi
}

# --- 执行环境准备流程 ---
check_requirements
setup_venv
install_dependencies

log_success "环境准备完毕！"