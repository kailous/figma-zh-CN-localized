#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import argparse

def format_json_file(file_path, output_path):
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

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_json)

        print(f"✅ 排序并格式化完成，结果已保存到: {output_path}")
        return True

    except json.JSONDecodeError:
        print(f"❌ 错误: {file_path} 不是有效的JSON文件")
        return False
    except Exception as e:
        print(f"❌ 处理文件时出错: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='格式化并按string长度排序JSON文件')
    parser.add_argument('-i', '--input', help='输入文件路径')
    parser.add_argument('-o', '--output', help='输出JSON文件路径')
    args = parser.parse_args()

    if not args.input:
        print("❗请使用 -i 指定输入文件路径")
        print("示例: python3 format_json.py -i ./lang/en/en.json -o ./lang/en/sorted_en.json")
        sys.exit(1)

    if not os.path.exists(args.input):
        print(f"❌ 输入文件不存在: {args.input}")
        sys.exit(1)

    if not args.output:
        input_dir = os.path.dirname(args.input)
        input_filename = os.path.basename(args.input)
        output_path = os.path.join(input_dir, f"sorted_{input_filename}")
    else:
        output_path = args.output

    success = format_json_file(args.input, output_path)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()