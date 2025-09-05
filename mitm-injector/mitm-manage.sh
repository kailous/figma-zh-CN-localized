#!/usr/bin/env bash
# mitm-manage.sh - mitmproxy 管理工具
set -euo pipefail
cd "$(dirname "$0")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

VENV=".venv"
CERT_DIR="$HOME/.mitmproxy"

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

# 激活虚拟环境
activate_venv() {
    if [ ! -d "$VENV" ]; then
        log_error "虚拟环境不存在，请先运行 ./run.sh"
        exit 1
    fi
    source "$VENV/bin/activate"
}

# 显示帮助信息
show_help() {
    cat << EOF
mitmproxy 管理工具

用法: $0 <命令> [选项]

命令:
  install-cert    安装 mitmproxy 证书到系统
  trust-cert      信任 mitmproxy 证书
  show-cert        显示证书信息
  reset-cert       重置证书（删除并重新生成）
  status           显示服务状态
  logs             显示日志
  test-config      测试配置文件
  clean            清理临时文件和缓存

选项:
  -h, --help       显示此帮助信息

EOF
}

# 安装证书
install_cert() {
    log_info "检查 mitmproxy 证书..."
    
    if [ ! -f "$CERT_DIR/mitmproxy-ca-cert.pem" ]; then
        log_warning "证书不存在，正在生成..."
        activate_venv
        mitmdump --version > /dev/null 2>&1 || true
    fi
    
    if [ ! -f "$CERT_DIR/mitmproxy-ca-cert.pem" ]; then
        log_error "证书生成失败"
        exit 1
    fi
    
    log_success "证书已生成: $CERT_DIR/mitmproxy-ca-cert.pem"
    
    # 根据操作系统安装证书
    case "$(uname -s)" in
        Darwin*)
            log_info "检测到 macOS 系统"
            install_cert_macos
            ;;
        Linux*)
            log_info "检测到 Linux 系统"
            install_cert_linux
            ;;
        *)
            log_error "不支持的操作系统"
            exit 1
            ;;
    esac
}

# macOS 安装证书
install_cert_macos() {
    local cert_file="$CERT_DIR/mitmproxy-ca-cert.pem"
    
    # 添加到钥匙串
    if security find-certificate -c "mitmproxy" /Library/Keychains/System.keychain > /dev/null 2>&1; then
        log_warning "证书已存在于系统钥匙串中"
    else
        log_info "正在添加证书到系统钥匙串..."
        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$cert_file"
        log_success "证书已添加到系统钥匙串"
    fi
    
    # 设置信任
    log_info "设置证书信任..."
    sudo security set-trust -d -r trustAsRoot -p ssl -p basic "$cert_file"
    log_success "证书信任设置完成"
    
    log_info "请重启浏览器使证书生效"
}

# Linux 安装证书
install_cert_linux() {
    local cert_file="$CERT_DIR/mitmproxy-ca-cert.pem"
    local cert_dest="/usr/local/share/ca-certificates/mitmproxy-ca-cert.crt"
    
    # 复制证书
    sudo mkdir -p /usr/local/share/ca-certificates
    sudo cp "$cert_file" "$cert_dest"
    sudo update-ca-certificates
    
    log_success "证书已安装到系统"
    log_info "请重启浏览器使证书生效"
}

# 信任证书
trust_cert() {
    log_info "打开证书信任页面..."
    
    # 检查是否有 mitmproxy 运行
    if pgrep -f "mitm(web|dump)" > /dev/null; then
        log_success "检测到 mitmproxy 正在运行"
        echo "请在浏览器访问: http://mitm.it"
    else
        log_warning "未检测到 mitmproxy 运行"
        echo "请先运行 ./run.sh，然后在浏览器访问: http://mitm.it"
    fi
}

# 显示证书信息
show_cert() {
    if [ ! -f "$CERT_DIR/mitmproxy-ca-cert.pem" ]; then
        log_error "证书不存在"
        exit 1
    fi
    
    echo
    echo "═══════════════ 证书信息 ════════════════"
    openssl x509 -in "$CERT_DIR/mitmproxy-ca-cert.pem" -text -noout | grep -E "(Subject:|Issuer:|Not Before|Not After)"
    echo "════════════════════════════════════════"
    echo
}

# 重置证书
reset_cert() {
    log_warning "这将删除所有现有的 mitmproxy 证书"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi
    
    # 停止可能运行的 mitmproxy
    pkill -f "mitm(web|dump)" 2>/dev/null || true
    
    # 删除证书目录
    if [ -d "$CERT_DIR" ]; then
        rm -rf "$CERT_DIR"
        log_success "证书已删除"
    fi
    
    log_info "下次运行 mitmproxy 时会自动生成新证书"
}

# 显示状态
show_status() {
    echo
    echo "═══════════════════ 状态信息 ═══════════════════"
    
    # 检查虚拟环境
    if [ -d "$VENV" ]; then
        echo -e "虚拟环境: ${GREEN}存在${NC}"
    else
        echo -e "虚拟环境: ${RED}不存在${NC}"
    fi
    
    # 检查证书
    if [ -f "$CERT_DIR/mitmproxy-ca-cert.pem" ]; then
        echo -e "证书文件: ${GREEN}存在${NC}"
        show_cert | head -5
    else
        echo -e "证书文件: ${RED}不存在${NC}"
    fi
    
    # 检查进程
    if pgrep -f "mitm(web|dump)" > /dev/null; then
        echo -e "mitmproxy: ${GREEN}运行中${NC}"
        pgrep -f "mitm(web|dump)" | head -5
    else
        echo -e "mitmproxy: ${RED}未运行${NC}"
    fi
    
    echo "═════════════════════════════════════════════"
    echo
}

# 显示日志
show_logs() {
    if pgrep -f "mitmweb" > /dev/null; then
        log_info "显示 mitmweb 日志..."
        # 这里可以根据实际情况调整日志获取方式
        echo "日志功能需要额外的配置"
    else
        log_warning "mitmweb 未运行"
    fi
}

# 测试配置
test_config() {
    log_info "测试配置文件..."
    
    if [ ! -f "config.yaml" ]; then
        log_error "config.yaml 不存在"
        exit 1
    fi
    
    activate_venv
    
    # 使用 Python 验证配置
    python - <<'PY'
import yaml
from pathlib import Path

try:
    with Path("config.yaml").open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    print("配置文件格式正确")
    
    # 检查必需的配置项
    required_keys = ["listen_port"]
    for key in required_keys:
        if key not in config:
            print(f"警告: 缺少配置项 {key}")
    
    # 显示配置摘要
    print("\n配置摘要:")
    for key, value in config.items():
        print(f"  {key}: {value}")
        
except yaml.YAMLError as e:
    print(f"配置文件格式错误: {e}")
    exit(1)
except Exception as e:
    print(f"其他错误: {e}")
    exit(1)
PY
}

# 清理
clean() {
    log_info "清理临时文件..."
    
    # 清理 Python 缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # 清理日志文件
    rm -f *.log 2>/dev/null || true
    
    log_success "清理完成"
}

# 主逻辑
case "${1:-}" in
    install-cert)
        install_cert
        ;;
    trust-cert)
        trust_cert
        ;;
    show-cert)
        show_cert
        ;;
    reset-cert)
        reset_cert
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test-config)
        test_config
        ;;
    clean)
        clean
        ;;
    -h|--help|"")
        show_help
        ;;
    *)
        log_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac