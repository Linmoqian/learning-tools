# 批量替换线代为线性代数，大物为大学物理
import os
from pathlib import Path

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
processed = 0
modified = 0

replacements = {
    "线代": "线性代数",
    "大物": "大学物理"
}

for md_file in notes_path.rglob("*.md"):
    try:
        content = md_file.read_text(encoding="utf-8")
        original = content
        
        # 执行替换
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        if content != original:
            md_file.write_text(content, encoding="utf-8")
            modified += 1
            print(f"已修改: {md_file.name}")
        
        processed += 1
    except Exception as e:
        print(f"处理失败: {md_file} - {e}")

print("\n" + "=" * 50)
print(f"处理完成: 共扫描 {processed} 个文件，修改 {modified} 个文件")