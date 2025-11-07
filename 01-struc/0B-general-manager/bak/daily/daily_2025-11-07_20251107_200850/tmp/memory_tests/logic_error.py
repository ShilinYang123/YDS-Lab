
# 这个文件包含逻辑错误
def divide_numbers(a, b):
    # 没有检查除零错误
    result = a / b
    return result

def process_list(items):
    # 可能的索引越界错误
    first_item = items[0]  # 没有检查列表是否为空
    return first_item
