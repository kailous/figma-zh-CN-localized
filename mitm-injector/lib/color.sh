#!/usr/bin/env bash
# ./lib/color.sh
# ====================== 颜色和样式 ======================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
# ====================== 工具函数 ======================
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# 打印全宽横线（用 ─）
print_line() {
    local cols=$(tput cols 2>/dev/null || echo 80)
    printf '%*s\n' "$cols" '' | tr ' ' '─'
}

# 打印全宽横线（用 =）
print_equal_line() {
    local cols=$(tput cols 2>/dev/null || echo 80)
    printf '%*s\n' "$cols" '' | tr ' ' '═'
}

# 打印带标题的分隔线，例如 " 配置信息 "
print_title_line() {
    local title="$1"
    local filler="${2:-═}"
    local cols

    cols=$(tput cols 2>/dev/null || echo 80)

    # 计算显示宽度：中文/全角算2列，半角/英文算1列
    # 依赖 python3（macOS 一般自带；若无 python3，可以改用你项目里的 venv）
    local disp_len
    disp_len=$(python3 - <<'PY' "$title"
import sys, unicodedata
s = sys.argv[1]
w = 0
for ch in s:
    ea = unicodedata.east_asian_width(ch)
    w += 2 if ea in ('W','F') else 1   # 宽/全角=2列，其它=1列
print(w)
PY
)

    # 中间文本两侧各留一个空格，美观
    local text=" $title "
    local text_len=$(( disp_len + 2 ))

    # 计算左右填充
    if [ "$text_len" -ge "$cols" ]; then
        # 标题太长，直接打印标题（不截断，以免乱码）
        printf "%s\n" "$title"
        return
    fi
    local left=$(( (cols - text_len) / 2 ))
    local right=$(( cols - text_len - left ))

    # 打印
    printf '%*s' "$left" '' | tr ' ' "$filler"
    printf "%s" "$text"
    printf '%*s' "$right" '' | tr ' ' "$filler"
    echo
}