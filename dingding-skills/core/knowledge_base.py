"""
知识库管理模块

管理 QA 知识库的导入、导出和查询
"""

import json
import csv
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from config import config, get_output_path
from core.qa_classifier import ClassifiedQA


@dataclass
class KnowledgeEntry:
    """知识条目"""
    id: str
    question: str
    answer: str
    category: str
    keywords: List[str]
    source: str
    confidence: float
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "keywords": self.keywords,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class KnowledgeBase:
    """
    知识库管理器
    
    功能：
    - 导入 QA 到知识库
    - 按分类组织知识
    - 支持多种格式导出
    - 知识检索
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or config.knowledge_base.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存中的知识库
        self._entries: Dict[str, List[KnowledgeEntry]] = defaultdict(list)
    
    def import_classified_qa(
        self,
        classified_qa_list: List[ClassifiedQA],
        source: str = "钉钉群聊",
    ) -> Dict[str, int]:
        """
        导入分类后的 QA 到知识库
        
        Args:
            classified_qa_list: 分类后的 QA 列表
            source: 来源标识
        
        Returns:
            各分类导入数量统计
        """
        import_counts = defaultdict(int)
        now = datetime.now()
        
        for classified_qa in classified_qa_list:
            entry = KnowledgeEntry(
                id=classified_qa.qa.id,
                question=classified_qa.qa.question,
                answer=classified_qa.qa.answer,
                category=classified_qa.category,
                keywords=classified_qa.keywords,
                source=source,
                confidence=classified_qa.confidence,
                created_at=now,
                updated_at=now,
            )
            
            self._entries[classified_qa.category].append(entry)
            import_counts[classified_qa.category] += 1
        
        return dict(import_counts)
    
    def export_to_json(
        self,
        output_path: Optional[Path] = None,
        by_category: bool = True,
    ) -> Path:
        """
        导出为 JSON 格式
        
        Args:
            output_path: 输出路径
            by_category: 是否按分类分文件
        
        Returns:
            输出路径
        """
        if by_category:
            # 按分类导出多个文件
            output_dir = self.output_dir / "by_category"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for category, entries in self._entries.items():
                file_path = output_dir / f"{category}.json"
                data = {
                    "category": category,
                    "category_name": config.knowledge_base.categories.get(category, category),
                    "count": len(entries),
                    "entries": [e.to_dict() for e in entries],
                }
                file_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            
            return output_dir
        else:
            # 导出单个文件
            if output_path is None:
                output_path = self.output_dir / "knowledge_base.json"
            
            all_entries = []
            for entries in self._entries.values():
                all_entries.extend(entries)
            
            data = {
                "total_count": len(all_entries),
                "categories": list(self._entries.keys()),
                "generated_at": datetime.now().isoformat(),
                "entries": [e.to_dict() for e in all_entries],
            }
            
            output_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            return output_path
    
    def export_to_csv(
        self,
        output_path: Optional[Path] = None,
    ) -> Path:
        """导出为 CSV 格式"""
        if output_path is None:
            output_path = self.output_dir / "knowledge_base.csv"
        
        all_entries = []
        for entries in self._entries.values():
            all_entries.extend(entries)
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "问题", "答案", "分类", "关键词",
                "来源", "置信度", "创建时间"
            ])
            
            for entry in all_entries:
                writer.writerow([
                    entry.id,
                    entry.question,
                    entry.answer,
                    entry.category,
                    ", ".join(entry.keywords),
                    entry.source,
                    entry.confidence,
                    entry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ])
        
        return output_path
    
    def export_to_markdown(
        self,
        output_path: Optional[Path] = None,
    ) -> Path:
        """导出为 Markdown 格式"""
        if output_path is None:
            output_path = self.output_dir / "knowledge_base.md"
        
        lines = [
            "# QA 知识库",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        
        for category, entries in self._entries.items():
            category_name = config.knowledge_base.categories.get(category, category)
            lines.extend([
                f"## {category_name}",
                "",
                f"共 {len(entries)} 条",
                "",
            ])
            
            for i, entry in enumerate(entries, 1):
                lines.extend([
                    f"### Q{i}: {entry.question}",
                    "",
                    f"**答案**: {entry.answer}",
                    "",
                    f"**关键词**: {', '.join(entry.keywords) if entry.keywords else '无'}",
                    "",
                    f"**置信度**: {entry.confidence:.2%}",
                    "",
                    "---",
                    "",
                ])
        
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path
    
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> List[KnowledgeEntry]:
        """
        搜索知识库
        
        Args:
            query: 搜索关键词
            category: 限定分类
            limit: 返回数量限制
        
        Returns:
            匹配的知识条目
        """
        results = []
        query_lower = query.lower()
        
        entries_to_search = []
        if category:
            entries_to_search = self._entries.get(category, [])
        else:
            for entries in self._entries.values():
                entries_to_search.extend(entries)
        
        for entry in entries_to_search:
            # 简单的关键词匹配
            score = 0
            if query_lower in entry.question.lower():
                score += 2
            if query_lower in entry.answer.lower():
                score += 1
            for keyword in entry.keywords:
                if query_lower in keyword.lower():
                    score += 0.5
            
            if score > 0:
                results.append((entry, score))
        
        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in results[:limit]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        total = sum(len(entries) for entries in self._entries.values())
        
        by_category = {
            category: len(entries)
            for category, entries in self._entries.items()
        }
        
        avg_confidence = 0.0
        if total > 0:
            total_confidence = sum(
                entry.confidence
                for entries in self._entries.values()
                for entry in entries
            )
            avg_confidence = total_confidence / total
        
        return {
            "total_count": total,
            "by_category": by_category,
            "avg_confidence": avg_confidence,
        }
    
    def clear(self):
        """清空知识库"""
        self._entries.clear()


def create_knowledge_base(
    classified_qa_list: List[ClassifiedQA],
    output_dir: Optional[str] = None,
    export_format: str = "json",
) -> Dict[str, Any]:
    """
    创建知识库并导出
    
    Args:
        classified_qa_list: 分类后的 QA 列表
        output_dir: 输出目录
        export_format: 导出格式 (json, csv, markdown, all)
    
    Returns:
        创建结果
    """
    kb = KnowledgeBase(output_dir)
    
    # 导入数据
    import_counts = kb.import_classified_qa(classified_qa_list)
    
    # 导出
    exported_files = []
    
    if export_format in ["json", "all"]:
        json_path = kb.export_to_json()
        exported_files.append(str(json_path))
    
    if export_format in ["csv", "all"]:
        csv_path = kb.export_to_csv()
        exported_files.append(str(csv_path))
    
    if export_format in ["markdown", "all"]:
        md_path = kb.export_to_markdown()
        exported_files.append(str(md_path))
    
    return {
        "import_counts": import_counts,
        "statistics": kb.get_statistics(),
        "exported_files": exported_files,
    }
