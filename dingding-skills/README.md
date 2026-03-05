# 钉钉群聊 QA 智能分析系统

基于 **chat-to-qa Skill** 的钉钉群聊数据分析工具，从零散的聊天记录中智能提取问答对并自动分类标签。

## 📋 核心功能

### 1. 获取群聊数据
- 支持获取钉钉群聊历史消息
- 自动解析消息内容和发送者信息

### 2. 智能 QA 提取 (chat-to-qa Skill)
- **理解上下文**：从零散对话中识别真正的问答
- **智能合并**：答案可能分散在多条消息中，自动合并
- **质量过滤**：忽略闲聊、表情等无关内容
- **自动分类**：系统Bug、数据问题、业务问题、用户问题等
- **严重级别**：critical、high、medium、low

### 3. 知识库导入
- 支持 JSON、CSV、Markdown 多格式导出
- 按分类自动组织
- 包含完整的标签和元信息

## 🚀 快速开始

### 1. 安装依赖

```bash
cd dingding-skills
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件填入 API 配置
```

### 3. 运行

```bash
# 使用模拟数据测试
python main.py --action all

# 使用真实 API
python main.py --action all --real
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
│       ├── SKILL.md                 # Skill 定义（含提取规则、分类体系）
│       ├── scripts/
│       │   ├── qa_extractor.py      # QA 提取核心脚本
│       │   └── knowledge_base_importer.py  # 知识库导入
│       ├── templates/
│       │   └── qa_template.json     # QA 数据模板
│       └── resources/
│           └── categories.json      # 分类标签定义
└── output/
    └── knowledge_base/              # 输出目录
        ├── knowledge_base.json      # 完整知识库
        ├── knowledge_base.csv       # CSV 格式
        ├── knowledge_base.md        # Markdown 格式
        └── by_category/             # 按分类组织
```

## 🔧 chat-to-qa Skill 说明

### Skill 功能

chat-to-qa Skill 是核心技能，用于：
1. **上下文理解**：理解零散对话的语义，识别真正的问答
2. **QA 提取**：从聊天记录中提取结构化的问答对
3. **自动分类**：根据内容自动打上分类标签
4. **严重级别判断**：评估问题的紧急程度

### 分类标签体系

| 标签 | 标识 | 说明 |
|------|------|------|
| 系统Bug | system_bug | 报错、崩溃、功能异常 |
| 数据问题 | data_issue | 数据错误、缺失、不一致 |
| 业务问题 | business_issue | 流程、规则、权限问题 |
| 用户问题 | user_issue | 使用咨询、操作指导 |
| 功能需求 | feature_request | 新功能建议、改进意见 |
| 其他 | other | 不属于以上分类 |

### 严重级别

| 级别 | 说明 |
|------|------|
| critical | 系统崩溃、核心功能不可用 |
| high | 功能异常、影响业务 |
| medium | 一般问题、有临时方案 |
| low | 咨询类、建议类 |

## 📊 输出示例

### JSON 格式

```json
{
  "qa_list": [
    {
      "id": "qa_0001",
      "question": "打开订单列表页面时出现500错误怎么办？",
      "answer": "500错误是服务器临时故障导致的。可以尝试刷新页面或联系技术支持。",
      "category": "system_bug",
      "category_name": "系统Bug",
      "confidence": 0.95,
      "context": "用户访问订单列表功能时遇到服务器错误",
      "keywords": ["500错误", "订单列表"],
      "severity": "high"
    }
  ],
  "statistics": {
    "total_count": 10,
    "by_category": {
      "system_bug": 2,
      "user_issue": 5,
      "business_issue": 3
    }
  }
}
```

## 🔒 配置说明

### 环境变量

```bash
# 钉钉配置
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret

# 大模型配置
LLM_API_BASE_URL=https://api.example.com/v1
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4
```

## 📝 使用场景

1. **智能客服知识库构建**
   - 从群聊历史自动提取常见问题解答
   - 持续更新知识库

2. **问题趋势分析**
   - 统计各类问题分布
   - 发现高频问题

3. **服务质量改进**
   - 识别未解决的问题
   - 优化回答质量

## 📄 License

MIT License
