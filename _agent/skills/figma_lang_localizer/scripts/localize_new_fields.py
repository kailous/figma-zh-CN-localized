import os
import sys
import subprocess
import argparse
import shutil
from datetime import datetime

# 路径配置
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
TOOLS_DIR = os.path.join(PROJECT_ROOT, 'tools')
LANG_DIR = os.path.join(PROJECT_ROOT, 'lang')
TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp_dir', 'localize')
BACKUP_DIR = os.path.join(LANG_DIR, 'backup')

def run_command(cmd, cwd=PROJECT_ROOT):
    """运行终端命令"""
    print(f"执行命令: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        sys.exit(1)

def ensure_dirs():
    """确保必要的目录存在"""
    for d in [TEMP_DIR, BACKUP_DIR]:
        os.makedirs(d, exist_ok=True)

def compare_mode():
    """对比模式：提取差异并排序"""
    ensure_dirs()
    zh_file = os.path.join(LANG_DIR, 'zh.json')
    en_file = os.path.join(LANG_DIR, 'en_latest.json')
    
    if not os.path.exists(en_file):
        print(f"❌ 错误: 找不到 {en_file}。请先运行 figma_lang_downloader 同步最新包。")
        return

    print("🔍 正在分析语言包差异...")
    # 1. 对比并生成差异
    compare_script = os.path.join(TOOLS_DIR, 'compare_keys.py')
    run_command([sys.executable, compare_script, '--zh-file', zh_file, '--en-file', en_file, '--out-dir', TEMP_DIR])
    
    # 2. 查找生成的 en-new.json
    new_fields_file = None
    for f in os.listdir(TEMP_DIR):
        if f.endswith('_en-new.json'):
            new_fields_file = os.path.join(TEMP_DIR, f)
            break
            
    if not new_fields_file or os.path.getsize(new_fields_file) < 5: # 简单判断是否有内容
        print("🎉 恭喜! 未发现新增字段，当前翻译已是最新。")
        return

    # 3. 排序并格式化新增字段
    print("🪄 正在对新增字段进行排序优化...")
    format_script = os.path.join(TOOLS_DIR, 'format_json.py')
    run_command([sys.executable, format_script, new_fields_file])
    
    # 4. 重命名为标准待处理文件
    pending_file = os.path.join(TEMP_DIR, 'new_fields_pending.json')
    if os.path.exists(pending_file): os.remove(pending_file)
    os.rename(new_fields_file, pending_file)
    
    print("\n✅ 提取完成!")
    print(f"👉 待翻译文件已就绪: {pending_file}")
    print("💡 你现在可以翻译该文件中的内容，完成后运行 --merge 合入。")

def merge_mode():
    """合并模式：安全合入 zh.json"""
    pending_file = os.path.join(TEMP_DIR, 'new_fields_pending.json')
    zh_file = os.path.join(LANG_DIR, 'zh.json')
    
    if not os.path.exists(pending_file):
        print(f"❌ 错误: 找不到待翻译文件 {pending_file}。请先运行 --compare。")
        return

    # 1. 备份 zh.json
    ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"zh_backup_{timestamp}.json")
    shutil.copy2(zh_file, backup_file)
    print(f"📦 已创建安全备份: {backup_file}")

    # 2. 合并
    print("正在合并新字段到 zh.json...")
    # 使用 tools/merge_json.py 逻辑或者是简单的字典合并
    # 鉴于 merge_json.py 只能从目录读，我们手动构造一个字典合并逻辑以确保精确性
    try:
        import json
        with open(zh_file, 'r', encoding='utf-8') as f:
            zh_data = json.load(f)
        with open(pending_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
            
        # 深度合并或简单合并取决于结构
        # 这里仅合并顶层键值对，符合 compare_keys 的逻辑
        zh_data.update(new_data)
        
        with open(zh_file, 'w', encoding='utf-8') as f:
            json.dump(zh_data, f, ensure_ascii=False, indent=2)
            
        # 最后对 zh.json 进行美化排序
        format_script = os.path.join(TOOLS_DIR, 'format_json.py')
        run_command([sys.executable, format_script, zh_file])
        
        print("✅ 合并成功! lang/zh.json 已更新。")
    except Exception as e:
        print(f"❌ 合并失败: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Figma 语言包本地化管理工具")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--compare", action="store_true", help="对比差异并准备待翻译文件")
    group.add_argument("--merge", action="store_true", help="将翻译后的文件合入主语言包")
    
    args = parser.parse_args()
    
    if args.compare:
        compare_mode()
    elif args.merge:
        merge_mode()
