#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import glob
import argparse

def merge_json_files(input_dir, output_file):
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

        json_files = sorted(glob.glob(os.path.join(input_dir, "part_*.json")))

        if not json_files:
            print(f"错误: 在 {input_dir} 中未找到 part_*.json 文件")
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
            os.makedirs(output_dir)
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
    parser.add_argument('-i', '--input', required=False, help="输入目录路径 (如: ./lang/zh/split)")
    parser.add_argument('-o', '--output', required=False, help="输出文件路径 (如: ./lang/zh/zh.json)")
    args = parser.parse_args()

    if not args.input or not args.output:
        print("❗用法: python3 merge_json.py --input 输入目录 --output 输出文件路径")
        print("示例: python3 merge_json.py --input ./lang/zh/split --output ./lang/zh/zh.json")
        sys.exit(1)

    success = merge_json_files(args.input, args.output)
    if not success:
        sys.exit(1)

    print("🎉 所有操作已完成！")

if __name__ == "__main__":
    main()