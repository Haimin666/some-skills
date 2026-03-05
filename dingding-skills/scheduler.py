"""
定时任务调度器

支持：
- 每日定时同步昨天的聊天数据
- 增量处理（只处理新消息）
- 自动导入 FastGPT 知识库
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import json

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "chat-to-qa" / "scripts"))

from rich.console import Console
from rich.panel import Panel

from config import config
from qa_extractor import QAExtractor, ChatMessage
from fastgpt_importer import FastGptImporter, KnowledgeBaseExporter

console = Console()


class SyncRecord:
    """同步记录"""
    
    RECORD_FILE = Path(__file__).parent / "output" / "sync_record.json"
    
    def __init__(self):
        self.record = self._load_record()
    
    def _load_record(self) -> dict:
        """加载同步记录"""
        if self.RECORD_FILE.exists():
            return json.loads(self.RECORD_FILE.read_text(encoding="utf-8"))
        return {
            "last_sync_time": None,
            "processed_msg_ids": [],
            "daily_stats": {}
        }
    
    def _save_record(self):
        """保存同步记录"""
        self.RECORD_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.RECORD_FILE.write_text(
            json.dumps(self.record, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def get_last_sync_time(self) -> Optional[datetime]:
        """获取上次同步时间"""
        if self.record.get("last_sync_time"):
            return datetime.fromisoformat(self.record["last_sync_time"])
        return None
    
    def update_sync_time(self, sync_time: datetime):
        """更新同步时间"""
        self.record["last_sync_time"] = sync_time.isoformat()
        self._save_record()
    
    def add_processed_msgs(self, msg_ids: List[str]):
        """添加已处理的消息ID"""
        self.record["processed_msg_ids"].extend(msg_ids)
        # 只保留最近 10000 条
        if len(self.record["processed_msg_ids"]) > 10000:
            self.record["processed_msg_ids"] = self.record["processed_msg_ids"][-10000:]
        self._save_record()
    
    def is_processed(self, msg_id: str) -> bool:
        """检查消息是否已处理"""
        return msg_id in self.record["processed_msg_ids"]
    
    def add_daily_stat(self, date: str, stat: dict):
        """添加每日统计"""
        self.record["daily_stats"][date] = stat
        # 只保留最近 30 天
        dates = list(self.record["daily_stats"].keys())
        if len(dates) > 30:
            for old_date in dates[:-30]:
                del self.record["daily_stats"][old_date]
        self._save_record()


class DingDingScheduler:
    """
    钉钉数据同步调度器
    
    功能：
    - 定时同步（每日 0 点）
    - 增量处理
    - 自动导入 FastGPT
    """
    
    def __init__(
        self,
        fastgpt_key: Optional[str] = None,
        fastgpt_dataset: Optional[str] = None,
        fastgpt_url: str = "https://api.fastgpt.in",
        use_real_api: bool = False,
    ):
        self.fastgpt_key = fastgpt_key or config.fastgpt.api_key
        self.fastgpt_dataset = fastgpt_dataset or config.fastgpt.dataset_id
        self.fastgpt_url = fastgpt_url or config.fastgpt.api_url
        self.use_real_api = use_real_api
        
        self.sync_record = SyncRecord()
        self._running = False
    
    async def sync_yesterday_data(self) -> dict:
        """
        同步昨天的聊天数据
        
        Returns:
            同步结果
        """
        console.print(Panel.fit(
            f"[bold blue]开始同步昨天的聊天数据[/bold blue]\n"
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            subtitle="DingDing Scheduler"
        ))
        
        # 计算昨天的时间范围
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        
        console.print(f"同步时间范围: {yesterday.strftime('%Y-%m-%d')} 00:00 - 23:59")
        
        try:
            # 1. 获取昨天的消息
            messages = await self._fetch_messages(yesterday, today)
            
            if not messages:
                console.print("[yellow]昨天没有新的聊天消息[/yellow]")
                return {"status": "no_data", "message": "没有新消息"}
            
            # 2. 过滤已处理的消息
            new_messages = [
                m for m in messages 
                if not self.sync_record.is_processed(m.msg_id)
            ]
            
            if not new_messages:
                console.print("[yellow]所有消息都已处理过[/yellow]")
                return {"status": "no_new_data", "message": "没有新消息"}
            
            console.print(f"待处理消息: [green]{len(new_messages)}[/green] 条")
            
            # 3. 提取 QA
            qa_data = await self._extract_qa(new_messages)
            
            if not qa_data.get("qa_list"):
                console.print("[yellow]没有提取到有效的 QA[/yellow]")
                return {"status": "no_qa", "message": "没有有效 QA"}
            
            qa_count = len(qa_data["qa_list"])
            console.print(f"提取 QA: [green]{qa_count}[/green] 条")
            
            # 4. 导出知识库
            export_result = await self._export_knowledge_base(qa_data, yesterday)
            
            # 5. 导入 FastGPT（如果配置了）
            fastgpt_result = None
            if self.fastgpt_key and self.fastgpt_dataset:
                fastgpt_result = await self._import_to_fastgpt(qa_data)
            
            # 6. 更新同步记录
            self.sync_record.add_processed_msgs([m.msg_id for m in new_messages])
            self.sync_record.update_sync_time(datetime.now())
            self.sync_record.add_daily_stat(
                yesterday.strftime("%Y-%m-%d"),
                {
                    "message_count": len(new_messages),
                    "qa_count": qa_count,
                    "sync_time": datetime.now().isoformat(),
                }
            )
            
            result = {
                "status": "success",
                "date": yesterday.strftime("%Y-%m-%d"),
                "message_count": len(new_messages),
                "qa_count": qa_count,
                "export_files": export_result,
                "fastgpt": fastgpt_result,
            }
            
            console.print(Panel.fit(
                f"[bold green]✅ 同步完成[/bold green]\n"
                f"日期: {yesterday.strftime('%Y-%m-%d')}\n"
                f"消息: {len(new_messages)} 条\n"
                f"QA: {qa_count} 条",
                subtitle="Sync Complete"
            ))
            
            return result
            
        except Exception as e:
            console.print(f"[red]同步失败: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    async def _fetch_messages(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[ChatMessage]:
        """获取消息"""
        if self.use_real_api:
            # TODO: 调用真实的钉钉 API
            return self._get_mock_messages(start_time, end_time)
        else:
            return self._get_mock_messages(start_time, end_time)
    
    def _get_mock_messages(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[ChatMessage]:
        """获取模拟消息"""
        # 模拟昨天的聊天数据
        base_time = start_time + timedelta(hours=10)
        
        mock_data = [
            {
                "msg_id": f"msg_{start_time.strftime('%Y%m%d')}_001",
                "sender_id": "user_001",
                "sender_name": "客户A",
                "sender_role": "customer",
                "content": "上海银行 签署【借款合同】提示：验证码初始化异常",
                "create_time": int(base_time.timestamp() * 1000),
            },
            {
                "msg_id": f"msg_{start_time.strftime('%Y%m%d')}_002",
                "sender_id": "user_002",
                "sender_name": "技术支持",
                "sender_role": "support",
                "content": "验证码输错6次会有这个报错提示，请重试输入正确验证码",
                "create_time": int((base_time + timedelta(minutes=5)).timestamp() * 1000),
            },
            {
                "msg_id": f"msg_{start_time.strftime('%Y%m%d')}_003",
                "sender_id": "user_003",
                "sender_name": "客户B",
                "sender_role": "customer",
                "content": "请问借款合同签署后多久可以放款？",
                "create_time": int((base_time + timedelta(hours=2)).timestamp() * 1000),
            },
            {
                "msg_id": f"msg_{start_time.strftime('%Y%m%d')}_004",
                "sender_id": "user_004",
                "sender_name": "业务经理",
                "sender_role": "business",
                "content": "正常情况下1-3个工作日放款，具体看银行审核进度",
                "create_time": int((base_time + timedelta(hours=2, minutes=5)).timestamp() * 1000),
            },
        ]
        
        return [
            ChatMessage(
                msg_id=d["msg_id"],
                sender_id=d["sender_id"],
                sender_name=d["sender_name"],
                sender_role=d.get("sender_role", "unknown"),
                content=d["content"],
                msg_type=d.get("msg_type", "text"),
                pic_url=d.get("pic_url", ""),
                create_time=d["create_time"],
            )
            for d in mock_data
        ]
    
    async def _extract_qa(self, messages: List[ChatMessage]) -> dict:
        """提取 QA"""
        api_base_url = os.getenv("LLM_API_BASE_URL", config.llm.api_base_url)
        api_key = os.getenv("LLM_API_KEY", config.llm.api_key)
        model = os.getenv("LLM_MODEL", config.llm.model)
        
        if self.use_real_api:
            async with QAExtractor(api_base_url, api_key, model) as extractor:
                return await extractor.extract_qa(messages, "金融业务群")
        else:
            # 模拟模式：返回模拟数据
            return self._mock_extract_qa(messages)
    
    def _mock_extract_qa(self, messages: List[ChatMessage]) -> dict:
        """模拟 QA 提取"""
        qa_list = []
        fastgpt_list = []
        
        # 简单规则匹配
        i = 0
        while i < len(messages) - 1:
            msg = messages[i]
            
            is_question = (
                "?" in msg.content or "？" in msg.content or
                "提示" in msg.content or "异常" in msg.content or
                any(kw in msg.content for kw in ["怎么", "如何", "请问"])
            )
            
            if is_question and i + 1 < len(messages):
                answer_msg = messages[i + 1]
                
                # 分类判断
                tags = []
                category = "other"
                text = msg.content + " " + answer_msg.content
                
                finance_keywords = ["借款", "合同", "贷款", "银行", "放款", "签署", "验证码"]
                system_keywords = ["异常", "报错", "错误", "失败", "超时", "初始化"]
                
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
                    "id": f"qa_{msg.msg_id}",
                    "question": msg.content,
                    "answer": answer_msg.content,
                    "tags": tags,
                    "category": category,
                    "confidence": 0.85,
                    "context": {
                        "questioner": msg.sender_name,
                        "answerer": answer_msg.sender_name,
                        "source_time": datetime.fromtimestamp(msg.create_time / 1000).strftime("%Y-%m-%d %H:%M"),
                    },
                    "keywords": [],
                    "severity": "medium",
                }
                
                qa_list.append(qa)
                fastgpt_list.append({
                    "q": qa["question"],
                    "a": qa["answer"],
                    "tags": qa["tags"],
                })
                
                i += 2
            else:
                i += 1
        
        return {
            "qa_list": qa_list,
            "fastgpt_list": fastgpt_list,
            "statistics": {
                "total_count": len(qa_list),
            }
        }
    
    async def _export_knowledge_base(
        self,
        qa_data: dict,
        date: datetime,
    ) -> dict:
        """导出知识库"""
        output_dir = Path(__file__).parent / "output" / "knowledge_base" / date.strftime("%Y-%m")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exporter = KnowledgeBaseExporter(str(output_dir))
        return exporter.export_all(qa_data, f"钉钉群聊 - {date.strftime('%Y-%m-%d')}")
    
    async def _import_to_fastgpt(self, qa_data: dict) -> dict:
        """导入 FastGPT"""
        fastgpt_list = qa_data.get("fastgpt_list", [])
        
        if not fastgpt_list:
            return {"status": "no_data"}
        
        try:
            async with FastGptImporter(
                self.fastgpt_url,
                self.fastgpt_key,
                self.fastgpt_dataset,
            ) as importer:
                result = await importer.import_qa_list(fastgpt_list)
                return result
        except Exception as e:
            console.print(f"[red]FastGPT 导入失败: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    async def start_scheduler(self, hour: int = 0, minute: int = 0):
        """
        启动定时任务
        
        Args:
            hour: 每天几点执行（默认 0 点）
            minute: 每天几分执行（默认 0 分）
        """
        console.print(Panel.fit(
            f"[bold green]启动定时同步服务[/bold green]\n"
            f"执行时间: 每日 {hour:02d}:{minute:02d}\n"
            f"FastGPT: {'已配置' if self.fastgpt_key else '未配置'}",
            subtitle="Scheduler Started"
        ))
        
        self._running = True
        
        while self._running:
            now = datetime.now()
            
            # 计算下次执行时间
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            
            wait_seconds = (next_run - now).total_seconds()
            
            console.print(f"下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            console.print(f"等待 {wait_seconds/3600:.1f} 小时...")
            
            # 等待到执行时间
            await asyncio.sleep(wait_seconds)
            
            # 执行同步
            try:
                await self.sync_yesterday_data()
            except Exception as e:
                console.print(f"[red]同步出错: {e}[/red]")
            
            # 等待一分钟避免重复执行
            await asyncio.sleep(60)
    
    def stop(self):
        """停止调度器"""
        self._running = False
        console.print("[yellow]调度器已停止[/yellow]")


async def run_once():
    """执行一次同步"""
    scheduler = DingDingScheduler(
        fastgpt_key=config.fastgpt.api_key,
        fastgpt_dataset=config.fastgpt.dataset_id,
        fastgpt_url=config.fastgpt.api_url,
    )
    return await scheduler.sync_yesterday_data()


async def run_scheduler(hour: int = 0, minute: int = 0):
    """启动定时调度"""
    scheduler = DingDingScheduler(
        fastgpt_key=config.fastgpt.api_key,
        fastgpt_dataset=config.fastgpt.dataset_id,
        fastgpt_url=config.fastgpt.api_url,
    )
    await scheduler.start_scheduler(hour, minute)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="钉钉数据同步调度器")
    parser.add_argument(
        "--mode",
        choices=["once", "schedule"],
        default="once",
        help="运行模式: once=执行一次, schedule=定时调度"
    )
    parser.add_argument("--hour", type=int, default=0, help="执行小时")
    parser.add_argument("--minute", type=int, default=0, help="执行分钟")
    parser.add_argument("--real", action="store_true", help="使用真实 API")
    
    args = parser.parse_args()
    
    if args.mode == "once":
        asyncio.run(run_once())
    else:
        asyncio.run(run_scheduler(args.hour, args.minute))
