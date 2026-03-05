"""
QA 生成器模块

从群聊消息中提取问答对
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from config import config
from api.dingtalk_api import ChatMessage


@dataclass
class QAPair:
    """问答对"""
    id: str
    question: str
    answer: str
    context: str
    source_msg_ids: List[str]
    confidence: float
    category: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "context": self.context,
            "source_msg_ids": self.source_msg_ids,
            "confidence": self.confidence,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QAPair":
        return cls(
            id=data["id"],
            question=data["question"],
            answer=data["answer"],
            context=data.get("context", ""),
            source_msg_ids=data.get("source_msg_ids", []),
            confidence=data.get("confidence", 0.0),
            category=data.get("category"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
        )


class QAGenerator:
    """
    QA 生成器
    
    功能：
    - 从群聊消息提取问答对
    - 使用大模型进行智能提取
    - 支持上下文理解
    """
    
    def __init__(self):
        self.llm_config = config.llm
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
                    "Authorization": f"Bearer {self.llm_config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=60),
            )
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def generate_qa(
        self,
        messages: List[ChatMessage],
        batch_size: int = 20,
    ) -> List[QAPair]:
        """
        从消息列表生成 QA 对
        
        Args:
            messages: 聊天消息列表
            batch_size: 批处理大小
        
        Returns:
            QA 对列表
        """
        await self._init_session()
        
        all_qa_pairs = []
        
        # 分批处理消息
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            qa_pairs = await self._process_batch(batch)
            all_qa_pairs.extend(qa_pairs)
        
        return all_qa_pairs
    
    async def _process_batch(self, messages: List[ChatMessage]) -> List[QAPair]:
        """处理一批消息"""
        # 格式化消息
        formatted_messages = self._format_messages(messages)
        
        # 构建提示词
        prompt = self.llm_config.qa_generation_prompt.format(
            messages=formatted_messages
        )
        
        # 调用大模型
        try:
            response = await self._call_llm(prompt)
            qa_list = self._parse_llm_response(response)
            
            # 构建 QAPair 对象
            qa_pairs = []
            for i, qa in enumerate(qa_list):
                qa_pairs.append(QAPair(
                    id=f"qa_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i:04d}",
                    question=qa.get("question", ""),
                    answer=qa.get("answer", ""),
                    context=qa.get("context", ""),
                    source_msg_ids=[m.msg_id for m in messages],
                    confidence=qa.get("confidence", 0.8),
                ))
            
            return qa_pairs
        except Exception as e:
            print(f"处理批次失败: {e}")
            return []
    
    def _format_messages(self, messages: List[ChatMessage]) -> str:
        """格式化消息用于 LLM 输入"""
        lines = []
        for msg in messages:
            time_str = msg.timestamp.strftime("%H:%M")
            lines.append(f"[{time_str}] {msg.sender_name}: {msg.content}")
        return "\n".join(lines)
    
    async def _call_llm(self, prompt: str) -> str:
        """调用大模型"""
        session = self._session
        
        payload = {
            "model": self.llm_config.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的客服问答助手。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.llm_config.max_tokens,
            "temperature": self.llm_config.temperature,
        }
        
        async with session.post(
            f"{self.llm_config.api_base_url}/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["choices"][0]["message"]["content"]
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """解析 LLM 响应"""
        # 尝试提取 JSON
        try:
            # 查找 JSON 数组
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # 如果解析失败，尝试其他格式
        qa_list = []
        lines = response.split("\n")
        current_q = None
        current_a = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("问") or line.startswith("Q:"):
                if current_q and current_a:
                    qa_list.append({
                        "question": current_q,
                        "answer": current_a,
                        "context": "",
                    })
                current_q = line.split(":", 1)[-1].split("：", 1)[-1].strip()
                current_a = None
            elif line.startswith("答") or line.startswith("A:"):
                current_a = line.split(":", 1)[-1].split("：", 1)[-1].strip()
        
        if current_q and current_a:
            qa_list.append({
                "question": current_q,
                "answer": current_a,
                "context": "",
            })
        
        return qa_list


class MockQAGenerator:
    """
    模拟 QA 生成器（用于测试）
    """
    
    async def generate_qa(
        self,
        messages: List[ChatMessage],
        batch_size: int = 20,
    ) -> List[QAPair]:
        """模拟生成 QA"""
        qa_pairs = []
        
        # 简单的规则匹配生成 QA
        i = 0
        while i < len(messages) - 1:
            msg = messages[i]
            content = msg.content
            
            # 检测问题（包含问号或关键词）
            is_question = ("?" in content or "？" in content or 
                          any(kw in content for kw in ["怎么", "如何", "为什么", "能不能", "可以", "求助"]))
            
            if is_question and i + 1 < len(messages):
                # 找下一个非问题的消息作为答案
                answer_msg = messages[i + 1]
                for j in range(i + 1, min(i + 5, len(messages))):
                    if not any(kw in messages[j].content for kw in ["?", "？", "怎么", "如何"]):
                        answer_msg = messages[j]
                        break
                
                qa_pairs.append(QAPair(
                    id=f"qa_mock_{len(qa_pairs):04d}",
                    question=content,
                    answer=answer_msg.content,
                    context=f"来自群聊，提问者: {msg.sender_name}",
                    source_msg_ids=[msg.msg_id, answer_msg.msg_id],
                    confidence=0.75,
                ))
                i += 2
            else:
                i += 1
        
        return qa_pairs
    
    async def close(self):
        pass


# 便捷函数
async def generate_qa_from_messages(
    messages: List[ChatMessage],
    use_mock: bool = True,
) -> List[QAPair]:
    """从消息生成 QA"""
    generator = MockQAGenerator() if use_mock else QAGenerator()
    async with generator:
        return await generator.generate_qa(messages)
