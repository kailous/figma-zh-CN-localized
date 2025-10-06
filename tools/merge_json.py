#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @name: merge_json.py
# @description: 合并拆分的JSON文件为一个文件
# @author: kailous
# @date: 2024-08-20
# @help: python3 tools/merge_json.py

import json
import os
import sys
import glob
import argparse
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_INPUT_DIR = os.path.join(PROJECT_ROOT, 'split_dir')
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'temp_dir')
DEFAULT_OUTPUT_FILE = os.path.join(DEFAULT_OUTPUT_DIR, 'merged.json')

def collect_json_files(input_dir):
    patterns = [
        os.path.join(input_dir, "split_*.json"),
        os.path.join(input_dir, "part_*.json"),
    ]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    return sorted(set(files))

def infer_output_path(json_files):
    split_pattern = re.compile(r'split_(.+?)_(\d+)\.json$', re.IGNORECASE)
    for file_path in json_files:
        match = split_pattern.search(os.path.basename(file_path))
        if match:
            lang_token = match.group(1)
            safe_token = lang_token.replace(os.sep, '_').replace('..', '')
            return os.path.join(DEFAULT_OUTPUT_DIR, f'merged_{safe_token}.json')
    return DEFAULT_OUTPUT_FILE

def merge_json_files(input_dir, output_file, json_files=None):
    """
    将多个JSON文件合并为一个文件
    
    Args:
        input_dir: 包含拆分JSON文件的目录路径
        output_file: 输出文件路径
    """
    try:
        if not os.path.exists(input_dir):
            print(f"错误: 输入目录不存在: {input_dir}")
            return False

        if json_files is None:
            json_files = collect_json_files(input_dir)

        if not json_files:
            print(f"错误: 在 {input_dir} 中未找到可合并的 JSON 文件")
            return False

        print(f"找到 {len(json_files)} 个JSON文件，开始合并...")

        merged_data = {}
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                merged_data.update(data)
                print(f"已处理: {os.path.basename(file_path)}")
            except json.JSONDecodeError:
                print(f"⚠️ 跳过无效JSON文件: {file_path}")
            except Exception as e:
                print(f"⚠️ 处理文件 {file_path} 时出错: {str(e)}")

        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"创建输出目录: {output_dir}")

        formatted_json = '{\n'
        items = list(merged_data.items())
        for i, (key, value) in enumerate(items):
            value_str = json.dumps(value, ensure_ascii=False)
            formatted_json += f'  "{key}": {value_str}'
            if i < len(items) - 1:
                formatted_json += ',\n'
            else:
                formatted_json += '\n'
        formatted_json += '}'

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_json)

        print(f"✅ 合并完成！结果已保存到: {output_file}")
        print(f"📦 总共合并了 {len(merged_data)} 个键值对")
        return True

    except Exception as e:
        print(f"❌ 合并文件时出错: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="合并多个JSON文件")
    parser.add_argument('-i', '--input', help="输入目录路径 (默认: 项目根目录下的 split_dir)")
    parser.add_argument('-o', '--output', help="输出文件路径 (默认: 项目根目录下的 temp_dir/merged.json)")
    args = parser.parse_args()

    input_dir = args.input or DEFAULT_INPUT_DIR

    if not args.input:
        print(f"ℹ️ 未指定输入目录，使用默认路径: {input_dir}")

    json_files = collect_json_files(input_dir)
    if not json_files:
        if not os.path.exists(input_dir):
            print(f"错误: 输入目录不存在: {input_dir}")
        else:
            print(f"错误: 在 {input_dir} 中未找到可合并的 JSON 文件")
        sys.exit(1)

    if args.output:
        output_file = args.output
    else:
        output_file = infer_output_path(json_files)
        print(f"ℹ️ 未指定输出文件，使用默认路径: {output_file}")

    success = merge_json_files(input_dir, output_file, json_files=json_files)
    if not success:
        sys.exit(1)

    print("🎉 所有操作已完成！")

if __name__ == "__main__":
    main()
