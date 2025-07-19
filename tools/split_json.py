#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")

        items = list(data.items())
        for i in range(num_files):
            start_idx = i * items_per_file
            end_idx = min((i + 1) * items_per_file, total_items)
            current_data = dict(items[start_idx:end_idx])

            output_file = os.path.join(output_dir, f"part_{i+1:03d}.json")

            formatted_json = '{\n'
            current_items = list(current_data.items())
            for j, (key, value) in enumerate(current_items):
                value_str = json.dumps(value, ensure_ascii=False)
                formatted_json += f'  "{key}": {value_str}'
                formatted_json += ',\n' if j < len(current_items) - 1 else '\n'
            formatted_json += '}'

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_json)

            print(f"已创建文件 {i+1}/{num_files}: {output_file}")

        return True
    except json.JSONDecodeError:
        print(f"❌ 错误: {input_file} 不是有效的JSON文件")
        return False
    except Exception as e:
        print(f"❌ 处理文件时出错: {str(e)}")
        return False

def copy_split_folder_to_zh(source_dir):
    """
    将split文件夹复制到lang/zh目录
    """
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        zh_dir = os.path.join(project_root, 'lang', 'zh')
        target_dir = os.path.join(zh_dir, 'split')

        if not os.path.exists(zh_dir):
            os.makedirs(zh_dir)
            print(f"创建目录: {zh_dir}")

        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            print(f"已删除已存在的目标目录: {target_dir}")

        shutil.copytree(source_dir, target_dir)
        print(f"✅ 已成功将split文件夹复制到: {target_dir}")
        return True
    except Exception as e:
        print(f"⚠️ 复制split文件夹时出错: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='将JSON文件拆分为多个小文件')
    parser.add_argument('--input', help='输入的JSON文件路径，如 ./lang/en/sorted_en.json')
    parser.add_argument('--output', help='拆分后的输出目录，如 ./lang/en/split')
    parser.add_argument('--items', type=int, default=500, help='每个文件包含的键值对数量（默认：500）')
    args = parser.parse_args()

    if not args.input or not args.output:
        print("❗用法示例：")
        print("python3 split_json.py --input ./lang/en/sorted_en.json --output ./lang/en/split --items 500")
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"❌ 错误: 输入文件不存在: {args.input}")
        sys.exit(1)

    success = split_json_file(args.input, args.output, args.items)
    if not success:
        sys.exit(1)

    print("🎉 拆分完成！")

    copy_success = copy_split_folder_to_zh(args.output)
    if not copy_success:
        print("⚠️ 警告: 复制split文件夹到lang/zh目录失败")
    else:
        print("✨ 所有操作已完成！")

if __name__ == "__main__":
    main()