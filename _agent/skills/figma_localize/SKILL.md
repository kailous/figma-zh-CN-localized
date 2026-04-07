---
name: figma_localize
description: Figma 语言包全自动汉化工具链。一条命令完成：下载 → 对比 → AI 翻译 → 合并 → 校验。
---

# Figma 语言包全自动汉化 Skill

本 Skill 是 figma-zh-CN-localized 项目的核心自动化能力，将 Figma 官方英文语言包的更新自动同步为高质量中文翻译。

## 快速开始

当用户说"汉化新增条目"、"同步语言包"或使用 `/localize` 时，按以下流程执行：

```bash
# 全流程一键执行
python3 _agent/skills/figma_localize/scripts/run_all.py

# 或分步执行
python3 _agent/skills/figma_localize/scripts/sync.py      # 1. 下载最新英文包
python3 _agent/skills/figma_localize/scripts/diff.py       # 2. 对比差异
python3 _agent/skills/figma_localize/scripts/translate.py   # 3. 生成翻译任务
python3 _agent/skills/figma_localize/scripts/merge.py       # 4. 合并到主包
python3 _agent/skills/figma_localize/scripts/verify.py      # 5. 校验完整性
```

## 流程说明

### Step 1: sync — 下载最新英文包
从 Figma 官网自动探测最新的 `figma_app-*.min.en.json.br`，解压后保存为 `lang/en_latest.json`。

### Step 2: diff — 对比差异
将 `lang/en_latest.json` 与 `lang/zh.json` 进行键对比，提取英文中有但中文中没有的字段，输出到 `.cache/pending.json`。

### Step 3: translate — AI 自动翻译
读取 `.cache/pending.json`，自动分批生成翻译。**Agent 应直接读取该文件，按术语表翻译，然后写入 `.cache/translated.json`**。

### Step 4: merge — 合并到主包
自动备份 `lang/zh.json` 到 `lang/backup/`，将 `.cache/translated.json` 合入主包并格式化。

### Step 5: verify — 校验完整性
再次运行差异对比，确认中英文包的键完全一致（0 差异）。

## AI 翻译术语表（强制约束）

翻译时 **必须** 遵循以下术语规范：

| 英文 | 中文 | 备注 |
|:---|:---|:---|
| Dev Mode | 开发模式 (Dev Mode) | 首次出现带括号 |
| Code Connect | Code Connect | 保持英文 |
| MCP server | MCP 服务器 | |
| Storybook | Storybook | 保持英文 |
| Autolayout | 自动布局 | |
| Component | 组件 | |
| Instance | 实例 | |
| Variant | 变体 | |
| Token | 令牌 / 代币 | 认证场景用"令牌"，设计场景用"令牌 (Token)" |
| Diff overlay | 差异叠加层 | |
| Sprint retrospective | 冲刺回顾 | |
| Brainstorm | 头脑风暴 | |
| Weave | Weave | Figma 产品名，保持英文 |
| Riff | Riff | 社区功能，保持英文 |
| FigJam | FigJam | 保持英文 |
| Slides | Slides | 保持英文 |
| Buzz | Buzz | 保持英文 |
| Make | Make / 制作 | 上下文决定 |
| Pay as you go | 按需付费 | |
| Credits | 点数 | |
| Seat | 席位 | |
| Billing group | 计费组 | |
| Plan | 方案 | |
| Workspace | 工作空间 | |
| Organization | 组织 | |
| Enterprise | 企业 | |
| Starter | 入门版 (Starter) | |
| Professional | 专业版 (Professional) | |
| Library | 组件库 / 库 | |
| Accessibility | 无障碍 | |
| False positive | 误报 | |
| SCIM | SCIM | 保持英文 |
| SSO | SSO | 保持英文 |
| Prorated | 按比例计算 | |

### 翻译原则
1. **保留占位符**：`{variableName}` 必须原样保留
2. **保留 ICU 语法**：`{count, plural, one {...} other {...}}` 格式必须保持
3. **保留产品名**：Figma、FigJam、Slides、Buzz、Weave 等不翻译
4. **"你"而非"您"**：全部使用"你"保持亲切感
5. **JSON 格式**：输出必须是合法的 JSON，与输入结构完全一致
