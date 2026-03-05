#!/usr/bin/env python3
"""
钉钉群聊数据同步启动脚本

使用方法：
    python start_sync.py --mode once              # 执行一次同步
    python start_sync.py --mode schedule --hour 0    # 每日 0 点执行
    python start_sync.py --mode schedule --hour 6    # 每日 6 点执行
    python start_sync.py --mode daemon                           # 后台守护进程模式
"""

import asyncio
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "skills" / "chat-to-qa" / "scripts"))

sys.path.insert(0, str(Path(__file__).parent))

from scheduler import DingDingScheduler, run_once, run_scheduler
from config import config
from rich.console import Console
from rich.panel import Panel

console = Console()


async def main():
    parser = argparse.ArgumentParser(description="钉钉群聊数据同步工具")
    
    parser.add_argument(
        "--mode",
        choices=["once", "schedule", "daemon"],
        default="once",
        help="运行模式: once=执行一次, schedule=定时调度, daemon=后台守护"
    )
    
    parser.add_argument(
        "--hour",
        type=int,
        default=0,
        help="定时执行时间（小时, 0-23)"
    )
    
    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="定时执行分钟(0-59)"
    )
    
    parser.add_argument(
        "--fastgpt-key",
        help="FastGpt API Key (可从环境变量读取)"
    )
    
    parser.add_argument(
        "--fastgpt-dataset",
        help="FastGpt Dataset ID (可从环境变量读取)"
    )
    
    parser.add_argument(
        "--real",
        action="store_true",
        help="使用真实 API (否则使用模拟数据)"
    )
    
    args = parser.parse_args()
    
    # 获取配置
    fastgpt_key = args.fastgpt_key or config.fastgpt.api_key
    fastgpt_dataset = args.fastgpt_dataset or config.fastgpt.dataset_id
    
    use_real_api = args.real
    
    
    if args.mode == "once":
        # 执行一次同步
        console.print(Panel.fit(
            "[bold green]钉钉数据同步工具[/bold green]\n"
            "模式: 单次执行",
            subtitle="DingDing Sync"
        ))
        
        await run_once(fastgpt_key, fastgpt_dataset, use_real_api=use_real_api)
        
    elif args.mode == "schedule":
        # 启动定时调度
        console.print(Panel.fit(
            "[bold green]钉钉数据同步服务[/bold green]\n"
            f"模式: 定时调度\n"
            f"执行时间: 每日 {args.hour:02d}:{args.minute:02d}",
            subtitle="DingDing Scheduler"
        ))
        
        scheduler = DingDingScheduler(
            fastgpt_key=fastgpt_key,
            fastgpt_dataset=fastgpt_dataset,
            use_real_api=use_real_api,
        )
        
        await scheduler.start(args.hour, args.minute)
        
    elif args.mode == "daemon":
        # 后台守护进程
        console.print(Panel.fit(
            "[bold green]钉钉数据同步服务[/bold green]\n"
            "模式: 后台守护进程\n"
            "将保持运行直到手动停止 (Ctrl+C)",
            subtitle="DingDing Daemon"
        ))
        
        scheduler = DingDingScheduler(
            fastgpt_key=fastgpt_key,
            fastgpt_dataset=fastgpt_dataset,
            use_real_api=use_real_api,
        )
        
        try:
                await scheduler.start(0, 0)
        except KeyboardInterrupt:
            console.print("\n[yellow]收到停止信号， 正在关闭服务...[/yellow]")


if __name__ == "__main__":
    asyncio.run(main())
