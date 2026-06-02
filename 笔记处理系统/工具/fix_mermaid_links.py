﻿import re
from pathlib import Path

notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

fixed_files = 0
total_fixes = 0

for md_file in notes_base.rglob("*.md"):
    if "知识点" in str(md_file.parent):
        continue
    
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 匹配 Mermaid 代码块
    mermaid_pattern = re.compile(r"```mermaid\s*(.*?)```", re.DOTALL)
    matches = mermaid_pattern.findall(content)
    
    new_content = content
    file_fixes = 0
    
    for block in matches:
        # 在 Mermaid 块中移除双向链接格式
        fixed_block = re.sub(r"\[\[([^\]]+)\]\]", r"\1", block)
        if fixed_block != block:
            new_content = new_content.replace(block, fixed_block)
            file_fixes += 1
    
    if file_fixes > 0:
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        fixed_files += 1
        total_fixes += file_fixes
    
print(f"修复了 {fixed_files} 个文件中的 {total_fixes} 处 Mermaid 链接")
