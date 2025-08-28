#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
PORT="${PORT:-8888}"

echo "👉 本脚本只在 venv 内运行，不依赖系统 Homebrew/全局 mitmproxy。"

# 1) 创建 & 激活 venv
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtual environment at $VENV ..."
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

# 2) 彻底禁用一切代理环境变量
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY
unset http_proxy https_proxy all_proxy no_proxy

# 3) pip 全程“隔离模式” + 禁用代理 + 关版本检查
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_CACHE_DIR=1

pip_i() {
  # --isolated 忽略全局/用户 pip.conf；--proxy '' 强制不走代理
  python -m pip install --quiet --isolated --proxy '' "$@"
}

# 4) 先把 pip 自身就地升到可用（同样隔离且禁代理）
echo "==> Upgrading pip in venv (isolated, no-proxy)..."
python -m pip install --quiet --isolated --proxy '' -U pip || true

# 5) 安装依赖（默认源失败则自动切清华镜像）
echo "==> Installing mitmproxy & PyYAML in venv (isolated, no-proxy)..."
if ! pip_i "mitmproxy>=10.0" "PyYAML>=6.0"; then
  echo "   Default index failed. Retrying with TUNA mirror..."
  if ! pip_i --index-url "https://pypi.tuna.tsinghua.edu.cn/simple" \
      "mitmproxy>=10.0" "PyYAML>=6.0"; then
    echo "❌ 安装 mitmproxy/PyYAML 失败。"
    echo "   排查建议："
    echo "   1) 是否存在 ~/.pip/pip.conf 或 ~/.config/pip/pip.conf 设置了 proxy/index？"
    echo "      如有，可暂时重命名： mv ~/.pip/pip.conf ~/.pip/pip.conf.bak"
    echo "   2) 终端里执行： env | egrep -i 'proxy|https_proxy|http_proxy' 确认为空。"
    echo "   3) 若仍失败，可把公司网络代理/网关切到直连后再试。"
    exit 1
  fi
fi

# 6) 文件检查
[ -f injector.py ] || { echo "❌ 缺少 injector.py"; exit 1; }

# 7) 读取配置（可选）
LISTEN_PORT="$PORT"
if [ -f config.yaml ]; then
  # 仅从 config.yaml 读取 listen_port（没有就用默认）
  LP=$(python - <<'PY'
import yaml, sys
try:
    cfg=yaml.safe_load(open("config.yaml","r",encoding="utf-8")) or {}
    print(int(cfg.get("listen_port", 0)))
except Exception:
    print(0)
PY
)
  if [ "${LP:-0}" -gt 0 ]; then LISTEN_PORT="$LP"; fi
fi

echo "💡 首次使用：请在浏览器访问 http://mitm.it 安装并信任证书，并将系统代理设置为 127.0.0.1:8888"
echo "==> Starting mitmweb on :$LISTEN_PORT (venv) ..."

exec mitmweb \
  --set connection_strategy=lazy \
  --set web_open_browser=false \
  --set web_show_client=false \
  -p "$LISTEN_PORT" \
  -s injector.py