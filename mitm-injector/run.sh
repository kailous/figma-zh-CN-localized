#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"

echo "👉 本脚本只在 venv 内运行，不依赖系统 Homebrew/全局 mitmproxy。"

# --- 1) venv ---
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtual environment at $VENV ..."
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

# --- 2) 禁用一切代理环境变量，避免 pip/探测被劫持 ---
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY
unset http_proxy https_proxy all_proxy no_proxy

export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_CACHE_DIR=1

pip_i() {
  # --isolated 忽略全局 pip.conf；--proxy '' 强制不走代理
  python -m pip install --quiet --isolated --proxy '' "$@"
}

echo "==> Upgrading pip in venv (isolated, no-proxy)..."
python -m pip install --quiet --isolated --proxy '' -U pip || true

echo "==> Installing mitmproxy & PyYAML in venv (isolated, no-proxy)..."
if ! pip_i "mitmproxy>=10.0" "PyYAML>=6.0"; then
  echo "   Default index failed. Retrying with TUNA mirror..."
  if ! pip_i --index-url "https://pypi.tuna.tsinghua.edu.cn/simple" "mitmproxy>=10.0" "PyYAML>=6.0"; then
    echo "❌ 安装 mitmproxy/PyYAML 失败。请检查是否仍有系统/终端代理拦截，或暂时切直连后重试。"
    exit 1
  fi
fi

# --- 3) 读取配置（用 Python 输出 key=value，Bash 3 也能稳妥解析） ---
CFG_TEXT="$(python - <<'PY'
import yaml
from pathlib import Path

try:
    cfg = {}
    p = Path("config.yaml")
    if p.exists():
        with p.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
except Exception:
    cfg = {}

def to_int(x, d):
    try:
        return int(x)
    except Exception:
        return d

def to_float(x, d):
    try:
        return float(x)
    except Exception:
        return d

listen_port = to_int((cfg.get("listen_port", 8888) or 8888), 8888)
up_http = (cfg.get("upstream_http") or "").strip()
up_socks = (cfg.get("upstream_socks5") or "").strip()
timeout = to_float((cfg.get("upstream_check_timeout_sec", 5) or 5), 5.0)

print(f"listen_port={listen_port}")
print(f"upstream_http={up_http}")
print(f"upstream_socks5={up_socks}")
print(f"check_timeout_sec={timeout}")
PY
)"

# 默认值
LISTEN_PORT=8888
UP_HTTP=""
UP_SOCKS=""
CHECK_TIMEOUT=5

# 解析 key=value（兼容 CRLF）
while IFS='=' read -r K V; do
  V="${V%$'\r'}"
  case "$K" in
    listen_port) LISTEN_PORT="$V" ;;
    upstream_http) UP_HTTP="$V" ;;
    upstream_socks5) UP_SOCKS="$V" ;;
    check_timeout_sec) CHECK_TIMEOUT="$V" ;;
    *) : ;;
  esac
done <<< "$CFG_TEXT"

# 允许用环境变量覆盖（可选）
LISTEN_PORT="${PORT:-$LISTEN_PORT}"
CHECK_TIMEOUT="${UPSTREAM_CHECK_TIMEOUT_SEC:-$CHECK_TIMEOUT}"

# --- 4) 探测上游可用性（支持 host:port / http://host:port / socks5://host:port） ---
probe() {
  # $1: 目标，如 127.0.0.1:8234 或 http://127.0.0.1:8234
  # $2: 超时秒
  python - <<'PY' "$@"
import socket, sys
from urllib.parse import urlparse

# 兼容被空参数调用的情况：直接失败返回 2
if len(sys.argv) < 3:
    sys.exit(2)

target = (sys.argv[1] or "").strip()
try:
    timeout = float(sys.argv[2])
except Exception:
    timeout = 5.0

if not target:
    sys.exit(2)

def host_port(x: str):
    x = x.strip()
    if "://" in x:
        p = urlparse(x)
        host = p.hostname
        port = p.port
        if port is None:
            if p.scheme == "http":
                port = 80
            elif p.scheme == "socks5":
                port = 1080
            elif p.scheme == "https":
                port = 443
            else:
                port = 80
        return host, int(port)
    if ":" in x:
        h, pr = x.rsplit(":", 1)
        return h, int(pr)
    return x, 80

try:
    h, prt = host_port(target)
    with socket.create_connection((h, prt), timeout=timeout):
        pass
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
}

HTTP_OK="no"
SOCKS_OK="no"

# 仅当有配置值时才探测；把 probe 的 stderr 屏蔽，避免打印 Traceback
if [ -n "$UP_HTTP" ]; then
  if probe "$UP_HTTP" "$CHECK_TIMEOUT" 2>/dev/null; then HTTP_OK="yes"; fi
fi
if [ -n "$UP_SOCKS" ]; then
  if probe "$UP_SOCKS" "$CHECK_TIMEOUT" 2>/dev/null; then SOCKS_OK="yes"; fi
fi

echo "==> Config:"
printf "   %-23s : %s\n" "监听端口" "$LISTEN_PORT"
printf "   %-23s : %s\n" "上游 HTTP 地址" "${UP_HTTP:-<empty>}"
printf "   %-23s : %s\n" "上游 SOCKS5 地址" "${UP_SOCKS:-<empty>}"
printf "   %-23s : %s\n" "检查上游超时秒" "$CHECK_TIMEOUT"
printf "   %-23s : <%s>\n" "上游 HTTP 地址可达" "$HTTP_OK"
printf "   %-23s : <%s>\n" "上游 SOCKS5 地址可达" "$SOCKS_OK"

# --- 5) 组装 mitmweb 启动参数 ---
COMMON_ARGS=(
  --set connection_strategy=lazy
  --set web_open_browser=false
  --set web_show_client=false
  -p "$LISTEN_PORT"
  -s injector.py
)

MODE_ARGS=()

# 强制上游（可选）：FORCE_UPSTREAM=http | socks
FORCE="${FORCE_UPSTREAM:-}"

if [ "$FORCE" = "http" ] && [ -n "$UP_HTTP" ]; then
  echo "✅ FORCE_UPSTREAM=http 生效：上游 $UP_HTTP"
  MODE_ARGS=( --mode "upstream:$UP_HTTP" )
elif [ "$FORCE" = "socks" ] && [ -n "$UP_SOCKS" ]; then
  echo "✅ FORCE_UPSTREAM=socks 生效：上游 $UP_SOCKS"
  MODE_ARGS=( --mode "socks5:$UP_SOCKS" )
else
  if [ "$HTTP_OK" = "yes" ]; then
    echo "✅ 检测到可用 HTTP 上游：$UP_HTTP"
    MODE_ARGS=( --mode "upstream:$UP_HTTP" )
  elif [ "$SOCKS_OK" = "yes" ]; then
    echo "✅ 检测到可用 SOCKS5 上游：$UP_SOCKS"
    MODE_ARGS=( --mode "socks5:$UP_SOCKS" )
  else
    echo "⚠️ 未检测到可用上游，采用直连模式。"
    MODE_ARGS=()
  fi
fi

echo "💡 首次使用：请在浏览器访问 http://mitm.it 安装并信任证书。并将代理端口全部设置为$LISTEN_PORT"
echo "==> Starting mitmweb on :$LISTEN_PORT (venv) ..."

if [ "${#MODE_ARGS[@]}" -gt 0 ]; then
  exec mitmweb "${COMMON_ARGS[@]}" "${MODE_ARGS[@]}"
else
  exec mitmweb "${COMMON_ARGS[@]}"
fi