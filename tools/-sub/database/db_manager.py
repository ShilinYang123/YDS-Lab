#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 数据库管理工具
提供数据库连接、操作、备份和维护功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading
import time
import shutil
import subprocess

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import psycopg2
    import psycopg2.extras
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

@dataclass
class DatabaseConfig:
    """数据库配置"""
    name: str
    type: str  # sqlite, postgresql, mysql, mongodb, redis
    host: str = 'localhost'
    port: int = None
    username: str = None
    password: str = None
    database: str = None
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}
        
        # 设置默认端口
        if self.port is None:
            default_ports = {
                'postgresql': 5432,
                'mysql': 3306,
                'mongodb': 27017,
                'redis': 6379
            }
            self.port = default_ports.get(self.type)

@dataclass
class QueryResult:
    """查询结果"""
    success: bool
    data: Any = None
    affected_rows: int = 0
    execution_time: float = 0
    error: str = None

@dataclass
class BackupInfo:
    """备份信息"""
    name: str
    database: str
    timestamp: str
    size: int
    path: str
    type: str  # full, incremental, schema

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化数据库管理器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.data_dir = self.project_root / "data"
        self.backup_dir = self.project_root / "backups" / "database"
        self.logs_dir = self.project_root / "logs" / "database"
        
        # 创建目录
        for directory in [self.data_dir, self.backup_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        self.databases = self._load_database_configs()
        
        # 连接池
        self.connections = {}
        self.connection_lock = threading.Lock()
        
        # 设置日志
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载数据库管理配置"""
        config_file = self.config_dir / "database_config.yaml"
        
        default_config = {
            'connection_pool': {
                'max_connections': 10,
                'timeout': 30,
                'retry_attempts': 3,
                'retry_delay': 1
            },
            'backup': {
                'auto_backup': True,
                'backup_schedule': 'daily',  # daily, weekly, monthly
                'retention_days': 30,
                'compression': True,
                'backup_types': ['full', 'schema']
            },
            'monitoring': {
                'enable_query_logging': True,
                'slow_query_threshold': 1.0,  # 秒
                'enable_performance_monitoring': True
            },
            'security': {
                'encrypt_passwords': True,
                'ssl_required': False,
                'connection_timeout': 30
            },
            'maintenance': {
                'auto_vacuum': True,
                'analyze_tables': True,
                'cleanup_logs': True,
                'log_retention_days': 7
            },
            'log_level': 'INFO'
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载数据库配置失败: {e}")
        
        return default_config
    
    def _load_database_configs(self) -> Dict[str, DatabaseConfig]:
        """加载数据库配置"""
        databases = {}
        
        # 从配置文件加载
        db_config_file = self.config_dir / "databases.yaml"
        
        if db_config_file.exists():
            try:
                with open(db_config_file, 'r', encoding='utf-8') as f:
                    db_configs = yaml.safe_load(f)
                    
                    for name, config in db_configs.items():
                        databases[name] = DatabaseConfig(
                            name=name,
                            **config
                        )
            except Exception as e:
                self.logger.error(f"加载数据库配置失败: {e}")
        
        # 默认SQLite数据库
        if 'default' not in databases:
            sqlite_path = self.data_dir / "default.db"
            databases['default'] = DatabaseConfig(
                name='default',
                type='sqlite',
                database=str(sqlite_path)
            )
        
        return databases
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / f"database_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def add_database(self, config: DatabaseConfig) -> bool:
        """添加数据库配置"""
        try:
            self.databases[config.name] = config
            self._save_database_configs()
            
            self.logger.info(f"数据库配置已添加: {config.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"添加数据库配置失败: {e}")
            return False
    
    def remove_database(self, name: str) -> bool:
        """移除数据库配置"""
        try:
            if name in self.databases:
                # 关闭连接
                self.disconnect(name)
                
                # 移除配置
                del self.databases[name]
                self._save_database_configs()
                
                self.logger.info(f"数据库配置已移除: {name}")
                return True
            else:
                self.logger.warning(f"数据库配置不存在: {name}")
                return False
        
        except Exception as e:
            self.logger.error(f"移除数据库配置失败: {e}")
            return False
    
    def _save_database_configs(self):
        """保存数据库配置"""
        db_config_file = self.config_dir / "databases.yaml"
        
        try:
            configs = {}
            for name, config in self.databases.items():
                config_dict = asdict(config)
                del config_dict['name']  # 名称作为key
                configs[name] = config_dict
            
            with open(db_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(configs, f, default_flow_style=False, allow_unicode=True)
        
        except Exception as e:
            self.logger.error(f"保存数据库配置失败: {e}")
    
    @contextmanager
    def get_connection(self, database_name: str = 'default'):
        """获取数据库连接（上下文管理器）"""
        connection = None
        
        try:
            connection = self.connect(database_name)
            yield connection
        
        finally:
            if connection:
                self.disconnect(database_name)
    
    def connect(self, database_name: str = 'default') -> Any:
        """连接数据库"""
        if database_name not in self.databases:
            raise ValueError(f"数据库配置不存在: {database_name}")
        
        with self.connection_lock:
            # 检查是否已有连接
            if database_name in self.connections:
                return self.connections[database_name]
            
            config = self.databases[database_name]
            connection = None
            
            try:
                if config.type == 'sqlite':
                    connection = self._connect_sqlite(config)
                
                elif config.type == 'postgresql':
                    connection = self._connect_postgresql(config)
                
                elif config.type == 'mysql':
                    connection = self._connect_mysql(config)
                
                elif config.type == 'mongodb':
                    connection = self._connect_mongodb(config)
                
                elif config.type == 'redis':
                    connection = self._connect_redis(config)
                
                else:
                    raise ValueError(f"不支持的数据库类型: {config.type}")
                
                self.connections[database_name] = connection
                self.logger.info(f"数据库连接成功: {database_name}")
                
                return connection
            
            except Exception as e:
                self.logger.error(f"数据库连接失败 {database_name}: {e}")
                raise
    
    def _connect_sqlite(self, config: DatabaseConfig) -> sqlite3.Connection:
        """连接SQLite数据库"""
        # 确保数据库目录存在
        db_path = Path(config.database)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        connection = sqlite3.connect(
            config.database,
            timeout=self.config['connection_pool']['timeout'],
            **config.options
        )
        
        # 设置行工厂
        connection.row_factory = sqlite3.Row
        
        # 启用外键约束
        connection.execute("PRAGMA foreign_keys = ON")
        
        return connection
    
    def _connect_postgresql(self, config: DatabaseConfig) -> Any:
        """连接PostgreSQL数据库"""
        if not POSTGRESQL_AVAILABLE:
            raise ImportError("PostgreSQL支持需要安装psycopg2: pip install psycopg2-binary")
        
        connection = psycopg2.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            database=config.database,
            connect_timeout=self.config['security']['connection_timeout'],
            **config.options
        )
        
        # 设置自动提交
        connection.autocommit = True
        
        return connection
    
    def _connect_mysql(self, config: DatabaseConfig) -> Any:
        """连接MySQL数据库"""
        if not MYSQL_AVAILABLE:
            raise ImportError("MySQL支持需要安装mysql-connector-python: pip install mysql-connector-python")
        
        connection = mysql.connector.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            database=config.database,
            connection_timeout=self.config['security']['connection_timeout'],
            **config.options
        )
        
        return connection
    
    def _connect_mongodb(self, config: DatabaseConfig) -> Any:
        """连接MongoDB数据库"""
        if not MONGODB_AVAILABLE:
            raise ImportError("MongoDB支持需要安装pymongo: pip install pymongo")
        
        # 构建连接字符串
        if config.username and config.password:
            connection_string = f"mongodb://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        else:
            connection_string = f"mongodb://{config.host}:{config.port}/{config.database}"
        
        client = pymongo.MongoClient(
            connection_string,
            serverSelectionTimeoutMS=self.config['security']['connection_timeout'] * 1000,
            **config.options
        )
        
        return client[config.database]
    
    def _connect_redis(self, config: DatabaseConfig) -> Any:
        """连接Redis数据库"""
        if not REDIS_AVAILABLE:
            raise ImportError("Redis支持需要安装redis: pip install redis")
        
        connection = redis.Redis(
            host=config.host,
            port=config.port,
            password=config.password,
            db=config.database or 0,
            socket_timeout=self.config['security']['connection_timeout'],
            **config.options
        )
        
        # 测试连接
        connection.ping()
        
        return connection
    
    def disconnect(self, database_name: str = None):
        """断开数据库连接"""
        with self.connection_lock:
            if database_name:
                if database_name in self.connections:
                    try:
                        connection = self.connections[database_name]
                        
                        # 根据数据库类型关闭连接
                        config = self.databases[database_name]
                        
                        if config.type in ['sqlite', 'postgresql', 'mysql']:
                            connection.close()
                        elif config.type == 'mongodb':
                            connection.client.close()
                        elif config.type == 'redis':
                            connection.close()
                        
                        del self.connections[database_name]
                        self.logger.info(f"数据库连接已关闭: {database_name}")
                    
                    except Exception as e:
                        self.logger.error(f"关闭数据库连接失败 {database_name}: {e}")
            else:
                # 关闭所有连接
                for name in list(self.connections.keys()):
                    self.disconnect(name)
    
    def execute_query(self, query: str, params: Tuple = None, database_name: str = 'default') -> QueryResult:
        """执行SQL查询"""
        start_time = time.time()
        
        try:
            with self.get_connection(database_name) as connection:
                config = self.databases[database_name]
                
                if config.type == 'sqlite':
                    return self._execute_sqlite_query(connection, query, params)
                
                elif config.type == 'postgresql':
                    return self._execute_postgresql_query(connection, query, params)
                
                elif config.type == 'mysql':
                    return self._execute_mysql_query(connection, query, params)
                
                else:
                    raise ValueError(f"SQL查询不支持数据库类型: {config.type}")
        
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"查询执行失败: {e}")
            
            return QueryResult(
                success=False,
                execution_time=execution_time,
                error=str(e)
            )
    
    def _execute_sqlite_query(self, connection: sqlite3.Connection, query: str, params: Tuple) -> QueryResult:
        """执行SQLite查询"""
        start_time = time.time()
        
        try:
            cursor = connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 判断查询类型
            query_type = query.strip().upper().split()[0]
            
            if query_type == 'SELECT':
                data = [dict(row) for row in cursor.fetchall()]
                affected_rows = len(data)
            else:
                data = None
                affected_rows = cursor.rowcount
                connection.commit()
            
            execution_time = time.time() - start_time
            
            # 记录慢查询
            if execution_time > self.config['monitoring']['slow_query_threshold']:
                self.logger.warning(f"慢查询检测 ({execution_time:.2f}s): {query[:100]}...")
            
            return QueryResult(
                success=True,
                data=data,
                affected_rows=affected_rows,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            raise e
    
    def _execute_postgresql_query(self, connection: Any, query: str, params: Tuple) -> QueryResult:
        """执行PostgreSQL查询"""
        start_time = time.time()
        
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 判断查询类型
            query_type = query.strip().upper().split()[0]
            
            if query_type == 'SELECT':
                data = [dict(row) for row in cursor.fetchall()]
                affected_rows = len(data)
            else:
                data = None
                affected_rows = cursor.rowcount
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                data=data,
                affected_rows=affected_rows,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            raise e
    
    def _execute_mysql_query(self, connection: Any, query: str, params: Tuple) -> QueryResult:
        """执行MySQL查询"""
        start_time = time.time()
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # 判断查询类型
            query_type = query.strip().upper().split()[0]
            
            if query_type == 'SELECT':
                data = cursor.fetchall()
                affected_rows = len(data)
            else:
                data = None
                affected_rows = cursor.rowcount
                connection.commit()
            
            execution_time = time.time() - start_time
            
            return QueryResult(
                success=True,
                data=data,
                affected_rows=affected_rows,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            raise e
    
    def create_table(self, table_name: str, columns: Dict[str, str], database_name: str = 'default') -> bool:
        """创建表"""
        try:
            config = self.databases[database_name]
            
            if config.type == 'sqlite':
                column_defs = []
                for col_name, col_type in columns.items():
                    column_defs.append(f"{col_name} {col_type}")
                
                query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            
            elif config.type in ['postgresql', 'mysql']:
                column_defs = []
                for col_name, col_type in columns.items():
                    column_defs.append(f"{col_name} {col_type}")
                
                query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            
            else:
                raise ValueError(f"创建表不支持数据库类型: {config.type}")
            
            result = self.execute_query(query, database_name=database_name)
            
            if result.success:
                self.logger.info(f"表创建成功: {table_name}")
                return True
            else:
                self.logger.error(f"表创建失败: {result.error}")
                return False
        
        except Exception as e:
            self.logger.error(f"创建表失败: {e}")
            return False
    
    def insert_data(self, table_name: str, data: Union[Dict, List[Dict]], database_name: str = 'default') -> bool:
        """插入数据"""
        try:
            if isinstance(data, dict):
                data = [data]
            
            if not data:
                return True
            
            # 获取列名
            columns = list(data[0].keys())
            placeholders = ', '.join(['?' if self.databases[database_name].type == 'sqlite' else '%s'] * len(columns))
            
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # 批量插入
            success_count = 0
            
            for row in data:
                values = tuple(row[col] for col in columns)
                result = self.execute_query(query, values, database_name)
                
                if result.success:
                    success_count += 1
                else:
                    self.logger.error(f"插入数据失败: {result.error}")
            
            self.logger.info(f"数据插入完成: {success_count}/{len(data)} 条记录")
            return success_count == len(data)
        
        except Exception as e:
            self.logger.error(f"插入数据失败: {e}")
            return False
    
    def update_data(self, table_name: str, data: Dict, where_clause: str, params: Tuple = None, database_name: str = 'default') -> bool:
        """更新数据"""
        try:
            set_clauses = []
            values = []
            
            for column, value in data.items():
                if self.databases[database_name].type == 'sqlite':
                    set_clauses.append(f"{column} = ?")
                else:
                    set_clauses.append(f"{column} = %s")
                values.append(value)
            
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"
            
            if params:
                values.extend(params)
            
            result = self.execute_query(query, tuple(values), database_name)
            
            if result.success:
                self.logger.info(f"数据更新成功: {result.affected_rows} 条记录")
                return True
            else:
                self.logger.error(f"数据更新失败: {result.error}")
                return False
        
        except Exception as e:
            self.logger.error(f"更新数据失败: {e}")
            return False
    
    def delete_data(self, table_name: str, where_clause: str, params: Tuple = None, database_name: str = 'default') -> bool:
        """删除数据"""
        try:
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            result = self.execute_query(query, params, database_name)
            
            if result.success:
                self.logger.info(f"数据删除成功: {result.affected_rows} 条记录")
                return True
            else:
                self.logger.error(f"数据删除失败: {result.error}")
                return False
        
        except Exception as e:
            self.logger.error(f"删除数据失败: {e}")
            return False
    
    def select_data(self, table_name: str, columns: str = '*', where_clause: str = None, params: Tuple = None, database_name: str = 'default') -> List[Dict]:
        """查询数据"""
        try:
            query = f"SELECT {columns} FROM {table_name}"
            
            if where_clause:
                query += f" WHERE {where_clause}"
            
            result = self.execute_query(query, params, database_name)
            
            if result.success:
                return result.data or []
            else:
                self.logger.error(f"数据查询失败: {result.error}")
                return []
        
        except Exception as e:
            self.logger.error(f"查询数据失败: {e}")
            return []
    
    def backup_database(self, database_name: str = 'default', backup_type: str = 'full') -> Optional[BackupInfo]:
        """备份数据库"""
        try:
            config = self.databases[database_name]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            backup_name = f"{database_name}_{backup_type}_{timestamp}"
            
            if config.type == 'sqlite':
                return self._backup_sqlite(config, backup_name, backup_type)
            
            elif config.type == 'postgresql':
                return self._backup_postgresql(config, backup_name, backup_type)
            
            elif config.type == 'mysql':
                return self._backup_mysql(config, backup_name, backup_type)
            
            else:
                self.logger.error(f"备份不支持数据库类型: {config.type}")
                return None
        
        except Exception as e:
            self.logger.error(f"数据库备份失败: {e}")
            return None
    
    def _backup_sqlite(self, config: DatabaseConfig, backup_name: str, backup_type: str) -> BackupInfo:
        """备份SQLite数据库"""
        source_path = Path(config.database)
        backup_path = self.backup_dir / f"{backup_name}.db"
        
        if backup_type == 'full':
            # 完整备份
            shutil.copy2(source_path, backup_path)
        
        elif backup_type == 'schema':
            # 仅备份结构
            with sqlite3.connect(source_path) as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    # 获取所有表的创建语句
                    cursor = source_conn.cursor()
                    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                    
                    for (sql,) in cursor.fetchall():
                        if sql:
                            backup_conn.execute(sql)
        
        # 压缩备份文件
        if self.config['backup']['compression']:
            compressed_path = backup_path.with_suffix('.db.gz')
            
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_path.unlink()  # 删除未压缩文件
            backup_path = compressed_path
        
        backup_info = BackupInfo(
            name=backup_name,
            database=config.name,
            timestamp=datetime.now().isoformat(),
            size=backup_path.stat().st_size,
            path=str(backup_path),
            type=backup_type
        )
        
        self.logger.info(f"SQLite备份完成: {backup_path}")
        return backup_info
    
    def _backup_postgresql(self, config: DatabaseConfig, backup_name: str, backup_type: str) -> BackupInfo:
        """备份PostgreSQL数据库"""
        backup_path = self.backup_dir / f"{backup_name}.sql"
        
        # 构建pg_dump命令
        cmd = [
            'pg_dump',
            '-h', config.host,
            '-p', str(config.port),
            '-U', config.username,
            '-d', config.database,
            '-f', str(backup_path)
        ]
        
        if backup_type == 'schema':
            cmd.append('--schema-only')
        
        # 设置密码环境变量
        env = os.environ.copy()
        env['PGPASSWORD'] = config.password
        
        # 执行备份
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"pg_dump失败: {result.stderr}")
        
        # 压缩备份文件
        if self.config['backup']['compression']:
            compressed_path = backup_path.with_suffix('.sql.gz')
            
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_path.unlink()
            backup_path = compressed_path
        
        backup_info = BackupInfo(
            name=backup_name,
            database=config.name,
            timestamp=datetime.now().isoformat(),
            size=backup_path.stat().st_size,
            path=str(backup_path),
            type=backup_type
        )
        
        self.logger.info(f"PostgreSQL备份完成: {backup_path}")
        return backup_info
    
    def _backup_mysql(self, config: DatabaseConfig, backup_name: str, backup_type: str) -> BackupInfo:
        """备份MySQL数据库"""
        backup_path = self.backup_dir / f"{backup_name}.sql"
        
        # 构建mysqldump命令
        cmd = [
            'mysqldump',
            '-h', config.host,
            '-P', str(config.port),
            '-u', config.username,
            f'-p{config.password}',
            config.database
        ]
        
        if backup_type == 'schema':
            cmd.append('--no-data')
        
        # 执行备份
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise Exception(f"mysqldump失败: {result.stderr}")
        
        # 压缩备份文件
        if self.config['backup']['compression']:
            compressed_path = backup_path.with_suffix('.sql.gz')
            
            import gzip
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_path.unlink()
            backup_path = compressed_path
        
        backup_info = BackupInfo(
            name=backup_name,
            database=config.name,
            timestamp=datetime.now().isoformat(),
            size=backup_path.stat().st_size,
            path=str(backup_path),
            type=backup_type
        )
        
        self.logger.info(f"MySQL备份完成: {backup_path}")
        return backup_info
    
    def restore_database(self, backup_path: str, database_name: str = 'default') -> bool:
        """恢复数据库"""
        try:
            config = self.databases[database_name]
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                self.logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            if config.type == 'sqlite':
                return self._restore_sqlite(config, backup_file)
            
            elif config.type == 'postgresql':
                return self._restore_postgresql(config, backup_file)
            
            elif config.type == 'mysql':
                return self._restore_mysql(config, backup_file)
            
            else:
                self.logger.error(f"恢复不支持数据库类型: {config.type}")
                return False
        
        except Exception as e:
            self.logger.error(f"数据库恢复失败: {e}")
            return False
    
    def _restore_sqlite(self, config: DatabaseConfig, backup_file: Path) -> bool:
        """恢复SQLite数据库"""
        try:
            # 关闭现有连接
            self.disconnect(config.name)
            
            # 备份当前数据库
            current_db = Path(config.database)
            if current_db.exists():
                backup_current = current_db.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
                shutil.copy2(current_db, backup_current)
                self.logger.info(f"当前数据库已备份至: {backup_current}")
            
            # 解压缩（如果需要）
            if backup_file.suffix == '.gz':
                import gzip
                temp_file = backup_file.with_suffix('')
                
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                backup_file = temp_file
            
            # 恢复数据库
            shutil.copy2(backup_file, current_db)
            
            # 清理临时文件
            if backup_file.name.endswith('.backup'):
                backup_file.unlink()
            
            self.logger.info(f"SQLite数据库恢复完成: {config.database}")
            return True
        
        except Exception as e:
            self.logger.error(f"SQLite恢复失败: {e}")
            return False
    
    def _restore_postgresql(self, config: DatabaseConfig, backup_file: Path) -> bool:
        """恢复PostgreSQL数据库"""
        try:
            # 解压缩（如果需要）
            restore_file = backup_file
            
            if backup_file.suffix == '.gz':
                import gzip
                temp_file = backup_file.with_suffix('')
                
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                restore_file = temp_file
            
            # 构建psql命令
            cmd = [
                'psql',
                '-h', config.host,
                '-p', str(config.port),
                '-U', config.username,
                '-d', config.database,
                '-f', str(restore_file)
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = config.password
            
            # 执行恢复
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            # 清理临时文件
            if restore_file != backup_file:
                restore_file.unlink()
            
            if result.returncode != 0:
                raise Exception(f"psql失败: {result.stderr}")
            
            self.logger.info(f"PostgreSQL数据库恢复完成")
            return True
        
        except Exception as e:
            self.logger.error(f"PostgreSQL恢复失败: {e}")
            return False
    
    def _restore_mysql(self, config: DatabaseConfig, backup_file: Path) -> bool:
        """恢复MySQL数据库"""
        try:
            # 解压缩（如果需要）
            restore_file = backup_file
            
            if backup_file.suffix == '.gz':
                import gzip
                temp_file = backup_file.with_suffix('')
                
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                restore_file = temp_file
            
            # 构建mysql命令
            cmd = [
                'mysql',
                '-h', config.host,
                '-P', str(config.port),
                '-u', config.username,
                f'-p{config.password}',
                config.database
            ]
            
            # 执行恢复
            with open(restore_file, 'r') as f:
                result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
            
            # 清理临时文件
            if restore_file != backup_file:
                restore_file.unlink()
            
            if result.returncode != 0:
                raise Exception(f"mysql失败: {result.stderr}")
            
            self.logger.info(f"MySQL数据库恢复完成")
            return True
        
        except Exception as e:
            self.logger.error(f"MySQL恢复失败: {e}")
            return False
    
    def list_backups(self, database_name: str = None) -> List[BackupInfo]:
        """列出备份文件"""
        backups = []
        
        try:
            for backup_file in self.backup_dir.glob('*'):
                if backup_file.is_file():
                    # 解析备份文件名
                    name_parts = backup_file.stem.split('_')
                    
                    if len(name_parts) >= 3:
                        db_name = name_parts[0]
                        backup_type = name_parts[1]
                        
                        # 过滤指定数据库
                        if database_name and db_name != database_name:
                            continue
                        
                        backup_info = BackupInfo(
                            name=backup_file.stem,
                            database=db_name,
                            timestamp=datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                            size=backup_file.stat().st_size,
                            path=str(backup_file),
                            type=backup_type
                        )
                        
                        backups.append(backup_info)
            
            # 按时间排序
            backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        except Exception as e:
            self.logger.error(f"列出备份失败: {e}")
        
        return backups
    
    def cleanup_old_backups(self, retention_days: int = None) -> int:
        """清理旧备份"""
        if retention_days is None:
            retention_days = self.config['backup']['retention_days']
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        try:
            for backup_file in self.backup_dir.glob('*'):
                if backup_file.is_file():
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        self.logger.info(f"删除旧备份: {backup_file.name}")
        
        except Exception as e:
            self.logger.error(f"清理备份失败: {e}")
        
        return deleted_count
    
    def get_database_info(self, database_name: str = 'default') -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            config = self.databases[database_name]
            info = {
                'name': config.name,
                'type': config.type,
                'host': config.host,
                'port': config.port,
                'database': config.database,
                'connected': database_name in self.connections
            }
            
            if config.type == 'sqlite':
                db_path = Path(config.database)
                if db_path.exists():
                    info['size'] = db_path.stat().st_size
                    info['modified'] = datetime.fromtimestamp(db_path.stat().st_mtime).isoformat()
                
                # 获取表信息
                try:
                    tables = self.select_data('sqlite_master', 'name', "type='table'", database_name=database_name)
                    info['tables'] = [table['name'] for table in tables]
                except:
                    info['tables'] = []
            
            return info
        
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return {}
    
    def list_databases(self) -> List[Dict[str, Any]]:
        """列出所有数据库"""
        databases = []
        
        for name, config in self.databases.items():
            db_info = self.get_database_info(name)
            databases.append(db_info)
        
        return databases

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 数据库管理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--list', action='store_true', help='列出所有数据库')
    parser.add_argument('--info', help='显示指定数据库信息')
    parser.add_argument('--backup', help='备份指定数据库')
    parser.add_argument('--backup-type', choices=['full', 'schema'], default='full', help='备份类型')
    parser.add_argument('--restore', nargs=2, metavar=('BACKUP_PATH', 'DATABASE'), help='恢复数据库')
    parser.add_argument('--list-backups', help='列出指定数据库的备份')
    parser.add_argument('--cleanup', action='store_true', help='清理旧备份')
    parser.add_argument('--query', nargs=2, metavar=('SQL', 'DATABASE'), help='执行SQL查询')
    parser.add_argument('--create-table', nargs=3, metavar=('TABLE', 'COLUMNS', 'DATABASE'), help='创建表')
    
    args = parser.parse_args()
    
    manager = DatabaseManager(args.project_root)
    
    # 列出数据库
    if args.list:
        databases = manager.list_databases()
        
        print("📊 数据库列表")
        print("="*50)
        
        for db in databases:
            print(f"名称: {db['name']}")
            print(f"类型: {db['type']}")
            print(f"连接状态: {'已连接' if db['connected'] else '未连接'}")
            
            if 'size' in db:
                print(f"大小: {db['size'] / (1024*1024):.1f} MB")
            
            if 'tables' in db:
                print(f"表数量: {len(db['tables'])}")
            
            print("-" * 30)
        
        return
    
    # 显示数据库信息
    if args.info:
        info = manager.get_database_info(args.info)
        
        if info:
            print(f"📋 数据库信息: {args.info}")
            print("="*40)
            
            for key, value in info.items():
                print(f"{key}: {value}")
        else:
            print(f"❌ 数据库不存在: {args.info}")
        
        return
    
    # 备份数据库
    if args.backup:
        print(f"🔄 备份数据库: {args.backup}")
        
        backup_info = manager.backup_database(args.backup, args.backup_type)
        
        if backup_info:
            print(f"✅ 备份完成:")
            print(f"  文件: {backup_info.path}")
            print(f"  大小: {backup_info.size / (1024*1024):.1f} MB")
            print(f"  类型: {backup_info.type}")
        else:
            print("❌ 备份失败")
        
        return
    
    # 恢复数据库
    if args.restore:
        backup_path, database_name = args.restore
        
        print(f"🔄 恢复数据库: {database_name}")
        
        if manager.restore_database(backup_path, database_name):
            print("✅ 恢复完成")
        else:
            print("❌ 恢复失败")
        
        return
    
    # 列出备份
    if args.list_backups:
        backups = manager.list_backups(args.list_backups)
        
        print(f"📦 备份列表: {args.list_backups}")
        print("="*50)
        
        for backup in backups:
            print(f"名称: {backup.name}")
            print(f"时间: {backup.timestamp}")
            print(f"大小: {backup.size / (1024*1024):.1f} MB")
            print(f"类型: {backup.type}")
            print(f"路径: {backup.path}")
            print("-" * 30)
        
        return
    
    # 清理备份
    if args.cleanup:
        deleted_count = manager.cleanup_old_backups()
        print(f"🧹 清理完成，删除了 {deleted_count} 个旧备份")
        return
    
    # 执行查询
    if args.query:
        sql, database_name = args.query
        
        print(f"🔍 执行查询: {database_name}")
        
        result = manager.execute_query(sql, database_name=database_name)
        
        if result.success:
            print(f"✅ 查询成功 (耗时: {result.execution_time:.3f}s)")
            
            if result.data:
                print(f"返回 {len(result.data)} 条记录:")
                
                for i, row in enumerate(result.data[:10]):  # 显示前10条
                    print(f"  {i+1}: {row}")
                
                if len(result.data) > 10:
                    print(f"  ... 还有 {len(result.data) - 10} 条记录")
            
            elif result.affected_rows > 0:
                print(f"影响 {result.affected_rows} 条记录")
        else:
            print(f"❌ 查询失败: {result.error}")
        
        return
    
    # 创建表
    if args.create_table:
        table_name, columns_str, database_name = args.create_table
        
        try:
            # 解析列定义 (格式: "name:TEXT,age:INTEGER")
            columns = {}
            for col_def in columns_str.split(','):
                col_name, col_type = col_def.split(':')
                columns[col_name.strip()] = col_type.strip()
            
            print(f"🔨 创建表: {table_name}")
            
            if manager.create_table(table_name, columns, database_name):
                print("✅ 表创建成功")
            else:
                print("❌ 表创建失败")
        
        except Exception as e:
            print(f"❌ 参数解析失败: {e}")
        
        return
    
    # 默认显示状态
    print("📊 数据库管理器状态")
    print("="*40)
    print(f"项目路径: {manager.project_root}")
    print(f"数据库数量: {len(manager.databases)}")
    print(f"活动连接: {len(manager.connections)}")
    
    # 显示配置的数据库
    for name, config in manager.databases.items():
        status = "已连接" if name in manager.connections else "未连接"
        print(f"  {name} ({config.type}): {status}")

if __name__ == "__main__":
    main()