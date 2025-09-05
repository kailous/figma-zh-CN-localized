#!/usr/bin/env bash
#
# 功能: 设置网络代理


set -euo pipefail
cd "$(dirname "$0")"


source ./lib/check_env.sh
source ./lib/load_config.sh

# 格式化信息获取主机和端口
# 主机
HOST=$(echo "$UPSTREAM_HTTP" | cut -d':' -f1)
# http&https 端口
HTTP_PORT=$(echo "$UPSTREAM_HTTP" | cut -d':' -f2)
# socks5 端口
SOCKS5_PORT=$(echo "$UPSTREAM_SOCKS5" | cut -d':' -f2)
# MitM 监听端口
MITM_PORT=$(echo "$LISTEN_PORT")

# 组合代理地址
# MitM 代理地址
MITM_PROXY="$HOST $MITM_PORT"
# 上游 HTTP 代理地址
UPSTREAM_HTTP_PROXY="$HOST $HTTP_PORT"
# 上游 SOCKS5 代理地址
UPSTREAM_SOCKS5_PROXY="$HOST $SOCKS5_PORT"

# 独立函数 检查是否需要管理员权限
check_admin() {
    if [ "$(id -u)" -ne 0 ]; then
        log_error "需要 root 权限来设置系统代理"
        exit 1
    fi
}

# 独立函数设置macOS系统代理为 MitM 代理
set_mitm_proxy() {

    # 检查是否需要root
    check_admin

    # 设置 HTTP 代理
    networksetup -setwebproxy "Wi-Fi" $MITM_PROXY
    networksetup -setsecurewebproxy "Wi-Fi" $MITM_PROXY

    # 设置 SOCKS5 代理
    networksetup -setsocksfirewallproxy "Wi-Fi" $MITM_PROXY

    log_success "系统代理已设置为 MitM 代理"
}

# 独立函数恢复代理为上游代理
restore_upstream_proxy() {

    # 检查是否需要root
    check_admin

    # 设置 HTTP 代理
    networksetup -setwebproxy "Wi-Fi" $UPSTREAM_HTTP_PROXY
    networksetup -setsecurewebproxy "Wi-Fi" $UPSTREAM_HTTP_PROXY

    # 设置 SOCKS5 代理
    networksetup -setsocksfirewallproxy "Wi-Fi" $UPSTREAM_SOCKS5_PROXY

    log_success "系统代理已恢复为上游代理"
}

# 独立函数移除系统代理
remove_proxy() {
    # 移除 HTTP 代理
    networksetup -setwebproxystate "Wi-Fi" off
    networksetup -setsecurewebproxystate "Wi-Fi" off

    # 移除 SOCKS5 代理
    networksetup -setsocksfirewallproxystate "Wi-Fi" off

    log_success "系统代理已移除"
}

# 独立函数检查系统代理是否已设置
check_proxy_status() {
    local proxy_info
    proxy_info=$(scutil --proxy)

    # 判断 HTTP 代理
    local http_enabled http_host http_port
    http_enabled=$(echo "$proxy_info" | awk -F': ' '/HTTPEnable/ {print $2}')
    if [ "$http_enabled" = "1" ]; then
        http_host=$(echo "$proxy_info" | awk -F': ' '/HTTPProxy/ {print $2}')
        http_port=$(echo "$proxy_info" | awk -F': ' '/HTTPPort/ {print $2}')
        # 判断$http_port是否等于$MITM_PORT
        if [ "$http_port" = "$MITM_PORT" ]; then
            log_info "HTTP 代理开启：$http_host:$http_port - [MitM]"
            # 设定变量 PROXY_HTTP_SERVER 为 MitM
            PROXY_HTTP_SERVER="MitM"
        else
            log_info "HTTP 代理开启：$http_host:$http_port - [Upstream]"
            # 设定变量 PROXY_HTTP_SERVER 为 Upstream
            PROXY_HTTP_SERVER="Upstream"
        fi
    else
        log_info "HTTP 代理未开启"
    fi

    # 判断 HTTPS 代理
    local https_enabled https_host https_port
    https_enabled=$(echo "$proxy_info" | awk -F': ' '/HTTPSEnable/ {print $2}')
    if [ "$https_enabled" = "1" ]; then
        https_host=$(echo "$proxy_info" | awk -F': ' '/HTTPSProxy/ {print $2}')
        https_port=$(echo "$proxy_info" | awk -F': ' '/HTTPSPort/ {print $2}')
        # 判断$https_port是否等于$MITM_PORT
        if [ "$https_port" = "$MITM_PORT" ]; then
            log_info "HTTPS 代理开启：$https_host:$https_port - [MitM]"
            # 设定变量 PROXY_HTTPS_SERVER 为 MitM
            PROXY_HTTPS_SERVER="MitM"
        else
            log_info "HTTPS 代理开启：$https_host:$https_port - [Upstream]"
            # 设定变量 PROXY_HTTPS_SERVER 为 Upstream
            PROXY_HTTPS_SERVER="Upstream"
        fi
    else
        log_info "HTTPS 代理未开启"
    fi

    # 判断 SOCKS5 代理
    local socks_enabled socks_host socks_port
    socks_enabled=$(echo "$proxy_info" | awk -F': ' '/SOCKSEnable/ {print $2}')
    if [ "$socks_enabled" = "1" ]; then
        socks_host=$(echo "$proxy_info" | awk -F': ' '/SOCKSProxy/ {print $2}')
        socks_port=$(echo "$proxy_info" | awk -F': ' '/SOCKSPort/ {print $2}')
        # 判断$ socks_port是否等于$MITM_PORT
        if [ "$socks_port" = "$MITM_PORT" ]; then
            log_info "SOCKS 代理开启：$socks_host:$socks_port - [MitM]"
            # 设定变量 PROXY_SOCKS_SERVER 为 MitM
            PROXY_SOCKS_SERVER="MitM"
        else
            log_info "SOCKS 代理开启：$socks_host:$socks_port - [Upstream]"
            # 设定变量 PROXY_SOCKS_SERVER 为 Upstream
            PROXY_SOCKS_SERVER="Upstream"
        fi
    else
        log_info "SOCKS 代理未开启"
    fi

    # 检查 PROXY_SOCKS_SERVER PROXY_HTTPS_SERVER PROXY_HTTP_SERVER
    # 3种情况
    # 1. 全部 MitM
    # 2. 全部 Upstream
    # 3. 混合
    if [ "$PROXY_SOCKS_SERVER" = "MitM" ] && [ "$PROXY_HTTPS_SERVER" = "MitM" ] && [ "$PROXY_HTTP_SERVER" = "MitM" ]; then
        log_info "当前代理模式为 MitM"
        # 设定变量 PROXY_SERVER 为 MitM
        PROXY_SERVER="MitM"
    elif [ "$PROXY_SOCKS_SERVER" = "Upstream" ] && [ "$PROXY_HTTPS_SERVER" = "Upstream" ] && [ "$PROXY_HTTP_SERVER" = "Upstream" ]; then
        log_info "当前代理模式为 Upstream"
        # 设定变量 PROXY_SERVER 为 Upstream
        PROXY_SERVER="Upstream"
    else
        log_info "当前代理模式为混合"
        # 提问修复为 MitM 或 Upstream
        log_info "请选择修复为 MitM 或 Upstream"
        read -p "请输入 MitM 或 Upstream: " proxy_choice
        if [ "$proxy_choice" = "MitM" ]; then
            set_mitm_proxy
        elif [ "$proxy_choice" = "Upstream" ]; then
            restore_upstream_proxy
        else
            log_error "无效选择"
            exit 1
        fi
    fi
}

# 通过参数判断执行哪个函数
case "$1" in
    "mitm")
        set_mitm_proxy # 设定系统代理为 MitM
        ;;
    "upstream")
        restore_upstream_proxy # 设定系统代理为 Upstream
        ;;
    "remove")
        remove_proxy # 移除系统代理
        ;;
    "check")
        check_proxy_status # 检查系统代理状态
        ;;
    *)
        log_error "用法: $0 {mitm|upstream|remove|check}"
        exit 1
        ;;
esac