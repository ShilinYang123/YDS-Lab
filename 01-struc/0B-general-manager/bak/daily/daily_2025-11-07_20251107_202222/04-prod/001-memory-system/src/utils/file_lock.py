import os
import time
import errno

class FileLockException(Exception):
    pass

class FileLock:
    """ A file locking mechanism that has context-manager support so you can use it in a with statement.
    This should be relatively cross-platform since it doesn't rely on fcntl.
    """

    def __init__(self, file_path, timeout=10, delay=.05):
        """ Prepare the file lock. Specify the file path, the timeout, and the delay between each attempt to lock.
        """
        self.is_locked = False
        # 将锁文件放置在目标文件所在目录，确保不同工作目录的进程也能共享同一个锁
        abs_target = os.path.abspath(file_path)
        target_dir = os.path.dirname(abs_target)
        base_name = os.path.basename(abs_target)
        self.lockfile = os.path.join(target_dir, f"{base_name}.lock")
        self.file_path = abs_target
        self.timeout = timeout
        self.delay = delay

    def acquire(self):
        """ Acquire the lock, waiting until it is obtained or timeout is reached.
        """
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                # 通过创建锁文件实现互斥；O_EXCL确保并发情况下只有一个进程能成功创建
                self.fd = os.open(self.lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                self.is_locked = True
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                time.sleep(self.delay)
        if not self.is_locked:
            raise FileLockException(f"Could not acquire lock on {self.file_path} within {self.timeout} seconds.")

    def release(self):
        """ Release the lock by deleting the lock file.
        """
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False

    def __enter__(self):
        """ Activated when used in the with statement. Should lock the file.
        """
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement. It automatically releases the lock.
        """
        if self.is_locked:
            self.release()

    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile lying around.
        """
        self.release()