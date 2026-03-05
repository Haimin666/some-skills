"""
示例 01: LLM (大语言模型) 基础使用

本示例展示如何使用大语言模型进行：
1. 简单问答
2. 自定义系统提示词
3. 流式输出
4. 温度参数调优
"""

import asyncio
import sys
from pathlib import Path

# 添加父目录到路径以便导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient, quick_chat
from config import config


async def example_simple_qa():
    """示例：简单问答"""
    print("\n" + "=" * 60)
    print("示例 1.1: 简单问答")
    print("=" * 60)

    async with AIClient() as client:
        # 基础问答
        questions = [
            "什么是机器学习？请用一句话回答。",
            "Python 的主要特点是什么？",
            "请解释一下 REST API 的概念。",
        ]

        for i, question in enumerate(questions, 1):
            print(f"\n问题 {i}: {question}")
            response = await client.chat(question)
            print(f"回答: {response.content}")
            print(f"模型: {response.model}")
            print(f"Token 使用: {response.usage}")


async def example_custom_system_prompt():
    """示例：自定义系统提示词"""
    print("\n" + "=" * 60)
    print("示例 1.2: 自定义系统提示词")
    print("=" * 60)

    async with AIClient() as client:
        # 不同的系统提示词创建不同的人格
        personalities = {
            "代码审查专家": "你是一位经验丰富的代码审查专家。请指出代码中的问题并提供改进建议。",
            "创意作家": "你是一位富有想象力的创意作家。请用生动有趣的语言回答问题。",
            "数据分析师": "你是一位专业的数据分析师。请用数据和逻辑分析问题。",
        }

        question = "如何优化一个运行缓慢的 Python 程序？"

        for role, system_prompt in personalities.items():
            print(f"\n{'=' * 20} {role} {'=' * 20}")
            response = await client.chat(question, system_prompt=system_prompt)
            print(f"回答:\n{response.content[:500]}...")


async def example_streaming():
    """示例：流式输出"""
    print("\n" + "=" * 60)
    print("示例 1.3: 流式输出")
    print("=" * 60)

    async with AIClient() as client:
        question = "请写一首关于人工智能的五言绝句"
        print(f"问题: {question}")
        print("回答: ", end="", flush=True)

        response = await client.chat(question, stream=True)
        async for chunk in response:
            print(chunk, end="", flush=True)
        print()


async def example_temperature_effect():
    """示例：温度参数效果对比"""
    print("\n" + "=" * 60)
    print("示例 1.4: 温度参数效果对比")
    print("=" * 60)

    # 保存原始温度设置
    original_temp = config.llm_temperature

    temperatures = [0.1, 0.5, 1.0]
    prompt = "给一个初创科技公司起一个名字"

    for temp in temperatures:
        print(f"\n温度 = {temp}:")
        config.llm_temperature = temp

        async with AIClient() as client:
            response = await client.chat(prompt)
            print(f"  {response.content}")

    # 恢复原始设置
    config.llm_temperature = original_temp


async def example_quick_functions():
    """示例：使用便捷函数"""
    print("\n" + "=" * 60)
    print("示例 1.5: 便捷函数")
    print("=" * 60)

    # 使用快速对话函数
    response = await quick_chat(
        "请用 3 个关键词形容 Python 语言",
        system_prompt="你是一个简洁的回答者，只用关键词回答。"
    )
    print(f"快速回答: {response}")


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("LLM (大语言模型) 基础使用示例")
    print("=" * 60)

    await example_simple_qa()
    await example_custom_system_prompt()
    await example_streaming()
    await example_temperature_effect()
    await example_quick_functions()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
