# 钉钉群聊 QA 智能分析系统（金融场景版）

基于 **chat-to-qa Skill** 的钉钉群聊数据分析工具，支持 **FastGPT 工作流** 直接调用。

## 🚀 快速开始（FastGPT 集成）

### 方式一：FastGPT 工作流调用（推荐）

#### 1. 启动 API 服务

```bash
cd dingding-skills
pip install -r requirements.txt
python api_server.py --port 8080
```

#### 2. 在 FastGPT 创建工作流

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  定时触发   │ ──▶ │ HTTP 请求   │ ──▶ │ 知识库导入  │
│  每日0点    │     │ 获取QA数据  │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

**HTTP 请求节点配置：**
```
请求方式: GET
请求地址: http://your-server:8080/api/fastgpt/qa?days=1
```

**返回数据格式：**
```json
{
  "list": [
    {
      "q": "上海银行签署借款合同提示：验证码初始化异常怎么办？",
      "a": "验证码输错6次后会出现此报错提示。请重新尝试。",
      "tags": ["金融", "系统"]
    }
  ],
  "total": 1
}
```

#### 3. 导入知识库

在 FastGPT 工作流中：
1. 添加"知识库导入"节点
2. 数据源选择 HTTP 返回的 `list` 字段
3. 完成自动导入

📖 详细教程请查看：[FASTGPT_GUIDE.md](./FASTGPT_GUIDE.md)

---

### 方式二：定时同步服务

每日 0 点自动同步昨天的数据：

```bash
python start_sync.py --mode schedule --hour 0 --minute 0 --real
```

### 方式三：Docker 部署

```bash
docker-compose up -d
```

---

## 📋 API 接口说明

| 接口 | 方法 | 说明 | FastGPT 推荐 |
|------|------|------|--------------|
| `/api/fastgpt/qa` | GET | 获取 FastGPT 格式 QA | ✅ 推荐 |
| `/api/messages` | GET | 获取聊天消息 | |
| `/api/extract-qa` | POST | 提取 QA | |
| `/api/sync` | POST | 完整同步 | |
| `/api/health` | GET | 健康检查 | |

### FastGPT 推荐接口

```
GET /api/fastgpt/qa?days=1
```

返回数据可直接导入知识库，无需额外处理。

---

## 📁 项目结构

```
dingding-skills/
├── api_server.py                   # HTTP API 服务（FastGPT 调用）
├── start_sync.py                   # 定时同步入口
├── scheduler.py                    # 定时调度器
├── main.py                         # 主程序
├── config.py                       # 配置管理
├── FASTGPT_GUIDE.md               # FastGPT 集成指南 ⭐
├── Dockerfile                      # Docker 部署
├── docker-compose.yml              # Docker 编排
├── skills/chat-to-qa/              # chat-to-qa Skill
│   ├── SKILL.md                    # Skill 定义
│   └── scripts/                    # 核心脚本
└── output/                         # 输出目录
```

---

## 🔧 配置说明

### 环境变量（.env）

```bash
# 钉钉配置
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret
DINGTALK_ACCESS_TOKEN=your_access_token

# 大模型配置（用于 QA 提取）
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_key
LLM_MODEL=gpt-4

# FastGPT 配置（可选，用于自动导入）
FASTGPT_API_URL=https://api.fastgpt.in
FASTGPT_API_KEY=your_fastgpt_key
FASTGPT_DATASET_ID=your_dataset_id
```

---

## 📊 分类标签（金融场景）

| 标签 | 说明 | 示例关键词 |
|------|------|-----------|
| 金融 | 金融业务问题 | 借款、合同、贷款、银行、验证码 |
| 系统 | 系统 Bug 问题 | 报错、异常、崩溃、超时、初始化 |
| 其他 | 其他问题 | - |

---

## 🎯 使用场景

### 场景 1：每日自动同步

1. FastGPT 定时触发工作流
2. 调用 API 获取昨天聊天数据
3. 自动提取 QA 并导入知识库

### 场景 2：按需手动同步

1. 手动触发 FastGPT 工作流
2. 指定同步天数
3. 查看统计结果

### 场景 3：钉钉机器人联动

1. 钉钉群消息触发 Webhook
2. 实时提取 QA
3. 立即导入知识库

---

## 📖 详细文档

- [FastGPT 工作流集成指南](./FASTGPT_GUIDE.md)
- [chat-to-qa Skill 说明](./skills/chat-to-qa/SKILL.md)

---

## 📄 License

MIT License
