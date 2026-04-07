#!/usr/bin/env python3
"""merge.py — 将翻译结果安全合入 lang/zh.json"""
import os
import sys
import json
import shutil
import subprocess
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(PROJECT_ROOT, '.cache')
LANG_DIR = os.path.join(PROJECT_ROOT, 'lang')
BACKUP_DIR = os.path.join(LANG_DIR, 'backup')


def merge():
    translated_file = os.path.join(CACHE_DIR, 'translated.json')
    zh_file = os.path.join(LANG_DIR, 'zh.json')

    if not os.path.exists(translated_file):
        print("❌ .cache/translated.json 不存在。请先完成翻译。")
        return False

    with open(translated_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    if not new_data:
        print("🎉 翻译文件为空，无需合并。")
        return True

    # 校验 JSON 结构
    for key, val in new_data.items():
        if not isinstance(val, dict) or 'string' not in val:
            print(f"  ⚠️  键 '{key}' 结构异常: 期望 {{'string': '...'}}")
            # 尝试修复
            if isinstance(val, str):
                new_data[key] = {"string": val}

    # 1. 备份
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"zh_backup_{timestamp}.json")
    shutil.copy2(zh_file, backup_file)
    print(f"📦 已创建备份: lang/backup/zh_backup_{timestamp}.json")

    # 2. 合并
    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    before_count = len(zh_data)
    zh_data.update(new_data)
    after_count = len(zh_data)

    with open(zh_file, 'w', encoding='utf-8') as f:
        json.dump(zh_data, f, ensure_ascii=False, indent=2)

    # 3. 格式化排序
    format_script = os.path.join(SCRIPT_DIR, 'format_json.py')
    if os.path.exists(format_script):
        subprocess.run([sys.executable, format_script, zh_file], check=True)

    added = after_count - before_count
    print(f"✅ 合并完成: 新增 {added} 条 (总计 {after_count} 条)")
    return True


if __name__ == "__main__":
    ok = merge()
    sys.exit(0 if ok else 1)
