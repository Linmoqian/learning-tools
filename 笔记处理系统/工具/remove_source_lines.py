#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
import re

notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

# 匹配来源行模式
source_pattern = re.compile(r'^>\\s*📖\\s*来源：.*$', re.MULTILINE)

modified_count = 0
total_count = 0

# 遍历所有知识点文件
for md_file in notes_base.rglob("知识点/**/*.md"):
    total_count += 1
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有来源行
        if '📖 来源：' in content:
            # 删除来源行
            new_content = source_pattern.sub('', content)
            # 清理多余空行
            new_content = re.sub(r'\n{3,}', '\n\n', new_content).strip() + '\n'
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            modified_count += 1
            if modified_count % 20 == 0:
                print(f"已处理 {modified_count} 个文件...")
    
    except Exception as e:
        print(f"处理 {md_file} 时出错: {e}")

print(f"\n完成！")
print(f"知识点文件总数: {total_count}")
print(f"修改的文件数: {modified_count}")