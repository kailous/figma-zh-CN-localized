# 开发者说明

本项目已经改为 Agent-first 维护方式，不再需要人工拆分 JSON、复制给 ChatGPT、再手动合并。

公开产物仍然是：

```text
lang/zh.json
```

这个路径不要移动或改名。

## 更新流程

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py
```

如果需要指定下载好的英文包：

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py --source figma_app-xxxx.min.en.json.br.json
```

如果流程提示需要翻译，Agent 会读取 `.cache/pending.json` 并写入 `.cache/translated.json`。合并前必须运行：

```bash
python3 _agent/skills/figma_localize/scripts/validate_translation.py
```

然后继续：

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py --skip-sync --skip-translate
python3 _agent/skills/figma_localize/scripts/verify.py
```

## 贡献方向

- 修正 `lang/zh.json` 中的翻译质量问题
- 改进 `_agent/skills/figma_localize/scripts/` 工具链
- 更新 Surge、FigCN、脚本使用教程
- 补充 Agent 术语表和翻译规则

旧的拆分脚本说明已废弃；请以 `_agent/skills/figma_localize/SKILL.md` 为准。
