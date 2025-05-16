#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import requests
import json
import sys
from pathlib import Path

def download_figma_json():
    # 创建目标目录
    output_dir = Path("lang/en")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        # 获取 Figma 主页
        print("正在获取 Figma 主页...")
        response = requests.get("https://www.figma.com", headers=headers)
        response.raise_for_status()
        
        # 使用正则表达式直接查找 JSON 文件链接
        pattern = r'(https://www\.figma\.com/webpack-artifacts/assets/figma_app_beta-[a-f0-9]+\.min\.en\.json(?:\.br)?)'
        matches = re.findall(pattern, response.text)
        
        if not matches:
            print("无法找到 Figma JSON 文件链接")
            sys.exit(1)
        
        # 获取第一个匹配的链接
        json_url = matches[0]
        
        # 移除 .br 后缀（如果有）
        if json_url.endswith('.br'):
            json_url = json_url[:-3]
        
        print(f"找到 JSON 文件链接: {json_url}")
        
        # 下载 JSON 文件
        print(f"正在下载: {json_url}")
        json_response = requests.get(json_url, headers=headers)
        json_response.raise_for_status()
        
        # 解析 JSON 以验证格式
        json_data = json.loads(json_response.content)
        
        # 从 URL 中提取文件名
        filename = json_url.split("/")[-1]
        output_file = output_dir / filename
        
        # 格式化 JSON 并保存到文件
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"成功下载并保存到: {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"处理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_figma_json()