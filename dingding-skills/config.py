"""
配置管理模块（金融场景版）
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


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
    """FastGpt 配置"""
    api_url: str = "https://api.fastgpt.in"
    api_key: str = ""
    dataset_id: str = ""


@dataclass
class AppConfig:
    """应用配置"""
    dingtalk: DingTalkConfig = field(default_factory=DingTalkConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    fastgpt: FastGptConfig = field(default_factory=FastGptConfig)


def load_config() -> AppConfig:
    """加载配置"""
    config = AppConfig()

    # 钉钉配置
    config.dingtalk.app_key = os.getenv("DINGTALK_APP_KEY", "")
    config.dingtalk.app_secret = os.getenv("DINGTALK_APP_SECRET", "")
    config.dingtalk.access_token = os.getenv("DINGTALK_ACCESS_TOKEN", "")

    # 大模型配置
    config.llm.api_base_url = os.getenv("LLM_API_BASE_URL", "https://api.example.com/v1")
    config.llm.api_key = os.getenv("LLM_API_KEY", "")
    config.llm.model = os.getenv("LLM_MODEL", "gpt-4")

    # FastGpt 配置
    config.fastgpt.api_url = os.getenv("FASTGPT_API_URL", "https://api.fastgpt.in")
    config.fastgpt.api_key = os.getenv("FASTGPT_API_KEY", "")
    config.fastgpt.dataset_id = os.getenv("FASTGPT_DATASET_ID", "")

    return config


config = load_config()
