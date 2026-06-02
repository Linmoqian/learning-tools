# test_state_engine_loading.py
from core.database import DatabaseManager
from core.state_engine import StateEngine


def test_state_engine_with_fixed_db():
    print("=== 测试状态引擎的完整加载 ===")

    # 创建数据库管理器
    db = DatabaseManager()

    # 创建状态引擎 - 这会自动调用 load_saved_state()
    print("\n创建状态引擎...")
    engine = StateEngine(db)

    # 检查加载的状态
    print(f"\n当前状态: {engine.get_current_state()}")
    print(f"高能模式: {engine.high_energy_mode}")
    print(f"低功耗模式: {engine.low_power_mode}")

    # 修改状态
    print("\n修改状态...")
    engine.manual_adjust('energy', 60)
    engine.manual_adjust('thirst', 50)
    engine.high_energy_mode = True

    print(f"修改后状态: {engine.get_current_state()}")
    print(f"高能模式: {engine.high_energy_mode}")

    # 保存状态
    print("\n保存状态...")
    success = engine.save_current_state()
    print(f"保存结果: {'成功' if success else '失败'}")

    # 创建新的状态引擎测试加载
    print("\n创建新的状态引擎测试加载...")
    db2 = DatabaseManager()
    engine2 = StateEngine(db2)

    print(f"新实例状态: {engine2.get_current_state()}")
    print(f"新实例高能模式: {engine2.high_energy_mode}")

    # 验证
    if (engine2.current_state['energy'] == 60 and
            engine2.current_state['thirst'] == 50 and
            engine2.high_energy_mode == True):
        print("\n✅ 状态引擎持久化测试通过！")
    else:
        print(f"\n❌ 状态引擎持久化测试失败")
        print(f"  预期: energy=60, thirst=50, high_energy_mode=True")
        print(f"  实际: {engine2.get_current_state()}, high_energy_mode={engine2.high_energy_mode}")


if __name__ == "__main__":
    test_state_engine_with_fixed_db()