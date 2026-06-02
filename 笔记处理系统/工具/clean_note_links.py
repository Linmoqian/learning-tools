import os
import re

def find_all_note_files(base_path):
    md_files = []
    for root, dirs, files in os.walk(base_path):
        if '知识点' in root:
            continue
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def clean_links_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    pattern = r'\[\[([^\[\]|]+)(?:\|[^\[\]]+)?\]\]'
    
    def replace_link(match):
        link_text = match.group(1)
        return link_text
    
    new_content = re.sub(pattern, replace_link, content)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def main():
    notes_dir = r'd:\Axelit\工作\trae\超级自动化学习工具\app\笔记'
    md_files = find_all_note_files(notes_dir)
    
    print(f"发现 {len(md_files)} 个笔记文件")
    
    cleaned_count = 0
    for md_file in md_files:
        if clean_links_in_file(md_file):
            cleaned_count += 1
            print(f"已清理: {md_file}")
    
    print(f"\n清理完成！共处理 {cleaned_count} 个文件")

if __name__ == '__main__':
    main()