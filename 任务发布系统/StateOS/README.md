# \# StateOS - 个人状态管理系统

# 

# StateOS是一个桌面应用程序，用于量化和管理个人每日生理、认知与任务状态。系统遵循"输入驱动、手动超驰"哲学。

# 

# \## 功能特性

# 

# \### ?? 核心功能

# \- \*\*晨间两级评估\*\*：每日启动时的结构化状态评估

# \- \*\*实时状态监控\*\*：精力值、口渴值、饥饿值实时显示

# \- \*\*战术指令系统\*\*：一键调整状态的快捷操作

# \- \*\*活动记录\*\*：记录日常活动并自动调整状态

# \- \*\*手动微调\*\*：精细调整各项状态值

# 

# \### ?? 战术指令

# \- \*\*紧急补水\*\*：立即将口渴值设为100%

# \- \*\*强制休息\*\*：进入低电量模式，精力值设为30%

# \- \*\*状态超频\*\*：激活90分钟高能状态

# \- \*\*认知过载\*\*：任务分解与清空

# 

# \## 系统要求

# 

# \- \*\*操作系统\*\*: Windows 10/11

# \- \*\*Python版本\*\*: Python 3.9 或更高版本

# \- \*\*内存\*\*: 至少 4GB RAM

# \- \*\*存储空间\*\*: 至少 100MB 可用空间

# 

# \## 安装步骤

# 

# \### 1. 克隆或下载项目

# ```bash

# git clone https://github.com/yourusername/stateos.git

# cd stateos

# 2\. 创建虚拟环境

# bash

# python -m venv venv

# 3\. 激活虚拟环境

# Windows:

# 

# bash

# venv\\Scripts\\activate

# 4\. 安装依赖

# bash

# pip install -r requirements.txt

# 5\. 运行程序

# bash

# python main.py

# 首次使用指南

# 第一天启动

# 运行程序后，会弹出晨间评估对话框

# 

# 根据实际情况选择睡眠质量和日程安排

# 

# 如果选择"困倦"或"头痛"，30分钟后会进行再校准

# 

# 评估完成后进入主界面

# 

# 主界面说明

# 顶部: 实时状态指示器（进度条+数值）

# 

# 中部: 战术指令按钮（四个核心功能）

# 

# 下部: 常规活动记录按钮

# 

# 底部: 手动微调滑块

# 

# 数据管理

# 数据存储位置

# 数据库: C:\\Users\\<用户名>\\.stateos\\data\\stateos.db

# 

# 日志文件: C:\\Users\\<用户名>\\.stateos\\logs\\

# 

# 配置文件: C:\\Users\\<用户名>\\.stateos\\config\\

# 

# 数据备份

# 程序每天自动备份数据库，备份文件位于:

# 

# text

# C:\\Users\\<用户名>\\.stateos\\backups\\

# 自定义配置

# 编辑 config/user\_config.yml 文件来自定义系统：

# 

# yaml

# \# 添加自定义课程

# course\_options:

# ? - "新课程名称"

# 

# \# 调整状态阈值

# threshold\_alerts:

# ? energy:

# ?   low: 25

# ?   critical: 10

# 

# \# 添加自定义活动

# custom\_activities:

# ? - name: "自定义活动"

# ?   energy\_change: 10

# ?   thirst\_change: -5

# 常见问题

# Q: 程序启动时报错 "No module named 'PyQt6'"

# A: 请确保已激活虚拟环境并安装了依赖包：

# 

# bash

# venv\\Scripts\\activate

# pip install -r requirements.txt

# Q: 如何重置所有数据？

# A: 删除数据库文件并重启程序：

# 

# 关闭StateOS

# 

# 删除 C:\\Users\\<用户名>\\.stateos\\data\\stateos.db

# 

# 重新启动StateOS

# 

# Q: 支持多用户吗？

# A: 每个Windows用户有独立的数据存储，互不干扰。

# 

# Q: 如何导出我的数据？

# A: 数据库文件可以直接用SQLite浏览器打开查看和导出。

# 

# 开发指南

# 项目结构

# text

# stateos/

# ├── main.py              # 程序入口

# ├── core/               # 核心业务逻辑

# ├── ui/                 # 用户界面

# ├── config/             # 配置文件

# ├── utils/              # 工具函数

# └── assets/             # 资源文件

# 运行测试

# bash

# python -m pytest tests/

# 许可证

# MIT License

# 

# 贡献

# 欢迎提交Issue和Pull Request。

# 

# 更新日志

# v1.0.0

# 初始版本发布

# 

# 实现晨间两级评估系统

# 

# 完成所有核心战术指令

# 

# 支持数据本地存储

