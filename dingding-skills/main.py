#!/usr/bin/env python3
"""
钉钉群聊 QA 智能分析系统（金融场景版）

功能：
1. 获取钉钉群聊数据
2. 使用 chat-to-qa Skill 从零散聊天中提取 QA
3. 自动分类标签（金融、系统、其他）
4. 导出 FastGpt 知识库格式
5. 可选：自动导入 FastGpt 知识库

使用方法：
    python main.py --action all
    python main.py --action fetch --chat-id <群聊ID>
    python main.py --action extract --chat-id <群聊ID>
    python main.py --action import --chat-id <群聊ID>
    python main.py --action fastgpt --chat-id <群聊ID>
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

# 添加 skills 路径
sys.path.insert(0, str(Path(__file__).parent / "skills" / "chat-to-qa" / "scripts"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import config
from qa_extractor import QAExtractor, ChatMessage, QAPair
from fastgpt_importer import export_to_knowledge_base, import_to_fastgpt

console = Console()


@dataclass
class MockChatMessage:
    """模拟聊天消息"""
    msg_id: str
    sender_id: str
    sender_name: str
    sender_role: str
    content: str
    msg_type: str = "text"
    pic_url: str = ""
    create_time: int = 0


class DingDingQAAnalyzer:
    """
    钉钉 QA 分析器（金融场景版）
    """

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.messages: List[ChatMessage] = []
        self.qa_data: dict = {}
        self.group_name: str = "金融业务群"

    async def fetch_messages(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ChatMessage]:
        """
        步骤 1: 获取群聊消息
        """
        console.print(Panel.fit(
            "[bold blue]步骤 1: 获取群聊数据[/bold blue]",
            subtitle="DingTalk API"
        ))

        if self.use_mock:
            messages = self._get_mock_messages()
        else:
            # TODO: 使用真实的钉钉 API
            messages = self._get_mock_messages()

        self.messages = messages
        console.print(f"\n获取到 [green]{len(messages)}[/green] 条消息")

        # 消息预览
        if messages:
            table = Table(title="消息预览（前5条）")
            table.add_column("时间", style="cyan")
            table.add_column("发送者", style="green")
            table.add_column("角色", style="yellow")
            table.add_column("内容", style="white")

            for msg in messages[:5]:
                time_str = ""
                if msg.create_time:
                    time_str = datetime.fromtimestamp(msg.create_time / 1000).strftime("%H:%M")
                
                content = msg.content[:30] + "..." if len(msg.content) > 30 else msg.content
                table.add_row(time_str, msg.sender_name, msg.sender_role, content)
            
            console.print(table)

        return messages

    def _get_mock_messages(self) -> List[ChatMessage]:
        """获取模拟消息（金融场景）"""
        mock_data = [
            {
                "msg_id": "msg_001",
                "sender_id": "user_001",
                "sender_name": "客户A",
                "sender_role": "customer",
                "content": "上海银行 签署【借款合同】提示：验证码初始化异常",
                "create_time": int(datetime.now().timestamp() * 1000) - 3600000,
            },
            {
                "msg_id": "msg_002",
                "sender_id": "user_001",
                "sender_name": "客户A",
                "sender_role": "customer",
                "content": "[图片]",
                "msg_type": "picture",
                "pic_url": "https://example.com/error.png",
                "create_time": int(datetime.now().timestamp() * 1000) - 3540000,
            },
            {
                "msg_id": "msg_003",
                "sender_id": "user_002",
                "sender_name": "技术支持",
                "sender_role": "support",
                "content": "验证码输错6次，验证码输错6次会有这个报错提示",
                "create_time": int(datetime.now().timestamp() * 1000) - 3480000,
            },
            {
                "msg_id": "msg_004",
                "sender_id": "user_002",
                "sender_name": "技术支持",
                "sender_role": "support",
                "content": "请重试，输入正确验证码就可以了",
                "create_time": int(datetime.now().timestamp() * 1000) - 3420000,
            },
            {
                "msg_id": "msg_005",
                "sender_id": "user_001",
                "sender_name": "客户A",
                "sender_role": "customer",
                "content": "好的，我试试",
                "create_time": int(datetime.now().timestamp() * 1000) - 3360000,
            },
            {
                "msg_id": "msg_006",
                "sender_id": "user_001",
                "sender_name": "客户A",
                "sender_role": "customer",
                "content": "可以了，谢谢",
                "create_time": int(datetime.now().timestamp() * 1000) - 3000000,
            },
            {
                "msg_id": "msg_007",
                "sender_id": "user_003",
                "sender_name": "客户B",
                "sender_role": "customer",
                "content": "请问借款合同签署后多久可以放款？",
                "create_time": int(datetime.now().timestamp() * 1000) - 2400000,
            },
            {
                "msg_id": "msg_008",
                "sender_id": "user_004",
                "sender_name": "业务经理",
                "sender_role": "business",
                "content": "正常情况下，合同签署完成后1-3个工作日放款",
                "create_time": int(datetime.now().timestamp() * 1000) - 2340000,
            },
            {
                "msg_id": "msg_009",
                "sender_id": "user_004",
                "sender_name": "业务经理",
                "sender_role": "business",
                "content": "具体时间取决于银行审核进度",
                "create_time": int(datetime.now().timestamp() * 1000) - 2280000,
            },
            {
                "msg_id": "msg_010",
                "sender_id": "user_005",
                "sender_name": "客户C",
                "sender_role": "customer",
                "content": "系统登录一直转圈，进不去怎么办？",
                "create_time": int(datetime.now().timestamp() * 1000) - 1800000,
            },
            {
                "msg_id": "msg_011",
                "sender_id": "user_002",
                "sender_name": "技术支持",
                "sender_role": "support",
                "content": "现在服务器在升级，预计10分钟后恢复",
                "create_time": int(datetime.now().timestamp() * 1000) - 1740000,
            },
            {
                "msg_id": "msg_012",
                "sender_id": "user_002",
                "sender_name": "技术支持",
                "sender_role": "support",
                "content": "请稍后再试",
                "create_time": int(datetime.now().timestamp() * 1000) - 1680000,
            },
            {
                "msg_id": "msg_013",
                "sender_id": "user_005",
                "sender_name": "客户C",
                "sender_role": "customer",
                "content": "可以了",
                "create_time": int(datetime.now().timestamp() * 1000) - 1200000,
            },
        ]

        messages = []
        for data in mock_data:
            messages.append(ChatMessage(
                msg_id=data["msg_id"],
                sender_id=data["sender_id"],
                sender_name=data["sender_name"],
                sender_role=data.get("sender_role", "unknown"),
                content=data["content"],
                msg_type=data.get("msg_type", "text"),
                pic_url=data.get("pic_url", ""),
                create_time=data["create_time"],
            ))
        
        return messages

    async def extract_qa(self) -> dict:
        """
        步骤 2: 使用 chat-to-qa Skill 提取 QA
        """
        console.print(Panel.fit(
            "[bold blue]步骤 2: 使用 Skill 提取 QA[/bold blue]",
            subtitle="chat-to-qa Skill (金融场景)"
        ))

        if not self.messages:
            console.print("[yellow]没有消息数据，请先获取消息[/yellow]")
            return {}

        # 从环境变量获取 API 配置
        api_base_url = os.getenv("LLM_API_BASE_URL", config.llm.api_base_url)
        api_key = os.getenv("LLM_API_KEY", config.llm.api_key)
        model = os.getenv("LLM_MODEL", config.llm.model)

        if self.use_mock:
            qa_data = await self._mock_extract_qa()
        else:
            async with QAExtractor(api_base_url, api_key, model) as extractor:
                qa_data = await extractor.extract_qa(self.messages, self.group_name)

        self.qa_data = qa_data

        # 显示统计
        stats = qa_data.get("statistics", {})
        console.print(f"\n提取到 [green]{stats.get('total_count', 0)}[/green] 个 QA 对")

        # 分类统计
        by_category = stats.get("by_category", {})
        if by_category:
            table = Table(title="分类统计")
            table.add_column("分类", style="cyan")
            table.add_column("数量", style="green")
            table.add_column("占比", style="yellow")

            total = stats.get("total_count", 1)
            category_names = {
                "finance": "金融",
                "system": "系统",
                "other": "其他",
            }
            for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
                table.add_row(
                    category_names.get(category, category),
                    str(count),
                    f"{count/total*100:.1f}%"
                )
            console.print(table)

        # QA 预览
        qa_list = qa_data.get("qa_list", [])
        if qa_list:
            console.print("\n[bold]QA 预览（前3条）:[/bold]")
            for i, qa in enumerate(qa_list[:3], 1):
                tags = ", ".join(qa.get("tags", []))
                console.print(f"\n[cyan]Q{i}: {qa['question'][:50]}...[/cyan]")
                console.print(f"[green]A: {qa['answer'][:60]}...[/green]")
                console.print(f"[yellow]标签: {tags} | 分类: {qa['category']}[/yellow]")

        return qa_data

    async def _mock_extract_qa(self) -> dict:
        """模拟 QA 提取（金融场景）"""
        qa_list = []
        fastgpt_list = []
        
        # 基于 mock 消息手动构建 QA
        qa_data = [
            {
                "id": "qa_001",
                "question": "上海银行签署借款合同提示：验证码初始化异常怎么办？",
                "answer": "验证码输错6次后会出现此报错提示。请重新尝试，输入正确的验证码即可正常完成签署。",
                "tags": ["金融", "系统"],
                "category": "finance",
                "confidence": 0.95,
                "context": {
                    "questioner": "客户A",
                    "answerer": "技术支持",
                    "group_name": self.group_name,
                    "has_image": True,
                    "image_desc": "错误提示截图",
                    "source_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                },
                "keywords": ["借款合同", "验证码", "上海银行"],
                "severity": "medium",
            },
            {
                "id": "qa_002",
                "question": "借款合同签署后多久可以放款？",
                "answer": "正常情况下，合同签署完成后1-3个工作日放款，具体时间取决于银行审核进度。",
                "tags": ["金融"],
                "category": "finance",
                "confidence": 0.98,
                "context": {
                    "questioner": "客户B",
                    "answerer": "业务经理",
                    "group_name": self.group_name,
                    "has_image": False,
                    "source_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                },
                "keywords": ["借款合同", "放款", "银行审核"],
                "severity": "low",
            },
            {
                "id": "qa_003",
                "question": "系统登录一直转圈进不去怎么办？",
                "answer": "可能是服务器正在升级维护，请等待几分钟后重新尝试登录。如问题持续，请联系技术支持。",
                "tags": ["系统"],
                "category": "system",
                "confidence": 0.90,
                "context": {
                    "questioner": "客户C",
                    "answerer": "技术支持",
                    "group_name": self.group_name,
                    "has_image": False,
                    "source_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                },
                "keywords": ["登录", "系统", "服务器"],
                "severity": "high",
            },
        ]

        for qa in qa_data:
            qa_list.append(qa)
            fastgpt_list.append({
                "q": qa["question"],
                "a": qa["answer"],
                "tags": qa["tags"],
            })

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

    async def export_knowledge_base(self) -> dict:
        """
        步骤 3: 导出知识库
        """
        console.print(Panel.fit(
            "[bold blue]步骤 3: 导出知识库[/bold blue]",
            subtitle="Knowledge Base Export"
        ))

        if not self.qa_data:
            console.print("[yellow]没有 QA 数据，请先提取 QA[/yellow]")
            return {}

        output_dir = Path(__file__).parent / "output" / "knowledge_base"
        exported_files = await export_to_knowledge_base(
            self.qa_data,
            output_dir=str(output_dir),
            source=f"钉钉群聊 - {self.group_name}",
        )

        console.print(f"\n[green]成功导出知识库！[/green]")
        console.print(f"QA 总数: {self.qa_data.get('statistics', {}).get('total_count', 0)} 条")

        console.print("\n导出文件:")
        for format_type, file_path in exported_files.items():
            console.print(f"  📄 [{format_type}] {file_path}")

        return exported_files

    async def import_to_fastgpt(
        self,
        api_key: str,
        dataset_id: str,
        api_base_url: str = "https://api.fastgpt.in",
    ) -> dict:
        """
        步骤 4: 导入 FastGpt 知识库
        """
        console.print(Panel.fit(
            "[bold blue]步骤 4: 导入 FastGpt 知识库[/bold blue]",
            subtitle="FastGpt Integration"
        ))

        if not self.qa_data:
            console.print("[yellow]没有 QA 数据，请先提取 QA[/yellow]")
            return {}

        result = await import_to_fastgpt(
            self.qa_data,
            api_key=api_key,
            dataset_id=dataset_id,
            api_base_url=api_base_url,
        )

        console.print(f"\n[green]导入完成！[/green]")
        console.print(f"成功: {result.get('imported', 0)} 条")
        console.print(f"失败: {result.get('failed', 0)} 条")

        if result.get("errors"):
            console.print("\n[red]错误信息:[/red]")
            for err in result["errors"]:
                console.print(f"  批次 {err['batch']}: {err['error']}")

        return result

    async def run_full_pipeline(self, chat_id: str = "all"):
        """运行完整流程"""
        console.print(Panel.fit(
            "[bold green]钉钉群聊 QA 智能分析系统[/bold green]\n"
            "金融场景版 - 使用 chat-to-qa Skill",
            subtitle="DingDing QA Analyzer"
        ))

        try:
            # 1. 获取消息
            await self.fetch_messages(chat_id)

            # 2. 提取 QA
            await self.extract_qa()

            # 3. 导出知识库
            await self.export_knowledge_base()

            console.print(Panel.fit(
                "[bold green]✅ 分析完成！[/bold green]\n"
                "已生成 FastGpt 导入格式文件",
                subtitle="可使用 fastgpt_import.json 导入到 FastGpt"
            ))

        except Exception as e:
            console.print(Panel.fit(
                f"[bold red]❌ 分析失败[/bold red]\n{e}",
                subtitle="请检查错误信息"
            ))
            raise


async def main():
    parser = argparse.ArgumentParser(
        description="钉钉群聊 QA 智能分析系统（金融场景版）",
    )

    parser.add_argument(
        "--action",
        choices=["fetch", "extract", "export", "fastgpt", "all"],
        default="all",
        help="执行的操作",
    )

    parser.add_argument(
        "--chat-id",
        default="all",
        help="群聊 ID",
    )

    parser.add_argument(
        "--use-mock",
        action="store_true",
        default=True,
        help="使用模拟数据（默认开启）",
    )

    parser.add_argument(
        "--real",
        action="store_true",
        help="使用真实 API（需配置凭据）",
    )

    # FastGpt 配置
    parser.add_argument(
        "--fastgpt-key",
        help="FastGpt API Key",
    )

    parser.add_argument(
        "--fastgpt-dataset",
        help="FastGpt Dataset ID",
    )

    parser.add_argument(
        "--fastgpt-url",
        default="https://api.fastgpt.in",
        help="FastGpt API URL",
    )

    args = parser.parse_args()
    use_mock = not args.real

    analyzer = DingDingQAAnalyzer(use_mock=use_mock)

    if args.action == "fetch":
        await analyzer.fetch_messages(args.chat_id)
    elif args.action == "extract":
        await analyzer.fetch_messages(args.chat_id)
        await analyzer.extract_qa()
    elif args.action == "export":
        await analyzer.fetch_messages(args.chat_id)
        await analyzer.extract_qa()
        await analyzer.export_knowledge_base()
    elif args.action == "fastgpt":
        if not args.fastgpt_key or not args.fastgpt_dataset:
            console.print("[red]请提供 FastGpt API Key 和 Dataset ID[/red]")
            return
        await analyzer.fetch_messages(args.chat_id)
        await analyzer.extract_qa()
        await analyzer.import_to_fastgpt(
            args.fastgpt_key,
            args.fastgpt_dataset,
            args.fastgpt_url,
        )
    elif args.action == "all":
        await analyzer.run_full_pipeline(args.chat_id)


if __name__ == "__main__":
    asyncio.run(main())
