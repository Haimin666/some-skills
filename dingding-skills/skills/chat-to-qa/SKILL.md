---
name: chat-to-qa
description: 从金融场景的钉钉群聊记录中智能提取问答对(QA)，自动分类标签（金融、系统、其他），支持理解上下文、人员、图片等信息，输出适配 FastGpt 知识库格式。
---

# Chat to QA Skill (金融场景版)

从金融业务群聊对话中智能提取问答对，理解上下文语义、识别人员角色、解析图片信息，生成结构化的 QA 并自动分类标签，可直接导入 FastGpt 知识库。

## When to Use This Skill

- 从金融业务群聊中提取有价值的问答信息
- 识别系统Bug和金融业务问题
- 需要理解上下文、人员、图片的复杂场景
- 将聊天记录转化为 FastGpt 知识库内容
- 构建金融客服智能问答系统

## Prerequisites

- 钉钉群聊数据（包含消息内容、发送者、时间、图片等）
- 大模型 API 访问权限（支持上下文理解和图片分析）
- FastGpt 知识库 API（可选，用于自动导入）

## Instructions

### 1. 数据输入格式

钉钉群聊消息包含以下字段：

```json
{
  "openConversationId": "cidmfWxxxx",
  "groupName": "金融业务群",
  "groupOwner": "群主名称",
  "messages": [
    {
      "msgId": "消息唯一标识",
      "senderId": "发送者ID",
      "senderName": "发送者名称",
      "senderRole": "角色（客户/客服/技术支持）",
      "content": "消息文本内容",
      "msgType": "text/picture/richText",
      "picURL": "图片地址（如有）",
      "createTime": 123000000
    }
  ]
}
```

### 2. 上下文理解规则

#### 2.1 识别问题和答案

**问题识别：**
- 包含疑问词：怎么、如何、为什么、能不能、可以、是否、什么
- 包含问号：？、?
- 报告异常或错误：提示、报错、异常、失败
- 金融业务咨询：合同、贷款、借款、签署、验证等

**答案识别：**
- 直接回答问题的内容
- 提供解决方案的描述
- 解释原因或操作步骤
- 技术支持或客服的回复

#### 2.2 人员角色理解

根据消息内容和发送者判断角色：
- **客户**：提出问题、反馈异常
- **客服**：回答问题、提供指导
- **技术支持**：解决技术问题、排查Bug
- **业务人员**：解释业务规则、流程

#### 2.3 图片信息处理

当消息包含图片时：
1. 使用 VLM 能力识别图片内容
2. 将图片关键信息融入上下文
3. 在 QA 中注明图片相关内容（如：截图显示...）

### 3. 分类标签体系（金融场景）

| 标签 | 标识 | 说明 | 识别关键词 |
|------|------|------|------------|
| 金融 | finance | 金融业务相关问题 | 合同、借款、贷款、签署、银行、验证码、交易、账户、金额、还款 |
| 系统 | system | 系统Bug、技术问题 | 报错、异常、崩溃、失败、超时、验证码初始化、接口、网络 |
| 其他 | other | 不属于以上分类 | - |

### 4. 输出格式（FastGpt 适配）

```json
{
  "qa_list": [
    {
      "id": "qa_唯一标识",
      "question": "整理后的问题内容",
      "answer": "整理后的答案内容",
      "tags": ["金融", "系统"],
      "category": "primary_category",
      "confidence": 0.95,
      "context": {
        "questioner": "提问者名称",
        "answerer": "回答者名称",
        "group_name": "群聊名称",
        "has_image": false,
        "image_desc": "图片描述（如有）",
        "source_time": "2024-01-01 10:00:00"
      },
      "keywords": ["关键词列表"],
      "severity": "high/medium/low"
    }
  ],
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

### 5. FastGpt 知识库导入格式

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

### 6. 处理流程

```
钉钉群聊数据
    │
    ▼
消息解析（文本、图片、富文本）
    │
    ▼
上下文理解
├── 识别人员角色
├── 理解对话意图
└── 处理图片信息（如有）
    │
    ▼
QA 候选识别
├── 问题检测
├── 答案匹配
└── 多消息合并
    │
    ▼
分类标签判断
├── 金融业务问题
├── 系统技术问题
└── 其他问题
    │
    ▼
输出结构化 QA（FastGpt 格式）
    │
    ▼
导入 FastGpt 知识库
```

## Examples

### Example 1: 金融系统问题

**输入聊天记录：**
```
[10:00] 客户A: 上海银行 签署【借款合同】提示：验证码初始化异常
[10:01] 客户A: [图片：错误提示截图]
[10:02] 技术支持: 验证码输错6次，验证码输错6次会有这个报错提示
[10:03] 技术支持: 请重试，输入正确验证码就可以了
[10:05] 客户A: 好的，我试试
[10:10] 客户A: 可以了，谢谢
```

**输出 QA：**
```json
{
  "id": "qa_001",
  "question": "上海银行签署借款合同提示：验证码初始化异常怎么办？",
  "answer": "验证码输错6次后会出现此报错提示。请重新尝试，输入正确的验证码即可正常完成签署。",
  "tags": ["金融", "系统"],
  "category": "finance",
  "confidence": 0.95,
  "context": {
    "questioner": "客户A",
    "answerer": "技术支持",
    "group_name": "金融业务群",
    "has_image": true,
    "image_desc": "错误提示截图，显示验证码初始化异常",
    "source_time": "2024-01-01 10:00"
  },
  "keywords": ["借款合同", "验证码", "上海银行", "签署"],
  "severity": "medium"
}
```

### Example 2: 纯金融业务问题

**输入聊天记录：**
```
[14:00] 客户B: 请问借款合同签署后多久可以放款？
[14:01] 业务经理: 正常情况下，合同签署完成后1-3个工作日放款
[14:02] 业务经理: 具体时间取决于银行审核进度
```

**输出 QA：**
```json
{
  "id": "qa_002",
  "question": "借款合同签署后多久可以放款？",
  "answer": "正常情况下，合同签署完成后1-3个工作日放款，具体时间取决于银行审核进度。",
  "tags": ["金融"],
  "category": "finance",
  "confidence": 0.98,
  "context": {
    "questioner": "客户B",
    "answerer": "业务经理",
    "group_name": "金融业务群",
    "has_image": false
  },
  "keywords": ["借款合同", "放款", "银行审核"],
  "severity": "low"
}
```

### Example 3: 纯系统问题

**输入聊天记录：**
```
[09:00] 客户C: 系统登录一直转圈，进不去
[09:02] 技术支持: 现在服务器在升级，预计10分钟后恢复
[09:02] 技术支持: 请稍后再试
[09:15] 客户C: 可以了
```

**输出 QA：**
```json
{
  "id": "qa_003",
  "question": "系统登录一直转圈进不去怎么办？",
  "answer": "可能是服务器正在升级维护，请等待几分钟后重新尝试登录。如问题持续，请联系技术支持。",
  "tags": ["系统"],
  "category": "system",
  "confidence": 0.90,
  "context": {
    "questioner": "客户C",
    "answerer": "技术支持",
    "has_image": false
  },
  "keywords": ["登录", "系统", "服务器"],
  "severity": "high"
}
```

## Error Handling

### 常见问题处理

1. **消息不完整**
   - 只有问题没有答案：标记为待补充，记录到待处理列表
   - 只有答案没有问题：尝试从上下文推断问题

2. **分类不确定**
   - 同时涉及金融和系统：打上两个标签 `["金融", "系统"]`
   - 无法确定：标记为 "其他"

3. **图片解析失败**
   - 记录图片 URL，标注 "图片待处理"
   - 根据上下文推断图片内容

4. **多人对话混乱**
   - 按时间线梳理对话
   - 使用 @ 提及和回复关系判断对话配对

## FastGpt Integration

### 导入到 FastGpt 知识库

```python
# FastGpt API 调用示例
import requests

def import_to_fastgpt(qa_list, dataset_id, api_key):
    """导入 QA 到 FastGpt 知识库"""
    url = f"https://api.fastgpt.in/api/v1/dataset/data/list"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data_list = [
        {
            "q": qa["question"],
            "a": qa["answer"],
            "tags": qa["tags"]
        }
        for qa in qa_list
    ]
    
    payload = {
        "datasetId": dataset_id,
        "data": data_list
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.json()
```

## Output Files

生成的文件：
1. `qa_full.json` - 完整 QA 数据（含上下文信息）
2. `fastgpt_import.json` - FastGpt 导入格式
3. `qa_statistics.json` - 统计分析报告
4. `by_category/` - 按分类组织的 QA 文件
