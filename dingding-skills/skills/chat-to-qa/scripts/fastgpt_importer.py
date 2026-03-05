"""
FastGPT 知识库导入器

适配 FastGPT 的 API 格式，支持创建知识库集合和数据导入
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import aiohttp
from rich.console import Console

console = Console()


class FastGptImporter:
    """
    FastGPT 知识库导入器
    
    FastGPT API 文档: https://doc.fastgpt.in/
    """
    
    def __init__(
        self,
        api_key: str,
        api_url: str = "https://api.fastgpt.in",
        dataset_id: str = "",
    ):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.dataset_id = dataset_id
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _init_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=120),
            )
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def import_data(
        self,
        qa_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        导入 QA 数据到 FastGPT 知识库
        
        FastGPT API 格式：
        POST /api/v1/dataset/data/list
        {
            "datasetId": "xxx",
            "data": [
                {
                    "q": "问题",
                    "a": "答案",
                    "tags": ["标签1", "标签2"]
                }
            ]
        }
        
        Args:
            qa_list: QA 列表，格式: [{"q": "", "a": "", "tags": []}]
        
        Returns:
            导入结果
        """
        if not qa_list:
            return {"total": 0, "inserted": 0}
        
        await self._init_session()
        
        url = f"{self.api_url}/api/v1/dataset/data/list"
        
        payload = {
            "datasetId": self.dataset_id,
            "data": qa_list
        }
        
        try:
            async with self._session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                
                console.print(f"[green]成功导入 {len(qa_list)} 条 QA 到 FastGPT[/green]")
                
                return {
                    "total": len(qa_list),
                    "result": result
                }
        except Exception as e:
            console.print(f"[red]FastGPT 导入失败: {e}[/red]")
            raise
    
    async def create_collection(
        self,
        name: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        创建知识库集合
        
        Args:
            name: 集合名称
            description: 集合描述
        
        Returns:
            创建结果
        """
        await self._init_session()
        
        url = f"{self.api_url}/api/v1/dataset/collection/create"
        
        payload = {
            "datasetId": self.dataset_id,
            "name": name,
            "description": description or f"钉钉群聊 QA - {datetime.now().strftime('%Y-%m-%d')}"
        }
        
        try:
            async with self._session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                
                console.print(f"[green]创建知识库集合成功: {result.get('data', {}).get('_id', '')}[/green]")
                
                return result
        except Exception as e:
            console.print(f"[red]创建集合失败: {e}[/red]")
            raise
    
    async def import_to_collection(
        self,
        collection_id: str,
        qa_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        导入数据到指定集合
        
        Args:
            collection_id: 集合 ID
            qa_list: QA 列表
        
        Returns:
            导入结果
        """
        if not qa_list:
            return {"total": 0, "inserted": 0}
        
        await self._init_session()
        
        url = f"{self.api_url}/api/v1/dataset/data/list"
        
        payload = {
            "datasetId": self.dataset_id,
            "collectionId": collection_id,
            "data": qa_list
        }
        
        try:
            async with self._session.post(url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()
                
                console.print(f"[green]成功导入 {len(qa_list)} 条 QA[/green]")
                
                return {
                    "total": len(qa_list),
                    "result": result
                }
        except Exception as e:
            console.print(f"[red]导入失败: {e}[/red]")
            raise


def format_qa_for_fastgpt(qa_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    格式化 QA 数据为 FastGPT 格式
    
    Args:
        qa_data: QA 数据（包含 qa_list 或 fastgpt_list）
    
    Returns:
        FastGPT 格式的 QA 列表
    """
    # 优先使用 fastgpt_list
    if "fastgpt_list" in qa_data:
        return qa_data["fastgpt_list"]
    
    # 否则从 qa_list 转换
    qa_list = qa_data.get("qa_list", [])
    return [
        {
            "q": qa.get("question", ""),
            "a": qa.get("answer", ""),
            "tags": qa.get("tags", []),
        }
        for qa in qa_list
    ]


async def import_to_fastgpt(
    qa_data: Dict[str, Any],
    api_key: str,
    dataset_id: str,
    api_url: str = "https://api.fastgpt.in",
) -> Dict[str, Any]:
    """
    便捷函数: 导入 QA 到 FastGPT
    
    Args:
        qa_data: QA 数据
        api_key: FastGPT API Key
        dataset_id: 数据集 ID
        api_url: FastGPT API URL
    
    Returns:
        导入结果
    """
    fastgpt_list = format_qa_for_fastgpt(qa_data)
    
    async with FastGptImporter(api_key, api_url, dataset_id) as importer:
        return await importer.import_data(fastgpt_list)
