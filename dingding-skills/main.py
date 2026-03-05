#!/usr/bin/env python3
"""
钉钉群聊 QA 智能分析系统 - 主程序

功能：
1. 获取钉钉群聊数据
2. 大模型生成 QA
3. QA 分类并导入知识库
4. 问题发现与分析

使用方法：
    python main.py --action all --chat-id <群聊ID>
    python main.py --action fetch --chat-id <群聊ID>
    python main.py --action generate --chat-id <群聊ID>
    python main.py --action classify --chat-id <群聊ID>
    python main.py --action analyze --chat-id <群聊ID>
"""

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import config, get_output_path
from api.dingtalk_api import DingTalkAPI, MockDingTalkAPI, ChatMessage
from core.qa_generator import QAGenerator, MockQAGenerator, QAPair
from core.qa_classifier import QAClassifier, ClassifiedQA
from core.problem_analyzer import ProblemAnalyzer, generate_report_file
from core.knowledge_base import KnowledgeBase, create_knowledge_base

# 初始化 Rich Console
console = Console()


class DingDingQAAnalyzer:
    """
    钉钉 QA 分析器
    
    整合所有模块，提供完整的分析流程
    """
    
    def __init__(self, use_mock: bool = True):
        """
        初始化分析器
        
        Args:
            use_mock: 是否使用模拟数据（用于测试）
        """
        self.use_mock = use_mock
        self.messages: List[ChatMessage] = []
        self.qa_pairs: List[QAPair] = []
        self.classified_qa: List[ClassifiedQA] = []
    
    async def fetch_messages(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ChatMessage]:
        """
        步骤 1: 获取群聊消息
        
        Args:
            chat_id: 群聊 ID
            start_time: 开始时间
            end_time: 结束时间
        """
        console.print(Panel.fit(
            "[bold blue]步骤 1: 获取群聊数据[/bold blue]",
            subtitle="钉钉 API"
        ))
        
        # 创建客户端
        if self.use_mock:
            client = MockDingTalkAPI()
        else:
            client = DingTalkAPI()
        
        try:
            async with client:
                messages = await client.get_chat_messages(
                    chat_id=chat_id,
                    start_time=start_time,
                    end_time=end_time,
                )
            
            self.messages = messages
            
            # 显示统计
            console.print(f"\n获取到 [green]{len(messages)}[/green] 条消息")
            
            # 显示消息预览
            if messages:
                table = Table(title="消息预览（前5条）")
                table.add_column("时间", style="cyan")
                table.add_column("发送者", style="green")
                table.add_column("内容", style="white")
                
                for msg in messages[:5]:
                    table.add_row(
                        msg.timestamp.strftime("%H:%M"),
                        msg.sender_name,
                        msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                    )
                
                console.print(table)
            
            return messages
        
        except Exception as e:
            console.print(f"[red]获取消息失败: {e}[/red]")
            raise
    
    async def generate_qa(self) -> List[QAPair]:
        """
        步骤 2: 生成 QA 对
        """
        console.print(Panel.fit(
            "[bold blue]步骤 2: 大模型生成 QA[/bold blue]",
            subtitle="AI Skills"
        ))
        
        if not self.messages:
            console.print("[yellow]没有消息数据，请先获取消息[/yellow]")
            return []
        
        # 创建生成器
        if self.use_mock:
            generator = MockQAGenerator()
        else:
            generator = QAGenerator()
        
        try:
            async with generator:
                qa_pairs = await generator.generate_qa(self.messages)
            
            self.qa_pairs = qa_pairs
            
            # 显示统计
            console.print(f"\n生成 [green]{len(qa_pairs)}[/green] 个 QA 对")
            
            # 显示预览
            if qa_pairs:
                table = Table(title="QA 预览（前5条）")
                table.add_column("问题", style="yellow")
                table.add_column("答案", style="green")
                
                for qa in qa_pairs[:5]:
                    table.add_row(
                        qa.question[:40] + "..." if len(qa.question) > 40 else qa.question,
                        qa.answer[:40] + "..." if len(qa.answer) > 40 else qa.answer,
                    )
                
                console.print(table)
            
            return qa_pairs
        
        except Exception as e:
            console.print(f"[red]生成 QA 失败: {e}[/red]")
            raise
    
    async def classify_qa(self) -> List[ClassifiedQA]:
        """
        步骤 3: 分类 QA
        """
        console.print(Panel.fit(
            "[bold blue]步骤 3: QA 分类[/bold blue]",
            subtitle="智能分类"
        ))
        
        if not self.qa_pairs:
            console.print("[yellow]没有 QA 数据，请先生成 QA[/yellow]")
            return []
        
        classifier = QAClassifier()
        
        try:
            async with classifier:
                classified_qa = await classifier.classify_batch(
                    self.qa_pairs,
                    use_llm=not self.use_mock,
                )
            
            self.classified_qa = classified_qa
            
            # 显示分类统计
            from collections import Counter
            category_counts = Counter([cq.category for cq in classified_qa])
            
            table = Table(title="分类统计")
            table.add_column("分类", style="cyan")
            table.add_column("数量", style="green")
            table.add_column("占比", style="yellow")
            
            total = len(classified_qa)
            for category, count in category_counts.most_common():
                category_name = config.knowledge_base.categories.get(category, category)
                percentage = f"{count/total*100:.1f}%"
                table.add_row(category_name, str(count), percentage)
            
            console.print(table)
            
            return classified_qa
        
        except Exception as e:
            console.print(f"[red]分类失败: {e}[/red]")
            raise
    
    async def import_to_knowledge_base(self) -> dict:
        """
        步骤 4: 导入知识库
        """
        console.print(Panel.fit(
            "[bold blue]步骤 4: 导入知识库[/bold blue]",
            subtitle="Knowledge Base"
        ))
        
        if not self.classified_qa:
            console.print("[yellow]没有分类数据，请先进行分类[/yellow]")
            return {}
        
        result = create_knowledge_base(
            self.classified_qa,
            export_format="all",
        )
        
        # 显示结果
        console.print(f"\n[green]成功导入知识库！[/green]")
        console.print(f"导入数量: {result['statistics']['total_count']} 条")
        console.print(f"平均置信度: {result['statistics']['avg_confidence']:.2%}")
        
        console.print("\n导出文件:")
        for file_path in result["exported_files"]:
            console.print(f"  📄 {file_path}")
        
        return result
    
    async def analyze_problems(self) -> dict:
        """
        步骤 5: 问题分析
        """
        console.print(Panel.fit(
            "[bold blue]步骤 5: 问题分析[/bold blue]",
            subtitle="Problem Discovery"
        ))
        
        if not self.classified_qa:
            console.print("[yellow]没有分类数据，请先进行分类[/yellow]")
            return {}
        
        analyzer = ProblemAnalyzer()
        report = analyzer.analyze(self.classified_qa)
        
        # 保存报告
        report_path = get_output_path("analysis_report.json")
        generate_report_file(report, report_path)
        
        # 也生成 Markdown 报告
        md_path = get_output_path("analysis_report.md")
        generate_report_file(report, md_path, format="markdown")
        
        # 显示报告摘要
        console.print(f"\n[bold]问题分析报告[/bold]")
        console.print(f"总问题数: {report.summary.total_count}")
        
        # 分类饼图数据
        console.print("\n分类分布:")
        for category, count in report.summary.by_category.items():
            category_name = config.knowledge_base.categories.get(category, category)
            bar = "█" * int(count / report.summary.total_count * 20)
            console.print(f"  {category_name}: {bar} {count}")
        
        # 高优先级问题
        if report.summary.high_priority_items:
            console.print(f"\n[red]高优先级问题: {len(report.summary.high_priority_items)} 个[/red]")
            for item in report.summary.high_priority_items[:3]:
                console.print(f"  ⚠️ {item['question'][:60]}...")
        
        # 建议
        console.print("\n[bold]建议:[/bold]")
        for i, rec in enumerate(report.recommendations[:5], 1):
            console.print(f"  {i}. {rec}")
        
        console.print(f"\n报告已保存:")
        console.print(f"  📄 {report_path}")
        console.print(f"  📄 {md_path}")
        
        return {
            "report": report,
            "report_path": str(report_path),
        }
    
    async def run_full_pipeline(
        self,
        chat_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        """
        运行完整流程
        """
        console.print(Panel.fit(
            "[bold green]钉钉群聊 QA 智能分析系统[/bold green]\n"
            "从群聊数据到问题发现的全流程",
            subtitle="DingDing QA Analyzer"
        ))
        
        try:
            # 1. 获取消息
            await self.fetch_messages(chat_id, start_time, end_time)
            
            # 2. 生成 QA
            await self.generate_qa()
            
            # 3. 分类 QA
            await self.classify_qa()
            
            # 4. 导入知识库
            await self.import_to_knowledge_base()
            
            # 5. 问题分析
            await self.analyze_problems()
            
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
    """主函数"""
    parser = argparse.ArgumentParser(
        description="钉钉群聊 QA 智能分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--action",
        choices=["fetch", "generate", "classify", "import", "analyze", "all"],
        default="all",
        help="执行的操作: fetch=获取消息, generate=生成QA, classify=分类, import=导入知识库, analyze=问题分析, all=完整流程",
    )
    
    parser.add_argument(
        "--chat-id",
        default="all",
        help="群聊 ID（默认获取所有）",
    )
    
    parser.add_argument(
        "--start-time",
        help="开始时间（格式: YYYY-MM-DD）",
    )
    
    parser.add_argument(
        "--end-time",
        help="结束时间（格式: YYYY-MM-DD）",
    )
    
    parser.add_argument(
        "--use-mock",
        action="store_true",
        default=True,
        help="使用模拟数据（用于测试，默认开启）",
    )
    
    parser.add_argument(
        "--real",
        action="store_true",
        help="使用真实钉钉 API（需要配置正确的凭据）",
    )
    
    args = parser.parse_args()
    
    # 解析时间参数
    start_time = None
    end_time = None
    
    if args.start_time:
        start_time = datetime.strptime(args.start_time, "%Y-%m-%d")
    if args.end_time:
        end_time = datetime.strptime(args.end_time, "%Y-%m-%d")
    
    # 判断是否使用真实 API
    use_mock = not args.real
    
    # 创建分析器
    analyzer = DingDingQAAnalyzer(use_mock=use_mock)
    
    # 执行操作
    if args.action == "fetch":
        await analyzer.fetch_messages(args.chat_id, start_time, end_time)
    
    elif args.action == "generate":
        await analyzer.fetch_messages(args.chat_id, start_time, end_time)
        await analyzer.generate_qa()
    
    elif args.action == "classify":
        await analyzer.fetch_messages(args.chat_id, start_time, end_time)
        await analyzer.generate_qa()
        await analyzer.classify_qa()
    
    elif args.action == "import":
        await analyzer.fetch_messages(args.chat_id, start_time, end_time)
        await analyzer.generate_qa()
        await analyzer.classify_qa()
        await analyzer.import_to_knowledge_base()
    
    elif args.action == "analyze":
        await analyzer.fetch_messages(args.chat_id, start_time, end_time)
        await analyzer.generate_qa()
        await analyzer.classify_qa()
        await analyzer.analyze_problems()
    
    elif args.action == "all":
        await analyzer.run_full_pipeline(args.chat_id, start_time, end_time)


if __name__ == "__main__":
    asyncio.run(main())
