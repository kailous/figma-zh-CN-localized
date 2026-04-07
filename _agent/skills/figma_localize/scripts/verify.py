#!/usr/bin/env python3
"""verify.py — 校验 zh.json 与 en_latest.json 的同步完整性"""
import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
LANG_DIR = os.path.join(PROJECT_ROOT, 'lang')


def verify():
    en_file = os.path.join(LANG_DIR, 'en_latest.json')
    zh_file = os.path.join(LANG_DIR, 'zh.json')

    if not os.path.exists(en_file):
        print("❌ lang/en_latest.json 不存在")
        return False

    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)

    en_keys = set(en_data.keys())
    zh_keys = set(zh_data.keys())

    missing = en_keys - zh_keys  # 英文有但中文没有
    extra = zh_keys - en_keys    # 中文有但英文没有

    print("🔎 同步校验报告")
    print(f"  英文包: {len(en_keys)} 个键")
    print(f"  中文包: {len(zh_keys)} 个键")

    if missing:
        print(f"  ❌ 缺失 {len(missing)} 个翻译:")
        for k in sorted(missing)[:10]:
            print(f"     - {k}")
        if len(missing) > 10:
            print(f"     ... 还有 {len(missing) - 10} 个")
        return False

    if extra:
        print(f"  ⚠️  中文包多出 {len(extra)} 个键 (可能是旧字段)")
    else:
        print("  ✅ 中英文键完全一致")

    print("  🎉 校验通过！翻译同步完整。")
    return True


if __name__ == "__main__":
    ok = verify()
    sys.exit(0 if ok else 1)
