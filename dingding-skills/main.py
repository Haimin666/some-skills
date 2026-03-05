#!/usr/bin/env python3
"""
钉钉群聊 QA 智能分析系统

功能：
1. 获取钉钉群聊数据
2. 使用 chat-to-qa Skill 从零散聊天中提取 QA
3. 自动分类标签
4. 导入知识库

使用方法：
    python main.py --action all
    python main.py --action fetch --chat-id <群聊ID>
    python main.py --action extract --chat-id <群聊ID>
    python main.py --action import --chat-id <群聊ID>
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

# 添加 skills 路径
sys.path.insert(0, str(Path(__file__).parent / "skills" / "chat-to-qa" / "scripts"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import config
from api.dingtalk_api import DingTalkAPI, MockDingTalkAPI, ChatMessage
from qa_extractor import QAExtractor, QAPair
from knowledge_base_importer import KnowledgeBaseImporter

console = Console()


class DingDingQAAnalyzer:
    """
    钉钉 QA 分析器

    使用 chat-to-qa Skill 从群聊中提取 QA
    """

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.messages: List[ChatMessage] = []
        self.qa_data: dict = {}

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

        client = MockDingTalkAPI() if self.use_mock else DingTalkAPI()

        try:
            async with client:
                messages = await client.get_chat_messages(
                    chat_id=chat_id,
                    start_time=start_time,
                    end_time=end_time,
                )

            self.messages = messages
            console.print(f"\n获取到 [green]{len(messages)}[/green] 条消息")

            # 消息预览
            if messages:
                table = Table(title="消息预览（前5条）")
                table.add_column("时间", style="cyan")
                table.add_column("发送者", style="green")
                table.add_column("内容", style="white")

                for msg in messages[:5]:
                    table.add_row(
                        msg.timestamp.strftime("%H:%M"),
                        msg.sender_name,
                        msg.content[:40] + "..." if len(msg.content) > 40 else msg.content,
                    )
                console.print(table)

            return messages

        except Exception as e:
            console.print(f"[red]获取消息失败: {e}[/red]")
            raise

    async def extract_qa(self) -> dict:
        """
        步骤 2: 使用 chat-to-qa Skill 提取 QA
        """
        console.print(Panel.fit(
            "[bold blue]步骤 2: 使用 Skill 提取 QA[/bold blue]",
            subtitle="chat-to-qa Skill"
        ))

        if not self.messages:
            console.print("[yellow]没有消息数据，请先获取消息[/yellow]")
            return {}

        # 从环境变量获取 API 配置
        api_base_url = os.getenv("LLM_API_BASE_URL", config.llm.api_base_url)
        api_key = os.getenv("LLM_API_KEY", config.llm.api_key)
        model = os.getenv("LLM_MODEL", config.llm.model)

        if self.use_mock:
            # 使用模拟数据
            qa_data = await self._mock_extract_qa()
        else:
            # 使用真实的 LLM API
            async with QAExtractor(api_base_url, api_key, model) as extractor:
                qa_data = await extractor.extract_qa(self.messages)

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
            for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
                category_names = {
                    "system_bug": "系统Bug",
                    "data_issue": "数据问题",
                    "business_issue": "业务问题",
                    "user_issue": "用户问题",
                    "feature_request": "功能需求",
                    "other": "其他",
                }
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
                console.print(f"\n[cyan]Q{i}: {qa['question'][:50]}...[/cyan]")
                console.print(f"[green]A: {qa['answer'][:80]}...[/green]")
                console.print(f"[yellow]分类: {qa['category_name']} | 严重级别: {qa['severity']}[/yellow]")

        return qa_data

    async def _mock_extract_qa(self) -> dict:
        """模拟 QA 提取（用于测试）"""
        qa_list = []

        # 简单规则匹配
        i = 0
        while i < len(self.messages) - 1:
            msg = self.messages[i]
            content = msg.content

            # 检测问题
            is_question = (
                "?" in content or "？" in content or
                any(kw in content for kw in ["怎么", "如何", "为什么", "能不能", "可以", "求助", "报错", "错误"])
            )

            if is_question and i + 1 < len(self.messages):
                # 找答案
                answer_msg = None
                for j in range(i + 1, min(i + 5, len(self.messages))):
                    next_content = self.messages[j].content
                    if len(next_content) > 10 and not any(kw in next_content for kw in ["?", "？", "哈哈", "嗯嗯"]):
                        answer_msg = self.messages[j]
                        break

                if answer_msg:
                    # 分类判断
                    category = "other"
                    severity = "medium"

                    text = content + " " + answer_msg.content
                    if any(kw in text for kw in ["报错", "崩溃", "异常", "bug", "500", "404"]):
                        category = "system_bug"
                        severity = "high"
                    elif any(kw in text for kw in ["数据", "不一致", "缺失"]):
                        category = "data_issue"
                    elif any(kw in text for kw in ["流程", "审批", "规则"]):
                        category = "business_issue"
                    elif any(kw in text for kw in ["怎么", "如何", "操作"]):
                        category = "user_issue"
                        severity = "low"
                    elif any(kw in text for kw in ["建议", "希望", "新增"]):
                        category = "feature_request"
                        severity = "low"

                    category_names = {
                        "system_bug": "系统Bug",
                        "data_issue": "数据问题",
                        "business_issue": "业务问题",
                        "user_issue": "用户问题",
                        "feature_request": "功能需求",
                        "other": "其他",
                    }

                    qa_list.append({
                        "id": f"qa_{len(qa_list):04d}",
                        "question": content,
                        "answer": answer_msg.content,
                        "category": category,
                        "category_name": category_names.get(category, "其他"),
                        "confidence": 0.75,
                        "context": f"提问者: {msg.sender_name}",
                        "source_msg_ids": [msg.msg_id, answer_msg.msg_id],
                        "keywords": [],
                        "severity": severity,
                    })
                    i += 2
                else:
                    i += 1
            else:
                i += 1

        # 统计
        from collections import Counter
        category_counts = Counter([qa["category"] for qa in qa_list])
        severity_counts = Counter([qa["severity"] for qa in qa_list])

        return {
            "qa_list": qa_list,
            "statistics": {
                "total_count": len(qa_list),
                "by_category": dict(category_counts),
                "by_severity": dict(severity_counts),
            }
        }

    async def import_to_knowledge_base(self) -> dict:
        """
        步骤 3: 导入知识库
        """
        console.print(Panel.fit(
            "[bold blue]步骤 3: 导入知识库[/bold blue]",
            subtitle="Knowledge Base"
        ))

        if not self.qa_data:
            console.print("[yellow]没有 QA 数据，请先提取 QA[/yellow]")
            return {}

        importer = KnowledgeBaseImporter(
            output_dir=str(Path(__file__).parent / "output" / "knowledge_base")
        )

        exported_files = importer.import_qa_data(self.qa_data, source="钉钉群聊")

        console.print(f"\n[green]成功导入知识库！[/green]")
        console.print(f"QA 总数: {self.qa_data.get('statistics', {}).get('total_count', 0)} 条")

        console.print("\n导出文件:")
        for format_type, file_path in exported_files.items():
            console.print(f"  📄 [{format_type}] {file_path}")

        return exported_files

    async def run_full_pipeline(self, chat_id: str = "all"):
        """运行完整流程"""
        console.print(Panel.fit(
            "[bold green]钉钉群聊 QA 智能分析系统[/bold green]\n"
            "使用 chat-to-qa Skill 从零散聊天中提取 QA",
            subtitle="DingDing QA Analyzer"
        ))

        try:
            # 1. 获取消息
            await self.fetch_messages(chat_id)

            # 2. 提取 QA
            await self.extract_qa()

            # 3. 导入知识库
            await self.import_to_knowledge_base()

            console.print(Panel.fit(
                "[bold green]✅ 分析完成！[/bold green]",
                subtitle="所有步骤执行成功"
            ))

        except Exception as e:
            console.print(Panel.fit(
                f"[bold red]❌ 分析失败[/bold red]\n{e}",
                subtitle="请检查错误信息"
            ))
            raise


async def main():
    parser = argparse.ArgumentParser(
        description="钉钉群聊 QA 智能分析系统",
    )

    parser.add_argument(
        "--action",
        choices=["fetch", "extract", "import", "all"],
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

    args = parser.parse_args()
    use_mock = not args.real

    analyzer = DingDingQAAnalyzer(use_mock=use_mock)

    if args.action == "fetch":
        await analyzer.fetch_messages(args.chat_id)
    elif args.action == "extract":
        await analyzer.fetch_messages(args.chat_id)
        await analyzer.extract_qa()
    elif args.action == "import":
        await analyzer.fetch_messages(args.chat_id)
        await analyzer.extract_qa()
        await analyzer.import_to_knowledge_base()
    elif args.action == "all":
        await analyzer.run_full_pipeline(args.chat_id)


if __name__ == "__main__":
    asyncio.run(main())
