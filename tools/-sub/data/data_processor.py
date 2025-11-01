#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 数据处理工具
提供数据清洗、转换、分析、可视化和导入导出功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import csv
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import sqlite3
import pickle
import hashlib
import re
from collections import defaultdict, Counter
import statistics
from enum import Enum

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class DataFormat(Enum):
    """数据格式枚举"""
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    PARQUET = "parquet"
    PICKLE = "pickle"
    SQL = "sql"
    XML = "xml"
    TSV = "tsv"

class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DataQualityReport:
    """数据质量报告"""
    total_rows: int
    total_columns: int
    missing_values: Dict[str, int]
    duplicate_rows: int
    data_types: Dict[str, str]
    memory_usage: float
    quality_score: float
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime

@dataclass
class ProcessingJob:
    """数据处理任务"""
    job_id: str
    name: str
    input_file: str
    output_file: str
    operations: List[Dict[str, Any]]
    status: ProcessingStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DataProcessor:
    """数据处理器"""
    
    def __init__(self, project_root: str = None):
        """初始化数据处理器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # 数据目录
        self.data_dir = self.project_root / "data"
        self.input_dir = self.data_dir / "input"
        self.output_dir = self.data_dir / "output"
        self.temp_dir = self.data_dir / "temp"
        self.cache_dir = self.data_dir / "cache"
        
        # 创建目录
        for directory in [self.data_dir, self.input_dir, self.output_dir, self.temp_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 配置文件
        self.config_file = self.data_dir / "processing_config.json"
        self.jobs_file = self.data_dir / "processing_jobs.json"
        
        # 初始化状态
        self.jobs = {}
        self.cache = {}
        self.processing_functions = {}
        
        # 设置日志
        self.logger = logging.getLogger('yds_lab.data_processor')
        
        # 加载配置和任务
        self._load_config()
        self._load_jobs()
        
        # 注册默认处理函数
        self._register_default_functions()
    
    def _load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                self.logger.error(f"加载配置失败: {e}")
                self.config = {}
        else:
            self.config = {
                'max_memory_usage': 1024 * 1024 * 1024,  # 1GB
                'chunk_size': 10000,
                'cache_enabled': True,
                'auto_backup': True,
                'quality_threshold': 0.8,
                'supported_formats': ['csv', 'json', 'excel', 'parquet'],
                'default_encoding': 'utf-8'
            }
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
    
    def _load_jobs(self):
        """加载处理任务"""
        if self.jobs_file.exists():
            try:
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    jobs_data = json.load(f)
                
                for job_id, job_data in jobs_data.items():
                    # 转换日期时间字符串
                    for field in ['created_at', 'started_at', 'completed_at']:
                        if job_data.get(field):
                            job_data[field] = datetime.fromisoformat(job_data[field])
                    
                    # 转换状态枚举
                    job_data['status'] = ProcessingStatus(job_data['status'])
                    
                    self.jobs[job_id] = ProcessingJob(**job_data)
            
            except Exception as e:
                self.logger.error(f"加载任务失败: {e}")
                self.jobs = {}
    
    def _save_jobs(self):
        """保存处理任务"""
        try:
            jobs_data = {}
            for job_id, job in self.jobs.items():
                job_dict = asdict(job)
                
                # 转换日期时间为字符串
                for field in ['created_at', 'started_at', 'completed_at']:
                    if job_dict.get(field):
                        job_dict[field] = job_dict[field].isoformat()
                
                # 转换状态枚举为字符串
                job_dict['status'] = job_dict['status'].value
                
                jobs_data[job_id] = job_dict
            
            with open(self.jobs_file, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False, default=str)
        
        except Exception as e:
            self.logger.error(f"保存任务失败: {e}")
    
    def _register_default_functions(self):
        """注册默认处理函数"""
        # 数据清洗函数
        self.processing_functions.update({
            'remove_duplicates': self._remove_duplicates,
            'fill_missing': self._fill_missing_values,
            'remove_outliers': self._remove_outliers,
            'normalize_text': self._normalize_text,
            'convert_types': self._convert_data_types,
            'filter_rows': self._filter_rows,
            'select_columns': self._select_columns,
            'rename_columns': self._rename_columns,
            'sort_data': self._sort_data,
            'group_by': self._group_by_operation,
            'merge_data': self._merge_data,
            'pivot_table': self._create_pivot_table,
            'calculate_stats': self._calculate_statistics,
            'create_features': self._create_features,
            'validate_data': self._validate_data
        })
    
    def load_data(self, file_path: str, format_type: DataFormat = None, **kwargs) -> pd.DataFrame:
        """加载数据"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        # 自动检测格式
        if format_type is None:
            format_type = self._detect_format(file_path)
        
        try:
            # 检查缓存
            cache_key = self._get_cache_key(file_path)
            if self.config.get('cache_enabled') and cache_key in self.cache:
                self.logger.info(f"从缓存加载数据: {file_path}")
                return self.cache[cache_key]
            
            self.logger.info(f"加载数据文件: {file_path} (格式: {format_type.value})")
            
            # 根据格式加载数据
            if format_type == DataFormat.CSV:
                df = pd.read_csv(file_path, encoding=kwargs.get('encoding', 'utf-8'), **kwargs)
            elif format_type == DataFormat.JSON:
                df = pd.read_json(file_path, encoding=kwargs.get('encoding', 'utf-8'), **kwargs)
            elif format_type == DataFormat.EXCEL:
                if not EXCEL_AVAILABLE:
                    raise ImportError("需要安装 openpyxl 来处理Excel文件")
                df = pd.read_excel(file_path, **kwargs)
            elif format_type == DataFormat.PARQUET:
                df = pd.read_parquet(file_path, **kwargs)
            elif format_type == DataFormat.PICKLE:
                df = pd.read_pickle(file_path)
            elif format_type == DataFormat.TSV:
                df = pd.read_csv(file_path, sep='\t', encoding=kwargs.get('encoding', 'utf-8'), **kwargs)
            else:
                raise ValueError(f"不支持的数据格式: {format_type}")
            
            # 缓存数据
            if self.config.get('cache_enabled'):
                self.cache[cache_key] = df.copy()
            
            self.logger.info(f"数据加载完成: {df.shape[0]} 行, {df.shape[1]} 列")
            return df
        
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            raise
    
    def save_data(self, df: pd.DataFrame, file_path: str, format_type: DataFormat = None, **kwargs) -> bool:
        """保存数据"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 自动检测格式
        if format_type is None:
            format_type = self._detect_format(file_path)
        
        try:
            self.logger.info(f"保存数据到文件: {file_path} (格式: {format_type.value})")
            
            # 备份现有文件
            if file_path.exists() and self.config.get('auto_backup'):
                backup_path = file_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}{file_path.suffix}')
                file_path.rename(backup_path)
                self.logger.info(f"已备份原文件: {backup_path}")
            
            # 根据格式保存数据
            if format_type == DataFormat.CSV:
                df.to_csv(file_path, index=False, encoding=kwargs.get('encoding', 'utf-8'), **kwargs)
            elif format_type == DataFormat.JSON:
                df.to_json(file_path, orient='records', force_ascii=False, indent=2, **kwargs)
            elif format_type == DataFormat.EXCEL:
                if not EXCEL_AVAILABLE:
                    raise ImportError("需要安装 openpyxl 来处理Excel文件")
                df.to_excel(file_path, index=False, **kwargs)
            elif format_type == DataFormat.PARQUET:
                df.to_parquet(file_path, index=False, **kwargs)
            elif format_type == DataFormat.PICKLE:
                df.to_pickle(file_path)
            elif format_type == DataFormat.TSV:
                df.to_csv(file_path, sep='\t', index=False, encoding=kwargs.get('encoding', 'utf-8'), **kwargs)
            else:
                raise ValueError(f"不支持的数据格式: {format_type}")
            
            self.logger.info(f"数据保存完成: {file_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")
            return False
    
    def _detect_format(self, file_path: Path) -> DataFormat:
        """检测文件格式"""
        suffix = file_path.suffix.lower()
        
        format_map = {
            '.csv': DataFormat.CSV,
            '.json': DataFormat.JSON,
            '.xlsx': DataFormat.EXCEL,
            '.xls': DataFormat.EXCEL,
            '.parquet': DataFormat.PARQUET,
            '.pkl': DataFormat.PICKLE,
            '.pickle': DataFormat.PICKLE,
            '.tsv': DataFormat.TSV,
            '.txt': DataFormat.TSV
        }
        
        return format_map.get(suffix, DataFormat.CSV)
    
    def _get_cache_key(self, file_path: Path) -> str:
        """生成缓存键"""
        stat = file_path.stat()
        content = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def analyze_data_quality(self, df: pd.DataFrame) -> DataQualityReport:
        """分析数据质量"""
        try:
            # 基本统计
            total_rows = len(df)
            total_columns = len(df.columns)
            
            # 缺失值统计
            missing_values = df.isnull().sum().to_dict()
            
            # 重复行统计
            duplicate_rows = df.duplicated().sum()
            
            # 数据类型
            data_types = df.dtypes.astype(str).to_dict()
            
            # 内存使用
            memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
            
            # 质量问题检测
            issues = []
            recommendations = []
            
            # 检查缺失值
            missing_ratio = sum(missing_values.values()) / (total_rows * total_columns)
            if missing_ratio > 0.1:
                issues.append(f"缺失值比例过高: {missing_ratio:.2%}")
                recommendations.append("考虑填充或删除缺失值")
            
            # 检查重复行
            if duplicate_rows > 0:
                issues.append(f"存在 {duplicate_rows} 行重复数据")
                recommendations.append("删除重复行")
            
            # 检查数据类型
            for col, dtype in data_types.items():
                if dtype == 'object':
                    # 检查是否应该是数值类型
                    try:
                        pd.to_numeric(df[col], errors='raise')
                        issues.append(f"列 '{col}' 可能应该是数值类型")
                        recommendations.append(f"转换列 '{col}' 为数值类型")
                    except:
                        pass
            
            # 检查异常值
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
                
                if len(outliers) > total_rows * 0.05:  # 超过5%的异常值
                    issues.append(f"列 '{col}' 存在较多异常值: {len(outliers)} 个")
                    recommendations.append(f"检查并处理列 '{col}' 的异常值")
            
            # 计算质量分数
            quality_score = 1.0
            quality_score -= missing_ratio * 0.3  # 缺失值影响
            quality_score -= (duplicate_rows / total_rows) * 0.2  # 重复行影响
            quality_score -= len(issues) * 0.1  # 问题数量影响
            quality_score = max(0.0, min(1.0, quality_score))
            
            return DataQualityReport(
                total_rows=total_rows,
                total_columns=total_columns,
                missing_values=missing_values,
                duplicate_rows=duplicate_rows,
                data_types=data_types,
                memory_usage=memory_usage,
                quality_score=quality_score,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            self.logger.error(f"数据质量分析失败: {e}")
            raise
    
    def create_processing_job(self, name: str, input_file: str, output_file: str, 
                            operations: List[Dict[str, Any]]) -> str:
        """创建数据处理任务"""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.jobs)}"
        
        job = ProcessingJob(
            job_id=job_id,
            name=name,
            input_file=input_file,
            output_file=output_file,
            operations=operations,
            status=ProcessingStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.jobs[job_id] = job
        self._save_jobs()
        
        self.logger.info(f"创建处理任务: {job_id} - {name}")
        return job_id
    
    def execute_job(self, job_id: str) -> bool:
        """执行处理任务"""
        if job_id not in self.jobs:
            self.logger.error(f"任务不存在: {job_id}")
            return False
        
        job = self.jobs[job_id]
        
        try:
            job.status = ProcessingStatus.PROCESSING
            job.started_at = datetime.now()
            job.progress = 0.0
            self._save_jobs()
            
            self.logger.info(f"开始执行任务: {job_id} - {job.name}")
            
            # 加载输入数据
            df = self.load_data(job.input_file)
            job.progress = 10.0
            self._save_jobs()
            
            # 执行操作
            total_operations = len(job.operations)
            for i, operation in enumerate(job.operations):
                operation_name = operation.get('name')
                operation_params = operation.get('params', {})
                
                self.logger.info(f"执行操作: {operation_name}")
                
                if operation_name in self.processing_functions:
                    df = self.processing_functions[operation_name](df, **operation_params)
                else:
                    raise ValueError(f"未知的操作: {operation_name}")
                
                # 更新进度
                job.progress = 10.0 + (i + 1) / total_operations * 80.0
                self._save_jobs()
            
            # 保存输出数据
            self.save_data(df, job.output_file)
            job.progress = 100.0
            
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.now()
            self._save_jobs()
            
            self.logger.info(f"任务执行完成: {job_id}")
            return True
        
        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self._save_jobs()
            
            self.logger.error(f"任务执行失败 {job_id}: {e}")
            return False
    
    # 数据处理函数
    def _remove_duplicates(self, df: pd.DataFrame, subset: List[str] = None, keep: str = 'first') -> pd.DataFrame:
        """删除重复行"""
        return df.drop_duplicates(subset=subset, keep=keep)
    
    def _fill_missing_values(self, df: pd.DataFrame, method: str = 'mean', columns: List[str] = None) -> pd.DataFrame:
        """填充缺失值"""
        if columns is None:
            columns = df.columns
        
        df_copy = df.copy()
        
        for col in columns:
            if col not in df_copy.columns:
                continue
            
            if method == 'mean' and df_copy[col].dtype in ['int64', 'float64']:
                df_copy[col].fillna(df_copy[col].mean(), inplace=True)
            elif method == 'median' and df_copy[col].dtype in ['int64', 'float64']:
                df_copy[col].fillna(df_copy[col].median(), inplace=True)
            elif method == 'mode':
                df_copy[col].fillna(df_copy[col].mode().iloc[0] if not df_copy[col].mode().empty else '', inplace=True)
            elif method == 'forward':
                df_copy[col].fillna(method='ffill', inplace=True)
            elif method == 'backward':
                df_copy[col].fillna(method='bfill', inplace=True)
            elif isinstance(method, (str, int, float)):
                df_copy[col].fillna(method, inplace=True)
        
        return df_copy
    
    def _remove_outliers(self, df: pd.DataFrame, columns: List[str] = None, method: str = 'iqr') -> pd.DataFrame:
        """删除异常值"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns
        
        df_copy = df.copy()
        
        for col in columns:
            if col not in df_copy.columns:
                continue
            
            if method == 'iqr':
                Q1 = df_copy[col].quantile(0.25)
                Q3 = df_copy[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                df_copy = df_copy[(df_copy[col] >= lower_bound) & (df_copy[col] <= upper_bound)]
            elif method == 'zscore':
                z_scores = np.abs(statistics.zscore(df_copy[col].dropna()))
                df_copy = df_copy[z_scores < 3]
        
        return df_copy
    
    def _normalize_text(self, df: pd.DataFrame, columns: List[str] = None, operations: List[str] = None) -> pd.DataFrame:
        """文本标准化"""
        if columns is None:
            columns = df.select_dtypes(include=['object']).columns
        
        if operations is None:
            operations = ['strip', 'lower']
        
        df_copy = df.copy()
        
        for col in columns:
            if col not in df_copy.columns:
                continue
            
            for operation in operations:
                if operation == 'strip':
                    df_copy[col] = df_copy[col].astype(str).str.strip()
                elif operation == 'lower':
                    df_copy[col] = df_copy[col].astype(str).str.lower()
                elif operation == 'upper':
                    df_copy[col] = df_copy[col].astype(str).str.upper()
                elif operation == 'title':
                    df_copy[col] = df_copy[col].astype(str).str.title()
                elif operation == 'remove_special':
                    df_copy[col] = df_copy[col].astype(str).str.replace(r'[^\w\s]', '', regex=True)
        
        return df_copy
    
    def _convert_data_types(self, df: pd.DataFrame, type_mapping: Dict[str, str]) -> pd.DataFrame:
        """转换数据类型"""
        df_copy = df.copy()
        
        for col, dtype in type_mapping.items():
            if col not in df_copy.columns:
                continue
            
            try:
                if dtype == 'int':
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').astype('Int64')
                elif dtype == 'float':
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce')
                elif dtype == 'datetime':
                    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                elif dtype == 'category':
                    df_copy[col] = df_copy[col].astype('category')
                elif dtype == 'string':
                    df_copy[col] = df_copy[col].astype(str)
            except Exception as e:
                self.logger.warning(f"转换列 {col} 到 {dtype} 失败: {e}")
        
        return df_copy
    
    def _filter_rows(self, df: pd.DataFrame, conditions: List[Dict[str, Any]]) -> pd.DataFrame:
        """过滤行"""
        df_copy = df.copy()
        
        for condition in conditions:
            column = condition.get('column')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if column not in df_copy.columns:
                continue
            
            if operator == '==':
                df_copy = df_copy[df_copy[column] == value]
            elif operator == '!=':
                df_copy = df_copy[df_copy[column] != value]
            elif operator == '>':
                df_copy = df_copy[df_copy[column] > value]
            elif operator == '>=':
                df_copy = df_copy[df_copy[column] >= value]
            elif operator == '<':
                df_copy = df_copy[df_copy[column] < value]
            elif operator == '<=':
                df_copy = df_copy[df_copy[column] <= value]
            elif operator == 'in':
                df_copy = df_copy[df_copy[column].isin(value)]
            elif operator == 'not_in':
                df_copy = df_copy[~df_copy[column].isin(value)]
            elif operator == 'contains':
                df_copy = df_copy[df_copy[column].astype(str).str.contains(str(value), na=False)]
        
        return df_copy
    
    def _select_columns(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """选择列"""
        available_columns = [col for col in columns if col in df.columns]
        return df[available_columns]
    
    def _rename_columns(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """重命名列"""
        return df.rename(columns=column_mapping)
    
    def _sort_data(self, df: pd.DataFrame, columns: List[str], ascending: Union[bool, List[bool]] = True) -> pd.DataFrame:
        """排序数据"""
        available_columns = [col for col in columns if col in df.columns]
        if available_columns:
            return df.sort_values(by=available_columns, ascending=ascending)
        return df
    
    def _group_by_operation(self, df: pd.DataFrame, group_columns: List[str], 
                          agg_operations: Dict[str, Union[str, List[str]]]) -> pd.DataFrame:
        """分组操作"""
        available_group_columns = [col for col in group_columns if col in df.columns]
        if not available_group_columns:
            return df
        
        return df.groupby(available_group_columns).agg(agg_operations).reset_index()
    
    def _merge_data(self, df: pd.DataFrame, other_file: str, on: Union[str, List[str]], 
                   how: str = 'inner') -> pd.DataFrame:
        """合并数据"""
        other_df = self.load_data(other_file)
        return df.merge(other_df, on=on, how=how)
    
    def _create_pivot_table(self, df: pd.DataFrame, index: Union[str, List[str]], 
                          columns: Union[str, List[str]], values: str, 
                          aggfunc: str = 'mean') -> pd.DataFrame:
        """创建透视表"""
        return df.pivot_table(index=index, columns=columns, values=values, aggfunc=aggfunc)
    
    def _calculate_statistics(self, df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
        """计算统计信息"""
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns
        
        stats_df = df[columns].describe()
        return stats_df
    
    def _create_features(self, df: pd.DataFrame, feature_definitions: List[Dict[str, Any]]) -> pd.DataFrame:
        """创建特征"""
        df_copy = df.copy()
        
        for feature_def in feature_definitions:
            feature_name = feature_def.get('name')
            feature_type = feature_def.get('type')
            params = feature_def.get('params', {})
            
            if feature_type == 'arithmetic':
                # 算术运算特征
                expression = params.get('expression')
                try:
                    df_copy[feature_name] = df_copy.eval(expression)
                except Exception as e:
                    self.logger.warning(f"创建算术特征失败 {feature_name}: {e}")
            
            elif feature_type == 'datetime':
                # 日期时间特征
                source_column = params.get('source_column')
                extract_part = params.get('extract_part')  # year, month, day, hour, etc.
                
                if source_column in df_copy.columns:
                    try:
                        dt_series = pd.to_datetime(df_copy[source_column])
                        df_copy[feature_name] = getattr(dt_series.dt, extract_part)
                    except Exception as e:
                        self.logger.warning(f"创建日期特征失败 {feature_name}: {e}")
            
            elif feature_type == 'categorical':
                # 分类特征
                source_column = params.get('source_column')
                bins = params.get('bins')
                labels = params.get('labels')
                
                if source_column in df_copy.columns:
                    try:
                        df_copy[feature_name] = pd.cut(df_copy[source_column], bins=bins, labels=labels)
                    except Exception as e:
                        self.logger.warning(f"创建分类特征失败 {feature_name}: {e}")
        
        return df_copy
    
    def _validate_data(self, df: pd.DataFrame, validation_rules: List[Dict[str, Any]]) -> pd.DataFrame:
        """数据验证"""
        df_copy = df.copy()
        validation_results = []
        
        for rule in validation_rules:
            rule_name = rule.get('name')
            rule_type = rule.get('type')
            params = rule.get('params', {})
            
            if rule_type == 'not_null':
                columns = params.get('columns', [])
                for col in columns:
                    if col in df_copy.columns:
                        null_count = df_copy[col].isnull().sum()
                        validation_results.append({
                            'rule': rule_name,
                            'column': col,
                            'passed': null_count == 0,
                            'details': f"空值数量: {null_count}"
                        })
            
            elif rule_type == 'range':
                column = params.get('column')
                min_value = params.get('min')
                max_value = params.get('max')
                
                if column in df_copy.columns:
                    out_of_range = df_copy[(df_copy[column] < min_value) | (df_copy[column] > max_value)]
                    validation_results.append({
                        'rule': rule_name,
                        'column': column,
                        'passed': len(out_of_range) == 0,
                        'details': f"超出范围的记录数: {len(out_of_range)}"
                    })
            
            elif rule_type == 'unique':
                column = params.get('column')
                
                if column in df_copy.columns:
                    duplicate_count = df_copy[column].duplicated().sum()
                    validation_results.append({
                        'rule': rule_name,
                        'column': column,
                        'passed': duplicate_count == 0,
                        'details': f"重复值数量: {duplicate_count}"
                    })
        
        # 将验证结果添加到元数据
        df_copy.attrs['validation_results'] = validation_results
        
        return df_copy
    
    def generate_report(self, df: pd.DataFrame, output_file: str = None) -> Dict[str, Any]:
        """生成数据报告"""
        try:
            # 数据质量分析
            quality_report = self.analyze_data_quality(df)
            
            # 基本统计
            numeric_stats = df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {}
            
            # 分类统计
            categorical_stats = {}
            for col in df.select_dtypes(include=['object', 'category']).columns:
                categorical_stats[col] = {
                    'unique_count': df[col].nunique(),
                    'top_values': df[col].value_counts().head(10).to_dict()
                }
            
            # 相关性分析
            correlation_matrix = {}
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 1:
                correlation_matrix = df[numeric_cols].corr().to_dict()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'data_shape': {'rows': len(df), 'columns': len(df.columns)},
                'quality_report': asdict(quality_report),
                'numeric_statistics': numeric_stats,
                'categorical_statistics': categorical_stats,
                'correlation_matrix': correlation_matrix,
                'column_info': {
                    col: {
                        'dtype': str(df[col].dtype),
                        'null_count': int(df[col].isnull().sum()),
                        'null_percentage': float(df[col].isnull().sum() / len(df) * 100)
                    }
                    for col in df.columns
                }
            }
            
            # 保存报告
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                
                self.logger.info(f"数据报告已保存: {output_path}")
            
            return report
        
        except Exception as e:
            self.logger.error(f"生成数据报告失败: {e}")
            raise
    
    def create_visualization(self, df: pd.DataFrame, chart_type: str, output_file: str = None, **kwargs) -> bool:
        """创建数据可视化"""
        if not PLOTTING_AVAILABLE:
            self.logger.error("matplotlib 和 seaborn 不可用，无法创建可视化")
            return False
        
        try:
            plt.figure(figsize=kwargs.get('figsize', (10, 6)))
            
            if chart_type == 'histogram':
                column = kwargs.get('column')
                if column and column in df.columns:
                    plt.hist(df[column].dropna(), bins=kwargs.get('bins', 30))
                    plt.title(f'{column} 分布')
                    plt.xlabel(column)
                    plt.ylabel('频次')
            
            elif chart_type == 'scatter':
                x_col = kwargs.get('x_column')
                y_col = kwargs.get('y_column')
                if x_col and y_col and x_col in df.columns and y_col in df.columns:
                    plt.scatter(df[x_col], df[y_col], alpha=0.6)
                    plt.xlabel(x_col)
                    plt.ylabel(y_col)
                    plt.title(f'{x_col} vs {y_col}')
            
            elif chart_type == 'boxplot':
                column = kwargs.get('column')
                if column and column in df.columns:
                    plt.boxplot(df[column].dropna())
                    plt.title(f'{column} 箱线图')
                    plt.ylabel(column)
            
            elif chart_type == 'correlation_heatmap':
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 1:
                    correlation_matrix = df[numeric_cols].corr()
                    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
                    plt.title('相关性热力图')
            
            elif chart_type == 'bar':
                column = kwargs.get('column')
                if column and column in df.columns:
                    value_counts = df[column].value_counts().head(kwargs.get('top_n', 10))
                    plt.bar(range(len(value_counts)), value_counts.values)
                    plt.xticks(range(len(value_counts)), value_counts.index, rotation=45)
                    plt.title(f'{column} 分布')
                    plt.ylabel('计数')
            
            plt.tight_layout()
            
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"可视化图表已保存: {output_path}")
            
            plt.close()
            return True
        
        except Exception as e:
            self.logger.error(f"创建可视化失败: {e}")
            plt.close()
            return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        return {
            'job_id': job.job_id,
            'name': job.name,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message
        }
    
    def list_jobs(self, status_filter: ProcessingStatus = None) -> List[Dict[str, Any]]:
        """列出所有任务"""
        jobs = []
        
        for job in self.jobs.values():
            if status_filter is None or job.status == status_filter:
                jobs.append({
                    'job_id': job.job_id,
                    'name': job.name,
                    'status': job.status.value,
                    'progress': job.progress,
                    'created_at': job.created_at.isoformat(),
                    'input_file': job.input_file,
                    'output_file': job.output_file
                })
        
        return sorted(jobs, key=lambda x: x['created_at'], reverse=True)
    
    def cancel_job(self, job_id: str) -> bool:
        """取消任务"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        if job.status in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
            job.status = ProcessingStatus.CANCELLED
            job.completed_at = datetime.now()
            self._save_jobs()
            
            self.logger.info(f"任务已取消: {job_id}")
            return True
        
        return False
    
    def delete_job(self, job_id: str) -> bool:
        """删除任务"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_jobs()
            
            self.logger.info(f"任务已删除: {job_id}")
            return True
        
        return False
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        self.logger.info("数据缓存已清空")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 数据处理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--load', help='加载数据文件')
    parser.add_argument('--format', choices=['csv', 'json', 'excel', 'parquet', 'pickle', 'tsv'], 
                       help='指定数据格式')
    parser.add_argument('--analyze', help='分析数据质量')
    parser.add_argument('--report', help='生成数据报告')
    parser.add_argument('--visualize', help='创建可视化图表')
    parser.add_argument('--chart-type', choices=['histogram', 'scatter', 'boxplot', 'correlation_heatmap', 'bar'],
                       default='histogram', help='图表类型')
    parser.add_argument('--column', help='指定列名')
    parser.add_argument('--x-column', help='X轴列名')
    parser.add_argument('--y-column', help='Y轴列名')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--jobs', action='store_true', help='列出所有任务')
    parser.add_argument('--job-status', help='查看任务状态')
    parser.add_argument('--execute-job', help='执行任务')
    parser.add_argument('--cancel-job', help='取消任务')
    parser.add_argument('--delete-job', help='删除任务')
    parser.add_argument('--clear-cache', action='store_true', help='清空缓存')
    
    args = parser.parse_args()
    
    processor = DataProcessor(args.project_root)
    
    # 加载数据
    if args.load:
        try:
            format_type = DataFormat(args.format) if args.format else None
            df = processor.load_data(args.load, format_type)
            print(f"✅ 数据加载成功: {df.shape[0]} 行, {df.shape[1]} 列")
            
            # 显示基本信息
            print("\n📊 数据概览:")
            print(df.head())
            print(f"\n📋 数据类型:")
            print(df.dtypes)
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
        return
    
    # 分析数据质量
    if args.analyze:
        try:
            format_type = DataFormat(args.format) if args.format else None
            df = processor.load_data(args.analyze, format_type)
            quality_report = processor.analyze_data_quality(df)
            
            print("📊 数据质量分析报告")
            print("="*50)
            print(f"总行数: {quality_report.total_rows}")
            print(f"总列数: {quality_report.total_columns}")
            print(f"重复行数: {quality_report.duplicate_rows}")
            print(f"内存使用: {quality_report.memory_usage:.2f} MB")
            print(f"质量分数: {quality_report.quality_score:.2f}")
            
            print(f"\n🔍 缺失值统计:")
            for col, count in quality_report.missing_values.items():
                if count > 0:
                    print(f"  {col}: {count}")
            
            if quality_report.issues:
                print(f"\n⚠️ 发现的问题:")
                for issue in quality_report.issues:
                    print(f"  - {issue}")
            
            if quality_report.recommendations:
                print(f"\n💡 建议:")
                for rec in quality_report.recommendations:
                    print(f"  - {rec}")
            
        except Exception as e:
            print(f"❌ 数据质量分析失败: {e}")
        return
    
    # 生成数据报告
    if args.report:
        try:
            format_type = DataFormat(args.format) if args.format else None
            df = processor.load_data(args.report, format_type)
            
            output_file = args.output or f"data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report = processor.generate_report(df, output_file)
            
            print(f"✅ 数据报告已生成: {output_file}")
            print(f"数据形状: {report['data_shape']['rows']} 行 x {report['data_shape']['columns']} 列")
            print(f"质量分数: {report['quality_report']['quality_score']:.2f}")
            
        except Exception as e:
            print(f"❌ 生成数据报告失败: {e}")
        return
    
    # 创建可视化
    if args.visualize:
        try:
            format_type = DataFormat(args.format) if args.format else None
            df = processor.load_data(args.visualize, format_type)
            
            output_file = args.output or f"visualization_{args.chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            kwargs = {}
            if args.column:
                kwargs['column'] = args.column
            if args.x_column:
                kwargs['x_column'] = args.x_column
            if args.y_column:
                kwargs['y_column'] = args.y_column
            
            success = processor.create_visualization(df, args.chart_type, output_file, **kwargs)
            
            if success:
                print(f"✅ 可视化图表已创建: {output_file}")
            else:
                print("❌ 创建可视化图表失败")
            
        except Exception as e:
            print(f"❌ 创建可视化失败: {e}")
        return
    
    # 列出任务
    if args.jobs:
        jobs = processor.list_jobs()
        
        if jobs:
            print("📋 处理任务列表:")
            print("="*80)
            for job in jobs:
                print(f"ID: {job['job_id']}")
                print(f"名称: {job['name']}")
                print(f"状态: {job['status']}")
                print(f"进度: {job['progress']:.1f}%")
                print(f"创建时间: {job['created_at']}")
                print(f"输入文件: {job['input_file']}")
                print(f"输出文件: {job['output_file']}")
                print("-" * 80)
        else:
            print("📋 暂无处理任务")
        return
    
    # 查看任务状态
    if args.job_status:
        status = processor.get_job_status(args.job_status)
        
        if status:
            print(f"📊 任务状态: {args.job_status}")
            print("="*40)
            print(f"名称: {status['name']}")
            print(f"状态: {status['status']}")
            print(f"进度: {status['progress']:.1f}%")
            print(f"创建时间: {status['created_at']}")
            if status['started_at']:
                print(f"开始时间: {status['started_at']}")
            if status['completed_at']:
                print(f"完成时间: {status['completed_at']}")
            if status['error_message']:
                print(f"错误信息: {status['error_message']}")
        else:
            print(f"❌ 任务不存在: {args.job_status}")
        return
    
    # 执行任务
    if args.execute_job:
        success = processor.execute_job(args.execute_job)
        
        if success:
            print(f"✅ 任务执行完成: {args.execute_job}")
        else:
            print(f"❌ 任务执行失败: {args.execute_job}")
        return
    
    # 取消任务
    if args.cancel_job:
        success = processor.cancel_job(args.cancel_job)
        
        if success:
            print(f"✅ 任务已取消: {args.cancel_job}")
        else:
            print(f"❌ 取消任务失败: {args.cancel_job}")
        return
    
    # 删除任务
    if args.delete_job:
        success = processor.delete_job(args.delete_job)
        
        if success:
            print(f"✅ 任务已删除: {args.delete_job}")
        else:
            print(f"❌ 删除任务失败: {args.delete_job}")
        return
    
    # 清空缓存
    if args.clear_cache:
        processor.clear_cache()
        print("✅ 数据缓存已清空")
        return
    
    # 默认显示状态
    print("📊 数据处理器")
    print("="*30)
    print(f"项目路径: {processor.project_root}")
    print(f"数据目录: {processor.data_dir}")
    print(f"缓存项目: {len(processor.cache)}")
    print(f"处理任务: {len(processor.jobs)}")
    
    # 显示最近的任务
    recent_jobs = processor.list_jobs()[:5]
    if recent_jobs:
        print(f"\n📋 最近任务:")
        for job in recent_jobs:
            print(f"  {job['job_id']}: {job['name']} ({job['status']})")

if __name__ == "__main__":
    main()