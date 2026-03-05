#!/usr/bin/env python3
"""
QA 提取器 - 根据 SKILL.md 规则从聊天记录中提取问答对

输出 CSV 格式：
- 第一列: q (问题)
- 第二列: a (答案)
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


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


@dataclass
class QAPair:
    """问答对"""
    question: str
    answer: str
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_csv_row(self) -> List[str]:
        """转换为 CSV 行 [q, a]"""
        return [self.question, self.answer]


class QAExtractor:
    """
    QA 提取器
    
    根据 SKILL.md 定义的规则：
    1. 识别问题（疑问词、问号、异常报告等）
    2. 匹配答案（直接回答、解决方案等）
    3. 分类标签（金融、系统、其他）
    """
    
    # 分类关键词（来自 SKILL.md）
    FINANCE_KEYWORDS = [
        "合同", "借款", "贷款", "签署", "银行", "验证码", "交易",
        "账户", "金额", "还款", "放款", "审核", "签约", "授信",
        "利率", "期限", "本金", "利息", "逾期", "结清", "转账"
    ]
    
    SYSTEM_KEYWORDS = [
        "报错", "异常", "崩溃", "失败", "超时", "初始化",
        "接口", "网络", "服务器", "登录", "加载", "白屏", "黑屏",
        "转圈", "卡住", "无法", "错误", "bug", "500", "404"
    ]
    
    # 问题识别关键词
    QUESTION_KEYWORDS = [
        "怎么", "如何", "为什么", "能不能", "可以", "是否", "什么",
        "请问", "求助", "怎么办", "为什么"
    ]
    
    def __init__(self):
        pass
    
    def extract_from_messages(self, messages: List[ChatMessage]) -> List[QAPair]:
        """
        从消息列表中提取 QA
        
        Args:
            messages: 聊天消息列表
        
        Returns:
            QA 对列表
        """
        qa_pairs = []
        
        i = 0
        while i < len(messages) - 1:
            msg = messages[i]
            content = msg.content.strip()
            
            # 判断是否是问题
            is_question = self._is_question(content)
            
            if is_question:
                # 查找答案
                answer_content = self._find_answer(messages, i)
                
                if answer_content:
                    # 分类标签
                    tags = self._classify(content + " " + answer_content)
                    
                    qa_pairs.append(QAPair(
                        question=self._clean_question(content),
                        answer=self._clean_answer(answer_content),
                        tags=tags,
                    ))
                    
                    i += 2  # 跳过问题和答案
                else:
                    i += 1
            else:
                i += 1
        
        return qa_pairs
    
    def _is_question(self, content: str) -> bool:
        """判断是否是问题"""
        if not content:
            return False
        
        # 包含问号
        if "?" in content or "？" in content:
            return True
        
        # 包含疑问词
        for kw in self.QUESTION_KEYWORDS:
            if kw in content:
                return True
        
        # 报告异常
        if any(kw in content for kw in ["提示", "报错", "异常", "失败"]):
            return True
        
        return False
    
    def _find_answer(self, messages: List[ChatMessage], question_idx: int) -> Optional[str]:
        """
        查找问题的答案
        
        查找接下来的几条消息，找到不是问题的回答
        """
        answers = []
        
        for j in range(question_idx + 1, min(question_idx + 5, len(messages))):
            msg = messages[j]
            content = msg.content.strip()
            
            # 跳过空消息
            if not content:
                continue
            
            # 跳过表情、确认词等
            if content in ["好的", "收到", "嗯", "可以", "谢谢", "[图片]"]:
                continue
            
            # 如果是下一个问题，停止
            if self._is_question(content):
                break
            
            # 这是答案
            answers.append(content)
            
            # 如果是技术支持/客服回复，可能就是这个答案
            if msg.sender_role in ["support", "service", "business"]:
                break
        
        return " ".join(answers) if answers else None
    
    def _classify(self, text: str) -> List[str]:
        """分类标签"""
        tags = []
        
        # 检查金融关键词
        if any(kw in text for kw in self.FINANCE_KEYWORDS):
            tags.append("金融")
        
        # 检查系统关键词
        if any(kw in text for kw in self.SYSTEM_KEYWORDS):
            tags.append("系统")
        
        # 默认其他
        if not tags:
            tags.append("其他")
        
        return tags
    
    def _clean_question(self, content: str) -> str:
        """清理问题文本"""
        # 去除前后空格
        content = content.strip()
        # 确保以问号结尾
        if not content.endswith("?") and not content.endswith("？"):
            content += "？"
        return content
    
    def _clean_answer(self, content: str) -> str:
        """清理答案文本"""
        content = content.strip()
        return content


def export_to_csv(qa_pairs: List[QAPair], output_path: str) -> str:
    """
    导出 QA 到 CSV 文件
    
    Args:
        qa_pairs: QA 对列表
        output_path: 输出文件路径
    
    Returns:
        导出的文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # 表头
        writer.writerow(['q', 'a'])
        # 数据行
        for qa in qa_pairs:
            writer.writerow(qa.to_csv_row())
    
    return str(output_path)


# 便捷函数
def extract_qa_csv(
    messages: List[Dict[str, Any]],
    output_path: str = "output/qa.csv",
) -> str:
    """
    便捷函数：从消息字典列表提取 QA 并导出 CSV
    
    Args:
        messages: 消息字典列表
        output_path: 输出文件路径
    
    Returns:
        导出的文件路径
    """
    # 转换为 ChatMessage 对象
    chat_messages = [
        ChatMessage(
            msg_id=m.get("msg_id", ""),
            sender_id=m.get("sender_id", ""),
            sender_name=m.get("sender_name", ""),
            sender_role=m.get("sender_role", "unknown"),
            content=m.get("content", ""),
            msg_type=m.get("msg_type", "text"),
            pic_url=m.get("pic_url", ""),
            create_time=m.get("create_time", 0),
        )
        for m in messages
    ]
    
    # 提取 QA
    extractor = QAExtractor()
    qa_pairs = extractor.extract_from_messages(chat_messages)
    
    # 导出 CSV
    return export_to_csv(qa_pairs, output_path)


if __name__ == "__main__":
    # 测试示例
    test_messages = [
        ChatMessage("1", "user1", "客户A", "customer", "上海银行 签署借款合同提示：验证码初始化异常"),
        ChatMessage("2", "user2", "技术支持", "support", "验证码输错6次会有这个报错，请重试输入正确验证码"),
        ChatMessage("3", "user3", "客户B", "customer", "借款合同签署后多久可以放款？"),
        ChatMessage("4", "user4", "业务经理", "business", "正常情况下1-3个工作日放款"),
    ]
    
    extractor = QAExtractor()
    qa_pairs = extractor.extract_from_messages(test_messages)
    
    print(f"提取到 {len(qa_pairs)} 个 QA 对:")
    for qa in qa_pairs:
        print(f"  Q: {qa.question}")
        print(f"  A: {qa.answer}")
        print(f"  Tags: {qa.tags}")
        print()
    
    # 导出 CSV
    output = export_to_csv(qa_pairs, "output/test_qa.csv")
    print(f"CSV 已导出: {output}")
