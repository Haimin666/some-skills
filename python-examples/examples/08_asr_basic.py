"""
示例 08: ASR (语音识别) 基础使用

本示例展示如何使用 ASR 进行语音识别：
1. 基础语音转文字
2. 多语言识别
3. 音频文件处理
4. 长音频处理
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


async def example_basic_asr():
    """示例：基础 ASR"""
    print("\n" + "=" * 60)
    print("示例 8.1: 基础语音识别")
    print("=" * 60)

    async with AIClient() as client:
        # 音频文件路径（实际使用时需要提供真实文件）
        audio_path = OUTPUT_DIR / "sample_audio.mp3"

        print("基础语音识别示例：")
        print("（需要实际的音频文件）\n")

        code_example = '''
# 使用文件路径
text = await client.speech_to_text(Path("/path/to/audio.mp3"))
print(f"识别结果: {text}")

# 使用字节数据
with open("/path/to/audio.mp3", "rb") as f:
    audio_bytes = f.read()
text = await client.speech_to_text(audio_bytes)
print(f"识别结果: {text}")

# 使用 URL
text = await client.speech_to_text("https://example.com/audio.mp3")
print(f"识别结果: {text}")
        '''

        print("代码示例:")
        print(code_example)


async def example_multilingual_asr():
    """示例：多语言识别"""
    print("\n" + "=" * 60)
    print("示例 8.2: 多语言语音识别")
    print("=" * 60)

    async with AIClient() as client:
        print("多语言识别支持：\n")

        languages = {
            "zh": "中文",
            "en": "英语",
            "ja": "日语",
            "ko": "韩语",
            "fr": "法语",
            "de": "德语",
            "es": "西班牙语",
        }

        for code, name in languages.items():
            print(f"  {code}: {name}")

        print("\n使用示例：")
        code_example = '''
# 指定语言识别
text = await client.speech_to_text(audio_path, language="zh")
print(f"中文识别: {text}")

text = await client.speech_to_text(audio_path, language="en")
print(f"英文识别: {text}")
        '''
        print(code_example)


async def example_audio_formats():
    """示例：支持的音频格式"""
    print("\n" + "=" * 60)
    print("示例 8.3: 支持的音频格式")
    print("=" * 60)

    print("ASR 支持的音频格式：\n")

    formats = [
        {"format": "MP3", "description": "最常见的压缩音频格式"},
        {"format": "WAV", "description": "无损音频格式，质量最高"},
        {"format": "M4A", "description": "Apple 设备常用格式"},
        {"format": "FLAC", "description": "无损压缩格式"},
        {"format": "OGG", "description": "开源音频格式"},
        {"format": "WEBM", "description": "Web 音频格式"},
    ]

    for fmt in formats:
        print(f"  {fmt['format']}: {fmt['description']}")

    print("\n最佳实践：")
    print("  - 采样率: 16000 Hz 或更高")
    print("  - 声道: 单声道即可")
    print("  - 比特率: 128 kbps 或更高")


async def example_long_audio():
    """示例：长音频处理"""
    print("\n" + "=" * 60)
    print("示例 8.4: 长音频处理")
    print("=" * 60)

    print("长音频处理策略：\n")

    strategies = """
    1. 分段处理
       - 将长音频分割成小段（如每段 30 秒）
       - 分别识别每段内容
       - 合并结果

    2. 代码示例：
    ```python
    from pydub import AudioSegment

    # 加载音频
    audio = AudioSegment.from_file("long_audio.mp3")

    # 分段（每段 30 秒）
    segment_length = 30 * 1000  # 毫秒

    transcripts = []
    for i in range(0, len(audio), segment_length):
        segment = audio[i:i+segment_length]

        # 导出为字节
        segment_bytes = segment.export(format="mp3").read()

        # 识别
        text = await client.speech_to_text(segment_bytes)
        transcripts.append(text)

    # 合并结果
    full_transcript = " ".join(transcripts)
    ```

    3. 性能优化：
       - 使用并发处理多个分段
       - 缓存已识别的片段
       - 实现进度跟踪
    """
    print(strategies)


async def example_meeting_transcription():
    """示例：会议转写"""
    print("\n" + "=" * 60)
    print("示例 8.5: 会议转写")
    print("=" * 60)

    print("会议转写应用示例：\n")

    code_example = '''
class MeetingTranscriber:
    """会议转写器"""

    def __init__(self):
        self.client = AIClient()

    async def transcribe(self, audio_path: Path) -> dict:
        """转写会议录音"""
        # 1. 语音识别
        transcript = await self.client.speech_to_text(audio_path)

        # 2. 使用 LLM 提取关键信息
        summary = await self.client.chat(
            f"请总结以下会议内容：\\n{transcript}",
            system_prompt="你是一个会议记录助手，擅长提取关键信息。"
        )

        # 3. 提取行动项
        action_items = await self.client.chat(
            f"从以下会议内容中提取行动项：\\n{transcript}",
            system_prompt="请以列表形式输出所有行动项。"
        )

        return {
            "transcript": transcript,
            "summary": summary.content,
            "action_items": action_items.content,
        }

# 使用
transcriber = MeetingTranscriber()
result = await transcriber.transcribe(Path("meeting.mp3"))
    '''

    print(code_example)


async def example_realtime_asr():
    """示例：实时语音识别"""
    print("\n" + "=" * 60)
    print("示例 8.6: 实时语音识别架构")
    print("=" * 60)

    print("实时语音识别实现方案：\n")

    architecture = """
    ┌─────────────────┐
    │   音频输入      │ (麦克风/流媒体)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   音频缓冲      │ (收集音频块)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   VAD 检测      │ (语音活动检测)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   ASR 处理      │ (语音识别)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │   结果输出      │ (实时显示)
    └─────────────────┘

    实现要点：
    1. 使用 WebSocket 进行实时通信
    2. 实现音频缓冲队列
    3. VAD 检测避免无效处理
    4. 支持断点续传
    """

    print(architecture)


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("ASR (语音识别) 基础使用示例")
    print("=" * 60)

    await example_basic_asr()
    await example_multilingual_asr()
    await example_audio_formats()
    await example_long_audio()
    await example_meeting_transcription()
    await example_realtime_asr()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
