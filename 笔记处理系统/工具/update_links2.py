#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

# 定义链接替换规则
replace_rules = [
    ("[[线性方程组求解]]", "[[线性方程组]]"),
    ("[[线性方程组解的结构]]", "[[线性方程组]]"),
    ("[[非齐次线性方程组]]", "[[线性方程组]]"),
    ("[[齐次线性方程组]]", "[[线性方程组]]"),
    ("[[齐次线性方程组解空间]]", "[[线性方程组]]"),
    ("[[齐次线性]]", "[[线性方程组]]"),
]

updated_count = 0

for md_file in notes_base.rglob("*.md"):
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        has_changes = False
        for old_link, new_link in replace_rules:
            if old_link in content:
                content = content.replace(old_link, new_link)
                has_changes = True
        
        if has_changes:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_count += 1
            if updated_count % 20 == 0:
                print(f"已更新 {updated_count} 个文件...")
                
    except Exception as e:
        pass

print(f"\n完成！共更新了 {updated_count} 个文件")