#!/usr/bin/env python3
"""diff.py — 对比 en_latest.json 与 zh.json，提取新增字段"""
import os
import sys
import json
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
TOOLS_DIR = os.path.join(PROJECT_ROOT, 'tools')
LANG_DIR = os.path.join(PROJECT_ROOT, 'lang')
CACHE_DIR = os.path.join(PROJECT_ROOT, '.cache')


def get_string_keys(data, prefix=''):
    """提取所有 'string' 叶子节点的完整路径"""
    keys = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if key == "string" and isinstance(value, str):
                keys.add(prefix)  # 用父级路径作为键
            elif isinstance(value, dict):
                keys.update(get_string_keys(value, full_key))
    return keys


def diff():
    en_file = os.path.join(LANG_DIR, 'en_latest.json')
    zh_file = os.path.join(LANG_DIR, 'zh.json')
    os.makedirs(CACHE_DIR, exist_ok=True)

    if not os.path.exists(en_file):
        print("❌ lang/en_latest.json 不存在。请先运行 sync.py")
        return False

    print("🔍 正在分析中英文语言包差异...")

    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    # 找到英文有但中文没有的顶层键
    en_keys = set(en_data.keys())
    zh_keys = set(zh_data.keys())
    new_keys = en_keys - zh_keys

    if not new_keys:
        print("🎉 没有发现新增字段，当前翻译已是最新。")
        # 写一个空文件标记
        pending_file = os.path.join(CACHE_DIR, 'pending.json')
        with open(pending_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return True

    # 提取新增字段
    pending = {}
    for key in sorted(new_keys):
        pending[key] = en_data[key]

    # 按 string 字段长度排序（便于翻译）
    try:
        pending = dict(sorted(pending.items(), key=lambda x: len(x[1].get('string', '')) if isinstance(x[1], dict) else 0))
    except Exception:
        pass

    pending_file = os.path.join(CACHE_DIR, 'pending.json')
    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)

    print(f"  📋 发现 {len(new_keys)} 个新增字段")
    print(f"  📁 待翻译文件: {pending_file}")
    return True


if __name__ == "__main__":
    ok = diff()
    sys.exit(0 if ok else 1)
