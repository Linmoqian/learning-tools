import re

# 测试内容
content = """[函数的连续性与间断点](../知识点/高数/函数的连续性与间断点.md)"""

# 测试正则表达式
pattern = r'\[([^\]]+)\]\(\.\./知识点/[^)]+\.md\)'
matches = re.findall(pattern, content)

print("测试正则表达式:")
print(f"Pattern: {pattern}")
print(f"Matches: {matches}")

# 尝试更简单的模式
pattern2 = r'\[([^\]]+)\]\([^)]+\.md\)'
matches2 = re.findall(pattern2, content)
print(f"\n更简单的Pattern: {pattern2}")
print(f"Matches: {matches2}")

# 提取完整匹配
pattern3 = r'(\[([^\]]+)\]\(([^)]+\.md)\))'
matches3 = re.findall(pattern3, content)
print(f"\n提取完整匹配:")
for m in matches3:
    print(f"  完整: {m[0]}")
    print(f"  显示: {m[1]}")
    print(f"  路径: {m[2]}")
