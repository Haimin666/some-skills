# FastGPT 工作流集成指南

本文档说明如何在 FastGPT 工作台中创建工作流，调用钉钉 QA 提取服务。

## 📋 前置准备

### 1. 启动 API 服务

```bash
cd dingding-skills
pip install fastapi uvicorn
python api_server.py --port 8080
```

服务启动后可访问：
- API 地址: `http://localhost:8080`
- API 文档: `http://localhost:8080/docs`

### 2. 确认服务正常

```bash
# 健康检查
curl http://localhost:8080/api/health

# 获取 QA 数据
curl http://localhost:8080/api/fastgpt/qa?days=1
```

---

## 🔧 方案一：简单工作流（推荐）

### 步骤 1：创建新工作流

在 FastGPT 工作台创建新工作流，名称如"钉钉QA同步"

### 步骤 2：添加定时触发器

如果 FastGPT 支持，添加定时触发器：
- 触发时间：每日 00:00
- 或手动触发

### 步骤 3：添加 HTTP 请求节点

配置 HTTP 请求节点：

```
节点名称: 获取QA数据
请求方式: GET
请求地址: http://your-server:8080/api/fastgpt/qa?days=1
超时时间: 60秒
```

### 步骤 4：处理返回数据

添加"数据处理"节点，从 HTTP 响应中提取 `list` 字段：

```javascript
// 表达式
{{httpResponse.list}}
```

### 步骤 5：导入知识库

添加"知识库导入"节点：
- 选择目标知识库
- 数据源：上一步处理的数据
- 格式：标准 QA 格式

### 工作流图示

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  定时触发   │ ──▶ │ HTTP 请求   │ ──▶ │ 数据处理    │ ──▶ │ 知识库导入  │
│  每日0点    │     │ 获取QA数据  │     │ 提取list    │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## 🔧 方案二：完整工作流

### 工作流节点配置

#### 节点 1：开始节点
- 类型：手动触发 或 定时触发

#### 节点 2：HTTP 请求 - 获取消息
```json
{
  "name": "获取聊天消息",
  "method": "GET",
  "url": "http://your-server:8080/api/messages",
  "params": {
    "start_date": "{{dateFormat yesterday 'YYYY-MM-DD'}}",
    "end_date": "{{dateFormat today 'YYYY-MM-DD'}}"
  }
}
```

#### 节点 3：HTTP 请求 - 提取 QA
```json
{
  "name": "提取QA",
  "method": "POST",
  "url": "http://your-server:8080/api/extract-qa",
  "body": {
    "messages": "{{node2.messages}}",
    "group_name": "金融业务群"
  }
}
```

#### 节点 4：数据处理
```javascript
// 提取 FastGPT 格式数据
return {
  list: node3.fastgpt_list,
  total: node3.statistics.total_count
};
```

#### 节点 5：条件判断
```javascript
// 判断是否有新 QA
if (node4.total > 0) {
  return "有数据";
} else {
  return "无数据";
}
```

#### 节点 6：知识库导入（条件：有数据）
```json
{
  "datasetId": "your_dataset_id",
  "data": "{{node4.list}}"
}
```

#### 节点 7：结束节点
- 输出：导入结果统计

---

## 🔧 方案三：Webhook 触发

如果需要外部触发（如钉钉机器人回调），可以配置 Webhook：

### 1. 配置 Webhook 接收节点

在 FastGPT 工作流中添加 Webhook 触发节点，获取 Webhook URL

### 2. 配置钉钉机器人

在钉钉群中添加自定义机器人，配置 Outgoing：
- URL: FastGPT Webhook URL
- 触发关键词: 配置需要的关键词

### 3. 工作流处理

```
Webhook 接收 -> 解析消息 -> HTTP 调用提取 QA -> 导入知识库
```

---

## 📊 API 返回格式说明

### `/api/fastgpt/qa` 返回格式

```json
{
  "list": [
    {
      "q": "上海银行签署借款合同提示：验证码初始化异常怎么办？",
      "a": "验证码输错6次后会出现此报错提示。请重新尝试，输入正确的验证码即可。",
      "tags": ["金融", "系统"]
    },
    {
      "q": "请问借款合同签署后多久可以放款？",
      "a": "正常情况下，合同签署完成后1-3个工作日放款，具体时间取决于银行审核进度。",
      "tags": ["金融"]
    }
  ],
  "total": 2,
  "sync_time": "2024-01-15T10:30:00",
  "statistics": {
    "total_count": 2,
    "by_category": {
      "finance": 1,
      "system": 1
    },
    "by_tags": {
      "金融": 2,
      "系统": 1
    }
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| list | Array | QA 列表，FastGPT 知识库可直接使用 |
| q | String | 问题 |
| a | String | 答案 |
| tags | Array | 标签，如 ["金融", "系统"] |
| total | Number | QA 总数 |
| sync_time | String | 同步时间 |
| statistics | Object | 统计信息 |

---

## 🚀 生产部署建议

### 1. 内网部署

API 服务部署在内网，FastGPT 通过内网地址调用：

```bash
# 内网部署
python api_server.py --host 10.0.0.100 --port 8080

# FastGPT 调用地址
http://10.0.0.100:8080/api/fastgpt/qa
```

### 2. 认证保护

添加 API Key 认证：

```python
# 在 api_server.py 中添加
from fastapi import Header, HTTPException

@app.get("/api/fastgpt/qa")
async def get_fastgpt_qa(
    days: int = 1,
    authorization: str = Header(None),
):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # ...原有逻辑
```

FastGPT 调用时添加 Header：
```
Authorization: Bearer your_api_key
```

### 3. 公网部署

如需公网访问，使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📝 常见问题

### Q1: FastGPT 工作流没有定时触发器？

A: 可以使用外部定时任务调用 FastGPT 的 API 触发工作流：

```bash
# crontab
0 0 * * * curl -X POST https://fastgpt.yourdomain.com/api/workflow/trigger \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{"workflowId": "xxx"}'
```

### Q2: 如何处理大量数据？

A: API 支持分页，工作流中循环处理：

```
循环调用:
GET /api/fastgpt/qa?days=1&offset=0&limit=100
GET /api/fastgpt/qa?days=1&offset=100&limit=100
...
```

### Q3: 如何避免重复导入？

A: API 返回 `sync_time`，可以记录上次同步时间：

```javascript
// FastGPT 工作流中存储上次的 sync_time
// 下次调用时检查
if (new_sync_time > last_sync_time) {
  // 导入新数据
}
```

---

## 🔗 相关链接

- FastGPT 官方文档: https://doc.fastgpt.in/
- API 服务代码: `dingding-skills/api_server.py`
- 完整项目: https://github.com/Haimin666/some-skills
