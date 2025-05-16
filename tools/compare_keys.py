import os
import json
import sys
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
        return get_nested_keys(data)
    except json.JSONDecodeError:
        print(f"错误: 文件 {file_path} 不是有效的JSON格式", file=sys.stderr)
        return set()
    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在", file=sys.stderr)
        return set()

def compare_keys(zh_dir, en_dir, log_file):
    try:
        zh_files = os.listdir(zh_dir)
        en_files = os.listdir(en_dir)
    except FileNotFoundError as e:
        print(f"错误: 目录不存在 - {e}", file=sys.stderr)
        return

    total_files = len(zh_files) + len(en_files)
    processed_files = 0

    with open(log_file, 'w', encoding='utf-8') as log:
        log.write("=== JSON键比较报告 ===\n\n")
        
        with tqdm(total=total_files, desc="处理文件中") as pbar:
            for zh_file in zh_files:
                if zh_file in en_files:
                    zh_path = os.path.join(zh_dir, zh_file)
                    en_path = os.path.join(en_dir, zh_file)
                    
                    zh_keys = get_json_keys(zh_path)
                    en_keys = get_json_keys(en_path)

                    diff_keys = zh_keys.symmetric_difference(en_keys)
                    if diff_keys:
                        log.write(f'文件: {zh_file}\n')
                        log.write(f'差异键数量: {len(diff_keys)}\n')
                        log.write('中文独有的键:\n')
                        for key in zh_keys - en_keys:
                            log.write(f'  - {key}\n')
                        log.write('英文独有的键:\n')
                        for key in en_keys - zh_keys:
                            log.write(f'  - {key}\n')
                        log.write('\n')
                else:
                    log.write(f'[缺失文件] 英文目录缺少文件: {zh_file}\n\n')
                
                processed_files += 1
                pbar.update(1)

            for en_file in en_files:
                if en_file not in zh_files:
                    log.write(f'[缺失文件] 中文目录缺少文件: {en_file}\n\n')
                processed_files += 1
                pbar.update(1)
        
        log.write("=== 比较完成 ===\n")

if __name__ == "__main__":
    zh_directory = '/Users/lipeng/Documents/Repository/Figma-CN/lang/zh/split'
    en_directory = '/Users/lipeng/Documents/Repository/Figma-CN/lang/en/split'
    log_file_path = '/Users/lipeng/Documents/Repository/Figma-CN/lang/debug.log'
    
    compare_keys(zh_directory, en_directory, log_file_path)