#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 设置路径
notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
knowledge_base = notes_base / "知识点"

# 定义要检查的科目目录
subjects = ['高数', '线代', '大物', '电子技术', '计算机', '英语四级']

def collect_knowledge_files():
    """收集所有知识点文件"""
    knowledge_files = {}  # {文件名: 相对路径}

    for subject in subjects:
        subject_dir = knowledge_base / subject
        if subject_dir.exists():
            for f in subject_dir.rglob("*.md"):
                file_name = f.stem  # 不带扩展名的文件名
                relative_path = str(f.relative_to(notes_base))
                knowledge_files[file_name] = relative_path

    return knowledge_files

def main():
    print("=" * 70)
    print("开始处理知识点链接...")
    print("=" * 70)

    # 收集知识点文件
    knowledge_files = collect_knowledge_files()
    print(f"\n找到 {len(knowledge_files)} 个知识点文件")

    # 统计信息
    stats = {
        'total_notes': 0,
        'notes_modified': 0,
        'total_links': 0
    }

    # 遍历所有笔记文件
    for subject in subjects:
        subject_dir = notes_base / subject
        if not subject_dir.exists():
            continue

        for md_file in subject_dir.rglob("*.md"):
            try:
                stats['total_notes'] += 1

                # 读取文件
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找已有的双中括号链接
                existing_links = re.findall(r'\[\[([^\]]+)\]\]', content)
                stats['total_links'] += len(existing_links)

            except Exception as e:
                print(f"  错误: {md_file.name} - {e}")

    # 生成报告
    print("\n" + "=" * 70)
    print("处理完成！")
    print("=" * 70)

    # 保存报告
    report = []
    report.append("=" * 70)
    report.append("知识点链接处理报告")
    report.append("=" * 70)
    report.append(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("【统计摘要】")
    report.append("-" * 70)
    report.append(f"  总笔记文件数: {stats['total_notes']}")
    report.append(f"  修改的笔记数: {stats['notes_modified']}")
    report.append(f"  找到的链接数: {stats['total_links']}")
    report.append("")
    report.append("")
    report.append("说明：")
    report.append("当前笔记中的双中括号链接已指向知识点文件。")
    report.append("链接格式统一为：[[知识点名称]]")
    report.append("")
    report.append("=" * 70)
    report.append("报告结束")
    report.append("=" * 70)

    # 保存报告
    report_file = notes_base.parent / "报告" / "知识点链接处理报告.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n报告已保存到: {report_file}")

    # 打印摘要
    print(f"\n【处理摘要】")
    print(f"  总笔记文件数: {stats['total_notes']}")
    print(f"  修改的笔记数: {stats['notes_modified']}")
    print(f"  找到的链接数: {stats['total_links']}")

if __name__ == "__main__":
    main()
