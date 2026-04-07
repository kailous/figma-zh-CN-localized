#!/usr/bin/env python3
"""translate.py — 读取 pending.json，输出翻译状态和指令供 AI Agent 消费"""
import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
CACHE_DIR = os.path.join(PROJECT_ROOT, '.cache')
LANG_DIR = os.path.join(PROJECT_ROOT, 'lang')
BATCH_SIZE = 200


def translate():
    pending_file = os.path.join(CACHE_DIR, 'pending.json')
    translated_file = os.path.join(CACHE_DIR, 'translated.json')

    if not os.path.exists(pending_file):
        print("❌ .cache/pending.json 不存在。请先运行 diff.py")
        return False

    with open(pending_file, 'r', encoding='utf-8') as f:
        pending = json.load(f)

    if not pending:
        print("🎉 没有待翻译字段。")
        # 创建空的 translated 文件
        with open(translated_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return True

    # 如果 translated.json 已存在且包含所有 pending 的键，则跳过
    if os.path.exists(translated_file):
        with open(translated_file, 'r', encoding='utf-8') as f:
            try:
                existing = json.load(f)
                if set(pending.keys()).issubset(set(existing.keys())):
                    print(f"✅ .cache/translated.json 已包含所有 {len(pending)} 个字段的翻译。")
                    return True
            except json.JSONDecodeError:
                pass

    # 计算分批信息
    keys = list(pending.keys())
    total = len(keys)
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"📋 待翻译: {total} 个字段 ({num_batches} 批)")
    print(f"📁 输入: {pending_file}")
    print(f"📁 输出: {translated_file}")
    print()
    print("=" * 60)
    print("🤖 AI Agent 翻译指令")
    print("=" * 60)
    print()
    print("请执行以下操作：")
    print(f"1. 读取 {pending_file}")
    print(f"2. 将所有英文 string 值翻译为中文")
    print("3. 遵循 SKILL.md 中的术语表")
    print("4. 保留所有 {variable} 占位符和 ICU 语法")
    print(f"5. 将结果写入 {translated_file}")
    print()

    # 输出前 5 条样本便于 Agent 快速理解结构
    print("📌 样本预览 (前 5 条):")
    for i, key in enumerate(keys[:5]):
        val = pending[key]
        s = val.get('string', '') if isinstance(val, dict) else str(val)
        print(f"  {key}: \"{s[:80]}{'...' if len(s) > 80 else ''}\"")

    return True


if __name__ == "__main__":
    ok = translate()
    sys.exit(0 if ok else 1)
