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
                knowledge_files[relative_path] = file_name

    return knowledge_files

def extract_markdown_links(content):
    """提取所有 Markdown 链接 [text](path) 格式"""
    pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)'
    matches = re.finditer(pattern, content)
    return [(m.group(0), m.group(1), m.group(2), m.start(), m.end()) for m in matches]

def main():
    print("=" * 70)
    print("开始转换 Markdown 链接为双中括号格式...")
    print("=" * 70)

    # 收集知识点文件
    knowledge_files = collect_knowledge_files()
    print(f"\n找到 {len(knowledge_files)} 个知识点文件")

    # 统计信息
    stats = {
        'total_notes': 0,
        'notes_modified': 0,
        'total_links_converted': 0,
        'conversions': defaultdict(list)
    }

    # 遍历所有笔记文件
    for subject in subjects:
        subject_dir = notes_base / subject
        if not subject_dir.exists():
            continue

        for md_file in subject_dir.rglob("*.md"):
            try:
                stats['total_notes'] += 1

                # 使用 UTF-8 编码读取
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取 Markdown 链接
                links = extract_markdown_links(content)

                if not links:
                    continue

                # 检查并转换链接
                new_content = content
                converted_count = 0
                conversions_in_file = []

                # 从后向前替换，避免位置偏移问题
                for full_match, link_text, path, start, end in reversed(links):
                    # 统一路径分隔符
                    path_normalized = path.replace('\\', '/')

                    # 检查是否指向知识点文件
                    if path_normalized in knowledge_files:
                        # 获取知识点文件名
                        knowledge_name = knowledge_files[path_normalized]

                        # 构建新的双中括号链接
                        new_link = f"[[{knowledge_name}]]"

                        # 替换
                        new_content = new_content[:start] + new_link + new_content[end:]
                        converted_count += 1

                        conversions_in_file.append({
                            'original': full_match,
                            'converted': new_link,
                            'knowledge': knowledge_name
                        })

                # 如果有转换，保存文件
                if converted_count > 0:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    stats['notes_modified'] += 1
                    stats['total_links_converted'] += converted_count

                    for conv in conversions_in_file:
                        stats['conversions'][conv['knowledge']].append(str(md_file.relative_to(notes_base)))

                    print(f"  已转换: {md_file.relative_to(notes_base)} - {converted_count} 个链接")

            except Exception as e:
                print(f"  错误: {md_file.name} - {e}")

    # 生成报告
    print("\n" + "=" * 70)
    print("转换完成！")
    print("=" * 70)

    # 保存报告
    report = []
    report.append("=" * 70)
    report.append("Markdown链接转双中括号报告")
    report.append("=" * 70)
    report.append(f"转换时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("【统计摘要】")
    report.append("-" * 70)
    report.append(f"  总笔记文件数: {stats['total_notes']}")
    report.append(f"  修改的笔记数: {stats['notes_modified']}")
    report.append(f"  转换的链接数: {stats['total_links_converted']}")
    report.append("")

    if stats['conversions']:
        report.append("")
        report.append("【转换详情】")
        report.append("-" * 70)

        # 按转换次数排序
        sorted_conversions = sorted(stats['conversions'].items(),
                                   key=lambda x: len(x[1]), reverse=True)

        for knowledge, files in sorted_conversions[:50]:  # 只显示前50个
            report.append(f"\n知识点: [[{knowledge}]]")
            report.append(f"  转换次数: {len(files)}")
            report.append(f"  涉及文件:")
            for f in files[:3]:
                report.append(f"    - {f}")
            if len(files) > 3:
                report.append(f"    ... 还有 {len(files) - 3} 个文件")

        if len(sorted_conversions) > 50:
            report.append(f"\n... 还有 {len(sorted_conversions) - 50} 个知识点")

    report.append("")
    report.append("=" * 70)
    report.append("报告结束")
    report.append("=" * 70)

    # 保存报告
    report_file = notes_base.parent / "报告" / "Markdown链接转双中括号报告.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n报告已保存到: {report_file}")

    # 打印摘要
    print(f"\n【转换摘要】")
    print(f"  总笔记文件数: {stats['total_notes']}")
    print(f"  修改的笔记数: {stats['notes_modified']}")
    print(f"  转换的链接数: {stats['total_links_converted']}")

if __name__ == "__main__":
    main()
