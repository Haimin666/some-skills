# 钉钉群聊 QA 提取工具

从钉钉群聊中提取问答对，输出 CSV 文件用于知识库导入。

## 快速开始

```bash
# 安装依赖
pip install rich

# 使用模拟数据测试
python main.py

# 使用真实钉钉 API
python main.py --real

# 指定输出文件
python main.py --output my_qa.csv
```

## 输出格式

CSV 文件包含两列：

| q | a |
|---|---|
| 上海银行签署借款合同提示：验证码初始化异常怎么办？ | 验证码输错6次后会出现此报错提示，请重新尝试。 |
| 借款合同签署后多久可以放款？ | 正常情况下1-3个工作日放款，具体看银行审核进度。 |

## 项目结构

```
dingding-skills/
├── main.py                    # 主程序
├── skills/chat-to-qa/
│   ├── SKILL.md              # Skill 定义（给 AI 的规则说明）
│   └── qa_extractor.py       # QA 提取实现
├── api/
│   └── dingtalk_api.py       # 钉钉 API（用户已调试好）
└── output/                    # CSV 输出目录
```

## 分类标签

根据 SKILL.md 定义，自动分类：

- **金融**: 合同、借款、贷款、银行、验证码等
- **系统**: 报错、异常、崩溃、超时、登录等  
- **其他**: 不属于以上分类

## 使用流程

```
钉钉群聊 → 获取消息 → 提取 QA → 导出 CSV
```

## 文件说明

- `skills/chat-to-qa/SKILL.md` - 定义 QA 提取规则（这是 Skill 的核心）
- `skills/chat-to-qa/qa_extractor.py` - 实现提取逻辑
- `api/dingtalk_api.py` - 钉钉 API 调用（用户已实现）
