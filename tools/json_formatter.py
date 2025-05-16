#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

def format_json_file(file_path, output_path):
    """
    格式化JSON文件，使每个键值对占用单独的一行
    并按照'string'属性的长度进行排序
    
    Args:
        file_path: JSON文件路径
        output_path: 输出文件路径
    """
    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 创建一个包含键和对应'string'属性长度的列表
        items_with_length = []
        for key, value in data.items():
            # 检查值是否为字典且包含'string'属性
            if isinstance(value, dict) and 'string' in value:
                string_length = len(value['string'])
                items_with_length.append((key, value, string_length))
            else:
                # 对于不符合格式的项，将长度设为-1，保持原有顺序
                items_with_length.append((key, value, -1))
        
        # 根据'string'属性的长度排序
        sorted_items = sorted(items_with_length, key=lambda x: x[2])
        
        # 将排序后的项转换为有序字典
        sorted_data = {item[0]: item[1] for item in sorted_items}
        items = list(sorted_data.items())
        
        # 将JSON转换为字符串，每个键值对占一行
        formatted_json = '{\n'
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
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_json)
        print(f"排序并格式化完成，结果已保存到: {output_path}")
            
    except json.JSONDecodeError:
        print(f"错误: {file_path} 不是有效的JSON文件")
        return False
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")
        return False
    
    return True

def main():
    # 设置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    en_dir = os.path.join(project_root, 'lang', 'en')
    
    json_file = None
    for file in os.listdir(en_dir):
        if file.endswith('.json'):
            json_file = os.path.join(en_dir, file)
            break
    
    if not json_file:
        print("错误: 在lang/en目录下未找到JSON文件")
        sys.exit(1)
    
    # 设置输出文件路径
    output_file = os.path.join(en_dir, 'sorted_en.json')
    
    # 处理文件
    success = format_json_file(json_file, output_file)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()