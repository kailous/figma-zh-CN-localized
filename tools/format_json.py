#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @name: format_json.py
# @description: 格式化JSON文件，使每个键值对占用单独的一行
# @author: kailous
# @date: 2024-08-20
# @help: python3 tools/format_json.py lang/zh.json

import json
import os
import sys
import argparse

def format_json_file(file_path):
    """
    格式化JSON文件，使每个键值对占用单独的一行
    并按照'string'属性的长度进行排序
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items_with_length = []
        for key, value in data.items():
            if isinstance(value, dict) and 'string' in value:
                string_length = len(value['string'])
                items_with_length.append((key, value, string_length))
            else:
                items_with_length.append((key, value, -1))

        sorted_items = sorted(items_with_length, key=lambda x: x[2])
        sorted_data = {key: value for key, value, _ in sorted_items}

        # 转换为漂亮的JSON字符串
        formatted_json = '{\n'
        items = list(sorted_data.items())
        for i, (key, value) in enumerate(items):
            value_str = json.dumps(value, ensure_ascii=False)
            formatted_json += f'  "{key}": {value_str}'
            formatted_json += ',\n' if i < len(items) - 1 else '\n'
        formatted_json += '}'

        # 写入文件（覆盖原文件）
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_json)

        print(f"✅ 排序并格式化完成: {file_path}")
        return True

    except json.JSONDecodeError:
        print(f"❌ 错误: {file_path} 不是有效的JSON文件")
        return False
    except Exception as e:
        print(f"❌ 处理文件时出错: {str(e)}")
        return False

def format_directory(directory_path):
    total_json = 0
    success_count = 0
    for entry in sorted(os.listdir(directory_path)):
        full_path = os.path.join(directory_path, entry)
        if os.path.isfile(full_path) and entry.lower().endswith('.json'):
            total_json += 1
            if format_json_file(full_path):
                success_count += 1
    if total_json == 0:
        print(f"⚠️ 目录中未找到JSON文件: {directory_path}")
        return False
    if success_count == total_json:
        print(f"✨ 共格式化 {success_count} 个JSON文件")
        return True
    print(f"⚠️ 共找到 {total_json} 个JSON文件，其中 {success_count} 个格式化成功")
    return False

def main():
    parser = argparse.ArgumentParser(description='格式化并按string长度排序JSON文件（支持文件或目录）')
    parser.add_argument('path', help='JSON文件路径或包含JSON文件的目录')
    args = parser.parse_args()

    target_path = args.path

    if not os.path.exists(target_path):
        print(f"❌ 输入路径不存在: {target_path}")
        sys.exit(1)

    if os.path.isfile(target_path):
        success = format_json_file(target_path)
    elif os.path.isdir(target_path):
        success = format_directory(target_path)
    else:
        print(f"❌ 不支持的路径类型: {target_path}")
        success = False

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
