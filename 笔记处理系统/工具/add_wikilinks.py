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

def read_file_safe(file_path):
    """安全读取文件"""
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read(), encoding
        except:
            continue
    return None, None

def find_keyword_in_text(keyword, text, max_count=3):
    """在文本中查找关键词"""
    # 清理关键词（去掉常见前缀）
    clean_keyword = keyword
    for prefix in ['高数-', '线代-', '大物-', '电子技术-', '计算机-', '英语四级-']:
        if clean_keyword.startswith(prefix):
            clean_keyword = clean_keyword[len(prefix):]
            break

    # 转义特殊字符用于正则
    escaped_keyword = re.escape(clean_keyword)

    # 查找关键词（不区分大小写）
    pattern = re.compile(escaped_keyword, re.IGNORECASE)
    matches = list(pattern.finditer(text))

    return matches[:max_count]

def add_wikilinks(content, note_file, knowledge_files):
    """为内容添加双中括号链接"""
    lines = content.split('\n')
    modified_lines = []
    added_links = []

    for line in lines:
        new_line = line

        # 检查每行是否已有链接
        if '[[' in new_line or '](' in new_line:
            modified_lines.append(new_line)
            continue

        # 尝试匹配知识点
        for knowledge_name, knowledge_path in knowledge_files.items():
            # 清理知识点名称
            clean_knowledge = knowledge_name
            for prefix in ['高数-', '线代-', '大物-', '电子技术-', '计算机-', '英语四级-']:
                if clean_knowledge.startswith(prefix):
                    clean_knowledge = clean_knowledge[len(prefix):]
                    break

            # 跳过太短的关键词
            if len(clean_knowledge) < 2:
                continue

            # 转义特殊字符
            escaped = re.escape(clean_knowledge)

            # 匹配独立的词语（前后有边界）
            pattern = re.compile(rf'\b({escaped})\b', re.IGNORECASE)

            # 检查是否已经链接
            if f'[[{knowledge_name}]]' in new_line or f'[[{clean_knowledge}]]' in new_line:
                continue

            # 替换
            def replace_func(match):
                matched_text = match.group(1)
                # 如果匹配的是知识点名称的一部分，保持原样
                if matched_text.lower() == knowledge_name.lower() or matched_text.lower() == clean_knowledge.lower():
                    return f'[[{knowledge_name}]]'
                return f'[[{knowledge_name}]]'

            new_line = pattern.sub(replace_func, new_line)

        modified_lines.append(new_line)

    return '\n'.join(modified_lines)

def main():
    print("=" * 70)
    print("开始为笔记添加知识点双中括号链接...")
    print("=" * 70)

    # 收集知识点文件
    knowledge_files = collect_knowledge_files()
    print(f"\n找到 {len(knowledge_files)} 个知识点文件")

    # 统计信息
    stats = {
        'total_notes': 0,
        'notes_modified': 0,
        'total_links_added': 0,
        'links_added': defaultdict(int)
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
                content, encoding = read_file_safe(md_file)
                if content is None:
                    print(f"  跳过: {md_file.relative_to(notes_base)} - 无法读取")
                    continue

                # 添加链接
                new_content = add_wikilinks(content, md_file, knowledge_files)

                # 如果内容有变化，保存文件
                if new_content != content:
                    # 计算添加了多少链接
                    new_links = len(re.findall(r'\[\[[^\]]+\]\]', new_content))
                    old_links = len(re.findall(r'\[\[[^\]]+\]\]', content))
                    added_count = new_links - old_links

                    if added_count > 0:
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)

                        stats['notes_modified'] += 1
                        stats['total_links_added'] += added_count

                        # 记录添加的链接
                        new_link_matches = re.findall(r'\[\[([^\]]+)\]\]', new_content)
                        for link in new_link_matches:
                            stats['links_added'][link] += 1

                        print(f"  已添加: {md_file.relative_to(notes_base)} - {added_count} 个链接")

            except Exception as e:
                print(f"  错误: {md_file.name} - {e}")

    # 生成报告
    print("\n" + "=" * 70)
    print("添加完成！")
    print("=" * 70)

    # 保存报告
    report = []
    report.append("=" * 70)
    report.append("知识点双中括号链接添加报告")
    report.append("=" * 70)
    report.append(f"添加时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("【统计摘要】")
    report.append("-" * 70)
    report.append(f"  总笔记文件数: {stats['total_notes']}")
    report.append(f"  修改的笔记数: {stats['notes_modified']}")
    report.append(f"  添加的链接数: {stats['total_links_added']}")
    report.append("")

    if stats['links_added']:
        report.append("")
        report.append("【添加的链接统计】")
        report.append("-" * 70)

        # 按添加次数排序
        sorted_links = sorted(stats['links_added'].items(),
                            key=lambda x: x[1], reverse=True)

        for link, count in sorted_links[:100]:  # 显示前100个
            report.append(f"  [[{link}]] - {count} 次")

        if len(sorted_links) > 100:
            report.append(f"\n... 还有 {len(sorted_links) - 100} 个链接")

    report.append("")
    report.append("=" * 70)
    report.append("报告结束")
    report.append("=" * 70)

    # 保存报告
    report_file = notes_base.parent / "报告" / "知识点链接添加报告.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"\n报告已保存到: {report_file}")

    # 打印摘要
    print(f"\n【添加摘要】")
    print(f"  总笔记文件数: {stats['total_notes']}")
    print(f"  修改的笔记数: {stats['notes_modified']}")
    print(f"  添加的链接数: {stats['total_links_added']}")

if __name__ == "__main__":
    main()
