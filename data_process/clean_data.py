import pandas as pd

def clean_all_data(df_dict):
    """
    接收包含5个DataFrame的字典，返回清洗后的字典
    """
    print("🧹 开始执行数据清洗流水线...")
    
    # 1. 基础清洗：去重、主外键校验、类型转换
    # 获取合法的学号池
    valid_student_ids = set(df_dict['basic']['student_id'].astype(str))
    
    for table_name, df in df_dict.items():
        # 确保所有表里的学号都是字符串格式
        if 'student_id' in df.columns:
            df['student_id'] = df['student_id'].astype(str)
        
        # 去重
        df = df.drop_duplicates()
        
        # 主外键一致性校验（剔除在基本信息表中找不到学号的脏数据）
        if table_name != 'basic':
            original_len = len(df)
            df = df[df['student_id'].isin(valid_student_ids)]
            if len(df) < original_len:
                print(f"  ⚠️ [{table_name}] 剔除了 {original_len - len(df)} 条孤儿数据（找不到对应学号）")
        
        df_dict[table_name] = df

    # 2. 针对性清洗：缺失值与异常值
    # 学生表：缺失的专业填补为"未分配"
    df_dict['basic']['major'] = df_dict['basic']['major'].fillna('未分配')
    
    # 成绩表：直接删除成绩为空的行 (你说的方案)，并处理异常分数
    df_dict['score'] = df_dict['score'].dropna(subset=['score'])
    df_dict['score'] = df_dict['score'][(df_dict['score']['score'] >= 0) & (df_dict['score']['score'] <= 100)]
    
    # 消费表：剔除金额小于等于0的异常记录
    df_dict['consume'] = df_dict['consume'][df_dict['consume']['amount'] > 0]

    # 3. 字段标准化：所有时间统一转为 YYYY-MM-DD HH:MM:SS
    # 需要精确到秒的表字段
    datetime_cols = {
        'consume': ['consume_time'],
        'sport': ['sport_time']
    }
    
    # 只需要精确到日期的表字段 (去掉后面的 00:00:00)
    date_cols = {
        'basic': ['enrollment_date'],
        'score': ['exam_date'],
        'library': ['borrow_date', 'return_date']
    }
    
    # 处理带时分秒的
    for table_name, cols in datetime_cols.items():
        for col in cols:
            df_dict[table_name][col] = pd.to_datetime(df_dict[table_name][col]).dt.strftime('%Y-%m-%d %H:%M:%S')

    # 处理纯日期的
    for table_name, cols in date_cols.items():
        for col in cols:
            df_dict[table_name][col] = pd.to_datetime(df_dict[table_name][col]).dt.strftime('%Y-%m-%d')

    # 4. 数据脱敏 (按需开启)
    # 方案：保留真实姓名以便可视化，如果必须脱敏可取消注释下面这行
    # df_dict['basic']['name'] = df_dict['basic']['name'].apply(lambda x: x[0] + '*' * (len(x)-1))
    
    print("✅ 数据清洗完成！")
    return df_dict