import os
import re

notes_dir = r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记"

all_files = []
for root, dirs, files in os.walk(notes_dir):
    for f in files:
        if f.endswith('.md'):
            all_files.append(os.path.join(root, f))

all_links = []
for filepath in all_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = re.findall(r'\[\[([^\]|]+?)\]\]', content)
            for link in matches:
                if not link.startswith('http://') and not link.startswith('https://'):
                    all_links.append(link)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

unique_links = sorted(set(all_links))
print(f"总文件数: {len(all_files)}")
print(f"总链接数: {len(all_links)}")
print(f"唯一链接数: {len(unique_links)}")

existing_files = [os.path.splitext(os.path.basename(f))[0] for f in all_files]
missing_links = [link for link in unique_links if link not in existing_files]

print(f"\n缺失链接数: {len(missing_links)}")
print("\n=== 缺失链接列表 ===")
for link in sorted(missing_links):
    print(link)