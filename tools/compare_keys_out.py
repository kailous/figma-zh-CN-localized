#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import argparse

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def compare_keys(json1, json2):
    keys1 = set(json1.keys())
    keys2 = set(json2.keys())

    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1

    json1_only = {key: json1[key] for key in only_in_1}
    json2_only = {key: json2[key] for key in only_in_2}

    return json1_only, json2_only

def main():
    parser = argparse.ArgumentParser(description="对比两个 JSON 文件的键，并提取差异")
    parser.add_argument('json1', help="第一个 JSON 文件路径")
    parser.add_argument('json2', help="第二个 JSON 文件路径")
    parser.add_argument('--out1', default='only_in_json1.json', help="只存在于第一个文件的键输出路径")
    parser.add_argument('--out2', default='only_in_json2.json', help="只存在于第二个文件的键输出路径")
    args = parser.parse_args()

    json1 = load_json(args.json1)
    json2 = load_json(args.json2)

    json1_only, json2_only = compare_keys(json1, json2)

    save_json(json1_only, args.out1)
    save_json(json2_only, args.out2)

    print(f"✅ 已生成差异文件：\n - {args.out1}（仅存在于 {args.json1} 的键）\n - {args.out2}（仅存在于 {args.json2} 的键）")

if __name__ == '__main__':
    main()