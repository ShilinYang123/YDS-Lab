
# 这个文件是正确的代码
def safe_divide(a, b):
    """安全的除法函数"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b

def safe_get_first(items):
    """安全获取列表第一个元素"""
    if not items:
        return None
    return items[0]

if __name__ == "__main__":
    print("测试代码运行正常")
