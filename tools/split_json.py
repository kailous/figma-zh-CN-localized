#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @name: split_json.py
# @description: 将JSON文件按照指定的键值对数量拆分成多个文件
# @author: kailous
# @date: 2024-08-20
# @help: python3 tools/split_json.py 100

import json
import os
import sys
import math
import shutil
import argparse

def split_json_file(input_file, output_dir, items_per_file=500):
    """
    将JSON文件按照指定的键值对数量拆分成多个文件
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        total_items = len(data)
        num_files = math.ceil(total_items / items_per_file)
        print(f"总共有 {total_items} 个键值对，将拆分为 {num_files} 个文件")

        os.makedirs(output_dir, exist_ok=True)
        file_stem = os.path.splitext(os.path.basename(input_file))[0]

        items = list(data.items())
        for i in range(num_files):
            start_idx = i * items_per_file
            end_idx = min((i + 1) * items_per_file, total_items)
            current_data = dict(items[start_idx:end_idx])

            formatted_json = '{\n'
            current_items = list(current_data.items())
            for j, (key, value) in enumerate(current_items):
                value_str = json.dumps(value, ensure_ascii=False)
                formatted_json += f'  "{key}": {value_str}'
                formatted_json += ',\n' if j < len(current_items) - 1 else '\n'
            formatted_json += '}'

            yield_json_path = os.path.join(output_dir, f"split_{file_stem}_{i+1:03d}.json")
            with open(yield_json_path, 'w', encoding='utf-8') as f:
                f.write(formatted_json)

            print(f"已创建文件 {i+1}/{num_files}: {yield_json_path}")

        return num_files
    except json.JSONDecodeError:
        print(f"❌ 错误: {input_file} 不是有效的JSON文件")
        return False
    except Exception as e:
        print(f"❌ 处理文件时出错: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='将JSON文件拆分为多个小文件')
    parser.add_argument('input', help='输入的JSON文件路径，如 ./lang/en/sorted_en.json')
    parser.add_argument('items', nargs='?', type=int, default=500, help='每个文件包含的键值对数量（默认：500）')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 错误: 输入文件不存在: {args.input}")
        sys.exit(1)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, 'split_dir')

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        print(f"已删除已存在的输出目录: {output_dir}")

    total_files = split_json_file(args.input, output_dir, args.items)
    if not total_files:
        print("⚠️ 未生成任何拆分文件")
        sys.exit(1)

    print(f"🎉 拆分完成，创建了 {total_files} 个文件！")

if __name__ == "__main__":
    main()
