import sqlite3
from database import execute_query, fetch_query, DB_FILE
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import tkinter as tk
import tkinter.messagebox as messagebox


def add_todo(title, description="", priority=1, due_date=None ,category=None):
    """
    添加一个新的待办事项到数据库中。
    :param title: 任务标题
    :param description: 任务描述（可选）
    :param priority: 任务优先级（默认值为 1）
    :param due_date: 截止日期，格式为 YYYY-MM-DD HH:MM:SS
    :param category: 分类（可选）
    """
    query = "INSERT INTO todos (title, description, priority, due_date,category) VALUES (?, ?, ?, ?,?)"
    execute_query(query, (title, description, priority, due_date,category))  # 执行插入操作
    print(f"已添加任务: {title}，截止日期: {due_date or '无'}，分类: {category or '无'}")


from database import execute_query, fetch_query


def list_todos(show_done=None, category=None):
    query = "SELECT id, title, description, priority, done, due_date, category FROM todos WHERE is_deleted = 0"
    params = ()
    
    if category:
        query += " AND category = ?"
        params = (category,)
    elif show_done is not None:
        query += " AND done = ?"
        params = (show_done,)

    results = fetch_query(query, params)
    return results or []


def update_todo(todo_id, done):
    """
    更新任务的完成状态。
    :param todo_id: 任务 ID
    :param done: 是否完成（布尔值）
    """
    query = "UPDATE todos SET done = ? WHERE id = ?"
    execute_query(query, (int(done), todo_id))  # 执行更新操作
    print(f"任务 {todo_id} 状态已更新为 {'完成' if done else '未完成'}")

def delete_todo(todo_id):
    """
    软删除一个待办事项。
    :param todo_id: 任务 ID
    """
    query = "UPDATE todos SET is_deleted = 1 WHERE id = ?"
    execute_query(query, (todo_id,))
    print(f"任务 {todo_id} 已删除。")


from datetime import datetime, timedelta
from database import fetch_query

def remind_todos():
    """
    提醒用户即将到期的未完成任务。
    """
    now = datetime.now()
    soon = now + timedelta(minutes=120)  # 提前 120 分钟提醒

    # 查询未完成且即将到期的任务
    query = """
    SELECT id, title, due_date FROM todos
    WHERE done = 0 AND due_date IS NOT NULL AND due_date <= ?
    """
    tasks = fetch_query(query, (soon,))

    if tasks:
        print("提醒：以下任务即将到期！")
        for task in tasks:
            print(f"[{task[0]}] {task[1]} (截止时间: {task[2]})")
    else:
        print("没有即将到期的任务。")

def generate_statistics():
    """
    生成待办事项的��计数据并绘制图表。
    """
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 获取任务完成情况数据
    query_done = "SELECT done, COUNT(*) FROM todos WHERE is_deleted = 0 GROUP BY done"
    done_data = fetch_query(query_done)
    
    # 确保有数据并处理数据
    if not done_data:
        messagebox.showinfo("提示", "暂无数据可供统计")
        return
        
    # 初始化完成和未完成的计数
    done_counts = [0, 0]  # [未完成数量, 已完成数量]
    for status, count in done_data:
        done_counts[status] = count
    
    done_labels = ["未完成", "已完成"]

    # 获取任务优先级分布数据
    query_priority = "SELECT priority, COUNT(*) FROM todos WHERE is_deleted = 0 GROUP BY priority"
    priority_data = fetch_query(query_priority)
    
    if not priority_data:
        messagebox.showinfo("提示", "暂无数据可供统计")
        return
        
    priority_labels = [f"优先级 {priority}" for priority, _ in priority_data]
    priority_counts = [count for _, count in priority_data]

    # 创建图形
    fig = plt.figure(figsize=(10, 5))
    
    # 绘制任务完成情况饼图
    plt.subplot(1, 2, 1)
    plt.pie(done_counts, labels=done_labels, autopct='%1.1f%%', startangle=140)
    plt.title("任务完成情况")

    # 绘制任务优先级分布柱状图
    plt.subplot(1, 2, 2)
    sns.barplot(x=priority_labels, y=priority_counts)
    plt.title("任务优先级分布")
    plt.xlabel("优先级")
    plt.ylabel("任务数量")

    # 调整布局
    plt.tight_layout()
    
    # 获取屏幕尺寸并居中显示
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.destroy()

    manager = plt.get_current_fig_manager()
    window_width = 1000
    window_height = 500
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    
    try:
        manager.window.wm_geometry(f"+{x_position}+{y_position}")
    except:
        try:
            manager.window.setGeometry(x_position, y_position, window_width, window_height)
        except:
            pass

    plt.show()
