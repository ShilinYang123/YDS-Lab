"""
TraeMate 主应用程序
重构版本的主入口文件
"""
import sys
import os
import tkinter as tk
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data.config_manager import ConfigManager
from src.data.log_manager import LogManager
from src.business.monitor_manager import MonitorManager, MonitorState
from src.business.handler_manager import HandlerManager
from src.ui.status_bar import StatusBar
from src.ui.system_tray import SystemTray
from src.ui.dialogs import ConfigDialog, LogsDialog


class TraeMateApp:
    """TraeMate主应用程序类"""
    
    def __init__(self):
        """初始化应用程序"""
        # 初始化数据层
        self.config_manager = ConfigManager()
        self.log_manager = LogManager()
        
        # 初始化业务层
        self.monitor_manager = MonitorManager(self.config_manager, self.log_manager)
        self.handler_manager = HandlerManager(self.config_manager, self.log_manager)
        
        # 初始化UI组件
        self.root = None
        self.status_bar = None
        self.system_tray = None
        
        # 应用程序状态
        self.is_running = False
        self.is_closing = False
        
        # 初始化日志
        self.log_manager.info("TraeMate 启动")
        
        # 创建UI
        self._create_ui()
        
        # 设置回调
        self._setup_callbacks()
    
    def _create_ui(self) -> None:
        """创建用户界面"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("TraeMate")
        self.root.overrideredirect(True)  # 无边框窗口
        
        # 设置窗口属性
        self._setup_window()
        
        # 创建状态栏
        self.status_bar = StatusBar(self.root, self.config_manager, self.log_manager)
        
        # 创建系统托盘
        self.system_tray = SystemTray(self.config_manager, self.log_manager)
    
    def _setup_window(self) -> None:
        """设置窗口属性"""
        config = self.config_manager.get_config()
        window_config = config.get("window", {})
        
        # 设置窗口大小和位置
        width = window_config.get("width", 420)
        height = window_config.get("height", 32)
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 计算窗口位置（屏幕顶部中央）
        x = (screen_width - width) // 2
        y = 0
        
        # 设置窗口几何属性
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # 设置窗口背景色
        bg_color = window_config.get("bg_color", "#2c3553")
        self.root.configure(bg=bg_color)
        
        # 设置窗口透明度
        alpha = window_config.get("alpha", 0.7)
        self.root.attributes("-alpha", alpha)
        
        # 设置窗口置顶
        self.root.attributes("-topmost", True)
        
        # 绑定窗口事件
        self.root.bind("<Button-1>", self._on_window_click)
        self.root.bind("<B1-Motion>", self._on_window_drag)
        self.root.bind("<Button-3>", self._on_right_click)  # 右键菜单
        
        # 记录拖动起始位置
        self.drag_start_x = 0
        self.drag_start_y = 0
    
    def _setup_callbacks(self) -> None:
        """设置回调函数"""
        # 监控管理器状态变化回调
        self.monitor_manager.set_state_change_callback(self._on_monitor_state_change)
        self.monitor_manager.set_indicator_callback(self.status_bar.set_indicator_state)
        
        # 系统托盘回调
        self.system_tray.set_callbacks(
            on_start=self.start_monitoring,
            on_stop=self.stop_monitoring,
            on_config=self.show_config_dialog,
            on_logs=self.show_logs_dialog,
            on_quit=self.quit_app
        )
        
        # 状态栏回调
        self.status_bar.set_callbacks(
            on_toggle=self.toggle_monitoring,
            on_config=self.show_config_dialog,
            on_quit=self.quit_app
        )
    
    def run(self) -> None:
        """运行应用程序"""
        try:
            # 启动系统托盘
            self.system_tray.start()
            
            # 显示主窗口
            self.root.mainloop()
        
        except Exception as e:
            self.log_manager.error(f"应用程序运行异常: {e}")
            raise
        
        finally:
            # 清理资源
            self._cleanup()
    
    def _cleanup(self) -> None:
        """清理资源"""
        try:
            # 停止监控
            if self.monitor_manager.is_running():
                self.monitor_manager.stop_monitoring()
            
            # 停止系统托盘
            if self.system_tray:
                self.system_tray.stop()
            
            self.log_manager.info("TraeMate 关闭")
        
        except Exception as e:
            print(f"清理资源时出错: {e}")
    
    def _on_window_click(self, event) -> None:
        """窗口点击事件"""
        # 记录拖动起始位置
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def _on_window_drag(self, event) -> None:
        """窗口拖动事件"""
        # 计算新位置
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        
        # 限制窗口在屏幕范围内
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = self.root.winfo_width()
        window_height = self.root.winfo_height()
        
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))
        
        # 移动窗口
        self.root.geometry(f"+{x}+{y}")
    
    def _on_right_click(self, event) -> None:
        """右键点击事件"""
        # 显示上下文菜单
        menu = tk.Menu(self.root, tearoff=0)
        
        if self.monitor_manager.is_running():
            menu.add_command(label="停止监控", command=self.stop_monitoring)
        else:
            menu.add_command(label="开始监控", command=self.start_monitoring)
        
        menu.add_separator()
        menu.add_command(label="配置", command=self.show_config_dialog)
        menu.add_command(label="日志", command=self.show_logs_dialog)
        menu.add_separator()
        menu.add_command(label="退出", command=self.quit_app)
        
        # 显示菜单
        menu.post(event.x_root, event.y_root)
    
    def _on_monitor_state_change(self, state: MonitorState) -> None:
        """监控状态变化回调"""
        self.is_running = (state == MonitorState.RUNNING)
        
        # 更新系统托盘
        if self.system_tray:
            self.system_tray.update_state(self.is_running)
        
        # 更新状态栏
        if self.status_bar:
            self.status_bar.update_state(state)
    
    def start_monitoring(self) -> None:
        """开始监控"""
        if not self.monitor_manager.is_running():
            self.monitor_manager.start_monitoring()
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        if self.monitor_manager.is_running():
            self.monitor_manager.stop_monitoring()
    
    def toggle_monitoring(self) -> None:
        """切换监控状态"""
        if self.monitor_manager.is_running():
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def show_config_dialog(self) -> None:
        """显示配置对话框"""
        config = self.config_manager.get_config()
        dialog = ConfigDialog(self.root, config, self._on_config_saved)
        self.root.wait_window(dialog.dialog)
    
    def _on_config_saved(self, config) -> None:
        """配置保存回调"""
        # 更新配置
        self.config_manager.set_config(config)
        self.config_manager.save_config()
        
        # 重新加载配置
        self.monitor_manager.reload_config()
        
        # 更新窗口设置
        self._setup_window()
        
        # 更新状态栏
        if self.status_bar:
            self.status_bar.reload_config()
        
        self.log_manager.info("配置已更新")
    
    def show_logs_dialog(self) -> None:
        """显示日志对话框"""
        dialog = LogsDialog(self.root, self.log_manager)
    
    def quit_app(self) -> None:
        """退出应用程序"""
        if self.is_closing:
            return
        
        self.is_closing = True
        
        # 停止监控
        if self.monitor_manager.is_running():
            self.monitor_manager.stop_monitoring()
        
        # 关闭主窗口
        if self.root:
            self.root.quit()


def main():
    """主函数"""
    try:
        # 创建并运行应用程序
        app = TraeMateApp()
        app.run()
    
    except KeyboardInterrupt:
        print("用户中断")
    
    except Exception as e:
        print(f"应用程序异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 确保程序退出
        sys.exit(0)


if __name__ == "__main__":
    main()