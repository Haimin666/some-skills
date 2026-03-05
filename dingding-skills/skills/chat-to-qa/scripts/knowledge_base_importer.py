"""
Knowledge Base Importer - 将 QA 导入知识库

支持多种格式导出，便于集成到不同的知识库系统
"""

import json
import csv
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path


class KnowledgeBaseImporter:
    """
    知识库导入器

    将提取的 QA 数据转换为知识库格式并导出
    """

    def __init__(self, output_dir: str = "output/knowledge_base"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def import_qa_data(
        self,
        qa_data: Dict[str, Any],
        source: str = "钉钉群聊",
        formats: List[str] = ["json", "csv", "markdown"],
    ) -> Dict[str, str]:
        """
        导入 QA 数据到知识库

        Args:
            qa_data: 包含 qa_list 的数据
            source: 数据来源
            formats: 导出格式列表

        Returns:
            导出的文件路径字典
        """
        qa_list = qa_data.get("qa_list", [])
        exported_files = {}

        # 添加来源信息
        for qa in qa_list:
            qa["source"] = source

        if "json" in formats:
            exported_files["json"] = str(self._export_json(qa_data))

        if "csv" in formats:
            exported_files["csv"] = str(self._export_csv(qa_list))

        if "markdown" in formats:
            exported_files["markdown"] = str(self._export_markdown(qa_list))

        # 按分类导出
        exported_files["by_category"] = str(self._export_by_category(qa_list))

        return exported_files

    def _export_json(self, qa_data: Dict[str, Any]) -> Path:
        """导出 JSON 格式"""
        output_path = self.output_dir / "knowledge_base.json"

        data = {
            **qa_data,
            "exported_at": datetime.now().isoformat(),
        }

        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return output_path

    def _export_csv(self, qa_list: List[Dict]) -> Path:
        """导出 CSV 格式"""
        output_path = self.output_dir / "knowledge_base.csv"

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "问题", "答案", "分类", "分类名称",
                "严重级别", "关键词", "置信度", "来源", "上下文"
            ])

            for qa in qa_list:
                writer.writerow([
                    qa.get("id", ""),
                    qa.get("question", ""),
                    qa.get("answer", ""),
                    qa.get("category", ""),
                    qa.get("category_name", ""),
                    qa.get("severity", ""),
                    ", ".join(qa.get("keywords", [])),
                    qa.get("confidence", ""),
                    qa.get("source", ""),
                    qa.get("context", ""),
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

        for category, items in by_category.items():
            category_name = items[0].get("category_name", category) if items else category
            lines.extend([
                f"## {category_name}",
                "",
                f"共 {len(items)} 条",
                "",
            ])

            for i, qa in enumerate(items, 1):
                lines.extend([
                    f"### Q{i}: {qa.get('question', '')}",
                    "",
                    f"**答案**: {qa.get('answer', '')}",
                    "",
                    f"**严重级别**: {qa.get('severity', 'medium')}",
                    f"**置信度**: {qa.get('confidence', 0):.0%}",
                    f"**关键词**: {', '.join(qa.get('keywords', [])) or '无'}",
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

        for category, items in by_category.items():
            category_name = items[0].get("category_name", category) if items else category
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


def import_to_knowledge_base(
    qa_data: Dict[str, Any],
    output_dir: str = "output/knowledge_base",
    formats: List[str] = ["json", "csv", "markdown"],
) -> Dict[str, str]:
    """便捷函数：导入知识库"""
    importer = KnowledgeBaseImporter(output_dir)
    return importer.import_qa_data(qa_data, formats=formats)
