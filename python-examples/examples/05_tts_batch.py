"""
示例 05: TTS 批量处理与高级功能

本示例展示：
1. 批量语音合成优化
2. 语音合成队列管理
3. 并发控制
4. 音频文件管理
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "batch"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TTSRequest:
    """TTS 请求"""
    id: str
    text: str
    voice: str = "tongtong"
    speed: float = 1.0
    output_path: Optional[str] = None


@dataclass
class TTSResult:
    """TTS 结果"""
    request: TTSRequest
    success: bool
    audio_size: int = 0
    error: Optional[str] = None
    duration: float = 0.0


class TTSBatchProcessor:
    """
    TTS 批量处理器

    功能：
    - 批量处理多个 TTS 请求
    - 并发控制
    - 进度跟踪
    - 错误处理与重试
    """

    def __init__(
        self,
        max_concurrent: int = 3,
        retry_count: int = 2,
    ):
        self.max_concurrent = max_concurrent
        self.retry_count = retry_count
        self.client: Optional[AIClient] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    async def initialize(self):
        """初始化"""
        self.client = AIClient()
        await self.client._init_session()
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

    async def close(self):
        """关闭连接"""
        if self.client:
            await self.client.close()

    async def process_single(self, request: TTSRequest) -> TTSResult:
        """处理单个请求"""
        start_time = datetime.now()

        async with self._semaphore:
            for attempt in range(self.retry_count + 1):
                try:
                    response = await self.client.text_to_speech(
                        text=request.text,
                        voice=request.voice,
                        speed=request.speed,
                    )

                    # 保存文件
                    output_path = request.output_path or str(
                        OUTPUT_DIR / f"{request.id}.wav"
                    )
                    Path(output_path).write_bytes(response.audio_data)

                    duration = (datetime.now() - start_time).total_seconds()

                    return TTSResult(
                        request=request,
                        success=True,
                        audio_size=len(response.audio_data),
                        duration=duration,
                    )

                except Exception as e:
                    if attempt == self.retry_count:
                        return TTSResult(
                            request=request,
                            success=False,
                            error=str(e),
                        )
                    await asyncio.sleep(1 * (attempt + 1))

        return TTSResult(request=request, success=False, error="Unknown error")

    async def process_batch(
        self,
        requests: List[TTSRequest],
        progress_callback: Optional[callable] = None,
    ) -> List[TTSResult]:
        """批量处理请求"""
        tasks = [self.process_single(req) for req in requests]
        results = []

        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, len(requests), result)

        return results


async def example_batch_processor():
    """示例：批量处理器"""
    print("\n" + "=" * 60)
    print("示例 5.1: 批量 TTS 处理器")
    print("=" * 60)

    # 创建批量请求
    requests = [
        TTSRequest(
            id=f"news_{i:03d}",
            text=f"这是第{i}条新闻播报内容，请听众朋友们注意收听。",
            voice="tongtong",
            speed=1.0,
        )
        for i in range(1, 6)
    ]

    # 进度回调
    def on_progress(current: int, total: int, result: TTSResult):
        status = "✓" if result.success else "✗"
        print(f"  [{current}/{total}] {status} {result.request.id}")
        if not result.success:
            print(f"      错误: {result.error}")

    # 处理
    processor = TTSBatchProcessor(max_concurrent=2)
    await processor.initialize()

    try:
        print(f"\n处理 {len(requests)} 个请求（并发数: 2）...")
        results = await processor.process_batch(requests, on_progress)

        # 统计
        success_count = sum(1 for r in results if r.success)
        total_size = sum(r.audio_size for r in results if r.success)
        total_time = sum(r.duration for r in results if r.success)

        print(f"\n处理完成!")
        print(f"  成功: {success_count}/{len(requests)}")
        print(f"  总大小: {total_size:,} 字节")
        print(f"  总时间: {total_time:.2f} 秒")

    finally:
        await processor.close()


async def example_audiobook_generator():
    """示例：有声书生成器"""
    print("\n" + "=" * 60)
    print("示例 5.2: 有声书生成器")
    print("=" * 60)

    # 章节内容
    chapters = [
        {
            "id": "ch01",
            "title": "第一章：初识",
            "content": """
            在一个阳光明媚的早晨，小明第一次踏入了这所古老的学院。
            高大的石柱上爬满了常青藤，阳光透过树叶洒下斑驳的光影。
            他深吸一口气，推开了那扇厚重的木门。
            """,
        },
        {
            "id": "ch02",
            "title": "第二章：邂逅",
            "content": """
            图书馆里，他遇见了一个正在读书的女孩。
            她抬头微笑，阳光恰好照在她的侧脸。
            这一刻，时间仿佛静止了。
            """,
        },
        {
            "id": "ch03",
            "title": "第三章：抉择",
            "content": """
            面对眼前的分岔路，小明陷入了沉思。
            一条路通向未知的冒险，另一条路则是安稳的生活。
            他知道，无论选择哪条路，人生都将因此改变。
            """,
        },
    ]

    async with AIClient() as client:
        for chapter in chapters:
            print(f"\n处理: {chapter['title']}")

            # 生成章节音频
            audio_data = await client.text_to_speech_long(
                chapter['title'] + chapter['content'],
                voice="tongtong",
                speed=0.9,  # 稍慢的语速更适合有声书
            )

            output_path = OUTPUT_DIR / f"audiobook_{chapter['id']}.wav"
            output_path.write_bytes(audio_data)

            print(f"  已保存: {output_path}")
            print(f"  大小: {len(audio_data):,} 字节")

    print("\n有声书生成完成！")


async def example_notification_generator():
    """示例：通知语音生成器"""
    print("\n" + "=" * 60)
    print("示例 5.3: 通知语音生成器")
    print("=" * 60)

    # 不同类型的通知
    notifications = [
        {
            "type": "reminder",
            "text": "提醒：您有一个会议将在15分钟后开始。",
            "voice": "xiaochen",
            "speed": 1.0,
        },
        {
            "type": "warning",
            "text": "警告：系统检测到异常登录尝试，请及时处理。",
            "voice": "xiaochen",
            "speed": 1.2,
        },
        {
            "type": "welcome",
            "text": "欢迎回来！您有3条新消息等待查看。",
            "voice": "tongtong",
            "speed": 1.0,
        },
        {
            "type": "success",
            "text": "恭喜！您的订单已成功提交，订单号为202401010001。",
            "voice": "tongtong",
            "speed": 1.1,
        },
    ]

    async with AIClient() as client:
        for notif in notifications:
            print(f"\n生成 {notif['type']} 通知...")

            response = await client.text_to_speech(
                text=notif['text'],
                voice=notif['voice'],
                speed=notif['speed'],
            )

            output_path = OUTPUT_DIR / f"notification_{notif['type']}.wav"
            output_path.write_bytes(response.audio_data)

            print(f"  文本: {notif['text']}")
            print(f"  已保存: {output_path}")


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("TTS 批量处理与高级功能示例")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")

    await example_batch_processor()
    await example_audiobook_generator()
    await example_notification_generator()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
