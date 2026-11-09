# database/init_db.py
import sqlite3
import pandas as pd
import os

# 定义数据库文件路径（确保在项目根目录下生成）
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'college_growth.db')

def init_database(df_dict):
    print(f"🔌 正在连接数据库: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 开启外键约束（极其重要！）
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 🌟 新增：每次运行前，先删除旧表（注意：因为有外键约束，要先删子表，再删主表）
    print("🧹 正在清理旧数据表...")
    cursor.execute("DROP TABLE IF EXISTS sport_record;")
    cursor.execute("DROP TABLE IF EXISTS library_record;")
    cursor.execute("DROP TABLE IF EXISTS consume_record;")
    cursor.execute("DROP TABLE IF EXISTS score_record;")
    cursor.execute("DROP TABLE IF EXISTS student_basic;")
    
    # 1. 执行建表 SQL
    print("🔨 开始创建数据表...")
    
    # 学生基本信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_basic (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT,
            major TEXT,
            enrollment_date TEXT
        )
    ''')
    
    # 成绩表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS score_record (
            record_id TEXT PRIMARY KEY,
            student_id TEXT,
            name TEXT,
            course_name TEXT,
            score INTEGER,
            exam_date TEXT,
            FOREIGN KEY (student_id) REFERENCES student_basic (student_id)
        )
    ''')
    
    # TODO 1: 请参考上面的格式，手写 consume_record（消费表）的建表 SQL
    # 字段：record_id, student_id, name, amount(REAL), consume_time, location, item_category, meal_type
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consume_record (
            record_id TEXT PRIMARY KEY,
            student_id TEXT,
            name TEXT,
            amount REAL,
            consume_time TEXT,
            location TEXT,
            item_category TEXT,
            meal_type TEXT,
            FOREIGN KEY (student_id) REFERENCES student_basic (student_id)
        )
    ''')
    
    # TODO 2: 请手写 library_record（图书馆表）的建表 SQL
    # 字段：record_id, student_id, name, book_name, borrow_date, return_date
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS library_record (
        record_id TEXT PRIMARY KEY,
        student_id TEXT,
        name TEXT,
        book_name TEXT,
        borrow_date TEXT,
        return_date TEXT,
        FOREIGN KEY (student_id) REFERENCES student_basic (student_id)
    )
    ''')
    
    # TODO 3: 请手写 sport_record（运动表）的建表 SQL
    # 字段：record_id, student_id, name, sport_type, duration_minutes(INTEGER), calories(INTEGER), sport_time
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sport_record (
        record_id TEXT PRIMARY KEY,
        student_id TEXT,
        name TEXT,
        sport_type TEXT,
        duration_minutes INTEGER,
        calories INTEGER,
        sport_time TEXT,
        FOREIGN KEY (student_id) REFERENCES student_basic (student_id)
    )
    ''')
    conn.commit()
    print("✅ 数据表创建完成！")

    # 2. 将清洗后的 DataFrame 写入数据库
    print("📥 开始写入数据...")
    try:
        # ⚠️ 注意：必须先插入主表 (student_basic)，再插入从表，否则外键约束会报错！
        df_dict['basic'].to_sql('student_basic', conn, if_exists='append', index=False)
        df_dict['score'].to_sql('score_record', conn, if_exists='append', index=False)
        df_dict['consume'].to_sql('consume_record', conn, if_exists='append', index=False)
        df_dict['library'].to_sql('library_record', conn, if_exists='append', index=False)
        df_dict['sport'].to_sql('sport_record', conn, if_exists='append', index=False)
        print("  - 所有表写入成功！")
    except Exception as e:
        print(f"❌ 写入数据失败: {e}")
    finally:
        conn.close()
        print("🔒 数据库连接已关闭。")

# --- 本地测试代码 ---
if __name__ == "__main__":
    # 为了测试，需要导入前面的模块（假设你已经在 data_process 目录下）
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    from data_process.generator_data import generate_student_basic, generate_score_record, generate_consume_record, generate_library_record, generate_sport_record
    from data_process.clean_data import clean_all_data
    
    # 1. 生成
    df_basic = generate_student_basic(500)
    df_score = generate_score_record(df_basic)
    df_consume = generate_consume_record(df_basic)
    df_library = generate_library_record(df_basic)
    df_sport = generate_sport_record(df_basic)
    
    raw_data = {
        'basic': df_basic,
        'score': df_score,
        'consume': df_consume,
        'library': df_library,
        'sport': df_sport
    }
    
    # 2. 清洗
    cleaned_data = clean_all_data(raw_data)
    
    # 3. 建库入库
    init_database(cleaned_data)