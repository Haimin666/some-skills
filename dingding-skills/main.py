#!/usr/bin/env python3
"""
钉钉群聊 QA 提取工具

功能：
1. 从钉钉获取群聊数据
2. 使用 chat-to-qa Skill 提取 QA
3. 导出 CSV 文件（第一列 q，第二列 a）

使用方法：
    python main.py                    # 使用模拟数据测试
    python main.py --real              # 使用真实钉钉 API
    python main.py --output my_qa.csv  # 指定输出文件
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加 skills 路径
sys.path.insert(0, str(Path(__file__).parent / "skills" / "chat-to-qa"))

from qa_extractor import (
    QAExtractor, 
    ChatMessage, 
    QAPair, 
    export_to_csv,
    extract_qa_csv,
)

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def get_mock_messages() -> List[ChatMessage]:
    """获取模拟消息（测试用）"""
    return [
        ChatMessage(
            msg_id="msg_001",
            sender_id="user_001",
            sender_name="客户A",
            sender_role="customer",
            content="上海银行 签署【借款合同】提示：验证码初始化异常",
            create_time=int(datetime.now().timestamp() * 1000) - 3600000,
        ),
        ChatMessage(
            msg_id="msg_002",
            sender_id="user_002",
            sender_name="技术支持",
            sender_role="support",
            content="验证码输错6次会有这个报错提示，请重试输入正确验证码",
            create_time=int(datetime.now().timestamp() * 1000) - 3500000,
        ),
        ChatMessage(
            msg_id="msg_003",
            sender_id="user_001",
            sender_name="客户A",
            sender_role="customer",
            content="好的，我试试",
            create_time=int(datetime.now().timestamp() * 1000) - 3400000,
        ),
        ChatMessage(
            msg_id="msg_004",
            sender_id="user_001",
            sender_name="客户A",
            sender_role="customer",
            content="可以了，谢谢",
            create_time=int(datetime.now().timestamp() * 1000) - 3000000,
        ),
        ChatMessage(
            msg_id="msg_005",
            sender_id="user_003",
            sender_name="客户B",
            sender_role="customer",
            content="请问借款合同签署后多久可以放款？",
            create_time=int(datetime.now().timestamp() * 1000) - 2400000,
        ),
        ChatMessage(
            msg_id="msg_006",
            sender_id="user_004",
            sender_name="业务经理",
            sender_role="business",
            content="正常情况下，合同签署完成后1-3个工作日放款",
            create_time=int(datetime.now().timestamp() * 1000) - 2300000,
        ),
        ChatMessage(
            msg_id="msg_007",
            sender_id="user_004",
            sender_name="业务经理",
            sender_role="business",
            content="具体时间取决于银行审核进度",
            create_time=int(datetime.now().timestamp() * 1000) - 2200000,
        ),
        ChatMessage(
            msg_id="msg_008",
            sender_id="user_005",
            sender_name="客户C",
            sender_role="customer",
            content="系统登录一直转圈，进不去怎么办？",
            create_time=int(datetime.now().timestamp() * 1000) - 1800000,
        ),
        ChatMessage(
            msg_id="msg_009",
            sender_id="user_002",
            sender_name="技术支持",
            sender_role="support",
            content="现在服务器在升级，预计10分钟后恢复，请稍后再试",
            create_time=int(datetime.now().timestamp() * 1000) - 1700000,
        ),
    ]


async def fetch_messages_from_dingtalk() -> List[ChatMessage]:
    """从钉钉获取消息（需要用户实现）"""
    # TODO: 用户需要在这里实现真实的钉钉 API 调用
    # 参考钉钉 API 文档实现
    console.print("[yellow]请实现钉钉 API 调用，目前返回模拟数据[/yellow]")
    return get_mock_messages()


async def main():
    parser = argparse.ArgumentParser(
        description="钉钉群聊 QA 提取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python main.py                          # 使用模拟数据
    python main.py --real                   # 使用真实钉钉 API
    python main.py --output qa_20240115.csv # 指定输出文件
        """,
    )
    
    parser.add_argument(
        "--real",
        action="store_true",
        help="使用真实钉钉 API（需先实现 API 调用）",
    )
    
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出 CSV 文件路径（默认: output/qa_YYYYMMDD_HHMMSS.csv）",
    )
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold green]钉钉群聊 QA 提取工具[/bold green]\n"
        "基于 chat-to-qa Skill 提取问答对\n"
        "输出格式: CSV (q, a 两列)",
        subtitle="QA Extractor"
    ))
    
    # 1. 获取消息
    console.print("\n[bold blue]步骤 1: 获取群聊消息[/bold blue]")
    
    if args.real:
        messages = await fetch_messages_from_dingtalk()
    else:
        messages = get_mock_messages()
    
    console.print(f"获取到 [green]{len(messages)}[/green] 条消息")
    
    # 显示消息预览
    if messages:
        table = Table(title="消息预览（前5条）")
        table.add_column("发送者", style="green")
        table.add_column("内容", style="white")
        
        for msg in messages[:5]:
            content = msg.content[:40] + "..." if len(msg.content) > 40 else msg.content
            table.add_row(msg.sender_name, content)
        
        console.print(table)
    
    # 2. 提取 QA
    console.print("\n[bold blue]步骤 2: 提取 QA 对[/bold blue]")
    
    extractor = QAExtractor()
    qa_pairs = extractor.extract_from_messages(messages)
    
    console.print(f"提取到 [green]{len(qa_pairs)}[/green] 个 QA 对")
    
    # 显示 QA 预览
    if qa_pairs:
        table = Table(title="QA 预览")
        table.add_column("Q", style="cyan")
        table.add_column("A", style="green")
        table.add_column("标签", style="yellow")
        
        for qa in qa_pairs:
            q = qa.question[:35] + "..." if len(qa.question) > 35 else qa.question
            a = qa.answer[:35] + "..." if len(qa.answer) > 35 else qa.answer
            tags = ", ".join(qa.tags)
            table.add_row(q, a, tags)
        
        console.print(table)
    
    # 3. 导出 CSV
    console.print("\n[bold blue]步骤 3: 导出 CSV[/bold blue]")
    
    if args.output:
        output_path = args.output
    else:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(output_dir / f"qa_{timestamp}.csv")
    
    csv_path = export_to_csv(qa_pairs, output_path)
    
    console.print(Panel.fit(
        f"[bold green]✅ 完成！[/bold green]\n"
        f"QA 数量: {len(qa_pairs)} 条\n"
        f"CSV 文件: {csv_path}",
        subtitle="导出完成"
    ))
    
    # 显示 CSV 内容预览
    console.print("\n[bold]CSV 内容预览:[/bold]")
    console.print("[dim]q,a[/dim]")
    for qa in qa_pairs[:3]:
        q_preview = qa.question[:30].replace(",", "，")
        a_preview = qa.answer[:30].replace(",", "，")
        console.print(f"[dim]{q_preview}...,{a_preview}...[/dim]")
    
    if len(qa_pairs) > 3:
        console.print(f"[dim]... 共 {len(qa_pairs)} 条[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
