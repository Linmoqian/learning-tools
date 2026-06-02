import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from src.models.database import Database


class AIImportProcessor:
    def __init__(self, db: Database):
        self.db = db
        self.ai_imports_dir = Path(__file__).parent.parent.parent / "ai_imports"
        self.ai_imports_dir.mkdir(exist_ok=True)

    def get_all_import_files(self) -> List[Path]:
        files = sorted(
            self.ai_imports_dir.glob("ai_output_*.json"),
            key=lambda x: x.name
        )
        return files

    def process_all_imports(self) -> Tuple[List[Dict[str, Any]], List[Path]]:
        results = []
        processed_files = []
        files = self.get_all_import_files()
        print(f"找到 {len(files)} 个导入文件")
        
        for file_path in files:
            print(f"正在处理: {file_path}")
            try:
                result = self._process_single_file(file_path)
                if result:
                    results.append(result)
                    processed_files.append(file_path)
            except Exception as e:
                print(f"处理文件失败 {file_path}: {e}")

        return results, processed_files

    def delete_processed_files(self, files: List[Path]):
        for file_path in files:
            self._delete_file(file_path)

    def _process_single_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            action = data.get("action")
            explanation = data.get("explanation", "")

            applied_changes = []

            if action == "schedule":
                changes = self._apply_schedule(data)
                applied_changes.extend(changes)
            elif action == "activities":
                changes = self._apply_activities(data)
                applied_changes.extend(changes)
            elif action == "tasks":
                changes = self._apply_tasks(data)
                applied_changes.extend(changes)
            elif action == "batch_tasks":
                changes = self._apply_batch_tasks(data)
                applied_changes.extend(changes)
            elif action == "delete_tasks":
                changes = self._apply_delete_tasks(data)
                applied_changes.extend(changes)
            elif action == "analysis":
                applied_changes.append(f"分析完成：{explanation}")

            self._log_import(file_path.name, explanation, applied_changes)

            return {
                "file": file_path.name,
                "action": action,
                "explanation": explanation,
                "changes": applied_changes
            }

        except Exception as e:
            return {
                "file": file_path.name,
                "action": "error",
                "explanation": f"处理失败: {str(e)}",
                "changes": []
            }

    def _apply_schedule(self, data: Dict) -> List[str]:
        changes = []

        # 获取所有现有活动
        existing_activities = self.db.get_activity_options()
        
        # 收集日程中用到的所有活动
        schedule_items = data.get("schedule_items", [])
        activities_from_schedule = []
        for item in schedule_items:
            activity = item.get("activity")
            if activity and activity not in activities_from_schedule:
                activities_from_schedule.append(activity)
        
        # 收集 new_activities_to_add
        new_activities = data.get("new_activities_to_add", [])
        all_activities_to_add = list(set(activities_from_schedule + new_activities))
        
        # 添加缺失的活动
        for activity in all_activities_to_add:
            if activity not in existing_activities:
                self.db.add_activity_option(activity)
                changes.append(f"添加活动：{activity}")

        # 应用日程
        for item in schedule_items:
            item_type = item.get("type")
            day_of_week = item.get("day_of_week")
            slot_id = item.get("slot_id")
            activity = item.get("activity")
            notes = item.get("notes", "")

            if item_type == "weekly":
                self.db.set_weekly_schedule(day_of_week, slot_id, activity, notes)
                changes.append(f"设置每周 {item.get('day_name')} {item.get('slot_name')}：{activity}")
            else:
                # temporary - 今天
                today = datetime.now().strftime("%Y-%m-%d")
                self.db.set_daily_schedule(today, slot_id, activity, notes)
                changes.append(f"设置今天 {item.get('slot_name')}：{activity}")

        return changes

    def _apply_activities(self, data: Dict) -> List[str]:
        changes = []
        operations = data.get("operations", [])

        for op in operations:
            if op["operation"] == "add":
                activity = op["activity_name"]
                existing = self.db.get_activity_options()
                if activity not in existing:
                    self.db.add_activity_option(activity)
                    changes.append(f"添加活动：{activity}")
            elif op["operation"] == "delete":
                activity = op["activity_name"]
                self.db.delete_activity_option(activity)
                changes.append(f"删除活动：{activity}")

        return changes

    def _apply_tasks(self, data: Dict) -> List[str]:
        changes = []
        operations = data.get("operations", [])

        for op in operations:
            if op["operation"] == "add":
                task = op["task"]
                self.db.add_task(
                    name=task["name"],
                    category=task.get("task_type", "normal"),
                    description=task.get("description", ""),
                    estimated_time=task.get("estimated_time", 30),
                    preferred_time=task.get("preferred_time"),
                    deadline=task.get("deadline"),
                    resistance=task.get("resistance", "medium"),
                    energy_required=task.get("energy_required", "medium"),
                    rarity=task.get("rarity", "common"),
                    priority=task.get("priority", 5),
                    is_daily=task.get("is_daily", False)
                )
                changes.append(f"添加任务：{task['name']}")
            elif op["operation"] == "delete":
                task_id = op["task_id"]
                self.db.delete_task(task_id)
                changes.append(f"删除任务：ID={task_id}")

        return changes

    def _apply_batch_tasks(self, data: Dict) -> List[str]:
        changes = []
        tasks = data.get("tasks", [])
        
        print(f"批量创建 {len(tasks)} 个任务...")
        
        task_name_map = {}
        task_prereq_map = {}
        
        for i, task_data in enumerate(tasks):
            name = task_data.get("name", f"任务{i+1}")
            
            task_id = self.db.add_task(
                name=name,
                category=task_data.get("category", "normal"),
                description=task_data.get("description", ""),
                estimated_time=task_data.get("estimated_time", 30),
                preferred_time=task_data.get("preferred_time"),
                deadline=task_data.get("deadline"),
                resistance=task_data.get("resistance", "medium"),
                energy_required=task_data.get("energy_required", "medium"),
                rarity=task_data.get("rarity", "common"),
                priority=task_data.get("priority", 5),
                is_daily=task_data.get("is_daily", False),
                prerequisite_ids=None
            )
            
            task_name_map[name] = task_id
            
            tags = task_data.get("tags", [])
            if tags:
                self.db.set_task_tags(task_id, tags)
            
            task_prereq_map[task_id] = task_data.get("prerequisite_ids", [])
            
            if (i + 1) % 10 == 0:
                print(f"  已创建 {i+1}/{len(tasks)} 个任务...")
        
        print("正在设置依赖关系...")
        
        last_created_id = None
        for i, task_data in enumerate(tasks):
            name = task_data.get("name", f"任务{i+1}")
            task_id = task_name_map.get(name)
            if task_id is None:
                continue
            
            raw_prereq_ids = task_prereq_map.get(task_id, [])
            resolved_prereq_ids = []
            
            for pid in raw_prereq_ids:
                if isinstance(pid, str):
                    if pid == "${prev_task_id}":
                        if last_created_id is not None:
                            resolved_prereq_ids.append(last_created_id)
                    elif pid.startswith("${task_name:") and pid.endswith("}"):
                        prereq_name = pid[12:-1]
                        if prereq_name in task_name_map:
                            resolved_prereq_ids.append(task_name_map[prereq_name])
                        else:
                            print(f"警告：未找到任务 '{prereq_name}'，跳过此依赖")
                    elif pid.startswith("${") and pid.endswith("}"):
                        pass
                    else:
                        try:
                            resolved_prereq_ids.append(int(pid))
                        except (ValueError, TypeError):
                            print(f"警告：无法解析前置任务引用 '{pid}'")
                elif isinstance(pid, int):
                    resolved_prereq_ids.append(pid)
            
            if resolved_prereq_ids:
                self.db.update_task(task_id, prerequisite_ids=resolved_prereq_ids)
            
            last_created_id = task_id
        
        changes.append(f"批量创建任务：{len(tasks)}个")
        print(f"批量创建完成！共 {len(tasks)} 个任务")
        
        return changes

    def _apply_delete_tasks(self, data: Dict) -> List[str]:
        changes = []
        task_names = data.get("task_names", [])
        
        print(f"批量删除 {len(task_names)} 个任务...")
        
        deleted_count = 0
        not_found_count = 0
        
        for task_name in task_names:
            task = self.db.get_task_by_name(task_name)
            if task:
                self.db.delete_task(task['id'])
                deleted_count += 1
                changes.append(f"已删除任务: {task_name}")
            else:
                not_found_count += 1
                changes.append(f"未找到任务: {task_name}")
        
        print(f"批量删除完成！成功删除 {deleted_count} 个任务，{not_found_count} 个未找到")
        
        return changes

    def _delete_file(self, file_path: Path):
        try:
            if file_path.exists():
                file_path.unlink()
                print(f"已删除文件: {file_path}")
            else:
                print(f"文件不存在: {file_path}")
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")

    def _log_import(self, filename: str, explanation: str, changes: List[str]):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO ai_analysis_imports (file_path, analysis_summary, applied_changes)
            VALUES (?, ?, ?)
        ''', (filename, explanation, json.dumps(changes, ensure_ascii=False)))
        self.db.conn.commit()

    def export_system_config(self) -> Dict[str, Any]:
        config = {
            "export_time": datetime.now().isoformat(),
            "tasks": self._get_tasks_config(),
            "activities": self.db.get_activity_options(),
            "weekly_schedule": self._get_weekly_schedule_config(),
            "daily_schedule": self._get_daily_schedule_config()
        }
        return config

    def _get_tasks_config(self) -> List[Dict]:
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE completed = 0 ORDER BY id')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _get_weekly_schedule_config(self) -> Dict[str, Any]:
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        schedule = {}
        for day_of_week in range(7):
            schedule[day_of_week] = {
                "day_name": day_names[day_of_week],
                "slots": self.db.get_weekly_schedule_for_day(day_of_week)
            }
        return schedule

    def _get_daily_schedule_config(self) -> Dict[str, Any]:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.db.get_daily_schedule(today)
