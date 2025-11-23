import os
import psutil
import logging
import traceback
from typing import Optional, Dict

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('S:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\logs\\common_utils.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

MEMORY_PATH = 'S:\\YDS-Lab\\03-dev\\006-AUTOVPN\\VPN-Sel\\memory.json'


def load_config(config_path: str = os.path.join(os.path.dirname(
        __file__), '..', 'config.env')) -> Optional[Dict[str, str]]:
    """
    动态加载当前脚本目录的config.env文件
    优先使用传入的config_path参数
    """
    try:
        if not os.path.exists(config_path):
            config_path = os.path.join(
                os.path.dirname(__file__), '..', 'config.env')
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 处理行内注释
                        if '#' in value:
                            value = value.split('#')[0]
                        config[key.strip()] = value.strip()
        else:
            logger.warning(f'配置文件 {config_path} 不存在')
        return config
    except Exception as e:
        logger.error(f'加载配置文件失败: {e}')
        logger.error(traceback.format_exc())
        return None


def is_process_running(process_name: str) -> bool:
    """
    检查指定进程是否正在运行

    :param process_name: 进程名称
    :return: 是否在运行
    """
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return True
        return False
    except Exception as e:
        logger.error(f'检查进程 {process_name} 是否运行时出错: {e}')
        logger.error(traceback.format_exc())
        return False


def kill_process_by_name(process_name: str) -> bool:
    """
    强制终止指定名称的进程

    :param process_name: 进程名称
    :return: 是否成功终止
    """
    try:
        terminated = False
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'] == process_name:
                try:
                    proc.kill()
                    logger.info(f'已终止进程: {process_name} (PID: {proc.pid})')
                    terminated = True
                except psutil.NoSuchProcess:
                    logger.warning(f'进程 {process_name} (PID: {proc.pid}) 已不存在')
                except psutil.AccessDenied:
                    logger.error(f'无法终止进程 {process_name} (PID: {proc.pid})，权限不足')
                except Exception as e:
                    logger.error(f'终止进程 {process_name} (PID: {proc.pid}) 时出错: {e}')
                    logger.error(traceback.format_exc())
        return terminated
    except Exception as e:
        logger.error(f'终止进程 {process_name} 时出错: {e}')
        logger.error(traceback.format_exc())
        return False


def is_port_in_use(port: int) -> bool:
    """
    检查端口是否被占用

    :param port: 端口号
    :return: 端口是否被占用
    """
    try:
        for conn in psutil.net_connections():
            if hasattr(conn, 'laddr') and hasattr(conn.laddr, 'port') and conn.laddr.port == port:
                return True
        return False
    except Exception as e:
        logger.error(f'检查端口 {port} 是否被占用时出错: {e}')
        logger.error(traceback.format_exc())
        return False


def get_default_gateway() -> Optional[str]:
    """
    获取Windows系统的默认网关IP地址

    :return: 默认网关IP地址，如果找不到则返回None
    """
    try:
        import subprocess
        import re
        # 执行ipconfig命令
        process = subprocess.Popen(
            ['ipconfig'],
            stdout=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW)
        output, _ = process.communicate()

        # 正则表达式匹配默认网关
        # 匹配 IPv4 地址
        gateway_match = re.search(
            r"Default Gateway[ .]*: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", output)
        if gateway_match:
            return gateway_match.group(1)
        else:
            # 如果没有IPv4的默认网关，尝试匹配IPv6的（虽然通常我们关注IPv4）
            # 这里的IPv6匹配可能需要根据实际ipconfig输出调整
            gateway_match_v6 = re.search(
                r"Default Gateway[ .]*: ([0-9a-fA-F:]+)", output)
            if gateway_match_v6:
                # 对于v6地址，可能需要进一步处理，例如选择非link-local的
                # 但对于ping测试，通常IPv4更常用
                logger.info(
                    f"找到IPv6默认网关: {
                        gateway_match_v6.group(1)}，但通常需要IPv4网关进行ping测试。")
                return None  # 或者返回IPv6地址，取决于后续如何使用
            logger.warning("无法从ipconfig输出中找到默认网关。")
            return None
    except FileNotFoundError:
        logger.error("ipconfig 命令未找到，请确保其在系统路径中。")
        return None
    except Exception as e:
        logger.error(f'获取默认网关失败: {e}')
        logger.error(traceback.format_exc())
        return None