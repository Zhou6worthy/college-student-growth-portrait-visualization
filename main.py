# main.py
import os
import sys

# 将当前目录加入环境变量，确保能正确导入包
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_process.generator_data import (
    generate_student_basic, 
    generate_score_record, 
    generate_consume_record, 
    generate_library_record, 
    generate_sport_record
)
from data_process.clean_data import clean_all_data
from database.init_db import init_database

def run_data_pipeline():
    print("🚀 ========================================")
    print("🚀 大学生成长画像系统 - 数据流水线启动")
    print("🚀 ========================================")
    
    # 1. 生成数据
    print("\n[1/3] 正在生成模拟数据...")
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
    print("✅ 数据生成完毕！")
    
    # 2. 清洗数据
    print("\n[2/3] 正在清洗与规范化数据...")
    cleaned_data = clean_all_data(raw_data)
    
    # 3. 建库并入库
    print("\n[3/3] 正在写入 SQLite 数据库...")
    init_database(cleaned_data)
    
    print("\n🎉 ========================================")
    print("🎉 数据底座已准备就绪！可以交付给 B (后端) 和 C (前端) 了！")
    print("🎉 数据库文件位置: ./college_growth.db")
    print("🎉 ========================================")

if __name__ == "__main__":
    run_data_pipeline()