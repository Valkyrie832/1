import sqlite3

# 数据库文件路径，所有待办事项将存储在此文件中
DB_FILE = "todo.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 创建todos表(如果不存在)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        priority INTEGER DEFAULT 1,
        done INTEGER DEFAULT 0,
        due_date TEXT,
        category TEXT,
        is_deleted INTEGER DEFAULT 0
    )
    """)

    # 检查并添加 is_deleted 列（如不存在）
    cursor.execute("PRAGMA table_info(todos)")
    columns = [row[1] for row in cursor.fetchall()]
    if "is_deleted" not in columns:
        cursor.execute("ALTER TABLE todos ADD COLUMN is_deleted INTEGER DEFAULT 0")

    conn.commit()
    conn.close()
    
    # 初始化测试数据
    clean_and_init_test_data()


def execute_query(query, params=()):
    """
    执行数据库写操作（如插入、更新或删除）。
    :param query: SQL 查询语句
    :param params: 查询参数
    """
    conn = sqlite3.connect(DB_FILE)  # 连接到数据库
    cursor = conn.cursor()
    cursor.execute(query, params)  # 执行 SQL 语句
    conn.commit()  # 提交更改
    conn.close()   # 关闭数据库连接

def fetch_query(query, params=()):
    """
    执行数据库读操作（如查询）。
    :param query: SQL 查询语句
    :param params: 查询参数
    :return: 查询结果
    """
    conn = sqlite3.connect(DB_FILE)  # 连接到数据库
    cursor = conn.cursor()
    cursor.execute(query, params)  # 执行 SQL 查询
    result = cursor.fetchall()  # 获取查询结果
    conn.close()  # 关闭数据库连接
    return result  # 返回查询结果

def clean_and_init_test_data():
    """清理并初始化测试数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute("DELETE FROM todos")
    
    # 准备测试数据
    test_data = [
        # 工作学习类
        ("完成项目报告", "整理本月项目进展情况", 3, 0, "2024-12-15 17:00:00", "工作学习", 0),
        ("准备技术分享", "准备下周团队技术分享会的PPT", 2, 0, "2024-12-13 14:00:00", "工作学习", 0),
        ("学习Python进阶", "完成在线课程第3章节", 1, 0, "2024-12-20 20:00:00", "工作学习", 0),
        
        # 家庭生活类
        ("采购生活用品", "购买日常用品和食材", 2, 0, "2024-12-11 18:00:00", "家庭生活", 0),
        ("打扫房间", "周末大扫除", 1, 0, "2024-12-16 10:00:00", "家庭生活", 0),
        
        # 健康养生类
        ("健身", "每周三次健身房锻炼", 2, 0, "2024-12-12 19:00:00", "健康养生", 0),
        ("体检预约", "年度体检预约", 3, 0, "2024-12-14 09:00:00", "健康养生", 0),
        
        # 社交人际类
        ("朋友聚会", "老同学聚会", 1, 0, "2024-12-17 18:30:00", "社交人际", 0),
        
        # 财务理财类
        ("信用卡还款", "处理本月信用卡账单", 3, 0, "2024-12-12 00:00:00", "财务理财", 0),
        ("投资计划", "制定下个月投资计划", 2, 0, "2024-12-18 16:00:00", "财务理财", 0)
    ]
    
    # 插入测试数据
    cursor.executemany("""
        INSERT INTO todos (title, description, priority, done, due_date, category, is_deleted)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, test_data)
    
    conn.commit()
    conn.close()