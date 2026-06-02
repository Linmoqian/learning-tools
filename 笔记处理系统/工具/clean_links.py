#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
import re

notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

# 收集所有知识点文件名（不含扩展名）
knowledge_files = set()
for md_file in notes_base.rglob("知识点/**/*.md"):
    knowledge_files.add(md_file.stem)

# 收集所有笔记文件名（不含扩展名，用于排除）
note_files = set()
for md_file in notes_base.rglob("*.md"):
    if "知识点" not in str(md_file.parent):
        note_files.add(md_file.stem)

# 统计数据
total_files = 0
modified_files = 0
removed_links = 0
kept_links = 0
file_reports = []

# 遍历所有笔记文件（不包括知识点）
for md_file in notes_base.rglob("*.md"):
    if "知识点" in str(md_file.parent):
        continue
    
    total_files += 1
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配所有双向链接 [[链接]] 或 [[链接|显示文本]]
        link_pattern = re.compile(r'\[\[([^\[\]]+)\]\]')
        links = link_pattern.findall(content)
        
        if not links:
            continue
        
        file_report = {
            'file': str(md_file),
            'removed': [],
            'kept': []
        }
        
        new_content = content
        for link in links:
            # 处理别名格式 [[目标|显示]]
            if '|' in link:
                target = link.split('|')[0]
                display = link.split('|')[1]
            else:
                target = link
                display = link
            
            # 判断是笔记还是知识点
            if target in note_files:
                # 指向笔记的链接，删除（替换为空）
                new_content = new_content.replace(f'[[{link}]]', '')
                removed_links += 1
                file_report['removed'].append(link)
            elif target in knowledge_files:
                # 指向知识点的链接，保持[[xxx]]格式
                # 如果是别名格式，转换为纯链接格式
                if '|' in link:
                    new_content = new_content.replace(f'[[{link}]]', f'[[{target}]]')
                kept_links += 1
                file_report['kept'].append(link)
            else:
                # 指向不存在的文件，保持不变
                if '|' in link:
                    new_content = new_content.replace(f'[[{link}]]', f'[[{target}]]')
                kept_links += 1
                file_report['kept'].append(link)
        
        # 清理多余空行
        new_content = re.sub(r'\n{3,}', '\n\n', new_content).strip() + '\n'
        
        if new_content != content:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            modified_files += 1
            file_reports.append(file_report)
            
            if modified_files % 20 == 0:
                print(f"已处理 {modified_files} 个文件...")
    
    except Exception as e:
        print(f"处理 {md_file} 时出错: {e}")

# 生成报告
report = "="*60 + "\n"
report += "笔记双向链接清理报告\n"
report += "="*60 + "\n"
report += "统计时间: 2026-05-29\n"
report += "="*60 + "\n\n"

report += "【总体统计】\n"
report += f"  笔记文件总数: {total_files}\n"
report += f"  修改的文件数: {modified_files}\n"
report += f"  移除的链接数: {removed_links}\n"
report += f"  保留的链接数: {kept_links}\n\n"

report += "="*60 + "\n\n"
report += "【详细清理记录】\n"

for report_item in file_reports:
    report += f"\n文件: {report_item['file']}\n"
    if report_item['removed']:
        report += "  移除的链接:\n"
        for link in report_item['removed']:
            report += f"    - {link}\n"
    if report_item['kept']:
        report += "  保留的链接:\n"
        for link in report_item['kept']:
            report += f"    - {link}\n"

report += "\n" + "="*60 + "\n"
report += "清理完成！\n"

# 保存报告
report_path = notes_base.parent / "报告" / "双向链接清理报告.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n完成！")
print(f"笔记文件总数: {total_files}")
print(f"修改的文件数: {modified_files}")
print(f"移除的链接数: {removed_links}")
print(f"保留的链接数: {kept_links}")
print(f"报告已保存到: {report_path}")