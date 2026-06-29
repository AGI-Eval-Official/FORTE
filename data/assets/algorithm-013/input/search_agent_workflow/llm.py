"""
AI搜索Agent - LLM交互模块
封装与大语言模型的交互逻辑
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM客户端
    封装与大语言模型API的交互，支持多种调用场景
    """

    def __init__(self, model: str, temperature: float = 0.7,
                 max_tokens: int = 2048, api_base: str = "https://api.openai.com/v1"):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_base = api_base
        logger.info(f"LLMClient initialized: model={model}, temp={temperature}")

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        发送聊天请求到LLM

        Args:
            messages: 对话消息列表，格式为 [{"role": "...", "content": "..."}]
            **kwargs: 额外参数（覆盖默认配置）

        Returns:
            LLM生成的回复文本
        """
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)

        logger.debug(f"LLM chat request: {len(messages)} messages, temp={temperature}")

        # 模拟LLM API调用
        # 实际实现中这里会调用 OpenAI API / Azure API 等
        response = self._call_api(messages, temperature, max_tokens)

        return response

    def _call_api(self, messages: List[Dict[str, str]],
                  temperature: float, max_tokens: int) -> str:
        """
        调用LLM API（模拟实现）

        实际项目中替换为真实API调用:
            import openai
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        """
        last_message = messages[-1]["content"] if messages else ""
        system_content = messages[0]["content"] if len(messages) > 0 else ""

        # 意图分类：根据查询内容模拟不同意图
        if "intent classifier" in system_content.lower() or "classify" in system_content.lower():
            query_lower = last_message.lower()
            if any(w in query_lower for w in ["news", "breaking", "today", "latest", "recent"]):
                return "news"
            if any(w in query_lower for w in ["paper", "research", "arxiv", "study", "academic"]):
                return "academic"
            if any(w in query_lower for w in ["difference", "compare", "vs", "versus"]):
                return "comparison"
            if any(w in query_lower for w in ["how to", "tutorial", "implement", "guide"]):
                return "tutorial"
            return "factual"


        # 查询改写：返回与原始查询有合理词重叠的改写结果
        if "rewrite" in system_content.lower():
            # 模拟正常改写（保留关键词，有足够词重叠）
            return f"detailed explanation of {last_message[:60]}"

        # 子查询拆分
        if "decompose" in system_content.lower() or "sub-queries" in system_content.lower():
            return f"sub-query 1 about {last_message[:30]}\nsub-query 2 about {last_message[:30]}"

        # 摘要生成：返回一段较长的模拟回答，用于测试截断逻辑
        if "search assistant" in system_content.lower() or "citations" in system_content.lower():
            return (
                "Based on the search results, here is a comprehensive answer. "
                "First, the topic involves several key aspects that are worth exploring. "
                "The primary consideration is the underlying mechanism, which has been "
                "studied extensively in recent literature [1]. Furthermore, practical "
                "applications demonstrate significant improvements over baseline methods [2]. "
                "In conclusion, the evidence strongly supports the proposed approach, "
                "and future work should focus on scalability and generalization [3]."
            )

        return f"LLM response to: {last_message[:100]}"

    def generate_with_prompt(self, system_prompt: str, user_input: str, **kwargs) -> str:
        """
        使用系统提示词和用户输入生成回复

        Args:
            system_prompt: 系统角色设定
            user_input: 用户输入内容
            **kwargs: 额外参数

        Returns:
            LLM生成的回复
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        return self.chat(messages, **kwargs)
