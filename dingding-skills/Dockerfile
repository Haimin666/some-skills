FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建输出目录
RUN mkdir -p /app/output/knowledge_base /app/output/logs

# 设置时区
ENV TZ=Asia/Shanghai

# 启动服务
CMD ["python", "start_sync.py", "--mode", "schedule", "--hour", "0", "--real"]
