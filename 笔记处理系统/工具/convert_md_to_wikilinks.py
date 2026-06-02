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
    print("开始转换 Markdown 链接为双中括号格式...")
    print("=" * 70)

    # 收集知识点文件
    knowledge_files = collect_knowledge_files()
    print(f"\n找到 {len(knowledge_files)} 个知识点文件")

    # 统计信息
    stats = {
        'total_notes': 0,
        'notes_modified': 0,
        'total_links_found': 0,
        'converted_count': 0
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

                # 直接查找所有 Markdown 链接
                pattern = r'(\[([^\]]+)\]\(([^)]+\.md)\))'
                matches = list(re.finditer(pattern, content))

                if not matches:
                    continue

                stats['total_links_found'] += len(matches)

                # 统计指向知识点的链接
                knowledge_links = []
                for match in matches:
                    full_match = match.group(1)
                    display_text = match.group(2)
                    path = match.group(3)

                    # 检查是否指向知识点
                    if '../知识点/' in path:
                        # 从路径提取知识点名称
                        path_match = re.search(r'知识点/[^\/]+/(.+)\.md$', path)
                        if path_match:
                            knowledge_name = path_match.group(1)
                            knowledge_links.append({
                                'full': full_match,
                                'display': display_text,
                                'path': path,
                                'name': knowledge_name,
                                'start': match.start(),
                                'end': match.end()
                            })

                if not knowledge_links:
                    continue

                print(f"  发现: {md_file.relative_to(notes_base)} - {len(knowledge_links)} 个链接")

                # 转换链接
                new_content = content
                converted = 0

                for link in reversed(knowledge_links):
                    # 检查知识点是否存在
                    if link['name'] in knowledge_files:
                        new_link = f"[[{link['name']}]]"
                        new_content = new_content[:link['start']] + new_link + new_content[link['end']:]
                        converted += 1
                    else:
                        print(f"    警告: 知识点不存在: {link['name']}")

                stats['converted_count'] += converted

                # 保存文件
                if converted > 0:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    stats['notes_modified'] += 1
                    print(f"    已转换: {converted} 个链接")

            except Exception as e:
                print(f"  错误: {md_file.name} - {e}")
                import traceback
                traceback.print_exc()

    # 生成报告
    print("\n" + "=" * 70)
    print("转换完成！")
    print("=" * 70)

    # 保存报告
    report = []
    report.append("=" * 70)
    report.append("Markdown链接转双中括号格式报告")
    report.append("=" * 70)
    report.append(f"转换时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("【统计摘要】")
    report.append("-" * 70)
    report.append(f"  总笔记文件数: {stats['total_notes']}")
    report.append(f"  修改的笔记数: {stats['notes_modified']}")
    report.append(f"  找到的Markdown链接: {stats['total_links_found']}")
    report.append(f"  成功转换: {stats['converted_count']}")
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
    print(f"  成功转换: {stats['converted_count']} 个链接")

if __name__ == "__main__":
    main()
