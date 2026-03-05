"""
钉钉 API 封装模块

提供钉钉群聊数据获取的 API 接口封装
"""

import asyncio
import hashlib
import hmac
import base64
import time
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from config import config, DingTalkConfig


@dataclass
class ChatMessage:
    """聊天消息"""
    msg_id: str
    sender_id: str
    sender_name: str
    content: str
    msg_type: str
    timestamp: datetime
    chat_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "msg_type": self.msg_type,
            "timestamp": self.timestamp.isoformat(),
            "chat_id": self.chat_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            msg_id=data["msg_id"],
            sender_id=data["sender_id"],
            sender_name=data["sender_name"],
            content=data["content"],
            msg_type=data["msg_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            chat_id=data["chat_id"],
        )


@dataclass
class ChatInfo:
    """群聊信息"""
    chat_id: str
    name: str
    owner_id: str
    member_count: int
    create_time: datetime


class DingTalkAPI:
    """
    钉钉 API 客户端
    
    功能：
    - 获取 Access Token
    - 获取群聊列表
    - 获取群聊消息
    - 获取用户信息
    """
    
    def __init__(self, dt_config: Optional[DingTalkConfig] = None):
        self.config = dt_config or config.dingtalk
        self._session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0
    
    async def __aenter__(self):
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _init_session(self):
        """初始化 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
            )
    
    async def close(self):
        """关闭连接"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("Session not initialized")
        return self._session
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_access_token(self) -> str:
        """获取 Access Token"""
        # 检查缓存
        if self._access_token and time.time() < self._token_expire_time:
            return self._access_token
        
        await self._init_session()
        session = self._get_session()
        
        url = f"{self.config.api_base_url}/gettoken"
        params = {
            "appkey": self.config.app_key,
            "appsecret": self.config.app_secret,
        }
        
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            
            if data.get("errcode", 0) != 0:
                raise Exception(f"获取 Access Token 失败: {data.get('errmsg')}")
            
            self._access_token = data["access_token"]
            self._token_expire_time = time.time() + data.get("expires_in", 7200) - 300
            
            return self._access_token
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_chat_list(self) -> List[ChatInfo]:
        """获取群聊列表"""
        token = await self.get_access_token()
        session = self._get_session()
        
        url = f"{self.config.api_base_url}/chat/list"
        headers = {"x-acs-dingtalk-access-token": token}
        
        chats = []
        next_token = None
        
        while True:
            params = {"maxResults": 100}
            if next_token:
                params["nextToken"] = next_token
            
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get("errcode", 0) != 0:
                    raise Exception(f"获取群聊列表失败: {data.get('errmsg')}")
                
                for chat_data in data.get("chat_info_list", []):
                    chats.append(ChatInfo(
                        chat_id=chat_data["chat_id"],
                        name=chat_data["name"],
                        owner_id=chat_data["owner_userid"],
                        member_count=chat_data.get("member_count", 0),
                        create_time=datetime.fromtimestamp(chat_data["create_time"] / 1000),
                    ))
                
                next_token = data.get("next_token")
                if not next_token:
                    break
        
        return chats
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_chat_messages(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_messages: int = 1000,
    ) -> List[ChatMessage]:
        """
        获取群聊消息
        
        Args:
            chat_id: 群聊 ID
            start_time: 开始时间
            end_time: 结束时间
            max_messages: 最大消息数
        
        Returns:
            消息列表
        """
        token = await self.get_access_token()
        session = self._get_session()
        
        url = f"{self.config.api_base_url}/chat/message/list"
        headers = {"x-acs-dingtalk-access-token": token}
        
        messages = []
        next_token = None
        
        # 默认获取最近 7 天的消息
        if not start_time:
            start_time = datetime.now() - timedelta(days=7)
        if not end_time:
            end_time = datetime.now()
        
        while len(messages) < max_messages:
            body = {
                "chat_id": chat_id,
                "start_time": int(start_time.timestamp() * 1000),
                "end_time": int(end_time.timestamp() * 1000),
                "max_results": min(100, max_messages - len(messages)),
            }
            if next_token:
                body["next_token"] = next_token
            
            async with session.post(url, headers=headers, json=body) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data.get("errcode", 0) != 0:
                    raise Exception(f"获取群聊消息失败: {data.get('errmsg')}")
                
                for msg_data in data.get("message_list", []):
                    # 过滤消息类型
                    msg_type = msg_data.get("msgtype", "text")
                    if msg_type not in self.config.message_types:
                        continue
                    
                    # 解析消息内容
                    content = self._parse_message_content(msg_data)
                    if not content:
                        continue
                    
                    messages.append(ChatMessage(
                        msg_id=msg_data["msgid"],
                        sender_id=msg_data.get("senderid", ""),
                        sender_name=msg_data.get("sender_nick", msg_data.get("senderid", "未知")),
                        content=content,
                        msg_type=msg_type,
                        timestamp=datetime.fromtimestamp(msg_data["gmt_create"] / 1000),
                        chat_id=chat_id,
                    ))
                
                next_token = data.get("next_token")
                if not next_token or not data.get("message_list"):
                    break
        
        return messages[:max_messages]
    
    def _parse_message_content(self, msg_data: Dict[str, Any]) -> Optional[str]:
        """解析消息内容"""
        msg_type = msg_data.get("msgtype", "text")
        
        if msg_type == "text":
            return msg_data.get("content", {}).get("text", "")
        elif msg_type == "richText":
            # 富文本消息
            content_parts = []
            for item in msg_data.get("content", {}).get("richContent", []):
                if item.get("type") == "text":
                    content_parts.append(item.get("text", ""))
            return "\n".join(content_parts)
        elif msg_type == "picture":
            return "[图片]"
        elif msg_type == "file":
            return f"[文件] {msg_data.get('content', {}).get('fileName', '')}"
        elif msg_type == "link":
            return f"[链接] {msg_data.get('content', {}).get('title', '')}"
        else:
            return None
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户信息"""
        token = await self.get_access_token()
        session = self._get_session()
        
        url = f"{self.config.api_base_url}/user/get"
        headers = {"x-acs-dingtalk-access-token": token}
        params = {"userid": user_id}
        
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            
            if data.get("errcode", 0) != 0:
                return {"userid": user_id, "name": "未知用户"}
            
            return {
                "userid": data.get("userid"),
                "name": data.get("name"),
                "department": data.get("department", []),
            }


class MockDingTalkAPI:
    """
    模拟钉钉 API（用于测试）
    
    在没有真实钉钉应用时，使用此类进行功能测试
    """
    
    def __init__(self):
        self._mock_messages: List[ChatMessage] = []
        self._generate_mock_data()
    
    def _generate_mock_data(self):
        """生成模拟数据"""
        mock_conversations = [
            {
                "sender": "张三",
                "content": "请问系统登录不了怎么办？",
                "type": "question",
            },
            {
                "sender": "李四",
                "content": "登录不了可能是密码错误，您可以尝试重置密码。在登录页面点击'忘记密码'，输入手机号获取验证码即可重置。",
                "type": "answer",
            },
            {
                "sender": "王五",
                "content": "我发现订单列表的数据对不上，总金额和明细不一致",
                "type": "question",
            },
            {
                "sender": "赵六",
                "content": "这是数据同步延迟的问题，我们的系统每天凌晨会进行数据校验和修复。如果紧急，可以联系运维手动触发同步。",
                "type": "answer",
            },
            {
                "sender": "小明",
                "content": "审批流程卡住了，提交后一直显示待处理",
                "type": "question",
            },
            {
                "sender": "客服小王",
                "content": "审批流程卡住可能有几种原因：1. 审批人未设置 2. 审批人离职 3. 系统异常。请提供工单号，我帮您查询具体原因。",
                "type": "answer",
            },
            {
                "sender": "用户A",
                "content": "页面打开就报错，显示500错误",
                "type": "question",
            },
            {
                "sender": "技术支持",
                "content": "500错误是服务器内部错误，请刷新页面重试。如果问题持续，请提供访问时间和大致操作步骤，我们会排查服务器日志。",
                "type": "answer",
            },
            {
                "sender": "产品经理",
                "content": "建议增加批量导出功能，现在一个个导太慢了",
                "type": "feature",
            },
            {
                "sender": "开发小李",
                "content": "好的，这个需求已记录，预计下个版本会支持批量导出，请关注更新公告。",
                "type": "answer",
            },
            {
                "sender": "财务小张",
                "content": "报销单据上传不了，一直提示文件过大",
                "type": "question",
            },
            {
                "sender": "IT支持",
                "content": "报销单据限制单个文件不超过10MB，请压缩图片或拆分文件后上传。支持jpg、png、pdf格式。",
                "type": "answer",
            },
            {
                "sender": "销售小陈",
                "content": "客户信息导出的Excel打不开，提示文件损坏",
                "type": "question",
            },
            {
                "sender": "技术小周",
                "content": "导出的Excel损坏可能是网络问题导致下载不完整。建议重新导出，或者尝试用WPS打开。如果仍有问题请反馈。",
                "type": "answer",
            },
        ]
        
        base_time = datetime.now() - timedelta(hours=2)
        for i, msg in enumerate(mock_conversations):
            self._mock_messages.append(ChatMessage(
                msg_id=f"mock_msg_{i:04d}",
                sender_id=f"user_{i:03d}",
                sender_name=msg["sender"],
                content=msg["content"],
                msg_type="text",
                timestamp=base_time + timedelta(minutes=i * 5),
                chat_id="mock_chat_001",
            ))
    
    async def get_chat_messages(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_messages: int = 1000,
    ) -> List[ChatMessage]:
        """获取模拟消息"""
        messages = [m for m in self._mock_messages if m.chat_id == chat_id or chat_id == "all"]
        return messages[:max_messages]
    
    async def get_chat_list(self) -> List[ChatInfo]:
        """获取模拟群聊列表"""
        return [
            ChatInfo(
                chat_id="mock_chat_001",
                name="技术支持群",
                owner_id="user_001",
                member_count=50,
                create_time=datetime.now() - timedelta(days=30),
            )
        ]
    
    async def get_access_token(self) -> str:
        return "mock_token"
    
    async def close(self):
        pass


# 便捷函数
async def get_dingtalk_client(use_mock: bool = False) -> DingTalkAPI:
    """获取钉钉客户端"""
    if use_mock:
        return MockDingTalkAPI()
    return DingTalkAPI()
