"""
配置文件 - AI 服务配置

使用说明：
1. 可以直接修改此文件中的配置
2. 或者创建 .env 文件设置环境变量
3. 环境变量优先级高于此文件配置
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIConfig:
    """AI 服务配置类"""

    # API 基础配置
    api_base_url: str = "https://api.example.com/v1"
    api_key: str = "your_api_key_here"

    # LLM 配置
    llm_model: str = "gpt-4"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7

    # TTS 配置
    tts_voice: str = "tongtong"  # 可选: tongtong, chuichui, xiaochen, jam, kazi, douji, luodo
    tts_speed: float = 1.0  # 范围: 0.5 - 2.0
    tts_format: str = "wav"  # 可选: wav, mp3, pcm
    tts_max_chars: int = 1024  # 单次请求最大字符数

    # VLM 配置
    vlm_model: str = "gpt-4-vision"

    # ASR 配置
    asr_model: str = "whisper-1"
    asr_language: str = "zh"  # 语言代码

    # 图像生成配置
    image_model: str = "dall-e-3"
    image_size: str = "1024x1024"  # 可选: 256x256, 512x512, 1024x1024
    image_quality: str = "standard"  # 可选: standard, hd

    # 请求配置
    request_timeout: int = 60  # 请求超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）


def get_config() -> AIConfig:
    """获取配置实例，支持从环境变量读取"""
    return AIConfig(
        api_base_url=os.getenv("AI_API_BASE_URL", "https://api.example.com/v1"),
        api_key=os.getenv("AI_API_KEY", "your_api_key_here"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4"),
        tts_voice=os.getenv("TTS_VOICE", "tongtong"),
        vlm_model=os.getenv("VLM_MODEL", "gpt-4-vision"),
        asr_model=os.getenv("ASR_MODEL", "whisper-1"),
        image_model=os.getenv("IMAGE_MODEL", "dall-e-3"),
    )


# 全局配置实例
config = get_config()
