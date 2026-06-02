import os
import re

def get_all_existing_knowledge_points(notes_dir):
    knowledge_dirs = [
        os.path.join(notes_dir, '知识点', '高数'),
        os.path.join(notes_dir, '知识点', '大物'),
        os.path.join(notes_dir, '知识点', '线代'),
        os.path.join(notes_dir, '知识点', '计算机'),
        os.path.join(notes_dir, '知识点', '英语四级'),
        os.path.join(notes_dir, '知识点', '电子技术'),
    ]
    existing = set()
    for knowledge_dir in knowledge_dirs:
        if os.path.exists(knowledge_dir):
            for root, dirs, files in os.walk