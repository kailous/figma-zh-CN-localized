# Agent 工具链

旧版 `tools/` 拆分、对比、合并流程已废弃。当前维护入口集中在：

```text
_agent/skills/figma_localize/scripts/
```

## 脚本

```text
sync.py                 同步 Figma 英文语言包
diff.py                 提取英文新增、中文缺失的字段
translate.py            输出 Agent 翻译任务状态
validate_translation.py 校验 translated.json 的键和占位符
merge.py                合并翻译并备份 zh.json
verify.py               校验中文包覆盖英文包
format_json.py          稳定格式化 JSON
run_all.py              串联主流程
```

## 常用命令

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py
python3 _agent/skills/figma_localize/scripts/run_all.py --source figma_app-xxxx.min.en.json.br.json
python3 _agent/skills/figma_localize/scripts/validate_translation.py
python3 _agent/skills/figma_localize/scripts/verify.py
```

## 产物约定

- `lang/zh.json`：唯一公开中文语言包
- `lang/en_latest.json`：最新英文包
- `.cache/pending.json`：待翻译字段
- `.cache/translated.json`：Agent 生成的翻译结果
- `lang/backup/`：合并前自动备份

`.cache/`、`lang/backup/` 和根目录下载包不提交。
