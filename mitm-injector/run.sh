#!/usr/bin/env bash

# # 引入配置
# source ./lib/load_config.sh

# 获取当前脚本所在目录
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")

# 切换到脚本所在目录
cd "$SCRIPT_DIR"

# 启动代理
sudo ./set_proxy.sh --start

# 判断是否第一次启动
if [ "$FIRST_START" = "true" ]; then
    # 安装证书
    sudo ./install_mitm_ca.sh
fi

# 启动 mitm-injector
./app.sh

# ── 清理函数 ──
set -euo pipefail


cleanup() {
  # 停止代理
  sudo "./set_proxy.sh" --stop || true
  echo "[info] 已执行清理"
}

# trap 在这里安装
trap cleanup EXIT
trap cleanup INT TERM HUP

# 主逻辑
echo "[info] 运行中，Ctrl+C 退出"
while true; do
  sleep 1
done