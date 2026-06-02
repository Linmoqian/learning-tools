#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StateOS 数据库备份工具
用于手动备份和恢复数据库
"""

import sys
import os
import sqlite3
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging


class StateOSBackup:
    """StateOS 备份管理器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # 默认数据目录
            self.data_dir = Path.home() / ".stateos" / "data"
        else:
            self.data_dir = Path(data_dir)

        self.backup_dir = self.data_dir.parent / "backups"
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        log_dir = self.data_dir.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "backup.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_backup(self, description: str = None) -> Path:
        """创建数据库备份"""
        try:
            # 确保目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 源数据库文件
            db_file = self.data_dir / "stateos.db"
            if not db_file.exists():
                self.logger.error(f"数据库文件不存在: {db_file}")
                raise FileNotFoundError(f"数据库文件不存在: {db_file}")

            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"stateos_backup_{timestamp}.db"

            if description:
                # 清理描述中的非法字符
                safe_desc = "".join(c for c in description if c.isalnum() or c in " _-")
                backup_name = f"stateos_backup_{timestamp}_{safe_desc}.db"

            backup_file = self.backup_dir / backup_name

            # 复制数据库文件
            shutil.copy2(db_file, backup_file)

            # 创建备份元数据
            metadata = {
                'backup_time': datetime.now().isoformat(),
                'description': description,
                'source_file': str(db_file),
                'backup_file': str(backup_file),
                'file_size': backup_file.stat().st_size,
                'database_info': self.get_database_info(db_file)
            }

            # 保存元数据
            metadata_file = backup_file.with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self.logger.info(f"备份创建成功: {backup_file}")
            print(f"✅ 备份创建成功: {backup_file}")

            # 清理旧备份
            self.cleanup_old_backups()

            return backup_file

        except Exception as e:
            self.logger.error(f"备份创建失败: {e}")
            print(f"❌ 备份创建失败: {e}")
            raise

    def restore_backup(self, backup_file: str, confirm: bool = True) -> bool:
        """恢复数据库备份"""
        try:
            backup_path = Path(backup_file)

            if not backup_path.exists():
                self.logger.error(f"备份文件不存在: {backup_path}")
                print(f"❌ 备份文件不存在: {backup_path}")
                return False

            # 目标数据库文件
            db_file = self.data_dir / "stateos.db"

            # 确认恢复
            if confirm:
                print(f"⚠️  警告：这将覆盖当前数据库！")
                print(f"    备份文件: {backup_path}")
                print(f"    目标文件: {db_file}")

                if db_file.exists():
                    db_size = db_file.stat().st_size
                    backup_size = backup_path.stat().st_size
                    print(f"    当前数据库大小: {self.format_size(db_size)}")
                    print(f"    备份文件大小: {self.format_size(backup_size)}")

                response = input("确认恢复？(y/N): ").strip().lower()
                if response != 'y':
                    print("恢复已取消")
                    return False

            # 确保数据目录存在
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # 如果目标文件存在，先备份当前数据库
            if db_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pre_restore_backup = self.data_dir / f"pre_restore_{timestamp}.db"
                shutil.copy2(db_file, pre_restore_backup)
                self.logger.info(f"创建恢复前备份: {pre_restore_backup}")
                print(f"📋 已创建恢复前备份: {pre_restore_backup}")

            # 复制备份文件
            shutil.copy2(backup_path, db_file)

            # 验证数据库
            if self.verify_database(db_file):
                self.logger.info(f"数据库恢复成功: {db_file}")
                print(f"✅ 数据库恢复成功: {db_file}")
                return True
            else:
                self.logger.error("数据库验证失败")
                print("❌ 数据库验证失败，恢复可能不完整")
                return False

        except Exception as e:
            self.logger.error(f"数据库恢复失败: {e}")
            print(f"❌ 数据库恢复失败: {e}")
            return False

    def list_backups(self, show_details: bool = False):
        """列出所有备份"""
        try:
            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 查找备份文件
            backup_files = list(self.backup_dir.glob("stateos_backup_*.db"))

            if not backup_files:
                print("📭 没有找到备份文件")
                return

            print(f"📚 找到 {len(backup_files)} 个备份文件:")
            print("=" * 80)

            backups = []
            for backup_file in sorted(backup_files, reverse=True):
                try:
                    # 获取文件信息
                    stat = backup_file.stat()
                    file_size = stat.st_size
                    modified_time = datetime.fromtimestamp(stat.st_mtime)

                    # 尝试读取元数据
                    metadata_file = backup_file.with_suffix('.json')
                    description = ""

                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            description = metadata.get('description', '')

                    backups.append({
                        'file': backup_file.name,
                        'path': str(backup_file),
                        'size': file_size,
                        'modified': modified_time,
                        'description': description
                    })

                    # 显示基本信息
                    size_str = self.format_size(file_size)
                    time_str = modified_time.strftime("%Y-%m-%d %H:%M:%S")

                    print(f"📁 {backup_file.name}")
                    print(f"   📅 时间: {time_str}")
                    print(f"   📊 大小: {size_str}")
                    if description:
                        print(f"   📝 描述: {description}")

                    if show_details:
                        # 显示数据库信息
                        db_info = self.get_database_info(backup_file)
                        if db_info:
                            print(f"   🗃️  表数量: {db_info.get('table_count', 0)}")
                            for table, count in db_info.get('record_counts', {}).items():
                                print(f"     • {table}: {count} 条记录")

                    print("-" * 40)

                except Exception as e:
                    print(f"❌ 读取备份信息失败 {backup_file.name}: {e}")

            return backups

        except Exception as e:
            self.logger.error(f"列出备份失败: {e}")
            print(f"❌ 列出备份失败: {e}")

    def cleanup_old_backups(self, max_backups: int = 30, max_age_days: int = 90):
        """清理旧备份"""
        try:
            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 查找备份文件
            backup_files = list(self.backup_dir.glob("stateos_backup_*.db"))

            if len(backup_files) <= max_backups:
                return

            # 按修改时间排序
            backup_files.sort(key=lambda x: x.stat().st_mtime)

            # 计算删除阈值
            cutoff_date = datetime.now() - timedelta(days=max_age_days)

            deleted_count = 0
            # 删除最旧的备份，直到满足数量限制
            while len(backup_files) > max_backups:
                file_to_delete = backup_files.pop(0)

                # 检查文件年龄
                file_date = datetime.fromtimestamp(file_to_delete.stat().st_mtime)

                # 删除条件：超过最大数量或超过最大年龄
                if len(backup_files) >= max_backups or file_date < cutoff_date:
                    # 删除数据库文件
                    file_to_delete.unlink()

                    # 删除对应的元数据文件
                    metadata_file = file_to_delete.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()

                    deleted_count += 1
                    self.logger.info(f"删除旧备份: {file_to_delete.name}")

            if deleted_count > 0:
                self.logger.info(f"清理了 {deleted_count} 个旧备份")
                print(f"🗑️  清理了 {deleted_count} 个旧备份")

        except Exception as e:
            self.logger.error(f"清理旧备份失败: {e}")
            print(f"❌ 清理旧备份失败: {e}")

    def get_database_info(self, db_file: Path) -> dict:
        """获取数据库信息"""
        try:
            if not db_file.exists():
                return {}

            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # 获取每个表的记录数
            record_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    record_counts[table] = count
                except:
                    continue

            conn.close()

            return {
                'table_count': len(tables),
                'tables': tables,
                'record_counts': record_counts
            }

        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return {}

    def verify_database(self, db_file: Path) -> bool:
        """验证数据库完整性"""
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            # 尝试执行一些基本查询来验证数据库完整性
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]

            cursor.execute("PRAGMA foreign_key_check")
            foreign_key_result = cursor.fetchall()

            conn.close()

            # integrity_check 应该返回 'ok'
            if integrity_result == 'ok' and len(foreign_key_result) == 0:
                return True
            else:
                self.logger.warning(
                    f"数据库验证警告: integrity={integrity_result}, foreign_key={len(foreign_key_result)}")
                return False

        except Exception as e:
            self.logger.error(f"数据库验证失败: {e}")
            return False

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def export_to_csv(self, output_dir: str = None):
        """导出数据库为CSV文件"""
        try:
            db_file = self.data_dir / "stateos.db"
            if not db_file.exists():
                print("❌ 数据库文件不存在")
                return

            if output_dir is None:
                output_dir = self.data_dir.parent / "exports"
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = output_path / f"export_{timestamp}"
            export_dir.mkdir(exist_ok=True)

            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            exported_tables = 0

            for table in tables:
                try:
                    # 获取表数据
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()

                    # 获取列名
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]

                    if rows:
                        # 创建CSV文件
                        csv_file = export_dir / f"{table}.csv"
                        with open(csv_file, 'w', encoding='utf-8') as f:
                            # 写入列名
                            f.write(','.join(columns) + '\n')

                            # 写入数据
                            for row in rows:
                                # 转义特殊字符
                                escaped_row = [
                                    str(cell).replace('"', '""').replace('\n', '\\n').replace('\r', '\\r')
                                    for cell in row
                                ]
                                f.write(','.join(f'"{cell}"' for cell in escaped_row) + '\n')

                        exported_tables += 1
                        print(f"✅ 导出表 {table}: {len(rows)} 行")

                except Exception as e:
                    print(f"❌ 导出表 {table} 失败: {e}")

            conn.close()

            print(f"📤 导出完成: {exported_tables}/{len(tables)} 个表已导出到 {export_dir}")

        except Exception as e:
            self.logger.error(f"导出数据库失败: {e}")
            print(f"❌ 导出数据库失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='StateOS 数据库备份工具')
    parser.add_argument('action', choices=['backup', 'restore', 'list', 'cleanup', 'export'],
                        help='要执行的操作')
    parser.add_argument('--file', help='备份文件路径（用于恢复）')
    parser.add_argument('--desc', help='备份描述')
    parser.add_argument('--data-dir', help='数据目录路径')
    parser.add_argument('--no-confirm', action='store_true',
                        help='恢复时不需要确认')
    parser.add_argument('--details', action='store_true',
                        help='列出备份时显示详细信息')
    parser.add_argument('--max-backups', type=int, default=30,
                        help='最大备份数量（默认: 30）')
    parser.add_argument('--max-age', type=int, default=90,
                        help='备份最大保留天数（默认: 90）')

    args = parser.parse_args()

    # 创建备份管理器
    backup_mgr = StateOSBackup(args.data_dir)

    try:
        if args.action == 'backup':
            # 创建备份
            backup_mgr.create_backup(args.desc)

        elif args.action == 'restore':
            # 恢复备份
            if not args.file:
                print("❌ 请使用 --file 参数指定要恢复的备份文件")
                return

            backup_mgr.restore_backup(args.file, not args.no_confirm)

        elif args.action == 'list':
            # 列出备份
            backup_mgr.list_backups(args.details)

        elif args.action == 'cleanup':
            # 清理旧备份
            backup_mgr.cleanup_old_backups(args.max_backups, args.max_age)

        elif args.action == 'export':
            # 导出为CSV
            backup_mgr.export_to_csv()

    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
