import os
import datetime

def log_to_general_office(message, category="info"):
    """
    简单的日志记录函数
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{category.upper()}] {message}"
    
    # 打印到控制台
    print(log_message)
    
    # 可选：写入日志文件
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{category}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")