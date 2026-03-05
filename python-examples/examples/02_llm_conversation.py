"""
示例 02: LLM 多轮对话

本示例展示如何实现：
1. 带历史记录的多轮对话
2. 对话上下文管理
3. 角色扮演对话
4. 对话摘要和记忆
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient, Message


class ConversationManager:
    """
    对话管理器 - 管理多轮对话的上下文和历史记录

    功能：
    - 维护对话历史
    - 支持系统提示词设置
    - 支持历史记录清理
    - 支持获取对话统计信息
    """

    def __init__(self, system_prompt: str = "你是一个有帮助的AI助手。"):
        self.system_prompt = system_prompt
        self.history: List[Dict] = []
        self.client: AIClient = None

    async def initialize(self):
        """初始化客户端"""
        self.client = AIClient()
        await client._init_session()

    async def chat(self, user_input: str) -> str:
        """发送消息并获取回复"""
        # 添加用户消息到历史
        self.history.append({"role": "user", "content": user_input})

        # 获取 AI 回复
        response = await self.client.chat_with_history(user_input, self.system_prompt)

        return response

    def get_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.history

    def clear_history(self):
        """清除对话历史"""
        self.history = []
        if self.client:
            self.client.clear_history()

    def get_stats(self) -> Dict:
        """获取对话统计"""
        total_messages = len(self.history)
        user_messages = sum(1 for m in self.history if m["role"] == "user")
        assistant_messages = total_messages - user_messages
        total_chars = sum(len(m["content"]) for m in self.history)

        return {
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "total_characters": total_chars,
        }


async def example_basic_conversation():
    """示例：基础多轮对话"""
    print("\n" + "=" * 60)
    print("示例 2.1: 基础多轮对话")
    print("=" * 60)

    async with AIClient() as client:
        # 设置系统提示词
        system_prompt = "你是一个友好的AI助手，会记住用户告诉你的信息。"

        # 第一轮对话
        print("\n用户: 我叫小华，今年25岁。")
        response = await client.chat_with_history("我叫小华，今年25岁。", system_prompt)
        print(f"AI: {response}")

        # 第二轮对话 - AI 应该记住名字
        print("\n用户: 我叫什么名字？")
        response = await client.chat_with_history("我叫什么名字？")
        print(f"AI: {response}")

        # 第三轮对话 - AI 应该记住年龄
        print("\n用户: 我多大年纪？")
        response = await client.chat_with_history("我多大年纪？")
        print(f"AI: {response}")

        # 显示对话统计
        stats = {
            "消息总数": len(client._conversation_history),
        }
        print(f"\n对话统计: {stats}")


async def example_role_play():
    """示例：角色扮演对话"""
    print("\n" + "=" * 60)
    print("示例 2.2: 角色扮演对话")
    print("=" * 60)

    async with AIClient() as client:
        # 技术面试官角色
        system_prompt = """你是一位资深的技术面试官，正在面试一个前端开发工程师职位。
你需要：
1. 问一些前端技术相关的问题
2. 对候选人的回答给出评价
3. 保持专业但友好的态度
4. 每次只问一个问题
"""

        print("\n=== 技术面试模拟 ===\n")

        # 模拟面试对话
        interactions = [
            "你好，我是来参加面试的。",
            "我熟悉 HTML、CSS、JavaScript，还有 Vue 和 React 框架。",
            "CSS 盒模型包括内容区、内边距、边框和外边距四个部分。",
        ]

        for user_input in interactions:
            print(f"候选人: {user_input}")
            response = await client.chat_with_history(user_input, system_prompt)
            print(f"面试官: {response}\n")


async def example_context_management():
    """示例：上下文管理"""
    print("\n" + "=" * 60)
    print("示例 2.3: 对话上下文管理")
    print("=" * 60)

    async with AIClient() as client:
        # 开始一个新对话
        system_prompt = "你是一个编程导师，帮助初学者学习 Python。"

        print("\n--- 开始第一个对话主题 ---")
        response = await client.chat_with_history("如何定义一个 Python 函数？", system_prompt)
        print(f"AI: {response[:200]}...")

        response = await client.chat_with_history("那如何给函数添加默认参数？")
        print(f"AI: {response[:200]}...")

        # 清除历史，开始新话题
        print("\n--- 清除历史，开始新话题 ---")
        client.clear_history()

        response = await client.chat_with_history("Python 的列表和元组有什么区别？")
        print(f"AI: {response[:200]}...")


async def example_conversation_summary():
    """示例：对话摘要"""
    print("\n" + "=" * 60)
    print("示例 2.4: 对话摘要")
    print("=" * 60)

    async with AIClient() as client:
        # 进行一系列对话
        system_prompt = "你是一个旅行顾问。"

        questions = [
            "我想去日本旅游，有什么推荐的城市吗？",
            "东京有什么值得去的地方？",
            "京都呢？有什么特别推荐的吗？",
        ]

        for q in questions:
            response = await client.chat_with_history(q, system_prompt)
            print(f"问: {q}")
            print(f"答: {response[:100]}...\n")

        # 请求摘要
        summary_prompt = "请用简洁的话总结我们刚才讨论的日本旅行建议。"
        response = await client.chat_with_history(summary_prompt)
        print(f"对话摘要: {response}")


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("LLM 多轮对话示例")
    print("=" * 60)

    await example_basic_conversation()
    await example_role_play()
    await example_context_management()
    await example_conversation_summary()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
