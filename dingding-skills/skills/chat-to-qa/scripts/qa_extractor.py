"""
QA Extractor - 从群聊消息中提取 QA 的核心脚本（金融场景版）

功能：
1. 理解上下文，从零散聊天中提取 QA
2. 支持金融场景分类（金融、系统、其他）
3. 理解人员角色、图片信息
4. 输出 FastGpt 适配格式
"""

import asyncio
import json
import re
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
    sender_role: str = "unknown"
    content: str = ""
    msg_type: str = "text"
    pic_url: str = ""
    create_time: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "sender_role": self.sender_role,
            "content": self.content,
            "msg_type": self.msg_type,
            "pic_url": self.pic_url,
            "create_time": self.create_time,
        }
    
    def format_for_llm(self) -> str:
        """格式化为 LLM 输入格式"""
        time_str = ""
        if self.create_time:
            time_str = datetime.fromtimestamp(self.create_time / 1000).strftime("%H:%M")
        
        role_label = f"[{self.sender_role}]" if self.sender_role != "unknown" else ""
        pic_label = " [图片]" if self.pic_url else ""
        
        return f"[{time_str}] {self.sender_name}{role_label}: {self.content}{pic_label}"


@dataclass
class QAPair:
    """问答对"""
    id: str
    question: str
    answer: str
    tags: List[str]
    category: str
    confidence: float
    context: Dict[str, Any]
    keywords: List[str]
    severity: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "tags": self.tags,
            "category": self.category,
            "confidence": self.confidence,
            "context": self.context,
            "keywords": self.keywords,
            "severity": self.severity,
        }
    
    def to_fastgpt(self) -> Dict[str, Any]:
        """转换为 FastGpt 格式"""
        return {
            "q": self.question,
            "a": self.answer,
            "tags": self.tags,
        }


class QAExtractor:
    """
    QA 提取器（金融场景版）
    
    分类标签：
    - finance: 金融业务问题
    - system: 系统Bug问题
    - other: 其他问题
    """

    # 分类标签定义
    CATEGORIES = {
        "finance": {
            "name": "金融",
            "keywords": [
                "合同", "借款", "贷款", "签署", "银行", "验证码", "交易",
                "账户", "金额", "还款", "放款", "审核", "签约", "授信",
                "利率", "期限", "本金", "利息", "逾期", "结清", "转账",
                "上海银行", "借款合同", "金融", "资金", "提现", "充值"
            ]
        },
        "system": {
            "name": "系统",
            "keywords": [
                "报错", "异常", "崩溃", "失败", "超时", "验证码初始化",
                "接口", "网络", "服务器", "登录", "加载", "白屏", "黑屏",
                "转圈", "卡住", "无法", "错误", "bug", "500", "404",
                "初始化", "系统", "页面", "闪退", "断开"
            ]
        },
        "other": {
            "name": "其他",
            "keywords": []
        }
    }

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
        group_name: str = "金融业务群",
        batch_size: int = 30,
    ) -> Dict[str, Any]:
        """
        从消息列表提取 QA

        Args:
            messages: 聊天消息列表
            group_name: 群聊名称
            batch_size: 批处理大小

        Returns:
            包含 qa_list 和 statistics 的字典
        """
        await self._init_session()

        all_qa_list = []

        # 分批处理，保留上下文衔接
        for i in range(0, len(messages), batch_size):
            start = max(0, i - 5) if i > 0 else i
            batch_messages = messages[start:i + batch_size]
            
            qa_list = await self._process_batch(
                batch_messages, 
                group_name,
                i // batch_size
            )
            all_qa_list.extend(qa_list)

        # 去重
        all_qa_list = self._deduplicate_qa(all_qa_list)

        # 生成统计
        statistics = self._generate_statistics(all_qa_list)

        return {
            "qa_list": [qa.to_dict() for qa in all_qa_list],
            "fastgpt_list": [qa.to_fastgpt() for qa in all_qa_list],
            "statistics": statistics,
        }

    async def _process_batch(
        self,
        messages: List[ChatMessage],
        group_name: str,
        batch_index: int,
    ) -> List[QAPair]:
        """处理一批消息"""
        formatted_messages = "\n".join([m.format_for_llm() for m in messages])
        prompt = self._build_extraction_prompt(formatted_messages, group_name)

        try:
            response = await self._call_llm(prompt)
            qa_list = self._parse_response(response, messages, group_name, batch_index)
            return qa_list
        except Exception as e:
            print(f"处理批次 {batch_index} 失败: {e}")
            return []

    def _build_extraction_prompt(self, messages: str, group_name: str) -> str:
        """构建提取 prompt"""
        return f"""你是一个专业的金融客服问答助手。请从以下钉钉群聊消息中提取有价值的问答对(QA)。

## 背景
这是金融业务场景的群聊，消息可能是零散的，需要理解上下文来判断问答关系。

## 分类标签
- 金融(finance): 金融业务问题，涉及合同、借款、贷款、签署、交易、验证码、银行等
- 系统(system): 系统Bug或技术问题，涉及报错、异常、崩溃、失败、超时、初始化等
- 其他(other): 不属于以上分类的问题

## 提取规则
1. **理解上下文**: 答案可能分散在多条消息中，需要合并
2. **识别角色**: 区分客户（提问者）和技术支持/客服（回答者）
3. **处理图片**: 如果有图片标记，在 context 中说明
4. **质量要求**: 问题要清晰完整，答案要准确有用
5. **多标签**: 可以同时属于"金融"和"系统"，用 tags 数组表示

## 群聊信息
群名: {group_name}

## 聊天记录
{messages}

## 输出格式
请以 JSON 格式输出：
```json
{{
  "qa_list": [
    {{
      "question": "整理后的问题",
      "answer": "整理后的答案",
      "tags": ["金融", "系统"],
      "category": "主分类(finance/system/other)",
      "confidence": 0.95,
      "questioner": "提问者名称",
      "answerer": "回答者名称",
      "has_image": false,
      "keywords": ["关键词"],
      "severity": "严重级别(critical/high/medium/low)"
    }}
  ]
}}
```

如果没有有价值的问答，输出: {{"qa_list": []}}"""

    async def _call_llm(self, prompt: str) -> str:
        """调用大模型"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的金融客服问答助手，擅长从群聊对话中提取有价值的问答信息。"
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
        group_name: str,
        batch_index: int,
    ) -> List[QAPair]:
        """解析 LLM 响应"""
        qa_list = []

        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                raw_qa_list = data.get("qa_list", [])

                for i, item in enumerate(raw_qa_list):
                    # 确定分类和标签
                    category = item.get("category", "other")
                    tags = item.get("tags", [])
                    
                    # 如果没有标签，根据分类添加
                    if not tags:
                        category_info = self.CATEGORIES.get(category, {})
                        category_name = category_info.get("name", "其他")
                        tags = [category_name]
                    
                    # 构建上下文
                    source_time = ""
                    if messages:
                        first_msg = messages[0]
                        if first_msg.create_time:
                            source_time = datetime.fromtimestamp(
                                first_msg.create_time / 1000
                            ).strftime("%Y-%m-%d %H:%M")
                    
                    context = {
                        "questioner": item.get("questioner", ""),
                        "answerer": item.get("answerer", ""),
                        "group_name": group_name,
                        "has_image": item.get("has_image", False),
                        "image_desc": item.get("image_desc", ""),
                        "source_time": source_time,
                    }
                    
                    qa = QAPair(
                        id=f"qa_{batch_index:03d}_{i:03d}",
                        question=item.get("question", ""),
                        answer=item.get("answer", ""),
                        tags=tags,
                        category=category,
                        confidence=item.get("confidence", 0.8),
                        context=context,
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
        
        # 统计标签
        all_tags = []
        for qa in qa_list:
            all_tags.extend(qa.tags)
        tag_counts = Counter(all_tags)

        return {
            "total_count": len(qa_list),
            "by_category": dict(category_counts),
            "by_severity": dict(severity_counts),
            "by_tags": dict(tag_counts),
            "generated_at": datetime.now().isoformat(),
        }


async def extract_qa_from_messages(
    messages: List[ChatMessage],
    api_base_url: str,
    api_key: str,
    model: str = "gpt-4",
    group_name: str = "金融业务群",
) -> Dict[str, Any]:
    """便捷函数：从消息提取 QA"""
    async with QAExtractor(api_base_url, api_key, model) as extractor:
        return await extractor.extract_qa(messages, group_name)
