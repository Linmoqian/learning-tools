# 综合替换脚本：高数→高等数学，以及去除来源行
import os
import re
from pathlib import Path

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
processed = 0
modified = 0

# 第一步：文件内容替换
print("=== 第一步：文件内容替换 ===")
replacements = {
    "高数": "高等数学",
    "线代": "线性代数",
    "大物": "大学物理"
}

for md_file in notes_path.rglob("*.md"):
    try:
        content = md_file.read_text(encoding="utf-8")
        original = content
        
        # 执行文本替换
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # 去除来源行：格式为 "> 📖 来源：[[...]]" 或类似
        # 使用正则移除来源行
        # 匹配 "> 📖 来源：..." 或 "> 📖 来源：[[...]]" 这样的行
        content = re.sub(r'^>\s*📖\s*来源：.*$', '', content, flags=re.MULTILINE)
        # 也匹配类似的来源行格式
        content = re.sub(r'^>\s*来源：.*$', '', content, flags=re.MULTILINE)
        
        # 清理多余空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        if content != original:
            md_file.write_text(content, encoding="utf-8")
            modified += 1
            print(f"已修改: {md_file.relative_to(notes_path)}")
        
        processed += 1
    except Exception as e:
        print(f"处理失败: {md_file} - {e}")

print(f"\n内容替换完成: 共扫描 {processed} 个文件，修改 {modified} 个文件\n")

# 第二步：重命名文件
print("=== 第二步：重命名文件 ===")
processed = 0
renamed = 0

replacements = {
    "高数": "高等数学",
    "线代": "线性代数",
    "大物": "大学物理"
}

files_to_rename = []
for root, dirs, files in os.walk(notes_path):
    for filename in files:
        if ".md" in filename:
            new_name = filename
            for old, new in replacements.items():
                new_name = new_name.replace(old, new)
            if new_name != filename:
                old_path = Path(root) / filename
                new_path = Path(root) / new_name
                files_to_rename.append((old_path, new_path))

for old_path, new_path in files_to_rename:
    try:
        old_path.rename(new_path)
        renamed += 1
        print(f"已重命名: {old_path.relative_to(notes_path)} -> {new_path.relative_to(notes_path)}")
        processed += 1
    except Exception as e:
        print(f"重命名失败: {old_path} - {e}")
        processed += 1

print(f"\n文件重命名完成: 共检查 {len(files_to_rename)} 个文件，重命名 {renamed} 个文件\n")

# 第三步：重命名文件夹
print("=== 第三步：重命名文件夹 ===")
processed = 0
renamed = 0

# 从深到浅重命名文件夹，避免路径问题
dirs_to_rename = []
for root, dirs, files in os.walk(notes_path, topdown=False):
    for dirname in dirs:
        new_name = dirname
        for old, new in replacements.items():
            new_name = new_name.replace(old, new)
        if new_name != dirname:
            old_dir = Path(root) / dirname
            new_dir = Path(root) / new_name
            dirs_to_rename.append((old_dir, new_dir))

for old_dir, new_dir in dirs_to_rename:
    try:
        old_dir.rename(new_dir)
        renamed += 1
        print(f"已重命名: {old_dir.relative_to(notes_path)} -> {new_dir.relative_to(notes_path)}")
        processed += 1
    except Exception as e:
        print(f"重命名失败: {old_dir} - {e}")
        processed += 1

print("\n" + "=" * 60)
print(f"全部完成：\n  - 内容替换: {modified} 个文件\n  - 文件重命名: {renamed} 个\n  - 文件夹重命名: {processed} 个")