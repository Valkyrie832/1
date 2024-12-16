import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from tkcalendar import DateEntry, Calendar
from ai_classifier import TaskClassifier
from commands import add_todo, list_todos, update_todo, delete_todo, generate_statistics
from database import init_db
from PIL import Image, ImageTk
import os
from ai_advisor import AIAdvisor
from voice_input import VoiceInput
from task_parser import TaskParser
from datetime import datetime, timedelta
import re
import calendar

TRANSLATIONS = {
    "中文": {
        "window_title": "待办事项管理系统",
        "filter_label": "分类筛选:",
        "filter_button": "查看",
        "categories": ["工作学习", "家庭生活", "社交人际", "健康养生", "财务理财", "其他"],
        "all": "所有",
        "columns": ("ID", "标题", "描述", "优先级", "状态", "截止日期", "分类"),
        "status": {"done": "完成", "undone": "未完成"},
        "buttons": {
            "add": "添加任务",
            "mark_done": "标记为完成",
            "delete": "删除任务",
            "refresh": "刷新列表",
            "statistics": "生成统计图"
        },
        "add_window": {
            "title": "添加任务",
            "auto_classify": "启用自动分类与优先级判断",
            "task_title": "标题:",
            "description": "描述:",
            "priority": "优先级:",
            "due_date": "截止日期:",
            "category": "分类:",
            "save": "保存任务",
            "time": "时间:",
            "hour": "时",
            "minute": "分", 
            "second": "秒",
            "voice_input": "语音输入",
            "start_voice": "开始语音输入",
            "stop_voice": "停止语音输入",
            "use_voice": "使用语音文本",
            "auto_analyze": "自动识别",
            "analyzing": "正在分析...",
            "analyze_complete": "分析完成",
            "target_select": "填入位置:",
            "target_title": "标题",
            "target_description": "描述",
        },
        "messages": {
            "warning": "警告",
            "error": "错误",
            "success": "成功",
            "select_task": "请选择一个任务",
            "empty_title": "任务标题不能为空",
            "invalid_priority": "优先级必须是 1、2 或 3",
            "task_added": "任务已添加",
            "task_marked": "任务已标记为完成",
            "task_deleted": "任务已删除",
            "confirm": "确认",
            "confirm_mark_done": "是否确认将任务「{}」标记为已完成？",
            "confirm_delete": "是否确认删除任务「{}」？"
        },
        "status_filter": "完成状态:",
        "priority_filter": "优先级:",
        "all": "全部",
        "done": "已完成",
        "undone": "未完成",
        "show_all": "显示所有任务",
    },
    "English": {
        "window_title": "Todo Management System",
        "filter_label": "Filter by Category:",
        "filter_button": "View",
        "categories": ["Work/Study", "Home/Life", "Social", "Health", "Finance", "Others"],
        "all": "All",
        "columns": ("ID", "Title", "Description", "Priority", "Status", "Due Date", "Category"),
        "status": {"done": "Done", "undone": "Pending"},
        "buttons": {
            "add": "Add Task",
            "mark_done": "Mark Done",
            "delete": "Delete Task",
            "refresh": "Refresh",
            "statistics": "Statistics"
        },
        "add_window": {
            "title": "Add Task",
            "auto_classify": "Enable Auto Classification & Priority",
            "task_title": "Title:",
            "description": "Description:",
            "priority": "Priority:",
            "due_date": "Due Date:",
            "category": "Category:",
            "save": "Save Task",
            "time": "Time:",
            "hour": "h",
            "minute": "m",
            "second": "s",
            "voice_input": "Voice Input",
            "start_voice": "Start Voice Input",
            "stop_voice": "Stop Voice Input",
            "use_voice": "Use Voice Text",
            "auto_analyze": "Auto Analyze",
            "analyzing": "Analyzing...",
            "analyze_complete": "Analysis Complete",
            "target_select": "Fill in:",
            "target_title": "Title",
            "target_description": "Description",
        },
        "messages": {
            "warning": "Warning",
            "error": "Error",
            "success": "Success",
            "select_task": "Please select a task",
            "empty_title": "Task title cannot be empty",
            "invalid_priority": "Priority must be 1, 2 or 3",
            "task_added": "Task added successfully",
            "task_marked": "Task marked as done",
            "task_deleted": "Task deleted successfully",
            "confirm": "Confirm",
            "confirm_mark_done": "Are you sure you want to mark task '{}' as done?",
            "confirm_delete": "Are you sure you want to delete task '{}'?",
        },
        "status_filter": "Status:",
        "priority_filter": "Priority:",
        "all": "All",
        "done": "Done",
        "undone": "Pending",
        "show_all": "Show All Tasks",
    }
}

# 在文件开头，TRANSLATIONS 字典之后添加
calendar_window = None
cal = None
due_dates = {}  # 将due_dates定义为全局变量

def toggle_calendar():
    """切换日历显示状态"""
    global calendar_window
    if calendar_window is None:
        show_calendar()
    else:
        calendar_window.destroy()
        calendar_window = None

def on_date_select(event):
    """日期选择事件处理"""
    global cal  # 声明 cal 为全局变量
    selected_date = cal.get_date()
    try:
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
        if date_obj in due_dates:
            show_date_tasks(date_obj)  # 直接在主界面显示任务
    except ValueError:
        pass

def show_calendar():
    """显示日历窗口"""
    global calendar_window, cal, due_dates  # 将due_dates声明为全局变量
    
    try:
        # 获取主窗口位置和大小
        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_width = root.winfo_width()
        
        # 创建日历窗口
        calendar_window = tk.Toplevel(root)
        calendar_window.title("任务日历")
        calendar_window.geometry(f"300x350+{root_x + root_width + 5}+{root_y}")  # 紧贴主窗口右侧
        calendar_window.transient(root)  # 设置为主窗口的临时窗口
        
        # 创建日历控件
        cal = Calendar(calendar_window, selectmode='day', date_pattern='y-mm-dd')
        cal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 获取所有任务的截止日期
        tasks = list_todos()
        due_dates.clear()  # 清空旧的数据
        for task in tasks:
            if task[5]:  # 检查是否有截止日期
                try:
                    due_date = datetime.strptime(task[5], '%Y-%m-%d %H:%M:%S').date()
                    if due_date not in due_dates:
                        due_dates[due_date] = []
                    due_dates[due_date].append(task)
                except ValueError:
                    continue
        
        # 标记有任务的日期
        for date, tasks in due_dates.items():
            # 根据任务优先级设置不同的标记颜色
            max_priority = max(task[3] for task in tasks)
            if max_priority == 3:
                cal.calevent_create(date, "高优先级任务", "high_priority")
                cal.tag_config("high_priority", background='red', foreground='white')
            elif max_priority == 2:
                cal.calevent_create(date, "中优先级任务", "medium_priority")
                cal.tag_config("medium_priority", background='orange')
            else:
                cal.calevent_create(date, "低优先级任务", "low_priority")
                cal.tag_config("low_priority", background='green', foreground='white')
        
        # 绑定日期选择事件
        def on_date_select(event):
            """日期选择事件处理"""
            selected_date = cal.get_date()
            try:
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
                if date_obj in due_dates:
                    show_date_tasks(date_obj)  # 直接在主界面显示任务
            except ValueError:
                pass
        
        cal.bind('<<CalendarSelected>>', on_date_select)
        
        # 窗口关闭时清理全局变量
        def on_calendar_close():
            global calendar_window
            calendar_window.destroy()
            calendar_window = None
            
        calendar_window.protocol("WM_DELETE_WINDOW", on_calendar_close)
        
    except Exception as e:
        messagebox.showerror("错误", f"显示日历时出错: {str(e)}")
        if calendar_window:
            calendar_window.destroy()
            calendar_window = None

def show_date_tasks(date):
    """在主界面显示指定日期的任务"""
    # 清空任务列表
    for row in tree.get_children():
        tree.delete(row)
    
    # 获取所有任务
    tasks = list_todos()
    
    # 过滤指定日期的任务
    filtered_tasks = []
    for task in tasks:
        if task[5]:  # 检查是否有截止日期
            try:
                task_due_date = datetime.strptime(task[5], '%Y-%m-%d %H:%M:%S').date()
                if task_due_date == date:
                    filtered_tasks.append(task)
            except ValueError:
                continue
    
    # 添加任务到列表
    for task in filtered_tasks:
        task_id, title, description, priority, done, due_date, category = task
        
        # 检查是否过期
        is_overdue = False
        if not done and due_date:
            try:
                due_datetime = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                if datetime.now() > due_datetime:
                    is_overdue = True
                    title = f"{title}（已过期）"
            except ValueError:
                pass
        
        item = tree.insert("", tk.END, values=(
            task_id, title, description, priority, 
            "已完成" if done else "未完成", 
            due_date, category
        ))
        
        if is_overdue:
            tree.tag_configure('overdue', foreground='red')
            tree.item(item, tags=('overdue',))

# 初始化数据库
init_db()

# 居中窗口函数
def center_window(root):
    root.update_idletasks()
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width - window_width) // 2
    y_position = (screen_height - window_height) // 2
    root.geometry("+{}+{}".format(x_position, y_position))

# 口配置
root = tk.Tk()
root.title("待办事项管理系统")
root.geometry("910x500")
center_window(root)

# 创建顶部框架来包含语言选择
top_frame = tk.Frame(root)
top_frame.pack(fill=tk.X, padx=5, pady=5)

# 将原来的language_frame改为放在top_frame中
language_frame = tk.Frame(top_frame)
language_frame.pack(side=tk.LEFT, fill=tk.X, padx=5)

current_language = tk.StringVar(value="中文")
tk.Label(language_frame, text="Language/语言:", font=("宋体", 12)).pack(side=tk.LEFT, padx=5)
language_selector = ttk.Combobox(language_frame, textvariable=current_language, 
                                values=["中文", "English"], state="readonly")
language_selector.pack(side=tk.LEFT, padx=5)

def update_language(*args):
    """更新界面语言"""
    lang = current_language.get()
    texts = TRANSLATIONS[lang]
    
    # 更新主窗口标题
    root.title(texts["window_title"])
    
    # 更新筛选区域的所有标签
    filter_labels = [widget for widget in filter_frame.winfo_children() if isinstance(widget, tk.Label)]
    filter_labels[0].configure(text=texts["filter_label"])
    filter_labels[1].configure(text=texts["status_filter"])
    filter_labels[2].configure(text=texts["priority_filter"])
    
    # 更新分类下拉框
    category_var.set(texts["all"])
    category_dropdown['values'] = [texts["all"]] + texts["categories"]
    
    # 更新完成状态下拉框
    current_status = status_var.get()
    if lang == "English":
        status_var.set("All" if current_status == "全部" else 
                      "Done" if current_status == "已完成" else 
                      "Pending" if current_status == "未完成" else current_status)
        status_dropdown['values'] = ["All", "Done", "Pending"]
    else:
        status_var.set("全部" if current_status == "All" else 
                      "已完成" if current_status == "Done" else 
                      "未完成" if current_status == "Pending" else current_status)
        status_dropdown['values'] = ["全部", "已完成", "未完成"]
    
    # 更新优先级下拉框
    current_priority = priority_var.get()
    if lang == "English":
        priority_var.set("All" if current_priority == "全部" else current_priority)
        priority_dropdown['values'] = ["All", "1", "2", "3"]
    else:
        priority_var.set("全部" if current_priority == "All" else current_priority)
        priority_dropdown['values'] = ["全部", "1", "2", "3"]
    
    # 更新查看按钮文本
    view_button.configure(text=texts["filter_button"])
    
    # 更新表格列头
    for col, text in zip(columns, texts["columns"]):
        tree.heading(col, text=text)
    
    # 更新按钮文本
    buttons = button_frame.winfo_children()
    buttons[0].configure(text=texts["buttons"]["add"])
    buttons[1].configure(text=texts["buttons"]["mark_done"])
    buttons[2].configure(text=texts["buttons"]["delete"])
    buttons[3].configure(text=texts["buttons"]["refresh"])
    buttons[4].configure(text=texts["buttons"]["statistics"])
    
    # 刷新任务列表以更新状态文本
    refresh_tasks()

# 绑定语言择件
language_selector.bind("<<ComboboxSelected>>", update_language)

# 创分类筛选区域的架
filter_frame = tk.Frame(root)
filter_frame.pack(fill=tk.X, padx=5, pady=5)

# 分类筛选标签和下拉框
categories = ["工作学习", "家庭生活", "社交人际", "健康养生", "财务理财", "其他"]
tk.Label(filter_frame, text="分类筛选:", font=("宋体", 12)).pack(side=tk.LEFT, padx=5)
category_var = tk.StringVar(value="所有")
category_dropdown = ttk.Combobox(
    filter_frame, 
    textvariable=category_var, 
    values=["所有"] + categories,
    state="readonly"  # 设置为只读模式
)
category_dropdown.pack(side=tk.LEFT, padx=5)

# 添加完成状态筛选
tk.Label(filter_frame, text="完成状态:", font=("宋体", 12)).pack(side=tk.LEFT, padx=5)
status_var = tk.StringVar(value="全部")
status_dropdown = ttk.Combobox(filter_frame, textvariable=status_var, 
                              values=["全部", "已完成", "未完成"], 
                              state="readonly", width=8)
status_dropdown.pack(side=tk.LEFT, padx=5)

# 添加优先级筛选
tk.Label(filter_frame, text="优先级:", font=("宋体", 12)).pack(side=tk.LEFT, padx=5)
priority_var = tk.StringVar(value="全部")
priority_dropdown = ttk.Combobox(filter_frame, textvariable=priority_var, 
                                values=["全部", "1", "2", "3"], 
                                state="readonly", width=8)
priority_dropdown.pack(side=tk.LEFT, padx=5)

# 查看按钮移到最后
view_button = tk.Button(filter_frame, text="查看", 
         command=lambda: refresh_tasks(category_var.get() if category_var.get() != "所有" else None), 
         width=8, height=1, font=("宋体", 12))
view_button.pack(side=tk.LEFT, padx=5)

# 创建任务列表 Treeview
columns = ("ID", "标题", "描述", "优先级", "状态", "截止日期", "分类")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    if col == columns[0]:
        tree.column(col, width=0,minwidth=0,stretch=False)
    elif col==columns[3]:
        tree.column(col, width=15)
    elif col == columns[4]:
        tree.column(col, width=15)
    elif col==columns[6]:
        tree.column(col, width=30)
    else:
        tree.column(col, width=130)
tree.pack(fill=tk.BOTH, expand=True)

# 刷新任务列表
def refresh_tasks(category=None):
    """刷新任务列表"""
    try:
        for row in tree.get_children():
            tree.delete(row)

        # 获取筛选条件
        status_filter = status_var.get()
        priority_filter = priority_var.get()

        # 获取所有任务
        tasks = list_todos(show_done=None, category=category)
        if not tasks:
            update_status("暂无任务")  # 使用全局状态栏而不是status_label
            return

        current_datetime = datetime.now()
        
        for task in tasks:
            try:
                task_id, title, description, priority, done, due_date, category = task
                
                # 应用筛选
                if status_filter in ["已完成", "Done"] and not done:
                    continue
                if status_filter in ["未完成", "Pending"] and done:
                    continue
                if priority_filter not in ["全部", "All"] and str(priority) != priority_filter:
                    continue

                # 检查是否过期
                is_overdue = False
                if not done and due_date:
                    try:
                        due_datetime = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                        if current_datetime > due_datetime:
                            is_overdue = True
                            title = f"{title}（已过期）"
                    except ValueError:
                        pass

                item = tree.insert("", tk.END, values=(
                    task_id, title, description, priority, 
                    "已完成" if done else "未完成", 
                    due_date, category
                ))
                
                if is_overdue:
                    tree.tag_configure('overdue', foreground='red')
                    tree.item(item, tags=('overdue',))
                    
            except Exception as e:
                print(f"处理任务时出错: {str(e)}")
                continue
                
    except Exception as e:
        messagebox.showerror("错误", f"刷新任务列表失败: {str(e)}")

# 加任务能
def add_task():
    def save_task():
        try:
            title = title_entry.get().strip()
            desc = desc_entry.get().strip()
            
            # 标题检查
            if not title:
                messagebox.showerror("错误", "任务标题不能为空")
                title_entry.focus()
                return
            if len(title) > 50:
                messagebox.showerror("错误", "任务标题不能超过50个字符")
                title_entry.focus()
                return
                
            # 优先级检查
            try:
                priority = priority_var.get()
                if priority not in [1, 2, 3]:
                    raise ValueError
            except:
                messagebox.showerror("错误", "优先级必须是1、2或3")
                return
                
            # 日期时间检查
            try:
                due_date = f"{date_entry.get()} {hour_var.get()}:{minute_var.get()}:{second_var.get()}"
                due_datetime = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                
                # 检查是否是过去的时间
                if due_datetime < datetime.now():
                    if not messagebox.askyesno(
                        "警告", 
                        "您设置的时间早于当前时间，是否继续？\n"
                        f"前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"设置时间：{due_date}"
                    ):
                        return
            except ValueError:
                messagebox.showerror("错误", "日期时间格式无效")
                return

            # 保存任务
            try:
                add_todo(title, desc, priority, due_date, category_var.get())
                messagebox.showinfo("成功", "任务已添加")
                add_window.destroy()
                refresh_tasks()
            except Exception as e:
                messagebox.showerror("错误", f"保存任务失败: {str(e)}")
                
        except Exception as e:
            messagebox.showerror("错误", f"添加任务时出错: {str(e)}")

    def toggle_voice_input():
        """切换语音输入状态"""
        try:
            if not hasattr(add_window, 'is_listening'):
                add_window.is_listening = False
                
            if not add_window.is_listening:
                # 检查麦克风权限
                try:
                    voice_input.check_microphone()
                except Exception as e:
                    messagebox.showerror("错误", f"麦克风初始化失败: {str(e)}\n请检查麦克风权限和连")
                    return
                    
                # 开始录音
                voice_text.delete("1.0", tk.END)
                status_label.config(text="正在录音...", foreground='red')
                
                def safe_insert(text):
                    try:
                        voice_text.insert(tk.END, text + "\n")
                        voice_text.see(tk.END)
                    except tk.TclError:
                        pass
                        
                try:
                    voice_input.start_listening(
                        safe_insert,
                        update_status,
                        'zh-CN' if current_language.get() == "中文" else 'en-US'
                    )
                    voice_button.config(text=texts["add_window"]["stop_voice"])
                    add_window.is_listening = True
                except Exception as e:
                    messagebox.showerror("错误", f"启动语音输入失败: {str(e)}")
                    status_label.config(text="语音输入启动失败")
                    
            else:
                # 停止录音
                try:
                    voice_input.stop_listening()
                    voice_button.config(text=texts["add_window"]["start_voice"])
                    add_window.is_listening = False
                    status_label.config(text="录音已停止", foreground='black')
                except Exception as e:
                    messagebox.showerror("错误", f"停止语音输入失败: {str(e)}")
                    
        except Exception as e:
            messagebox.showerror("错误", f"语音输入功能出错: {str(e)}")
    
    def use_voice_text():
        """使用语音输入的文本"""
        text = voice_text.get("1.0", tk.END).strip()
        if text:
            # 根据选的目填入相应的输入框
            if target_var.get() == "title":
                title_entry.delete(0, tk.END)
                title_entry.insert(0, text)
            else:  # description
                desc_entry.delete(0, tk.END)
                desc_entry.insert(0, text)
    
    def auto_analyze_text():
        """自动分析描述内容，识别任务信息"""
        try:
            text = voice_text.get("1.0", tk.END).strip()
            if not text:
                messagebox.showwarning("警告", "请先输入或录入文本")
                return
            
            status_label.config(text="正在分析...", foreground='blue')
            voice_text.update()
            
            try:
                parser = TaskParser()
                result = parser.parse_text(text)
                
                if not result:
                    messagebox.showwarning("警告", "无法识别文本内容，请检查输入")
                    status_label.config(text="识别失败")
                    return
                    
                if not any(result.values()):
                    desc_entry.delete(0, tk.END)
                    desc_entry.insert(0, text)
                    status_label.config(text="未识别到结构化信息，已将文本填入描述框")
                    return
                
                # 更新表单显示
                _update_form_with_result(result, text)
                status_label.config(text="分析完成", foreground='green')
                
            except Exception as e:
                print(f"分析过程出错: {str(e)}")
                messagebox.showerror("错误", f"分析文本失败: {str(e)}")
                desc_entry.delete(0, tk.END)
                desc_entry.insert(0, text)
                status_label.config(text="分析出错，已将文本填入描述框")
                
        except Exception as e:
            messagebox.showerror("错误", f"自动识别功能出错: {str(e)}")
    
    def _update_form_with_result(result, original_text):
        """更新表单显示解析结果"""
        try:
            # 更新标题
            if result.get('title'):
                title_entry.delete(0, tk.END)
                title_entry.insert(0, result['title'])
                
                # 如果标题是从原文提取的，高亮显示
                if result['title'] in original_text:
                    title_entry.configure(background='#e6ffe6')  # 浅绿色背景
                    root.after(2000, lambda: title_entry.configure(background='white'))  # 2秒后恢复
            
            # 更新描述 - 只使用原始描述，不包含时间信息
            if result.get('description'):
                # 移除描述中的时间相关文本
                desc = result['description']
                time_patterns = [
                    r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?',  # 完整日期
                    r'今天|明天|后天|下周[一二三四五六日]?|下个?月',  # 相对日期
                    r'[早上午中下晚]午?\d{1,2}[点时:：]\d{1,2}分?',  # 时间
                    r'月底|月初|周末|年底|年初|春节|元旦|五一|十一'  # 特殊时间点
                ]
                for pattern in time_patterns:
                    desc = re.sub(pattern, '', desc)
                desc = re.sub(r'\s+', ' ', desc).strip()  # 清理多余空格
                
                if desc:  # 如果清理后还有内容
                    desc_entry.delete(0, tk.END)
                    desc_entry.insert(0, desc)
            elif not result.get('title'):
                # 如果没有识别出标题和描述，使用原文
                desc_entry.delete(0, tk.END)
                desc_entry.insert(0, original_text)
            
            # 更新日期时间
            if result.get('due_date'):
                try:
                    due_date = datetime.strptime(result['due_date'], '%Y-%m-%d %H:%M:%S')
                    date_entry.set_date(due_date.date())
                    hour_var.set(f"{due_date.hour:02d}")
                    minute_var.set(f"{due_date.minute:02d}")
                    second_var.set(f"{due_date.second:02d}")
                    
                    # 如果日期在24小时内，高亮显示
                    if (due_date - datetime.now()).days < 1:
                        date_entry.configure(background='#ffe6e6')
                        root.after(2000, lambda: date_entry.configure(background='white'))
                except ValueError:
                    pass
            
            # 更新分类
            if result.get('category'):
                category_var.set(result['category'])
            
            # 更新优先级
            if result.get('priority'):
                priority_var.set(result['priority'])
            
            # 显示分析结果提示
            status_label.configure(text="✓ 分析完成", foreground='green')
            root.after(2000, lambda: status_label.configure(text="", foreground='black'))
            
        except Exception as e:
            print(f"更新表单时出错: {str(e)}")
            status_label.configure(text="⚠ 更新表单时出错", foreground='red')
            root.after(2000, lambda: status_label.configure(text="", foreground='black'))
    
    # 创建添加任务窗口
    add_window = tk.Toplevel(root)
    lang = current_language.get()
    texts = TRANSLATIONS[lang]
    
    add_window.title(texts["add_window"]["title"])
    add_window.geometry("800x500")  # 增加窗口宽度以容纳语音输入部分
    center_window(add_window)
    
    # 创建左右分隔框架
    left_frame = ttk.Frame(add_window)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    right_frame = ttk.Frame(add_window)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # 侧任务输入界面
    custom_font = tkFont.Font(family="宋体", size=10)
    
    # 修改标和输入框的布局
    tk.Label(left_frame, text=texts["add_window"]["task_title"]).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
    title_entry = tk.Entry(left_frame, font=custom_font, width=30)
    title_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)

    tk.Label(left_frame, text=texts["add_window"]["description"]).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
    desc_entry = tk.Entry(left_frame, font=custom_font, width=30)
    desc_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

    tk.Label(left_frame, text=texts["add_window"]["priority"]).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
    priority_var = tk.IntVar(value=1)
    priority_dropdown = ttk.Combobox(left_frame, textvariable=priority_var, values=[1, 2, 3], 
                                   state="readonly", width=5)
    priority_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

    tk.Label(left_frame, text=texts["add_window"]["due_date"]).grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
    date_entry = DateEntry(left_frame, date_pattern='yyyy-mm-dd', width=12)
    date_entry.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)

    # 时间选择框
    time_frame = ttk.Frame(left_frame)
    time_frame.grid(row=4, column=1, padx=10, pady=10, sticky=tk.W)

    # 时间标签
    tk.Label(left_frame, text=texts["add_window"]["time"]).grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)

    # 小时选择
    hour_var = tk.StringVar(value="00")
    hour_dropdown = ttk.Combobox(time_frame, textvariable=hour_var, 
                                values=[f"{i:02d}" for i in range(24)],
                                width=5, state="readonly")
    hour_dropdown.pack(side=tk.LEFT, padx=2)
    tk.Label(time_frame, text=texts["add_window"]["hour"]).pack(side=tk.LEFT, padx=1)

    # 分钟选择
    minute_var = tk.StringVar(value="00")
    minute_dropdown = ttk.Combobox(time_frame, textvariable=minute_var,
                                  values=[f"{i:02d}" for i in range(60)],
                                  width=5, state="readonly")
    minute_dropdown.pack(side=tk.LEFT, padx=2)
    tk.Label(time_frame, text=texts["add_window"]["minute"]).pack(side=tk.LEFT, padx=1)

    # 秒选择
    second_var = tk.StringVar(value="00")
    second_dropdown = ttk.Combobox(time_frame, textvariable=second_var,
                                  values=[f"{i:02d}" for i in range(60)],
                                  width=5, state="readonly")
    second_dropdown.pack(side=tk.LEFT, padx=2)
    tk.Label(time_frame, text=texts["add_window"]["second"]).pack(side=tk.LEFT, padx=1)

    tk.Label(left_frame, text=texts["add_window"]["category"]).grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
    category_var = tk.StringVar(value=texts["categories"][-1])
    category_dropdown = ttk.Combobox(left_frame, textvariable=category_var, 
                                   values=texts["categories"], width=15)
    category_dropdown.grid(row=5, column=1, padx=10, pady=10, sticky=tk.W)

    # 右侧语音输入界面
    voice_frame = ttk.LabelFrame(right_frame, text=texts["add_window"]["voice_input"])
    voice_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 态标签
    status_label = ttk.Label(voice_frame, text="")
    status_label.pack(fill=tk.X, padx=5, pady=2)
    
    # 语音输入文本框
    voice_text = tk.Text(voice_frame, height=15, width=40, font=custom_font)
    voice_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(voice_frame, command=voice_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    voice_text.config(yscrollcommand=scrollbar.set)
    
    # 钮框架
    button_frame = ttk.Frame(voice_frame)
    button_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def update_status(status_text):
        """更新状态标签"""
        try:
            status_label.config(text=status_text)
        except tk.TclError:
            pass
    
    # 语音输入按钮
    voice_input = VoiceInput()
    voice_button = ttk.Button(
        button_frame,
        text=texts["add_window"]["start_voice"],
        command=toggle_voice_input
    )
    voice_button.pack(side=tk.LEFT, padx=5)
    
    # 使用语音文本按钮
    use_text_button = ttk.Button(
        button_frame,
        text=texts["add_window"]["use_voice"],
        command=use_voice_text
    )
    use_text_button.pack(side=tk.LEFT, padx=5)
    
    # 自动识别按钮
    analyze_button = ttk.Button(
        button_frame,
        text=texts["add_window"]["auto_analyze"],
        command=auto_analyze_text
    )
    analyze_button.pack(side=tk.LEFT, padx=5)
    
    # 添加一个变量来跟踪当前选择的输入目标
    target_var = tk.StringVar(value="description")  # 默认填入描述
    
    # 在按钮框架中添加单选按钮
    target_frame = ttk.Frame(voice_frame)
    target_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Radiobutton(
        target_frame,
        text=texts["add_window"]["task_title"],
        variable=target_var,
        value="title"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Radiobutton(
        target_frame,
        text=texts["add_window"]["description"],
        variable=target_var,
        value="description"
    ).pack(side=tk.LEFT, padx=5)
    
    # 创建一个框架来纳保存按钮，以实现居中效果
    save_button_frame = ttk.Frame(left_frame)
    save_button_frame.grid(row=6, column=0, columnspan=2, pady=20)
    
    # 配置save_button_frame的列权重以实现居中效果
    save_button_frame.columnconfigure(0, weight=1)

    save_button = ttk.Button(
        save_button_frame, 
        text=texts["add_window"]["save"], 
        command=save_task,
        width=15
    )
    save_button.grid(row=0, column=0)  # 使用grid而不是pack

    # 配置add_window的列权重
    add_window.columnconfigure(1, weight=1)

    # 窗口关闭时停止语音输入
    def on_closing():
        voice_input.stop_listening()  # 确保停止语音输入
        add_window.destroy()
    
    add_window.protocol("WM_DELETE_WINDOW", on_closing)

# 更新任务状态功能
def mark_done():
    lang = current_language.get()
    texts = TRANSLATIONS[lang]
    
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning(texts["messages"]["warning"], 
                             texts["messages"]["select_task"])
        return

    # 添加确认对话框
    task_title = tree.item(selected_item)["values"][1]  # 获取任务标题
    confirm_message = texts["messages"]["confirm_mark_done"].format(task_title)
    if messagebox.askyesno(texts["messages"]["confirm"], confirm_message):
        task_id = tree.item(selected_item)["values"][0]
        update_todo(task_id, True)
        messagebox.showinfo(texts["messages"]["success"], 
                          texts["messages"]["task_marked"])
        refresh_tasks()

# 删除任务功能
def delete_task():
    lang = current_language.get()
    texts = TRANSLATIONS[lang]
    
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning(texts["messages"]["warning"], 
                             texts["messages"]["select_task"])
        return

    # 添加确认对话框
    task_title = tree.item(selected_item)["values"][1]  # 获取任务标题
    confirm_message = texts["messages"]["confirm_delete"].format(task_title)
    if messagebox.askyesno(texts["messages"]["confirm"], confirm_message):
        task_id = tree.item(selected_item)["values"][0]
        delete_todo(task_id)
        messagebox.showinfo(texts["messages"]["success"], 
                          texts["messages"]["task_deleted"])
        refresh_tasks()

# 修改按功能区的代
button_frame = ttk.Frame(root, style="TFrame")
button_frame.pack(fill=tk.X, padx=10, pady=5)
button_frame.grid_columnconfigure(0, weight=1)
button_frame.grid_columnconfigure(1, weight=1)
button_frame.grid_columnconfigure(2, weight=1)
button_frame.grid_columnconfigure(3, weight=1)
button_frame.grid_columnconfigure(4, weight=1)

# 使用默认样式创建按钮
ttk.Button(
    button_frame, 
    text="添加任务", 
    command=add_task
).grid(row=0, column=0, padx=5, pady=5)

ttk.Button(
    button_frame, 
    text="标记为完成", 
    command=mark_done
).grid(row=0, column=1, padx=5, pady=5)

ttk.Button(
    button_frame, 
    text="删除任务", 
    command=delete_task
).grid(row=0, column=2, padx=5, pady=5)

ttk.Button(
    button_frame, 
    text="刷新列表", 
    command=refresh_tasks
).grid(row=0, column=3, padx=5, pady=5)

ttk.Button(
    button_frame, 
    text="生成统计图", 
    command=generate_statistics
).grid(row=0, column=4, padx=5, pady=5)

# 在button_frame中添加AI提建议按钮
ttk.Button(
    button_frame, 
    text="AI提建议", 
    command=lambda: show_ai_advice()
).grid(row=0, column=5, padx=5, pady=5)

def show_ai_advice():
    """显示AI建议"""
    # 创建加载窗口
    loading_window = tk.Toplevel(root)
    loading_window.title("正在分析")
    loading_window.geometry("300x150")  # 增加加载窗口大小
    center_window(loading_window)
    
    tk.Label(
        loading_window, 
        text="AI正在分析数据，请稍等...",
        wraplength=250  # 增加文本换行宽度
    ).pack(expand=True)
    
    def get_advice():
        advisor = AIAdvisor()
        advice = advisor.get_task_analysis()
        
        loading_window.destroy()
        
        # 显示建议窗口
        advice_window = tk.Toplevel(root)
        advice_window.title("AI建议")
        advice_window.geometry("600x400")  # 增加建议窗口大小
        center_window(advice_window)
        
        # 创建文本框显示建议
        text_widget = tk.Text(advice_window, wrap=tk.WORD, padx=20, pady=20)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, advice)
        text_widget.config(state=tk.DISABLED, font=("宋体", 12))  # 设置更大的字体
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(advice_window, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
    
    import threading
    threading.Thread(target=get_advice).start()

# 添加全局错误处理
def show_error(title, message):
    """显示错误消息"""
    messagebox.showerror(title, message)

def show_warning(title, message):
    """显示警告消息"""
    messagebox.showwarning(title, message)

def show_info(title, message):
    """显示信息消息"""
    messagebox.showinfo(title, message)

# 添加状态栏
status_bar = ttk.Label(root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

def update_status(message):
    """更新状态栏消息"""
    status_bar.config(text=message)

# 添加快捷键
root.bind('<Control-n>', lambda e: add_task())
root.bind('<Control-r>', lambda e: refresh_tasks())
root.bind('<Delete>', lambda e: delete_task())

# 在创建窗口后添加图标设置（在主窗口创建之后，但在mainloop之前）
calendar_button = ttk.Button(
    root,
    text="📅",  # 使用日历emoji作为默认图标 
    command=toggle_calendar,
    width=3
)
calendar_button.pack(in_=top_frame, side=tk.RIGHT, padx=5)

# 启动程序
refresh_tasks()
root.mainloop()
