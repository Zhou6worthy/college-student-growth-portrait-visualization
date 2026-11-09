# 🎓 大学生成长画像与可视化系统

## 📖 项目简介
本项目是一个全栈的数据分析与可视化系统，旨在通过收集学生在校期间的**学业成绩、校园消费、图书借阅、体育运动**等多维度数据，构建客观的“学生成长画像”。系统利用数据分析技术计算各项成长指标，并通过前端大屏进行直观的交互式可视化展示，帮助教育管理者了解学生群体的行为规律与成长状态。

本项目为课程设计/小组协作项目，采用“数据先行、接口对齐、并行开发、联调验收”的工程化开发模式。

## 🛠️ 技术栈
*   **数据层 (Data Layer)**：Python 3.x, Pandas, Faker (模拟数据生成), SQLite3
*   **指标与接口层 (Metrics & API)**：FastAPI, NumPy (数据计算)
*   **前端展示层 (Frontend)**：Vue3, Vite, Element Plus, ECharts

## 📂 项目目录结构
```text
college-student-growth-portrait-visualization/
│
├── data_process/           # [成员 A] 数据生成与清洗模块
│   ├── generate_data.py    # 模拟数据生成器
│   ├── clean_data.py       # 数据清洗与标准化
│   ├── check_quality.py    # 数据质量检查报告
│   └── books.txt           # 图书馆借阅数据源
│
├── database/               # [成员 A] 数据库模块
│   └── init_db.py          # SQLite 建表、外键约束与数据入库
│
├── metrics/                # [成员 B] 指标计算模块 (开发中)
├── api/                    # [成员 B] FastAPI 接口模块 (开发中)
├── frontend/               # [成员 C] Vue3 可视化模块 (开发中)
│
├── docs/                   # [三人共同] 项目文档
│   └── data_dictionary.md  # 数据字典 (表结构与字段说明)
│
├── main.py                 # [成员 A] 数据流水线总调度入口
├── requirements.txt        # 项目依赖配置
└── README.md               # 项目说明文档