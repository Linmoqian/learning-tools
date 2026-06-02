"""
StateOS 测试模块
"""

__version__ = "1.0.0"

import sys
import os

# 添加项目根目录到Python路径，以便可以导入模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
