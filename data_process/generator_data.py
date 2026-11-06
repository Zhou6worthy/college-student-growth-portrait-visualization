# generator.py
import random
import pandas as pd
from faker import Faker
import datetime

# 初始化 Faker，指定中文
fake = Faker('zh_CN')
current_year = datetime.datetime.now().year

# 工具函数：获取期末考试时间
def get_final_exam_date(enroll_date: datetime.date) -> datetime.date:
    exam_months = {
        (2, 27): 6,
        (9, 4): 12,
    }

    enrollment_day = (enroll_date.month, enroll_date.day)
    if enrollment_day not in exam_months:
        # 容错处理，防止异常中断
        return enroll_date + datetime.timedelta(days=120)

    exam_month = exam_months[enrollment_day]
    return datetime.date(enroll_date.year, exam_month, 20)


# 工具函数：生成合理范围内的随机时间
def generate_random_time(start_date, end_date, min_hour, max_hour):
    """生成指定日期范围、指定小时范围内的随机时间"""
    random_date = fake.date_between(start_date=start_date, end_date=end_date)
    random_hour = random.randint(min_hour, max_hour)
    random_minute = random.randint(0, 59)
    random_second = random.randint(0, 59)
    return datetime.datetime.combine(
        random_date, 
        datetime.time(random_hour, random_minute, random_second)
    )

# 工具函数：加载本地图书列表
def load_book_list(filepath="mini_data_system/books.txt"):
    book_titles = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过注释行（#开头）和空行
            if line and not line.startswith("#"):
                book_titles.append(line)
    return book_titles

def generate_student_basic(num_students=100):
    """生成学生基本信息表"""
    students = []
    majors = ['计算机科学', '软件工程', '人工智能', '数据科学', '网络安全']
    
    for i in range(num_students):
        enroll_year = random.choice([current_year - 3, current_year - 2, current_year - 1, current_year])
        enroll_month,enroll_day = random.choice([(2,27),(9,4)])
        enrollment_date = datetime.date(enroll_year, enroll_month, enroll_day)
        student_id = f"{enroll_year}{i+1:04d}" 
        
        gender = random.choice(['男', '女'])
        name = fake.name_male() if gender == "男" else fake.name_female()
        major = random.choice(majors)
        
        students.append({
            "student_id": student_id,
            "name": name,
            "gender": gender,
            "major": major,
            "enrollment_date": enrollment_date
        })
        
    df_basic = pd.DataFrame(students)
    return df_basic

def generate_score_record(df_basic, num_records=300):
    """根据学生入学日期生成成绩记录及期末考试日期。"""
    scores = []
    courses = ['高等数学', '大学英语', 'Python编程', '数据结构', '操作系统', '计算机组成原理']

    # 建立索引，方便查找学生姓名和入学日期
    student_info = df_basic.set_index("student_id").to_dict("index")
    student_id_pool = list(student_info.keys())

    for i in range(num_records):
        record_id = f"S{i + 1:04d}"
        student_id = random.choice(student_id_pool)
        
        # 满足你的需求：获取姓名
        name = student_info[student_id]["name"]
        enrollment_date = student_info[student_id]["enrollment_date"]
        
        exam_date = get_final_exam_date(enrollment_date)
        course_name = random.choice(courses)
        score = random.randint(35, 100)

        scores.append({
            "record_id": record_id,
            "student_id": student_id,
            "name": name,  # 关联姓名
            "course_name": course_name,
            "score": score,
            "exam_date": exam_date
        })

    return pd.DataFrame(scores)

def generate_consume_record(df_basic, num_records=500):
    """生成消费记录表（包含饮食特点分析维度）"""
    consumes = []
    student_info = df_basic.set_index("student_id").to_dict("index")
    student_id_pool = list(student_info.keys())
    
    locations = ['一食堂', '二食堂', '三食堂', '校园超市', '水果店', '咖啡厅']

    for i in range(num_records):
        record_id = f"C{i + 1:04d}"
        student_id = random.choice(student_id_pool)
        name = student_info[student_id]["name"]
        
        # 1. 先决定买什么（品类）
        # 食堂主要买正餐，超市买零食日用品，水果店买水果
        location = random.choice(locations)
        if location in ['一食堂', '二食堂', '三食堂']:
            item_category = random.choice(['正餐', '正餐', '饮品']) # 食堂正餐概率大
        elif location == '校园超市':
            item_category = random.choice(['零食', '日用品', '饮品'])
        elif location == '水果店':
            item_category = '水果'
        else: # 咖啡厅
            item_category = '饮品'

        # 2. 根据品类决定时间和金额
        if item_category == '正餐':
            amount = round(random.uniform(10.0, 30.0), 2)
            # 正餐时间：11-14点 或 17-20点
            start_h = random.choice([11, 17])
            consume_time = generate_random_time('-1y', 'now', start_h, start_h + 3)
        elif item_category == '日用品':
            amount = round(random.uniform(15.0, 80.0), 2)
            consume_time = generate_random_time('-1y', 'now', 8, 22) # 超市全天开
        else:
            amount = round(random.uniform(3.0, 15.0), 2)
            consume_time = generate_random_time('-1y', 'now', 7, 22) # 零食饮品
            
        # 3. 根据最终时间决定餐次
        hour = consume_time.hour
        if 5 <= hour < 10: meal_type = '早餐'
        elif 10 <= hour < 15: meal_type = '午餐'
        elif 15 <= hour < 20: meal_type = '晚餐'
        else: meal_type = '夜宵'
        
        consumes.append({
            "record_id": record_id,
            "student_id": student_id,
            "name": name,
            "amount": amount,
            "consume_time": consume_time,
            "location": location,
            "item_category": item_category,
            "meal_type": meal_type
        })
        
    return pd.DataFrame(consumes)

def generate_library_record(df_basic, num_records=200):
    """生成图书馆借阅记录表"""
    libraries = []
    student_info = df_basic.set_index("student_id").to_dict("index")
    student_id_pool = list(student_info.keys())
    
    books = load_book_list()
    
    for i in range(num_records):
        record_id = f"L{i + 1:04d}"
        student_id = random.choice(student_id_pool)
        name = student_info[student_id]["name"]
        
        # 借阅日期在过去的4年内
        borrow_date = fake.date_time_between(start_date='-4y', end_date='-10d').date()
        # 归还日期在借阅日期之后，通常在10-30天内
        return_date = borrow_date + datetime.timedelta(days=random.randint(5, 30))
        
        book_name = random.choice(books)
        
        libraries.append({
            "record_id": record_id,
            "student_id": student_id,
            "name": name,
            "book_name": book_name,
            "borrow_date": borrow_date,
            "return_date": return_date
        })
        
    return pd.DataFrame(libraries)

def generate_sport_record(df_basic, num_records=300):
    """生成运动记录表"""
    sports = []
    student_info = df_basic.set_index("student_id").to_dict("index")
    student_id_pool = list(student_info.keys())
    
    sport_types = ['跑步', '篮球', '羽毛球', '游泳', '健身']
    
    for i in range(num_records):
        record_id = f"T{i + 1:04d}"
        student_id = random.choice(student_id_pool)
        name = student_info[student_id]["name"]
        
        sport_type = random.choice(sport_types)
        duration = random.randint(20, 120) # 运动时长20-120分钟
        
        # 简单估算卡路里：每分钟消耗 5-15 卡路里
        calories = duration * random.randint(5, 15)
        
        # 运动时间在过去半年内,下午 16点到晚上 21点之间
        sport_time = generate_random_time('-6m', 'now', 16, 21)
        
        sports.append({
            "record_id": record_id,
            "student_id": student_id,
            "name": name,
            "sport_type": sport_type,
            "duration_minutes": duration,
            "calories": calories,
            "sport_time": sport_time
        })
        
    return pd.DataFrame(sports)

# # --- 用于本地测试的代码 ---
# if __name__ == "__main__":
#     # 1. 基本信息表
#     df_basic = generate_student_basic(num_students=100)
#     print("=== 基本信息表 (前5行) ===")
#     print(df_basic.head(), "\n")
    
#     # 2. 成绩表
#     df_score = generate_score_record(df_basic, num_records=300)
#     print("=== 成绩表 (前5行) ===")
#     print(df_score.head(), "\n")
    
#     # 3. 消费表
#     df_consume = generate_consume_record(df_basic, num_records=500)
#     print("=== 消费表 (前5行) ===")
#     print(df_consume.head(), "\n")
    
#     # 4. 图书馆表
#     df_library = generate_library_record(df_basic, num_records=200)
#     print("=== 图书馆表 (前5行) ===")
#     print(df_library.head(), "\n")
    
#     # 5. 运动表
#     df_sport = generate_sport_record(df_basic, num_records=300)
#     print("=== 运动表 (前5行) ===")
#     print(df_sport.head(), "\n")