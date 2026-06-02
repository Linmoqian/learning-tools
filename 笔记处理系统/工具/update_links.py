#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

# 定义链接替换规则
replace_rules = [
    ("[[线性相关]]", "[[线性相关与线性无关]]"),
    ("[[线性相关性]]", "[[线性相关与线性无关]]"),
    ("[[线性相关与无关定义]]", "[[线性相关与线性无关]]"),
    ("[[线性相关与无关判定]]", "[[线性相关与线性无关]]"),
    ("[[线性无关]]", "[[函数线性无关]]"),
]

updated_count = 0
total_files = 0

for md_file in notes_base.rglob("*.md"):
    total_files += 1
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
        print(f"跳过 {md_file}: {e}")

print(f"\n完成！共扫描 {total_files} 个文件，更新了 {updated_count} 个文件")