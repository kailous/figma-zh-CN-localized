#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ====================== 配置 ======================
VENV=".venv"
REQUIREMENTS_FILE="requirements.txt"
CONFIG_FILE="config.yaml"
CERT_DIR="$HOME/.mitmproxy"

# ====================== 颜色和样式 ======================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ====================== 工具函数 ======================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                Figma 中文本地化 - MITM 代理                   ║"
    echo "║                     (figma-zh-CN-localized)                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_requirements() {
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 python3，请先安装 Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.8"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_error "Python 版本过低，需要 3.8+，当前版本：$PYTHON_VERSION"
        exit 1
    fi
    
    log_success "Python 版本检查通过: $PYTHON_VERSION"
}

setup_venv() {
    if [ ! -d "$VENV" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv "$VENV"
        log_success "虚拟环境创建成功"
    else
        log_info "使用现有虚拟环境"
    fi
    
    # 激活虚拟环境
    source "$VENV/bin/activate"
    
    # 升级 pip
    log_info "升级 pip..."
    python -m pip install --quiet --upgrade pip
}

install_dependencies() {
    log_info "安装依赖包..."
    
    # 清理代理环境变量
    unset HTTP_PROXY HTTPS_PROXY ALL_PROXY NO_PROXY
    unset http_proxy https_proxy all_proxy no_proxy
    
    export PIP_DISABLE_PIP_VERSION_CHECK=1
    export PIP_NO_CACHE_DIR=1
    
    # 定义安装函数
    pip_install() {
        python -m pip install --quiet --isolated --proxy '' "$@"
    }
    
    # 尝试默认源
    if pip_install -r "$REQUIREMENTS_FILE"; then
        log_success "依赖包安装成功"
        return
    fi
    
    # 尝试清华源
    log_warning "默认源安装失败，尝试使用清华源..."
    if pip_install -i "https://pypi.tuna.tsinghua.edu.cn/simple" -r "$REQUIREMENTS_FILE"; then
        log_success "依赖包安装成功（使用清华源）"
        return
    fi
    
    log_error "依赖包安装失败，请检查网络连接"
    exit 1
}

check_certificate() {
    if [ ! -f "$CERT_DIR/mitmproxy-ca-cert.pem" ]; then
        log_warning "未找到 mitmproxy 证书"
        log_info "首次运行时，mitmproxy 会自动生成证书"
        log_info "请在浏览器访问 http://mitm.it 安装证书"
        return 1
    fi
    
    log_success "证书文件存在: $CERT_DIR/mitmproxy-ca-cert.pem"
    return 0
}

load_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "配置文件不存在: $CONFIG_FILE"
        return 1
    fi
    
    # 使用 Python 解析 YAML
    CONFIG_PYTHON=$(python - <<'PY'
import yaml
import sys
from pathlib import Path

try:
    with Path("config.yaml").open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    
    # 默认值
    listen_port = cfg.get("listen_port", 8888)
    upstream_http = cfg.get("upstream_http", "")
    upstream_socks5 = cfg.get("upstream_socks5", "")
    timeout = cfg.get("upstream_check_timeout_sec", 5)
    lang_file = cfg.get("lang_file", "")
    force_lang = cfg.get("force_lang", False)
    
    print(f"listen_port={listen_port}")
    print(f"upstream_http={upstream_http}")
    print(f"upstream_socks5={upstream_socks5}")
    print(f"check_timeout_sec={timeout}")
    print(f"lang_file={lang_file}")
    print(f"force_lang={force_lang}")
    
except Exception as e:
    print(f"error={e}", file=sys.stderr)
    sys.exit(1)
PY
)
    
    if echo "$CONFIG_PYTHON" | grep -q "^error="; then
        log_error "配置文件解析失败"
        return 1
    fi
    
    # 解析配置
    while IFS='=' read -r key value; do
        case "$key" in
            listen_port) LISTEN_PORT="$value" ;;
            upstream_http) UPSTREAM_HTTP="$value" ;;
            upstream_socks5) UPSTREAM_SOCKS5="$value" ;;
            check_timeout_sec) CHECK_TIMEOUT="$value" ;;
            lang_file) LANG_FILE="$value" ;;
            force_lang) FORCE_LANG="$value" ;;
        esac
    done <<< "$CONFIG_PYTHON"
    
    return 0
}

probe_upstream() {
    local target="$1"
    local timeout="${2:-5}"
    
    [ -z "$target" ] && return 2
    
    # 使用 Python 检测代理
    python3 - <<PY
import socket
import sys

def parse_target(target):
    """解析代理地址"""
    target = target.strip()
    if not target:
        return None, None
    
    # 处理不同格式的地址
    # 格式1: host:port
    # 格式2: http://host:port
    # 格式3: socks5://host:port
    
    # 去除协议前缀
    if "://" in target:
        target = target.split("://", 1)[1]
    
    # 去除路径部分
    if "/" in target:
        target = target.split("/")[0]
    
    # 解析主机和端口
    if ":" in target:
        parts = target.rsplit(":", 1)
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            return None, None
    else:
        # 没有端口，使用默认值
        host = target
        port = 8080  # HTTP 代理默认端口
    
    # 处理 IPv6 地址
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]
    
    return host, port

try:
    target = """$target"""
    timeout = float("""$timeout""")
    
    host, port = parse_target(target)
    if not host:
        print(f"无法解析地址: {target}", file=sys.stderr)
        sys.exit(2)
    
    # 尝试连接
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"代理 {host}:{port} 可访问")
            sys.exit(0)
        else:
            print(f"代理 {host}:{port} 连接失败 (错误码: {result})", file=sys.stderr)
            sys.exit(1)
    except socket.gaierror as e:
        print(f"无法解析主机 {host}: {e}", file=sys.stderr)
        sys.exit(1)
    except socket.timeout:
        print(f"连接超时 {host}:{port} ({timeout}秒)", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"连接错误 {host}:{port}: {e}", file=sys.stderr)
        sys.exit(1)
        
except Exception as e:
    print(f"检测脚本错误: {e}", file=sys.stderr)
    sys.exit(2)
PY
}

check_upstreams() {
    HTTP_OK="no"
    SOCKS_OK="no"
    
    log_info "检测上游代理..."
    
    if [ -n "${UPSTREAM_HTTP:-}" ]; then
        log_info "检测 HTTP 代理: $UPSTREAM_HTTP"
        if probe_upstream "$UPSTREAM_HTTP" "$CHECK_TIMEOUT"; then
            HTTP_OK="yes"
            log_success "HTTP 上游可用: $UPSTREAM_HTTP"
        else
            log_warning "HTTP 上游不可达: $UPSTREAM_HTTP"
        fi
    fi
    
    if [ -n "${UPSTREAM_SOCKS5:-}" ]; then
        log_info "检测 SOCKS5 代理: $UPSTREAM_SOCKS5"
        if probe_upstream "$UPSTREAM_SOCKS5" "$CHECK_TIMEOUT"; then
            SOCKS_OK="yes"
            log_success "SOCKS5 上游可用: $UPSTREAM_SOCKS5"
        else
            log_warning "SOCKS5 上游不可达: $UPSTREAM_SOCKS5"
        fi
    fi
    
    # 如果都没配置，提示
    if [ -z "${UPSTREAM_HTTP:-}" ] && [ -z "${UPSTREAM_SOCKS5:-}" ]; then
        log_info "未配置上游代理，将使用直连模式"
    fi
}

print_config() {
    echo
    echo "══════════════════════ 配置信息 ══════════════════════"
    printf "%-25s : %s\n" "监听端口" "$LISTEN_PORT"
    printf "%-25s : %s\n" "本地语言文件" "${LANG_FILE:-<未配置>}"
    printf "%-25s : %s\n" "强制中文" "$FORCE_LANG"
    printf "%-25s : %s\n" "HTTP 上游" "${UPSTREAM_HTTP:-<未配置>}"
    printf "%-25s : %s\n" "SOCKS5 上游" "${UPSTREAM_SOCKS5:-<未配置>}"
    printf "%-25s : %s\n" "上游检测超时" "${CHECK_TIMEOUT}秒"
    printf "%-25s : %s\n" "HTTP 上游状态" "$HTTP_OK"
    printf "%-25s : %s\n" "SOCKS5 上游状态" "$SOCKS_OK"
    echo "══════════════════════════════════════════════════════"
    echo
}

start_mitmproxy() {
    # 构建 mitmweb 参数
    COMMON_ARGS=(
        --set allow_hosts='^(.+\.)?figma\.com(:443)?$|^kailous\.github\.io(:443)?$'
        --set connection_strategy=lazy
        --set web_open_browser=false
        --set web_host=127.0.0.1
        --set web_port=8081
        -p "$LISTEN_PORT"
        -s injector.py
    )
    
    MODE_ARGS=()
    
    # 检查强制上游模式
    FORCE_MODE="${FORCE_UPSTREAM:-}"
    
    if [ "$FORCE_MODE" = "http" ] && [ -n "${UPSTREAM_HTTP:-}" ]; then
        log_info "强制使用 HTTP 上游: $UPSTREAM_HTTP"
        MODE_ARGS=( --mode "upstream:http://$UPSTREAM_HTTP" )
    elif [ "$FORCE_MODE" = "socks" ] && [ -n "${UPSTREAM_SOCKS5:-}" ]; then
        log_info "强制使用 SOCKS5 上游: $UPSTREAM_SOCKS5"
        MODE_ARGS=( --mode "socks5://$UPSTREAM_SOCKS5" )
    elif [ "$HTTP_OK" = "yes" ]; then
        log_info "自动选择 HTTP 上游: $UPSTREAM_HTTP"
        MODE_ARGS=( --mode "upstream:http://$UPSTREAM_HTTP" )
    elif [ "$SOCKS_OK" = "yes" ]; then
        log_info "自动选择 SOCKS5 上游: $UPSTREAM_SOCKS5"
        MODE_ARGS=( --mode "socks5://$UPSTREAM_SOCKS5" )
    else
        log_info "未检测到可用上游，使用直连模式"
    fi
    
    # 启动 mitmweb
    log_info "启动 mitmproxy Web 界面..."
    log_info "Web 界面: http://127.0.0.1:8081"
    echo
    
    if [ "${#MODE_ARGS[@]}" -gt 0 ]; then
        exec mitmweb "${COMMON_ARGS[@]}" "${MODE_ARGS[@]}"
    else
        exec mitmweb "${COMMON_ARGS[@]}"
    fi
}

# ====================== 主流程 ======================
main() {
    print_banner
    
    # 基础检查
    check_requirements
    setup_venv
    install_dependencies
    
    # 配置加载 - 初始化默认值
    LISTEN_PORT="8888"
    UPSTREAM_HTTP=""
    UPSTREAM_SOCKS5=""
    CHECK_TIMEOUT="5"
    LANG_FILE=""
    FORCE_LANG="false"
    
    # 加载配置文件
    load_config
    
    # 环境变量覆盖
    LISTEN_PORT="${PORT:-${LISTEN_PORT:-8888}}"
    CHECK_TIMEOUT="${UPSTREAM_CHECK_TIMEOUT_SEC:-${CHECK_TIMEOUT:-5}}"
    
    # 证书检查
    check_certificate
    
    # 上游检测
    check_upstreams
    
    # 显示配置
    print_config
    
    # 使用提示
    echo -e "${YELLOW}💡 使用提示：${NC}"
    echo "1. 首次使用请在浏览器访问 ${CYAN}http://mitm.it${NC} 安装证书"
    echo "2. 将系统代理设置为 ${CYAN}127.0.0.1:$LISTEN_PORT${NC}"
    echo "3. Web 管理界面: ${CYAN}http://127.0.0.1:8081${NC}"
    echo "4. 按 ${CYAN}Ctrl+C${NC} 停止服务"
    echo
    echo "═════════════════════════════════════════════════════════════════"
    
    # 启动服务
    start_mitmproxy
}

# 捕获中断信号
trap 'log_warning "脚本被中断"; exit 130' INT TERM

# 运行主函数
main "$@"