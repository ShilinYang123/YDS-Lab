#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YDS-Lab 部署管理工具
提供自动化部署、环境管理、发布流程和回滚功能
适配YDS-Lab项目结构和AI Agent协作需求
"""

import os
import sys
import json
import yaml
import time
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import threading
import hashlib
import zipfile
import tarfile

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

@dataclass
class DeploymentTarget:
    """部署目标配置"""
    name: str
    type: str  # local, ssh, docker, k8s, aws, azure, gcp
    host: str = ''
    port: int = 22
    username: str = ''
    password: str = ''
    key_file: str = ''
    docker_image: str = ''
    k8s_namespace: str = 'default'
    aws_region: str = 'us-east-1'
    environment: str = 'production'
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

@dataclass
class DeploymentJob:
    """部署任务"""
    id: str
    name: str
    target: str
    status: str = 'pending'  # pending, running, success, failed, cancelled
    start_time: datetime = None
    end_time: datetime = None
    log_file: str = ''
    error: str = ''
    rollback_id: str = ''
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

@dataclass
class DeploymentHistory:
    """部署历史记录"""
    id: str
    job_id: str
    target: str
    version: str
    timestamp: datetime
    status: str
    duration: float = 0
    files_changed: int = 0
    rollback_available: bool = True
    backup_path: str = ''

class DeploymentManager:
    """部署管理器"""
    
    def __init__(self, project_root: str = None):
        """初始化部署管理器"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.config_dir = self.project_root / "Struc" / "GeneralOffice" / "config"
        self.data_dir = self.project_root / "data" / "deployment"
        self.logs_dir = self.project_root / "logs" / "deployment"
        self.backups_dir = self.project_root / "backups" / "deployment"
        self.scripts_dir = self.project_root / "scripts" / "deployment"
        
        # 创建目录
        for directory in [self.data_dir, self.logs_dir, self.backups_dir, self.scripts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        self.targets = self._load_targets()
        
        # 初始化状态
        self.jobs = {}
        self.history = []
        self.running_jobs = {}
        
        # 设置日志
        self._setup_logging()
        
        # 加载历史记录
        self._load_history()
        
        # 初始化Docker客户端
        self.docker_client = None
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                self.logger.warning(f"Docker客户端初始化失败: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载部署配置"""
        config_file = self.config_dir / "deployment_config.yaml"
        
        default_config = {
            'build': {
                'enabled': True,
                'command': 'npm run build',
                'output_dir': 'dist',
                'clean_before_build': True,
                'parallel_builds': False
            },
            'backup': {
                'enabled': True,
                'keep_backups': 5,
                'compress': True,
                'exclude_patterns': [
                    '*.log',
                    '*.tmp',
                    'node_modules',
                    '.git',
                    '__pycache__'
                ]
            },
            'deployment': {
                'timeout': 300,
                'retry_count': 3,
                'retry_delay': 10,
                'parallel_deployments': 2,
                'health_check': {
                    'enabled': True,
                    'url': '/health',
                    'timeout': 30,
                    'retries': 5
                },
                'rollback': {
                    'auto_rollback': True,
                    'rollback_timeout': 60
                }
            },
            'notifications': {
                'enabled': False,
                'webhook_url': '',
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'recipients': []
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': '',
                    'channel': '#deployments'
                }
            },
            'security': {
                'verify_checksums': True,
                'encrypt_backups': False,
                'secure_transfer': True,
                'audit_log': True
            },
            'monitoring': {
                'enabled': True,
                'metrics_endpoint': '',
                'log_aggregation': False,
                'performance_tracking': True
            },
            'log_level': 'INFO'
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载部署配置失败: {e}")
        
        return default_config
    
    def _load_targets(self) -> Dict[str, DeploymentTarget]:
        """加载部署目标配置"""
        targets = {}
        
        targets_file = self.config_dir / "deployment_targets.yaml"
        
        if targets_file.exists():
            try:
                with open(targets_file, 'r', encoding='utf-8') as f:
                    targets_config = yaml.safe_load(f)
                    
                    for name, config in targets_config.items():
                        targets[name] = DeploymentTarget(
                            name=name,
                            **config
                        )
            except Exception as e:
                print(f"⚠️ 加载部署目标配置失败: {e}")
        
        return targets
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.logs_dir / f"deployment_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _load_history(self):
        """加载部署历史"""
        history_file = self.data_dir / "deployment_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    
                    for item in history_data:
                        # 转换时间戳
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                        
                        self.history.append(DeploymentHistory(**item))
            except Exception as e:
                self.logger.error(f"加载部署历史失败: {e}")
    
    def _save_history(self):
        """保存部署历史"""
        history_file = self.data_dir / "deployment_history.json"
        
        try:
            history_data = []
            for item in self.history:
                data = asdict(item)
                data['timestamp'] = item.timestamp.isoformat()
                history_data.append(data)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self.logger.error(f"保存部署历史失败: {e}")
    
    def create_deployment_job(self, name: str, target: str, config: Dict[str, Any] = None) -> str:
        """创建部署任务"""
        job_id = f"deploy_{int(time.time())}_{hash(name) % 10000:04d}"
        
        job = DeploymentJob(
            id=job_id,
            name=name,
            target=target,
            config=config or {}
        )
        
        self.jobs[job_id] = job
        
        self.logger.info(f"部署任务已创建: {job_id} - {name}")
        return job_id
    
    def start_deployment(self, job_id: str) -> bool:
        """启动部署任务"""
        if job_id not in self.jobs:
            self.logger.error(f"部署任务不存在: {job_id}")
            return False
        
        job = self.jobs[job_id]
        
        if job.status != 'pending':
            self.logger.error(f"部署任务状态不正确: {job.status}")
            return False
        
        if job.target not in self.targets:
            self.logger.error(f"部署目标不存在: {job.target}")
            return False
        
        # 检查并发限制
        running_count = sum(1 for j in self.jobs.values() if j.status == 'running')
        if running_count >= self.config['deployment']['parallel_deployments']:
            self.logger.warning(f"达到并发部署限制: {running_count}")
            return False
        
        # 更新任务状态
        job.status = 'running'
        job.start_time = datetime.now()
        job.log_file = str(self.logs_dir / f"deploy_{job_id}.log")
        
        # 启动部署线程
        thread = threading.Thread(
            target=self._run_deployment,
            args=(job_id,),
            daemon=True
        )
        thread.start()
        
        self.running_jobs[job_id] = thread
        
        self.logger.info(f"部署任务已启动: {job_id}")
        return True
    
    def _run_deployment(self, job_id: str):
        """运行部署任务"""
        job = self.jobs[job_id]
        target = self.targets[job.target]
        
        try:
            # 创建备份
            if self.config['backup']['enabled']:
                backup_id = self._create_backup(target)
                job.rollback_id = backup_id
            
            # 构建项目
            if self.config['build']['enabled']:
                self._build_project(job)
            
            # 执行部署
            success = self._deploy_to_target(job, target)
            
            if success:
                # 健康检查
                if self.config['deployment']['health_check']['enabled']:
                    health_ok = self._health_check(target)
                    
                    if not health_ok and self.config['deployment']['rollback']['auto_rollback']:
                        self.logger.warning(f"健康检查失败，开始自动回滚: {job_id}")
                        self._rollback_deployment(job_id)
                        success = False
                
                if success:
                    job.status = 'success'
                    self.logger.info(f"部署成功: {job_id}")
                    
                    # 记录历史
                    self._record_deployment_history(job, target, 'success')
                    
                    # 发送通知
                    self._send_notification(job, 'success')
                else:
                    job.status = 'failed'
                    job.error = "健康检查失败"
            else:
                job.status = 'failed'
                self.logger.error(f"部署失败: {job_id}")
                
                # 发送通知
                self._send_notification(job, 'failed')
        
        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            self.logger.error(f"部署异常: {job_id} - {e}")
            
            # 发送通知
            self._send_notification(job, 'failed')
        
        finally:
            job.end_time = datetime.now()
            
            # 清理运行状态
            if job_id in self.running_jobs:
                del self.running_jobs[job_id]
    
    def _build_project(self, job: DeploymentJob):
        """构建项目"""
        self.logger.info(f"开始构建项目: {job.id}")
        
        build_config = self.config['build']
        
        # 清理构建目录
        if build_config['clean_before_build']:
            output_dir = self.project_root / build_config['output_dir']
            if output_dir.exists():
                shutil.rmtree(output_dir)
        
        # 执行构建命令
        try:
            result = subprocess.run(
                build_config['command'],
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.config['deployment']['timeout']
            )
            
            if result.returncode != 0:
                raise Exception(f"构建失败: {result.stderr}")
            
            self.logger.info(f"项目构建完成: {job.id}")
        
        except subprocess.TimeoutExpired:
            raise Exception("构建超时")
        except Exception as e:
            raise Exception(f"构建失败: {e}")
    
    def _deploy_to_target(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """部署到目标环境"""
        self.logger.info(f"开始部署到目标: {target.name}")
        
        try:
            if target.type == 'local':
                return self._deploy_local(job, target)
            elif target.type == 'ssh':
                return self._deploy_ssh(job, target)
            elif target.type == 'docker':
                return self._deploy_docker(job, target)
            elif target.type == 'k8s':
                return self._deploy_k8s(job, target)
            elif target.type == 'aws':
                return self._deploy_aws(job, target)
            else:
                raise Exception(f"不支持的部署类型: {target.type}")
        
        except Exception as e:
            self.logger.error(f"部署失败: {e}")
            job.error = str(e)
            return False
    
    def _deploy_local(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """本地部署"""
        try:
            source_dir = self.project_root / self.config['build']['output_dir']
            target_dir = Path(target.config.get('target_dir', '/tmp/deployment'))
            
            # 创建目标目录
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            if source_dir.exists():
                shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
            else:
                # 复制整个项目
                for item in self.project_root.iterdir():
                    if item.name not in ['.git', 'node_modules', '__pycache__']:
                        if item.is_dir():
                            shutil.copytree(item, target_dir / item.name, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, target_dir)
            
            # 执行部署后脚本
            post_deploy_script = target.config.get('post_deploy_script')
            if post_deploy_script:
                subprocess.run(post_deploy_script, shell=True, cwd=target_dir, check=True)
            
            return True
        
        except Exception as e:
            self.logger.error(f"本地部署失败: {e}")
            return False
    
    def _deploy_ssh(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """SSH部署"""
        if not SSH_AVAILABLE:
            self.logger.error("paramiko库未安装，SSH部署不可用")
            return False
        
        try:
            # 创建SSH连接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 连接参数
            connect_kwargs = {
                'hostname': target.host,
                'port': target.port,
                'username': target.username
            }
            
            if target.key_file:
                connect_kwargs['key_filename'] = target.key_file
            elif target.password:
                connect_kwargs['password'] = target.password
            
            ssh.connect(**connect_kwargs)
            
            # 创建SFTP连接
            sftp = ssh.open_sftp()
            
            # 上传文件
            source_dir = self.project_root / self.config['build']['output_dir']
            remote_dir = target.config.get('remote_dir', '/tmp/deployment')
            
            # 创建远程目录
            stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
            stdout.channel.recv_exit_status()
            
            # 递归上传文件
            self._upload_directory(sftp, source_dir, remote_dir)
            
            # 执行部署脚本
            deploy_script = target.config.get('deploy_script')
            if deploy_script:
                stdin, stdout, stderr = ssh.exec_command(f'cd {remote_dir} && {deploy_script}')
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode()
                    raise Exception(f"部署脚本执行失败: {error_output}")
            
            # 关闭连接
            sftp.close()
            ssh.close()
            
            return True
        
        except Exception as e:
            self.logger.error(f"SSH部署失败: {e}")
            return False
    
    def _upload_directory(self, sftp, local_dir: Path, remote_dir: str):
        """递归上传目录"""
        for item in local_dir.iterdir():
            local_path = str(item)
            remote_path = f"{remote_dir}/{item.name}"
            
            if item.is_dir():
                # 创建远程目录
                try:
                    sftp.mkdir(remote_path)
                except:
                    pass  # 目录可能已存在
                
                # 递归上传
                self._upload_directory(sftp, item, remote_path)
            else:
                # 上传文件
                sftp.put(local_path, remote_path)
    
    def _deploy_docker(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """Docker部署"""
        if not DOCKER_AVAILABLE or not self.docker_client:
            self.logger.error("Docker不可用")
            return False
        
        try:
            # 构建Docker镜像
            image_name = target.docker_image or f"yds-lab-{job.name}:latest"
            
            dockerfile_path = self.project_root / "Dockerfile"
            if not dockerfile_path.exists():
                # 创建默认Dockerfile
                self._create_default_dockerfile()
            
            # 构建镜像
            self.logger.info(f"构建Docker镜像: {image_name}")
            
            image, build_logs = self.docker_client.images.build(
                path=str(self.project_root),
                tag=image_name,
                rm=True
            )
            
            # 停止旧容器
            container_name = target.config.get('container_name', f"yds-lab-{job.name}")
            
            try:
                old_container = self.docker_client.containers.get(container_name)
                old_container.stop()
                old_container.remove()
            except docker.errors.NotFound:
                pass
            
            # 启动新容器
            container_config = target.config.get('container_config', {})
            
            container = self.docker_client.containers.run(
                image_name,
                name=container_name,
                detach=True,
                **container_config
            )
            
            self.logger.info(f"Docker容器已启动: {container.id[:12]}")
            return True
        
        except Exception as e:
            self.logger.error(f"Docker部署失败: {e}")
            return False
    
    def _create_default_dockerfile(self):
        """创建默认Dockerfile"""
        dockerfile_content = """
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
"""
        
        dockerfile_path = self.project_root / "Dockerfile"
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content.strip())
    
    def _deploy_k8s(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """Kubernetes部署"""
        try:
            # 这里需要kubectl命令行工具
            k8s_config = target.config
            namespace = target.k8s_namespace
            
            # 应用Kubernetes配置
            manifest_file = k8s_config.get('manifest_file', 'k8s-deployment.yaml')
            manifest_path = self.project_root / manifest_file
            
            if not manifest_path.exists():
                self.logger.error(f"Kubernetes配置文件不存在: {manifest_file}")
                return False
            
            # 执行kubectl apply
            cmd = f"kubectl apply -f {manifest_path} -n {namespace}"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config['deployment']['timeout']
            )
            
            if result.returncode != 0:
                raise Exception(f"kubectl执行失败: {result.stderr}")
            
            self.logger.info(f"Kubernetes部署完成: {namespace}")
            return True
        
        except Exception as e:
            self.logger.error(f"Kubernetes部署失败: {e}")
            return False
    
    def _deploy_aws(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """AWS部署"""
        if not AWS_AVAILABLE:
            self.logger.error("boto3库未安装，AWS部署不可用")
            return False
        
        try:
            # 这里可以实现AWS S3、EC2、ECS等部署
            aws_config = target.config
            service_type = aws_config.get('service_type', 's3')
            
            if service_type == 's3':
                return self._deploy_aws_s3(job, target)
            elif service_type == 'ec2':
                return self._deploy_aws_ec2(job, target)
            elif service_type == 'ecs':
                return self._deploy_aws_ecs(job, target)
            else:
                raise Exception(f"不支持的AWS服务类型: {service_type}")
        
        except Exception as e:
            self.logger.error(f"AWS部署失败: {e}")
            return False
    
    def _deploy_aws_s3(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """AWS S3部署"""
        try:
            s3_client = boto3.client('s3', region_name=target.aws_region)
            
            bucket_name = target.config['bucket_name']
            source_dir = self.project_root / self.config['build']['output_dir']
            
            # 上传文件到S3
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(source_dir)
                    s3_key = str(relative_path).replace('\\', '/')
                    
                    s3_client.upload_file(
                        str(file_path),
                        bucket_name,
                        s3_key
                    )
            
            self.logger.info(f"文件已上传到S3: {bucket_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"S3部署失败: {e}")
            return False
    
    def _deploy_aws_ec2(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """AWS EC2部署"""
        # 实现EC2部署逻辑
        pass
    
    def _deploy_aws_ecs(self, job: DeploymentJob, target: DeploymentTarget) -> bool:
        """AWS ECS部署"""
        # 实现ECS部署逻辑
        pass
    
    def _create_backup(self, target: DeploymentTarget) -> str:
        """创建备份"""
        backup_id = f"backup_{int(time.time())}_{target.name}"
        backup_dir = self.backups_dir / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if target.type == 'local':
                # 本地备份
                target_dir = Path(target.config.get('target_dir', '/tmp/deployment'))
                if target_dir.exists():
                    shutil.copytree(target_dir, backup_dir / 'files')
            
            elif target.type == 'ssh':
                # SSH备份
                # 这里可以实现远程备份逻辑
                pass
            
            # 压缩备份
            if self.config['backup']['compress']:
                backup_archive = f"{backup_dir}.tar.gz"
                
                with tarfile.open(backup_archive, 'w:gz') as tar:
                    tar.add(backup_dir, arcname=backup_id)
                
                # 删除原目录
                shutil.rmtree(backup_dir)
            
            self.logger.info(f"备份已创建: {backup_id}")
            return backup_id
        
        except Exception as e:
            self.logger.error(f"创建备份失败: {e}")
            return ""
    
    def _health_check(self, target: DeploymentTarget) -> bool:
        """健康检查"""
        health_config = self.config['deployment']['health_check']
        
        if not health_config['enabled']:
            return True
        
        try:
            import requests
            
            # 构建健康检查URL
            base_url = target.config.get('base_url', f"http://{target.host}")
            health_url = f"{base_url}{health_config['url']}"
            
            # 重试检查
            for i in range(health_config['retries']):
                try:
                    response = requests.get(
                        health_url,
                        timeout=health_config['timeout']
                    )
                    
                    if response.status_code == 200:
                        self.logger.info("健康检查通过")
                        return True
                
                except Exception as e:
                    self.logger.warning(f"健康检查失败 (尝试 {i+1}): {e}")
                
                if i < health_config['retries'] - 1:
                    time.sleep(5)
            
            return False
        
        except Exception as e:
            self.logger.error(f"健康检查异常: {e}")
            return False
    
    def _rollback_deployment(self, job_id: str) -> bool:
        """回滚部署"""
        job = self.jobs[job_id]
        
        if not job.rollback_id:
            self.logger.error("没有可用的回滚备份")
            return False
        
        try:
            target = self.targets[job.target]
            
            # 恢复备份
            backup_path = self.backups_dir / f"{job.rollback_id}.tar.gz"
            
            if backup_path.exists():
                # 解压备份
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(self.backups_dir)
                
                # 恢复文件
                backup_dir = self.backups_dir / job.rollback_id / 'files'
                
                if target.type == 'local':
                    target_dir = Path(target.config.get('target_dir', '/tmp/deployment'))
                    
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    
                    shutil.copytree(backup_dir, target_dir)
                
                self.logger.info(f"部署已回滚: {job_id}")
                return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"回滚失败: {e}")
            return False
    
    def _record_deployment_history(self, job: DeploymentJob, target: DeploymentTarget, status: str):
        """记录部署历史"""
        duration = 0
        if job.start_time and job.end_time:
            duration = (job.end_time - job.start_time).total_seconds()
        
        history = DeploymentHistory(
            id=f"history_{int(time.time())}",
            job_id=job.id,
            target=target.name,
            version=job.config.get('version', 'latest'),
            timestamp=datetime.now(),
            status=status,
            duration=duration,
            rollback_available=bool(job.rollback_id),
            backup_path=job.rollback_id
        )
        
        self.history.append(history)
        self._save_history()
        
        # 清理旧历史记录
        if len(self.history) > 100:
            self.history = self.history[-100:]
            self._save_history()
    
    def _send_notification(self, job: DeploymentJob, status: str):
        """发送通知"""
        if not self.config['notifications']['enabled']:
            return
        
        message = f"部署任务 {job.name} ({job.id}) 状态: {status}"
        
        if status == 'failed' and job.error:
            message += f"\n错误: {job.error}"
        
        # Webhook通知
        webhook_url = self.config['notifications']['webhook_url']
        if webhook_url:
            try:
                import requests
                
                payload = {
                    'text': message,
                    'job_id': job.id,
                    'status': status,
                    'target': job.target,
                    'timestamp': datetime.now().isoformat()
                }
                
                requests.post(webhook_url, json=payload, timeout=10)
            except Exception as e:
                self.logger.error(f"Webhook通知发送失败: {e}")
        
        # Slack通知
        slack_config = self.config['notifications']['slack']
        if slack_config['enabled'] and slack_config['webhook_url']:
            try:
                import requests
                
                payload = {
                    'channel': slack_config['channel'],
                    'text': message,
                    'username': 'YDS-Lab Deployment Bot'
                }
                
                requests.post(slack_config['webhook_url'], json=payload, timeout=10)
            except Exception as e:
                self.logger.error(f"Slack通知发送失败: {e}")
    
    def cancel_deployment(self, job_id: str) -> bool:
        """取消部署任务"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        if job.status != 'running':
            return False
        
        job.status = 'cancelled'
        job.end_time = datetime.now()
        
        # 停止线程（注意：这里只是标记，实际停止需要在部署逻辑中检查状态）
        if job_id in self.running_jobs:
            del self.running_jobs[job_id]
        
        self.logger.info(f"部署任务已取消: {job_id}")
        return True
    
    def get_job_status(self, job_id: str) -> Optional[DeploymentJob]:
        """获取任务状态"""
        return self.jobs.get(job_id)
    
    def list_jobs(self, status: str = None) -> List[DeploymentJob]:
        """列出部署任务"""
        jobs = list(self.jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        return sorted(jobs, key=lambda x: x.start_time or datetime.min, reverse=True)
    
    def list_targets(self) -> List[DeploymentTarget]:
        """列出部署目标"""
        return list(self.targets.values())
    
    def add_target(self, target: DeploymentTarget) -> bool:
        """添加部署目标"""
        try:
            self.targets[target.name] = target
            self._save_targets()
            
            self.logger.info(f"部署目标已添加: {target.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"添加部署目标失败: {e}")
            return False
    
    def remove_target(self, name: str) -> bool:
        """移除部署目标"""
        try:
            if name in self.targets:
                del self.targets[name]
                self._save_targets()
                
                self.logger.info(f"部署目标已移除: {name}")
                return True
            else:
                return False
        
        except Exception as e:
            self.logger.error(f"移除部署目标失败: {e}")
            return False
    
    def _save_targets(self):
        """保存部署目标配置"""
        targets_file = self.config_dir / "deployment_targets.yaml"
        
        try:
            targets_config = {}
            for name, target in self.targets.items():
                config_dict = asdict(target)
                del config_dict['name']
                targets_config[name] = config_dict
            
            with open(targets_file, 'w', encoding='utf-8') as f:
                yaml.dump(targets_config, f, default_flow_style=False, allow_unicode=True)
        
        except Exception as e:
            self.logger.error(f"保存部署目标配置失败: {e}")
    
    def get_deployment_history(self, target: str = None, limit: int = 50) -> List[DeploymentHistory]:
        """获取部署历史"""
        history = self.history
        
        if target:
            history = [h for h in history if h.target == target]
        
        return sorted(history, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def cleanup_old_backups(self):
        """清理旧备份"""
        try:
            keep_backups = self.config['backup']['keep_backups']
            
            # 获取所有备份文件
            backup_files = []
            for file_path in self.backups_dir.glob('backup_*.tar.gz'):
                backup_files.append((file_path.stat().st_mtime, file_path))
            
            # 按时间排序
            backup_files.sort(reverse=True)
            
            # 删除多余的备份
            for _, file_path in backup_files[keep_backups:]:
                file_path.unlink()
                self.logger.info(f"已删除旧备份: {file_path.name}")
        
        except Exception as e:
            self.logger.error(f"清理备份失败: {e}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YDS-Lab 部署管理工具')
    parser.add_argument('--project-root', help='指定项目根目录路径')
    parser.add_argument('--list-targets', action='store_true', help='列出部署目标')
    parser.add_argument('--list-jobs', help='列出部署任务 (可选状态过滤)')
    parser.add_argument('--deploy', nargs=2, metavar=('NAME', 'TARGET'), help='创建并启动部署任务')
    parser.add_argument('--status', help='查看任务状态')
    parser.add_argument('--cancel', help='取消部署任务')
    parser.add_argument('--rollback', help='回滚部署')
    parser.add_argument('--history', help='查看部署历史 (可选目标过滤)')
    parser.add_argument('--cleanup', action='store_true', help='清理旧备份')
    
    args = parser.parse_args()
    
    manager = DeploymentManager(args.project_root)
    
    # 列出部署目标
    if args.list_targets:
        targets = manager.list_targets()
        
        print("🎯 部署目标列表")
        print("="*50)
        
        for target in targets:
            print(f"名称: {target.name}")
            print(f"类型: {target.type}")
            print(f"主机: {target.host}")
            print(f"环境: {target.environment}")
            print("-" * 30)
        
        return
    
    # 列出部署任务
    if args.list_jobs is not None:
        status_filter = args.list_jobs if args.list_jobs else None
        jobs = manager.list_jobs(status_filter)
        
        print("📋 部署任务列表")
        print("="*50)
        
        for job in jobs:
            print(f"ID: {job.id}")
            print(f"名称: {job.name}")
            print(f"目标: {job.target}")
            print(f"状态: {job.status}")
            
            if job.start_time:
                print(f"开始时间: {job.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if job.end_time:
                duration = (job.end_time - job.start_time).total_seconds()
                print(f"持续时间: {duration:.1f}s")
            
            if job.error:
                print(f"错误: {job.error}")
            
            print("-" * 30)
        
        return
    
    # 创建并启动部署
    if args.deploy:
        name, target = args.deploy
        
        print(f"🚀 创建部署任务: {name} -> {target}")
        
        job_id = manager.create_deployment_job(name, target)
        
        if manager.start_deployment(job_id):
            print(f"✅ 部署任务已启动: {job_id}")
        else:
            print(f"❌ 部署任务启动失败")
        
        return
    
    # 查看任务状态
    if args.status:
        job = manager.get_job_status(args.status)
        
        if job:
            print(f"📊 任务状态: {args.status}")
            print("="*40)
            print(f"名称: {job.name}")
            print(f"目标: {job.target}")
            print(f"状态: {job.status}")
            
            if job.start_time:
                print(f"开始时间: {job.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if job.end_time:
                print(f"结束时间: {job.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                duration = (job.end_time - job.start_time).total_seconds()
                print(f"持续时间: {duration:.1f}s")
            
            if job.error:
                print(f"错误: {job.error}")
            
            if job.log_file and Path(job.log_file).exists():
                print(f"日志文件: {job.log_file}")
        else:
            print(f"❌ 任务不存在: {args.status}")
        
        return
    
    # 取消部署
    if args.cancel:
        if manager.cancel_deployment(args.cancel):
            print(f"✅ 部署任务已取消: {args.cancel}")
        else:
            print(f"❌ 取消部署失败: {args.cancel}")
        
        return
    
    # 回滚部署
    if args.rollback:
        if manager._rollback_deployment(args.rollback):
            print(f"✅ 部署已回滚: {args.rollback}")
        else:
            print(f"❌ 回滚失败: {args.rollback}")
        
        return
    
    # 查看部署历史
    if args.history is not None:
        target_filter = args.history if args.history else None
        history = manager.get_deployment_history(target_filter)
        
        print("📚 部署历史")
        print("="*50)
        
        for record in history:
            print(f"ID: {record.id}")
            print(f"任务: {record.job_id}")
            print(f"目标: {record.target}")
            print(f"版本: {record.version}")
            print(f"时间: {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"状态: {record.status}")
            print(f"持续时间: {record.duration:.1f}s")
            print(f"可回滚: {'是' if record.rollback_available else '否'}")
            print("-" * 30)
        
        return
    
    # 清理备份
    if args.cleanup:
        print("🧹 清理旧备份")
        manager.cleanup_old_backups()
        print("✅ 清理完成")
        return
    
    # 默认显示状态
    print("🚀 部署管理器状态")
    print("="*40)
    print(f"项目路径: {manager.project_root}")
    print(f"部署目标: {len(manager.targets)}")
    print(f"活跃任务: {len([j for j in manager.jobs.values() if j.status == 'running'])}")
    print(f"历史记录: {len(manager.history)}")

if __name__ == "__main__":
    main()