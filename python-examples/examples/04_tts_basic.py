"""
示例 04: TTS (语音合成) 基础使用

本示例展示如何使用 TTS 进行语音合成：
1. 基础文本转语音
2. 不同语音和语速
3. 保存音频文件
4. 流式语音合成
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient
from config import config

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


async def example_basic_tts():
    """示例：基础 TTS"""
    print("\n" + "=" * 60)
    print("示例 4.1: 基础文本转语音")
    print("=" * 60)

    async with AIClient() as client:
        text = "你好，欢迎使用语音合成服务。这是一段测试语音。"
        print(f"输入文本: {text}")

        response = await client.text_to_speech(text)

        # 保存音频文件
        output_path = OUTPUT_DIR / "basic_tts.wav"
        output_path.write_bytes(response.audio_data)

        print(f"音频已保存: {output_path}")
        print(f"格式: {response.format}")
        print(f"数据大小: {len(response.audio_data)} 字节")


async def example_different_voices():
    """示例：不同语音类型"""
    print("\n" + "=" * 60)
    print("示例 4.2: 不同语音类型")
    print("=" * 60)

    async with AIClient() as client:
        # 可用的语音类型
        voices = ["tongtong", "chuichui", "xiaochen"]

        text = "欢迎体验不同的语音风格。"

        for voice in voices:
            print(f"\n使用语音: {voice}")
            response = await client.text_to_speech(text, voice=voice)

            output_path = OUTPUT_DIR / f"tts_voice_{voice}.wav"
            output_path.write_bytes(response.audio_data)

            print(f"  已保存: {output_path}")
            print(f"  数据大小: {len(response.audio_data)} 字节")


async def example_different_speeds():
    """示例：不同语速"""
    print("\n" + "=" * 60)
    print("示例 4.3: 不同语速")
    print("=" * 60)

    async with AIClient() as client:
        text = "这是一段用于测试不同语速的文本。"
        speeds = [0.7, 1.0, 1.5]

        for speed in speeds:
            print(f"\n语速: {speed}x")
            response = await client.text_to_speech(text, speed=speed)

            output_path = OUTPUT_DIR / f"tts_speed_{speed}.wav"
            output_path.write_bytes(response.audio_data)

            print(f"  已保存: {output_path}")


async def example_long_text_tts():
    """示例：长文本语音合成"""
    print("\n" + "=" * 60)
    print("示例 4.4: 长文本语音合成")
    print("=" * 60)

    async with AIClient() as client:
        # 一段较长的文本
        long_text = """
        人工智能是计算机科学的一个分支，它企图了解智能的实质，
        并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
        人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大，
        可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。
        人工智能可以对人的意识、思维的信息过程进行模拟。
        人工智能不是人的智能，但能像人那样思考，也可能超过人的智能。
        """

        print(f"文本长度: {len(long_text)} 字符")
        print("正在处理长文本...")

        audio_data = await client.text_to_speech_long(long_text)

        output_path = OUTPUT_DIR / "tts_long_text.wav"
        output_path.write_bytes(audio_data)

        print(f"音频已保存: {output_path}")
        print(f"数据大小: {len(audio_data)} 字节")


async def example_batch_tts():
    """示例：批量语音合成"""
    print("\n" + "=" * 60)
    print("示例 4.5: 批量语音合成")
    print("=" * 60)

    async with AIClient() as client:
        # 多条文本批量处理
        texts = [
            "第一章：故事的开始",
            "第二章：意外的发现",
            "第三章：艰难的抉择",
            "第四章：新的旅程",
            "第五章：未完待续",
        ]

        results = []
        for i, text in enumerate(texts, 1):
            print(f"处理 {i}/{len(texts)}: {text}")

            response = await client.text_to_speech(text)
            output_path = OUTPUT_DIR / f"chapter_{i}.wav"
            output_path.write_bytes(response.audio_data)

            results.append({
                "text": text,
                "path": str(output_path),
                "size": len(response.audio_data),
            })

        print("\n批量处理完成！")
        print(f"总文件数: {len(results)}")
        print(f"总大小: {sum(r['size'] for r in results)} 字节")


async def example_tts_with_format_conversion():
    """示例：不同音频格式"""
    print("\n" + "=" * 60)
    print("示例 4.6: 不同音频格式")
    print("=" * 60)

    async with AIClient() as client:
        text = "测试不同音频格式的输出效果。"
        formats = ["wav", "mp3", "pcm"]

        for fmt in formats:
            print(f"\n格式: {fmt}")
            try:
                response = await client.text_to_speech(text, output_format=fmt)

                output_path = OUTPUT_DIR / f"tts_format.{fmt}"
                output_path.write_bytes(response.audio_data)

                print(f"  已保存: {output_path}")
                print(f"  数据大小: {len(response.audio_data)} 字节")
            except Exception as e:
                print(f"  错误: {e}")


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("TTS (语音合成) 基础使用示例")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")

    await example_basic_tts()
    await example_different_voices()
    await example_different_speeds()
    await example_long_text_tts()
    await example_batch_tts()
    await example_tts_with_format_conversion()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print(f"请查看 {OUTPUT_DIR} 目录获取生成的音频文件")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
