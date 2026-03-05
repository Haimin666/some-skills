"""
FastGpt Knowledge Base Importer

将 QA 数据导入 FastGpt 知识库
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import aiohttp


class FastGptImporter:
    """
    FastGpt 知识库导入器
    
    支持将 QA 数据导入到 FastGpt 知识库
    """
    
    def __init__(
        self,
        api_base_url: str = "https://api.fastgpt.in",
        api_key: str = "",
        dataset_id: str = "",
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
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
                timeout=aiohttp.ClientTimeout(total=60),
            )
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def import_qa_list(
        self,
        qa_list: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        导入 QA 列表到 FastGpt 知识库
        
        Args:
            qa_list: QA 列表（FastGpt 格式）
            batch_size: 批量导入大小
        
        Returns:
            导入结果
        """
        await self._init_session()
        
        imported_count = 0
        failed_count = 0
        errors = []
        
        # 分批导入
        for i in range(0, len(qa_list), batch_size):
            batch = qa_list[i:i + batch_size]
            
            try:
                result = await self._import_batch(batch)
                imported_count += len(batch)
            except Exception as e:
                failed_count += len(batch)
                errors.append({
                    "batch": i // batch_size,
                    "error": str(e),
                })
        
        return {
            "total": len(qa_list),
            "imported": imported_count,
            "failed": failed_count,
            "errors": errors,
        }
    
    async def _import_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """导入一批数据"""
        url = f"{self.api_base_url}/api/v1/dataset/data/list"
        
        payload = {
            "datasetId": self.dataset_id,
            "data": batch,
        }
        
        async with self._session.post(url, json=payload) as response:
            response.raise_for_status()
            return await response.json()


class KnowledgeBaseExporter:
    """
    知识库导出器
    
    支持多种格式导出 QA 数据
    """
    
    def __init__(self, output_dir: str = "output/knowledge_base"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        qa_data: Dict[str, Any],
        source: str = "钉钉群聊",
    ) -> Dict[str, str]:
        """
        导出所有格式
        
        Args:
            qa_data: QA 数据（包含 qa_list, fastgpt_list, statistics）
            source: 数据来源
        
        Returns:
            导出的文件路径字典
        """
        exported_files = {}
        
        # 1. 完整 JSON 格式
        exported_files["full_json"] = str(self._export_full_json(qa_data, source))
        
        # 2. FastGpt 导入格式
        exported_files["fastgpt"] = str(self._export_fastgpt(qa_data))
        
        # 3. CSV 格式
        exported_files["csv"] = str(self._export_csv(qa_data.get("qa_list", [])))
        
        # 4. Markdown 格式
        exported_files["markdown"] = str(self._export_markdown(qa_data.get("qa_list", [])))
        
        # 5. 按分类导出
        exported_files["by_category"] = str(self._export_by_category(qa_data.get("qa_list", [])))
        
        return exported_files

    def _export_full_json(self, qa_data: Dict[str, Any], source: str) -> Path:
        """导出完整 JSON"""
        output_path = self.output_dir / "qa_full.json"
        
        data = {
            **qa_data,
            "source": source,
            "exported_at": datetime.now().isoformat(),
        }
        
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return output_path

    def _export_fastgpt(self, qa_data: Dict[str, Any]) -> Path:
        """导出 FastGpt 格式"""
        output_path = self.output_dir / "fastgpt_import.json"
        
        fastgpt_list = qa_data.get("fastgpt_list", [])
        
        data = {
            "list": fastgpt_list,
            "total": len(fastgpt_list),
            "exported_at": datetime.now().isoformat(),
        }
        
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return output_path

    def _export_csv(self, qa_list: List[Dict]) -> Path:
        """导出 CSV 格式"""
        import csv
        
        output_path = self.output_dir / "knowledge_base.csv"
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "问题", "答案", "标签", "分类",
                "严重级别", "关键词", "置信度", "提问者", "回答者", "来源时间"
            ])
            
            for qa in qa_list:
                context = qa.get("context", {})
                writer.writerow([
                    qa.get("id", ""),
                    qa.get("question", ""),
                    qa.get("answer", ""),
                    ", ".join(qa.get("tags", [])),
                    qa.get("category", ""),
                    qa.get("severity", ""),
                    ", ".join(qa.get("keywords", [])),
                    qa.get("confidence", ""),
                    context.get("questioner", ""),
                    context.get("answerer", ""),
                    context.get("source_time", ""),
                ])
        
        return output_path

    def _export_markdown(self, qa_list: List[Dict]) -> Path:
        """导出 Markdown 格式"""
        output_path = self.output_dir / "knowledge_base.md"
        
        lines = [
            "# QA 知识库",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总数: {len(qa_list)} 条",
            "",
        ]
        
        # 按分类组织
        by_category = {}
        for qa in qa_list:
            cat = qa.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(qa)
        
        category_names = {
            "finance": "金融",
            "system": "系统",
            "other": "其他",
        }
        
        for category, items in by_category.items():
            category_name = category_names.get(category, category)
            lines.extend([
                f"## {category_name}",
                "",
                f"共 {len(items)} 条",
                "",
            ])
            
            for i, qa in enumerate(items, 1):
                context = qa.get("context", {})
                tags = ", ".join(qa.get("tags", []))
                
                lines.extend([
                    f"### Q{i}: {qa.get('question', '')}",
                    "",
                    f"**答案**: {qa.get('answer', '')}",
                    "",
                    f"**标签**: {tags}",
                    f"**严重级别**: {qa.get('severity', 'medium')}",
                    f"**置信度**: {qa.get('confidence', 0):.0%}",
                    f"**提问者**: {context.get('questioner', '未知')}",
                    f"**回答者**: {context.get('answerer', '未知')}",
                    "",
                    "---",
                    "",
                ])
        
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def _export_by_category(self, qa_list: List[Dict]) -> Path:
        """按分类导出"""
        category_dir = self.output_dir / "by_category"
        category_dir.mkdir(parents=True, exist_ok=True)
        
        by_category = {}
        for qa in qa_list:
            cat = qa.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(qa)
        
        category_names = {
            "finance": "金融",
            "system": "系统",
            "other": "其他",
        }
        
        for category, items in by_category.items():
            category_name = category_names.get(category, category)
            file_path = category_dir / f"{category}.json"
            
            data = {
                "category": category,
                "category_name": category_name,
                "count": len(items),
                "items": items,
                "exported_at": datetime.now().isoformat(),
            }
            
            file_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        
        return category_dir


async def export_to_knowledge_base(
    qa_data: Dict[str, Any],
    output_dir: str = "output/knowledge_base",
    source: str = "钉钉群聊",
) -> Dict[str, str]:
    """便捷函数：导出到知识库"""
    exporter = KnowledgeBaseExporter(output_dir)
    return exporter.export_all(qa_data, source)


async def import_to_fastgpt(
    qa_data: Dict[str, Any],
    api_key: str,
    dataset_id: str,
    api_base_url: str = "https://api.fastgpt.in",
) -> Dict[str, Any]:
    """便捷函数：导入到 FastGpt"""
    fastgpt_list = qa_data.get("fastgpt_list", [])
    
    async with FastGptImporter(api_base_url, api_key, dataset_id) as importer:
        return await importer.import_qa_list(fastgpt_list)
