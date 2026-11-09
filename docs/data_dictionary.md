# 大学生成长画像系统 - 数据字典

> **注**：本数据字典由数据工程模块（成员 A）维护。所有数据均由 Python 脚本自动生成并清洗入库，存储于 SQLite 数据库 `college_growth.db` 中。

## 1. 基础信息表 (student_basic)
**说明**：记录学生的基本身份信息，是其他所有表的基准主表。

| 字段名 | 数据类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| student_id | TEXT | 学号 | **主键**，格式为：年份+4位流水号 (如 20240001) |
| name | TEXT | 姓名 | |
| gender | TEXT | 性别 | 男 / 女 |
| major | TEXT | 专业 | 计科 / 软工 / AI / 数科 / 网安 |
| enrollment_date | TEXT | 入学日期 | 格式：YYYY-MM-DD (如 2023-09-04) |

---

## 2. 成绩记录表 (score_record)
**说明**：记录学生各门课程的成绩，每个学生、每门课均有一条记录。

| 字段名 | 数据类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| record_id | TEXT | 成绩流水号 | **主键**，格式：S + 5位流水号 (如 S00001) |
| student_id | TEXT | 学号 | **外键**，关联 student_basic.student_id |
| name | TEXT | 姓名 | |
| course_name | TEXT | 课程名称 | 高数 / 英语 / Python等 |
| score | INTEGER | 分数 | 范围：35 - 100 |
| exam_date | TEXT | 考试日期 | 格式：YYYY-MM-DD |

---

## 3. 消费记录表 (consume_record)
**说明**：记录学生在校期间的校园卡消费明细。由于是流水数据，记录条数较多。

| 字段名 | 数据类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| record_id | TEXT | 消费流水号 | **主键**，格式：C + 5位流水号 (如 C00001) |
| student_id | TEXT | 学号 | **外键**，关联 student_basic.student_id |
| name | TEXT | 姓名 | |
| amount | REAL | 消费金额 | 单位：元，保留两位小数 |
| consume_time | TEXT | 消费时间 | 格式：YYYY-MM-DD HH:MM:SS |
| location | TEXT | 消费地点 | 一食堂 / 校园超市 / 咖啡厅等 |
| item_category | TEXT | 消费品类 | 正餐 / 饮品 / 零食 / 日用品 / 水果 |
| meal_type | TEXT | 餐次 | 早餐 / 午餐 / 晚餐 / 夜宵 (基于时间推断) |

---

## 4. 图书馆借阅表 (library_record)
**说明**：记录学生的图书借阅与归还历史。

| 字段名 | 数据类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| record_id | TEXT | 借阅流水号 | **主键**，格式：L + 5位流水号 (如 L00001) |
| student_id | TEXT | 学号 | **外键**，关联 student_basic.student_id |
| name | TEXT | 姓名 | |
| book_name | TEXT | 书名 | 来源于真实书籍列表 |
| borrow_date | TEXT | 借阅日期 | 格式：YYYY-MM-DD |
| return_date | TEXT | 归还日期 | 格式：YYYY-MM-DD (保证在借阅日期之后) |

---

## 5. 运动记录表 (sport_record)
**说明**：记录学生在校的体育锻炼情况。

| 字段名 | 数据类型 | 说明 | 备注 |
| :--- | :--- | :--- | :--- |
| record_id | TEXT | 运动流水号 | **主键**，格式：T + 5位流水号 (如 T00001) |
| student_id | TEXT | 学号 | **外键**，关联 student_basic.student_id |
| name | TEXT | 姓名 | |
| sport_type | TEXT | 运动类型 | 跑步 / 篮球 / 羽毛球等 |
| duration_minutes | INTEGER | 运动时长 | 单位：分钟 (20-120) |
| calories | INTEGER | 消耗卡路里 | 单位：大卡 (时长 × 5~15的系数) |
| sport_time | TEXT | 运动时间 | 格式：YYYY-MM-DD HH:MM:SS (集中在16:00-21:00) |