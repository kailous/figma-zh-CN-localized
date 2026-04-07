#!/usr/bin/env python3
"""sync.py — 从 Figma 官网下载最新英文语言包"""
import sys
import os
import re
import urllib.request
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

VERIFIED_HASHES = []  # 保留为空，强制使用自动探测

def sync(manual_hash=None):
    url = 'https://www.figma.com/community'
    headers = {'User-Agent': 'Mozilla/5.0'}

    h = manual_hash
    prefix = "figma_app"

    if not h:
        print("🔍 正在从 Figma 探测最新语言包...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                res = response.read().decode('utf-8', errors='ignore')
                found = re.search(r'figma_app(?:_beta|__rspack)?-([a-f0-9]{10,64})', res)
                if found:
                    h = found.group(1)
                    if "__rspack" in found.group(0):
                        prefix = "figma_app__rspack"
                    elif "_beta" in found.group(0):
                        prefix = "figma_app_beta"
                    print(f"  ✅ 捕获资源标识: {prefix}-{h}")
        except Exception as e:
            print(f"  ⚠️  自动探测失败: {e}")
            return False

    if not h:
        print("  ❌ 无法定位语言包。可手动指定哈希: python3 .../sync.py <hash>")
        return False

    # 尝试下载，自动切换前缀
    prefixes = list(dict.fromkeys([prefix, "figma_app__rspack", "figma_app"]))
    dest_dir = os.path.join(PROJECT_ROOT, "lang")
    dest_file = os.path.join(dest_dir, "en_latest.json")
    dest_br = os.path.join(dest_dir, "en_latest.json.br")
    os.makedirs(dest_dir, exist_ok=True)

    for p in prefixes:
        sync_url = f"https://www.figma.com/webpack-artifacts/assets/{p}-{h}.min.en.json.br"
        try:
            print(f"  ⬇️  尝试: {p}-{h} ...")
            req = urllib.request.Request(sync_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                with open(dest_br, 'wb') as f:
                    f.write(data)

            subprocess.run(["brotli", "-d", "-f", dest_br, "-o", dest_file], check=True)
            size_mb = os.path.getsize(dest_file) / 1024 / 1024
            print(f"  ✅ 同步完成: {dest_file} ({size_mb:.1f} MB)")
            return True
        except Exception:
            continue

    print(f"  ❌ 所有前缀尝试均失败 (hash: {h})")
    return False


if __name__ == "__main__":
    arg_hash = sys.argv[1] if len(sys.argv) > 1 else None
    ok = sync(arg_hash)
    sys.exit(0 if ok else 1)
