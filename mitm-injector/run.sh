#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ====================== 配置 ======================
# 主脚本只保留自己核心业务所需的配置
CERT_DIR="$HOME/.mitmproxy"

# 引入工具函数
source ./lib/color.sh
source ./lib/check_env.sh
source ./lib/load_config.sh


# ====================== 主脚本核心函数 ======================
# 这些函数与主业务逻辑紧密相关，因此保留在主脚本中

print_banner() {
    echo -e "${CYAN}"
    print_equal_line
    echo ""
    echo "  Figma 中文本地化 - MITM 代理  v$VERSION"
    echo "  RainForest by Kailous"
    echo ""
    echo "  项目地址: https://github.com/kailous/figma-zh-CN-localized"
    echo "  项目文档: https://kailous.github.io/figma-zh-CN-localized/"
    echo ""
    print_equal_line
    echo -e "${NC}"
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

probe_upstream() {
    local target="$1"
    local timeout="${2:-5}"
    
    [ -z "$target" ] && return 2
    
    # 使用 Python 检测代理 (此处的 python3 命令来自激活的虚拟环境)
    python3 - <<PY
import socket
import sys

def parse_target(target):
    """解析代理地址"""
    target = target.strip()
    if not target:
        return None, None
    if "://" in target:
        target = target.split("://", 1)[1]
    if "/" in target:
        target = target.split("/")[0]
    if ":" in target:
        parts = target.rsplit(":", 1)
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            return None, None
    else:
        host = target
        port = 8080
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
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    
    result = sock.connect_ex((host, port))
    sock.close()
    
    if result == 0:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)
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
    
    if [ -z "${UPSTREAM_HTTP:-}" ] && [ -z "${UPSTREAM_SOCKS5:-}" ]; then
        log_info "未配置上游代理，将使用直连模式"
    fi
}

# 打印配置信息
print_config() {
    echo
    print_title_line "配置信息"
    echo
    printf "监听端口: %s\n" "$LISTEN_PORT"
    printf "语言文件: %s\n" "${LANG_FILE:-<未配置>}"
    printf "HTTP 上游: %s\n" "${UPSTREAM_HTTP:-<未配置>}"
    printf "SOCKS5 上游: %s\n" "${UPSTREAM_SOCKS5:-<未配置>}"
    printf "上游检测超时: %s秒\n" "${CHECK_TIMEOUT:-<未配置>}"
    printf "HTTP 上游状态: %s\n" "$HTTP_OK"
    printf "SOCKS5 上游状态: %s\n" "$SOCKS_OK"
    echo
}

# 启动 mitmproxy
start_mitmproxy() {
    # 构建 mitmweb 参数
    COMMON_ARGS=(
        --set allow_hosts='^(.+\.)?figma\.com(:443)?$|^kailous\.github\.io(:443)?$'
        --set connection_strategy=lazy
        # --set web_open_browser=true
        --set web_open_browser=$WEB_ADMIN_OPEN
        --set web_host=$WEB_ADMIN_HOST
        --set web_port=$WEB_ADMIN_PORT
        -p "$LISTEN_PORT"
        -s injector.py
    )
    
    MODE_ARGS=()
    
    if [ "$HTTP_OK" = "yes" ]; then
        log_info "自动选择 HTTP 上游: $UPSTREAM_HTTP"
        MODE_ARGS=( --mode "upstream:http://$UPSTREAM_HTTP" )
    elif [ "$SOCKS_OK" = "yes" ]; then
        log_info "自动选择 SOCKS5 上游: $UPSTREAM_SOCKS5"
        MODE_ARGS=( --mode "socks5://$UPSTREAM_SOCKS5" )
    else
        log_info "未检测到可用上游，使用直连模式"
    fi
    
    # 判断 web_admin_open 是否为 true
    if [ "$WEB_ADMIN_OPEN" = "true" ]; then
        log_info "启动 mitmproxy Web 界面..."
        echo
    fi
    
    if [ "${#MODE_ARGS[@]}" -gt 0 ]; then
        exec mitmweb "${COMMON_ARGS[@]}" "${MODE_ARGS[@]}"
    else
        exec mitmweb "${COMMON_ARGS[@]}"
    fi
}

# ====================== 主流程 ======================
main() {
    print_banner
    
    # --- 模块化引入 ---
    # 1. 引入环境准备脚本, 它会负责检查Python、创建venv并安装依赖
    log_info "准备运行环境..."
    source ./lib/check_env.sh
    
    # 2. 引入配置加载脚本, 它会负责读取config.yaml
    # --- 模块化结束 ---
    
    # 环境变量覆盖 (允许通过命令行环境变量覆盖配置, 优先级更高)
    export LISTEN_PORT="${PORT:-${LISTEN_PORT:-8888}}"
    export CHECK_TIMEOUT="${UPSTREAM_CHECK_TIMEOUT_SEC:-${CHECK_TIMEOUT:-5}}"
    
    # --- 运行核心业务逻辑 ---
    log_info "执行主程序..."
    check_certificate
    check_upstreams
    print_config
    
    # 使用提示
    print_title_line "使用提示"
    echo
    echo "1. 首次使用请在浏览器访问 http://mitm.it 安装证书"
    echo "2. 将系统代理设置为 127.0.0.1:$LISTEN_PORT"
    echo "3. 按 Ctrl+C 停止服务"
    echo
    print_equal_line
    echo
    # 启动服务
    start_mitmproxy
}

# 捕获中断信号 执行set_proxy.sh脚本 关闭代理
trap 'log_warning "脚本被中断"; exit 130' INT TERM

# 运行主函数
main "$@"