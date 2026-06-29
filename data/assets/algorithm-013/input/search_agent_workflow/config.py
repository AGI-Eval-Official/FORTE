"""
AI Search Agent - Workflow Architecture Configuration
"""


class WorkflowConfig:
    """Workflow Search Agent Configuration"""

    # ==================== LLM Configuration ====================
    llm_model = "gpt-4"
    llm_temperature = 0.7
    llm_max_tokens = 2048
    llm_api_base = "https://api.openai.com/v1"
    llm_timeout = 30

    # ==================== Search Tool Configuration ====================
    web_search_engine = "google"
    web_search_top_k = 5
    knowledge_base_top_k = 3
    arxiv_search_top_k = 3

    # 新闻类查询的时间限制（天），0 表示不限制
    news_date_restrict_days = 7

    # ==================== Workflow Node Configuration ====================
    max_retries_per_node = 2
    node_timeout = 60

    # ==================== Query Analysis Configuration ====================
    query_rewrite_enabled = True
    intent_categories = [
        "factual",
        "comparison",
        "tutorial",
        "news",
        "academic",
    ]

    # 查询改写语义漂移检测：改写后查询与原始查询的词重叠率低于此阈值时，
    # 认为改写发生了语义漂移，回退使用原始查询
    rewrite_drift_threshold = 0.2

    # ==================== Search Quality Configuration ====================
    # 搜索结果质量过滤：relevance_score 低于此阈值的结果将被丢弃
    result_quality_threshold = 0.5

    # 质量过滤后若有效结果数低于此值，则降级：放宽阈值重新过滤
    min_results_after_filter = 2

    # ==================== Result Ranking Configuration ====================
    # 多源配额均衡：每个来源（web / knowledge_base / arxiv）最多保留的结果数
    # 防止单一来源垄断最终结果
    source_quota_per_type = 3

    # ==================== Result Generation Configuration ====================
    max_summary_length = 500
    citation_format = "numbered"
    enable_source_verification = True

    # ==================== Logging & Debug ====================
    log_level = "INFO"
    log_file = "search_agent.log"
    debug_mode = False
