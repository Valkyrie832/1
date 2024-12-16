import argparse
from commands import add_todo, list_todos, update_todo, delete_todo
from database import init_db
from apscheduler.schedulers.background import BackgroundScheduler
from commands import remind_todos

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="命令行待办事项管理系统")
    subparsers = parser.add_subparsers(dest="command")

    # 添加任务子命令
    add_parser = subparsers.add_parser("add", help="添加待办事项")
    add_parser.add_argument("--title", required=True, help="任务标题")
    add_parser.add_argument("--desc", default="", help="任务描述")
    add_parser.add_argument("--priority", type=int, default=1, help="优先级 (1-3)")
    add_parser.add_argument("--due_date", default=None, help="任务截止日期 (格式：YYYY-MM-DD HH:MM:SS)")

    # 查看任务子命令
    list_parser = subparsers.add_parser("list", help="列出待办事项")
    list_parser.add_argument(
        "--done",
        type=int,
        choices=[0, 1],
        default=None,
        help="筛选完成状态 (0 = 未完成, 1 = 已完成)"
    )

    # 更新任务状态子命令
    update_parser = subparsers.add_parser("update", help="更新任务状态")
    update_parser.add_argument("--id", type=int, required=True, help="任务 ID")
    update_parser.add_argument("--done", type=int, choices=[0, 1], required=True, help="完成状态 (0 = 未完成, 1 = 已完成)")

    # 删除任务子命令
    delete_parser = subparsers.add_parser("delete", help="删除待办事项")
    delete_parser.add_argument("--id", type=int, required=True, help="任务 ID")

    #提醒即将到期的任务子命令
    remind_parser = subparsers.add_parser("remind", help="启动任务提醒服务")

    return parser.parse_args()  # 返回解析后的命令行参数

def start_reminder():
    """
    启动任务提醒服务。
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(remind_todos, 'interval', minutes=1)  # 每分钟检查一次
    scheduler.start()
    print("任务提醒服务已启动，按 Ctrl+C 停止。")

    try:
        while True:
            pass  # 保持进程运行
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    # 初始化数据库（创建表格）
    init_db()

    # 解析命令行参数
    args = parse_args()

    # 根据用户输入的子命令调用相应功能
    if args.command == "add":
        add_todo(args.title, args.desc, args.priority, args.due_date)
    elif args.command == "list":
        list_todos(args.done)
    elif args.command == "update":
        update_todo(args.id, args.done)
    elif args.command == "delete":
        delete_todo(args.id)
    elif args.command == "remind":
        start_reminder()

    else:
        print("未知命令，请使用 --help 查看帮助信息。")
