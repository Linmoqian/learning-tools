# 分析缺失知识点 - 区分笔记引用和知识点拓展
import re
from pathlib import Path
from collections import defaultdict

notes_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\笔记")
report_path = Path(r"d:\Axelit\工作\trae\超级自动化学习工具\app\报告")

# 第一步：收集所有知识点文件
print("=== 收集知识点文件 ===")
knowledge_points = set()
kp_subjects = {}  # 记录每个知识点属于哪个科目
for kp_dir in (notes_path / "知识点").iterdir():
    if not kp_dir.is_dir():
        continue
    subject = kp_dir.name
    for kp_file in kp_dir.glob("*.md"):
        name = kp_file.stem
        knowledge_points.add(name)
        kp_subjects[name] = subject

print(f"找到 {len(knowledge_points)} 个知识点\n")

# 第二步：收集笔记中的链接
print("=== 分析笔记直接引用 ===")
note_references = defaultdict(set)
for subject_dir in notes_path.iterdir():
    if not subject_dir.is_dir() or subject_dir.name == "知识点":
        continue
    subject = subject_dir.name
    for md_file in subject_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            for link in links:
                link = link.strip()
                # 跳过笔记标题样式的链接
                if re.match(r'^\d+[_-]', link):
                    continue
                note_references[subject].add(link)
        except Exception as e:
            print(f"读取失败 {md_file}: {e}")

all_note_refs = set()
for refs in note_references.values():
    all_note_refs.update(refs)

print(f"笔记中共引用 {len(all_note_refs)} 个知识点\n")

# 第三步：收集知识点中的拓展链接
print("=== 分析知识点拓展引用 ===")
kp_extensions = defaultdict(set)
for kp_dir in (notes_path / "知识点").iterdir():
    if not kp_dir.is_dir():
        continue
    subject = kp_dir.name
    for kp_file in kp_dir.glob("*.md"):
        try:
            content = kp_file.read_text(encoding="utf-8")
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            kp_name = kp_file.stem
            for link in links:
                link = link.strip()
                if re.match(r'^\d+[_-]', link):
                    continue
                kp_extensions[(subject, kp_name)].add(link)
        except Exception as e:
            print(f"读取失败 {kp_file}: {e}")

all_kp_extensions = set()
for refs in kp_extensions.values():
    all_kp_extensions.update(refs)

print(f"知识点中共拓展引用 {len(all_kp_extensions)} 个知识点\n")

# 第四步：分析缺失
print("=== 分析缺失 ===")
missing_from_notes = []
missing_from_kps = []

for ref in sorted(all_note_refs):
    if ref not in knowledge_points:
        missing_from_notes.append(ref)

for ref in sorted(all_kp_extensions):
    if ref not in knowledge_points:
        missing_from_kps.append(ref)

print(f"笔记引用缺失: {len(missing_from_notes)}")
print(f"知识点拓展缺失: {len(missing_from_kps)}")

# 第五步：找出重叠和唯一
missing_notes_only = set(missing_from_notes) - set(missing_from_kps)
missing_kps_only = set(missing_from_kps) - set(missing_from_notes)
missing_both = set(missing_from_notes) & set(missing_from_kps)

print(f"仅笔记引用: {len(missing_notes_only)}")
print(f"仅知识点拓展: {len(missing_kps_only)}")
print(f"两者均引用: {len(missing_both)}\n")

# 第六步：判断基础知识点 - 基于出现频率
print("=== 统计引用频率 ===")
ref_counts = defaultdict(int)
# 统计笔记引用
for refs in note_references.values():
    for ref in refs:
        ref_counts[ref] += 1
# 统计知识点拓展
for refs in kp_extensions.values():
    for ref in refs:
        ref_counts[ref] += 1

# 按频率排序
sorted_refs = sorted(ref_counts.items(), key=lambda x: x[1], reverse=True)

# 高频可能是基础
top_candidates = []
for name, count in sorted_refs[:50]:  # 看前50
    if name not in knowledge_points:
        top_candidates.append((name, count))

print(f"\n高频缺失 (前20):")
for name, count in top_candidates[:20]:
    print(f"  {name}: {count}次")

# 生成报告
print("\n=== 生成报告 ===")
report = f"""# 缺失知识点综合分析

> 生成时间：自动生成

## 统计总览

| 类别 | 数量 |
|------|------|
| 现有知识点 | {len(knowledge_points)} |
| 笔记引用知识点 | {len(all_note_refs)} |
| 知识点拓展引用 | {len(all_kp_extensions)} |
| 笔记引用缺失 | {len(missing_from_notes)} |
| 知识点拓展缺失 | {len(missing_from_kps)} |

---

## 一、笔记中直接引用的缺失知识点

{len(missing_from_notes)}个：

"""
for ref in sorted(missing_from_notes):
    report += f"- [[{ref}]]\n"

report += f"""

---

## 二、知识点中拓展的缺失知识点

{len(missing_from_kps)}个：

"""
for ref in sorted(missing_from_kps):
    report += f"- [[{ref}]]\n"

report += f"""

---

## 三、分类详情

### 仅笔记引用
{len(missing_notes_only)}个：

"""
for ref in sorted(missing_notes_only):
    report += f"- [[{ref}]]\n"

report += f"""

### 仅知识点拓展
{len(missing_kps_only)}个：

"""
for ref in sorted(missing_kps_only):
    report += f"- [[{ref}]]\n"

report += f"""

### 两者均引用
{len(missing_both)}个：

"""
for ref in sorted(missing_both):
    report += f"- [[{ref}]]\n"

report += f"""

---

## 四、推荐优先补充的基础知识点

基于引用频率，以下高频缺失知识点建议优先作为基础知识点补充：

"""

for name, count in top_candidates[:20]:
    report += f"- [[{name}]] (被引用 {count} 次)\n"

report += f"""

---

## 五、引用频率全表

"""
report += "| 知识点 | 引用次数 | 状态 |\n"
report += "|--------|----------|------|\n"
for name, count in sorted_refs[:100]:
    status = "✅ 已存在" if name in knowledge_points else "❌ 缺失"
    report += f"| {name} | {count} | {status} |\n"

# 保存报告
report_file = report_path / "缺失知识点综合分析.md"
report_file.write_text(report, encoding="utf-8")
print(f"报告已保存: {report_file}")