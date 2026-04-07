import sys
import os
import re
import urllib.request
import subprocess

# 策略配置：内置已验证的哈希作为兜底 (手动抓取)
VERIFIED_HASHES = ["a72dbae372dd2bf8"]

def sync(manual_hash=None):
    # 彻底复刻诊断成功逻辑: 极简 URL 与 Headers (仅 User-Agent)
    url = 'https://www.figma.com/community'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    h = manual_hash
    prefix = "figma_app" # 2026/04 探测表明 community 页面目前回归了 figma_app 前缀
    
    if not h:
        print(f"正在从社区页面探测最新资源...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                res = response.read().decode('utf-8', errors='ignore')
                found = re.search(r'figma_app(?:_beta|__rspack)?-([a-f0-9]{10,64})', res)
                if found:
                    h = found.group(1)
                    if "__rspack" in found.group(0): prefix = "figma_app__rspack"
                    elif "_beta" in found.group(0): prefix = "figma_app_beta"
                    print(f"✅ 捕获成功! 特征标识: {prefix}, 哈希: {h}")
        except Exception as e:
            print(f"⚠️ 自动探测受阻 (Figma 网络防御): {e}")
            if VERIFIED_HASHES:
                h = VERIFIED_HASHES[0]
                print(f"💡 使用内置已验证哈希进行兜底同步: {h}")
            else:
                print("❌ 无法自动定位语言包，请尝试在命令行指定哈希: python3 .../download_latest.py <hash>")
                return False

    if not h: return False
    
    # 开始同步流程
    # 尝试多种前缀 (防止 figma_app 与 __rspack 切换)
    prefixes = [prefix, "figma_app__rspack", "figma_app"]
    success = False
    
    for p in sorted(list(set(prefixes)), reverse=True):
        sync_url = f"https://www.figma.com/webpack-artifacts/assets/{p}-{h}.min.en.json.br"
        dest_dir = "lang"
        dest_file = os.path.join(dest_dir, "en_latest.json")
        temp_br = os.path.join(dest_dir, "temp.br")
        
        os.makedirs(dest_dir, exist_ok=True)
        
        try:
            print(f"正在尝试下载流程: {p}-{h} ...")
            down_req = urllib.request.Request(sync_url, headers=headers)
            with urllib.request.urlopen(down_req, timeout=30) as down_res:
                with open(temp_br, 'wb') as f:
                    f.write(down_res.read())
            
            subprocess.run(["brotli", "-d", "-f", temp_br, "-o", dest_file], check=True)
            if os.path.exists(temp_br): os.remove(temp_br)
            print(f"🎉 同步完成! 文件已保存至: {dest_file}")
            success = True
            break
        except Exception:
            # 探测失败则继续尝试下一个前缀
            continue
            
    if not success:
        print(f"❌ 下载失败: 无法访问哈希 {h} 对应的资源。")
        
    return success

if __name__ == "__main__":
    arg_hash = sys.argv[1] if len(sys.argv) > 1 else None
    sync(arg_hash)
