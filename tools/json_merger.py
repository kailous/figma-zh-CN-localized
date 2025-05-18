#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import glob

def merge_json_files(input_dir, output_file):
    """
    将多个JSON文件合并为一个文件
    
    Args:
        input_dir: 包含拆分JSON文件的目录路径
        output_file: 输出文件路径
    """
    try:
        # 确保输入目录存在
        if not os.path.exists(input_dir):
            print(f"错误: 输入目录不存在: {input_dir}")
            return False
        
        # 获取所有JSON文件
        json_files = sorted(glob.glob(os.path.join(input_dir, "part_*.json")))
        
        if not json_files:
            print(f"错误: 在 {input_dir} 中未找到JSON文件")
            return False
        
        print(f"找到 {len(json_files)} 个JSON文件，开始合并...")
        
        # 合并所有文件的数据
        merged_data = {}
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                merged_data.update(data)
                print(f"已处理: {os.path.basename(file_path)}")
            except json.JSONDecodeError:
                print(f"警告: 跳过无效的JSON文件: {file_path}")
            except Exception as e:
                print(f"警告: 处理文件 {file_path} 时出错: {str(e)}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        
        # 将合并的数据写入输出文件
        # 将JSON转换为字符串，保持原始格式
        formatted_json = '{\n'
        items = list(merged_data.items())
        for i, (key, value) in enumerate(items):
            # 将值转换为JSON字符串
            value_str = json.dumps(value, ensure_ascii=False)
            # 添加键值对，每个占一行
            formatted_json += f'  "{key}":{value_str}'
            # 如果不是最后一项，添加逗号
            if i < len(items) - 1:
                formatted_json += ',\n'
            else:
                formatted_json += '\n'
        formatted_json += '}'
        
        # 输出结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_json)
        
        print(f"合并完成！结果已保存到: {output_file}")
        print(f"总共合并了 {len(merged_data)} 个键值对")
        
        return True
    except Exception as e:
        print(f"合并文件时出错: {str(e)}")
        return False

def main():
    # 设置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    zh_dir = os.path.join(project_root, 'lang', 'zh')
    
    # 输入目录路径
    input_dir = os.path.join(zh_dir, 'split')
    
    # 检查输入目录是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        sys.exit(1)
    
    # 设置输出文件路径
    output_file = os.path.join(zh_dir, 'zh.json')
    
    # 处理文件
    success = merge_json_files(input_dir, output_file)
    if not success:
        sys.exit(1)
    
    print("所有操作已完成！")

if __name__ == "__main__":
    main()