#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

# UTF-8 BOM 字节序列
BOM = b'\xef\xbb\xbf'

total_files = 0
fixed_files = 0
total_bom_removed = 0

# 遍历所有 markdown 文件
for md_file in notes_base.rglob("*.md"):
    total_files += 1
    try:
        # 读取文件为二进制
        with open(md_file, 'rb') as f:
            content = f.read()

        # 检查是否有 BOM
        if content.startswith(BOM):
            # 移除 BOM
            new_content = content[len(BOM):]

            # 写回文件（无 BOM）
            with open(md_file, 'wb') as f:
                f.write(new_content)

            fixed_files += 1
            total_bom_removed += 1

            if fixed_files % 100 == 0:
                print(f"已修复 {fixed_files} 个文件...")

    except Exception as e:
        print(f"跳过 {md_file}: {e}")

print(f"\n完成！")
print(f"总计扫描 {total_files} 个文件")
print(f"修复了 {fixed_files} 个含 BOM 的文件")
print(f"移除了 {total_bom_removed} 个 BOM 字符")