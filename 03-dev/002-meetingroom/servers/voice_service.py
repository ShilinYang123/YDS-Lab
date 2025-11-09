"""
YDS AI 语音服务系统
集成Shimmy/Ollama STT/TTS服务，提供语音转文字和文字转语音功能
"""

import os
import json
import asyncio
import aiohttp
import subprocess
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import tempfile
import wave
import io

logger = logging.getLogger(__name__)

class VoiceServiceType(Enum):
    """语音服务类型"""
    STT = "stt"  # Speech to Text
    TTS = "tts"  # Text to Speech

class VoiceModel(Enum):
    """语音模型"""
    WHISPER_TINY = "whisper-tiny"
    WHISPER_BASE = "whisper-base"
    WHISPER_SMALL = "whisper-small"
    WHISPER_MEDIUM = "whisper-medium"
    WHISPER_LARGE = "whisper-large"
    COQUI_TTS = "coqui-tts"
    ESPEAK_TTS = "espeak-tts"

class AudioFormat(Enum):
    """音频格式"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"

@dataclass
class VoiceServiceConfig:
    """语音服务配置"""
    service_type: VoiceServiceType
    model: VoiceModel
    endpoint: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_audio_length: int = 300  # 秒
    supported_formats: List[AudioFormat] = None
    language: str = "zh"
    enabled: bool = True

@dataclass
class STTRequest:
    """语音转文字请求"""
    audio_data: bytes
    format: AudioFormat
    language: str = "zh"
    model: VoiceModel = VoiceModel.WHISPER_BASE
    timestamp: datetime = None

@dataclass
class STTResponse:
    """语音转文字响应"""
    text: str
    confidence: float
    language: str
    duration: float
    segments: List[Dict[str, Any]] = None
    processing_time: float = None

@dataclass
class TTSRequest:
    """文字转语音请求"""
    text: str
    language: str = "zh"
    voice: str = "default"
    speed: float = 1.0
    pitch: float = 1.0
    format: AudioFormat = AudioFormat.WAV
    model: VoiceModel = VoiceModel.COQUI_TTS

@dataclass
class TTSResponse:
    """文字转语音响应"""
    audio_data: bytes
    format: AudioFormat
    duration: float
    sample_rate: int
    processing_time: float = None

class VoiceServiceManager:
    """语音服务管理器"""
    
    def __init__(self, config_path: str = None):
        # 统一配置路径优先使用 config/voice_service_config.json，保留根路径回退
        if config_path:
            resolved_config_path = config_path
        else:
            candidate_paths = [
                os.path.join("config", "voice_service_config.json"),
                "voice_service_config.json",
            ]
            resolved_config_path = None
            for p in candidate_paths:
                if os.path.exists(p):
                    resolved_config_path = p
                    break
            if resolved_config_path is None:
                resolved_config_path = os.path.join("config", "voice_service_config.json")
        self.config_path = resolved_config_path
        logger.info(f"[VoiceServiceManager] 使用配置路径: {self.config_path}")
        self.services: Dict[str, VoiceServiceConfig] = {}
        self.shimmy_process = None
        self.ollama_process = None
        self._load_config()
        self._setup_default_services()
    
    def _load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    for service_data in config.get('services', []):
                        service = VoiceServiceConfig(
                            service_type=VoiceServiceType(service_data['service_type']),
                            model=VoiceModel(service_data['model']),
                            endpoint=service_data['endpoint'],
                            api_key=service_data.get('api_key'),
                            timeout=service_data.get('timeout', 30),
                            max_audio_length=service_data.get('max_audio_length', 300),
                            supported_formats=[AudioFormat(f) for f in service_data.get('supported_formats', ['wav'])],
                            language=service_data.get('language', 'zh'),
                            enabled=service_data.get('enabled', True)
                        )
                        service_key = f"{service.service_type.value}_{service.model.value}"
                        self.services[service_key] = service
        except Exception as e:
            logger.error(f"加载语音服务配置失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        try:
            config = {'services': []}
            
            for service in self.services.values():
                service_data = {
                    'service_type': service.service_type.value,
                    'model': service.model.value,
                    'endpoint': service.endpoint,
                    'api_key': service.api_key,
                    'timeout': service.timeout,
                    'max_audio_length': service.max_audio_length,
                    'supported_formats': [f.value for f in service.supported_formats] if service.supported_formats else ['wav'],
                    'language': service.language,
                    'enabled': service.enabled
                }
                config['services'].append(service_data)
            
            # 确保保存目录存在
            save_dir = os.path.dirname(self.config_path) or "."
            os.makedirs(save_dir, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存语音服务配置失败: {e}")
    
    def get_stt_config(self, model: VoiceModel = None) -> Optional[VoiceServiceConfig]:
        """获取STT服务配置"""
        return self._get_best_service(VoiceServiceType.STT, model)
    
    def get_tts_config(self, model: VoiceModel = None) -> Optional[VoiceServiceConfig]:
        """获取TTS服务配置"""
        return self._get_best_service(VoiceServiceType.TTS, model)
    
    def _setup_default_services(self):
        """设置默认服务"""
        if not self.services:
            default_services = [
                VoiceServiceConfig(
                    service_type=VoiceServiceType.STT,
                    model=VoiceModel.WHISPER_BASE,
                    endpoint="http://localhost:11434/api/generate",
                    timeout=60,
                    max_audio_length=600,
                    supported_formats=[AudioFormat.WAV, AudioFormat.MP3, AudioFormat.OGG],
                    language="zh",
                    enabled=True
                ),
                VoiceServiceConfig(
                    service_type=VoiceServiceType.STT,
                    model=VoiceModel.WHISPER_SMALL,
                    endpoint="http://localhost:11434/api/generate",
                    timeout=90,
                    max_audio_length=600,
                    supported_formats=[AudioFormat.WAV, AudioFormat.MP3, AudioFormat.OGG],
                    language="zh",
                    enabled=True
                ),
                VoiceServiceConfig(
                    service_type=VoiceServiceType.TTS,
                    model=VoiceModel.COQUI_TTS,
                    endpoint="http://localhost:5002/api/tts",
                    timeout=30,
                    supported_formats=[AudioFormat.WAV, AudioFormat.MP3],
                    language="zh",
                    enabled=True
                ),
                VoiceServiceConfig(
                    service_type=VoiceServiceType.TTS,
                    model=VoiceModel.ESPEAK_TTS,
                    endpoint="http://localhost:5003/api/tts",
                    timeout=15,
                    supported_formats=[AudioFormat.WAV],
                    language="zh",
                    enabled=True
                )
            ]
            
            for service in default_services:
                service_key = f"{service.service_type.value}_{service.model.value}"
                self.services[service_key] = service
            
            self._save_config()
    
    async def start_shimmy_service(self) -> bool:
        """启动Shimmy服务"""
        try:
            # 检查Shimmy是否已经运行
            if await self._check_service_health("http://localhost:11434/api/tags"):
                logger.info("Shimmy服务已在运行")
                return True
            
            # 启动Shimmy
            shimmy_cmd = ["ollama", "serve"]
            self.shimmy_process = subprocess.Popen(
                shimmy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.expanduser("~")
            )
            
            # 等待服务启动
            for _ in range(30):  # 等待30秒
                await asyncio.sleep(1)
                if await self._check_service_health("http://localhost:11434/api/tags"):
                    logger.info("Shimmy服务启动成功")
                    return True
            
            logger.error("Shimmy服务启动超时")
            return False
            
        except Exception as e:
            logger.error(f"启动Shimmy服务失败: {e}")
            return False
    
    async def stop_shimmy_service(self):
        """停止Shimmy服务"""
        if self.shimmy_process:
            self.shimmy_process.terminate()
            self.shimmy_process.wait()
            self.shimmy_process = None
            logger.info("Shimmy服务已停止")
    
    async def _check_service_health(self, endpoint: str) -> bool:
        """检查服务健康状态"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status == 200
        except:
            return False
    
    async def speech_to_text(self, request: STTRequest) -> STTResponse:
        """语音转文字"""
        start_time = time.time()
        
        # 选择最佳STT服务
        service = self._get_best_service(VoiceServiceType.STT, request.model)
        if not service:
            raise ValueError("未找到可用的STT服务")
        
        try:
            # 验证音频格式和长度
            if not self._validate_audio(request.audio_data, request.format, service.max_audio_length):
                raise ValueError("音频格式或长度不符合要求")
            
            # 调用STT服务
            if "ollama" in service.endpoint or "shimmy" in service.endpoint:
                response = await self._call_ollama_stt(service, request)
            else:
                response = await self._call_generic_stt(service, request)
            
            response.processing_time = time.time() - start_time
            return response
            
        except Exception as e:
            logger.error(f"语音转文字失败: {e}")
            raise
    
    async def text_to_speech(self, request: TTSRequest) -> TTSResponse:
        """文字转语音"""
        start_time = time.time()
        
        # 选择最佳TTS服务
        service = self._get_best_service(VoiceServiceType.TTS, request.model)
        if not service:
            raise ValueError("未找到可用的TTS服务")
        
        try:
            # 调用TTS服务
            if "coqui" in service.endpoint:
                response = await self._call_coqui_tts(service, request)
            elif "espeak" in service.endpoint:
                response = await self._call_espeak_tts(service, request)
            else:
                response = await self._call_generic_tts(service, request)
            
            response.processing_time = time.time() - start_time
            return response
            
        except Exception as e:
            logger.error(f"文字转语音失败: {e}")
            raise
    
    def _get_best_service(self, service_type: VoiceServiceType, preferred_model: VoiceModel = None) -> Optional[VoiceServiceConfig]:
        """获取最佳服务"""
        available_services = [
            service for service in self.services.values()
            if service.service_type == service_type and service.enabled
        ]
        
        if not available_services:
            return None
        
        # 优先选择指定模型
        if preferred_model:
            for service in available_services:
                if service.model == preferred_model:
                    return service
        
        # 返回第一个可用服务
        return available_services[0]
    
    def _validate_audio(self, audio_data: bytes, format: AudioFormat, max_length: int) -> bool:
        """验证音频数据"""
        try:
            # 检查数据大小
            if len(audio_data) == 0:
                return False
            
            # 对于WAV格式，检查时长
            if format == AudioFormat.WAV:
                with io.BytesIO(audio_data) as audio_io:
                    with wave.open(audio_io, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        duration = frames / sample_rate
                        return duration <= max_length
            
            # 其他格式暂时只检查大小（简化处理）
            max_size = max_length * 16000 * 2  # 假设16kHz, 16bit
            return len(audio_data) <= max_size
            
        except Exception as e:
            logger.error(f"音频验证失败: {e}")
            return False
    
    async def _call_ollama_stt(self, service: VoiceServiceConfig, request: STTRequest) -> STTResponse:
        """调用Ollama STT服务"""
        try:
            # 保存音频到临时文件
            with tempfile.NamedTemporaryFile(suffix=f".{request.format.value}", delete=False) as temp_file:
                temp_file.write(request.audio_data)
                temp_path = temp_file.name
            
            try:
                # 使用whisper模型进行转录
                cmd = [
                    "ollama", "run", request.model.value.replace("-", ":"),
                    "--", "transcribe", temp_path
                ]
                
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=service.timeout
                )
                
                if process.returncode == 0:
                    text = process.stdout.strip()
                    return STTResponse(
                        text=text,
                        confidence=0.9,  # Ollama不提供置信度，使用默认值
                        language=request.language,
                        duration=0.0  # 需要从音频文件计算
                    )
                else:
                    raise Exception(f"Ollama STT失败: {process.stderr}")
                    
            finally:
                # 清理临时文件
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"调用Ollama STT失败: {e}")
            raise
    
    async def _call_generic_stt(self, service: VoiceServiceConfig, request: STTRequest) -> STTResponse:
        """调用通用STT服务"""
        try:
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('audio', request.audio_data, 
                              filename=f'audio.{request.format.value}',
                              content_type=f'audio/{request.format.value}')
                data.add_field('language', request.language)
                data.add_field('model', request.model.value)
                
                headers = {}
                if service.api_key:
                    headers['Authorization'] = f'Bearer {service.api_key}'
                
                async with session.post(
                    service.endpoint,
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=service.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return STTResponse(
                            text=result.get('text', ''),
                            confidence=result.get('confidence', 0.0),
                            language=result.get('language', request.language),
                            duration=result.get('duration', 0.0),
                            segments=result.get('segments', [])
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"STT服务错误 {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"调用通用STT服务失败: {e}")
            raise
    
    async def _call_coqui_tts(self, service: VoiceServiceConfig, request: TTSRequest) -> TTSResponse:
        """调用Coqui TTS服务"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'text': request.text,
                    'language': request.language,
                    'voice': request.voice,
                    'speed': request.speed,
                    'pitch': request.pitch,
                    'format': request.format.value
                }
                
                headers = {'Content-Type': 'application/json'}
                if service.api_key:
                    headers['Authorization'] = f'Bearer {service.api_key}'
                
                async with session.post(
                    service.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=service.timeout)
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        return TTSResponse(
                            audio_data=audio_data,
                            format=request.format,
                            duration=0.0,  # 需要从音频数据计算
                            sample_rate=22050  # Coqui默认采样率
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"Coqui TTS服务错误 {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"调用Coqui TTS服务失败: {e}")
            raise
    
    async def _call_espeak_tts(self, service: VoiceServiceConfig, request: TTSRequest) -> TTSResponse:
        """调用eSpeak TTS服务"""
        try:
            # 使用本地eSpeak命令
            cmd = [
                "espeak",
                "-s", str(int(request.speed * 175)),  # 语速
                "-p", str(int(request.pitch * 50)),   # 音调
                "-v", f"{request.language}",          # 语言
                "--stdout",                           # 输出到stdout
                request.text
            ]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                timeout=service.timeout
            )
            
            if process.returncode == 0:
                return TTSResponse(
                    audio_data=process.stdout,
                    format=AudioFormat.WAV,
                    duration=0.0,  # 需要计算
                    sample_rate=22050
                )
            else:
                raise Exception(f"eSpeak TTS失败: {process.stderr.decode()}")
                
        except Exception as e:
            logger.error(f"调用eSpeak TTS服务失败: {e}")
            raise
    
    async def _call_generic_tts(self, service: VoiceServiceConfig, request: TTSRequest) -> TTSResponse:
        """调用通用TTS服务"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'text': request.text,
                    'language': request.language,
                    'voice': request.voice,
                    'speed': request.speed,
                    'pitch': request.pitch,
                    'format': request.format.value
                }
                
                headers = {'Content-Type': 'application/json'}
                if service.api_key:
                    headers['Authorization'] = f'Bearer {service.api_key}'
                
                async with session.post(
                    service.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=service.timeout)
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        return TTSResponse(
                            audio_data=audio_data,
                            format=request.format,
                            duration=0.0,
                            sample_rate=22050
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"TTS服务错误 {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"调用通用TTS服务失败: {e}")
            raise
    
    def get_available_services(self) -> Dict[str, List[str]]:
        """获取可用服务列表"""
        services = {"stt": [], "tts": []}
        
        for service in self.services.values():
            if service.enabled:
                service_info = f"{service.model.value} ({service.endpoint})"
                services[service.service_type.value].append(service_info)
        
        return services
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "shimmy_running": self.shimmy_process is not None and self.shimmy_process.poll() is None,
            "total_services": len(self.services),
            "enabled_services": len([s for s in self.services.values() if s.enabled]),
            "stt_services": len([s for s in self.services.values() if s.service_type == VoiceServiceType.STT and s.enabled]),
            "tts_services": len([s for s in self.services.values() if s.service_type == VoiceServiceType.TTS and s.enabled])
        }

# 全局实例
voice_service = VoiceServiceManager()