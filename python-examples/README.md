# Python 大模型 Skills 使用案例

这是一个完整的 Python 示例项目，展示如何使用大模型的各种 AI 能力（Skills）。

## 📋 目录结构

```
python-examples/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python 依赖
├── config.py                    # 配置文件
├── client.py                    # AI 客户端封装
├── examples/                    # 示例代码目录
│   ├── 01_llm_basic.py         # LLM 基础使用
│   ├── 02_llm_conversation.py  # LLM 多轮对话
│   ├── 03_llm_code_assistant.py # LLM 代码助手
│   ├── 04_tts_basic.py         # TTS 语音合成
│   ├── 05_tts_batch.py         # TTS 批量处理
│   ├── 06_vlm_basic.py         # VLM 图像理解
│   ├── 07_vlm_ocr.py           # VLM OCR 文字提取
│   ├── 08_asr_basic.py         # ASR 语音识别
│   ├── 09_image_generation.py  # 图像生成
│   └── 10_multi_skill_app.py   # 综合应用示例
└── output/                      # 输出文件目录
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd python-examples
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件或直接修改 `config.py`：

```python
API_BASE_URL = "your_api_base_url"
API_KEY = "your_api_key"
```

### 3. 运行示例

```bash
# 运行 LLM 基础示例
python examples/01_llm_basic.py

# 运行 TTS 语音合成示例
python examples/04_tts_basic.py

# 运行综合应用
python examples/10_multi_skill_app.py
```

## 📚 Skills 介绍

### 1. LLM (大语言模型)
- **用途**: 文本生成、对话、代码生成、翻译等
- **示例**: `01_llm_basic.py`, `02_llm_conversation.py`, `03_llm_code_assistant.py`

### 2. TTS (语音合成)
- **用途**: 文本转语音、有声书、语音通知等
- **示例**: `04_tts_basic.py`, `05_tts_batch.py`

### 3. VLM (视觉语言模型)
- **用途**: 图像理解、OCR、图像问答等
- **示例**: `06_vlm_basic.py`, `07_vlm_ocr.py`

### 4. ASR (语音识别)
- **用途**: 语音转文字、语音命令、会议转写等
- **示例**: `08_asr_basic.py`

### 5. Image Generation (图像生成)
- **用途**: AI 绘图、创意设计、图像创作等
- **示例**: `09_image_generation.py`

## 🔧 客户端封装

`client.py` 提供了统一的 AI 客户端封装，支持所有 Skills：

```python
from client import AIClient

# 创建客户端
client = AIClient()

# LLM 对话
response = await client.chat("你好，请介绍一下自己")

# TTS 语音合成
audio_data = await client.text_to_speech("欢迎使用语音合成服务")

# VLM 图像理解
result = await client.analyze_image(image_url, "描述这张图片")

# ASR 语音识别
text = await client.speech_to_text(audio_file)

# 图像生成
image_data = await client.generate_image("一只可爱的猫咪")
```

## 📝 最佳实践

1. **错误处理**: 所有 API 调用都应包含异常处理
2. **重试机制**: 实现指数退避重试策略
3. **资源管理**: 及时释放资源，避免内存泄漏
4. **并发控制**: 控制并发请求数量，避免限流
5. **缓存策略**: 对重复请求实现缓存

## 🎯 使用场景

| Skill | 应用场景 |
|-------|----------|
| LLM | 智能客服、内容生成、代码助手、翻译系统 |
| TTS | 有声读物、语音通知、导航播报、配音系统 |
| VLM | 图像搜索、内容审核、OCR识别、智能分析 |
| ASR | 语音输入、会议转写、字幕生成、语音助手 |
| Image Gen | 创意设计、游戏素材、广告图生成、艺术创作 |

## 📄 License

MIT License
