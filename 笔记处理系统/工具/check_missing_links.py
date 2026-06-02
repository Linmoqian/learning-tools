import os
import re
from datetime import datetime

def find_all_md_files(base_path):
    md_files = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    return md_files

def extract_wikilinks(content):
    pattern = r'\[\[([^\[\]|]+)(?:\|[^\[\]]+)?\]\]'
    links = re.findall(pattern, content)
    return links

def get_all_existing_knowledge_points(knowledge_dirs):
    existing = set()
    for knowledge_dir in knowledge_dirs:
        if os.path.exists(knowledge_dir):
            for root, dirs, files in os.walk(knowledge_dir):
                for file in files:
                    if file.endswith('.md'):
                        name = os.path.splitext(file)[0]
                        existing.add(name)
    return existing

def get_all_note_files(notes_dir):
    notes = set()
    for root, dirs, files in os.walk(notes_dir):
        if '知识点' in root:
            continue
        for file in files:
            if file.endswith('.md'):
                name = os.path.splitext(file)[0]
                notes.add(name)
    return notes

def is_chapter_name(link):
    chapter_patterns = [
        r'^高数[-\s—_]',
        r'^大物[-\s—_]',
        r'^线代[-\s—_]',
        r'^计算机[-\s—_]',
        r'^英语四级[-\s—_]',
        r'^电子技术[-\s—_]',
        r'^第.*章',
        r'^第.*节',
        r'^第.*部分',
        r'.*[-\s—_]积分$',
        r'.*[-\s—_]级数$',
        r'.*[-\s—_]几何$',
        r'.*[-\s—_]微分$',
        r'.*[-\s—_]方程$',
        r'.*[-\s—_]电路$',
        r'.*[-\s—_]分析$',
        r'.*[-\s—_]函数$',
        r'.*[-\s—_]物理$',
        r'.*[-\s—_]半导体$',
        r'.*[-\s—_]数字$',
        r'.*[-\s—_]器件$',
        r'.*[-\s—_]基础$',
        r'.*[-\s—_]原理$',
        r'.*[-\s—_]概述$',
        r'.*[-\s—_]简介$',
        r'.*[-\s—_]总结$',
        r'.*[-\s—_]复习$',
        r'.*[-\s—_]练习$',
        r'.*[-\s—_]习题$',
        r'.*[-\s—_]例题$',
        r'.*[-\s—_]详解$',
        r'.*[-\s—_]技巧$',
        r'.*[-\s—_]方法$',
        r'.*[-\s—_]应用$',
        r'.*[-\s—_]实战$',
        r'.*[-\s—_]实验$',
        r'.*[-\s—_]操作$',
        r'.*[-\s—_]指南$',
        r'.*[-\s—_]教程$',
        r'.*[-\s—_]笔记$',
        r'.*[-\s—_]讲义$',
        r'.*[-\s—_]课件$',
        r'.*[-\s—_]大纲$',
        r'.*[-\s—_]考纲$',
        r'.*[-\s—_]考点$',
        r'.*[-\s—_]重点$',
        r'.*[-\s—_]难点$',
        r'.*[-\s—_]易错点$',
        r'.*[-\s—_]误区$',
        r'.*[-\s—_]陷阱$',
        r'^\d+[_-].*',
    ]
    for pattern in chapter_patterns:
        if re.search(pattern, link):
            return True
    return False

def main():
    notes_dir = r'd:\Axelit\工作\trae\超级自动化学习工具\app\笔记'
    knowledge_dirs = [
        os.path.join(notes_dir, '知识点', '高数'),
        os.path.join(notes_dir, '知识点', '大物'),
        os.path.join(notes_dir, '知识点', '线代'),
        os.path.join(notes_dir, '知识点', '计算机'),
        os.path.join(notes_dir, '知识点', '英语四级'),
    ]
    
    md_files = find_all_md_files(notes_dir)
    print(f"发现 {len(md_files)} 个 markdown 文件")
    
    existing_knowledge = get_all_existing_knowledge_points(knowledge_dirs)
    print(f"发现 {len(existing_knowledge)} 个知识点文件")
    
    existing_notes = get_all_note_files(notes_dir)
    print(f"发现 {len(existing_notes)} 个笔记文件")
    
    missing_links = set()
    checked_files = 0
    
    for md_file in md_files:
        if '知识点' in md_file:
            continue
        
        try:
            with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            links = extract_wikilinks(content)
            
            for link in links:
                clean_link = link.strip()
                if clean_link:
                    if clean_link in existing_notes:
                        continue
                    if clean_link in existing_knowledge:
                        continue
                    if is_chapter_name(clean_link):
                        continue
                    missing_links.add(clean_link)
            
            checked_files += 1
            if checked_files % 20 == 0:
                print(f"已检查 {checked_files} 个文件，发现 {len(missing_links)} 个缺失知识点")
                
        except Exception as e:
            print(f"读取文件 {md_file} 时出错: {e}")
    
    missing_links = sorted(missing_links)
    
    output_path = r'd:\Axelit\工作\trae\超级自动化学习工具\app\报告\缺失知识点清单.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("缺失知识点清单\n")
        f.write("="*70 + "\n")
        f.write(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"文件总数(笔记): {checked_files}\n")
        f.write(f"知识点文件总数: {len(existing_knowledge)}\n")
        f.write(f"缺失知识点数量: {len(missing_links)}\n")
        f.write("\n")
        f.write("="*70 + "\n")
        f.write("\n")
        
        for i, link in enumerate(missing_links, 1):
            f.write(f"{i:3d}. {link}\n")
        
        f.write("\n")
        f.write("="*70 + "\n")
        f.write(f"\n共计 {len(missing_links)} 个知识点待创建\n")
    
    print(f"\n检查完成！共发现 {len(missing_links)} 个缺失知识点")
    print(f"结果已保存到: {output_path}")

if __name__ == '__main__':
    main()