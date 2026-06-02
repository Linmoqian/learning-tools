# 批量重命名文件，将线代替换为线性代数，大物替换为大学物理
import os
from pathlib import Path

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
processed = 0
renamed = 0

replacements = {
    "线代": "线性代数",
    "大物": "大学物理"
}

# 先收集所有需要重命名的文件，避免边遍历边修改
files_to_rename = []
for root, dirs, files in os.walk(notes_path):
    for filename in files:
        if ".md" in filename:
            new_name = filename
            for old, new in replacements.items():
                new_name = new_name.replace(old, new)
            if new_name != filename:
                old_path = Path(root) / filename
                new_path = Path(root) / new_name
                files_to_rename.append((old_path, new_path))

# 执行重命名
for old_path, new_path in files_to_rename:
    try:
        old_path.rename(new_path)
        renamed += 1
        print(f"已重命名: {old_path.name} -> {new_path.name}")
        processed += 1
    except Exception as e:
        print(f"重命名失败: {old_path} - {e}")
        processed += 1

print("\n" + "=" * 50)
print(f"处理完成: 共检查 {len(files_to_rename)} 个文件，重命名 {renamed} 个文件")