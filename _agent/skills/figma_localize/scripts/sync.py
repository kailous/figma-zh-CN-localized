#!/usr/bin/env python3
"""sync.py — 同步最新英文语言包，优先使用本地下载的 .br 文件"""
import sys
import os
import re
import urllib.request
import subprocess
import shutil
import glob
import json
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

VERIFIED_HASHES = []  # 保留为空，强制使用自动探测

def decompress_brotli(src, dest):
    """解压 Brotli 文件。优先使用系统 brotli，缺失时回退到 Node.js 内置 zlib。"""
    brotli_bin = shutil.which("brotli")
    if brotli_bin:
        subprocess.run([brotli_bin, "-d", "-f", src, "-o", dest], check=True)
        return

    node_bin = shutil.which("node")
    if node_bin:
        script = (
            "const fs=require('fs');"
            "const zlib=require('zlib');"
            "fs.writeFileSync(process.argv[2],"
            "zlib.brotliDecompressSync(fs.readFileSync(process.argv[1])));"
        )
        subprocess.run([node_bin, "-e", script, src, dest], check=True)
        return

    raise RuntimeError("未找到 brotli 命令或 node，无法解压 .br 文件")


def sync_local_pack(source_file, dest_br, dest_file):
    """同步本地文件；允许 .br 文件实际已经是明文 JSON。"""
    with open(source_file, "rb") as f:
        head = f.read(1)

    if head in (b"{", b"["):
        with open(source_file, "r", encoding="utf-8") as f:
            json.load(f)
        shutil.copy2(source_file, dest_file)
        if os.path.abspath(source_file) != os.path.abspath(dest_br):
            shutil.copy2(source_file, dest_br)
        return

    if os.path.abspath(source_file) != os.path.abspath(dest_br):
        shutil.copy2(source_file, dest_br)
    decompress_brotli(dest_br, dest_file)


def find_local_pack():
    patterns = [
        os.path.join(PROJECT_ROOT, "figma_app*.min.en.json.br"),
        os.path.join(PROJECT_ROOT, "figma_app*.min.en.json.br.json"),
        os.path.join(PROJECT_ROOT, "lang", "figma_app*.min.en.json.br"),
        os.path.join(PROJECT_ROOT, "lang", "figma_app*.min.en.json.br.json"),
    ]
    matches = []
    for pattern in patterns:
        matches.extend(glob.glob(pattern))
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)


def sync(manual_source=None, prefer_remote=False):
    dest_dir = os.path.join(PROJECT_ROOT, "lang")
    dest_file = os.path.join(dest_dir, "en_latest.json")
    dest_br = os.path.join(dest_dir, "en_latest.json.br")
    os.makedirs(dest_dir, exist_ok=True)

    if manual_source and os.path.isfile(manual_source):
        source_file = manual_source
    elif not prefer_remote:
        source_file = find_local_pack()
    else:
        source_file = None

    if source_file:
        print(f"📦 使用本地英文包: {os.path.relpath(source_file, PROJECT_ROOT)}")
        try:
            sync_local_pack(source_file, dest_br, dest_file)
        except Exception as e:
            print(f"  ❌ 解压失败: {e}")
            return False
        size_mb = os.path.getsize(dest_file) / 1024 / 1024
        print(f"  ✅ 同步完成: {dest_file} ({size_mb:.1f} MB)")
        return True

    url = 'https://www.figma.com/community'
    headers = {'User-Agent': 'Mozilla/5.0'}

    h = manual_source
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

    for p in prefixes:
        sync_url = f"https://www.figma.com/webpack-artifacts/assets/{p}-{h}.min.en.json.br"
        try:
            print(f"  ⬇️  尝试: {p}-{h} ...")
            req = urllib.request.Request(sync_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                with open(dest_br, 'wb') as f:
                    f.write(data)

            decompress_brotli(dest_br, dest_file)
            size_mb = os.path.getsize(dest_file) / 1024 / 1024
            print(f"  ✅ 同步完成: {dest_file} ({size_mb:.1f} MB)")
            return True
        except Exception:
            continue

    print(f"  ❌ 所有前缀尝试均失败 (hash: {h})")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="同步 Figma 英文语言包到 lang/en_latest.json")
    parser.add_argument("source", nargs="?", help="本地包路径或 Figma 资源 hash")
    parser.add_argument("--remote", action="store_true", help="忽略根目录本地包，强制远程探测/下载")
    args = parser.parse_args()
    ok = sync(args.source, prefer_remote=args.remote)
    sys.exit(0 if ok else 1)
