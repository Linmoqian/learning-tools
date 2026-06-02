import sqlite3
import json

db_path = "data/task_publisher.db"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("="*80)
print("修复任务357问题")
print("="*80)

# 先查看任务357
cursor.execute('SELECT * FROM tasks WHERE id = 357')
task_357 = cursor.fetchone()
if task_357:
    print(f"任务357: {task_357['name']}")
    print(f"  is_unlocked: {task_357['is_unlocked']}")
    print(f"  prerequisite_ids: {task_357['prerequisite_ids']}")
    
    # 删除它
    cursor.execute('DELETE FROM task_tags WHERE task_id = 357')
    cursor.execute('DELETE