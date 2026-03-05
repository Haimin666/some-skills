# 鞂钉群聊 QA 智能分析系统（金融场景版）

基于 **chat-to-qa Skill** 的钉钉群聊数据分析工具，专为金融场景设计，从零散的聊天记录中智能提取问答对并自动分类标签，支持定时同步和 FastGPT 知识库导入。

## 📋 核心功能

### 1. 获取群聊数据
- 获取钉钉群聊历史消息
- 支持文本、图片、富文本消息
- 识别发送者角色（客户、技术支持、业务经理等）
- 支持增量同步（避免重复处理）

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

### 4. FastGPT 知识库集成
- 导出 FastGPT 导入格式
- 支持直接导入 FastGPT 知识库
- 支持创建知识库集合
- 多格式导出（JSON、CSV、Markdown）

### 5. 定时同步服务
- 每日自动同步昨天的聊天数据
- 支持自定义同步时间
- 后台守护进程模式

## 🚀 快速开始

### 1. 安装依赖

```bash
cd dingding-skills
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 钉钉配置
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret
DINGTALK_ACCESS_TOKEN=your_access_token

# 大模型配置
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_llm_key
LLM_MODEL=gpt-4

# FastGPT 配置（用于导入知识库）
FASTGPT_API_URL=https://api.fastgpt.in
FASTGPT_API_KEY=your_fastgpt_key
FASTGPT_DATASET_ID=your_dataset_id

# 同步配置
SYNC_HOUR=0
SYNC_MINUTE=0
SYNC_BATCH_SIZE=100
SYNC_MAX_MESSAGES=1000

# 应用配置
APP_MODE=production
LOG_LEVEL=INFO
```

### 3. 使用方式

#### 方式一： 单次执行

```bash
# 执行一次同步
python start_sync.py --mode once --real

# 指定 FastGPT 配置
python start_sync.py \
    --mode once \
    --fastgpt-key YOUR_KEY \
    --fastgpt-dataset YOUR_DATASET_ID \
    --real
```

#### 方式二: 定时调度

```bash
# 每日 0 点执行
python start_sync.py --mode schedule --hour 0 --minute 0 --real

# 每日 6 点执行
python start_sync.py --mode schedule --hour 6 --minute 0 --real
```

#### 方式三: 后台守护进程

```bash
# 启动后台服务（使用 PM2 管理）
pm2 start start_sync.py --name dingding-sync -- --mode daemon
```

#### 方式四: 使用主程序

```bash
# 完整流程
python main.py --action all

# 导入到 FastGPT
python main.py --action fastgpt \
    --fastgpt-key YOUR_KEY \
    --fastgpt-dataset YOUR_DATASET_ID
```

## 📁 项目结构

```
dingding-skills/
├── main.py                          # 主程序入口
├── start_sync.py                   # 定时同步入口
├── config.py                        # 配置管理
├── scheduler.py                     # 定时调度器
├── requirements.txt                 # 依赖
├── api/
│   └── dingtalk_api.py             # 钉钉 API 封装
├── skills/
│   └── chat-to-qa/                  # chat-to-qa Skill
│       ├── SKILL.md                 # Skill 定义
│       ├── scripts/
│       │   ├── qa_extractor.py      # QA 提取
│       │   └── fastgpt_importer.py  # FastGPT 导入
│       ├── templates/
│       │   └── qa_template.json     # QA 模板
│       └── resources/
│           └── categories.json      # 分类定义
└── output/
    ├── knowledge_base/              # 输出目录
    │   ├── qa_full.json             # 完整数据
    │   ├── fastgpt_import.json      # FastGPT 导入格式
    │   └── sync_record.json         # 同步记录
    └── logs/                         # 日志目录
```

## 💡 FastGPT 集成

### 1. FastGPT API 配置

在 FastGPT 中创建知识库，获取以下配置：
- Dataset ID: 知识库 ID
- API Key: API 密钥

### 2. 导入格式

FastGPT 要求的 JSON 格式：

```json
{
  "list": [
    {
      "q": "上海银行签署借款合同提示：验证码初始化异常怎么办？",
      "a": "验证码输错6次后会出现此报错提示。请重新尝试，输入正确的验证码即可。",
      "tags": ["金融", "系统"]
    }
  ]
}
```

### 3. 使用 FastGPT

1. 在 FastGPT 中创建知识库
2. 获取 Dataset ID 和 API Key
3. 配置环境变量或命令行参数
4. 执行同步脚本

## 📊 输出文件

### qa_full.json - 完整 QA 数据

```json
{
  "qa_list": [...],
  "fastgpt_list": [...],
  "statistics": {
    "total_count": 10,
    "by_category": {
      "finance": 5,
      "system": 3,
      "other": 2
    }
  }
}
```

### sync_record.json - 同步记录

```json
{
  "last_sync_time": "2024-01-15T00:00:00",
  "processed_msg_ids": ["msg_001", "msg_002"],
  "daily_stats": {
    "2024-01-14": {
      "total": 100,
      "qa_generated": 10
    }
  }
}
```

## 🔧 部署方案

### 方案一: Cron 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天 0 点执行）
0 0 * * * cd /path/to/dingding-skills && python start_sync.py --mode once --real
```

### 方案二: Systemd 服务

创建 `/etc/systemd/system/dingding-sync.service`:

```ini
[Unit]
Description=DingDing Sync Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/dingding-skills
ExecStart=/usr/bin/python3 start_sync.py --mode schedule --hour 0 --real
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl enable dingding-sync
sudo systemctl start dingding-sync
```

### 方案三: Docker 部署

创建 `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "start_sync.py", "--mode", "schedule", "--hour", "0", "--real"]
```

构建和运行:

```bash
docker build -t dingding-sync .
docker run -d --env-file .env dingding-sync
```

### 方案四: PM2 进程管理

```bash
# 安装 PM2
npm install -g pm2

# 启动服务
pm2 start start_sync.py --name dingding-sync -- --mode daemon --real

# 设置开机自启
pm2 startup
pm2 save
```

## 📝 日志查看

```bash
# 查看日志
tail -f output/logs/sync.log
```

## 📄 License

MIT License
