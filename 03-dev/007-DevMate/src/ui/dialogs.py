"""
对话框组件
负责配置对话框和日志查看对话框
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from typing import Callable, Dict, Any, Optional, List
from src.data.log_manager import LogManager


class ConfigDialog:
    """配置对话框组件"""
    
    def __init__(self, parent, config: Dict[str, Any], on_save: Callable = None):
        """
        初始化配置对话框
        
        Args:
            parent: 父窗口
            config: 当前配置
            on_save: 保存回调函数
        """
        self.parent = parent
        self.config = config.copy()  # 创建配置副本
        self.on_save = on_save
        self.logger = LogManager()
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("配置")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_window()
        
        # 创建UI
        self._create_ui()
    
    def _center_window(self) -> None:
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_ui(self) -> None:
        """创建UI组件"""
        # 创建笔记本控件用于分组
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 基本设置选项卡
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="基本设置")
        self._create_general_tab(general_frame)
        
        # 监控设置选项卡
        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text="监控设置")
        self._create_monitor_tab(monitor_frame)
        
        # 检测设置选项卡
        detection_frame = ttk.Frame(notebook)
        notebook.add(detection_frame, text="检测设置")
        self._create_detection_tab(detection_frame)
        
        # 自定义处理项选项卡
        handlers_frame = ttk.Frame(notebook)
        notebook.add(handlers_frame, text="自定义处理项")
        self._create_handlers_tab(handlers_frame)
        
        # 按钮区域
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_frame, text="保存", command=self._on_save).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="取消", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)
    
    def _create_general_tab(self, parent) -> None:
        """创建基本设置选项卡"""
        # 窗口宽度
        tk.Label(parent, text="窗口宽度:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.width_var = tk.IntVar(value=self.config.get("window", {}).get("width", 420))
        tk.Scale(parent, from_=200, to=800, orient=tk.HORIZONTAL, variable=self.width_var, 
                length=200).grid(row=0, column=1, padx=10, pady=5)
        
        # 窗口高度
        tk.Label(parent, text="窗口高度:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.height_var = tk.IntVar(value=self.config.get("window", {}).get("height", 32))
        tk.Scale(parent, from_=20, to=100, orient=tk.HORIZONTAL, variable=self.height_var,
                length=200).grid(row=1, column=1, padx=10, pady=5)
        
        # 背景颜色
        tk.Label(parent, text="背景颜色:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.bg_color_var = tk.StringVar(value=self.config.get("window", {}).get("bg_color", "#2c3553"))
        tk.Entry(parent, textvariable=self.bg_color_var, width=20).grid(row=2, column=1, padx=10, pady=5)
        
        # 透明度
        tk.Label(parent, text="透明度:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.alpha_var = tk.DoubleVar(value=self.config.get("window", {}).get("alpha", 0.7))
        tk.Scale(parent, from_=0.1, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, 
                variable=self.alpha_var, length=200).grid(row=3, column=1, padx=10, pady=5)
        
        # 指示器大小
        tk.Label(parent, text="指示器大小:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        self.indicator_size_var = tk.IntVar(value=self.config.get("indicator", {}).get("size", 14))
        tk.Scale(parent, from_=8, to=30, orient=tk.HORIZONTAL, variable=self.indicator_size_var,
                length=200).grid(row=4, column=1, padx=10, pady=5)
    
    def _create_monitor_tab(self, parent) -> None:
        """创建监控设置选项卡"""
        # 监控间隔
        tk.Label(parent, text="监控间隔(秒):").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.interval_var = tk.DoubleVar(value=self.config.get("monitor", {}).get("interval_seconds", 2.0))
        tk.Scale(parent, from_=0.5, to=10.0, resolution=0.5, orient=tk.HORIZONTAL,
                variable=self.interval_var, length=200).grid(row=0, column=1, padx=10, pady=5)
        
        # 冷却时间
        tk.Label(parent, text="冷却时间(秒):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.cooldown_var = tk.IntVar(value=self.config.get("monitor", {}).get("cooldown_seconds", 30))
        tk.Scale(parent, from_=5, to=120, orient=tk.HORIZONTAL, variable=self.cooldown_var,
                length=200).grid(row=1, column=1, padx=10, pady=5)
        
        # 进程名称
        tk.Label(parent, text="监控进程:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        process_names = self.config.get("monitor", {}).get("process_names", ["trae", "cursor"])
        self.process_var = tk.StringVar(value=", ".join(process_names))
        tk.Entry(parent, textvariable=self.process_var, width=30).grid(row=2, column=1, padx=10, pady=5)
        
        # 跳过进程检查
        self.skip_process_var = tk.BooleanVar(value=self.config.get("monitor", {}).get("skip_process_check", False))
        tk.Checkbutton(parent, text="跳过进程检查", variable=self.skip_process_var).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
    
    def _create_detection_tab(self, parent) -> None:
        """创建检测设置选项卡"""
        # 缩放因子
        tk.Label(parent, text="图像缩放因子:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.scale_var = tk.DoubleVar(value=self.config.get("detection", {}).get("scale_factor", 1.0))
        tk.Scale(parent, from_=0.5, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                variable=self.scale_var, length=200).grid(row=0, column=1, padx=10, pady=5)
        
        # 主按钮阈值
        tk.Label(parent, text="主按钮阈值:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.threshold_main_var = tk.DoubleVar(value=self.config.get("detection", {}).get("threshold_main", 0.6))
        tk.Scale(parent, from_=0.3, to=0.9, resolution=0.05, orient=tk.HORIZONTAL,
                variable=self.threshold_main_var, length=200).grid(row=1, column=1, padx=10, pady=5)
        
        # 处理项阈值
        tk.Label(parent, text="处理项阈值:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.threshold_handlers_var = tk.DoubleVar(value=self.config.get("detection", {}).get("threshold_handlers", 0.85))
        tk.Scale(parent, from_=0.5, to=0.95, resolution=0.05, orient=tk.HORIZONTAL,
                variable=self.threshold_handlers_var, length=200).grid(row=2, column=1, padx=10, pady=5)
    
    def _create_handlers_tab(self, parent) -> None:
        """创建自定义处理项选项卡"""
        # 处理项列表
        list_frame = tk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 列表框和滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.handlers_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.handlers_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.handlers_listbox.yview)
        
        # 添加处理项
        handlers = self.config.get("custom_handlers", [])
        for handler in handlers:
            self.handlers_listbox.insert(tk.END, f"{handler.get('name', '')} - {handler.get('description', '')}")
        
        # 按钮区域
        button_frame = tk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_frame, text="添加", command=self._add_handler).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="编辑", command=self._edit_handler).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="删除", command=self._delete_handler).pack(side=tk.LEFT, padx=5)
    
    def _add_handler(self) -> None:
        """添加自定义处理项"""
        dialog = HandlerDialog(self.dialog, None)
        self.dialog.wait_window(dialog.dialog)
        
        if dialog.result:
            self.config.setdefault("custom_handlers", []).append(dialog.result)
            self.handlers_listbox.insert(tk.END, f"{dialog.result.get('name', '')} - {dialog.result.get('description', '')}")
    
    def _edit_handler(self) -> None:
        """编辑自定义处理项"""
        selection = self.handlers_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的处理项")
            return
        
        index = selection[0]
        handlers = self.config.get("custom_handlers", [])
        if index < len(handlers):
            handler = handlers[index]
            dialog = HandlerDialog(self.dialog, handler)
            self.dialog.wait_window(dialog.dialog)
            
            if dialog.result:
                handlers[index] = dialog.result
                self.handlers_listbox.delete(index)
                self.handlers_listbox.insert(index, f"{dialog.result.get('name', '')} - {dialog.result.get('description', '')}")
    
    def _delete_handler(self) -> None:
        """删除自定义处理项"""
        selection = self.handlers_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的处理项")
            return
        
        index = selection[0]
        handlers = self.config.get("custom_handlers", [])
        if index < len(handlers):
            del handlers[index]
            self.handlers_listbox.delete(index)
    
    def _on_save(self) -> None:
        """保存配置"""
        # 更新配置
        self.config["window"]["width"] = self.width_var.get()
        self.config["window"]["height"] = self.height_var.get()
        self.config["window"]["bg_color"] = self.bg_color_var.get()
        self.config["window"]["alpha"] = self.alpha_var.get()
        
        self.config["indicator"]["size"] = self.indicator_size_var.get()
        
        self.config["monitor"]["interval_seconds"] = self.interval_var.get()
        self.config["monitor"]["cooldown_seconds"] = self.cooldown_var.get()
        self.config["monitor"]["process_names"] = [name.strip() for name in self.process_var.get().split(",")]
        self.config["monitor"]["skip_process_check"] = self.skip_process_var.get()
        
        self.config["detection"]["scale_factor"] = self.scale_var.get()
        self.config["detection"]["threshold_main"] = self.threshold_main_var.get()
        self.config["detection"]["threshold_handlers"] = self.threshold_handlers_var.get()
        
        # 调用保存回调
        if self.on_save:
            self.on_save(self.config)
        
        self.dialog.destroy()
    
    def _on_cancel(self) -> None:
        """取消保存"""
        self.dialog.destroy()


class HandlerDialog:
    """处理项编辑对话框"""
    
    def __init__(self, parent, handler: Optional[Dict[str, Any]] = None):
        """
        初始化处理项对话框
        
        Args:
            parent: 父窗口
            handler: 要编辑的处理项，如果为None则创建新处理项
        """
        self.parent = parent
        self.handler = handler.copy() if handler else {}
        self.result = None
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑处理项" if handler else "添加处理项")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_window()
        
        # 创建UI
        self._create_ui()
    
    def _center_window(self) -> None:
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_ui(self) -> None:
        """创建UI组件"""
        # 名称
        tk.Label(self.dialog, text="名称:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.name_var = tk.StringVar(value=self.handler.get("name", ""))
        tk.Entry(self.dialog, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=10, pady=5)
        
        # 描述
        tk.Label(self.dialog, text="描述:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.description_var = tk.StringVar(value=self.handler.get("description", ""))
        tk.Entry(self.dialog, textvariable=self.description_var, width=30).grid(row=1, column=1, padx=10, pady=5)
        
        # 图像文件
        tk.Label(self.dialog, text="图像文件:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        image_frame = tk.Frame(self.dialog)
        image_frame.grid(row=2, column=1, sticky=tk.W+tk.E, padx=10, pady=5)
        
        self.image_var = tk.StringVar(value=self.handler.get("image_file", ""))
        tk.Entry(image_frame, textvariable=self.image_var, width=25).pack(side=tk.LEFT)
        tk.Button(image_frame, text="浏览", command=self._browse_image).pack(side=tk.LEFT, padx=5)
        
        # 点击偏移X
        tk.Label(self.dialog, text="点击偏移X:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        self.offset_x_var = tk.IntVar(value=self.handler.get("offset_x", 0))
        tk.Scale(self.dialog, from_=-50, to=50, orient=tk.HORIZONTAL, variable=self.offset_x_var,
                length=200).grid(row=3, column=1, padx=10, pady=5)
        
        # 点击偏移Y
        tk.Label(self.dialog, text="点击偏移Y:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        self.offset_y_var = tk.IntVar(value=self.handler.get("offset_y", 0))
        tk.Scale(self.dialog, from_=-50, to=50, orient=tk.HORIZONTAL, variable=self.offset_y_var,
                length=200).grid(row=4, column=1, padx=10, pady=5)
        
        # 是否启用
        self.enabled_var = tk.BooleanVar(value=self.handler.get("enabled", True))
        tk.Checkbutton(self.dialog, text="启用", variable=self.enabled_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
        # 按钮区域
        button_frame = tk.Frame(self.dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        tk.Button(button_frame, text="确定", command=self._on_ok).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="取消", command=self._on_cancel).pack(side=tk.RIGHT, padx=5)
    
    def _browse_image(self) -> None:
        """浏览图像文件"""
        file_path = filedialog.askopenfilename(
            title="选择图像文件",
            filetypes=[("图像文件", "*.png *.jpg *.jpeg *.bmp"), ("所有文件", "*.*")]
        )
        if file_path:
            self.image_var.set(file_path)
    
    def _on_ok(self) -> None:
        """确定按钮回调"""
        if not self.name_var.get():
            messagebox.showwarning("警告", "请输入处理项名称")
            return
        
        self.result = {
            "name": self.name_var.get(),
            "description": self.description_var.get(),
            "image_file": self.image_var.get(),
            "offset_x": self.offset_x_var.get(),
            "offset_y": self.offset_y_var.get(),
            "enabled": self.enabled_var.get()
        }
        
        self.dialog.destroy()
    
    def _on_cancel(self) -> None:
        """取消按钮回调"""
        self.dialog.destroy()


class LogsDialog:
    """日志查看对话框"""
    
    def __init__(self, parent, log_manager):
        """
        初始化日志对话框
        
        Args:
            parent: 父窗口
            log_manager: 日志管理器实例
        """
        self.parent = parent
        self.log_manager = log_manager
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("日志查看")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        
        # 居中显示
        self._center_window()
        
        # 创建UI
        self._create_ui()
        
        # 加载日志
        self._load_logs()
    
    def _center_window(self) -> None:
        """将窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_ui(self) -> None:
        """创建UI组件"""
        # 工具栏
        toolbar = tk.Frame(self.dialog)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="刷新", command=self._load_logs).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="清空日志", command=self._clear_logs).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="导出日志", command=self._export_logs).pack(side=tk.LEFT, padx=5)
        
        # 日志文本区域
        self.text_area = scrolledtext.ScrolledText(
            self.dialog,
            wrap=tk.WORD,
            width=100,
            height=30,
            font=("Consolas", 10)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = tk.Label(self.dialog, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)
    
    def _load_logs(self) -> None:
        """加载日志"""
        self.status_var.set("正在加载日志...")
        self.dialog.update()
        
        # 在后台线程中加载日志
        threading.Thread(target=self._load_logs_thread, daemon=True).start()
    
    def _load_logs_thread(self) -> None:
        """在后台线程中加载日志"""
        try:
            logs = self.log_manager.get_recent_logs(1000)
            log_text = "".join(logs)
            
            # 在主线程中更新UI
            self.dialog.after(0, self._update_log_text, log_text)
        except Exception as e:
            self.dialog.after(0, self._show_error, f"加载日志失败: {e}")
    
    def _update_log_text(self, text: str) -> None:
        """更新日志文本"""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.status_var.set(f"日志已加载，共 {len(text.splitlines())} 行")
    
    def _show_error(self, message: str) -> None:
        """显示错误消息"""
        messagebox.showerror("错误", message)
        self.status_var.set("错误")
    
    def _clear_logs(self) -> None:
        """清空日志"""
        if messagebox.askyesno("确认", "确定要清空所有日志吗？"):
            if self.log_manager.clear_logs():
                self.text_area.delete(1.0, tk.END)
                self.status_var.set("日志已清空")
            else:
                self.status_var.set("清空日志失败")
    
    def _export_logs(self) -> None:
        """导出日志"""
        file_path = filedialog.asksaveasfilename(
            title="导出日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_area.get(1.0, tk.END))
                self.status_var.set(f"日志已导出到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出日志失败: {e}")
                self.status_var.set("导出日志失败")