## 开发者说明

### compare_keys.py <br> 对比工具
对比两个 JSON 文件的键值对差异，主要是为了避免重复翻译键值对。
参数说明
- -ZH, --zh-dir 中文 JSON 文件路径(目录)
- -EN, --en-dir 英文 JSON 文件路径(目录)
- -zh, --zh-file 中文 JSON 文件路径(文件)
- -en, --en-file 英文 JSON 文件路径(文件)
- -o, --out-dir 结果输出目录（可选）
日志会自动写入项目根目录下的 `compare_keys_directory.log` 或 `compare_keys_single.log`。同时会生成 `_en-new.json`、`_zh-new.json` 以及（如有需要）`_zh-filtered.json`，默认写入根目录的 `temp_dir`，可通过 `--out-dir` 自定义目录。
```
python3 tools/compare_keys.py \
--zh-file lang/zh.json \
--en-file org_dir/en.json
```

### format_json.py <br> 格式化并按 string 长度排序
用于将 JSON 文件格式化，并按照其中 string 字段的长度升序排序输出。为了方便丢给 chatgpt 进行逐行翻译。
参数说明
- JSON 文件路径或目录路径（位置参数）
会直接覆盖原文件；如果传入目录，则对该目录下所有 `.json` 文件执行格式化。
```
python3 tools/format_json.py lang/zh.json
python3 tools/format_json.py lang/
```

### split_json.py <br> 拆分大型 JSON 文件为多个小文件
用于将大型 JSON 文件拆分为多个小文件，每个小文件包含指定数量的键值对。chatgpt 一次处理的词条数量有限，所以需要拆分文件。
参数说明
- 输入 JSON 文件路径（位置参数）
- 每个小文件的键值对数量（可选，默认 500）
拆分结果会写入项目根目录的 `split_dir` 目录，文件名形如 `split_<文件名>_001.json`。
```
python3 tools/split_json.py lang/en.json 100
```

### merge_json.py <br> 合并多个拆分后的 JSON 文件
用于将多个拆分后的 JSON 文件合并为一个大型 JSON 文件。
参数说明
- -i, --input 输入目录路径（可选，默认使用项目根目录的 `split_dir`）
- -o, --output 输出 JSON 文件路径（可选，默认写入项目根目录的 `temp_dir/merged*.json`。若拆分文件名形如 `split_en_*.json` 会自动生成 `merged_en.json`，`split_zh_*` 则生成 `merged_zh.json`）
```
python3 tools/merge_json.py
python3 tools/merge_json.py -i lang/zh/split -o lang/zh/merged.json
```

### 对比工具使用方法
```
python3 tools/compare_keys.py --zh-file ./lang/zh/zh.json --en-file ./lang/zh/en.json
```

### 格式化工具使用方法
```
python3 tools/format_json.py lang/zh.json
python3 tools/format_json.py lang/
```
