"""
QA 分类器模块

对问答对进行智能分类
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
from core.qa_generator import QAPair


@dataclass
class ClassifiedQA:
    """分类后的 QA"""
    qa: QAPair
    category: str
    confidence: float
    reason: str
    keywords: List[str]
    severity: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.qa.to_dict(),
            "category": self.category,
            "classification_confidence": self.confidence,
            "classification_reason": self.reason,
            "keywords": self.keywords,
            "severity": self.severity,
        }


class QAClassifier:
    """
    QA 分类器
    
    支持的分类：
    - system_bug: 系统Bug
    - data_issue: 数据问题
    - business_issue: 业务问题
    - user_issue: 用户问题
    - feature_request: 功能需求
    - other: 其他问题
    """
    
    # 分类关键词
    CATEGORY_KEYWORDS = {
        "system_bug": [
            "报错", "错误", "崩溃", "异常", "bug", "500", "404",
            "无法", "失败", "卡住", "闪退", "白屏", "黑屏",
            "不响应", "超时", "连接失败", "服务器错误",
        ],
        "data_issue": [
            "数据", "不一致", "错误", "缺失", "丢失", "重复",
            "对不上", "不匹配", "同步", "导入", "导出",
            "显示错误", "数据问题", "数据异常",
        ],
        "business_issue": [
            "流程", "审批", "规则", "配置", "设置", "权限",
            "业务", "操作", "步骤", "办理", "申请", "审核",
        ],
        "user_issue": [
            "怎么", "如何", "能不能", "可以", "怎样", "使用",
            "操作", "功能", "在哪里", "找不到", "不会用",
        ],
        "feature_request": [
            "建议", "希望", "想要", "能不能加", "新增", "功能",
            "改进", "优化", "需求", "期待",
        ],
    }
    
    # 严重级别关键词
    SEVERITY_KEYWORDS = {
        "critical": ["崩溃", "无法使用", "严重", "紧急", "全部用户"],
        "high": ["报错", "失败", "无法", "影响", "阻碍"],
        "medium": ["问题", "异常", "不对", "错误"],
        "low": ["建议", "咨询", "询问", "优化"],
    }
    
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
    
    async def classify_batch(
        self,
        qa_pairs: List[QAPair],
        use_llm: bool = True,
    ) -> List[ClassifiedQA]:
        """
        批量分类 QA 对
        
        Args:
            qa_pairs: QA 对列表
            use_llm: 是否使用大模型分类
        
        Returns:
            分类后的 QA 列表
        """
        await self._init_session()
        
        results = []
        
        if use_llm:
            results = await self._classify_with_llm(qa_pairs)
        else:
            results = await self._classify_with_rules(qa_pairs)
        
        return results
    
    async def _classify_with_llm(
        self,
        qa_pairs: List[QAPair],
    ) -> List[ClassifiedQA]:
        """使用大模型分类"""
        # 格式化 QA 列表
        qa_list_str = "\n".join([
            f"ID: {qa.id}\n问题: {qa.question}\n答案: {qa.answer}\n"
            for qa in qa_pairs
        ])
        
        prompt = self.llm_config.classification_prompt.format(qa_list=qa_list_str)
        
        try:
            response = await self._call_llm(prompt)
            classifications = self._parse_classification_response(response)
            
            results = []
            for qa in qa_pairs:
                cls = classifications.get(qa.id, {
                    "category": "other",
                    "confidence": 0.5,
                    "reason": "未能识别具体分类",
                })
                
                # 提取关键词
                keywords = self._extract_keywords(qa.question + " " + qa.answer)
                
                # 判断严重级别
                severity = self._determine_severity(qa.question, cls["category"])
                
                results.append(ClassifiedQA(
                    qa=qa,
                    category=cls["category"],
                    confidence=cls["confidence"],
                    reason=cls["reason"],
                    keywords=keywords,
                    severity=severity,
                ))
            
            return results
        except Exception as e:
            print(f"LLM 分类失败，使用规则分类: {e}")
            return await self._classify_with_rules(qa_pairs)
    
    async def _classify_with_rules(
        self,
        qa_pairs: List[QAPair],
    ) -> List[ClassifiedQA]:
        """使用规则分类"""
        results = []
        
        for qa in qa_pairs:
            # 合并问题和答案进行关键词匹配
            text = qa.question + " " + qa.answer
            
            # 计算各分类的匹配分数
            scores = {}
            matched_keywords = {}
            
            for category, keywords in self.CATEGORY_KEYWORDS.items():
                score = 0
                matched = []
                for keyword in keywords:
                    if keyword in text:
                        score += 1
                        matched.append(keyword)
                scores[category] = score
                matched_keywords[category] = matched
            
            # 选择最高分的分类
            if max(scores.values()) > 0:
                best_category = max(scores, key=scores.get)
                confidence = scores[best_category] / sum(scores.values()) if sum(scores.values()) > 0 else 0.5
                keywords = matched_keywords[best_category]
            else:
                best_category = "other"
                confidence = 0.5
                keywords = []
            
            # 判断严重级别
            severity = self._determine_severity(text, best_category)
            
            results.append(ClassifiedQA(
                qa=qa,
                category=best_category,
                confidence=min(confidence, 1.0),
                reason=f"基于关键词匹配: {', '.join(keywords[:3])}" if keywords else "默认分类",
                keywords=keywords,
                severity=severity,
            ))
        
        return results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        for category, kws in self.CATEGORY_KEYWORDS.items():
            for kw in kws:
                if kw in text and kw not in keywords:
                    keywords.append(kw)
        return keywords[:5]
    
    def _determine_severity(self, text: str, category: str) -> str:
        """判断严重级别"""
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return severity
        return "medium"
    
    async def _call_llm(self, prompt: str) -> str:
        """调用大模型"""
        session = self._session
        
        payload = {
            "model": self.llm_config.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的问答分类助手。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": self.llm_config.max_tokens,
            "temperature": 0.3,
        }
        
        async with session.post(
            f"{self.llm_config.api_base_url}/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["choices"][0]["message"]["content"]
    
    def _parse_classification_response(self, response: str) -> Dict[str, Dict]:
        """解析分类响应"""
        classifications = {}
        
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                results = json.loads(json_match.group())
                for item in results:
                    qa_id = item.get("id", "")
                    classifications[qa_id] = {
                        "category": item.get("category", "other"),
                        "confidence": item.get("confidence", 0.5),
                        "reason": item.get("reason", ""),
                    }
        except json.JSONDecodeError:
            pass
        
        return classifications


# 便捷函数
async def classify_qa_pairs(
    qa_pairs: List[QAPair],
    use_llm: bool = False,
) -> List[ClassifiedQA]:
    """分类 QA 对"""
    classifier = QAClassifier()
    async with classifier:
        return await classifier.classify_batch(qa_pairs, use_llm=use_llm)
