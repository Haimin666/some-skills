"""
配置管理模块

管理钉钉、大模型、FastGPT 等配置
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DingTalkConfig:
    """钉钉配置"""
    app_key: str = ""
    app_secret: str = ""
    access_token: str = ""
    api_base_url: str = "https://oapi.dingtalk.com"


@dataclass
class LLMConfig:
    """大模型配置"""
    api_base_url: str = "https://api.example.com/v1"
    api_key: str = ""
    model: str = "gpt-4"


@dataclass
class FastGptConfig:
    """FastGPT 配置"""
    api_url: str = "https://api.fastgpt.in"
    api_key: str = ""
    dataset_id: str = ""
    # 知识库配置
    collection_id: Optional[str] = None  # 知识库集合 ID（可选）


@dataclass
class SyncConfig:
    """同步配置"""
    sync_hour: int = 0      # 同步时间（小时）
    sync_minute: int = 0  # 同步时间（分钟）
    batch_size: int = 100    # 批处理大小
    max_messages: int = 1000  # 最大消息数


    output_dir: str = "output/knowledge_base"


@dataclass
class AppConfig:
    """应用总配置"""
    dingtalk: DingTalkConfig = field(default_factory=DingTalkConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    fastgpt: FastGptConfig = field(default_factory=FastGptConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    
    # 运行模式
    mode: str = "production"  # production, development, test
    log_level: str = "INFO"


def load_config() -> AppConfig:
    """从环境变量加载配置"""
    config = AppConfig()
    
    # 钉钉配置
    config.dingtalk.app_key = os.getenv("DINGTALK_APP_KEY", "")
    config.dingtalk.app_secret = os.getenv("DINGTALK_APP_SECRET", "")
    config.dingtalk.access_token = os.getenv("DINGTALK_ACCESS_TOKEN", "")
    
    # 大模型配置
    config.llm.api_base_url = os.getenv(
        "LLM_API_BASE_URL", 
        "https://api.example.com/v1"
    )
    config.llm.api_key = os.getenv("LLM_API_KEY", "")
    config.llm.model = os.getenv("LLM_MODEL", "gpt-4")
    
    # FastGPT 配置
    config.fastgpt.api_url = os.getenv(
        "FASTGPT_API_URL", 
        "https://api.fastgpt.in"
    )
    config.fastgpt.api_key = os.getenv("FASTGPT_API_KEY", "")
    config.fastgpt.dataset_id = os.getenv("FASTGPT_DATASET_ID", "")
    config.fastgpt.collection_id = os.getenv("FASTGPT_COLLECTION_ID")
    
    # 同步配置
    config.sync.sync_hour = int(os.getenv("SYNC_HOUR", "0"))
    config.sync.sync_minute = int(os.getenv("SYNC_MINUTE", "0"))
    config.sync.batch_size = int(os.getenv("SYNC_BATCH_SIZE", "100"))
    config.sync.max_messages = int(os.getenv("SYNC_MAX_MESSAGES", "1000"))
    config.sync.output_dir = os.getenv("SYNC_OUTPUT_DIR", "output/knowledge_base")
    
    # 运行配置
    config.mode = os.getenv("APP_MODE", "production")
    config.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    return config


# 全局配置实例
config = load_config()
