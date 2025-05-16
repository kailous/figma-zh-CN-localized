#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import math
import shutil

def split_json_file(input_file, output_dir, items_per_file=500):
    """
    将JSON文件按照指定的键值对数量拆分成多个文件
    
    Args:
        input_file: 输入JSON文件路径
        output_dir: 输出目录路径
        items_per_file: 每个文件包含的键值对数量，默认为500
    """
    try:
        # 读取JSON文件
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 计算需要拆分的文件数量
        total_items = len(data)
        num_files = math.ceil(total_items / items_per_file)
        
        print(f"总共有 {total_items} 个键值对，将拆分为 {num_files} 个文件")
        
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"创建输出目录: {output_dir}")
        
        # 将数据拆分成多个文件
        items = list(data.items())
        for i in range(num_files):
            # 计算当前文件的起始和结束索引
            start_idx = i * items_per_file
            end_idx = min((i + 1) * items_per_file, total_items)
            
            # 提取当前文件的数据
            current_data = dict(items[start_idx:end_idx])
            
            # 设置输出文件路径
            output_file = os.path.join(output_dir, f"part_{i+1:03d}.json")
            
            # 将JSON转换为字符串，保持原始格式
            formatted_json = '{\n'
            current_items = list(current_data.items())
            for j, (key, value) in enumerate(current_items):
                # 将值转换为JSON字符串
                value_str = json.dumps(value, ensure_ascii=False)
                # 添加键值对，每个占一行
                formatted_json += f'  "{key}":{value_str}'
                # 如果不是最后一项，添加逗号
                if j < len(current_items) - 1:
                    formatted_json += ',\n'
                else:
                    formatted_json += '\n'
            formatted_json += '}'
            
            # 输出结果
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_json)
            print(f"已创建文件 {i+1}/{num_files}: {output_file}")
            
    except json.JSONDecodeError:
        print(f"错误: {input_file} 不是有效的JSON文件")
        return False
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        return False
    
    return True

def copy_split_folder_to_zh(source_dir):
    """
    将split文件夹复制到lang/zh目录
    
    Args:
        source_dir: split文件夹的源路径
    """
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        zh_dir = os.path.join(project_root, 'lang', 'zh')
        
        # 确保zh目录存在
        if not os.path.exists(zh_dir):
            os.makedirs(zh_dir)
            print(f"创建目录: {zh_dir}")
        
        # 设置目标目录路径
        target_dir = os.path.join(zh_dir, 'split')
        
        # 如果目标目录已存在，先删除
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
            print(f"已删除已存在的目标目录: {target_dir}")
        
        # 复制目录
        shutil.copytree(source_dir, target_dir)
        print(f"已成功将split文件夹复制到: {target_dir}")
        return True
    except Exception as e:
        print(f"复制split文件夹时出错: {str(e)}")
        return False

def main():
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='将JSON文件拆分为多个小文件')
    parser.add_argument('--items', type=int, default=500, help='每个文件包含的键值对数量（默认：500）')
    args = parser.parse_args()
    
    # 设置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    en_dir = os.path.join(project_root, 'lang', 'en')
    
    # 输入文件路径
    input_file = os.path.join(en_dir, 'sorted_en.json')
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        sys.exit(1)
    
    # 设置输出目录路径
    output_dir = os.path.join(en_dir, 'split')
    
    # 处理文件，使用命令行参数指定的键值对数量
    success = split_json_file(input_file, output_dir, args.items)
    if not success:
        sys.exit(1)
    
    print("拆分完成！")
    
    # 将split文件夹复制到lang/zh目录
    copy_success = copy_split_folder_to_zh(output_dir)
    if not copy_success:
        print("警告: 复制split文件夹到lang/zh目录失败")
    else:
        print("所有操作已完成！")

if __name__ == "__main__":
    main()