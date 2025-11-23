import tkinter as tk
import threading
import time
import json
import os
try:
    import pystray
    from PIL import Image
    PYSTRAY_AVAILABLE = True
except Exception:
    PYSTRAY_AVAILABLE = False
try:
    import cv2
    import numpy as np
    import pyautogui
    DETECTION_AVAILABLE = True
except Exception:
    DETECTION_AVAILABLE = False
import datetime
try:
    import psutil
    PROCESS_AVAILABLE = True
except Exception:
    PROCESS_AVAILABLE = False
import sys
from tkinter import filedialog, messagebox
from shutil import copyfile


class TraeMate:
    def __init__(self, config_path):
        self.load_config(config_path)
        self.running = True
        self.monitoring = True
        self.blink_state = False
        self.cooldown = False
        self.init_window()
        self.setup_ui()
        self.start_threads()

    def load_config(self, config_path):
        # 兼容PyInstaller打包路径
        if hasattr(sys, '_MEIPASS'):
            config_path = os.path.join(sys._MEIPASS, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        # 初始化自定义处理项
        if 'custom_handlers' not in self.config:
            self.config['custom_handlers'] = []
        # 检测配置（屏幕缩放）默认值
        if 'detection' not in self.config:
            self.config['detection'] = {'scale_factor': 1.0}

    def save_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def init_window(self):
        if hasattr(self, 'min_btn'):
            self.min_btn.destroy()
        if hasattr(self, 'close_btn'):
            self.close_btn.destroy()
        if hasattr(self, 'frame'):
            self.frame.destroy()
        cfg = self.config['window']
        self.root = tk.Tk()
        self.root.title(self.config['app_name'])
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.7)
        screen_width = self.root.winfo_screenwidth()
        window_width = 420
        window_height = 32
        r = 12
        x_position = (screen_width - window_width) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+0")
        self.bg_canvas = tk.Canvas(
            self.root,
            width=window_width,
            height=window_height,
            bg='#2c3553',
            highlightthickness=0)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.bg_canvas.create_polygon([r,
                                       0,
                                       window_width - r,
                                       0,
                                       window_width,
                                       r,
                                       window_width,
                                       window_height - r,
                                       window_width - r,
                                       window_height,
                                       r,
                                       window_height,
                                       0,
                                       window_height - r,
                                       0,
                                       r],
                                      smooth=True,
                                      fill='#2c3553',
                                      outline='')
        self.frame = tk.Frame(self.bg_canvas, bg='#2c3553')
        self.bg_canvas.create_window(
            window_width // 2,
            window_height // 2,
            window=self.frame,
            anchor='center')
        self.status_label = tk.Label(
            self.frame,
            text="Trae状态监控中...",
            fg="#F8F8F8",
            bg="#2c3553",
            font=("微软雅黑", 9)
        )
        self.status_label.pack(side=tk.LEFT, padx=6)
        self.indicator_canvas = tk.Canvas(
            self.frame,
            width=14,
            height=14,
            bg="#2c3553",
            highlightthickness=0)
        self.indicator_canvas.pack(side=tk.LEFT, padx=2)
        self.indicator = self.indicator_canvas.create_oval(
            2, 2, 12, 12, fill="#00ff00", outline="", width=0)
        self.app_label = tk.Label(
            self.frame,
            text=f"{self.config['app_name']}  {self.config['author']}",
            fg="#F8F8F8",
            bg="#2c3553",
            font=("微软雅黑", 9)
        )
        self.app_label.pack(side=tk.RIGHT, padx=6)
        self.min_btn = tk.Label(
            self.frame,
            text="_",
            fg="#F8F8F8",
            bg="#2c3553",
            font=(
                "微软雅黑",
                9))
        self.min_btn.pack(side=tk.RIGHT, padx=2)
        self.min_btn.bind("<Button-1>", self.minimize_window)
        self.close_btn = tk.Label(
            self.frame,
            text="×",
            fg="#F8F8F8",
            bg="#2c3553",
            font=(
                "微软雅黑",
                9))
        self.close_btn.pack(side=tk.RIGHT, padx=2)
        self.close_btn.bind("<Button-1>", self.close_app)
        self.min_btn.bind(
            "<Enter>",
            lambda e: self.min_btn.config(
                bg="#3e4970"))
        self.min_btn.bind(
            "<Leave>",
            lambda e: self.min_btn.config(
                bg="#2c3553"))
        self.close_btn.bind(
            "<Enter>",
            lambda e: self.close_btn.config(
                bg="#c0392b"))
        self.close_btn.bind(
            "<Leave>",
            lambda e: self.close_btn.config(
                bg="#2c3553"))
        self.root.bind('<ButtonPress-1>', self.start_move)
        self.root.bind('<ButtonRelease-1>', self.stop_move)
        self.root.bind('<B1-Motion>', self.do_move)

    def start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def stop_move(self, event):
        self._drag_x = None
        self._drag_y = None

    def do_move(self, event):
        x = self.root.winfo_x() + event.x - (self._drag_x if hasattr(self, '_drag_x')
                                             and self._drag_x is not None else 0)
        y = self.root.winfo_y() + event.y - (self._drag_y if hasattr(self, '_drag_y')
                                             and self._drag_y is not None else 0)
        self.root.geometry(f'+{x}+{y}')

    def setup_ui(self):
        self.add_indicator_click()
        self.create_context_menu()
        # 绑定主界面右键弹出菜单
        self.root.bind("<Button-3>", self.show_context_menu)
        # 启动即创建并显示托盘图标，避免用户最小化前托盘区域无图标
        try:
            if PYSTRAY_AVAILABLE and not hasattr(self, 'tray_icon'):
                self.create_tray_icon()
                # 显示托盘图标（不隐藏主窗口）
                try:
                    self.tray_icon.visible = True
                except Exception as e:
                    self.write_log(f"托盘可见性设置失败: {e}")
        except Exception as e:
            self.write_log(f"启动创建托盘图标异常: {e}")

    def add_indicator_click(self):
        self.indicator_canvas.bind("<Button-1>", self.toggle_monitoring)

    def minimize_window(self, event=None):
        # 如果系统未安装托盘依赖，则不隐藏窗口，避免无法恢复
        if not PYSTRAY_AVAILABLE:
            try:
                messagebox.showinfo('提示', '缺少托盘支持（pystray/PIL），窗口将保持显示。')
            except Exception:
                pass
            return
        self.root.withdraw()
        if not hasattr(self, 'tray_icon'):
            self.create_tray_icon()
        else:
            self.tray_icon.visible = True

    def close_app(self, event=None):
        self.running = False
        self.root.destroy()
        os._exit(0)

    def create_tray_icon(self):
        if not PYSTRAY_AVAILABLE:
            self.write_log('托盘不可用：未安装 pystray 或 PIL，跳过创建托盘图标')
            return
        icon_image = Image.new('RGB', (32, 32), (44, 53, 83))
        self.tray_icon = pystray.Icon(
            self.config['app_name'],
            icon_image,
            self.config['app_name'],
            menu=pystray.Menu(
                pystray.MenuItem('恢复主界面', self.restore_window),
                pystray.MenuItem('查看日志', self.show_log),
                pystray.MenuItem('新增处理项', self.open_add_handler_window),
                pystray.MenuItem('退出', self.close_app)
            )
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        # 默认显示托盘图标
        try:
            self.tray_icon.visible = True
            self.write_log('托盘图标已创建并显示')
        except Exception as e:
            self.write_log(f"托盘图标显示失败: {e}")

    def restore_window(self, icon=None, item=None):
        self.root.deiconify()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.visible = False

    def show_log(self, icon=None, item=None):
        log_file = os.path.join(os.path.dirname(__file__), 'trae_mate_log.txt')
        if not os.path.exists(log_file):
            return
        log_win = tk.Toplevel(self.root)
        log_win.title('日志查看')
        log_win.geometry('600x400')
        text = tk.Text(log_win, wrap='word', font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True)
        with open(log_file, 'r', encoding='utf-8') as f:
            text.insert(tk.END, f.read())
        text.config(state=tk.DISABLED)

    def open_add_handler_window(self, icon=None, item=None):
        win = tk.Toplevel(self.root)
        win.title('新增处理项')
        win.geometry('400x260')
        tk.Label(win, text='处理名称（可选）:').pack(anchor='w', padx=10, pady=2)
        name_entry = tk.Entry(win)
        name_entry.pack(fill='x', padx=10)
        tk.Label(win, text='系统提示信息:').pack(anchor='w', padx=10, pady=2)
        tip_entry = tk.Entry(win)
        tip_entry.pack(fill='x', padx=10)
        tk.Label(win, text='按钮图片:').pack(anchor='w', padx=10, pady=2)
        img_path_var = tk.StringVar()
        img_entry = tk.Entry(win, textvariable=img_path_var)
        img_entry.pack(fill='x', padx=10)

        def upload_img():
            path = filedialog.askopenfilename(
                filetypes=[('图片文件', '*.png;*.jpg;*.jpeg')])
            if path:
                # 复制到当前目录
                dst_name = f"handler_btn_{int(time.time())}.png"
                dst_path = os.path.join(os.path.dirname(__file__), dst_name)
                copyfile(path, dst_path)
                img_path_var.set(dst_name)

        def screenshot_img():
            win.withdraw()
            time.sleep(0.5)
            img = pyautogui.screenshot()
            dst_name = f"handler_btn_{int(time.time())}.png"
            dst_path = os.path.join(os.path.dirname(__file__), dst_name)
            img.save(dst_path)
            img_path_var.set(dst_name)
            win.deiconify()

        btn_frame = tk.Frame(win)
        btn_frame.pack(fill='x', padx=10, pady=2)
        tk.Button(
            btn_frame,
            text='上传图片',
            command=upload_img).pack(
            side='left',
            padx=2)
        tk.Button(
            btn_frame,
            text='屏幕截图',
            command=screenshot_img).pack(
            side='left',
            padx=2)

        def on_ok():
            name = name_entry.get().strip()
            tip = tip_entry.get().strip()
            img_path = img_path_var.get().strip()
            if not tip or not img_path:
                messagebox.showerror('错误', '系统提示信息和按钮图片为必填项！')
                return
            self.config['custom_handlers'].append({
                'name': name,
                'tip': tip,
                'img': img_path  # 只保存文件名
            })
            self.save_config()
            messagebox.showinfo('成功', '新增处理项已保存！')
            win.destroy()
        tk.Button(
            win,
            text='确定',
            command=on_ok).pack(
            side='left',
            padx=30,
            pady=10)
        tk.Button(
            win,
            text='取消',
            command=win.destroy).pack(
            side='right',
            padx=30,
            pady=10)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="新增处理项", command=self.open_add_handler_window)
        self.context_menu.add_command(label="查看日志", command=self.show_log)
        # 便捷操作：缩小到托盘区
        self.context_menu.add_command(label="缩小到托盘区", command=self.minimize_window)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="退出", command=self.close_app)

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def start_threads(self):
        threading.Thread(target=self.blink_indicator, daemon=True).start()
        if DETECTION_AVAILABLE:
            threading.Thread(target=self.monitor_trae, daemon=True).start()
        else:
            # 缺少检测依赖（cv2/numpy/pyautogui）时不启动监控线程，避免程序直接退出
            try:
                self.status_label.config(text="检测模块未安装，监控已停用")
                # 指示灯置为灰色
                self.indicator_canvas.itemconfig(
                    self.indicator, fill=self.config['indicator']['color_inactive'])
            except Exception:
                pass
            self.write_log("缺少检测依赖（cv2/numpy/pyautogui），未启动监控线程")

    def blink_indicator(self):
        while self.running:
            if self.monitoring:
                self.blink_state = not self.blink_state
                color = self.config['indicator']['color_active'] if self.blink_state else '#004400'
                try:
                    self.indicator_canvas.itemconfig(
                        self.indicator, fill=color)
                except Exception as e:
                    self.write_log(f"圆点闪烁异常: {e}")
            else:
                try:
                    self.indicator_canvas.itemconfig(
                        self.indicator, fill=self.config['indicator']['color_inactive'])
                except Exception as e:
                    self.write_log(f"圆点闪烁异常: {e}")
            time.sleep(self.config['indicator']['blink_interval'])

    def toggle_monitoring(self, event=None):
        self.monitoring = not self.monitoring
        if self.monitoring:
            self.status_label.config(text="Trae状态监控中...")
            self.write_log("恢复监控")
        else:
            self.status_label.config(text="暂停监控")
            self.write_log("暂停监控")
        self.update_indicator()

    def update_indicator(self):
        if self.monitoring:
            self.indicator_canvas.itemconfig(
                self.indicator, fill=self.config['indicator']['color_active'])
        else:
            self.indicator_canvas.itemconfig(
                self.indicator, fill=self.config['indicator']['color_inactive'])

    def monitor_trae(self):
        while self.running:
            if self.monitoring and self.check_trae_process():
                screenshot = pyautogui.screenshot()
                screenshot_np = np.array(screenshot)
                screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
                try:
                    # 1. 检测主"继续"按钮
                    template = cv2.imread(
                        os.path.join(
                            os.path.dirname(__file__),
                            'continue_btn.png'))
                    if template is not None:
                        # 根据配置的屏幕缩放比例，动态缩放模板
                        try:
                            sf = float(self.config.get('detection', {}).get('scale_factor', 1.0))
                        except Exception:
                            sf = 1.0
                        if sf and sf != 1.0:
                            try:
                                template = cv2.resize(template, (int(template.shape[1] * sf), int(template.shape[0] * sf)))
                            except Exception as e:
                                self.write_log(f"模板缩放异常: {e}")
                        res = cv2.matchTemplate(
                            screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                        threshold = float(self.config.get('detection', {}).get('threshold_main', 0.8))
                        self.write_log(f"检测'继续'按钮，匹配度: {max_val:.3f}")
                        if max_val >= threshold and not self.cooldown:
                            btn_x = max_loc[0] + template.shape[1] // 2
                            btn_y = max_loc[1] + template.shape[0] // 2
                            pyautogui.click(btn_x, btn_y)
                            self.status_label.config(text="已自动点击'继续'按钮")
                            self.write_log(
                                f"检测到'继续'按钮，已自动点击，位置: ({btn_x}, {btn_y})，置信度: {
                                    max_val:.3f}")
                            self.cooldown = True
                            threading.Timer(
                                self.config['monitor']['cooldown_seconds'],
                                self.reset_cooldown).start()
                    # 2. 检测所有自定义处理项
                    for handler in self.config.get('custom_handlers', []):
                        # 检查提示信息（OCR可选，暂略，直接检测按钮图片）
                        handler_img = cv2.imread(
                            os.path.join(
                                os.path.dirname(__file__),
                                handler['img']))
                        if handler_img is not None:
                            # 根据配置的屏幕缩放比例，动态缩放模板
                            try:
                                sf = float(self.config.get('detection', {}).get('scale_factor', 1.0))
                            except Exception:
                                sf = 1.0
                            if sf and sf != 1.0:
                                try:
                                    handler_img = cv2.resize(handler_img, (int(handler_img.shape[1] * sf), int(handler_img.shape[0] * sf)))
                                except Exception as e:
                                    self.write_log(f"模板缩放异常: {e}")
                            res = cv2.matchTemplate(
                                screenshot_bgr, handler_img, cv2.TM_CCOEFF_NORMED)
                            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(
                                res)
                            threshold = float(self.config.get('detection', {}).get('threshold_handlers', 0.85))
                            if max_val >= threshold and not self.cooldown:
                                btn_x = max_loc[0] + handler_img.shape[1] // 2
                                btn_y = max_loc[1] + handler_img.shape[0] // 2
                                pyautogui.click(btn_x, btn_y)
                                self.status_label.config(
                                    text=f"已自动点击自定义项: {handler.get('name', '')}")
                                self.write_log(
                                    f"检测到自定义处理项[{
                                        handler.get(
                                            'name',
                                            '')}]，已自动点击，位置: ({btn_x}, {btn_y})，置信度: {
                                        max_val:.3f}")
                                self.cooldown = True
                                threading.Timer(
                                    self.config['monitor']['cooldown_seconds'],
                                    self.reset_cooldown).start()
                except Exception as e:
                    self.write_log(f"监控异常: {e}")
            time.sleep(self.config['monitor']['interval_seconds'])

    def reset_cooldown(self):
        self.cooldown = False

    def write_log(self, message):
        log_dir = os.path.dirname(__file__)
        log_file = os.path.join(log_dir, f"trae_mate_log.txt")
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{now} {message}\\n")

    def apply_rounded_corners(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int)
            )
        except Exception as e:
            self.write_log(f"倒圆角设置失败: {e}")

    def resize_window(self, event=None):
        screen_width = self.root.winfo_screenwidth()
        window_width = min(max(int(screen_width * 0.4), 320), 800)
        window_height = self.config['window']['height']
        x_position = (screen_width - window_width) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+0")

    def bind_resize(self):
        self.root.bind('<Configure>', self.resize_window)

    def check_trae_process(self):
        try:
            if not PROCESS_AVAILABLE:
                self.write_log("进程检查不可用：未安装 psutil，默认继续监控")
                return True
            monitor_cfg = self.config.get('monitor', {})
            # 可通过配置跳过进程检查，适配不同应用或调试场景
            if monitor_cfg.get('skip_process_check', False):
                return True
            names = [n.lower() for n in monitor_cfg.get('process_names', ['trae'])]
            for p in psutil.process_iter(['name']):
                name = (p.info.get('name') or '').lower()
                if any(n in name for n in names):
                    return True
            return False
        except Exception as e:
            self.write_log(f"进程检查异常: {e}")
            # 异常时默认允许继续监控以避免功能中断
            return True


if __name__ == '__main__':
    if hasattr(sys, '_MEIPASS'):
        config_path = os.path.join(sys._MEIPASS, 'config.json')
    else:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    app = TraeMate(config_path)
    app.root.mainloop()
