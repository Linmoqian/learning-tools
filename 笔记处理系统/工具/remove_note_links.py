# Remove note-to-note links in pre/post sections
# Convert [[XX_title]] to plain text

import os
import re
from pathlib import Path

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
processed = 0
modified = 0

# Pattern 1: [[digits_title]] — description
# e.g. [[01_计算机系统概述]] — 计算机的基本组成
pattern1 = re.compile(r'\[\[(\d+[-_])([^\]]+)\]\]\s*—')

# Pattern 2: [[title]] — description (in pre/post sections)
# e.g. [[三极管]] — 三极管的微变等效模型
pattern2 = re.compile(r'(### (?:前置依赖|后续应用|对比辨析)[^\n]*\n(?:[ \t]*[-*][ \t]*))\[\[([^\]]+)\]\]\s*—')

for md_file in notes_path.rglob("*.md"):
    try:
        content = md_file.read_text(encoding='utf-8')
        original = content
        file_changed = False

        # Apply pattern 1
        new_content = pattern1.sub(r'\2 —', content)
        if new_content != content:
            content = new_content
            file_changed = True

        # Apply pattern 2
        new_content = pattern2.sub(r'\1\2 —', content)
        if new_content != content:
            content = new_content
            file_changed = True

        if file_changed:
            md_file.write_text(content, encoding='utf-8')
            modified += 1
            print(f"Modified: {md_file.name}")

        processed += 1
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

print()
print("=" * 50)
print(f"Done! Scanned {processed} files, modified {modified} files")
