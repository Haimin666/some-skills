"""
示例 10: 综合应用 - 智能内容创作助手

本示例展示如何组合多种 AI Skills 构建实际应用：
1. 文章生成与配音 (LLM + TTS)
2. 图文内容创作 (LLM + Image Generation)
3. 语音转文字与摘要 (ASR + LLM)
4. 图片内容分析 (VLM + LLM)
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "multi_skill"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Article:
    """文章数据"""
    title: str
    content: str
    audio_path: Optional[str] = None
    cover_image_path: Optional[str] = None


class ContentCreator:
    """
    智能内容创作助手

    功能：
    - 自动生成文章
    - 文章配音
    - 生成封面图
    - 内容摘要
    """

    def __init__(self):
        self.client = AIClient()

    async def initialize(self):
        """初始化"""
        await self.client._init_session()

    async def close(self):
        """关闭连接"""
        await self.client.close()

    async def create_article(
        self,
        topic: str,
        style: str = "专业",
        length: int = 500,
    ) -> Article:
        """创作文章"""
        print(f"\n正在创作文章: {topic}")

        # 构建提示词
        system_prompt = f"""你是一位专业的内容创作者，擅长撰写{style}风格的文章。
请确保文章：
1. 标题吸引人
2. 内容结构清晰
3. 语言流畅自然
4. 字数在 {length} 字左右"""

        prompt = f"""请以"{topic}"为主题，写一篇文章。

请按照以下格式输出：
## 标题
[文章标题]

## 正文
[文章内容]"""

        response = await self.client.chat(prompt, system_prompt=system_prompt)

        # 解析标题和内容
        content = response.content
        title = topic

        if "## 标题" in content:
            parts = content.split("## 正文")
            if len(parts) >= 2:
                title_part = parts[0].replace("## 标题", "").strip()
                content = parts[1].strip()
                title = title_part.split("\n")[0].strip()

        return Article(title=title, content=content)

    async def add_voice_over(
        self,
        article: Article,
        voice: str = "tongtong",
        speed: float = 1.0,
    ) -> Article:
        """为文章添加配音"""
        print(f"正在为文章《{article.title}》添加配音...")

        # 准备配音文本
        voice_text = f"{article.title}。{article.content}"

        # 生成长文本语音
        audio_data = await self.client.text_to_speech_long(
            voice_text,
            voice=voice,
            speed=speed,
        )

        # 保存音频
        audio_path = str(OUTPUT_DIR / f"article_{hash(article.title) % 10000}.wav")
        Path(audio_path).write_bytes(audio_data)

        article.audio_path = audio_path
        print(f"配音已保存: {audio_path}")

        return article

    async def add_cover_image(
        self,
        article: Article,
        style: str = "vivid",
    ) -> Article:
        """为文章生成封面图"""
        print(f"正在为文章《{article.title}》生成封面...")

        # 根据文章内容生成图像提示词
        prompt = f"为文章《{article.title}》创作一张封面图片，风格现代简约，主题相关"

        try:
            image_data = await self.client.generate_image(prompt, style=style)

            # 保存图像
            image_path = str(OUTPUT_DIR / f"cover_{hash(article.title) % 10000}.png")
            Path(image_path).write_bytes(image_data)

            article.cover_image_path = image_path
            print(f"封面已保存: {image_path}")
        except Exception as e:
            print(f"封面生成失败: {e}")

        return article

    async def summarize(self, text: str, max_points: int = 5) -> str:
        """生成摘要"""
        prompt = f"请用 {max_points} 个要点总结以下内容：\n\n{text}"
        response = await self.client.chat(prompt)
        return response.content


class AudioContentProcessor:
    """
    音频内容处理器

    功能：
    - 语音转文字
    - 内容摘要
    - 关键信息提取
    """

    def __init__(self):
        self.client = AIClient()

    async def initialize(self):
        await self.client._init_session()

    async def close(self):
        await self.client.close()

    async def process_audio(
        self,
        audio_path: Path,
        extract_action_items: bool = True,
    ) -> dict:
        """处理音频内容"""
        print(f"正在处理音频: {audio_path}")

        # 语音转文字
        transcript = await self.client.speech_to_text(audio_path)

        # 生成摘要
        summary = await self.client.chat(
            f"请总结以下内容：\n{transcript}",
            system_prompt="你是一个专业的内容总结助手，擅长提炼关键信息。",
        )

        result = {
            "transcript": transcript,
            "summary": summary.content,
        }

        # 提取行动项
        if extract_action_items:
            action_items = await self.client.chat(
                f"从以下内容中提取所有行动项和待办事项：\n{transcript}",
                system_prompt="请以列表形式输出，每项一个要点。",
            )
            result["action_items"] = action_items.content

        return result


class ImageContentAnalyzer:
    """
    图像内容分析器

    功能：
    - 图像描述
    - 内容标签
    - 文字识别
    """

    def __init__(self):
        self.client = AIClient()

    async def initialize(self):
        await self.client._init_session()

    async def close(self):
        await self.client.close()

    async def analyze(
        self,
        image_source,
        extract_text: bool = True,
        generate_tags: bool = True,
    ) -> dict:
        """分析图像内容"""
        print("正在分析图像...")

        result = {}

        # 图像描述
        description = await self.client.analyze_image(
            image_source,
            "请详细描述这张图片的内容、主体、颜色和氛围。",
        )
        result["description"] = description

        # 文字识别
        if extract_text:
            text = await self.client.extract_text_from_image(image_source)
            result["extracted_text"] = text

        # 生成标签
        if generate_tags:
            tags_response = await self.client.analyze_image(
                image_source,
                "请用 5 个关键词描述这张图片，用逗号分隔。",
            )
            result["tags"] = [t.strip() for t in tags_response.split(",")]

        return result


# ==================== 示例运行 ====================


async def example_content_creator():
    """示例：内容创作助手"""
    print("\n" + "=" * 60)
    print("示例 10.1: 智能内容创作助手")
    print("=" * 60)

    creator = ContentCreator()
    await creator.initialize()

    try:
        # 创建文章
        article = await creator.create_article(
            topic="人工智能在日常生活中的应用",
            style="科普",
            length=300,
        )

        print(f"\n文章标题: {article.title}")
        print(f"文章内容:\n{article.content[:200]}...")

        # 添加配音
        article = await creator.add_voice_over(article)

        # 生成封面
        article = await creator.add_cover_image(article)

        print("\n内容创作完成！")

    finally:
        await creator.close()


async def example_audio_processor():
    """示例：音频内容处理"""
    print("\n" + "=" * 60)
    print("示例 10.2: 音频内容处理器")
    print("=" * 60)

    print("""
    音频内容处理流程：

    1. 语音识别 (ASR)
       ┌─────────────────┐
       │   音频文件      │
       └────────┬────────┘
                │
                ▼
       ┌─────────────────┐
       │   ASR 转写      │
       └────────┬────────┘
                │
                ▼
    2. 内容处理 (LLM)
       ┌─────────────────┐
       │   文字内容      │
       └────────┬────────┘
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
    ┌────────┐    ┌────────┐
    │  摘要  │    │行动项  │
    └────────┘    └────────┘

    使用示例：
    ```python
    processor = AudioContentProcessor()
    await processor.initialize()

    result = await processor.process_audio(
        Path("meeting.mp3"),
        extract_action_items=True
    )

    print("转写内容:", result["transcript"])
    print("摘要:", result["summary"])
    print("行动项:", result["action_items"])
    ```
    """)


async def example_image_analyzer():
    """示例：图像内容分析"""
    print("\n" + "=" * 60)
    print("示例 10.3: 图像内容分析器")
    print("=" * 60)

    analyzer = ImageContentAnalyzer()
    await analyzer.initialize()

    try:
        # 使用示例图片
        image_url = "https://picsum.photos/seed/analyze/400/300"

        result = await analyzer.analyze(
            image_url,
            extract_text=True,
            generate_tags=True,
        )

        print(f"\n图像描述: {result['description'][:200]}...")
        print(f"提取文字: {result.get('extracted_text', '无')}")
        print(f"标签: {result.get('tags', [])}")

    finally:
        await analyzer.close()


async def example_multi_skill_workflow():
    """示例：多技能协作工作流"""
    print("\n" + "=" * 60)
    print("示例 10.4: 多技能协作工作流")
    print("=" * 60)

    print("""
    多技能协作工作流示例：

    ┌─────────────────────────────────────────────────────────┐
    │                    智能内容创作流程                       │
    └─────────────────────────────────────────────────────────┘

    输入主题
         │
         ▼
    ┌─────────┐
    │   LLM   │ ──→ 生成文章内容
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
    ┌───┐   ┌───────┐
    │TTS│   │ Image │
    └─┬─┘   │  Gen  │
      │     └───┬───┘
      │         │
      ▼         ▼
    音频      封面图

    应用场景：
    1. 自媒体内容创作
    2. 在线教育课程制作
    3. 新闻播报生成
    4. 营销内容制作
    """)


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("综合应用 - 智能内容创作助手")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")

    await example_content_creator()
    await example_audio_processor()
    await example_image_analyzer()
    await example_multi_skill_workflow()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
