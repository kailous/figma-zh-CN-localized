---
name: figma_localize
description: Agent-first Figma 中文语言包维护工具链：同步英文包、提取差异、生成翻译、校验占位符、合并并发布。
---

# Figma 中文语言包 Agent Skill

你维护的是 `figma-zh-CN-localized`。公开产物是 `lang/zh.json`，这个路径不能移动、改名或替换成版本化路径。

## 默认工作流

1. 同步英文包

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py
```

可选：

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py --source figma_app-xxxx.min.en.json.br.json
python3 _agent/skills/figma_localize/scripts/run_all.py --remote
```

2. 如果流程停在翻译阶段，读取 `.cache/pending.json`，生成 `.cache/translated.json`。

3. 合并前必须校验：

```bash
python3 _agent/skills/figma_localize/scripts/validate_translation.py
```

4. 合并和完整性校验：

```bash
python3 _agent/skills/figma_localize/scripts/run_all.py --skip-sync --skip-translate
python3 _agent/skills/figma_localize/scripts/verify.py
```

5. 发布前确认：

```bash
python3 -m json.tool lang/en_latest.json > /dev/null
python3 -m json.tool lang/zh.json > /dev/null
git diff --stat
```

## 工具职责

- `sync.py`：同步英文包到 `lang/en_latest.json`。支持本地 `.br`、浏览器另存为 `.br.json`、明文 JSON、Brotli 压缩包和远程 hash。
- `diff.py`：将英文包中新增但中文包缺失的键写入 `.cache/pending.json`。
- `translate.py`：显示翻译任务状态；真正翻译由 Agent 写入 `.cache/translated.json`。
- `validate_translation.py`：检查 translated 的 key、占位符和 ICU 片段是否安全。
- `merge.py`：备份 `lang/zh.json`，合并翻译并格式化。
- `verify.py`：确认 `lang/en_latest.json` 中所有 key 均被 `lang/zh.json` 覆盖。
- `format_json.py`：按字符串长度排序并压成稳定 JSON 格式。

## 翻译硬性规则

1. 保留所有 `{variableName}`、`{count, plural, ...}`、`{date, date, ...}` 等 ICU 片段。变量名和逗号不能汉化。
2. 全部使用“你”，不要使用“您”。
3. 按 UI 短句翻译，优先简洁：按钮、菜单、标签不要写成长句。
4. 产品名保持英文：Figma、FigJam、Slides、Buzz、Weave、Riff、Make、FigPal。
5. 技术名按上下文保留：MCP、Code Connect、Storybook、GitHub、Xcode、OIDC、SSO、SCIM、API、JSON、CSS、HTML、JSX。
6. 不确定的命令、路径、代码片段、快捷键、邮箱、URL 保持原样。
7. 合并前必须跑 `validate_translation.py`；如有占位符错误，不能合并。

## 术语表

| 英文 | 中文 |
|:---|:---|
| Dev Mode | 开发模式 (Dev Mode) |
| MCP server | MCP 服务器 |
| Autolayout | 自动布局 |
| Component | 组件 |
| Instance | 实例 |
| Variant | 变体 |
| Token | 令牌 |
| Diff overlay | 差异叠加层 |
| Sprint retrospective | 冲刺回顾 |
| Brainstorm | 头脑风暴 |
| Credits | 点数 |
| Seat | 席位 |
| Billing group | 计费组 |
| Plan | 方案 |
| Workspace | 工作空间 |
| Organization | 组织 |
| Enterprise | 企业 |
| Starter | 入门版 (Starter) |
| Professional | 专业版 (Professional) |
| Library | 组件库 |
| Accessibility | 无障碍 |
| False positive | 误报 |
| Prorated | 按比例计算 |

## 发布注意

- 根目录 `figma_app*.min.en.json.br*` 是临时输入，已被 `.gitignore` 忽略，不要提交。
- `.cache/` 和 `lang/backup/` 不提交。
- 如果推送后 GitHub Pages 未立即刷新，先比对 raw.githubusercontent.com，再等待 Pages/CDN 缓存刷新。
