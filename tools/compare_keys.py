#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @name: compare_keys.py
# @description: 比较两个JSON文件的键值对，提取不同的字符串键值对
# @author: kailous
# @date: 2024-08-20
# @help: python3 tools/compare_keys.py --zh-file lang/zh.json --en-file org_dir/en.json

import os
import json
import sys
import argparse
from tqdm import tqdm

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'temp_dir')

def get_string_keys(data, prefix=''):
    keys = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if key == "string" and isinstance(value, str):
                keys.add(full_key)
            elif isinstance(value, dict):
                keys.update(get_string_keys(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    keys.update(get_string_keys(item, f"{full_key}[{i}]"))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            keys.update(get_string_keys(item, f"{prefix}[{i}]"))
    return keys

def get_json_keys(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError:
        print(f"错误: 文件 {file_path} 不是有效的JSON格式", file=sys.stderr)
        return {}
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在", file=sys.stderr)
        return {}

def extract_string_diff(en_data, zh_data):
    result = {}

    def recurse(en_node, zh_node):
        if isinstance(en_node, dict):
            temp = {}
            for k, v in en_node.items():
                zh_sub = zh_node.get(k) if isinstance(zh_node, dict) else None
                child = recurse(v, zh_sub)
                if child:
                    temp[k] = child
            return temp if temp else None
        else:
            return en_node if isinstance(en_node, str) and zh_node != en_node else None

    diff = recurse(en_data, zh_data)
    return diff if diff else {}

def count_keys(data):
    if isinstance(data, dict):
        return sum(count_keys(v) for v in data.values()) + (1 if 'string' in data and isinstance(data['string'], str) else 0)
    return 0

def get_common_structure_only(base_data, keys_to_keep):
    def recurse(node, prefix=''):
        if isinstance(node, dict):
            result = {}
            for k, v in node.items():
                full_key = f"{prefix}.{k}" if prefix else k
                sub_result = recurse(v, full_key)
                if sub_result:
                    result[k] = sub_result
            return result if result else None
        elif isinstance(node, str):
            return node if prefix in keys_to_keep else None
        return None
    return recurse(base_data)

def get_removed_structure(base_data, keys_to_remove):
    def recurse(node, prefix=''):
        if isinstance(node, dict):
            result = {}
            for k, v in node.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, (dict, list)):
                    sub_result = recurse(v, full_key)
                    if sub_result:
                        result[k] = sub_result
                elif full_key not in keys_to_remove:
                    result[k] = v
            return result if result else None
        elif isinstance(node, str):
            return None if prefix in keys_to_remove else node
        return node
    return recurse(base_data)

# === 新增：过滤中文独有键 ===
def filter_zh_unique_keys(zh_data, en_data):
    """
    生成一个新的中文结构：移除所有“只在中文里存在而英文里没有”的键（基于含 'string' 的叶子路径）
    """
    zh_keys = get_string_keys(zh_data)
    en_keys = get_string_keys(en_data)
    zh_only = zh_keys - en_keys
    if not zh_only:
        return zh_data  # 无需变更
    filtered = get_removed_structure(zh_data, zh_only)
    return filtered if filtered is not None else {}

def compare_keys(zh_dir, en_dir, out_dir=None):
    try:
        zh_files = os.listdir(zh_dir)
        en_files = os.listdir(en_dir)
    except FileNotFoundError as e:
        print(f"错误: 目录不存在 - {e}", file=sys.stderr)
        return

    total_files = len(set(zh_files).union(en_files))
    target_dir = out_dir or DEFAULT_OUTPUT_DIR

    log_path = os.path.join(PROJECT_ROOT, 'compare_keys_directory.log')
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("=== JSON键比较报告 ===\n")
        log.write("此文件使用 UTF-8 编码打开，推荐用 VSCode / Notepad++ 查看\n\n")

        with tqdm(total=total_files, desc="处理文件中") as pbar:
            for zh_file in zh_files:
                if zh_file in en_files:
                    zh_path = os.path.join(zh_dir, zh_file)
                    en_path = os.path.join(en_dir, zh_file)

                    zh_data = get_json_keys(zh_path)
                    en_data = get_json_keys(en_path)

                    zh_keys = get_string_keys(zh_data)
                    en_keys = get_string_keys(en_data)

                    diff_keys = zh_keys.symmetric_difference(en_keys)
                    if diff_keys:
                        log.write(f'文件: {zh_file}\n')
                        log.write(f'差异键数量: {len(diff_keys)}\n')
                        log.write('中文独有的键:\n')
                        for key in sorted(zh_keys - en_keys):
                            log.write(f'  - {key}\n')
                        log.write('英文独有的键:\n')
                        for key in sorted(en_keys - zh_keys):
                            log.write(f'  - {key}\n')
                        log.write("---------------\n")

                        os.makedirs(target_dir, exist_ok=True)
                        file_base = os.path.splitext(zh_file)[0]
                        en_only = en_keys - zh_keys
                        zh_only = zh_keys - en_keys

                        en_struct = get_common_structure_only(en_data, en_only)
                        zh_struct = get_removed_structure(zh_data, zh_only)

                        en_out = os.path.join(target_dir, f"{file_base}_en-new.json")
                        zh_out = os.path.join(target_dir, f"{file_base}_zh-new.json")

                        with open(en_out, 'w', encoding='utf-8') as f:
                            json.dump(en_struct, f, ensure_ascii=False, indent=2)
                        with open(zh_out, 'w', encoding='utf-8') as f:
                            json.dump(zh_struct, f, ensure_ascii=False, indent=2)

                        print(f"已生成: {en_out}, {zh_out}")

                        filtered = filter_zh_unique_keys(zh_data, en_data)
                        if filtered == zh_data:
                            print(f"文件 {zh_file} 没有中文独有键，已跳过过滤输出")
                        elif filtered == zh_struct:
                            print(f"文件 {zh_file} 的过滤结果与 {zh_out} 内容一致，已跳过重复输出")
                        else:
                            zh_filtered_out = os.path.join(target_dir, f"{file_base}_zh-filtered.json")
                            with open(zh_filtered_out, 'w', encoding='utf-8') as f:
                                json.dump(filtered, f, ensure_ascii=False, indent=2)
                            print(f"已生成过滤后的中文文件（移除中文独有键）: {zh_filtered_out}")
                else:
                    log.write(f'[缺失文件] 英文目录缺少文件: {zh_file}\n\n')
                pbar.update(1)

            for en_file in en_files:
                if en_file not in zh_files:
                    log.write(f'[缺失文件] 中文目录缺少文件: {en_file}\n\n')
                pbar.update(1)

        log.write("=== 比较完成 ===\n")
    print(f"日志输出: {log_path}")

def compare_single_files(zh_file, en_file, out_dir=None):
    zh_data = get_json_keys(zh_file)
    en_data = get_json_keys(en_file)

    zh_keys = get_string_keys(zh_data)
    en_keys = get_string_keys(en_data)

    log_path = os.path.join(PROJECT_ROOT, 'compare_keys_single.log')
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("=== 单文件JSON键比较报告 ===\n\n")
        log.write(f'中文文件: {zh_file}\n')
        log.write(f'英文文件: {en_file}\n\n')

        diff_keys = zh_keys.symmetric_difference(en_keys)
        if diff_keys:
            log.write(f'差异键数量: {len(diff_keys)}\n')
            log.write('中文独有的键:\n')
            for key in sorted(zh_keys - en_keys):
                log.write(f'  - {key}\n')
            log.write('英文独有的键:\n')
            for key in sorted(en_keys - zh_keys):
                log.write(f'  - {key}\n')
            log.write("---------------\n")
        else:
            log.write('两个文件的键完全一致\n')
        log.write("\n=== 比较完成 ===\n")
    print(f"日志输出: {log_path}")

    target_dir = out_dir or DEFAULT_OUTPUT_DIR
    base_zh = os.path.splitext(os.path.basename(zh_file))[0]
    base_en = os.path.splitext(os.path.basename(en_file))[0]
    zh_struct = None
    zh_out = None

    en_only = en_keys - zh_keys
    zh_only = zh_keys - en_keys

    if diff_keys:
        os.makedirs(target_dir, exist_ok=True)

        en_struct = get_common_structure_only(en_data, en_only)
        zh_struct = get_removed_structure(zh_data, zh_only)

        en_out = os.path.join(target_dir, f"{base_en}_en-new.json")
        zh_out = os.path.join(target_dir, f"{base_zh}_zh-new.json")

        with open(en_out, 'w', encoding='utf-8') as f:
            json.dump(en_struct, f, ensure_ascii=False, indent=2)
        with open(zh_out, 'w', encoding='utf-8') as f:
            json.dump(zh_struct, f, ensure_ascii=False, indent=2)

        print(f"已生成英文独有内容文件: {en_out}")
        print(f"已生成去除中文独有内容的文件: {zh_out}")

    filtered = filter_zh_unique_keys(zh_data, en_data)
    if filtered == zh_data:
        print("没有中文独有键，已跳过过滤输出")
    elif zh_struct is not None and filtered == zh_struct:
        print(f"过滤结果与 {zh_out} 内容一致，已跳过重复输出")
    else:
        os.makedirs(target_dir, exist_ok=True)
        zh_filtered_out = os.path.join(target_dir, f"{base_zh}_zh-filtered.json")
        with open(zh_filtered_out, 'w', encoding='utf-8') as f:
            json.dump(filtered, f, ensure_ascii=False, indent=2)
        print(f"已生成过滤后的中文文件（移除中文独有键）: {zh_filtered_out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='比较中英文JSON文件的翻译字段')
    parser.add_argument('-ZH', '--zh-dir', type=str, help='中文JSON文件目录')
    parser.add_argument('-EN', '--en-dir', type=str, help='英文JSON文件目录')
    parser.add_argument('-zh', '--zh-file', type=str, help='单个中文JSON文件路径')
    parser.add_argument('-en', '--en-file', type=str, help='单个英文JSON文件路径')
    parser.add_argument('-o', '--out-dir', type=str, help='输出目录（可选）')

    args = parser.parse_args()

    if (args.zh_file or args.en_file) and (args.zh_dir or args.en_dir):
        parser.error("不能同时使用文件比较和目录比较参数")

    if args.zh_file and args.en_file:
        compare_single_files(args.zh_file, args.en_file, args.out_dir)
    elif args.zh_dir and args.en_dir:
        compare_keys(args.zh_dir, args.en_dir, args.out_dir)
    else:
        parser.print_help()
        print("\n使用示例:")
        print("1. 比较目录：")
        print("   python3 tools/compare_keys.py --zh-dir ./zh --en-dir ./en")
        print("2. 比较单文件：")
        print("   python3 tools/compare_keys.py --zh-file zh.json --en-file en.json")
        print("3. 指定输出目录：")
        print("   python3 tools/compare_keys.py --zh-dir ./zh --en-dir ./en --out-dir ./out")
