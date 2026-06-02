# Add wiki links to knowledge point tables
# Handle "相关知识点" and "核心词条索引" tables

import re
from pathlib import Path

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
processed = 0
modified = 0


def process_file(content):
    """Process file content and add wiki links to table first columns"""
    new_content = content

    # Find all table sections with headers matching our patterns
    section_headers = ['相关知识点', '核心词条索引']

    for header in section_headers:
        # Find the section with this header
        header_pattern = rf'## (?:🔗 |📚 )?{header}\n'
        matches = list(re.finditer(header_pattern, new_content))

        for match in reversed(matches):  # Process in reverse to maintain positions
            section_start = match.end()

            # Find the next section or end of file
            next_section = re.search(r'\n## ', new_content[section_start:])
            if next_section:
                section_end = section_start + next_section.start()
            else:
                section_end = len(new_content)

            section_content = new_content[section_start:section_end]

            # Skip leading newline
            section_content = section_content.lstrip('\n')

            # Find the header row (first |...| line)
            header_row_match = re.match(r'\|[^|]+\|[^\n]*\n', section_content)
            if not header_row_match:
                continue
            header_end = header_row_match.end()

            # Find separator row (|---|...|)
            sep_match = re.search(r'\|[-|: ]+\|[-|: ]+\|[^\n]*\n', section_content[header_end:])
            if not sep_match:
                continue

            # Extract table rows
            rows_start = header_end + sep_match.end()
            rows_content = section_content[rows_start:]

            # Process each row
            new_rows = ""
            for line in rows_content.split('\n'):
                line = line.strip()
                if not line or line.startswith('|---'):
                    continue

                # Parse row
                cells = [c.strip() for c in line.split('|')]

                if len(cells) >= 2:
                    first_cell = cells[1]

                    # Skip if already has [[]]
                    if first_cell.startswith('[[') and first_cell.endswith(']]'):
                        new_rows += line + '\n'
                        continue

                    # Add [[]] to first column
                    cells[1] = f"[[{first_cell}]]"
                    new_rows += '| ' + ' | '.join(cells[1:]) + ' |\n'
                else:
                    new_rows += line + '\n'

            # Reconstruct section (add back leading newline)
            new_section = '\n' + section_content[:rows_start] + new_rows
            new_content = new_content[:section_start] + new_section + new_content[section_end:]

    return new_content


for md_file in notes_path.rglob("*.md"):
    try:
        content = md_file.read_text(encoding='utf-8')
        original = content

        new_content = process_file(content)

        if new_content != content:
            md_file.write_text(new_content, encoding='utf-8')
            modified += 1
            print(f"Modified: {md_file.name}")

        processed += 1
    except Exception as e:
        print(f"Error processing {md_file}: {e}")

print()
print("=" * 50)
print(f"Done! Scanned {processed} files, modified {modified} files")
