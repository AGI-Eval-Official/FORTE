"""
AI搜索Agent - 工具模块
定义搜索Agent可调用的各类搜索工具
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果数据结构"""
    title: str
    url: str
    snippet: str
    source: str                        # 来源类型: web / knowledge_base / arxiv
    relevance_score: float = 0.0       # 相关性分数
    timestamp: Optional[str] = None    # 结果时间戳（deprecated，保留兼容）
    published_date: Optional[str] = None  # 内容发布日期，格式 YYYY-MM-DD
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebSearchTool:
    """
    网页搜索工具
    封装外部搜索引擎API，支持Google/Bing等。

    新增能力：
      - date_restrict_days 参数：限制搜索结果的发布时间范围（天），
        用于新闻类查询只返回近期内容。0 表示不限制。
    """

    def __init__(self, engine: str = "google", top_k: int = 5,
                 date_restrict_days: int = 0):
        self.engine = engine
        self.top_k = top_k
        self.date_restrict_days = date_restrict_days
        logger.info(
            f"WebSearchTool initialized with engine={engine}, top_k={top_k}, "
            f"date_restrict_days={date_restrict_days}"
        )

    def search(self, query: str) -> List[SearchResult]:
        """
        执行网页搜索

        Args:
            query: 搜索查询字符串

        Returns:
            搜索结果列表；若设置了 date_restrict_days，则只返回时间范围内的结果
        """
        logger.info(f"WebSearch: query='{query}', date_restrict_days={self.date_restrict_days}")

        results = self._call_search_api(query)

        # 若设置了时间限制，过滤掉超出时间范围的结果
        if self.date_restrict_days > 0:
            cutoff = (datetime.now() - timedelta(days=self.date_restrict_days)).strftime("%Y-%m-%d")
            results = [r for r in results if r.published_date and r.published_date >= cutoff]
            logger.info(f"WebSearch: {len(results)} results after date filter (cutoff={cutoff})")

        return results[:self.top_k]

    def _call_search_api(self, query: str) -> List[SearchResult]:
        """调用搜索引擎API（模拟实现）"""
        time.sleep(0.1)

        # 模拟不同发布日期的结果（用于测试时间过滤逻辑）
        today = datetime.now()
        mock_results = [
            SearchResult(
                title=f"Search Result {i+1} for: {query}",
                url=f"https://example.com/result/{i+1}",
                snippet=f"This is a relevant snippet about '{query}' from source {i+1}...",
                source="web",
                relevance_score=1.0 - i * 0.1,
                timestamp="2024-01-01",
                published_date=(today - timedelta(days=i * 3)).strftime("%Y-%m-%d"),
            )
            for i in range(self.top_k)
        ]
        return mock_results


class KnowledgeBaseTool:
    """
    知识库检索工具
    基于向量数据库的语义检索，用于查询内部知识库
    """

    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        logger.info(f"KnowledgeBaseTool initialized with top_k={top_k}")

    def search(self, query: str) -> List[SearchResult]:
        """
        在知识库中检索相关文档

        Args:
            query: 搜索查询字符串

        Returns:
            检索结果列表
        """
        logger.info(f"KnowledgeBaseSearch: query='{query}'")

        results = self._vector_search(query)

        return results[:self.top_k]

    def _vector_search(self, query: str) -> List[SearchResult]:
        """执行向量检索（模拟实现）"""
        time.sleep(0.05)

        mock_results = [
            SearchResult(
                title=f"KB Document {i+1}",
                url=f"kb://doc/{i+1}",
                snippet=f"Knowledge base content related to '{query}'...",
                source="knowledge_base",
                relevance_score=0.95 - i * 0.1,
                published_date="2023-06-01",
            )
            for i in range(self.top_k)
        ]
        return mock_results


class ArxivSearchTool:
    """
    学术论文搜索工具
    检索arXiv上的学术论文，适用于学术/研究类查询
    """

    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        logger.info(f"ArxivSearchTool initialized with top_k={top_k}")

    def search(self, query: str) -> List[SearchResult]:
        """
        搜索学术论文

        Args:
            query: 搜索查询字符串

        Returns:
            论文搜索结果列表
        """
        logger.info(f"ArxivSearch: query='{query}'")

        results = self._search_arxiv(query)

        return results[:self.top_k]

    def _search_arxiv(self, query: str) -> List[SearchResult]:
        """调用arXiv API（模拟实现）"""
        time.sleep(0.1)

        mock_results = [
            SearchResult(
                title=f"[Paper] Research on {query} - Part {i+1}",
                url=f"https://arxiv.org/abs/2024.{i+1:05d}",
                snippet=f"Abstract: This paper investigates {query} and proposes...",
                source="arxiv",
                relevance_score=0.9 - i * 0.1,
                published_date=f"2024-0{i+1}-15",
                metadata={"authors": ["Author A", "Author B"], "year": 2024},
            )
            for i in range(self.top_k)
        ]
        return mock_results


class ToolRegistry:
    """
    工具注册表
    管理所有可用工具的注册和调用
    """

    def __init__(self):
        self._tools: Dict[str, Any] = {}

    def register(self, name: str, tool: Any):
        """注册工具"""
        self._tools[name] = tool
        logger.info(f"Tool registered: {name}")

    def get_tool(self, name: str) -> Any:
        """获取工具实例"""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def list_tools(self) -> List[str]:
        """列出所有已注册的工具"""
        return list(self._tools.keys())
