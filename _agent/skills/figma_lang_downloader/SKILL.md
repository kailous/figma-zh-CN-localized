---
name: figma_lang_downloader
description: 下载 Figma 最新的官方英文语言包 (JSON)。
---

# Figma 语言包下载 Skill

该 Skill 用于从 Figma 官网自动探测并下载最新的英文语言包。

## 已验证的逻辑
1. 抓取 `https://www.figma.com/` 等入口页面。
2. 使用正则表达式 `https://www.figma.com/webpack-artifacts/assets/figma_app(?:_beta)?-[a-f0-9]+\.min\.en\.json(?:\.br)?` 提取最新的 JSON URL。
3. 下载并根据需要解压（.br 格式使用 brotli）。
4. 结果保存到 `lang/en_latest.json`。

## 如何使用
直接运行以下脚本即可：
```bash
python3 _agent/skills/figma_lang_downloader/scripts/download_latest.py
```
