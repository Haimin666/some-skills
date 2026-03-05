# 钉钉群聊 QA 智能分析系统

基于大模型 Skills 的钉钉群聊数据分析工具，自动生成 QA 并进行智能分类和问题发现。

## 📋 功能特性

### 1. 钉钉群聊数据获取
- 支持获取指定群聊的历史消息
- 自动解析消息内容和发送者信息
- 支持增量同步和全量同步

### 2. 大模型 QA 生成
- 从群聊对话中自动提取问答对
- 支持上下文理解，生成高质量 QA
- 可配置生成规则和过滤条件

### 3. QA 分类管理
- 智能分类：系统bug、数据问题、业务问题、用户问题等
- 自动导入知识库
- 支持分类规则自定义

### 4. 问题发现与分析
- 自动识别潜在问题
- 生成问题统计报告
- 提供问题趋势分析

## 🚀 快速开始

### 1. 安装依赖

```bash
cd dingding-skills
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

需要配置：
- 钉钉 AppKey 和 AppSecret
- 大模型 API 配置
- 知识库配置

### 3. 运行

```bash
# 获取群聊数据
python main.py --action fetch --chat-id <群聊ID>

# 生成 QA
python main.py --action generate --chat-id <群聊ID>

# 分类并导入知识库
python main.py --action classify --chat-id <群聊ID>

# 分析问题
python main.py --action analyze --chat-id <群聊ID>

# 完整流程
python main.py --action all --chat-id <群聊ID>
```

## 📁 项目结构

```
dingding-skills/
├── README.md                   # 项目说明
├── config.py                   # 配置管理
├── requirements.txt            # Python 依赖
├── main.py                     # 主程序入口
├── api/
│   └── dingtalk_api.py        # 钉钉 API 封装
├── core/
│   ├── qa_generator.py        # QA 生成器
│   ├── qa_classifier.py       # QA 分类器
│   ├── problem_analyzer.py    # 问题分析器
│   └── knowledge_base.py      # 知识库管理
├── output/
│   └── knowledge_base/        # 知识库输出目录
└── logs/                       # 日志目录
```

## 🔧 配置说明

### 钉钉配置

在钉钉开放平台创建企业内部应用，获取：
- AppKey
- AppSecret
- 配置消息读取权限

### 问题分类配置

系统默认支持以下问题类型：

| 类型 | 说明 | 示例 |
|------|------|------|
| system_bug | 系统Bug | 页面崩溃、功能异常等 |
| data_issue | 数据问题 | 数据错误、数据缺失等 |
| business_issue | 业务问题 | 业务流程、规则咨询等 |
| user_issue | 用户问题 | 使用问题、操作指导等 |
| feature_request | 功能需求 | 新功能建议、改进意见 |
| other | 其他问题 | 不属于以上分类的问题 |

## 📊 输出示例

### QA 文件格式

```json
{
  "qa_list": [
    {
      "id": "qa_001",
      "question": "如何重置密码？",
      "answer": "您可以通过登录页面点击'忘记密码'，然后输入手机号获取验证码进行重置。",
      "category": "user_issue",
      "confidence": 0.95,
      "source": "群聊消息",
      "created_at": "2024-01-01 10:00:00"
    }
  ]
}
```

### 问题分析报告

```json
{
  "summary": {
    "total_issues": 100,
    "by_category": {
      "system_bug": 15,
      "data_issue": 10,
      "business_issue": 30,
      "user_issue": 35,
      "feature_request": 10
    }
  },
  "trends": {
    "increasing": ["system_bug"],
    "stable": ["business_issue"],
    "decreasing": ["data_issue"]
  },
  "recommendations": [
    "建议优先处理 system_bug 类问题，占比 15%",
    "用户问题较多，建议优化用户引导流程"
  ]
}
```

## 🔒 安全说明

1. 所有敏感配置通过环境变量管理
2. API Token 不硬编码在代码中
3. 知识库数据支持加密存储

## 📝 License

MIT License
