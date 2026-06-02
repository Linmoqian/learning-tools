# 重命名剩余的文件夹
import os
from pathlib import Path

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")

# 尝试重命名
folders_to_rename = [
    (notes_path / "知识点" / "高数", notes_path / "知识点" / "高等数学"),
    (notes_path / "高数", notes_path / "高等数学")
]

for old_dir, new_dir in folders_to_rename:
    try:
        if old_dir.exists():
            old_dir.rename(new_dir)
            print(f"✅ 成功重命名: {old_dir.name} -> {new_dir.name}")
        else:
            print(f"ℹ️ 文件夹不存在: {old_dir}")
    except Exception as e:
        print(f"❌ 重命名失败: {old_dir}")
        print(f"   错误: {e}")
        print(f"   请先关闭可能打开该文件夹的程序，然后手动重命名")