# 钉钉群聊 QA 智能分析系统（金融场景版）

基于 **chat-to-qa Skill** 的钉钉群聊数据分析工具，专为金融场景设计，从零散的聊天记录中智能提取问答对并自动分类标签。

## 📋 核心功能

### 1. 获取群聊数据
- 获取钉钉群聊历史消息
- 支持文本、图片、富文本消息
- 识别发送者角色（客户、技术支持、业务经理等）

### 2. 智能 QA 提取 (chat-to-qa Skill)
- **上下文理解**：从零散对话中识别问答关系
- **人员角色识别**：区分提问者和回答者
- **图片信息处理**：支持解析图片内容
- **金融场景分类**：金融、系统、其他

### 3. 分类标签（金融场景）

| 标签 | 标识 | 说明 | 示例关键词 |
|------|------|------|-----------|
| 金融 | finance | 金融业务问题 | 合同、借款、贷款、签署、验证码、银行 |
| 系统 | system | 系统Bug问题 | 报错、异常、崩溃、超时、初始化 |
| 其他 | other | 其他问题 | - |

### 4. FastGpt 知识库集成
- 导出 FastGpt 导入格式
- 支持直接导入 FastGpt 知识库
- 多格式导出（JSON、CSV、Markdown）

## 🚀 快速开始

### 1. 安装依赖

```bash
cd dingding-skills
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```bash
# 大模型配置
LLM_API_BASE_URL=https://api.example.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4

# FastGpt 配置（可选）
FASTGPT_API_KEY=your_fastgpt_key
FASTGPT_DATASET_ID=your_dataset_id
```

### 3. 运行

```bash
# 使用模拟数据测试
python main.py --action all

# 使用真实 API
python main.py --action all --real

# 导入到 FastGpt
python main.py --action fastgpt \
    --fastgpt-key YOUR_KEY \
    --fastgpt-dataset YOUR_DATASET_ID
```

## 📁 项目结构

```
dingding-skills/
├── main.py                          # 主程序入口
├── config.py                        # 配置管理
├── requirements.txt                 # 依赖
├── api/
│   └── dingtalk_api.py             # 钉钉 API 封装
├── skills/
│   └── chat-to-qa/                  # chat-to-qa Skill
│       ├── SKILL.md                 # Skill 定义
│       ├── scripts/
│       │   ├── qa_extractor.py      # QA 提取
│       │   └── fastgpt_importer.py  # FastGpt 导入
│       ├── templates/
│       │   └── qa_template.json     # QA 模板
│       └── resources/
│           └── categories.json      # 分类定义
└── output/
    └── knowledge_base/              # 输出目录
        ├── qa_full.json             # 完整数据
        ├── fastgpt_import.json      # FastGpt 导入格式
        ├── knowledge_base.csv       # CSV 格式
        ├── knowledge_base.md        # Markdown 格式
        └── by_category/             # 按分类组织
```

## 💡 使用示例

### 示例 1: 金融系统问题

**聊天记录：**
```
[10:00] 客户A: 上海银行 签署【借款合同】提示：验证码初始化异常
[10:02] 技术支持: 验证码输错6次会有这个报错提示
[10:03] 技术支持: 请重试，输入正确验证码就可以了
```

**提取 QA：**
```json
{
  "question": "上海银行签署借款合同提示：验证码初始化异常怎么办？",
  "answer": "验证码输错6次后会出现此报错提示。请重新尝试，输入正确的验证码即可。",
  "tags": ["金融", "系统"],
  "category": "finance"
}
```

### 示例 2: 纯金融问题

**聊天记录：**
```
[14:00] 客户B: 请问借款合同签署后多久可以放款？
[14:01] 业务经理: 正常情况下1-3个工作日放款
```

**提取 QA：**
```json
{
  "question": "借款合同签署后多久可以放款？",
  "answer": "正常情况下，合同签署完成后1-3个工作日放款。",
  "tags": ["金融"],
  "category": "finance"
}
```

## 📊 FastGpt 导入格式

```json
{
  "list": [
    {
      "q": "问题内容",
      "a": "答案内容",
      "tags": ["金融", "系统"]
    }
  ]
}
```

## 🔧 命令说明

| 命令 | 说明 |
|------|------|
| `--action fetch` | 获取群聊数据 |
| `--action extract` | 提取 QA |
| `--action export` | 导出知识库 |
| `--action fastgpt` | 导入 FastGpt |
| `--action all` | 完整流程 |
| `--real` | 使用真实 API |
| `--fastgpt-key` | FastGpt API Key |
| `--fastgpt-dataset` | FastGpt Dataset ID |

## 📄 License

MIT License
