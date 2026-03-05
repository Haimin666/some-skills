"""
示例 03: LLM 代码助手

本示例展示如何使用 LLM 作为代码助手：
1. 代码生成
2. 代码解释
3. 代码调试
4. 代码重构建议
5. 单元测试生成
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient


class CodeAssistant:
    """代码助手类 - 封装代码相关的 AI 功能"""

    def __init__(self):
        self.client = AIClient()

    async def initialize(self):
        """初始化客户端"""
        await self.client._init_session()

    async def close(self):
        """关闭连接"""
        await self.client.close()

    async def generate_code(self, description: str, language: str = "Python") -> str:
        """生成代码"""
        system_prompt = f"""你是一位经验丰富的{language}开发者。
请根据用户描述生成简洁、高效、可读性强的代码。
代码应该包含适当的注释和错误处理。"""

        response = await self.client.chat(description, system_prompt=system_prompt)
        return response.content

    async def explain_code(self, code: str, language: str = "Python") -> str:
        """解释代码"""
        system_prompt = f"""你是一位{language}编程导师。
请用清晰易懂的语言解释代码的功能、逻辑和关键概念。
对于初学者可能不理解的部分，提供额外的说明。"""

        prompt = f"请解释以下{language}代码:\n\n```\n{code}\n```"
        response = await self.client.chat(prompt, system_prompt=system_prompt)
        return response.content

    async def debug_code(self, code: str, error_message: str, language: str = "Python") -> str:
        """调试代码"""
        system_prompt = f"""你是一位{language}调试专家。
请分析代码中的错误，找出问题原因，并提供修复方案。
解释错误产生的原因，帮助用户理解并避免类似错误。"""

        prompt = f"""请帮我调试以下{language}代码:

代码:
```
{code}
```

错误信息:
```
{error_message}
```

请指出问题所在并提供修复后的代码。"""

        response = await self.client.chat(prompt, system_prompt=system_prompt)
        return response.content

    async def refactor_code(self, code: str, language: str = "Python") -> str:
        """重构代码"""
        system_prompt = f"""你是一位{language}代码优化专家。
请分析代码并提供重构建议，包括：
1. 代码风格改进
2. 性能优化
3. 可读性提升
4. 最佳实践应用"""

        prompt = f"请重构以下{language}代码:\n\n```\n{code}\n```"
        response = await self.client.chat(prompt, system_prompt=system_prompt)
        return response.content

    async def generate_tests(self, code: str, language: str = "Python") -> str:
        """生成单元测试"""
        system_prompt = f"""你是一位{language}测试专家。
请为给定代码生成全面的单元测试，包括：
1. 正常情况测试
2. 边界情况测试
3. 异常情况测试
使用标准的测试框架（如 Python 的 unittest 或 pytest）。"""

        prompt = f"请为以下{language}代码生成单元测试:\n\n```\n{code}\n```"
        response = await self.client.chat(prompt, system_prompt=system_prompt)
        return response.content

    async def convert_code(self, code: str, from_lang: str, to_lang: str) -> str:
        """代码语言转换"""
        system_prompt = f"""你是一位多语言编程专家。
请将{from_lang}代码转换为等效的{to_lang}代码。
保持代码的功能和逻辑一致，使用目标语言的最佳实践和惯用写法。"""

        prompt = f"请将以下{from_lang}代码转换为{to_lang}:\n\n```\n{code}\n```"
        response = await self.client.chat(prompt, system_prompt=system_prompt)
        return response.content


async def example_code_generation():
    """示例：代码生成"""
    print("\n" + "=" * 60)
    print("示例 3.1: 代码生成")
    print("=" * 60)

    assistant = CodeAssistant()
    await assistant.initialize()

    try:
        # 生成一个排序函数
        description = "写一个函数，接受一个列表，返回去除重复元素后的列表，保持原始顺序"
        print(f"\n需求: {description}")
        print("-" * 40)

        code = await assistant.generate_code(description)
        print(f"生成的代码:\n{code}")
    finally:
        await assistant.close()


async def example_code_explanation():
    """示例：代码解释"""
    print("\n" + "=" * 60)
    print("示例 3.2: 代码解释")
    print("=" * 60)

    assistant = CodeAssistant()
    await assistant.initialize()

    try:
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        print(f"代码:\n{code}")
        print("-" * 40)

        explanation = await assistant.explain_code(code)
        print(f"解释:\n{explanation}")
    finally:
        await assistant.close()


async def example_code_debugging():
    """示例：代码调试"""
    print("\n" + "=" * 60)
    print("示例 3.3: 代码调试")
    print("=" * 60)

    assistant = CodeAssistant()
    await assistant.initialize()

    try:
        buggy_code = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

result = calculate_average([])
print(result)
"""
        error_msg = "ZeroDivisionError: division by zero"

        print(f"代码:\n{buggy_code}")
        print(f"错误: {error_msg}")
        print("-" * 40)

        fix = await assistant.debug_code(buggy_code, error_msg)
        print(f"调试建议:\n{fix}")
    finally:
        await assistant.close()


async def example_code_refactoring():
    """示例：代码重构"""
    print("\n" + "=" * 60)
    print("示例 3.4: 代码重构")
    print("=" * 60)

    assistant = CodeAssistant()
    await assistant.initialize()

    try:
        code = """
def get_user_data(user_id):
    if user_id:
        if user_id > 0:
            if user_id < 1000:
                return {'id': user_id, 'name': 'User' + str(user_id)}
            else:
                return None
        else:
            return None
    else:
        return None
"""
        print(f"原代码:\n{code}")
        print("-" * 40)

        refactored = await assistant.refactor_code(code)
        print(f"重构建议:\n{refactored}")
    finally:
        await assistant.close()


async def example_test_generation():
    """示例：单元测试生成"""
    print("\n" + "=" * 60)
    print("示例 3.5: 单元测试生成")
    print("=" * 60)

    assistant = CodeAssistant()
    await assistant.initialize()

    try:
        code = """
def calculate_discount(price, discount_rate):
    if discount_rate < 0 or discount_rate > 1:
        raise ValueError("Discount rate must be between 0 and 1")
    return price * (1 - discount_rate)
"""
        print(f"被测代码:\n{code}")
        print("-" * 40)

        tests = await assistant.generate_tests(code)
        print(f"生成的测试:\n{tests}")
    finally:
        await assistant.close()


async def example_code_conversion():
    """示例：代码语言转换"""
    print("\n" + "=" * 60)
    print("示例 3.6: 代码语言转换")
    print("=" * 60)

    assistant = CodeAssistant()
    await assistant.initialize()

    try:
        javascript_code = """
function greet(name) {
    if (name === undefined || name === null) {
        return "Hello, Guest!";
    }
    return `Hello, ${name}!`;
}
"""
        print(f"JavaScript 代码:\n{javascript_code}")
        print("-" * 40)

        python_code = await assistant.convert_code(javascript_code, "JavaScript", "Python")
        print(f"Python 代码:\n{python_code}")
    finally:
        await assistant.close()


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("LLM 代码助手示例")
    print("=" * 60)

    await example_code_generation()
    await example_code_explanation()
    await example_code_debugging()
    await example_code_refactoring()
    await example_test_generation()
    await example_code_conversion()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
