#!/usr/bin/env python3
"""run_all.py — 一键全流程调度器：同步 → 对比 → 翻译 → 合并 → 校验"""
import sys
import os
import argparse
import importlib.util

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_module(name):
    """动态加载同目录下的模块"""
    path = os.path.join(SCRIPT_DIR, f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    parser = argparse.ArgumentParser(description="Figma 语言包全自动汉化")
    parser.add_argument("--skip-sync", action="store_true", help="跳过下载步骤（使用本地已有的 en_latest.json）")
    parser.add_argument("--skip-translate", action="store_true", help="跳过翻译步骤（假设 translated.json 已就绪）")
    args = parser.parse_args()

    steps = [
        ("sync",      "📥 同步最新英文包",       args.skip_sync),
        ("diff",      "🔍 对比差异",             False),
        ("translate", "🤖 生成翻译任务",         args.skip_translate),
        ("merge",     "📦 合并到主语言包",       False),
        ("verify",    "✅ 校验同步完整性",       False),
    ]

    print("=" * 50)
    print("  Figma 语言包全自动汉化工具链")
    print("=" * 50)
    print()

    for name, label, skip in steps:
        if skip:
            print(f"{label} ... ⏭️  已跳过")
            continue

        print(f"{label} ...")
        mod = load_module(name)

        # 每个模块都有同名的主函数
        func = getattr(mod, name)
        result = func()

        if result is False:
            print(f"\n❌ 步骤 [{name}] 失败，流程中断。")
            sys.exit(1)

        # translate 步骤特殊处理：如果有待翻译字段，需要 Agent 介入
        if name == "translate":
            cache_dir = os.path.join(os.path.dirname(SCRIPT_DIR), '..', '..', '..', '.cache')
            cache_dir = os.path.normpath(os.path.join(SCRIPT_DIR, '..', '..', '..', '..', '..', '.cache'))
            pending = os.path.join(cache_dir, 'pending.json')
            translated = os.path.join(cache_dir, 'translated.json')

            if os.path.exists(pending):
                import json
                with open(pending, 'r') as f:
                    data = json.load(f)
                if data and not os.path.exists(translated):
                    print(f"\n⏸️  有 {len(data)} 个字段待 AI 翻译。")
                    print("   Agent 请读取 .cache/pending.json 并翻译后写入 .cache/translated.json")
                    print("   然后重新运行: python3 .../run_all.py --skip-sync --skip-translate")
                    sys.exit(2)  # 特殊退出码表示需要 Agent 介入

        print()

    print("=" * 50)
    print("  🎉 全流程完成！语言包已同步至最新。")
    print("=" * 50)


if __name__ == "__main__":
    main()
