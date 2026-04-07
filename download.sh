#!/bin/bash
# Figma 语言包同步工具包装器
# 解决 macOS 下直接运行 .py 脚本可能遇到的 403 Forbidden 问题

SCRIPT_PATH="_agent/skills/figma_lang_downloader/scripts/download_latest.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 错误: 找不到探测脚本 $SCRIPT_PATH"
    exit 1
fi

echo "🚀 正在启动 Figma 语言包自动化同步..."
cat "$SCRIPT_PATH" | python3
