"""
示例 07: VLM OCR 与文档理解

本示例展示如何使用 VLM 进行：
1. 文档 OCR 识别
2. 表格识别
3. 手写文字识别
4. 多语言文字识别
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


async def example_document_ocr():
    """示例：文档 OCR"""
    print("\n" + "=" * 60)
    print("示例 7.1: 文档 OCR 识别")
    print("=" * 60)

    async with AIClient() as client:
        # 文档图片示例
        image_url = "https://picsum.photos/seed/doc/400/500"

        print(f"文档图像 URL: {image_url}")

        prompt = """
        请识别图片中的所有文字内容，并按照以下格式输出：
        1. 保持原有的段落结构
        2. 识别标题和正文，并用适当的格式区分
        3. 如果有列表或项目符号，请保留格式
        """

        result = await client.analyze_image(image_url, prompt)
        print(f"\n识别结果:\n{result}")


async def example_table_recognition():
    """示例：表格识别"""
    print("\n" + "=" * 60)
    print("示例 7.2: 表格识别")
    print("=" * 60)

    async with AIClient() as client:
        # 表格图片示例
        image_url = "https://picsum.photos/seed/table/400/300"

        print(f"表格图像 URL: {image_url}")

        prompt = """
        请识别图片中的表格内容，并以 Markdown 表格格式输出：
        - 识别所有行和列
        - 保持数据的对应关系
        - 如果有合并单元格，请在输出中标注
        """

        result = await client.analyze_image(image_url, prompt)
        print(f"\n识别结果:\n{result}")


async def example_handwriting_recognition():
    """示例：手写文字识别"""
    print("\n" + "=" * 60)
    print("示例 7.3: 手写文字识别")
    print("=" * 60)

    async with AIClient() as client:
        # 手写文字图片示例
        image_url = "https://picsum.photos/seed/handwriting/400/200"

        print(f"手写图像 URL: {image_url}")

        prompt = """
        请仔细识别图片中的手写文字。
        注意：
        1. 对于模糊或难以辨认的字，请在括号中标注猜测内容
        2. 如果有涂改或删除痕迹，请标注
        3. 保持原有的行间距和布局
        """

        result = await client.analyze_image(image_url, prompt)
        print(f"\n识别结果:\n{result}")


async def example_multilingual_ocr():
    """示例：多语言 OCR"""
    print("\n" + "=" * 60)
    print("示例 7.4: 多语言文字识别")
    print("=" * 60)

    async with AIClient() as client:
        # 多语言文本图片示例
        image_url = "https://picsum.photos/seed/multilang/400/200"

        print(f"多语言图像 URL: {image_url}")

        prompt = """
        请识别图片中的所有文字，并：
        1. 区分不同的语言
        2. 标注每段文字的语言类型
        3. 如果可能，提供翻译
        """

        result = await client.analyze_image(image_url, prompt)
        print(f"\n识别结果:\n{result}")


async def example_receipt_recognition():
    """示例：收据/发票识别"""
    print("\n" + "=" * 60)
    print("示例 7.5: 收据/发票识别")
    print("=" * 60)

    async with AIClient() as client:
        # 收据图片示例
        image_url = "https://picsum.photos/seed/receipt/300/400"

        print(f"收据图像 URL: {image_url}")

        prompt = """
        请识别这张收据/发票图片，并提取以下信息（以JSON格式输出）：
        {
            "merchant_name": "商家名称",
            "date": "日期",
            "items": [
                {"name": "商品名", "price": "价格", "quantity": "数量"}
            ],
            "subtotal": "小计",
            "tax": "税额",
            "total": "总计"
        }
        如果某些信息无法识别，请标记为 null。
        """

        result = await client.analyze_image(image_url, prompt)
        print(f"\n识别结果:\n{result}")


async def example_id_card_recognition():
    """示例：证件识别"""
    print("\n" + "=" * 60)
    print("示例 7.6: 证件识别（示例）")
    print("=" * 60)

    print("""
    证件识别注意事项：

    1. 隐私保护
       - 只识别必要的信息
       - 对敏感信息进行脱敏处理
       - 遵守相关法律法规

    2. 使用示例代码：
    ```python
    async with AIClient() as client:
        prompt = '''
        请识别证件上的以下信息：
        - 姓名
        - 证件号码（部分隐藏）
        - 有效期
        注意：请对证件号码进行脱敏处理，只显示前3位和后4位。
        '''
        result = await client.analyze_image(image_path, prompt)
    ```

    3. 最佳实践
       - 使用 HTTPS 传输
       - 不存储原始证件图片
       - 及时清理临时文件
    """)


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("VLM OCR 与文档理解示例")
    print("=" * 60)

    await example_document_ocr()
    await example_table_recognition()
    await example_handwriting_recognition()
    await example_multilingual_ocr()
    await example_receipt_recognition()
    await example_id_card_recognition()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
