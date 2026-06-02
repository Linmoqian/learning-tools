#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from pathlib import Path

# 设置路径
notes_base = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
knowledge_base = notes_base / "知识点"

# 定义要合并的知识点组
merge_groups = [
    {
        "main": "线性相关与线性无关",
        "merge": ["线性相关", "线性无关", "线性相关与无关定义", "线性相关与无关判定", "线性相关性"]
    },
    {
        "main": "线性方程组",
        "merge": ["线性方程组求解"]
    },
    {
        "main": "线性空间",
        "merge": ["线性空间与基底维数"]
    },
    {
        "main": "特征值与特征向量",
        "merge": ["特征值", "特征向量", "特征值非零"]
    },
    {
        "main": "矩阵",
        "merge": ["矩阵运算", "矩阵的秩", "矩阵的等价", "矩阵的迹", "矩阵乘法"]
    }
]

def find_files_with_link(link_name):
    """查找所有包含指定链接的文件"""
    files = []
    for md_file in notes_base.rglob("*.md"):
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if f"[[{link_name}]]" in content:
                    files.append(md_file)
        except:
            pass
    return files

def update_links_in_file(filepath, old_links, new_link):
    """更新文件中的链接"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for old_link in old_links:
            old_pattern = f"[[{old_link}]]"
            new_pattern = f"[[{new_link}]]"
            content = content.replace(old_pattern, new_pattern)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  错误更新 {filepath}: {e}")
        return False

def merge_knowledge_points(group):
    """合并一组知识点"""
    main_name = group["main"]
    merge_names = group["merge"]
    
    print(f"\n{'='*60}")
    print(f"合并知识点组：{main_name}")
    print(f"要合并的知识点：{', '.join(merge_names)}")
    print(f"{'='*60}")
    
    # 找出所有引用这些知识点的文件
    all_files = set()
    for name in [main_name] + merge_names:
        files = find_files_with_link(name)
        all_files.update(files)
        print(f"  引用 [[{name}]] 的文件: {len(files)} 个")
    
    print(f"\n  总共有 {len(all_files)} 个文件需要更新")
    
    # 更新所有文件中的链接
    updated_count = 0
    for filepath in all_files:
        success = update_links_in_file(filepath, merge_names, main_name)
        if success:
            updated_count += 1
            if updated_count % 20 == 0:
                print(f"  已更新 {updated_count}/{len(all_files)} 个文件...")
    
    print(f"\n  ✅ 成功更新 {updated_count} 个文件")
    
    # 删除被合并的文件
    deleted_count = 0
    for name in merge_names:
        for subject in ['高数', '线代', '大物', '电子技术', '计算机', '英语四级']:
            filepath = knowledge_base / subject / f"{name}.md"
            if filepath.exists():
                filepath.unlink()
                deleted_count += 1
                print(f"  删除文件: {filepath}")
    
    print(f"\n  🗑️ 删除了 {deleted_count} 个重复文件")
    
    return updated_count, deleted_count

def main():
    print("开始合并相似知识点...")
    
    total_updated = 0
    total_deleted = 0
    
    for group in merge_groups:
        updated, deleted = merge_knowledge_points(group)
        total_updated += updated
        total_deleted += deleted
    
    print(f"\n{'='*60}")
    print("合并完成！")
    print(f"{'='*60}")
    print(f"总共更新了 {total_updated} 个文件")
    print(f"总共删除了 {total_deleted} 个重复文件")

if __name__ == "__main__":
    main()