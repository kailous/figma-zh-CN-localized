#!/usr/bin/env python3
"""validate_translation.py — 校验 Agent 生成的 translated.json 是否可安全合并"""
import json
import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
CACHE_DIR = os.path.join(PROJECT_ROOT, ".cache")

SIMPLE_PLACEHOLDER_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")
ICU_ARGUMENT_RE = re.compile(
    r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*,\s*(plural|selectordinal|select|date|time|number)\s*,"
)
ICU_BRANCH_KEY_RE = re.compile(r"\s*(?:[A-Za-z_][A-Za-z0-9_]*|=\d+)\s*")
SIMPLE_ARGUMENT_RE = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{4,}")
URL_OR_COMMAND_RE = re.compile(r"(https?://|ssh-keyscan|ssh-agent|@[\w.-]+)")
ALLOW_UNCHANGED = {
    "Figma", "FigJam", "Slides", "Weave", "Riff", "GitHub", "Storybook",
    "MCP", "OIDC", "SSO", "SCIM", "API", "JSON", "CSS", "HTML", "JSX",
    "Xcode", "PowerPoint", "Excel", "Word", "OKLAB", "OKLCH", "HSL",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _balanced_end(text, start):
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _collect_placeholders(text, found):
    index = 0
    while index < len(text):
        if text[index] != "{":
            index += 1
            continue
        end = _balanced_end(text, index)
        if end == -1:
            break
        inner = text[index + 1:end]
        argument = ICU_ARGUMENT_RE.match(inner)
        if argument:
            found.append("{%s,%s}" % (argument.group(1), argument.group(2)))
            body = inner[argument.end():]
            offset = 0
            while offset < len(body):
                key = ICU_BRANCH_KEY_RE.match(body, offset)
                if not key:
                    break
                offset = key.end()
                if offset >= len(body) or body[offset] != "{":
                    break
                branch_end = _balanced_end(body, offset)
                if branch_end == -1:
                    break
                # Branch copy may contain nested placeholders; branch keys do not count.
                _collect_placeholders(body[offset + 1:branch_end], found)
                offset = branch_end + 1
        else:
            argument = SIMPLE_ARGUMENT_RE.match(inner)
            if argument:
                found.append("{" + argument.group(1) + "}")
        index = end + 1


def placeholders(text):
    found = []
    _collect_placeholders(text or "", found)
    return sorted(found)


def strip_placeholders(text):
    return SIMPLE_PLACEHOLDER_RE.sub("", text or "")


def validate_translation():
    pending_file = os.path.join(CACHE_DIR, "pending.json")
    translated_file = os.path.join(CACHE_DIR, "translated.json")

    if not os.path.exists(pending_file):
        print("❌ .cache/pending.json 不存在。请先运行 diff.py")
        return False
    if not os.path.exists(translated_file):
        print("❌ .cache/translated.json 不存在。请先完成翻译")
        return False

    pending = load_json(pending_file)
    translated = load_json(translated_file)

    pending_keys = set(pending.keys())
    translated_keys = set(translated.keys())
    missing = pending_keys - translated_keys
    extra = translated_keys - pending_keys

    ok = True
    if missing:
        ok = False
        print(f"❌ translated.json 缺少 {len(missing)} 个键")
        for key in sorted(missing)[:20]:
            print(f"   - {key}")
    if extra:
        print(f"⚠️  translated.json 多出 {len(extra)} 个键，merge.py 会忽略不了它们；建议清理")

    placeholder_errors = []
    unchanged = []
    for key in sorted(pending_keys & translated_keys):
        src = pending[key].get("string", "") if isinstance(pending[key], dict) else ""
        dst = translated[key].get("string", "") if isinstance(translated[key], dict) else ""
        if placeholders(src) != placeholders(dst):
            placeholder_errors.append((key, src, dst))
        visible_src = strip_placeholders(src)
        if (
            src == dst
            and ENGLISH_WORD_RE.search(visible_src)
            and not URL_OR_COMMAND_RE.search(visible_src)
            and not any(token in visible_src for token in ALLOW_UNCHANGED)
        ):
            unchanged.append((key, src))

    if placeholder_errors:
        ok = False
        print(f"❌ 占位符/ICU 片段不一致: {len(placeholder_errors)} 条")
        for key, src, dst in placeholder_errors[:20]:
            print(f"   - {key}")
            print(f"     EN: {src}")
            print(f"     ZH: {dst}")

    if unchanged:
        print(f"⚠️  仍有 {len(unchanged)} 条疑似未翻译英文（可保留技术词，但需人工/Agent 复核）")
        for key, src in unchanged[:30]:
            print(f"   - {key}: {src}")

    if ok:
        print("✅ 翻译文件结构与占位符校验通过")
    return ok


if __name__ == "__main__":
    sys.exit(0 if validate_translation() else 1)
