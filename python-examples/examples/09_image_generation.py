"""
示例 09: AI 图像生成

本示例展示如何使用 AI 进行图像生成：
1. 基础图像生成
2. 不同尺寸和质量
3. 图像变体生成
4. 批量图像生成
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from client import AIClient

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def example_basic_generation():
    """示例：基础图像生成"""
    print("\n" + "=" * 60)
    print("示例 9.1: 基础图像生成")
    print("=" * 60)

    async with AIClient() as client:
        prompt = "一只可爱的橘猫在阳光下打盹，温暖的色调"

        print(f"提示词: {prompt}")
        print("正在生成图像...")

        try:
            image_data = await client.generate_image(prompt)

            # 保存图像
            output_path = OUTPUT_DIR / "basic_generation.png"
            output_path.write_bytes(image_data)

            print(f"图像已保存: {output_path}")
            print(f"图像大小: {len(image_data):,} 字节")
        except Exception as e:
            print(f"生成失败: {e}")


async def example_different_sizes():
    """示例：不同尺寸"""
    print("\n" + "=" * 60)
    print("示例 9.2: 不同尺寸图像生成")
    print("=" * 60)

    async with AIClient() as client:
        prompt = "一座现代化的建筑在蓝天白云下"

        sizes = [
            ("256x256", "小尺寸"),
            ("512x512", "中等尺寸"),
            ("1024x1024", "大尺寸"),
        ]

        for size, desc in sizes:
            print(f"\n生成 {desc} ({size})...")

            try:
                image_data = await client.generate_image(prompt, size=size)

                output_path = OUTPUT_DIR / f"size_{size.replace('x', '_')}.png"
                output_path.write_bytes(image_data)

                print(f"  已保存: {output_path}")
                print(f"  大小: {len(image_data):,} 字节")
            except Exception as e:
                print(f"  失败: {e}")


async def example_different_qualities():
    """示例：不同质量"""
    print("\n" + "=" * 60)
    print("示例 9.3: 不同质量图像生成")
    print("=" * 60)

    async with AIClient() as client:
        prompt = "一幅精美的山水画，中国传统风格"

        qualities = [
            ("standard", "标准质量"),
            ("hd", "高清质量"),
        ]

        for quality, desc in qualities:
            print(f"\n生成 {desc}...")

            try:
                image_data = await client.generate_image(prompt, quality=quality)

                output_path = OUTPUT_DIR / f"quality_{quality}.png"
                output_path.write_bytes(image_data)

                print(f"  已保存: {output_path}")
            except Exception as e:
                print(f"  失败: {e}")


async def example_different_styles():
    """示例：不同风格"""
    print("\n" + "=" * 60)
    print("示例 9.4: 不同风格图像生成")
    print("=" * 60)

    async with AIClient() as client:
        styles = [
            ("vivid", "鲜艳风格", "一片梦幻的森林，色彩斑斓"),
            ("natural", "自然风格", "一片安静的森林，自然光线"),
        ]

        for style, desc, prompt in styles:
            print(f"\n生成 {desc} ({style})...")
            print(f"  提示词: {prompt}")

            try:
                image_data = await client.generate_image(prompt, style=style)

                output_path = OUTPUT_DIR / f"style_{style}.png"
                output_path.write_bytes(image_data)

                print(f"  已保存: {output_path}")
            except Exception as e:
                print(f"  失败: {e}")


async def example_image_variation():
    """示例：图像变体"""
    print("\n" + "=" * 60)
    print("示例 9.5: 图像变体生成")
    print("=" * 60)

    print("图像变体生成：\n")

    code_example = '''
async with AIClient() as client:
    # 原图路径
    original_image = Path("original.png")

    # 生成变体
    variation = await client.generate_image_variation(
        original_image,
        prompt="将这张图片转换为水彩画风格"
    )

    # 保存变体
    output_path = OUTPUT_DIR / "variation.png"
    output_path.write_bytes(variation)
    '''

    print(code_example)


async def example_prompt_engineering():
    """示例：提示词工程"""
    print("\n" + "=" * 60)
    print("示例 9.6: 提示词工程")
    print("=" * 60)

    print("优秀的图像生成提示词技巧：\n")

    tips = """
    1. 结构化提示词
       主体 + 动作 + 环境 + 风格 + 质量

       示例：
       "一只金毛犬 (主体) 在草地上奔跑 (动作)，
        阳光明媚的公园背景 (环境)，
        摄影风格，高细节 (风格)，
        8K 分辨率 (质量)"

    2. 使用具体描述
       ❌ "一个漂亮的房子"
       ✅ "一栋维多利亚风格的两层小屋，
          白色外墙和蓝色百叶窗，
          花园里开满了红色的玫瑰"

    3. 指定艺术风格
       - 油画风格
       - 水彩画
       - 数字艺术
       - 照片写实
       - 动漫风格
       - 像素艺术

    4. 添加质量关键词
       - 高细节 (highly detailed)
       - 专业摄影 (professional photography)
       - 电影级光效 (cinematic lighting)
       - 8K分辨率 (8K resolution)

    5. 负面提示词（如果支持）
       "模糊, 低质量, 变形, 丑陋"
    """

    print(tips)


async def example_batch_generation():
    """示例：批量图像生成"""
    print("\n" + "=" * 60)
    print("示例 9.7: 批量图像生成")
    print("=" * 60)

    async with AIClient() as client:
        prompts = [
            "一朵盛开的红玫瑰，特写镜头",
            "一朵盛开的向日葵，阳光明媚",
            "一朵盛开的樱花，粉色花瓣",
        ]

        print(f"批量生成 {len(prompts)} 张图像...\n")

        for i, prompt in enumerate(prompts, 1):
            print(f"[{i}/{len(prompts)}] {prompt}")

            try:
                image_data = await client.generate_image(prompt)

                output_path = OUTPUT_DIR / f"flower_{i}.png"
                output_path.write_bytes(image_data)

                print(f"  ✓ 已保存: {output_path}")
            except Exception as e:
                print(f"  ✗ 失败: {e}")


async def example_use_cases():
    """示例：应用场景"""
    print("\n" + "=" * 60)
    print("示例 9.8: 图像生成应用场景")
    print("=" * 60)

    use_cases = """
    1. 内容创作
       - 博客封面图
       - 社交媒体图片
       - 文章配图

    2. 设计素材
       - Logo 概念设计
       - UI 界面原型
       - 图标设计

    3. 营销素材
       - 广告创意图
       - 产品展示图
       - 活动海报

    4. 游戏开发
       - 角色概念图
       - 场景概念图
       - 物品图标

    5. 教育培训
       - 教学插图
       - 概念可视化
       - 学习卡片

    6. 个人创作
       - 头像生成
       - 艺术创作
       - 纪念图片
    """

    print(use_cases)


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("AI 图像生成示例")
    print("=" * 60)
    print(f"输出目录: {OUTPUT_DIR}")

    await example_basic_generation()
    await example_different_sizes()
    await example_different_qualities()
    await example_different_styles()
    await example_image_variation()
    await example_prompt_engineering()
    await example_batch_generation()
    await example_use_cases()

    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print(f"请查看 {OUTPUT_DIR} 目录获取生成的图像")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
