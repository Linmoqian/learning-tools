import sys
import os
import yaml

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=== 测试自定义活动 ===\n")

# 1. 直接读取配置文件
config_path = os.path.join(project_root, "config", "user_config.yml")

with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("1. 配置文件中的自定义活动:")
if 'custom_activities' in config:
    for i, activity in enumerate(config['custom_activities'], 1):
        print(f"   {i}. {activity.get('name')}")
        print(f"      精力: {activity.get('energy_change', 0)}")
        print(f"      口渴: {activity.get('thirst_change', 0)}")
        print(f"      饥饿: {activity.get('hunger_change', 0)}")
else:
    print("   ✗ 没有找到 custom_activities")

print("\n2. 通过配置管理器获取:")
try:
    from config.config_manager import get_config_manager

    config_mgr = get_config_manager()
    all_activities = config_mgr.get_all_activities()

    custom_count = sum(1 for a in all_activities.values() if a.get('type') == 'custom')
    default_count = sum(1 for a in all_activities.values() if a.get('type') == 'default')

    print(f"   总活动数: {len(all_activities)}")
    print(f"   默认活动: {default_count}")
    print(f"   自定义活动: {custom_count}")

    if custom_count > 0:
        print("\n   自定义活动列表:")
        for name, data in all_activities.items():
            if data.get('type') == 'custom':
                print(f"   • {name}")

except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback

    traceback.print_exc()