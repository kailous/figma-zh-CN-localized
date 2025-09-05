#!/usr/bin/env bash
#
# 功能: 读取 config.yaml 并将配置项导出为环境变量

set -euo pipefail

# 引用主脚本的工具函数
source <(grep -E 'RED=|GREEN=|YELLOW=|BLUE=|CYAN=|NC=|log_' run.sh)

CONFIG_FILE="config.yaml"
VENV_PYTHON="./.venv/bin/python3"

if [ ! -f "$CONFIG_FILE" ]; then
    log_warning "配置文件不存在: $CONFIG_FILE"
    return 1
fi

log_info "加载配置文件 $CONFIG_FILE..."
# 使用虚拟环境的 Python 来解析 YAML
CONFIG_PYTHON=$("$VENV_PYTHON" - <<'PY'
import yaml, sys
from pathlib import Path

try:
    with Path("config.yaml").open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    print(f"export VERSION='{cfg.get('version', '1.0.0')}'")
    print(f"export LISTEN_PORT={cfg.get('listen_port', 8888)}")
    print(f"export UPSTREAM_HTTP='{cfg.get('upstream_http', '')}'")
    print(f"export UPSTREAM_SOCKS5='{cfg.get('upstream_socks5', '')}'")
    print(f"export CHECK_TIMEOUT={cfg.get('upstream_check_timeout_sec', 5)}")

    # 修复 remote_url：二级 key
    lp = cfg.get('language_pack', {}) or {}
    local_path = (lp.get('local_path') or '').strip()
    remote_url = (lp.get('remote_url') or '').strip()
    # 本地优先，否则用远程
    lang_file = local_path if local_path else remote_url
    print(f"export LANG_FILE='{lang_file}'")
    print(f"export FORCE_LANG={cfg.get('force_lang', False)}")

    # 后台管理界面
    print(f"export WEB_ADMIN_PORT='{cfg.get('web_admin_port', '8081')}'")
    print(f"export WEB_ADMIN_HOST='{cfg.get('web_admin_host', '127.0.0.1')}'")
    print(f"export WEB_ADMIN_OPEN={cfg.get('web_admin_open', 'false')}")

except Exception as e:
    print(f"echo '配置文件解析失败: {e}' >&2", file=sys.stderr)
    sys.exit(1)
PY
)

if [ $? -ne 0 ]; then
    log_error "$CONFIG_PYTHON"
    exit 1
fi

# 执行 Python 脚本生成的 export 命令，将配置加载到当前 Shell
eval "$CONFIG_PYTHON"
log_success "配置加载完成。"