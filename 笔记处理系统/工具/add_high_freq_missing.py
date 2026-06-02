# 将高频缺失拓展知识点添加到知识点缺失清单
import re
from pathlib import Path
from collections import defaultdict

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
report_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\报告")

# 第一步：收集所有知识点文件
knowledge_points = set()
for kp_dir in (notes_path / "知识点").iterdir():
    if not kp_dir.is_dir():
        continue
    for kp_file in kp_dir.glob("*.md"):
        name = kp_file.stem
        knowledge_points.add(name)

# 第二步：收集排除项（科目/模块文件名）
exclusions = set()
for subject_dir in notes_path.iterdir():
    if not subject_dir.is_dir() or subject_dir.name == "知识点":
        continue
    for md_file in subject_dir.glob("*.md"):
        exclusions.add(md_file.stem)

# 第三步：收集知识点中的拓展链接并统计频率
kp_extensions = defaultdict(int)
for kp_dir in (notes_path / "知识点").iterdir():
    if not kp_dir.is_dir():
        continue
    for kp_file in kp_dir.glob("*.md"):
        try:
            content = kp_file.read_text(encoding="utf-8")
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            for link in links:
                link = link.strip()
                if re.match(r'^\d+[_-]', link):
                    continue
                if link in exclusions:
                    continue
                if re.match(r'^§', link):
                    continue
                kp_extensions[link] += 1
        except:
            pass

# 第四步：筛选高频缺失知识点（引用次数 >= 3）
high_freq_missing = []
for name, count in sorted(kp_extensions.items(), key=lambda x: x[1], reverse=True):
    if name not in knowledge_points and count >= 3:
        high_freq_missing.append((name, count))

print(f"高频缺失知识点（引用>=3次）: {len(high_freq_missing)}个")
for name, count in high_freq_missing:
    print(f"  {name}: {count}次")

# 第五步：更新缺失知识点清单
missing_list_file = report_path / "缺失知识点清单.txt"
if missing_list_file.exists():
    existing_content = missing_list_file.read_text(encoding="utf-8")
else:
    existing_content = "# 缺失知识点清单\n\n> 生成时间: 自动更新\n\n## 统计信息\n\n## 缺失知识点列表\n\n"

# 提取已有缺失知识点
existing_missing = set(re.findall(r'\[\[([^\]]+)\]\]', existing_content))

# 添加新的高频缺失知识点
new_entries = []
for name, count in high_freq_missing:
    if name not in existing_missing:
        new_entries.append(f"- [[{name}]] （被引用{count}次）")

print(f"\n新增 {len(new_entries)} 个高频缺失知识点")

# 更新报告
if new_entries:
    # 在缺失知识点列表前添加高频缺失部分
    if "## 高频缺失知识点" not in existing_content:
        existing_content = existing_content.replace(
            "## 缺失知识点列表",
            f"## 高频缺失知识点（引用>=3次）\n\n{chr(10).join(new_entries)}\n\n## 缺失知识点列表"
        )
    missing_list_file.write_text(existing_content, encoding="utf-8")
    print("已更新缺失知识点清单")
else:
    print("无新增高频缺失知识点")