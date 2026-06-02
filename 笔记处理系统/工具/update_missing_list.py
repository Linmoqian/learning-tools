# Update missing knowledge points list
# Compare [[links]] in notes with actual knowledge point files
# Filter out note titles and chapter names

import re
from pathlib import Path

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
report_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\报告")
kp_base = notes_path / "知识点"

# Step 1: Collect all knowledge point files
knowledge_points = set()

if kp_base.exists():
    for subdir in kp_base.iterdir():
        if subdir.is_dir():
            for kp_file in subdir.glob("*.md"):
                name = kp_file.stem
                knowledge_points.add(name)

print(f"Found {len(knowledge_points)} knowledge points")

# Step 2: Collect all [[links]] from notes (exclude 知识点 folder itself)
note_links = set()
note_titles = set()  # Track note file titles
for md_file in notes_path.rglob("*.md"):
    # Skip 知识点 folder and its subdirectories
    if '知识点' in str(md_file) or '归档' in str(md_file) or '备份' in str(md_file):
        continue

    try:
        content = md_file.read_text(encoding='utf-8')

        # Track note titles (first H1 heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            note_titles.add(title_match.group(1).strip())

        # Find all [[...]] links
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        for link in links:
            note_links.add(link.strip())
    except:
        pass

print(f"Found {len(note_links)} unique links in notes")
print(f"Found {len(note_titles)} note titles")

# Step 3: Filter patterns - items that are NOT knowledge points
def is_not_knowledge_point(item):
    # Skip if it's a note title
    if item in note_titles:
        return True

    # Skip if it starts with digit followed by underscore (note file pattern like "01_xxx")
    if re.match(r'^\d+[_-]', item):
        return True

    # Skip if it starts with digit followed by dash (note file pattern like "01-xxx")
    if re.match(r'^\d+-', item):
        return True

    # Skip CET4/ CET- patterns (note file patterns like "01CET4-xxx")
    if re.match(r'^\d+(?:CET[三四级]|四级)-', item, re.IGNORECASE):
        return True

    # Skip patterns like "01CET4-阅读" (digit + CET + dash + Chinese)
    if re.match(r'^\d+CET', item):
        return True

    # Skip CET4-xxx patterns (CET4 followed by hyphen and Chinese)
    if re.match(r'^CET4-', item, re.IGNORECASE):
        return True

    # Skip CET-xxx patterns
    if re.match(r'^CET-\d', item, re.IGNORECASE):
        return True

    # Skip CET4x patterns (e.g., CET4-写作)
    if re.match(r'^CET4\d', item, re.IGNORECASE):
        return True

    # Skip section symbols (like §1.1, §2)
    if re.match(r'^§\d+', item):
        return True

    # Skip obvious non-knowledge patterns
    if item in ['分析方法', '句子结构分析', '书信格式', '一个让你怀疑 C 语言的例子']:
        return True

    return False

# Step 4: Find missing knowledge points (filtered)
missing = []
for link in sorted(note_links):
    if link not in knowledge_points and not is_not_knowledge_point(link):
        missing.append(link)

missing.sort()
print(f"Found {len(missing)} missing knowledge points (after filtering)")

# Step 5: Generate report
report = f"""# 缺失知识点清单

> 生成时间: 自动更新

## 统计信息

- 知识点文件总数: {len(knowledge_points)}
- 笔记中链接总数: {len(note_links)}
- 缺失知识点数量: {len(missing)}

## 缺失知识点列表

按字母/拼音排序:

"""

for item in missing:
    report += f"- [[{item}]]\n"

# Save report
report_file = report_path / "缺失知识点清单.txt"
report_file.write_text(report, encoding='utf-8')
print(f"Report saved to: {report_file}")

# Print summary
print()
print("=" * 50)
print(f"Total knowledge points: {len(knowledge_points)}")
print(f"Total links in notes: {len(note_links)}")
print(f"Missing knowledge points: {len(missing)}")
print()
print("All missing points:")
for item in missing:
    print(f"  - {item}")
