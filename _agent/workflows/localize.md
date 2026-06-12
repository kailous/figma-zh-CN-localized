---
description: Agent 维护 Figma 中文语言包：同步英文包、补译新增字段、校验并发布
---

# /localize

// turbo-all

## 目标

把 Figma 最新英文语言包同步到 `lang/en_latest.json`，补齐 `lang/zh.json` 缺失字段，并保证公开路径 `lang/zh.json` 可直接发布。

## 流程

1. 读取规则

```bash
sed -n '1,220p' _agent/skills/figma_localize/SKILL.md
```

2. 同步英文包

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py
```

如果用户给了下载文件：

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py --source <path-to-figma_app>
```

如果要忽略本地临时包：

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py --remote
```

3. 翻译

如果 `.cache/pending.json` 非空：

- 读取 `.cache/pending.json`
- 生成 `.cache/translated.json`
- 保持 JSON key 和结构一致
- 保留所有占位符和 ICU 语法
- 遵循 `SKILL.md` 术语表

4. 翻译质量校验

```bash
python3 _agent/skills/figma_localize/scripts/validate_translation.py
```

5. 合并并校验

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py --skip-sync --skip-translate
python3 _agent/skills/figma_localize/scripts/verify.py
```

6. 发布前检查

```bash
python3 -m json.tool lang/en_latest.json > /dev/null
python3 -m json.tool lang/zh.json > /dev/null
git diff --stat
git status --short --branch
```

7. 提交和推送

只提交跟踪文件和工具/文档改动。不要提交根目录下载包、`.cache/` 或 `lang/backup/`。
