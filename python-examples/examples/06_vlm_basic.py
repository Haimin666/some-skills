"""
示例 06: VLM (视觉语言模型) 基础使用

本示例展示如何使用 VLM 进行图像理解：
1. 图像描述
2. 图像问答
3. 多图像比较
4. 本地图像分析
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


async def example_image_description():
    """示例：图像描述"""
    print("\n" + "=" * 60)
    print("示例 6.1: 图像描述")
    print("=" * 60)

    async with AIClient() as client:
        # 使用网络图片 URL
        image_url = "https://picsum.photos/400/300"

        print(f"图像 URL: {image_url}")
        print("正在分析图像...")

        description = await client.analyze_image(
            image_url,
            prompt="请详细描述这张图片的内容，包括场景、主体、颜色和氛围。",
        )

        print(f"\n图像描述:\n{description}")


async def example_image_qa():
    """示例：图像问答"""
    print("\n" + "=" * 60)
    print("示例 6.2: 图像问答")
    print("=" * 60)

    async with AIClient() as client:
        # 使用风景图片
        image_url = "https://picsum.photos/seed/nature/400/300"

        questions = [
            "这张图片中有哪些主要元素？",
            "图片的色调是什么？",
            "这看起来是什么季节？为什么？",
            "如果要给这张图片起个标题，你会起什么？",
        ]

        print(f"图像 URL: {image_url}\n")

        for i, question in enumerate(questions, 1):
            print(f"问题 {i}: {question}")
            answer = await client.analyze_image(image_url, question)
            print(f"回答: {answer}")
            print("-" * 40)


async def example_multiple_images():
    """示例：多图像比较"""
    print("\n" + "=" * 60)
    print("示例 6.3: 多图像比较")
    print("=" * 60)

    async with AIClient() as client:
        # 使用两张不同的图片
        image_urls = [
            "https://picsum.photos/seed/tech/200/200",
            "https://picsum.photos/seed/nature2/200/200",
        ]

        print("比较两张图片...\n")

        # 分别分析每张图片
        descriptions = []
        for i, url in enumerate(image_urls, 1):
            desc = await client.analyze_image(url, "用一句话描述这张图片的主要内容。")
            descriptions.append(desc)
            print(f"图片 {i}: {desc}")

        print("\n比较两张图片的风格和主题差异...")
        comparison = await client.analyze_image(
            image_urls[0],
            prompt=f"""
            这张图片的内容是：{descriptions[0]}
            另一张图片的内容是：{descriptions[1]}
            请分析这两张图片在主题和风格上的主要差异。
            """,
        )
        print(f"分析结果: {comparison}")


async def example_local_image():
    """示例：本地图像分析"""
    print("\n" + "=" * 60)
    print("示例 6.4: 本地图像分析")
    print("=" * 60)

    # 创建一个简单的测试图片（如果不存在）
    test_image_path = OUTPUT_DIR / "test_image.txt"

    # 在实际使用中，这里应该是一个真实的图片文件
    print("本地图像分析示例：")
    print("（需要实际的图片文件）")

    code_example = '''
    async with AIClient() as client:
        # 方法 1: 使用 Path 对象
        image_path = Path("/path/to/your/image.jpg")
        description = await client.analyze_image(image_path, "描述这张图片")

        # 方法 2: 使用字节数据
        with open("/path/to/your/image.jpg", "rb") as f:
            image_bytes = f.read()
        description = await client.analyze_image(image_bytes, "描述这张图片")
    '''
    print(f"代码示例:{code_example}")


async def example_ocr():
    """示例：OCR 文字识别"""
    print("\n" + "=" * 60)
    print("示例 6.5: OCR 文字识别")
    print("=" * 60)

    async with AIClient() as client:
        # 使用包含文字的图片
        image_url = "https://picsum.photos/seed/document/400/200"

        print(f"图像 URL: {image_url}")
        print("正在识别图片中的文字...\n")

        extracted_text = await client.extract_text_from_image(image_url)

        print(f"识别结果:\n{extracted_text}")


async def example_image_tagging():
    """示例：图像标签生成"""
    print("\n" + "=" * 60)
    print("示例 6.6: 图像标签生成")
    print("=" * 60)

    async with AIClient() as client:
        image_url = "https://picsum.photos/seed/random/400/300"

        print(f"图像 URL: {image_url}")

        prompt = """
        请分析这张图片并生成以下信息（以JSON格式输出）：
        {
            "main_subject": "主要主体",
            "tags": ["标签1", "标签2", "标签3"],
            "colors": ["主要颜色"],
            "mood": "图片氛围",
            "style": "图片风格"
        }
        """

        result = await client.analyze_image(image_url, prompt)
        print(f"\n标签结果:\n{result}")


async def example_product_analysis():
    """示例：商品图像分析"""
    print("\n" + "=" * 60)
    print("示例 6.7: 商品图像分析")
    print("=" * 60)

    async with AIClient() as client:
        # 模拟商品图片
        image_url = "https://picsum.photos/seed/product/400/300"

        prompt = """
        请作为电商分析师分析这张商品图片：
        1. 商品类型和类别
        2. 可能的目标用户群体
        3. 商品的卖点
        4. 图片拍摄质量评价
        5. 改进建议
        """

        print(f"商品图像 URL: {image_url}")
        print("正在分析商品图像...\n")

        analysis = await client.analyze_image(image_url, prompt)
        print(f"分析结果:\n{analysis}")


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("VLM (视觉语言模型) 基础使用示例")
    print("=" * 60)

    await example_image_description()
    await example_image_qa()
    await example_multiple_images()
    await example_local_image()
    await example_ocr()
    await example_image_tagging()
    await example_product_analysis()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
