"""
HTTP API 服务 - 供 FastGPT 工作流调用

提供以下 API：
1. GET  /api/messages     - 获取聊天消息
2. POST /api/extract-qa   - 从消息提取 QA
3. POST /api/sync         - 完整同步流程
4. GET  /api/fastgpt/qa   - FastGPT 格式 QA（推荐）
5. GET  /api/health       - 健康检查

使用方法：
    python api_server.py --port 8080
    
在 FastGPT 工作流中：
    - HTTP 请求节点调用 http://your-server:8080/api/fastgpt/qa?days=1
    - 返回 FastGPT 格式的 QA 数据
    - 直接导入知识库
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "skills" / "chat-to-qa" / "scripts"))

from config import config

# 创建 FastAPI 应用
app = FastAPI(
    title="钉钉 QA 提取服务",
    description="从钉钉群聊中提取 QA，供 FastGPT 知识库使用",
    version="1.0.0",
)

# 跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== 请求/响应模型 ==============

class MessageRequest(BaseModel):
    """消息请求"""
    chat_id: str = "all"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    max_messages: int = 1000


class ExtractQARequest(BaseModel):
    """提取 QA 请求"""
    messages: List[Dict[str, Any]]
    group_name: str = "金融业务群"


class SyncRequest(BaseModel):
    """同步请求"""
    chat_id: str = "all"
    days: int = 1
    auto_import: bool = False
    fastgpt_key: Optional[str] = None
    fastgpt_dataset: Optional[str] = None


class QAResponse(BaseModel):
    """QA 响应"""
    success: bool
    qa_list: List[Dict[str, Any]]
    fastgpt_list: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    message: str = ""


# ============== 全局状态 ==============

class AppState:
    use_real_api: bool = False
    last_sync_time: Optional[datetime] = None
    sync_count: int = 0


state = AppState()


# ============== 核心逻辑 ==============

def get_mock_messages(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """获取模拟消息"""
    base_time = start_time or (datetime.now() - timedelta(days=1))
    
    return [
        {
            "msg_id": "msg_api_001",
            "sender_id": "user_001",
            "sender_name": "客户A",
            "sender_role": "customer",
            "content": "上海银行 签署【借款合同】提示：验证码初始化异常",
            "create_time": int(base_time.timestamp() * 1000),
        },
        {
            "msg_id": "msg_api_002",
            "sender_id": "user_002",
            "sender_name": "技术支持",
            "sender_role": "support",
            "content": "验证码输错6次会有这个报错提示，请重试输入正确验证码",
            "create_time": int((base_time + timedelta(minutes=5)).timestamp() * 1000),
        },
        {
            "msg_id": "msg_api_003",
            "sender_id": "user_003",
            "sender_name": "客户B",
            "sender_role": "customer",
            "content": "请问借款合同签署后多久可以放款？",
            "create_time": int((base_time + timedelta(hours=2)).timestamp() * 1000),
        },
        {
            "msg_id": "msg_api_004",
            "sender_id": "user_004",
            "sender_name": "业务经理",
            "sender_role": "business",
            "content": "正常情况下1-3个工作日放款，具体看银行审核进度",
            "create_time": int((base_time + timedelta(hours=2, minutes=5)).timestamp() * 1000),
        },
        {
            "msg_id": "msg_api_005",
            "sender_id": "user_005",
            "sender_name": "客户C",
            "sender_role": "customer",
            "content": "系统登录一直转圈进不去怎么办？",
            "create_time": int((base_time + timedelta(hours=4)).timestamp() * 1000),
        },
        {
            "msg_id": "msg_api_006",
            "sender_id": "user_002",
            "sender_name": "技术支持",
            "sender_role": "support",
            "content": "服务器正在升级，请等待10分钟后重试",
            "create_time": int((base_time + timedelta(hours=4, minutes=2)).timestamp() * 1000),
        },
    ]


def extract_qa_from_messages(messages: List[Dict]) -> Dict[str, Any]:
    """从消息中提取 QA"""
    qa_list = []
    fastgpt_list = []
    
    i = 0
    while i < len(messages) - 1:
        msg = messages[i]
        content = msg.get("content", "")
        
        # 判断是否是问题
        is_question = (
            "?" in content or "？" in content or
            "提示" in content or "异常" in content or
            any(kw in content for kw in ["怎么", "如何", "请问", "怎么办"])
        )
        
        if is_question and i + 1 < len(messages):
            answer_msg = messages[i + 1]
            answer_content = answer_msg.get("content", "")
            
            # 跳过过短的答案
            if len(answer_content) < 5:
                i += 1
                continue
            
            # 分类
            tags = []
            category = "other"
            text = content + " " + answer_content
            
            finance_keywords = ["借款", "合同", "贷款", "银行", "放款", "签署", "验证码", "金融", "还款"]
            system_keywords = ["异常", "报错", "错误", "失败", "超时", "初始化", "系统", "登录", "服务器"]
            
            if any(kw in text for kw in finance_keywords):
                tags.append("金融")
                category = "finance"
            if any(kw in text for kw in system_keywords):
                tags.append("系统")
                if category == "other":
                    category = "system"
            
            if not tags:
                tags = ["其他"]
            
            qa = {
                "id": f"qa_{msg.get('msg_id', i)}",
                "question": content,
                "answer": answer_content,
                "tags": tags,
                "category": category,
                "confidence": 0.85,
                "context": {
                    "questioner": msg.get("sender_name", "未知"),
                    "answerer": answer_msg.get("sender_name", "未知"),
                    "source_time": datetime.fromtimestamp(
                        msg.get("create_time", 0) / 1000
                    ).strftime("%Y-%m-%d %H:%M") if msg.get("create_time") else "",
                },
            }
            
            qa_list.append(qa)
            fastgpt_list.append({
                "q": content,
                "a": answer_content,
                "tags": tags,
            })
            
            i += 2
        else:
            i += 1
    
    # 统计
    from collections import Counter
    category_counts = Counter([qa["category"] for qa in qa_list])
    tag_counts = Counter([tag for qa in qa_list for tag in qa["tags"]])
    
    return {
        "qa_list": qa_list,
        "fastgpt_list": fastgpt_list,
        "statistics": {
            "total_count": len(qa_list),
            "by_category": dict(category_counts),
            "by_tags": dict(tag_counts),
        }
    }


# ============== API 端点 ==============

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "last_sync": state.last_sync_time.isoformat() if state.last_sync_time else None,
        "sync_count": state.sync_count,
    }


@app.get("/api/messages")
async def get_messages(
    chat_id: str = Query(default="all", description="群聊 ID"),
    start_date: Optional[str] = Query(default=None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="结束日期 (YYYY-MM-DD)"),
    max_messages: int = Query(default=100, description="最大消息数"),
):
    """
    获取聊天消息
    
    FastGPT 工作流调用:
    GET /api/messages?start_date=2024-01-14&end_date=2024-01-15
    """
    start_time = None
    end_time = None
    
    if start_date:
        start_time = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_time = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    
    messages = get_mock_messages(start_time, end_time)
    
    return {
        "success": True,
        "count": len(messages[:max_messages]),
        "messages": messages[:max_messages],
    }


@app.post("/api/extract-qa", response_model=QAResponse)
async def extract_qa(request: ExtractQARequest):
    """
    从消息中提取 QA
    
    FastGPT 工作流调用:
    POST /api/extract-qa
    Body: {"messages": [...], "group_name": "金融业务群"}
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="消息列表不能为空")
    
    qa_data = extract_qa_from_messages(request.messages)
    
    return QAResponse(
        success=True,
        qa_list=qa_data["qa_list"],
        fastgpt_list=qa_data["fastgpt_list"],
        statistics=qa_data["statistics"],
        message=f"成功提取 {len(qa_data['qa_list'])} 个 QA",
    )


@app.post("/api/sync", response_model=QAResponse)
async def sync_data(request: SyncRequest):
    """
    完整同步流程
    
    FastGPT 定时任务调用:
    POST /api/sync
    Body: {"days": 1, "auto_import": false}
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=request.days)
    
    messages = get_mock_messages(start_time, end_time)
    
    if not messages:
        return QAResponse(
            success=True,
            qa_list=[],
            fastgpt_list=[],
            statistics={"total_count": 0},
            message="没有找到消息",
        )
    
    qa_data = extract_qa_from_messages(messages)
    
    state.last_sync_time = datetime.now()
    state.sync_count += 1
    
    return QAResponse(
        success=True,
        qa_list=qa_data["qa_list"],
        fastgpt_list=qa_data["fastgpt_list"],
        statistics={
            **qa_data["statistics"],
            "sync_time": state.last_sync_time.isoformat(),
        },
        message=f"成功同步 {request.days} 天数据，提取 {len(qa_data['qa_list'])} 个 QA",
    )


@app.get("/api/fastgpt/qa")
async def get_fastgpt_qa(
    days: int = Query(default=1, description="获取最近几天的数据"),
):
    """
    【推荐】获取 FastGPT 格式的 QA 数据
    
    FastGPT 工作流最简调用:
    GET /api/fastgpt/qa?days=1
    
    返回格式直接可用于知识库导入:
    {
      "list": [
        {"q": "问题", "a": "答案", "tags": ["金融"]}
      ]
    }
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    messages = get_mock_messages(start_time, end_time)
    qa_data = extract_qa_from_messages(messages)
    
    state.last_sync_time = datetime.now()
    state.sync_count += 1
    
    return {
        "list": qa_data["fastgpt_list"],
        "total": len(qa_data["fastgpt_list"]),
        "sync_time": datetime.now().isoformat(),
        "statistics": qa_data["statistics"],
    }


# ============== 启动 ==============

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="钉钉 QA 提取 API 服务")
    parser.add_argument("--port", type=int, default=8080, help="服务端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务地址")
    parser.add_argument("--real", action="store_true", help="使用真实 API")
    
    args = parser.parse_args()
    state.use_real_api = args.real
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║        钉钉 QA 提取 API 服务 (FastGPT 集成)              ║
╠══════════════════════════════════════════════════════════╣
║  服务地址: http://{args.host}:{args.port}                       ║
║  API 文档: http://{args.host}:{args.port}/docs                  ║
╠══════════════════════════════════════════════════════════╣
║  FastGPT 工作流推荐接口:                                ║
║                                                          ║
║  GET /api/fastgpt/qa?days=1                             ║
║  返回: {"list": [{"q": "...", "a": "...", "tags": [...]}]}║
╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
