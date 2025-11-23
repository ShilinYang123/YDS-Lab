"""
进程监控服务模块
负责检测指定进程是否在运行
"""
import psutil
from typing import List, Optional
from src.data.log_manager import LogManager


class ProcessMonitorService:
    """进程监控服务，负责检测指定进程是否在运行"""
    
    def __init__(self, process_names: List[str] = None):
        """
        初始化进程监控服务
        
        Args:
            process_names: 要监控的进程名称列表
        """
        self.process_names = process_names or []
        self.logger = LogManager()
    
    def set_process_names(self, process_names: List[str]) -> None:
        """
        设置要监控的进程名称列表
        
        Args:
            process_names: 进程名称列表
        """
        self.process_names = process_names
        self.logger.info(f"监控进程列表已更新: {', '.join(process_names)}")
    
    def add_process_name(self, process_name: str) -> None:
        """
        添加要监控的进程名称
        
        Args:
            process_name: 进程名称
        """
        if process_name not in self.process_names:
            self.process_names.append(process_name)
            self.logger.info(f"已添加监控进程: {process_name}")
    
    def remove_process_name(self, process_name: str) -> bool:
        """
        移除要监控的进程名称
        
        Args:
            process_name: 进程名称
            
        Returns:
            是否成功移除
        """
        if process_name in self.process_names:
            self.process_names.remove(process_name)
            self.logger.info(f"已移除监控进程: {process_name}")
            return True
        return False
    
    def is_process_running(self, process_name: str) -> bool:
        """
        检查指定进程是否在运行
        
        Args:
            process_name: 进程名称
            
        Returns:
            进程是否在运行
        """
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # 检查进程名是否匹配（不区分大小写）
                    if process_name.lower() in proc.info['name'].lower():
                        self.logger.debug(f"找到运行中的进程: {proc.info['name']} (PID: {proc.info['pid']})")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            self.logger.debug(f"未找到运行中的进程: {process_name}")
            return False
        except Exception as e:
            self.logger.error(f"检查进程 {process_name} 时出错: {e}")
            return False
    
    def is_any_monitored_process_running(self) -> bool:
        """
        检查是否有任何被监控的进程在运行
        
        Returns:
            是否有被监控的进程在运行
        """
        if not self.process_names:
            self.logger.warning("没有设置要监控的进程")
            return False
        
        for process_name in self.process_names:
            if self.is_process_running(process_name):
                self.logger.info(f"检测到监控进程在运行: {process_name}")
                return True
        
        self.logger.info("没有检测到任何监控进程在运行")
        return False
    
    def get_running_monitored_processes(self) -> List[str]:
        """
        获取当前正在运行的被监控进程列表
        
        Returns:
            正在运行的进程名称列表
        """
        running_processes = []
        
        for process_name in self.process_names:
            if self.is_process_running(process_name):
                running_processes.append(process_name)
        
        return running_processes
    
    def get_process_info(self, process_name: str) -> Optional[dict]:
        """
        获取指定进程的详细信息
        
        Args:
            process_name: 进程名称
            
        Returns:
            进程信息字典，未找到时返回None
        """
        try:
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        # 获取更详细的信息
                        with proc.oneshot():
                            return {
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'username': proc.info['username'],
                                'cpu_percent': proc.info['cpu_percent'],
                                'memory_percent': proc.info['memory_percent'],
                                'status': proc.status(),
                                'create_time': proc.create_time(),
                                'exe': proc.exe(),
                                'cwd': proc.cwd()
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"获取进程 {process_name} 信息时出错: {e}")
            return None
    
    def kill_process(self, process_name: str) -> bool:
        """
        终止指定进程
        
        Args:
            process_name: 进程名称
            
        Returns:
            是否成功终止
        """
        try:
            killed = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if process_name.lower() in proc.info['name'].lower():
                        proc.terminate()
                        killed = True
                        self.logger.info(f"已终止进程: {proc.info['name']} (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            return killed
        except Exception as e:
            self.logger.error(f"终止进程 {process_name} 时出错: {e}")
            return False
    
    def update_config(self, config: dict) -> None:
        """
        更新服务配置
        
        Args:
            config: 配置字典，包含process_names等参数
        """
        if "process_names" in config:
            self.set_process_names(config["process_names"])
            
        self.logger.info(f"ProcessMonitorService配置已更新: {config}")