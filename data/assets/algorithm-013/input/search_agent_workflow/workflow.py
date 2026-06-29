"""
AI搜索Agent - Workflow核心模块
实现基于固定流程编排的搜索Agent

Workflow架构说明：
整个搜索流程被拆分为若干固定节点（Node），按照预定义的顺序依次执行：
1. QueryAnalysisNode: 查询分析（意图识别 + 查询改写 + 语义漂移检测）
2. SearchPlanNode: 搜索规划（根据意图选择搜索工具组合，新闻类附加时间限制）
3. SearchExecutionNode: 搜索执行（调用工具 + 质量过滤 + 低质量降级兜底）
4. ResultRankingNode: 结果排序（去重 + 多源配额均衡 + 相关性排序）
5. SummaryGenerationNode: 摘要生成（LLM生成 + 句子边界截断）

各节点通过共享的WorkflowState传递数据，流程是线性且固定的。
"""

import logging
import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from tools import SearchResult, WebSearchTool, KnowledgeBaseTool, ArxivSearchTool, ToolRegistry
from llm import LLMClient
from config import WorkflowConfig

logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """
    Workflow状态对象
    在各节点之间传递和共享数据
    """
    # 原始输入
    original_query: str = ""

    # 查询分析结果
    intent: str = ""                          # 查询意图
    rewritten_query: str = ""                 # 改写后的查询（经漂移检测后可能回退为原始查询）
    rewrite_accepted: bool = True             # 改写结果是否被接受（False 表示发生漂移回退）
    sub_queries: List[str] = field(default_factory=list)  # 拆分的子查询

    # 搜索规划
    selected_tools: List[str] = field(default_factory=list)  # 选择的工具列表

    # 搜索结果
    raw_results: List[SearchResult] = field(default_factory=list)       # 原始搜索结果
    filtered_results: List[SearchResult] = field(default_factory=list)  # 质量过滤后结果

    # 排序后结果
    ranked_results: List[SearchResult] = field(default_factory=list)    # 排序后结果

    # 最终输出
    final_answer: str = ""                    # 最终生成的回答
    answer_truncated: bool = False            # 摘要是否被截断
    citations: List[Dict[str, str]] = field(default_factory=list)  # 引用来源

    # 执行元信息
    execution_log: List[Dict[str, Any]] = field(default_factory=list)  # 执行日志
    total_time: float = 0.0                   # 总执行时间


class BaseNode:
    """
    Workflow节点基类
    所有节点继承此基类，实现execute方法
    """

    def __init__(self, name: str, config: WorkflowConfig):
        self.name = name
        self.config = config

    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        执行节点逻辑

        Args:
            state: 当前workflow状态

        Returns:
            更新后的workflow状态
        """
        raise NotImplementedError

    def _log_execution(self, state: WorkflowState, start_time: float, status: str = "success"):
        """记录节点执行日志"""
        elapsed = time.time() - start_time
        state.execution_log.append({
            "node": self.name,
            "status": status,
            "elapsed_time": elapsed,
        })
        logger.info(f"Node [{self.name}] completed in {elapsed:.3f}s with status={status}")


class QueryAnalysisNode(BaseNode):
    """
    查询分析节点
    功能：意图识别 + 查询改写 + 语义漂移检测 + 子查询拆分

    在Workflow架构中，这是第一个固定执行的节点，无论查询是什么类型
    都会执行完整的分析流程。

    【业务逻辑1 - 查询改写语义漂移检测】
    查询改写后，计算改写结果与原始查询的词重叠率（Jaccard相似度）。
    若重叠率低于 rewrite_drift_threshold，认为改写发生了语义漂移
    （如原始查询"Python GIL"被改写成了"Java多线程"），此时回退使用原始查询，
    并在 state.rewrite_accepted = False 中记录。
    易出错点：
      - 重叠率计算需要对两个查询分词后取集合交集/并集，不能直接字符串比较
      - 回退时应使用 original_query 而非空字符串
      - rewrite_accepted 标志需要正确传递给后续节点（子查询拆分应基于最终采用的查询）
    """

    def __init__(self, config: WorkflowConfig, llm_client: LLMClient):
        super().__init__("QueryAnalysis", config)
        self.llm = llm_client

    def execute(self, state: WorkflowState) -> WorkflowState:
        start_time = time.time()
        logger.info(f"[QueryAnalysis] Analyzing query: '{state.original_query}'")

        # Step 1: 意图识别
        state.intent = self._classify_intent(state.original_query)
        logger.info(f"[QueryAnalysis] Intent classified: {state.intent}")

        # Step 2: 查询改写 + 语义漂移检测
        if self.config.query_rewrite_enabled:
            candidate = self._rewrite_query(state.original_query, state.intent)
            # 漂移检测：改写结果与原始查询词重叠率过低则回退
            overlap = self._compute_token_overlap(state.original_query, candidate)
            if overlap < self.config.rewrite_drift_threshold:
                logger.warning(
                    f"[QueryAnalysis] Rewrite drift detected "
                    f"(overlap={overlap:.2f} < threshold={self.config.rewrite_drift_threshold}), "
                    f"falling back to original query."
                )
                state.rewritten_query = state.original_query
                state.rewrite_accepted = False
            else:
                state.rewritten_query = candidate
                state.rewrite_accepted = True
        else:
            state.rewritten_query = state.original_query
            state.rewrite_accepted = True

        logger.info(
            f"[QueryAnalysis] rewritten_query='{state.rewritten_query}', "
            f"accepted={state.rewrite_accepted}"
        )

        # Step 3: 子查询拆分（基于最终采用的查询，而非原始查询）
        state.sub_queries = self._decompose_query(state.rewritten_query, state.intent)

        self._log_execution(state, start_time)
        return state

    def _classify_intent(self, query: str) -> str:
        """使用LLM进行意图分类"""
        system_prompt = (
            "You are a query intent classifier. Classify the user query into one of: "
            "factual, comparison, tutorial, news, academic. "
            "Respond with only the category name."
        )
        intent = self.llm.generate_with_prompt(system_prompt, query, temperature=0.0)
        intent = intent.strip().lower()

        if intent not in self.config.intent_categories:
            intent = "factual"
        return intent

    def _rewrite_query(self, query: str, intent: str) -> str:
        """查询改写：优化查询以提升搜索效果"""
        system_prompt = (
            f"Rewrite the following search query to improve search results. "
            f"The query intent is '{intent}'. "
            f"Make it more specific and searchable. Return only the rewritten query."
        )
        rewritten = self.llm.generate_with_prompt(system_prompt, query)
        return rewritten.strip() if rewritten.strip() else query

    def _compute_token_overlap(self, query_a: str, query_b: str) -> float:
        """
        计算两个查询字符串的词级 Jaccard 相似度

        Jaccard = |tokens_A ∩ tokens_B| / |tokens_A ∪ tokens_B|

        Args:
            query_a: 原始查询
            query_b: 改写后查询

        Returns:
            0.0 ~ 1.0 之间的相似度分数；两个查询均为空时返回 1.0
        """
        def tokenize(text: str):
            return set(re.findall(r'\w+', text.lower()))

        tokens_a = tokenize(query_a)
        tokens_b = tokenize(query_b)

        if not tokens_a and not tokens_b:
            return 1.0
        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union)

    def _decompose_query(self, query: str, intent: str) -> List[str]:
        """将复杂查询拆分为子查询"""
        if intent in ["factual", "news"]:
            return [query]

        system_prompt = (
            "Decompose the following complex query into 2-3 simpler sub-queries. "
            "Return each sub-query on a new line."
        )
        response = self.llm.generate_with_prompt(system_prompt, query)
        sub_queries = [q.strip() for q in response.strip().split('\n') if q.strip()]

        return sub_queries if sub_queries else [query]


class SearchPlanNode(BaseNode):
    """
    搜索规划节点
    功能：根据查询意图决定调用哪些搜索工具

    在Workflow架构中，工具选择策略是固定的规则映射：
    - factual -> web_search + knowledge_base
    - academic -> arxiv + web_search
    - news -> web_search（附加时间限制）
    - comparison -> web_search + knowledge_base
    - tutorial -> web_search + knowledge_base

    【业务逻辑2 - 新闻类查询附加时间限制】
    当意图为 "news" 时，需要将 WebSearchTool 替换为带有
    date_restrict_days 参数的实例，确保只返回近期新闻。
    易出错点：
      - 需要在 ToolRegistry 中注册一个新的带时间限制的 web_search 实例，
        而不是修改原有实例（避免影响其他意图的搜索）
      - 注册键名需要与后续 SearchExecutionNode 中的调用保持一致
      - date_restrict_days 应从 config 读取，不能硬编码
    """

    def __init__(self, config: WorkflowConfig, tool_registry: ToolRegistry):
        super().__init__("SearchPlan", config)
        self.tool_registry = tool_registry

        # 固定的意图-工具映射规则
        self.intent_tool_mapping = {
            "factual": ["web_search", "knowledge_base"],
            "comparison": ["web_search", "knowledge_base"],
            "tutorial": ["web_search", "knowledge_base"],
            "news": ["web_search_news"],   # 新闻类使用带时间限制的专用实例
            "academic": ["arxiv_search", "web_search"],
        }

    def execute(self, state: WorkflowState) -> WorkflowState:
        start_time = time.time()
        logger.info(f"[SearchPlan] Planning search for intent: '{state.intent}'")

        state.selected_tools = self.intent_tool_mapping.get(
            state.intent, ["web_search"]
        )

        # 新闻类：动态注册带时间限制的 WebSearchTool 实例
        if state.intent == "news" and "web_search_news" not in self.tool_registry.list_tools():
            news_tool = WebSearchTool(
                engine=self.config.web_search_engine,
                top_k=self.config.web_search_top_k,
                date_restrict_days=self.config.news_date_restrict_days,
            )
            self.tool_registry.register("web_search_news", news_tool)
            logger.info(
                f"[SearchPlan] Registered web_search_news with "
                f"date_restrict_days={self.config.news_date_restrict_days}"
            )

        logger.info(f"[SearchPlan] Selected tools: {state.selected_tools}")
        self._log_execution(state, start_time)
        return state


class SearchExecutionNode(BaseNode):
    """
    搜索执行节点
    功能：调用选定的搜索工具，收集搜索结果，并进行质量过滤

    【业务逻辑3 - 搜索结果质量过滤与降级兜底】
    搜索完成后，按 relevance_score 阈值过滤低质量结果。
    若过滤后有效结果数低于 min_results_after_filter，则触发降级：
    放宽阈值（阈值减半）重新过滤，确保后续节点有足够结果可用。
    易出错点：
      - 降级时应在原始结果（raw_results）上重新过滤，而非在已过滤结果上再过滤
      - 降级阈值计算：threshold / 2，需避免除零（threshold 为 0 时跳过过滤）
      - filtered_results 为空时不应继续执行后续节点（需在 state 中标记）
      - 过滤逻辑应保持结果的原始顺序，不能因过滤改变排列
    """

    def __init__(self, config: WorkflowConfig, tool_registry: ToolRegistry):
        super().__init__("SearchExecution", config)
        self.tool_registry = tool_registry

    def execute(self, state: WorkflowState) -> WorkflowState:
        start_time = time.time()
        logger.info(f"[SearchExecution] Executing search with tools: {state.selected_tools}")

        all_results = []

        for sub_query in state.sub_queries:
            for tool_name in state.selected_tools:
                try:
                    tool = self.tool_registry.get_tool(tool_name)
                    results = tool.search(sub_query)
                    all_results.extend(results)
                    logger.info(
                        f"[SearchExecution] {tool_name} returned {len(results)} results "
                        f"for query: '{sub_query}'"
                    )
                except Exception as e:
                    logger.error(f"[SearchExecution] Error with {tool_name}: {e}")

        state.raw_results = all_results
        logger.info(f"[SearchExecution] Total raw results: {len(all_results)}")

        # 质量过滤
        threshold = self.config.result_quality_threshold
        state.filtered_results = self._filter_by_quality(all_results, threshold)
        logger.info(
            f"[SearchExecution] After quality filter (threshold={threshold}): "
            f"{len(state.filtered_results)} results"
        )

        # 降级兜底：过滤后结果不足时放宽阈值重新过滤
        if len(state.filtered_results) < self.config.min_results_after_filter and threshold > 0:
            relaxed_threshold = threshold / 2
            logger.warning(
                f"[SearchExecution] Too few results after filter "
                f"({len(state.filtered_results)} < {self.config.min_results_after_filter}), "
                f"relaxing threshold to {relaxed_threshold:.2f}"
            )
            # 注意：必须在原始结果上重新过滤，而非在已过滤结果上再过滤
            state.filtered_results = self._filter_by_quality(all_results, relaxed_threshold)
            logger.info(
                f"[SearchExecution] After relaxed filter: {len(state.filtered_results)} results"
            )

        self._log_execution(state, start_time)
        return state

    def _filter_by_quality(
        self, results: List[SearchResult], threshold: float
    ) -> List[SearchResult]:
        """
        按相关性分数阈值过滤结果，保持原始顺序

        Args:
            results: 待过滤的结果列表
            threshold: relevance_score 最低阈值

        Returns:
            过滤后的结果列表（顺序与输入一致）
        """
        return [r for r in results if r.relevance_score >= threshold]


class ResultRankingNode(BaseNode):
    """
    结果排序节点
    功能：对搜索结果进行去重、多源配额均衡和相关性排序

    【业务逻辑4 - 多源配额均衡】
    在去重和排序之后，对每个来源（web / knowledge_base / arxiv）
    分别限制最多保留 source_quota_per_type 条结果，防止单一来源
    （如 web_search 返回大量结果）垄断最终结果集，确保多源信息的多样性。
    易出错点：
      - 配额计数需要按 source 字段分组，而非按工具名分组
      - 配额截断应在排序之后进行（先按相关性排序，再按配额截取各来源的 Top-N）
      - 最终结果需要将各来源的截取结果合并后再次按 relevance_score 排序，
        而不是简单拼接（否则来源顺序会影响最终排列）
      - 若某来源结果数不足配额，保留全部，不应补零或报错
    """

    def __init__(self, config: WorkflowConfig):
        super().__init__("ResultRanking", config)

    def execute(self, state: WorkflowState) -> WorkflowState:
        start_time = time.time()
        logger.info(f"[ResultRanking] Ranking {len(state.filtered_results)} filtered results")

        # Step 1: 去重（按URL）
        seen_urls = set()
        unique_results = []
        for result in state.filtered_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        # Step 2: 按相关性分数排序（降序）
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        # Step 3: 多源配额均衡
        # 对每个来源分别截取 Top-N，再合并后重新排序
        quota = self.config.source_quota_per_type
        source_buckets: Dict[str, List[SearchResult]] = {}
        for result in unique_results:
            source_buckets.setdefault(result.source, []).append(result)

        balanced: List[SearchResult] = []
        for source, bucket in source_buckets.items():
            # bucket 已按 relevance_score 降序排列（继承自 unique_results 的顺序）
            accepted = bucket[:quota]
            logger.info(
                f"[ResultRanking] source='{source}': {len(bucket)} results, "
                f"keeping top {len(accepted)} (quota={quota})"
            )
            balanced.extend(accepted)

        # Step 4: 合并后再次按相关性排序，确保最终顺序正确
        balanced.sort(key=lambda x: x.relevance_score, reverse=True)
        state.ranked_results = balanced

        logger.info(f"[ResultRanking] Final ranked results: {len(state.ranked_results)}")
        self._log_execution(state, start_time)
        return state


class SummaryGenerationNode(BaseNode):
    """
    摘要生成节点
    功能：基于排序后的搜索结果，使用LLM生成最终回答，并进行句子边界截断

    【业务逻辑5 - 摘要句子边界截断】
    LLM生成的摘要可能超出 max_summary_length 字符限制。
    超出时不能硬截（会截断单词或句子中间），需要找到不超过限制的
    最后一个句子边界（句号/问号/感叹号），在此处截断并追加省略标记"..."。
    若找不到任何句子边界（整段都是一个句子），则退而求其次在单词边界截断。
    易出错点：
      - 句子边界检测需要同时支持中英文标点（。！？.!?）
      - 截断位置应取"不超过 max_summary_length 的最后一个句子边界"，
        而非"第一个超出限制的句子边界之前"（两者在边界值处行为不同）
      - 追加"..."后总长度可能超出限制，需在截断时预留省略号的长度
      - answer_truncated 标志需要在截断时设置为 True
    """

    def __init__(self, config: WorkflowConfig, llm_client: LLMClient):
        super().__init__("SummaryGeneration", config)
        self.llm = llm_client

    def execute(self, state: WorkflowState) -> WorkflowState:
        start_time = time.time()
        logger.info(
            f"[SummaryGeneration] Generating answer from {len(state.ranked_results)} results"
        )

        context = self._build_context(state.ranked_results)

        system_prompt = (
            "You are a helpful search assistant. Based on the search results provided, "
            "generate a comprehensive and accurate answer to the user's question. "
            "Include numbered citations [1], [2], etc. referring to the sources."
        )
        user_input = (
            f"Question: {state.original_query}\n\n"
            f"Search Results:\n{context}\n\n"
            f"Please provide a comprehensive answer with citations."
        )

        raw_answer = self.llm.generate_with_prompt(system_prompt, user_input)

        # 句子边界截断
        state.final_answer, state.answer_truncated = self._truncate_at_sentence_boundary(
            raw_answer, self.config.max_summary_length
        )

        if state.answer_truncated:
            logger.info(
                f"[SummaryGeneration] Answer truncated: "
                f"{len(raw_answer)} -> {len(state.final_answer)} chars"
            )

        # 构建引用列表
        state.citations = [
            {"index": i + 1, "title": r.title, "url": r.url, "source": r.source}
            for i, r in enumerate(state.ranked_results)
        ]

        self._log_execution(state, start_time)
        return state

    def _build_context(self, results: List[SearchResult]) -> str:
        """将搜索结果组装为LLM可用的上下文字符串"""
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(
                f"[{i + 1}] Title: {result.title}\n"
                f"    Source: {result.source}\n"
                f"    Content: {result.snippet}\n"
            )
        return "\n".join(context_parts)

    def _truncate_at_sentence_boundary(
        self, text: str, max_length: int
    ) -> tuple:
        """
        在句子边界处截断文本，超出 max_length 时追加"..."

        截断规则：
          1. 若文本长度 <= max_length，直接返回，不截断
          2. 在 text[:max_length - 3] 范围内（预留"..."的3个字符）
             找到最后一个句子边界（。！？.!?）
          3. 若找到句子边界，在此处截断并追加"..."
          4. 若未找到句子边界，退而求其次在最后一个空格处截断并追加"..."
          5. 若连空格也没有，直接硬截到 max_length - 3 并追加"..."

        Args:
            text: 原始文本
            max_length: 最大字符数（含省略号）

        Returns:
            (truncated_text, was_truncated) 元组
        """
        if len(text) <= max_length:
            return text, False

        # 预留省略号长度
        ellipsis = "..."
        search_end = max_length - len(ellipsis)
        candidate = text[:search_end]

        # 在候选文本中找最后一个句子边界
        sentence_end_pattern = re.compile(r'[。！？.!?]')
        matches = list(sentence_end_pattern.finditer(candidate))

        if matches:
            # 取最后一个句子边界的位置（含标点本身）
            cut_pos = matches[-1].end()
            return text[:cut_pos] + ellipsis, True

        # 退而求其次：在最后一个空格处截断
        last_space = candidate.rfind(' ')
        if last_space > 0:
            return text[:last_space] + ellipsis, True

        # 兜底：硬截
        return candidate + ellipsis, True


class SearchWorkflow:
    """
    搜索Workflow主控制器

    编排所有节点的执行顺序，实现完整的搜索流程。
    Workflow架构的核心特点：
    1. 流程固定：所有查询都经过相同的5个节点
    2. 节点顺序不可变：QueryAnalysis -> SearchPlan -> SearchExecution -> ResultRanking -> SummaryGeneration
    3. 无条件分支：不会根据中间结果动态调整后续流程
    4. 一次性执行：整个流程从头到尾执行一次，不会迭代
    """

    def __init__(self, config: WorkflowConfig = None):
        self.config = config or WorkflowConfig()

        # 初始化LLM客户端
        self.llm_client = LLMClient(
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
            api_base=self.config.llm_api_base,
        )

        # 初始化搜索工具
        self.tool_registry = ToolRegistry()
        self.tool_registry.register("web_search", WebSearchTool(
            engine=self.config.web_search_engine,
            top_k=self.config.web_search_top_k,
        ))
        self.tool_registry.register("knowledge_base", KnowledgeBaseTool(
            top_k=self.config.knowledge_base_top_k,
        ))
        self.tool_registry.register("arxiv_search", ArxivSearchTool(
            top_k=self.config.arxiv_search_top_k,
        ))
        # 注意：web_search_news 由 SearchPlanNode 在运行时按需注册

        # 初始化Workflow节点（固定顺序）
        self.nodes = [
            QueryAnalysisNode(self.config, self.llm_client),
            SearchPlanNode(self.config, self.tool_registry),
            SearchExecutionNode(self.config, self.tool_registry),
            ResultRankingNode(self.config),
            SummaryGenerationNode(self.config, self.llm_client),
        ]

    def run(self, query: str) -> WorkflowState:
        """
        执行完整的搜索Workflow

        Args:
            query: 用户的搜索查询

        Returns:
            包含搜索结果的WorkflowState
        """
        logger.info(f"{'='*60}")
        logger.info(f"SearchWorkflow started: query='{query}'")
        logger.info(f"{'='*60}")

        start_time = time.time()

        state = WorkflowState(original_query=query)

        for node in self.nodes:
            try:
                state = node.execute(state)
            except Exception as e:
                logger.error(f"Node [{node.name}] failed: {e}")
                state.execution_log.append({
                    "node": node.name,
                    "status": "failed",
                    "error": str(e),
                })
                break

        state.total_time = time.time() - start_time
        logger.info(f"SearchWorkflow completed in {state.total_time:.3f}s")

        return state
