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
    knowledge_files = {}  # {文件名: 完整路径}

    for subject in subjects:
        subject_dir = knowledge_base / subject
        if subject_dir.exists():
            for f in subject_dir.rglob("*.md"):
                file_name = f.stem  # 不带扩展名的文件名
                knowledge_files[file_name] = str(f)

    return knowledge_files

def main():
    print("=" * 70)
    print("开始验证双中括号链接...")
    print("=" * 70)

    # 收集知识点文件
    knowledge_files = collect_knowledge_files()
    print(f"\n找到 {len(knowledge_files)} 个知识点文件")

    # 统计信息
    stats = {
        'total_links': 0,
        'valid_links': 0,
        'invalid_links': 0,
        'link_details': defaultdict(lambda: {'count': 0, 'files': []})
    }

    # 遍历所有笔记文件
    for subject in subjects:
        subject_dir = notes_base / subject
        if not subject_dir.exists():
            continue

        for md_file in subject_dir.rglob("*.md"):
            try:
                # 读取文件
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 查找双中括号链接
                links = re.findall(r'\[\[([^\]]+)\]\]', content)

                for link in links:
                    stats['total_links'] += 1

                    # 检查链接是否指向知识点文件
                    if link in knowledge_files:
                        stats['valid_links'] += 1
                    else:
                        stats['invalid_links'] += 1
                        stats['link_details'][link]['count'] += 1
                        stats['link_details'][link]['files'].append(str(md_file.relative_to(notes_base)))

            except Exception as e:
                print(f"  错误: {md_file.name} - {e}")

    # 生成报告
    print("\n" + "=" * 70)
    print("验证完成！")
    print("=" * 70)

    # 保存报告
    report = []
    report.append("=" * 70)
    report.append("双中括号链接验证报告")
    report.append("=" * 70)
    report.append(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"知识点文件总数: {len(knowledge_files)}")
    report.append("")
    report.append("【统计摘要】")
    report.append("-" * 70)
    report.append(f"  总链接数: {stats['total_links']}")
    report.append(f"  有效链接: {stats['valid_links']}")
    report.append(f"  无效链接: {stats['invalid_links']}")
    report.append(f"  无效链接类型数: {len(stats['link_details'])}")
    report.append("")

    if stats['invalid_links'] > 0:
        report.append("")
        report.append("【无效链接详情】")
        report.append("-" * 70)

        # 按出现次数排序
        sorted_invalid = sorted(stats['link_details'].items(),
                               key=lambda x: x[1]['count'], reverse=True)

        for link, details in sorted_invalid[:100]:  # 显示前100个
            report.append(f"\n  [[{link}]]")
            report.append(f"    出现次数: {details['count']}")
            for f in details['files'][:5]:
                report.append(f"    涉及笔记: {f}")
            if len(details['files']) > 5:
                report.append(f"             ... 还有 {len(details['files']) - 5} 个文件")

            # 尝试模糊匹配
            for kf in knowledge_files:
                if link in kf or kf in link:
                    report.append(f"    可能对应: [[{kf}]]")
                    break

    report.append("")
    report.append("=" * 70)
    report.append("报告结束")
    report.append("=" * 70)

    # 保存报告
    report_file = notes_base.parent / "报告" / "双中括号链接验证报告.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n报告已保存到: {report_file}")

    # 打印摘要
    print(f"\n【验证摘要】")
    print(f"  总链接数: {stats['total_links']}")
    print(f"  有效链接: {stats['valid_links']} ({stats['valid_links']/stats['total_links']*100:.1f}%)")
    print(f"  无效链接: {stats['invalid_links']} ({stats['invalid_links']/stats['total_links']*100:.1f}%)")

if __name__ == "__main__":
    main()
