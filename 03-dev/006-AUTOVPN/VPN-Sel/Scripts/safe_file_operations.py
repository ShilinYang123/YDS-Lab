def atomic_write(file_path, mode, content):
    with open(file_path, mode) as f:
        f.write(content)
