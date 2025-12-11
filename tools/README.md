# 工具使用说明

`tools/` 目录下的脚本用于拆分、格式化、合并和对比 Figma 语言包（或结构相同的 JSON）。以下说明基于当前脚本实现，默认在仓库根目录运行命令：`python3 tools/<script>.py ...`。

## 环境要求
- Python 3.8+（自带 `json`/`argparse` 等标准库即可）
- 额外依赖：`tqdm`（仅 `compare_keys.py` 需要）。安装：`pip install tqdm`

## 目录约定
- `lang/`：翻译后的完整语言包，常用 `lang/zh.json`
- `org_dir/`：原始英文语言包，常用 `org_dir/en.json`
- `split_dir/`：`split_json.py` 生成的小文件；`merge_json.py` 默认从此处读
- `temp_dir/`：中间产物输出目录（格式化结果、差异结果、合并结果）

## 脚本详解

### split_json.py - 拆分大文件
- 功能：按顶层键值数量切片，将大 JSON 拆成若干小文件，便于投递给 AI 或协作翻译。
- 用法：`python3 tools/split_json.py <input_json> [items_per_file]`
  - `items_per_file` 默认为 `500`，决定每个输出文件包含的键值对数量。
- 行为与输出：
  - 运行前会删除并重建根目录下的 `split_dir/`（注意提前备份已有拆分结果）。
  - 输出文件命名为 `split_<源文件名>_<序号>.json`，序号从 001 递增，写入 `split_dir/`。
  - 拆分时保留原文件的键顺序，内容以 pretty JSON（每条独占一行）写入。
- 典型场景：`python3 tools/split_json.py lang/zh.json 300`

### merge_json.py - 合并拆分结果
- 功能：将拆分后的小文件重新合并成一个完整 JSON。
- 用法：`python3 tools/merge_json.py [-i INPUT_DIR] [-o OUTPUT_FILE]`
  - 默认输入目录：`split_dir/`，可识别 `split_*.json` 和 `part_*.json`。
  - 默认输出文件：若输入文件名包含 `split_<token>_***.json`，输出为 `temp_dir/merged_<token>.json`；否则写入 `temp_dir/merged.json`。
- 行为与输出：
  - 以文件名排序后逐个读取，后读到的文件中的同名键会覆盖先前的值。
  - 输出为 pretty JSON，必要时会自动创建输出目录。
- 典型场景：`python3 tools/merge_json.py -i split_dir -o temp_dir/merged_zh.json`

### format_json.py - 排序与格式化
- 功能：按 `string` 字段长度对顶层条目排序，并将每个键值对独占一行，便于人工检查或提交给 AI。
- 用法：`python3 tools/format_json.py <file_or_dir>`
  - 传入单个文件时，原地覆盖；传入目录时会遍历该目录下所有 `.json` 文件逐个处理。
- 行为与输出：
  - 如果条目包含 `{"string": "..."}` 结构，则按字符串长度升序排序；否则保持原顺序但同样格式化。
  - 写回原文件；无额外输出目录。
- 典型场景：`python3 tools/format_json.py lang/zh.json` 或 `python3 tools/format_json.py split_dir/`

### compare_keys.py - 对比中英文键差异
- 功能：比较中英文 JSON 的翻译键（仅关注叶子节点键名为 `string` 的路径），找出缺失或多余的条目，并生成差异结构。
- 用法（两种模式，不能混用目录与文件参数）：
  - 目录对比：`python3 tools/compare_keys.py --zh-dir <zh_dir> --en-dir <en_dir> [--out-dir <dir>]`
  - 单文件对比：`python3 tools/compare_keys.py --zh-file <zh.json> --en-file <en.json> [--out-dir <dir>]`
  - 默认输出目录：`temp_dir/`
- 行为与输出：
  - 日志：目录模式写入根目录 `compare_keys_directory.log`，单文件模式写入 `compare_keys_single.log`。
  - 差异文件（仅在发现差异时生成，输出到 `out_dir`）：
    - `<name>_en-new.json`：英文独有的键及其原始值（保持原结构）。
    - `<name>_zh-new.json`：移除“仅中文存在”的键后的中文结构。
    - `<name>_zh-filtered.json`：中文文件再过滤掉“中文独有键”后的结果（若与 `_zh-new` 相同则跳过）。
  - 进度显示：使用 `tqdm` 显示处理进度；若缺少文件，会在日志中标记。
- 典型场景：`python3 tools/compare_keys.py --zh-dir lang --en-dir org_dir` 或 `python3 tools/compare_keys.py --zh-file lang/zh.json --en-file org_dir/en.json --out-dir temp_dir/compare`

## 推荐工作流
1) 拆分：`split_json.py` 将完整语言包切块到 `split_dir/`，便于多人或 AI 翻译。
2) 翻译与整理：对拆分文件翻译后，可用 `format_json.py split_dir/` 统一格式。
3) 合并：翻译完成后用 `merge_json.py` 生成合并版本（默认输出到 `temp_dir/`）。
4) 对比：用 `compare_keys.py` 与原始英文包比对，检查是否有遗漏或多余的键，复核输出的差异文件后再入库。

若流程中需要自定义输入输出路径，可通过脚本参数覆盖默认目录；默认路径均以仓库根目录为基准。
