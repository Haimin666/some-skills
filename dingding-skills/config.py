"""
配置管理模块
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DingTalkConfig:
    """钉钉配置"""
    app_key: str = ""
    app_secret: str = ""
    api_base_url: str = "https://oapi.dingtalk.com"


@dataclass
class LLMConfig:
    """大模型配置"""
    api_base_url: str = "https://api.example.com/v1"
    api_key: str = ""
    model: str = "gpt-4"


@dataclass
class AppConfig:
    """应用配置"""
    dingtalk: DingTalkConfig = field(default_factory=DingTalkConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)


def load_config() -> AppConfig:
    """加载配置"""
    config = AppConfig()

    # 钉钉配置
    config.dingtalk.app_key = os.getenv("DINGTALK_APP_KEY", "")
    config.dingtalk.app_secret = os.getenv("DINGTALK_APP_SECRET", "")

    # 大模型配置
    config.llm.api_base_url = os.getenv("LLM_API_BASE_URL", "https://api.example.com/v1")
    config.llm.api_key = os.getenv("LLM_API_KEY", "")
    config.llm.model = os.getenv("LLM_MODEL", "gpt-4")

    return config


config = load_config()
