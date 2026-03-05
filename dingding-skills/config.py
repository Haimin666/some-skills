"""
配置管理模块

管理钉钉 API 配置、大模型配置、知识库配置等
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
from pathlib import Path


@dataclass
class DingTalkConfig:
    """钉钉配置"""
    app_key: str = ""
    app_secret: str = ""
    agent_id: str = ""
    api_base_url: str = "https://oapi.dingtalk.com"
    
    # 消息获取配置
    max_messages: int = 1000  # 单次最大获取消息数
    message_types: List[str] = field(default_factory=lambda: ["text", "richText"])  # 支持的消息类型


@dataclass  
class LLMConfig:
    """大模型配置"""
    api_base_url: str = "https://api.example.com/v1"
    api_key: str = ""
    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # QA 生成配置
    qa_generation_prompt: str = """
你是一个专业的客服问答助手。请从以下群聊消息中提取有价值的问答对。

要求：
1. 问题要清晰、完整
2. 答案要准确、有用
3. 忽略无关的闲聊内容
4. 对于模糊的问题，根据上下文进行合理补充

群聊消息：
{messages}

请以 JSON 格式输出问答对列表：
[
  {{"question": "问题内容", "answer": "答案内容", "context": "上下文说明"}}
]
"""

    # 分类配置
    classification_prompt: str = """
请对以下问答对进行分类。分类类型包括：
- system_bug: 系统Bug（页面崩溃、功能异常、报错等）
- data_issue: 数据问题（数据错误、数据缺失、数据不一致等）
- business_issue: 业务问题（业务流程、规则咨询、业务异常等）
- user_issue: 用户问题（使用问题、操作指导、功能咨询等）
- feature_request: 功能需求（新功能建议、改进意见等）
- other: 其他问题

问答对：
{qa_list}

请以 JSON 格式输出分类结果：
[
  {{"id": "qa_id", "category": "分类", "confidence": 0.95, "reason": "分类理由"}}
]
"""


@dataclass
class KnowledgeBaseConfig:
    """知识库配置"""
    output_dir: str = "output/knowledge_base"
    format: str = "json"  # json, csv, markdown
    batch_size: int = 100  # 批量导入大小
    
    # 分类配置
    categories: Dict[str, str] = field(default_factory=lambda: {
        "system_bug": "系统Bug",
        "data_issue": "数据问题",
        "business_issue": "业务问题",
        "user_issue": "用户问题",
        "feature_request": "功能需求",
        "other": "其他问题"
    })


@dataclass
class AnalysisConfig:
    """分析配置"""
    # 问题严重级别
    severity_levels: Dict[str, str] = field(default_factory=lambda: {
        "critical": "严重-需立即处理",
        "high": "高-需尽快处理",
        "medium": "中-正常处理",
        "low": "低-可延后处理"
    })
    
    # 趋势分析配置
    trend_window_days: int = 7  # 趋势分析时间窗口
    
    # 报告配置
    report_format: str = "json"  # json, html, markdown


@dataclass
class AppConfig:
    """应用总配置"""
    dingtalk: DingTalkConfig = field(default_factory=DingTalkConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    # 日志配置
    log_level: str = "INFO"
    log_dir: str = "logs"


def load_config() -> AppConfig:
    """从环境变量加载配置"""
    config = AppConfig()
    
    # 钉钉配置
    config.dingtalk.app_key = os.getenv("DINGTALK_APP_KEY", "")
    config.dingtalk.app_secret = os.getenv("DINGTALK_APP_SECRET", "")
    config.dingtalk.agent_id = os.getenv("DINGTALK_AGENT_ID", "")
    
    # 大模型配置
    config.llm.api_base_url = os.getenv("LLM_API_BASE_URL", "https://api.example.com/v1")
    config.llm.api_key = os.getenv("LLM_API_KEY", "")
    config.llm.model = os.getenv("LLM_MODEL", "gpt-4")
    
    # 知识库配置
    config.knowledge_base.output_dir = os.getenv("KB_OUTPUT_DIR", "output/knowledge_base")
    
    return config


# 全局配置实例
config = load_config()


def get_output_path(filename: str) -> Path:
    """获取输出文件路径"""
    output_dir = Path(config.knowledge_base.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / filename
