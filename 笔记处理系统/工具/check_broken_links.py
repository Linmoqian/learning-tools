import os
import re
from pathlib import Path
from collections import defaultdict

# 设置路径
base_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
notes_dir = base_path  # 笔记根目录
knowledge_dir = base_path / "知识点"  # 知识点目录

# 收集所有知识点文件（按科目分类）
def collect_knowledge_files():
    knowledge_files = defaultdict(set)

    if not knowledge_dir.exists():
        print(f"知识点目录不存在: {knowledge_dir}")
        return knowledge_files

    for subject_dir in knowledge_dir.iterdir():
        if subject_dir.is_dir():
            subject = subject_dir.name
            for md_file in subject_dir.rglob("*.md"):
                # 去掉.md后缀，保留文件名
                file_name = md_file.stem
                knowledge_files[subject].add(file_name)
                # 也添加完整路径的相对形式
                rel_path = md_file.relative_to(knowledge_dir)
                knowledge_files['all'].add(str(rel_path))

    return knowledge_files

# 从笔记文件中提取超链接
def extract_links(note_file):
    links = set()

    try:
        with open(note_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取 [[...]] 格式的链接
        pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(pattern, content)

        for match in matches:
            # 处理链接中的路径分隔符
            link = match.strip()
            links.add(link)
    except Exception as e:
        print(f"读取文件失败 {note_file}: {e}")

    return links

# 检查链接是否存在
def check_link_exists(link, knowledge_files):
    # 直接文件名（去掉.md）
    file_name = link

    # 检查是否是完整路径
    if '/' in link or '\\' in link:
        # 可能是路径形式
        path_form = link.replace('\\', '/')
        # 尝试不同的扩展名
        for ext in ['', '.md']:
            test_path = knowledge_dir / (path_form + ext)
            if test_path.exists():
                return True
            # 也检查相对于知识点目录的情况
            for subject in ['高数', '线代', '大物', '电子技术', '计算机', '英语四级']:
                test_path2 = knowledge_dir / subject / (path_form + ext)
                if test_path2.exists():
                    return True

    # 直接文件名匹配（不区分大小写）
    link_lower = file_name.lower()

    for subject in knowledge_files:
        if subject == 'all':
            continue
        for kf in knowledge_files[subject]:
            if kf.lower() == link_lower:
                return True

    return False

def main():
    # 设置输出编码为UTF-8
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("=" * 60)
    print("开始检查笔记中的超链接...")
    print("=" * 60)

    # 收集知识点文件
    print("\n[1/4] 收集知识点文件...")
    knowledge_files = collect_knowledge_files()

    total_knowledge = sum(len(files) for subject, files in knowledge_files.items() if subject != 'all')
    print(f"找到 {total_knowledge} 个知识点文件")
    for subject, files in knowledge_files.items():
        if subject != 'all':
            print(f"  - {subject}: {len(files)} 个文件")

    # 定义要检查的科目目录
    subjects = ['高数', '线代', '大物', '电子技术', '计算机', '英语四级']

    all_notes = []
    for subject in subjects:
        subject_dir = notes_dir / subject
        if subject_dir.exists():
            for md_file in subject_dir.rglob("*.md"):
                all_notes.append(md_file)

    print(f"\n[2/4] 扫描 {len(all_notes)} 个笔记文件...")

    # 收集所有超链接和缺失文件
    all_links = defaultdict(list)  # 链接 -> [(笔记文件, 具体位置)]
    missing_files = defaultdict(list)  # 缺失文件 -> [(笔记文件, 链接文本)]

    for note_file in all_notes:
        links = extract_links(note_file)

        for link in links:
            exists = check_link_exists(link, knowledge_files)

            if not exists:
                # 尝试查找最接近的匹配
                best_match = None
                link_lower = link.lower()

                for subject, files in knowledge_files.items():
                    if subject == 'all':
                        continue
                    for kf in files:
                        # 计算相似度
                        kf_lower = kf.lower()
                        if link_lower in kf_lower or kf_lower in link_lower:
                            best_match = kf
                            break
                    if best_match:
                        break

                missing_files[link].append({
                    'note': note_file.relative_to(notes_dir),
                    'suggestion': best_match
                })

    print(f"\n[3/4] 检查完成，发现 {len(missing_files)} 个缺失的知识点链接")

    # 生成报告
    print("\n[4/4] 生成报告...")
    print("=" * 60)
    print("缺失知识点清单")
    print("=" * 60)

    if not missing_files:
        print("\n✓ 所有超链接都指向存在的知识点文件！")
    else:
        # 按科目分类显示
        categorized = defaultdict(list)

        for link, occurrences in sorted(missing_files.items()):
            # 统计来自哪些笔记
            notes = [occ['note'] for occ in occurrences]
            suggestion = occurrences[0]['suggestion']

            # 尝试判断科目
            subject = "未知"
            for s in subjects:
                if any(s in str(n) for n in notes):
                    subject = s
                    break

            categorized[subject].append({
                'link': link,
                'count': len(occurrences),
                'notes': notes,
                'suggestion': suggestion
            })

        total_missing = 0
        for subject in sorted(categorized.keys()):
            items = categorized[subject]
            total_missing += len(items)
            print(f"\n【{subject}】- {len(items)} 处缺失")
            print("-" * 60)

            for item in sorted(items, key=lambda x: x['link']):
                print(f"\n  >> {item['link']}")
                print(f"     出现次数: {item['count']}")
                print(f"     涉及笔记: {', '.join(str(n) for n in item['notes'][:3])}")
                if item['notes'] and len(item['notes']) > 3:
                    print(f"               ... 还有 {len(item['notes']) - 3} 个文件")
                if item['suggestion']:
                    print(f"     提示: 可能对应 {item['suggestion']}")

        print("\n" + "=" * 60)
        print(f"总计: {len(missing_files)} 个不同的缺失链接")
        print(f"      {total_missing} 次出现")

        # 计算涉及的笔记文件数量
        involved_notes = set()
        for occurrences in missing_files.values():
            for occ in occurrences:
                involved_notes.add(str(occ['note']))
        print(f"      涉及 {len(involved_notes)} 个笔记文件")

    # 保存到文件
    report_file = base_path / "缺失知识点清单.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("缺失知识点清单\n")
        f.write("=" * 60 + "\n")
        f.write(f"检查时间: 自动生成\n")
        f.write(f"知识点总数: {total_knowledge}\n")
        f.write(f"笔记总数: {len(all_notes)}\n")
        f.write(f"缺失链接数: {len(missing_files)}\n\n")

        if missing_files:
            categorized = defaultdict(list)
            for link, occurrences in sorted(missing_files.items()):
                notes = [occ['note'] for occ in occurrences]
                suggestion = occurrences[0]['suggestion']

                subject = "未知"
                for s in subjects:
                    if any(s in str(n) for n in notes):
                        subject = s
                        break

                categorized[subject].append({
                    'link': link,
                    'count': len(occurrences),
                    'notes': notes,
                    'suggestion': suggestion
                })

            for subject in sorted(categorized.keys()):
                items = categorized[subject]
                f.write(f"\n【{subject}】- {len(items)} 处缺失\n")
                f.write("-" * 60 + "\n")

                for item in sorted(items, key=lambda x: x['link']):
                    f.write(f"\n  {item['link']}\n")
                    f.write(f"    出现次数: {item['count']}\n")
                    f.write(f"    涉及笔记: {', '.join(str(n) for n in item['notes'][:3])}")
                    if len(item['notes']) > 3:
                        f.write(f" ... 还有 {len(item['notes']) - 3} 个文件")
                    f.write("\n")
                    if item['suggestion']:
                        f.write(f"    可能对应: {item['suggestion']}\n")

    print(f"\n报告已保存到: {report_file}")

if __name__ == "__main__":
    main()
