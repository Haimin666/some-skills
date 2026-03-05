"""
问题分析器模块

对分类后的 QA 进行问题发现和趋势分析
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter
from pathlib import Path

from config import config
from core.qa_classifier import ClassifiedQA


@dataclass
class ProblemSummary:
    """问题摘要"""
    total_count: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
    top_keywords: List[str]
    high_priority_items: List[Dict[str, Any]]


@dataclass
class TrendAnalysis:
    """趋势分析"""
    category: str
    trend: str  # increasing, stable, decreasing
    change_rate: float
    data_points: List[Dict[str, Any]]


@dataclass
class AnalysisReport:
    """分析报告"""
    generated_at: datetime
    summary: ProblemSummary
    trends: List[TrendAnalysis]
    recommendations: List[str]
    detailed_issues: List[Dict[str, Any]]


class ProblemAnalyzer:
    """
    问题分析器
    
    功能：
    - 问题统计分析
    - 趋势识别
    - 报告生成
    - 问题预警
    """
    
    def __init__(self):
        self.analysis_config = config.analysis
    
    def analyze(
        self,
        classified_qa_list: List[ClassifiedQA],
        historical_data: Optional[List[Dict]] = None,
    ) -> AnalysisReport:
        """
        分析问题
        
        Args:
            classified_qa_list: 分类后的 QA 列表
            historical_data: 历史数据（用于趋势分析）
        
        Returns:
            分析报告
        """
        # 生成摘要
        summary = self._generate_summary(classified_qa_list)
        
        # 趋势分析
        trends = self._analyze_trends(classified_qa_list, historical_data)
        
        # 生成建议
        recommendations = self._generate_recommendations(summary, trends)
        
        # 提取详细问题
        detailed_issues = self._extract_detailed_issues(classified_qa_list)
        
        return AnalysisReport(
            generated_at=datetime.now(),
            summary=summary,
            trends=trends,
            recommendations=recommendations,
            detailed_issues=detailed_issues,
        )
    
    def _generate_summary(
        self,
        classified_qa_list: List[ClassifiedQA],
    ) -> ProblemSummary:
        """生成问题摘要"""
        # 分类统计
        category_counter = Counter([qa.category for qa in classified_qa_list])
        
        # 严重级别统计
        severity_counter = Counter([
            qa.severity or "medium" for qa in classified_qa_list
        ])
        
        # 关键词统计
        all_keywords = []
        for qa in classified_qa_list:
            all_keywords.extend(qa.keywords)
        keyword_counter = Counter(all_keywords)
        
        # 高优先级问题
        high_priority = [
            {
                "id": qa.qa.id,
                "question": qa.qa.question,
                "category": qa.category,
                "severity": qa.severity,
                "reason": qa.reason,
            }
            for qa in classified_qa_list
            if qa.severity in ["critical", "high"]
        ][:10]  # 取前 10 个
        
        return ProblemSummary(
            total_count=len(classified_qa_list),
            by_category=dict(category_counter),
            by_severity=dict(severity_counter),
            top_keywords=[kw for kw, _ in keyword_counter.most_common(10)],
            high_priority_items=high_priority,
        )
    
    def _analyze_trends(
        self,
        classified_qa_list: List[ClassifiedQA],
        historical_data: Optional[List[Dict]] = None,
    ) -> List[TrendAnalysis]:
        """趋势分析"""
        trends = []
        
        # 当前各分类数量
        current_counts = Counter([qa.category for qa in classified_qa_list])
        
        if historical_data:
            # 与历史数据对比
            for category in current_counts.keys():
                current = current_counts[category]
                historical = historical_data[-1].get("by_category", {}).get(category, 0) if historical_data else 0
                
                if historical > 0:
                    change_rate = (current - historical) / historical
                else:
                    change_rate = 1.0 if current > 0 else 0.0
                
                if change_rate > 0.1:
                    trend = "increasing"
                elif change_rate < -0.1:
                    trend = "decreasing"
                else:
                    trend = "stable"
                
                trends.append(TrendAnalysis(
                    category=category,
                    trend=trend,
                    change_rate=change_rate,
                    data_points=[
                        {"date": datetime.now().isoformat(), "count": current}
                    ],
                ))
        else:
            # 没有历史数据时，仅记录当前状态
            for category, count in current_counts.items():
                trends.append(TrendAnalysis(
                    category=category,
                    trend="stable",
                    change_rate=0.0,
                    data_points=[
                        {"date": datetime.now().isoformat(), "count": count}
                    ],
                ))
        
        return trends
    
    def _generate_recommendations(
        self,
        summary: ProblemSummary,
        trends: List[TrendAnalysis],
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于问题数量建议
        total = summary.total_count
        if total > 100:
            recommendations.append(f"问题总量较大（{total}个），建议优先处理高优先级问题")
        
        # 基于分类建议
        category_counts = summary.by_category
        if category_counts.get("system_bug", 0) > 10:
            recommendations.append(
                f"系统Bug问题较多（{category_counts['system_bug']}个），建议进行系统性排查"
            )
        
        if category_counts.get("data_issue", 0) > 5:
            recommendations.append(
                f"数据问题频发（{category_counts['data_issue']}个），建议检查数据同步机制"
            )
        
        if category_counts.get("user_issue", 0) > 20:
            recommendations.append(
                f"用户咨询较多（{category_counts['user_issue']}个），建议优化用户引导和帮助文档"
            )
        
        # 基于严重级别建议
        severity_counts = summary.by_severity
        critical_count = severity_counts.get("critical", 0)
        high_count = severity_counts.get("high", 0)
        
        if critical_count > 0:
            recommendations.append(
                f"有{critical_count}个严重问题需要立即处理！"
            )
        
        if high_count > 5:
            recommendations.append(
                f"有{high_count}个高优先级问题待处理，建议安排专人跟进"
            )
        
        # 基于趋势建议
        for trend in trends:
            if trend.trend == "increasing" and trend.category == "system_bug":
                recommendations.append(
                    f"系统Bug问题呈上升趋势（增长率{trend.change_rate:.1%}），建议关注系统稳定性"
                )
        
        # 基于关键词建议
        top_keywords = summary.top_keywords[:3]
        if top_keywords:
            recommendations.append(
                f"高频关键词: {', '.join(top_keywords)}，建议重点关注相关功能模块"
            )
        
        return recommendations
    
    def _extract_detailed_issues(
        self,
        classified_qa_list: List[ClassifiedQA],
    ) -> List[Dict[str, Any]]:
        """提取详细问题列表"""
        issues = []
        
        # 按分类整理
        by_category = {}
        for qa in classified_qa_list:
            if qa.category not in by_category:
                by_category[qa.category] = []
            by_category[qa.category].append(qa)
        
        # 生成详细报告
        for category, qa_list in by_category.items():
            # 按严重级别排序
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_qa = sorted(
                qa_list,
                key=lambda x: severity_order.get(x.severity or "medium", 2)
            )
            
            issues.append({
                "category": category,
                "category_name": config.knowledge_base.categories.get(category, category),
                "count": len(qa_list),
                "by_severity": dict(Counter([qa.severity or "medium" for qa in qa_list])),
                "items": [
                    {
                        "id": qa.qa.id,
                        "question": qa.qa.question,
                        "answer": qa.qa.answer,
                        "severity": qa.severity,
                        "keywords": qa.keywords,
                        "confidence": qa.confidence,
                    }
                    for qa in sorted_qa[:20]  # 每个分类最多20条
                ],
            })
        
        return issues


def generate_report_file(
    report: AnalysisReport,
    output_path: Path,
    format: str = "json",
) -> Path:
    """生成报告文件"""
    if format == "json":
        content = json.dumps({
            "generated_at": report.generated_at.isoformat(),
            "summary": {
                "total_count": report.summary.total_count,
                "by_category": report.summary.by_category,
                "by_severity": report.summary.by_severity,
                "top_keywords": report.summary.top_keywords,
                "high_priority_items": report.summary.high_priority_items,
            },
            "trends": [
                {
                    "category": t.category,
                    "trend": t.trend,
                    "change_rate": t.change_rate,
                }
                for t in report.trends
            ],
            "recommendations": report.recommendations,
            "detailed_issues": report.detailed_issues,
        }, ensure_ascii=False, indent=2)
    elif format == "markdown":
        content = _generate_markdown_report(report)
    else:
        content = str(report)
    
    output_path.write_text(content, encoding="utf-8")
    return output_path


def _generate_markdown_report(report: AnalysisReport) -> str:
    """生成 Markdown 格式报告"""
    lines = [
        "# 问题分析报告",
        "",
        f"生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 概览",
        "",
        f"- 总问题数: {report.summary.total_count}",
        "",
        "### 按分类统计",
        "",
        "| 分类 | 数量 |",
        "|------|------|",
    ]
    
    for category, count in report.summary.by_category.items():
        category_name = config.knowledge_base.categories.get(category, category)
        lines.append(f"| {category_name} | {count} |")
    
    lines.extend([
        "",
        "### 按严重级别统计",
        "",
        "| 级别 | 数量 |",
        "|------|------|",
    ])
    
    for severity, count in report.summary.by_severity.items():
        severity_name = config.analysis.severity_levels.get(severity, severity)
        lines.append(f"| {severity_name} | {count} |")
    
    lines.extend([
        "",
        "## 高优先级问题",
        "",
    ])
    
    for item in report.summary.high_priority_items[:5]:
        lines.extend([
            f"### {item['question'][:50]}...",
            f"- 分类: {config.knowledge_base.categories.get(item['category'], item['category'])}",
            f"- 严重级别: {config.analysis.severity_levels.get(item['severity'], item['severity'])}",
            f"- 原因: {item['reason']}",
            "",
        ])
    
    lines.extend([
        "## 建议",
        "",
    ])
    
    for i, rec in enumerate(report.recommendations, 1):
        lines.append(f"{i}. {rec}")
    
    return "\n".join(lines)
