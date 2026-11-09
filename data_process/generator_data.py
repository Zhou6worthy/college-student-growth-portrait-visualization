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
def load_book_list(filepath="data_process/books.txt"):
    book_titles = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过注释行（#开头）和空行
            if line and not line.startswith("#"):
                book_titles.append(line)
    return book_titles

# 建表
def generate_student_basic(num_students=500):
    students = []
    
    # 1. 按照你要求的固定人数生成专业池
    majors_pool = (
        ['计算机科学'] * 128 + 
        ['软件工程'] * 128 + 
        ['人工智能'] * 100 + 
        ['数据科学'] * 100 + 
        ['网络安全'] * 44
    )
    # 打乱顺序，这样学号和专业就不会呈现出“前128个都是计科”的规律
    random.shuffle(majors_pool) 
    
    for i in range(num_students):
        enroll_year = random.choice([current_year - 3, current_year - 2, current_year - 1, current_year])
        enroll_month,enroll_day = random.choice([(2,27),(9,4)])
        enrollment_date = datetime.date(enroll_year, enroll_month, enroll_day)
        student_id = f"{enroll_year}{i+1:04d}" 
        
        gender = random.choice(['男', '女'])
        name = fake.name_male() if gender == "男" else fake.name_female()
        
        # 从打乱的专业池里按顺序拿
        major = majors_pool[i] 
        
        students.append({
            "student_id": student_id,
            "name": name,
            "gender": gender,
            "major": major,
            "enrollment_date": enrollment_date
        })
        
    return pd.DataFrame(students)

def generate_score_record(df_basic):
    """每个学生都有每门课的成绩"""
    scores = []
    courses = ['高等数学', '大学英语', 'Python编程', '数据结构', '操作系统', '计算机组成原理']
    
    student_info = df_basic.set_index("student_id").to_dict("index")
    record_counter = 1
    
    # 遍历每个学生
    for student_id, info in student_info.items():
        # 遍历每门课
        for course in courses:
            record_id = f"S{record_counter:05d}"
            
            # 每个人的每门课成绩独立生成
            score = random.randint(35, 100) # 适当提高最低分，避免太难看
            exam_date = get_final_exam_date(info["enrollment_date"])
            
            scores.append({
                "record_id": record_id,
                "student_id": student_id,
                "name": info["name"],
                "course_name": course,
                "score": score,
                "exam_date": exam_date
            })
            record_counter += 1

    return pd.DataFrame(scores)

def generate_consume_record(df_basic):
    consumes = []
    student_info = df_basic.set_index("student_id").to_dict("index")
    locations = ['一食堂', '二食堂', '三食堂', '校园超市', '水果店', '咖啡厅']
    record_counter = 1

    for student_id, info in student_info.items():
        # 保底+波动：每个人生成 30 到 60 条消费记录
        num_personal_records = random.randint(30, 60) 
        
        for _ in range(num_personal_records):
            record_id = f"C{record_counter:05d}"
        # ... 原有的生成品类、时间的代码不变 ...
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
 
            name = info["name"]
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
            record_counter += 1
    return pd.DataFrame(consumes)

def generate_library_record(df_basic):
    """生成图书馆借阅记录表（保底+波动模式）"""
    libraries = []
    student_info = df_basic.set_index("student_id").to_dict("index")
    
    # 加载你本地准备的图书列表
    books = load_book_list()
    
    record_counter = 1 # 用于生成全局唯一的 record_id
    
    # 遍历每个学生，保证每个人都有借书记录
    for student_id, info in student_info.items():
        # 保底+波动：每个人随机生成 1 到 8 次借阅记录
        num_personal_records = random.randint(1, 8)
        
        for _ in range(num_personal_records):
            record_id = f"L{record_counter:05d}"
            
            # 借阅日期在过去的4年内 (注意留出归还的时间)
            borrow_date = fake.date_time_between(start_date='-4y', end_date='-10d').date()
            # 归还日期在借阅日期之后，通常在5-30天内
            return_date = borrow_date + datetime.timedelta(days=random.randint(5, 30))
            
            book_name = random.choice(books)
            
            libraries.append({
                "record_id": record_id,
                "student_id": student_id,
                "name": info["name"],
                "book_name": book_name,
                "borrow_date": borrow_date,
                "return_date": return_date
            })
            record_counter += 1
            
    return pd.DataFrame(libraries)

def generate_sport_record(df_basic):
    """生成运动记录表（保底+波动模式）"""
    sports = []
    student_info = df_basic.set_index("student_id").to_dict("index")
    sport_types = ['跑步', '篮球', '羽毛球', '游泳', '健身']
    
    record_counter = 1 # 用于生成全局唯一的 record_id
    
    # 遍历每个学生，保证每个人都有运动记录
    for student_id, info in student_info.items():
        # 保底+波动：每个人随机生成 5 到 15 次运动记录
        num_personal_records = random.randint(5, 15)
        
        for _ in range(num_personal_records):
            record_id = f"T{record_counter:05d}"
            
            sport_type = random.choice(sport_types)
            duration = random.randint(20, 120) # 运动时长20-120分钟
            
            # 简单估算卡路里：每分钟消耗 5-15 卡路里
            calories = duration * random.randint(5, 15)
            
            # 运动时间在过去半年内, 下午 16点到晚上 21点之间
            sport_time = generate_random_time('-6m', 'now', 16, 21)
            
            sports.append({
                "record_id": record_id,
                "student_id": student_id,
                "name": info["name"], # 直接从学生信息字典中获取
                "sport_type": sport_type,
                "duration_minutes": duration,
                "calories": calories,
                "sport_time": sport_time
            })
            record_counter += 1
            
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