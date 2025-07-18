import os
import json
import sys
import argparse
import traceback
from tqdm import tqdm

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

def compare_keys(zh_dir, en_dir, log_file, extract=False):
    try:
        zh_files = os.listdir(zh_dir)
        en_files = os.listdir(en_dir)
    except FileNotFoundError as e:
        print(f"错误: 目录不存在 - {e}", file=sys.stderr)
        return

    total_files = len(set(zh_files).union(en_files))

    with open(log_file, 'w', encoding='utf-8') as log:
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

                        if extract:
                            file_base = os.path.splitext(zh_file)[0]
                            en_only = en_keys - zh_keys
                            zh_only = zh_keys - en_keys

                            en_struct = get_common_structure_only(en_data, en_only)
                            zh_struct = get_removed_structure(zh_data, zh_only)

                            en_out = f"{file_base}_en-new.json"
                            zh_out = f"{file_base}_zh-new.json"

                            with open(en_out, 'w', encoding='utf-8') as f:
                                json.dump(en_struct, f, ensure_ascii=False, indent=2)
                            with open(zh_out, 'w', encoding='utf-8') as f:
                                json.dump(zh_struct, f, ensure_ascii=False, indent=2)

                            print(f"已生成: {en_out}, {zh_out}")
                else:
                    log.write(f'[缺失文件] 英文目录缺少文件: {zh_file}\n\n')
                pbar.update(1)

            for en_file in en_files:
                if en_file not in zh_files:
                    log.write(f'[缺失文件] 中文目录缺少文件: {en_file}\n\n')
                pbar.update(1)

        log.write("=== 比较完成 ===\n")

def compare_single_files(zh_file, en_file, log_file, extract=False):
    zh_data = get_json_keys(zh_file)
    en_data = get_json_keys(en_file)

    zh_keys = get_string_keys(zh_data)
    en_keys = get_string_keys(en_data)

    with open(log_file, 'w', encoding='utf-8') as log:
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

    if extract:
        base_zh = os.path.splitext(os.path.basename(zh_file))[0]
        base_en = os.path.splitext(os.path.basename(en_file))[0]

        en_only = en_keys - zh_keys
        zh_only = zh_keys - en_keys

        en_struct = get_common_structure_only(en_data, en_only)
        zh_struct = get_removed_structure(zh_data, zh_only)

        en_out = f"{base_en}_en-new.json"
        zh_out = f"{base_zh}_zh-new.json"

        with open(en_out, 'w', encoding='utf-8') as f:
            json.dump(en_struct, f, ensure_ascii=False, indent=2)
        with open(zh_out, 'w', encoding='utf-8') as f:
            json.dump(zh_struct, f, ensure_ascii=False, indent=2)

        print(f"已生成英文独有内容文件: {en_out}")
        print(f"已生成去除中文独有内容的文件: {zh_out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='比较中英文JSON文件的翻译字段')
    parser.add_argument('--zh-dir', type=str, help='中文JSON文件目录')
    parser.add_argument('--en-dir', type=str, help='英文JSON文件目录')
    parser.add_argument('--zh-file', type=str, help='单个中文JSON文件路径')
    parser.add_argument('--en-file', type=str, help='单个英文JSON文件路径')
    parser.add_argument('--log', type=str, help='日志文件路径')
    parser.add_argument('--extract', action='store_true', help='是否提取英文独有字段并清理中文')

    args = parser.parse_args()

    if (args.zh_file or args.en_file) and (args.zh_dir or args.en_dir):
        parser.error("不能同时使用文件比较和目录比较参数")

    if args.zh_file and args.en_file:
        log_file = args.log or 'single_file_compare.log'
        compare_single_files(args.zh_file, args.en_file, log_file, args.extract)
    elif args.zh_dir and args.en_dir:
        log_file = args.log or 'directory_compare.log'
        compare_keys(args.zh_dir, args.en_dir, log_file, args.extract)
    else:
        parser.print_help()
        print("\n使用示例:")
        print("1. 比较目录并提取差异:")
        print("   python compare_keys.py --zh-dir ./zh --en-dir ./en --log out.log --extract")
        print("2. 比较单文件并生成提取结果:")
        print("   python compare_keys.py --zh-file zh.json --en-file en.json --log out.log --extract")