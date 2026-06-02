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

def collect_files():
    """收集所有知识点文件和笔记文件"""
    knowledge_files = {}  # {文件名: 完整路径}
    note_files = {}       # {文件名: 完整路径}

    # 收集知识点文件
    for subject in subjects:
        subject_dir = knowledge_base / subject
        if subject_dir.exists():
            for f in subject_dir.rglob("*.md"):
                file_name = f.stem  # 不带扩展名的文件名
                knowledge_files[file_name] = str(f)

    # 收集笔记文件
    for subject in subjects:
        subject_dir = notes_base / subject
        if subject_dir.exists():
            for f in subject_dir.rglob("*.md"):
                file_name = f.stem
                note_files[file_name] = str(f)

    return knowledge_files, note_files

def extract_links(content):
    """提取所有 [[...]] 格式的链接"""
    pattern = r'\[\[([^\]]+)\]\]'
    matches = re.findall(pattern, content)
    return matches

def normalize_link(link_text):
    """规范化链接文本"""
    # 去掉别名部分（|后的内容）
    if '|' in link_text:
        link_text = link_text.split('|')[0].strip()

    # 去掉 .md 扩展名
    if link_text.endswith('.md'):
        link_text = link_text[:-3]

    return link_text.strip()

def check_link(link_text, knowledge_files, note_files):
    """检查链接是否存在"""
    normalized = normalize_link(link_text)

    # 首先检查是否指向知识点文件
    if normalized in knowledge_files:
        return True, 'knowledge'

    # 检查是否指向笔记文件
    if normalized in note_files:
        return True, 'note'

    return False, None

def fuzzy_match(suggestion, knowledge_files):
    """模糊匹配可能的对应知识点"""
    suggestion_lower = suggestion.lower()

    # 精确匹配
    if suggestion in knowledge_files:
        return suggestion

    # 模糊匹配
    for key in knowledge_files:
        key_lower = key.lower()
        # 检查关键词匹配
        if (suggestion_lower in key_lower) or (key_lower in suggestion_lower):
            return key

    return None

def main():
    print("=" * 70)
    print("开始检查笔记中的超链接...")
    print("=" * 70)

    # 收集文件
    knowledge_files, note_files = collect_files()
    print(f"\n找到 {len(knowledge_files)} 个知识点文件")
    print(f"找到 {len(note_files)} 个笔记文件")

    # 统计信息
    stats = {
        'total_links': 0,
        'valid_links': 0,
        'missing_links': 0,
        'missing_details': defaultdict(lambda: {'count': 0, 'files': []}),
        'by_subject': defaultdict(lambda: {'total': 0, 'missing': 0})
    }

    # 遍历所有笔记文件
    for subject in subjects:
        subject_dir = notes_base / subject
        if not subject_dir.exists():
            continue

        for md_file in subject_dir.rglob("*.md"):
            try:
                # 使用 UTF-8 编码读取
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 提取链接
                links = extract_links(content)
                stats['by_subject'][subject]['total'] += len(links)

                for link in links:
                    stats['total_links'] += 1
                    normalized = normalize_link(link)

                    # 检查链接是否存在
                    exists, link_type = check_link(normalized, knowledge_files, note_files)

                    if exists:
                        stats['valid_links'] += 1
                    else:
                        stats['missing_links'] += 1
                        stats['by_subject'][subject]['missing'] += 1

                        # 记录缺失的链接
                        stats['missing_details'][normalized]['count'] += 1
                        relative_path = str(md_file.relative_to(notes_base))
                        if relative_path not in stats['missing_details'][normalized]['files']:
                            stats['missing_details'][normalized]['files'].append(relative_path)

            except Exception as e:
                print(f"  错误: {md_file.name} - {e}")

    # 生成报告
    print("\n" + "=" * 70)
    print("检查完成！")
    print("=" * 70)

    # 保存报告
    report = []
    report.append("=" * 70)
    report.append("缺失知识点清单")
    report.append("=" * 70)
    report.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"知识点总数: {len(knowledge_files)}")
    report.append(f"笔记总数: {len(note_files)}")
    report.append(f"缺失链接数: {stats['missing_links']}")
    report.append("")

    # 按科目统计
    for subject in subjects:
        subject_stats = stats['by_subject'][subject]
        if subject_stats['total'] > 0:
            report.append(f"【{subject}】- {subject_stats['missing']} 处缺失")
            report.append("-" * 70)
            report.append("")

            # 找出该科目中缺失的链接
            subject_missing = []
            for link, details in stats['missing_details'].items():
                files = [f for f in details['files'] if subject in f]
                if files:
                    subject_missing.append((link, details['count'], files))

            # 按出现次数排序
            subject_missing.sort(key=lambda x: x[1], reverse=True)

            for link, count, files in subject_missing:
                report.append(f"  {link}")
                report.append(f"    出现次数: {count}")
                for f in files[:5]:
                    report.append(f"    涉及笔记: {f}")
                if len(files) > 5:
                    report.append(f"             ... 还有 {len(files) - 5} 个文件")

                # 尝试模糊匹配
                suggestion = fuzzy_match(link, knowledge_files)
                if suggestion:
                    report.append(f"    可能对应: {suggestion}")

                report.append("")

            report.append("")

    # 统计摘要
    report.append("=" * 70)
    report.append("统计摘要")
    report.append("=" * 70)
    report.append(f"  总链接数: {stats['total_links']}")
    report.append(f"  有效链接: {stats['valid_links']}")
    report.append(f"  缺失链接: {stats['missing_links']}")
    report.append(f"  缺失链接类型数: {len(stats['missing_details'])}")
    report.append("")
    report.append("按科目统计:")
    for subject in subjects:
        subject_stats = stats['by_subject'][subject]
        if subject_stats['total'] > 0:
            report.append(f"  {subject}: {subject_stats['missing']}/{subject_stats['total']} 处缺失")

    # 保存报告
    report_file = notes_base / "缺失知识点清单.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n报告已保存到: {report_file}")

    # 打印摘要
    print(f"\n【检查摘要】")
    print(f"  总链接数: {stats['total_links']}")
    print(f"  有效链接: {stats['valid_links']}")
    print(f"  缺失链接: {stats['missing_links']}")
    print(f"  缺失链接类型数: {len(stats['missing_details'])}")

    print("\n按科目统计:")
    for subject in subjects:
        subject_stats = stats['by_subject'][subject]
        if subject_stats['total'] > 0:
            print(f"  {subject}: {subject_stats['missing']}/{subject_stats['total']} 处缺失")

if __name__ == "__main__":
    main()
