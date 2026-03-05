"""
QA Extractor - 从群聊消息中提取 QA 的核心脚本

使用大模型理解上下文，从零散的聊天记录中提取结构化的问答对
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import aiohttp


@dataclass
class ChatMessage:
    """聊天消息"""
    msg_id: str
    sender_id: str
    sender_name: str
    content: str
    timestamp: datetime
    chat_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "chat_id": self.chat_id,
        }

    def format_for_llm(self) -> str:
        """格式化为 LLM 输入格式"""
        time_str = self.timestamp.strftime("%H:%M")
        return f"[{time_str}] {self.sender_name}: {self.content}"


@dataclass
class QAPair:
    """问答对"""
    id: str
    question: str
    answer: str
    category: str
    category_name: str
    confidence: float
    context: str
    source_msg_ids: List[str]
    keywords: List[str]
    severity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "category_name": self.category_name,
            "confidence": self.confidence,
            "context": self.context,
            "source_msg_ids": self.source_msg_ids,
            "keywords": self.keywords,
            "severity": self.severity,
        }


class QAExtractor:
    """
    QA 提取器

    使用大模型从群聊消息中提取结构化 QA
    """

    # 分类标签定义
    CATEGORIES = {
        "system_bug": "系统Bug",
        "data_issue": "数据问题",
        "business_issue": "业务问题",
        "user_issue": "用户问题",
        "feature_request": "功能需求",
        "other": "其他",
    }

    # 严重级别定义
    SEVERITY_LEVELS = ["critical", "high", "medium", "low"]

    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model: str = "gpt-4",
    ):
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.model = model
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _init_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=120),
            )

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def extract_qa(
        self,
        messages: List[ChatMessage],
        batch_size: int = 30,
    ) -> Dict[str, Any]:
        """
        从消息列表提取 QA

        Args:
            messages: 聊天消息列表
            batch_size: 批处理大小

        Returns:
            包含 qa_list 和 statistics 的字典
        """
        await self._init_session()

        all_qa_list = []

        # 分批处理，保留上下文衔接
        for i in range(0, len(messages), batch_size):
            # 获取当前批次，包含上一批最后 5 条作为上下文
            start = max(0, i - 5) if i > 0 else i
            batch_messages = messages[start:i + batch_size]

            qa_list = await self._process_batch(batch_messages, i // batch_size)
            all_qa_list.extend(qa_list)

        # 去重（基于问题内容的相似度）
        all_qa_list = self._deduplicate_qa(all_qa_list)

        # 生成统计信息
        statistics = self._generate_statistics(all_qa_list)

        return {
            "qa_list": [qa.to_dict() for qa in all_qa_list],
            "statistics": statistics,
        }

    async def _process_batch(
        self,
        messages: List[ChatMessage],
        batch_index: int,
    ) -> List[QAPair]:
        """处理一批消息"""
        # 格式化消息
        formatted_messages = "\n".join([m.format_for_llm() for m in messages])

        # 构建 prompt
        prompt = self._build_extraction_prompt(formatted_messages)

        # 调用大模型
        try:
            response = await self._call_llm(prompt)
            qa_list = self._parse_response(response, messages, batch_index)
            return qa_list
        except Exception as e:
            print(f"处理批次 {batch_index} 失败: {e}")
            return []

    def _build_extraction_prompt(self, messages: str) -> str:
        """构建提取 prompt"""
        return f"""你是一个专业的客服问答助手。请从以下群聊消息中提取有价值的问答对(QA)。

## 任务说明
群聊记录是零散的，需要你理解上下文来判断哪些是真正的问答。

## 提取规则
1. **识别问题**：包含疑问词（怎么、如何、为什么等）、问号、或表达困惑的内容
2. **识别答案**：回答问题、提供解决方案、解释说明的内容
3. **理解上下文**：答案可能分散在多条消息中，需要合并理解
4. **质量要求**：忽略纯闲聊、表情包；问题要清晰完整，答案要准确有用

## 分类标签
- system_bug: 系统Bug（报错、崩溃、功能异常）
- data_issue: 数据问题（数据错误、缺失、不一致）
- business_issue: 业务问题（流程、规则、权限）
- user_issue: 用户问题（使用咨询、操作指导）
- feature_request: 功能需求（建议、改进意见）
- other: 其他问题

## 严重级别
- critical: 严重问题，系统崩溃、核心功能不可用
- high: 高优先级，功能异常、影响业务
- medium: 中等优先级，一般问题
- low: 低优先级，咨询类问题

## 群聊消息
{messages}

## 输出格式
请以 JSON 格式输出：
```json
{{
  "qa_list": [
    {{
      "question": "整理后的问题",
      "answer": "整理后的答案",
      "category": "分类标签",
      "confidence": 0.95,
      "context": "上下文说明",
      "keywords": ["关键词"],
      "severity": "严重级别"
    }}
  ]
}}
```

如果消息中没有有价值的问答，输出空列表：{{"qa_list": []}}"""

    async def _call_llm(self, prompt: str) -> str:
        """调用大模型"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的客服问答助手，擅长从群聊对话中提取有价值的问答信息。"
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 4096,
            "temperature": 0.3,
        }

        async with self._session.post(
            f"{self.api_base_url}/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["choices"][0]["message"]["content"]

    def _parse_response(
        self,
        response: str,
        messages: List[ChatMessage],
        batch_index: int,
    ) -> List[QAPair]:
        """解析 LLM 响应"""
        qa_list = []

        try:
            # 提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                raw_qa_list = data.get("qa_list", [])

                for i, item in enumerate(raw_qa_list):
                    category = item.get("category", "other")
                    qa = QAPair(
                        id=f"qa_{batch_index:03d}_{i:03d}",
                        question=item.get("question", ""),
                        answer=item.get("answer", ""),
                        category=category,
                        category_name=self.CATEGORIES.get(category, "其他"),
                        confidence=item.get("confidence", 0.8),
                        context=item.get("context", ""),
                        source_msg_ids=[m.msg_id for m in messages],
                        keywords=item.get("keywords", []),
                        severity=item.get("severity", "medium"),
                    )
                    qa_list.append(qa)
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")

        return qa_list

    def _deduplicate_qa(self, qa_list: List[QAPair]) -> List[QAPair]:
        """去重"""
        seen_questions = set()
        unique_qa = []

        for qa in qa_list:
            # 简单的去重：基于问题前 50 字符
            question_key = qa.question[:50].strip()
            if question_key not in seen_questions:
                seen_questions.add(question_key)
                unique_qa.append(qa)

        return unique_qa

    def _generate_statistics(self, qa_list: List[QAPair]) -> Dict[str, Any]:
        """生成统计信息"""
        from collections import Counter

        category_counts = Counter([qa.category for qa in qa_list])
        severity_counts = Counter([qa.severity for qa in qa_list])

        return {
            "total_count": len(qa_list),
            "by_category": dict(category_counts),
            "by_severity": dict(severity_counts),
            "generated_at": datetime.now().isoformat(),
        }


# 便捷函数
async def extract_qa_from_messages(
    messages: List[ChatMessage],
    api_base_url: str,
    api_key: str,
    model: str = "gpt-4",
) -> Dict[str, Any]:
    """从消息提取 QA"""
    async with QAExtractor(api_base_url, api_key, model) as extractor:
        return await extractor.extract_qa(messages)
