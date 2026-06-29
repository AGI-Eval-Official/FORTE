# Rubrics

> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则该任务整体判定为不通过。**

```path
/workspace/input/output/config.py
/workspace/input/output/tools.py
/workspace/input/output/llm.py
/workspace/input/output/react_agent.py
/workspace/input/output/main.py
```

```json
[
  {
    "id": "01",
    "content": "【ReAct核心循环实现】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须实现完整的ReAct推理循环，核心要求：(1) 存在明确的Thought -> Action -> Observation循环结构，循环体内依次执行推理、动作选择、工具调用、结果观察；(2) 每次循环中Agent通过LLM生成Thought（推理当前状态和下一步计划）；(3) Agent根据Thought选择一个Action（工具调用）并解析出工具名称和参数；(4) 执行Action后获得Observation（工具返回结果）并反馈给Agent；(5) 循环持续进行直到Agent主动决定终止（调用finish动作）或达到最大迭代次数。判定为'不通过'的情况：不存在Thought/Action/Observation循环；流程仍为固定顺序执行（退化为Workflow）；缺少循环迭代机制。",
    "weight": 1
  },
  {
    "id": "02",
    "content": "【动态工具选择机制】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。Agent必须通过推理动态选择工具，而非硬编码规则映射。具体要求：(1) 不存在类似原Workflow中的intent_tool_mapping固定映射表；(2) 工具选择由LLM在Thought阶段推理决定，根据当前查询和已有信息判断使用哪个工具；(3) Agent可以在不同迭代步中选择不同的工具（如先用web_search，发现信息不足后改用arxiv_search）；(4) 工具的自然语言描述被包含在Prompt中供LLM参考选择；(5) 存在Action解析逻辑，能从LLM输出中正确提取工具名称和调用参数。判定为'不通过'的情况：存在硬编码的意图-工具映射表；工具选择不由LLM推理决定；缺少Action解析器。",
    "weight": 1
  },
  {
    "id": "03",
    "content": "【自主终止与Finish动作】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 和 <file>/workspace/input/output/tools.py</file>。Agent必须能自主判断何时停止搜索并生成最终回答。具体要求：(1) 存在finish动作/工具的定义，Agent调用finish表示搜索结束并输出最终答案；(2) Agent在Thought中推理判断已有信息是否足够回答问题，若足够则选择finish；(3) finish动作携带最终答案内容作为参数；(4) 存在最大迭代次数限制（max_iterations），防止Agent无限循环；(5) 达到最大迭代次数时有兜底处理逻辑（如强制生成回答）。判定为'不通过'的情况：不存在finish机制；Agent无法自主终止只能靠超时；缺少最大迭代次数控制。",
    "weight": 1
  },
  {
    "id": "04",
    "content": "【ReAct Prompt设计】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须设计合理的ReAct格式提示词引导LLM正确输出。具体要求：(1) 系统提示词中明确要求LLM按照Thought/Action/Observation格式输出；(2) Prompt中包含可用工具的列表及其描述和参数说明；(3) Prompt中给出了ReAct格式的示例（few-shot），展示期望的输出格式；(4) Prompt指导LLM在Thought中分析当前状态、已有信息和下一步计划；(5) Action的输出格式清晰可解析（如 Action: tool_name[parameter] 或 JSON格式）。判定为'不通过'的情况：无ReAct格式的Prompt设计；Prompt中缺少工具描述；缺少格式示例导致输出不可解析。",
    "weight": 1
  },
  {
    "id": "05",
    "content": "【搜索工具保留与复用】判断依据文件：<file>/workspace/input/output/tools.py</file>。原有的三个搜索工具必须完整保留并正常可用。具体要求：(1) WebSearchTool保留完整实现，包含search方法，接收query参数返回SearchResult列表；同时保留 date_restrict_days 参数支持，用于新闻类查询的时间过滤；(2) KnowledgeBaseTool保留完整实现，包含search方法；(3) ArxivSearchTool保留完整实现，包含search方法；(4) SearchResult数据结构保留（title、url、snippet、source、relevance_score、published_date等字段）；(5) ToolRegistry工具注册表机制保留；(6) 每个工具新增description属性或等效机制，提供自然语言描述供Agent推理时参考。判定为'不通过'的情况：删除了任何原有搜索工具；工具接口发生不兼容变更；缺少工具描述信息；WebSearchTool丢失date_restrict_days参数支持。",
    "weight": 1
  },
  {
    "id": "06",
    "content": "【执行轨迹记录】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须记录完整的ReAct执行轨迹。具体要求：(1) 记录每一步的Thought内容（Agent的推理过程）；(2) 记录每一步的Action（选择的工具和参数）；(3) 记录每一步的Observation（工具返回结果）；(4) 轨迹以结构化形式存储（如列表，每个元素包含step、thought、action、observation字段）；(5) 支持获取完整轨迹用于调试和展示。判定为'不通过'的情况：不记录执行轨迹；只记录最终结果不记录中间推理过程；轨迹结构不完整缺少Thought/Action/Observation任一。",
    "weight": 1
  },
  {
    "id": "07",
    "content": "【配置完整性】判断依据文件：<file>/workspace/input/output/config.py</file>。配置文件必须适配ReAct架构，移除Workflow特有配置并新增ReAct配置。具体要求：(1) 新增最大推理迭代步数配置（如max_iterations）；(2) 保留LLM相关配置（model、temperature、max_tokens等）；(3) 保留搜索工具配置（web_search_top_k、knowledge_base_top_k、arxiv_search_top_k等）；(4) 移除或不再使用Workflow特有的固定节点配置（如node_timeout、max_retries_per_node等固定流程控制参数）；(5) 保留业务逻辑相关配置：news_date_restrict_days（新闻时间限制）、result_quality_threshold（质量过滤阈值）、min_results_after_filter（降级触发阈值）、source_quota_per_type（多源配额）、rewrite_drift_threshold（漂移检测阈值）、max_summary_length（摘要长度限制）；这些配置在ReAct架构中同样需要被Agent或工具使用。判定为'不通过'的情况：缺少最大迭代步数配置；删除了LLM或搜索工具的核心配置；仍保留大量Workflow特有的流程编排配置；丢失了业务逻辑相关配置项。",
    "weight": 1
  },
  {
    "id": "08",
    "content": "【移除固定流程编排】判断依据文件：<file>/workspace/input/output/react_agent.py</file>（或所有输出文件）。重构后的代码必须彻底移除Workflow架构的固定流程编排模式。具体要求：(1) 不存在原有的固定节点类（QueryAnalysisNode、SearchPlanNode、SearchExecutionNode、ResultRankingNode、SummaryGenerationNode）；(2) 不存在固定的节点列表按序执行逻辑；(3) 不存在WorkflowState在固定节点间传递的模式；(4) 搜索规划不再依赖固定的intent_tool_mapping映射表；(5) 代码体现ReAct的核心特征：根据推理动态决策，而非预定义流程。判定为'不通过'的情况：保留了固定节点类结构只是换了名字；仍存在固定的节点顺序执行逻辑；intent到tool的映射仍是硬编码规则。",
    "weight": 1
  },
  {
    "id": "09",
    "content": "【查询改写语义漂移检测迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 或 <file>/workspace/input/output/tools.py</file>。原Workflow中 QueryAnalysisNode 实现了查询改写后的语义漂移检测逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 存在计算两个查询字符串词级相似度（如Jaccard重叠率）的函数或方法；(2) 改写后的查询与原始查询相似度低于阈值（rewrite_drift_threshold）时，回退使用原始查询，而非使用改写后的漂移查询；(3) 漂移检测阈值从配置中读取（config.rewrite_drift_threshold），不能硬编码；(4) 漂移检测结果（是否回退）需要在执行轨迹或状态中有所体现，便于调试；(5) 子查询拆分或后续搜索应基于漂移检测后最终采用的查询（回退后用原始查询，未回退用改写查询）。判定为'不通过'的情况：完全丢弃了漂移检测逻辑；漂移时使用了改写后的错误查询而非回退到原始查询；阈值硬编码而非从配置读取。",
    "weight": 1
  },
  {
    "id": "10",
    "content": "【搜索结果质量过滤与降级兜底迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 或 <file>/workspace/input/output/tools.py</file>。原Workflow中 SearchExecutionNode 实现了质量过滤和降级兜底逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 工具调用返回结果后，按 relevance_score 阈值（result_quality_threshold）过滤低质量结果；(2) 过滤后有效结果数低于 min_results_after_filter 时，触发降级：放宽阈值（阈值减半）在原始结果上重新过滤，而非在已过滤结果上再次过滤；(3) 降级逻辑的阈值计算正确（threshold / 2），且 threshold 为 0 时跳过过滤；(4) 过滤结果的顺序与原始结果顺序一致（过滤不改变排列顺序）；(5) 质量过滤的结果（包括是否触发降级）需在执行轨迹的Observation中有所体现。判定为'不通过'的情况：完全丢弃了质量过滤逻辑；降级时在已过滤结果上再次过滤（导致结果更少）；阈值减半计算错误；过滤改变了结果顺序。",
    "weight": 1
  },
  {
    "id": "11",
    "content": "【多源配额均衡迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。原Workflow中 ResultRankingNode 实现了多源配额均衡逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 在收集到足够搜索结果后（通常在finish之前），对结果按来源（source字段）分组，每个来源最多保留 source_quota_per_type 条结果；(2) 配额截取应在按相关性排序之后进行（先排序再截取各来源Top-N）；(3) 各来源截取后的结果合并时需再次按 relevance_score 排序，不能简单拼接；(4) 某来源结果数不足配额时保留全部，不报错；(5) 配额值从配置中读取（config.source_quota_per_type），不能硬编码。判定为'不通过'的情况：完全丢弃了多源配额逻辑；配额截取在排序之前进行（导致截取的不是各来源最优结果）；合并后未重新排序；配额值硬编码。",
    "weight": 1
  },
  {
    "id": "12",
    "content": "【摘要句子边界截断迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。原Workflow中 SummaryGenerationNode 实现了摘要句子边界截断逻辑，ReAct架构在生成最终回答时必须保留并正确迁移此能力。具体要求：(1) 生成的最终回答（finish动作的answer参数，或兜底回答）超出 max_summary_length 时触发截断；(2) 截断必须在句子边界处进行（支持中英文句子结束标点：。！？.!?），不能硬截到字符中间；(3) 截断时预留省略号（\"...\"）的长度，即在 max_summary_length - 3 范围内寻找最后一个句子边界；(4) 若找不到句子边界则退而求其次在单词边界（空格）处截断；(5) 截断后追加\"...\"，并在状态或轨迹中标记 answer_truncated=True。判定为'不通过'的情况：完全丢弃了截断逻辑；截断时未预留省略号长度导致总长度超出限制；截断在字符中间而非句子/单词边界；未标记截断状态。",
    "weight": 1
  }
]
```
