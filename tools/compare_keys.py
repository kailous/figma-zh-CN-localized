import os
import json
import sys
import argparse
import traceback
from tqdm import tqdm

def get_nested_keys(data, prefix=''):
    keys = set()
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            if isinstance(value, (dict, list)):
                keys.update(get_nested_keys(value, full_key))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            keys.update(get_nested_keys(item, f"{prefix}[{i}]"))
    return keys

def get_json_keys(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return get_nested_keys(data), data
    except json.JSONDecodeError:
        print(f"错误: 文件 {file_path} 不是有效的JSON格式", file=sys.stderr)
        return set(), {}
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在", file=sys.stderr)
        return set(), {}

def extract_nested_diff(en_data, zh_data):
    result = {}
    for key in en_data:
        if key not in zh_data:
            result[key] = en_data[key]
        elif isinstance(en_data[key], dict) and isinstance(zh_data.get(key), dict):
            nested_diff = extract_nested_diff(en_data[key], zh_data[key])
            if nested_diff:
                result[key] = nested_diff
    return result

def count_keys(data):
    if isinstance(data, dict):
        return sum(count_keys(v) for v in data.values()) + len(data)
    return 0

def extract_english_only(en_data, zh_data, output_file):
    result = extract_nested_diff(en_data, zh_data)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return count_keys(result)

def compare_keys(zh_dir, en_dir, log_file, extract_file=None):
    try:
        zh_files = os.listdir(zh_dir)
        en_files = os.listdir(en_dir)
    except FileNotFoundError as e:
        print(f"错误: 目录不存在 - {e}", file=sys.stderr)
        return

    total_files = len(set(zh_files).union(en_files))
    total_english_only_keys = 0

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("=== JSON键比较报告 ===\n")
        log.write("此文件使用 UTF-8 编码打开，推荐用 VSCode / Notepad++ 查看\n\n")

        with tqdm(total=total_files, desc="处理文件中") as pbar:
            for zh_file in zh_files:
                if zh_file in en_files:
                    zh_path = os.path.join(zh_dir, zh_file)
                    en_path = os.path.join(en_dir, zh_file)

                    zh_keys, zh_data = get_json_keys(zh_path)
                    en_keys, en_data = get_json_keys(en_path)

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

                        if extract_file:
                            base_extract_path = os.path.splitext(extract_file)[0]
                            file_base_name = os.path.splitext(zh_file)[0]
                            file_extract_path = f"{base_extract_path}_{file_base_name}.json"
                            keys_count = extract_english_only(en_data, zh_data, file_extract_path)
                            total_english_only_keys += keys_count
                            print(f"已提取 {keys_count} 个英文独有键值到 {file_extract_path}")
                else:
                    log.write(f'[缺失文件] 英文目录缺少文件: {zh_file}\n\n')
                pbar.update(1)

            for en_file in en_files:
                if en_file not in zh_files:
                    log.write(f'[缺失文件] 中文目录缺少文件: {en_file}\n\n')

                    if extract_file:
                        en_path = os.path.join(en_dir, en_file)
                        try:
                            with open(en_path, 'r', encoding='utf-8') as f:
                                en_data = json.load(f)

                            base_extract_path = os.path.splitext(extract_file)[0]
                            file_base_name = os.path.splitext(en_file)[0]
                            file_extract_path = f"{base_extract_path}_{file_base_name}.json"

                            with open(file_extract_path, 'w', encoding='utf-8') as f:
                                json.dump(en_data, f, ensure_ascii=False, indent=2)
                            print(f"已提取缺失文件 {en_file} 的所有内容到 {file_extract_path}")
                        except Exception:
                            print(f"提取文件 {en_file} 时出错:\n{traceback.format_exc()}")
                pbar.update(1)

        log.write("=== 比较完成 ===\n")
        if extract_file and total_english_only_keys > 0:
            log.write(f"\n总共提取了 {total_english_only_keys} 个英文独有的键值对\n")

    if extract_file:
        print(f"比较完成，总共提取了 {total_english_only_keys} 个英文独有的键值对")

def compare_single_files(zh_file, en_file, log_file, extract_file=None):
    zh_keys, zh_data = get_json_keys(zh_file)
    en_keys, en_data = get_json_keys(en_file)

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

            if extract_file:
                keys_count = extract_english_only(en_data, zh_data, extract_file)
                log.write(f"\n已提取 {keys_count} 个英文独有的键值对到 {extract_file}\n")
                print(f"已提取 {keys_count} 个英文独有键值到 {extract_file}")
        else:
            log.write('两个文件的键完全一致\n')
        log.write("\n=== 比较完成 ===\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='比较中英文JSON文件的键')

    parser.add_argument('--zh-dir', type=str, help='中文JSON文件目录')
    parser.add_argument('--en-dir', type=str, help='英文JSON文件目录')
    parser.add_argument('--zh-file', type=str, help='单个中文JSON文件路径')
    parser.add_argument('--en-file', type=str, help='单个英文JSON文件路径')
    parser.add_argument('--log', type=str, help='日志文件路径')
    parser.add_argument('--extract', type=str, help='提取英文独有键值的输出JSON文件路径')

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
        print("1. 比较两个目录:")
        print("   python compare_keys.py --zh-dir /path/to/zh/dir --en-dir /path/to/en/dir --log output.txt --extract english_only.json")
        print("\n2. 比较两个文件:")
        print("   python compare_keys.py --zh-file /path/to/zh/file.json --en-file /path/to/en/file.json --log output.txt --extract english_only.json")
