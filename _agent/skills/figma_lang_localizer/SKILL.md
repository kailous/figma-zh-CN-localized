# Figma 语言包汉化同步 Skill (figma_lang_localizer)

本 Skill 用于自动化处理 Figma 官方语言包更新后产生的新增字段。它集成了 `tools/` 目录下的各项脚本，提供一套标准的、工业级的汉化同步工作流。

## 核心功能

1. **自动对比差异**: 提取 `en_latest.json` 相比 `zh.json` 新增的键值对。
2. **按长排序优化**: 自动对新增字段按字符串长度排序，极大提升 AI 翻译或人工审阅效率。
3. **安全合并备份**: 将翻译后的内容合入 `zh.json`，并自动生成备份。

## 使用方法

### 1. 查找新增字段

运行以下命令，脚本将分析 `lang/en_latest.json` 并在 `temp_dir/localize/` 下生成待翻译文件。

```bash
python3 _agent/skills/figma_lang_localizer/scripts/localize_new_fields.py --compare
```

### 2. 翻译与整理

系统会提示待翻译文件路径（通常为 `temp_dir/localize/new_fields_pending.json`）。你可以手动翻译该文件，或者要求 AI 助手协助翻译。

### 3. 合并回主语言包

翻译完成后，运行以下命令将内容合入 `zh.json`：

```bash
python3 _agent/skills/figma_lang_localizer/scripts/localize_new_fields.py --merge
```

## 技术细节

- **对比逻辑**: 仅关注叶子节点键名为 `string` 的路径，忽略结构差异。
- **依赖说明**: 需要 `python3` 环境。已在 `tools/compare_keys.py` 中实现了对 `tqdm` 的可选兼容。
- **备份机制**: 每次合并前，旧的 `zh.json` 将会被备份至 `lang/backup/`。
