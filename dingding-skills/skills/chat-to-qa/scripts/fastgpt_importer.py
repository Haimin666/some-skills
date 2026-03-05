# encoding: utf-8
import requests
import json
import os
import urllib.parse  # 引入 urllib.parse

# 1. 设置 API 地址和认证信息
url = "https://alg-fastgpt.corp.shiqiao.com/api/core/dataset/collection/create/localFile"
api_key = "xxx"  # 请替换为你的真实 API Key

headers = {
    "Authorization": f"Bearer {api_key}"
}

# 2. 准备文件路径
file_path = "/Users/lbc/Downloads/答疑文档更新2026-3-5.csv"

# 3. 准备 data 字段的数据
payload = {
    "datasetId": "69a9186ad9aab1e5fb351c37",
    "parentId": None,
    "trainingType": "qa",
    "chunkSize": 512,
    "chunkSplitter": "",
    "qaPrompt": "第一列为q第二列为a",
    "metadata": {},
    "chunkSettingMode": "auto"
}

try:
    # 4. 关键步骤：手动对文件名进行 URL 编码
    # 获取原始文件名
    original_filename = os.path.basename(file_path)
    # 将中文文件名编码为 %E7%AD%94%E7%96%91... 格式
    # safe='' 表示连特殊字符也编码，通常文件名建议保留空格不编码，或者根据后端习惯调整
    encoded_filename = urllib.parse.quote(original_filename)

    print(f"原始文件名: {original_filename}")
    print(f"编码后文件名: {encoded_filename}")

    with open(file_path, 'rb') as f:
        # 在 files 参数中使用编码后的文件名
        # requests 看到是 ASCII 字符串，就不会再添加额外的 charset 头信息
        files = {
            'file': (encoded_filename, f, 'text/csv')
        }

        # data 字段转换
        data = {
            'data': json.dumps(payload, ensure_ascii=False)
        }

        # 5. 发送请求
        response = requests.post(url, headers=headers, data=data, files=files)

        print(f"Status Code: {response.status_code}")
        print("Response Body:", response.text)

except FileNotFoundError:
    print(f"错误：找不到文件 {file_path}")
except Exception as e:
    print(f"请求发生错误: {e}")