#!/usr/bin/env bash
# mitmproxy 根证书安装（极简版）
# 1) 优先使用 ~/.mitmproxy/mitmproxy-ca-cert.pem（纯证书）
# 2) 若只有 mitmproxy-ca.pem（含私钥），提取证书段后安装

set -euo pipefail

# 让脚本可在任意路径下执行：将引用与文件操作锚定到脚本目录
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 引入颜色和样式（必须存在于脚本同级的 lib/color.sh）
# 例如：mitm-injector/lib/color.sh
source "$SCRIPT_DIR/lib/color.sh"

# 目标保存文件（最终用于安装的“纯证书”）——仍保存在当前工作目录
MITM_CA_FILE="${1:-mitmproxy-ca.pem}"

# 从来源获取证书（本地优先，其次通过代理/直连拉取）
request_mitm_ca() {
    local local_cert_only="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
    local local_bundle="$HOME/.mitmproxy/mitmproxy-ca.pem"

    # 1) 优先使用纯证书
    if [ -f "$local_cert_only" ]; then
        cp -f "$local_cert_only" "$MITM_CA_FILE"
        log_success "已从本地拷贝纯证书 → $MITM_CA_FILE"
        return 0
    fi

    # 2) 其次用 bundle（含私钥）再提取
    if [ -f "$local_bundle" ]; then
        cp -f "$local_bundle" "$MITM_CA_FILE"
        log_success "已从本地拷贝 bundle → $MITM_CA_FILE（稍后提取证书段）"
        return 0
    fi

    # 3) 再尝试网络获取（直连，若失败你可改成走代理）
    log_info "下载 mitmproxy 根证书（可能是 bundle）..."
    if ! curl -fsSL -o "$MITM_CA_FILE" "http://mitm.it/cert/pem"; then
        log_error "下载失败：无法获取 http://mitm.it/cert/pem"
        exit 1
    fi

    if ! grep -q "BEGIN CERTIFICATE" "$MITM_CA_FILE"; then
        log_error "下载内容不是 PEM 证书"
        exit 1
    fi
    log_success "已下载证书文件 → $MITM_CA_FILE"
}

# 确保文件是“纯证书”（不含私钥），必要时从 bundle 中提取第一段证书
ensure_cert_only() {
    # 文件里如果出现私钥或多段内容，先提取第一段 CERTIFICATE
    if grep -q "BEGIN RSA PRIVATE KEY\|BEGIN PRIVATE KEY" "$MITM_CA_FILE"; then
        log_info "检测到私钥，提取证书段..."
        awk '
          BEGIN{inblk=0}
          /-----BEGIN CERTIFICATE-----/ {inblk=1; print; next}
          /-----END CERTIFICATE-----/   {if(inblk){print; exit}}
          {if(inblk) print}
        ' "$MITM_CA_FILE" > "${MITM_CA_FILE}.certonly"
        mv -f "${MITM_CA_FILE}.certonly" "$MITM_CA_FILE"
        log_success "已提取为纯证书 → $MITM_CA_FILE"
    fi

    # 即使没有私钥，也可能包含多段；仅保留第一段证书
    if awk '/-----BEGIN CERTIFICATE-----/{c++} END{exit !(c>1)}' "$MITM_CA_FILE"; then
        log_info "检测到多段证书，保留第一段..."
        awk '
          BEGIN{inblk=0}
          /-----BEGIN CERTIFICATE-----/ {inblk=1; print; next}
          /-----END CERTIFICATE-----/   {if(inblk){print; exit}}
          {if(inblk) print}
        ' "$MITM_CA_FILE" > "${MITM_CA_FILE}.first"
        mv -f "${MITM_CA_FILE}.first" "$MITM_CA_FILE"
        log_success "已保留第一段证书 → $MITM_CA_FILE"
    fi

    # 最后再做一次基本校验
    if ! openssl x509 -in "$MITM_CA_FILE" -noout >/dev/null 2>&1; then
        log_error "证书解析失败：格式仍不正确（${MITM_CA_FILE}）"
        exit 1
    fi
}

# 安装 mitmproxy 根证书
install_mitm_ca() {
    log_info "安装 mitmproxy 根证书..."
    if ! sudo security add-trusted-cert -d -r trustRoot \
        -k /Library/Keychains/System.keychain "$MITM_CA_FILE"; then
        log_error "安装 mitmproxy 根证书失败"
        exit 1
    fi
    log_success "mitmproxy 根证书已安装为受信任的根证书"
}

# 主流程
request_mitm_ca
ensure_cert_only
install_mitm_ca