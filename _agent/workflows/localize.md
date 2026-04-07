---
description: 一键汉化 Figma 语言包：下载 → 对比 → AI 翻译 → 合并 → 校验
---

# /localize — Figma 语言包全自动汉化

// turbo-all

## 完整流程

1. 读取 Skill 定义
```
查看 _agent/skills/figma_localize/SKILL.md 了解术语表和翻译规则
```

2. 同步最新英文包
```bash
python3 _agent/skills/figma_localize/scripts/sync.py
```

3. 对比差异，提取新增字段
```bash
python3 _agent/skills/figma_localize/scripts/diff.py
```

4. 检查翻译任务
```bash
python3 _agent/skills/figma_localize/scripts/translate.py
```

5. **AI 翻译** — 如果 `.cache/pending.json` 非空，则：
   - 读取 `.cache/pending.json` 中的全部英文字段
   - 按 SKILL.md 中的术语表进行翻译
   - 保留所有 `{variable}` 占位符和 ICU 复数语法
   - 将翻译结果写入 `.cache/translated.json`（格式与输入一致）

6. 合并翻译到主语言包
```bash
python3 _agent/skills/figma_localize/scripts/merge.py
```

7. 校验同步完整性
```bash
python3 _agent/skills/figma_localize/scripts/verify.py
```
