"""
AI 客户端封装 - 统一的 AI 服务调用接口

支持的功能：
- LLM: 大语言模型对话
- TTS: 文本转语音
- VLM: 视觉语言模型（图像理解）
- ASR: 语音转文字
- Image Generation: AI 图像生成
"""

import asyncio
import base64
import json
from typing import Optional, List, Dict, Any, Union, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from config import config, AIConfig


@dataclass
class Message:
    """聊天消息"""
    role: str  # system, user, assistant
    content: Union[str, List[Dict[str, Any]]]

    def to_dict(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


@dataclass
class TTSResponse:
    """TTS 响应"""
    audio_data: bytes
    format: str
    duration: Optional[float] = None


@dataclass
class ImageAnalysisResponse:
    """图像分析响应"""
    description: str
    tags: Optional[List[str]] = None
    objects: Optional[List[Dict[str, Any]]] = None


class AIClient:
    """
    AI 客户端 - 统一的 AI 服务调用接口

    使用示例：
    ```python
    client = AIClient()

    # LLM 对话
    response = await client.chat("你好")

    # TTS 语音合成
    audio = await client.text_to_speech("测试语音")

    # VLM 图像理解
    result = await client.analyze_image(image_url, "描述图片")

    # ASR 语音识别
    text = await client.speech_to_text(audio_file)

    # 图像生成
    image = await client.generate_image("一只猫")
    ```
    """

    def __init__(self, cfg: Optional[AIConfig] = None):
        self.config = cfg or config
        self._session: Optional[aiohttp.ClientSession] = None
        self._conversation_history: List[Message] = []

    async def __aenter__(self):
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _init_session(self):
        """初始化 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.config.request_timeout),
            )

    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_session(self) -> aiohttp.ClientSession:
        """获取 HTTP 会话"""
        if self._session is None or self._session.closed:
            raise RuntimeError("Session not initialized. Use async context manager or call _init_session()")
        return self._session

    # ==================== LLM 相关方法 ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        conversation_id: Optional[str] = None,
        stream: bool = False,
    ) -> Union[ChatResponse, AsyncGenerator[str, None]]:
        """
        发送聊天消息

        Args:
            message: 用户消息
            system_prompt: 系统提示词
            conversation_id: 会话 ID（用于多轮对话）
            stream: 是否流式返回

        Returns:
            ChatResponse 或异步生成器
        """
        await self._init_session()
        session = self._get_session()

        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 添加历史消息
        if conversation_id:
            for msg in self._conversation_history:
                messages.append(msg.to_dict())

        # 添加当前消息
        messages.append({"role": "user", "content": message})

        # 构建请求体
        payload = {
            "model": self.config.llm_model,
            "messages": messages,
            "max_tokens": self.config.llm_max_tokens,
            "temperature": self.config.llm_temperature,
            "stream": stream,
        }

        async with session.post(
            f"{self.config.api_base_url}/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()

            if stream:
                return self._stream_response(response)
            else:
                data = await response.json()
                return ChatResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data.get("model", self.config.llm_model),
                    usage=data.get("usage", {}),
                    finish_reason=data["choices"][0].get("finish_reason", ""),
                )

    async def _stream_response(self, response) -> AsyncGenerator[str, None]:
        """处理流式响应"""
        async for line in response.content:
            if line:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk["choices"][0].get("delta", {}).get("content"):
                            yield chunk["choices"][0]["delta"]["content"]
                    except json.JSONDecodeError:
                        continue

    async def chat_with_history(
        self,
        message: str,
        system_prompt: str = "你是一个有帮助的AI助手。",
    ) -> str:
        """
        带历史记录的对话

        Args:
            message: 用户消息
            system_prompt: 系统提示词

        Returns:
            AI 回复内容
        """
        await self._init_session()

        # 添加用户消息到历史
        self._conversation_history.append(Message(role="user", content=message))

        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        for msg in self._conversation_history:
            messages.append(msg.to_dict())

        response = await self.chat(message, system_prompt)

        # 添加 AI 回复到历史
        self._conversation_history.append(Message(role="assistant", content=response.content))

        return response.content

    def clear_history(self):
        """清除对话历史"""
        self._conversation_history = []

    # ==================== TTS 相关方法 ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        output_format: Optional[str] = None,
    ) -> TTSResponse:
        """
        文本转语音

        Args:
            text: 要转换的文本（最大 1024 字符）
            voice: 语音类型（tongtong, chuichui, xiaochen, jam, kazi, douji, luodo）
            speed: 语速（0.5 - 2.0）
            output_format: 输出格式（wav, mp3, pcm）

        Returns:
            TTSResponse 包含音频数据
        """
        await self._init_session()
        session = self._get_session()

        # 参数验证
        if len(text) > self.config.tts_max_chars:
            raise ValueError(f"文本长度超过最大限制 {self.config.tts_max_chars} 字符")

        speed = speed or self.config.tts_speed
        if not 0.5 <= speed <= 2.0:
            raise ValueError("语速必须在 0.5 到 2.0 之间")

        voice = voice or self.config.tts_voice
        output_format = output_format or self.config.tts_format

        payload = {
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": output_format,
        }

        async with session.post(
            f"{self.config.api_base_url}/audio/tts",
            json=payload,
        ) as response:
            response.raise_for_status()
            audio_data = await response.read()

            return TTSResponse(
                audio_data=audio_data,
                format=output_format,
            )

    async def text_to_speech_long(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        chunk_size: int = 1000,
    ) -> bytes:
        """
        长文本转语音（自动分段处理）

        Args:
            text: 长文本
            voice: 语音类型
            speed: 语速
            chunk_size: 每段最大字符数

        Returns:
            合并后的音频数据
        """
        # 分段处理长文本
        chunks = self._split_text(text, chunk_size)
        audio_chunks = []

        for chunk in chunks:
            response = await self.text_to_speech(chunk, voice, speed)
            audio_chunks.append(response.audio_data)

        # 简单拼接（实际应用中可能需要更复杂的音频合并逻辑）
        return b"".join(audio_chunks)

    def _split_text(self, text: str, max_length: int = 1000) -> List[str]:
        """将长文本分割成小段"""
        chunks = []
        sentences = text.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n").split("\n")

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    # ==================== VLM 相关方法 ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def analyze_image(
        self,
        image_source: Union[str, bytes, Path],
        prompt: str = "请描述这张图片的内容",
        detail: str = "auto",
    ) -> str:
        """
        分析图像

        Args:
            image_source: 图像来源（URL、字节数据或文件路径）
            prompt: 提示词
            detail: 分析程度（low, high, auto）

        Returns:
            图像分析结果
        """
        await self._init_session()
        session = self._get_session()

        # 处理不同类型的图像输入
        if isinstance(image_source, bytes):
            image_url = f"data:image/jpeg;base64,{base64.b64encode(image_source).decode()}"
        elif isinstance(image_source, Path):
            image_data = image_source.read_bytes()
            image_url = f"data:image/jpeg;base64,{base64.b64encode(image_data).decode()}"
        else:
            image_url = image_source

        payload = {
            "model": self.config.vlm_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": detail},
                        },
                    ],
                }
            ],
            "max_tokens": 1000,
        }

        async with session.post(
            f"{self.config.api_base_url}/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["choices"][0]["message"]["content"]

    async def extract_text_from_image(
        self,
        image_source: Union[str, bytes, Path],
    ) -> str:
        """
        从图像中提取文字（OCR）

        Args:
            image_source: 图像来源

        Returns:
            提取的文字
        """
        prompt = """请仔细识别图片中的所有文字内容，并按照原文的格式和布局输出。
注意：
1. 保持原有的换行和段落结构
2. 识别所有可见文字，包括标题、正文、注释等
3. 如果有表格，请用表格形式输出"""
        return await self.analyze_image(image_source, prompt)

    async def describe_image(
        self,
        image_source: Union[str, bytes, Path],
    ) -> ImageAnalysisResponse:
        """
        详细描述图像

        Args:
            image_source: 图像来源

        Returns:
            图像分析响应
        """
        prompt = """请详细描述这张图片，包括：
1. 主要内容和主题
2. 图像中的对象和元素
3. 颜色、构图、风格等视觉特征
4. 图像传达的情感或信息"""
        description = await self.analyze_image(image_source, prompt)
        return ImageAnalysisResponse(description=description)

    # ==================== ASR 相关方法 ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def speech_to_text(
        self,
        audio_source: Union[bytes, Path, str],
        language: Optional[str] = None,
    ) -> str:
        """
        语音转文字

        Args:
            audio_source: 音频来源（字节数据、文件路径或 URL）
            language: 语言代码（如 zh, en）

        Returns:
            转录的文字
        """
        await self._init_session()
        session = self._get_session()

        # 准备音频数据
        if isinstance(audio_source, bytes):
            audio_data = audio_source
            filename = "audio.mp3"
        elif isinstance(audio_source, Path):
            audio_data = audio_source.read_bytes()
            filename = audio_source.name
        else:
            # URL 情况
            async with session.get(audio_source) as resp:
                audio_data = await resp.read()
                filename = "audio.mp3"

        # 构建 multipart 表单数据
        form_data = aiohttp.FormData()
        form_data.add_field("file", audio_data, filename=filename, content_type="audio/mpeg")
        form_data.add_field("model", self.config.asr_model)
        if language:
            form_data.add_field("language", language)

        async with session.post(
            f"{self.config.api_base_url}/audio/transcriptions",
            data=form_data,
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("text", "")

    # ==================== 图像生成相关方法 ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def generate_image(
        self,
        prompt: str,
        size: Optional[str] = None,
        quality: Optional[str] = None,
        style: Optional[str] = None,
    ) -> bytes:
        """
        生成图像

        Args:
            prompt: 图像描述
            size: 图像尺寸（256x256, 512x512, 1024x1024）
            quality: 图像质量（standard, hd）
            style: 图像风格（vivid, natural）

        Returns:
            图像数据（PNG 格式）
        """
        await self._init_session()
        session = self._get_session()

        payload = {
            "model": self.config.image_model,
            "prompt": prompt,
            "size": size or self.config.image_size,
            "quality": quality or self.config.image_quality,
            "n": 1,
        }

        if style:
            payload["style"] = style

        async with session.post(
            f"{self.config.api_base_url}/images/generations",
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()

            # 获取图像 URL 并下载
            image_url = data["data"][0]["url"]
            async with session.get(image_url) as img_response:
                return await img_response.read()

    async def generate_image_variation(
        self,
        image_source: Union[bytes, Path],
        prompt: str,
    ) -> bytes:
        """
        基于现有图像生成变体

        Args:
            image_source: 参考图像
            prompt: 变体描述

        Returns:
            生成的图像数据
        """
        # 先分析原图
        description = await self.analyze_image(image_source, "简要描述这张图片的风格和主题")

        # 组合提示词
        combined_prompt = f"基于以下描述创建一个变体：{description}。新要求：{prompt}"

        return await self.generate_image(combined_prompt)


# ==================== 便捷函数 ====================

async def quick_chat(message: str, system_prompt: Optional[str] = None) -> str:
    """快速对话"""
    async with AIClient() as client:
        response = await client.chat(message, system_prompt)
        return response.content


async def quick_tts(text: str, output_path: str) -> str:
    """快速语音合成"""
    async with AIClient() as client:
        response = await client.text_to_speech(text)
        Path(output_path).write_bytes(response.audio_data)
        return output_path


async def quick_image_analysis(image_path: str, question: str) -> str:
    """快速图像分析"""
    async with AIClient() as client:
        return await client.analyze_image(Path(image_path), question)


# ==================== 示例使用 ====================

async def main():
    """示例：综合使用各种 AI 能力"""

    print("=" * 60)
    print("AI Skills 综合演示")
    print("=" * 60)

    async with AIClient() as client:
        # 1. LLM 对话
        print("\n1. LLM 对话示例")
        print("-" * 40)
        response = await client.chat("你好，请用一句话介绍自己")
        print(f"AI: {response.content}")

        # 2. 多轮对话
        print("\n2. 多轮对话示例")
        print("-" * 40)
        reply1 = await client.chat_with_history("我叫小明")
        print(f"AI: {reply1}")
        reply2 = await client.chat_with_history("我叫什么名字？")
        print(f"AI: {reply2}")

        # 3. TTS 语音合成
        print("\n3. TTS 语音合成示例")
        print("-" * 40)
        tts_response = await client.text_to_speech("欢迎使用语音合成服务")
        print(f"生成了 {len(tts_response.audio_data)} 字节的音频数据")

        # 4. 图像分析
        print("\n4. VLM 图像分析示例")
        print("-" * 40)
        # 使用示例图片 URL
        image_url = "https://picsum.photos/200"
        analysis = await client.analyze_image(image_url, "描述这张图片")
        print(f"分析结果: {analysis[:200]}...")

        # 5. 图像生成
        print("\n5. 图像生成示例")
        print("-" * 40)
        image_data = await client.generate_image("一只可爱的橘猫在阳光下打盹")
        print(f"生成了 {len(image_data)} 字节的图像数据")


if __name__ == "__main__":
    asyncio.run(main())
