#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
import re

notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

# 收集所有知识点文件名（不含扩展名）
knowledge_files = set()
for md_file in notes_base.rglob("知识点/**/*.md"):
    knowledge_files.add(md_file.stem)

print(f"已识别知识点文件数: {len(knowledge_files)}")

# 记录缺失的知识点
missing_knowledge = {}

# 遍历所有笔记文件（不包括知识点目录）
for md_file in notes_base.rglob("*.md"):
    if "知识点" in str(md_file.parent):
        continue
    
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 匹配所有双向链接 [[链接]]
        link_pattern = re.compile(r'\[\[([^\[\]]+)\]\]')
        links = link_pattern.findall(content)
        
        for link in links:
            # 处理别名格式 [[目标|显示]]
            if '|' in link:
                target = link.split('|')[0]
            else:
                target = link
            
            # 检查是否在知识点文件中存在
            if target not in knowledge_files:
                # 记录缺失的知识点
                if target not in missing_knowledge:
                    missing_knowledge[target] = []
                missing_knowledge[target].append(str(md_file))
    
    except Exception as e:
        print(f"处理 {md_file} 时出错: {e}")

# 生成缺失清单报告
report = "="*70 + "\n"
report += "知识点缺失清单\n"
report += "="*70 + "\n"
report += f"统计时间: 2026-05-29\n"
report += f"总笔记文件数: {len(list(notes_base.rglob('*.md'))) - len(list(notes_base.rglob('知识点/**/*.md')))}\n"
report += f"知识点文件数: {len(knowledge_files)}\n"
report += f"缺失知识点数: {len(missing_knowledge)}\n"
report += "="*70 + "\n\n"

if missing_knowledge:
    # 按引用次数排序
    sorted_missing = sorted(missing_knowledge.items(), key=lambda x: len(x[1]), reverse=True)
    
    for idx, (knowledge, files) in enumerate(sorted_missing, 1):
        report += f"{idx}. [[{knowledge}]]\n"
        report += f"   引用次数: {len(files)}次\n"
        report += f"   引用位置:\n"
        for file_path in files[:3]:  # 最多显示3个引用位置
            report += f"     - {file_path}\n"
        if len(files) > 3:
            report += f"     ... 还有 {len(files) - 3} 处引用\n"
        report += "\n"
else:
    report += "✅ 所有链接都指向存在的知识点文件！\n"

report += "="*70 + "\n"
report += "说明：仅统计笔记文件中的知识点链接缺失，不检查知识点文件内部的链接\n"

# 保存报告
report_path = notes_base.parent / "缺失知识点清单.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n完成！")
print(f"知识点文件数: {len(knowledge_files)}")
print(f"缺失知识点数: {len(missing_knowledge)}")
print(f"报告已保存到: {report_path}")