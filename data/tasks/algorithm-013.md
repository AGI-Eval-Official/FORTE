---
id: algorithm-013
name: algorithm-013
category: algorithm
grading_type: llm_judge
timeout_seconds: 2400
input_modality: text
workspace_files:
- source: input/search_agent_workflow/config.py
  dest: input/search_agent_workflow/config.py
- source: input/search_agent_workflow/requirements.txt
  dest: input/search_agent_workflow/requirements.txt
- source: input/search_agent_workflow/search_agent.log
  dest: input/search_agent_workflow/search_agent.log
- source: input/search_agent_workflow/tools.py
  dest: input/search_agent_workflow/tools.py
- source: input/search_agent_workflow/llm.py
  dest: input/search_agent_workflow/llm.py
- source: input/search_agent_workflow/workflow.py
  dest: input/search_agent_workflow/workflow.py
- source: input/search_agent_workflow/main.py
  dest: input/search_agent_workflow/main.py
- source: skills/hf-token-stats/SKILL.md
  dest: skills/hf-token-stats/SKILL.md
- source: skills/algorithm-coding-guide/SKILL.md
  dest: skills/algorithm-coding-guide/SKILL.md
- source: skills/paper-code-understanding/SKILL.md
  dest: skills/paper-code-understanding/SKILL.md
- source: skills/paper-code-understanding/references/analysis-checklist.md
  dest: skills/paper-code-understanding/references/analysis-checklist.md
- source: skills/algorithm-code-understanding/SKILL.md
  dest: skills/algorithm-code-understanding/SKILL.md
- source: skills/algorithm-code-understanding/references/deep-checklist.md
  dest: skills/algorithm-code-understanding/references/deep-checklist.md
solution_files:
- source: solution/rubrics.md
  dest: solution/rubrics.md
rubric_file_paths:
- /workspace/input/output/config.py
- /workspace/input/output/tools.py
- /workspace/input/output/llm.py
- /workspace/input/output/react_agent.py
- /workspace/input/output/main.py
rubrics:
- id: '01'
  content: 【ReAct核心循环实现】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须实现完整的ReAct推理循环，核心要求：(1) 存在明确的Thought -> Action -> Observation循环结构，循环体内依次执行推理、动作选择、工具调用、结果观察；(2) 每次循环中Agent通过LLM生成Thought（推理当前状态和下一步计划）；(3) Agent根据Thought选择一个Action（工具调用）并解析出工具名称和参数；(4) 执行Action后获得Observation（工具返回结果）并反馈给Agent；(5) 循环持续进行直到Agent主动决定终止（调用finish动作）或达到最大迭代次数。判定为'不通过'的情况：不存在Thought/Action/Observation循环；流程仍为固定顺序执行（退化为Workflow）；缺少循环迭代机制。
  weight: 1
- id: '02'
  content: 【动态工具选择机制】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。Agent必须通过推理动态选择工具，而非硬编码规则映射。具体要求：(1) 不存在类似原Workflow中的intent_tool_mapping固定映射表；(2) 工具选择由LLM在Thought阶段推理决定，根据当前查询和已有信息判断使用哪个工具；(3) Agent可以在不同迭代步中选择不同的工具（如先用web_search，发现信息不足后改用arxiv_search）；(4) 工具的自然语言描述被包含在Prompt中供LLM参考选择；(5) 存在Action解析逻辑，能从LLM输出中正确提取工具名称和调用参数。判定为'不通过'的情况：存在硬编码的意图-工具映射表；工具选择不由LLM推理决定；缺少Action解析器。
  weight: 1
- id: '03'
  content: 【自主终止与Finish动作】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 和 <file>/workspace/input/output/tools.py</file>。Agent必须能自主判断何时停止搜索并生成最终回答。具体要求：(1) 存在finish动作/工具的定义，Agent调用finish表示搜索结束并输出最终答案；(2) Agent在Thought中推理判断已有信息是否足够回答问题，若足够则选择finish；(3) finish动作携带最终答案内容作为参数；(4) 存在最大迭代次数限制（max_iterations），防止Agent无限循环；(5) 达到最大迭代次数时有兜底处理逻辑（如强制生成回答）。判定为'不通过'的情况：不存在finish机制；Agent无法自主终止只能靠超时；缺少最大迭代次数控制。
  weight: 1
- id: '04'
  content: '【ReAct Prompt设计】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须设计合理的ReAct格式提示词引导LLM正确输出。具体要求：(1) 系统提示词中明确要求LLM按照Thought/Action/Observation格式输出；(2) Prompt中包含可用工具的列表及其描述和参数说明；(3) Prompt中给出了ReAct格式的示例（few-shot），展示期望的输出格式；(4) Prompt指导LLM在Thought中分析当前状态、已有信息和下一步计划；(5) Action的输出格式清晰可解析（如 Action: tool_name[parameter] 或 JSON格式）。判定为''不通过''的情况：无ReAct格式的Prompt设计；Prompt中缺少工具描述；缺少格式示例导致输出不可解析。'
  weight: 1
- id: '05'
  content: 【搜索工具保留与复用】判断依据文件：<file>/workspace/input/output/tools.py</file>。原有的三个搜索工具必须完整保留并正常可用。具体要求：(1) WebSearchTool保留完整实现，包含search方法，接收query参数返回SearchResult列表；同时保留 date_restrict_days 参数支持，用于新闻类查询的时间过滤；(2) KnowledgeBaseTool保留完整实现，包含search方法；(3) ArxivSearchTool保留完整实现，包含search方法；(4) SearchResult数据结构保留（title、url、snippet、source、relevance_score、published_date等字段）；(5) ToolRegistry工具注册表机制保留；(6) 每个工具新增description属性或等效机制，提供自然语言描述供Agent推理时参考。判定为'不通过'的情况：删除了任何原有搜索工具；工具接口发生不兼容变更；缺少工具描述信息；WebSearchTool丢失date_restrict_days参数支持。
  weight: 1
- id: '06'
  content: 【执行轨迹记录】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须记录完整的ReAct执行轨迹。具体要求：(1) 记录每一步的Thought内容（Agent的推理过程）；(2) 记录每一步的Action（选择的工具和参数）；(3) 记录每一步的Observation（工具返回结果）；(4) 轨迹以结构化形式存储（如列表，每个元素包含step、thought、action、observation字段）；(5) 支持获取完整轨迹用于调试和展示。判定为'不通过'的情况：不记录执行轨迹；只记录最终结果不记录中间推理过程；轨迹结构不完整缺少Thought/Action/Observation任一。
  weight: 1
- id: '07'
  content: 【配置完整性】判断依据文件：<file>/workspace/input/output/config.py</file>。配置文件必须适配ReAct架构，移除Workflow特有配置并新增ReAct配置。具体要求：(1) 新增最大推理迭代步数配置（如max_iterations）；(2) 保留LLM相关配置（model、temperature、max_tokens等）；(3) 保留搜索工具配置（web_search_top_k、knowledge_base_top_k、arxiv_search_top_k等）；(4) 移除或不再使用Workflow特有的固定节点配置（如node_timeout、max_retries_per_node等固定流程控制参数）；(5) 保留业务逻辑相关配置：news_date_restrict_days（新闻时间限制）、result_quality_threshold（质量过滤阈值）、min_results_after_filter（降级触发阈值）、source_quota_per_type（多源配额）、rewrite_drift_threshold（漂移检测阈值）、max_summary_length（摘要长度限制）；这些配置在ReAct架构中同样需要被Agent或工具使用。判定为'不通过'的情况：缺少最大迭代步数配置；删除了LLM或搜索工具的核心配置；仍保留大量Workflow特有的流程编排配置；丢失了业务逻辑相关配置项。
  weight: 1
- id: '08'
  content: 【移除固定流程编排】判断依据文件：<file>/workspace/input/output/react_agent.py</file>（或所有输出文件）。重构后的代码必须彻底移除Workflow架构的固定流程编排模式。具体要求：(1) 不存在原有的固定节点类（QueryAnalysisNode、SearchPlanNode、SearchExecutionNode、ResultRankingNode、SummaryGenerationNode）；(2) 不存在固定的节点列表按序执行逻辑；(3) 不存在WorkflowState在固定节点间传递的模式；(4) 搜索规划不再依赖固定的intent_tool_mapping映射表；(5) 代码体现ReAct的核心特征：根据推理动态决策，而非预定义流程。判定为'不通过'的情况：保留了固定节点类结构只是换了名字；仍存在固定的节点顺序执行逻辑；intent到tool的映射仍是硬编码规则。
  weight: 1
- id: '09'
  content: 【查询改写语义漂移检测迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 或 <file>/workspace/input/output/tools.py</file>。原Workflow中 QueryAnalysisNode 实现了查询改写后的语义漂移检测逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 存在计算两个查询字符串词级相似度（如Jaccard重叠率）的函数或方法；(2) 改写后的查询与原始查询相似度低于阈值（rewrite_drift_threshold）时，回退使用原始查询，而非使用改写后的漂移查询；(3) 漂移检测阈值从配置中读取（config.rewrite_drift_threshold），不能硬编码；(4) 漂移检测结果（是否回退）需要在执行轨迹或状态中有所体现，便于调试；(5) 子查询拆分或后续搜索应基于漂移检测后最终采用的查询（回退后用原始查询，未回退用改写查询）。判定为'不通过'的情况：完全丢弃了漂移检测逻辑；漂移时使用了改写后的错误查询而非回退到原始查询；阈值硬编码而非从配置读取。
  weight: 1
- id: '10'
  content: 【搜索结果质量过滤与降级兜底迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 或 <file>/workspace/input/output/tools.py</file>。原Workflow中 SearchExecutionNode 实现了质量过滤和降级兜底逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 工具调用返回结果后，按 relevance_score 阈值（result_quality_threshold）过滤低质量结果；(2) 过滤后有效结果数低于 min_results_after_filter 时，触发降级：放宽阈值（阈值减半）在原始结果上重新过滤，而非在已过滤结果上再次过滤；(3) 降级逻辑的阈值计算正确（threshold / 2），且 threshold 为 0 时跳过过滤；(4) 过滤结果的顺序与原始结果顺序一致（过滤不改变排列顺序）；(5) 质量过滤的结果（包括是否触发降级）需在执行轨迹的Observation中有所体现。判定为'不通过'的情况：完全丢弃了质量过滤逻辑；降级时在已过滤结果上再次过滤（导致结果更少）；阈值减半计算错误；过滤改变了结果顺序。
  weight: 1
- id: '11'
  content: 【多源配额均衡迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。原Workflow中 ResultRankingNode 实现了多源配额均衡逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 在收集到足够搜索结果后（通常在finish之前），对结果按来源（source字段）分组，每个来源最多保留 source_quota_per_type 条结果；(2) 配额截取应在按相关性排序之后进行（先排序再截取各来源Top-N）；(3) 各来源截取后的结果合并时需再次按 relevance_score 排序，不能简单拼接；(4) 某来源结果数不足配额时保留全部，不报错；(5) 配额值从配置中读取（config.source_quota_per_type），不能硬编码。判定为'不通过'的情况：完全丢弃了多源配额逻辑；配额截取在排序之前进行（导致截取的不是各来源最优结果）；合并后未重新排序；配额值硬编码。
  weight: 1
- id: '12'
  content: 【摘要句子边界截断迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。原Workflow中 SummaryGenerationNode 实现了摘要句子边界截断逻辑，ReAct架构在生成最终回答时必须保留并正确迁移此能力。具体要求：(1) 生成的最终回答（finish动作的answer参数，或兜底回答）超出 max_summary_length 时触发截断；(2) 截断必须在句子边界处进行（支持中英文句子结束标点：。！？.!?），不能硬截到字符中间；(3) 截断时预留省略号（"..."）的长度，即在 max_summary_length - 3 范围内寻找最后一个句子边界；(4) 若找不到句子边界则退而求其次在单词边界（空格）处截断；(5) 截断后追加"..."，并在状态或轨迹中标记 answer_truncated=True。判定为'不通过'的情况：完全丢弃了截断逻辑；截断时未预留省略号长度导致总长度超出限制；截断在字符中间而非句子/单词边界；未标记截断状态。
  weight: 1
---

## Prompt

你是一名AI搜索算法工程师，当前负责搜索Agent系统的架构升级工作。线上搜索系统目前使用的是基于Workflow（固定流程编排）架构的AI搜索Agent，现在需要将其重构为基于ReAct（Reasoning + Acting）架构，以提升Agent在复杂搜索场景下的自主推理和动态决策能力。

### 背景信息

- **线上Workflow搜索Agent代码**：`/workspace/input/search_agent_workflow/`
  - `config.py` - 系统配置（LLM参数、搜索工具参数、Workflow节点配置等）
  - `tools.py` - 搜索工具模块（WebSearchTool、KnowledgeBaseTool、ArxivSearchTool、ToolRegistry）
  - `llm.py` - LLM交互模块（封装大语言模型API调用）
  - `workflow.py` - Workflow核心模块（固定流程节点：QueryAnalysis -> SearchPlan -> SearchExecution -> ResultRanking -> SummaryGeneration）
  - `main.py` - 主入口脚本
  - `requirements.txt` - 依赖包

### 当前Workflow架构的局限性

当前Workflow架构存在以下问题，需要通过ReAct架构来解决：

1. **流程固定不灵活**：所有查询都经过相同的5个固定节点，无法根据查询复杂度动态调整
2. **无法迭代优化**：搜索结果不满意时无法自动追加搜索或换用其他工具
3. **缺乏推理能力**：节点间的决策基于硬编码规则（如意图-工具映射表），而非推理判断
4. **一次性执行**：整个流程执行一次即结束，无法根据中间结果判断是否需要进一步搜索

### ReAct架构核心思想

ReAct（Reasoning + Acting）是一种让Agent交替进行"推理"和"行动"的架构模式：

- **Thought（推理）**：Agent分析当前状态，决定下一步该做什么
- **Action（行动）**：Agent选择并调用一个工具执行具体操作
- **Observation（观察）**：Agent获取工具执行的结果
- 以上三步循环迭代，直到Agent判断已获得足够信息来回答用户问题

### 任务要求

请将线上基于Workflow架构的搜索Agent，重构为基于ReAct架构的搜索Agent，并完成代码改写。具体要求如下：

#### 1. 架构重构

- **移除固定流程编排**：取消原有的5个固定节点顺序执行模式
- **实现ReAct循环**：Agent通过"Thought -> Action -> Observation"循环自主决定何时搜索、搜索什么、何时停止
- **动态工具选择**：Agent通过推理动态选择调用哪个工具，而非依赖硬编码的意图-工具映射表
- **迭代搜索能力**：Agent可以根据已有搜索结果判断是否需要进一步搜索，支持多轮搜索迭代
- **自主终止判断**：Agent能判断何时已收集到足够信息，自主决定停止搜索并生成回答

#### 2. ReAct核心组件实现

- **ReAct Agent类**：实现核心的ReAct推理循环，管理Thought/Action/Observation的交替执行
- **Prompt工程**：设计ReAct格式的系统提示词，引导LLM按照Thought/Action/Observation格式输出
- **Action解析器**：解析LLM输出中的Action指令，提取工具名称和参数
- **最大迭代控制**：设置最大推理步数，防止无限循环
- **执行轨迹记录**：记录完整的Thought/Action/Observation轨迹，便于调试和分析

#### 3. 保留并复用搜索工具

- **保留现有工具**：WebSearchTool、KnowledgeBaseTool、ArxivSearchTool必须保留并正常工作
- **保留ToolRegistry**：工具注册表机制继续使用
- **新增Finish工具**：增加一个"finish"工具/动作，用于Agent主动结束搜索并输出最终回答
- **工具描述信息**：为每个工具添加自然语言描述，供Agent在推理时参考选择

#### 4. 配置更新

- 更新`config.py`：新增ReAct相关配置（最大推理步数、ReAct提示词模板路径等）
- 移除Workflow特有配置（如固定节点超时、节点重试等）
- 保留LLM和搜索工具相关配置
- **保留所有业务质量保障配置**（见下方"迁移与移除原则"）

#### 5. 代码质量要求

- 代码结构清晰，模块化设计，各组件职责明确
- 关键模块需要有注释说明原理和实现逻辑
- 所有文件语法正确，可以正常import和运行
- 保持Python风格一致性
- ReAct的Prompt设计要清晰明确，引导LLM正确输出格式化的Thought/Action/Observation

### 迁移与移除原则

Workflow 的 `workflow.py` 中包含两类性质不同的逻辑，重构时需要自行判断每段逻辑属于哪一类，并做出相应处理：

#### 应移除的逻辑（架构强绑定）

判断标准：该逻辑是否只是为了弥补 Workflow"无推理能力"而存在的硬编码补丁？若在 ReAct 中这部分决策可以由 LLM 的 Thought 推理自然替代，则应移除。

示例：固定节点结构（QueryAnalysisNode、SearchPlanNode 等节点类及其顺序编排）属于此类，应移除。

#### 应迁移的逻辑（业务质量保障）

判断标准：该逻辑是否与架构无关，而是保障搜索结果质量或输出规范的产品需求？若换成任何架构都同样需要这个保障，则应迁移。

示例：对最终答案按句子边界截断（防止输出在词语中间截断）属于此类，应迁移到 ReAct 实现中。

对应地，config.py 中与业务质量保障逻辑相关的配置项也需自行判断是否保留，原则同上。

### 总体要求

- 请直接完成所有任务，不要问我任何问题，也不要让我做出进一步决策
- 如果遇到任何问题和决策点，请自行判断并给出合理方案
- 重构后的代码需保持模块化和可读性，方便后续维护
- 确保从Workflow到ReAct的架构重构是完整且正确的，体现ReAct架构的核心优势

### 输出要求

将重构后的完整ReAct搜索Agent代码输出到 `/workspace/input/output/` 目录下，包含以下文件：
- `config.py` - 更新后的配置文件
- `tools.py` - 更新后的工具模块（保留原有工具，新增工具描述和Finish动作）
- `llm.py` - LLM交互模块（可复用，如有修改请说明）
- `react_agent.py` - ReAct Agent核心实现（替代原workflow.py）
- `main.py` - 更新后的主入口脚本
- `requirements.txt` - 依赖包（如有新增）

## Grading Criteria

- [ ] [01] 【ReAct核心循环实现】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须实现完整的ReAct推理循环，核心要求：(1) 存在明确的Thought -> Action -> Observation循环结构，循环体内依次执行推理、动作选择、工具调用、结果观察；(2) 每次循环中Agent通过LLM生成Thought（推理当前状态和下一步计划）；(3) Agent根据Thought选择一个Action（工具调用）并解析出工具名称和参数；(4) 执行Action后获得Observation（工具返回结果）并反馈给Agent；(5) 循环持续进行直到Agent主动决定终止（调用finish动作）或达到最大迭代次数。判定为'不通过'的情况：不存在Thought/Action/Observation循环；流程仍为固定顺序执行（退化为Workflow）；缺少循环迭代机制。
- [ ] [02] 【动态工具选择机制】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。Agent必须通过推理动态选择工具，而非硬编码规则映射。具体要求：(1) 不存在类似原Workflow中的intent_tool_mapping固定映射表；(2) 工具选择由LLM在Thought阶段推理决定，根据当前查询和已有信息判断使用哪个工具；(3) Agent可以在不同迭代步中选择不同的工具（如先用web_search，发现信息不足后改用arxiv_search）；(4) 工具的自然语言描述被包含在Prompt中供LLM参考选择；(5) 存在Action解析逻辑，能从LLM输出中正确提取工具名称和调用参数。判定为'不通过'的情况：存在硬编码的意图-工具映射表；工具选择不由LLM推理决定；缺少Action解析器。
- [ ] [03] 【自主终止与Finish动作】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 和 <file>/workspace/input/output/tools.py</file>。Agent必须能自主判断何时停止搜索并生成最终回答。具体要求：(1) 存在finish动作/工具的定义，Agent调用finish表示搜索结束并输出最终答案；(2) Agent在Thought中推理判断已有信息是否足够回答问题，若足够则选择finish；(3) finish动作携带最终答案内容作为参数；(4) 存在最大迭代次数限制（max_iterations），防止Agent无限循环；(5) 达到最大迭代次数时有兜底处理逻辑（如强制生成回答）。判定为'不通过'的情况：不存在finish机制；Agent无法自主终止只能靠超时；缺少最大迭代次数控制。
- [ ] [04] 【ReAct Prompt设计】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须设计合理的ReAct格式提示词引导LLM正确输出。具体要求：(1) 系统提示词中明确要求LLM按照Thought/Action/Observation格式输出；(2) Prompt中包含可用工具的列表及其描述和参数说明；(3) Prompt中给出了ReAct格式的示例（few-shot），展示期望的输出格式；(4) Prompt指导LLM在Thought中分析当前状态、已有信息和下一步计划；(5) Action的输出格式清晰可解析（如 Action: tool_name[parameter] 或 JSON格式）。判定为'不通过'的情况：无ReAct格式的Prompt设计；Prompt中缺少工具描述；缺少格式示例导致输出不可解析。
- [ ] [05] 【搜索工具保留与复用】判断依据文件：<file>/workspace/input/output/tools.py</file>。原有的三个搜索工具必须完整保留并正常可用。具体要求：(1) WebSearchTool保留完整实现，包含search方法，接收query参数返回SearchResult列表；同时保留 date_restrict_days 参数支持，用于新闻类查询的时间过滤；(2) KnowledgeBaseTool保留完整实现，包含search方法；(3) ArxivSearchTool保留完整实现，包含search方法；(4) SearchResult数据结构保留（title、url、snippet、source、relevance_score、published_date等字段）；(5) ToolRegistry工具注册表机制保留；(6) 每个工具新增description属性或等效机制，提供自然语言描述供Agent推理时参考。判定为'不通过'的情况：删除了任何原有搜索工具；工具接口发生不兼容变更；缺少工具描述信息；WebSearchTool丢失date_restrict_days参数支持。
- [ ] [06] 【执行轨迹记录】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。必须记录完整的ReAct执行轨迹。具体要求：(1) 记录每一步的Thought内容（Agent的推理过程）；(2) 记录每一步的Action（选择的工具和参数）；(3) 记录每一步的Observation（工具返回结果）；(4) 轨迹以结构化形式存储（如列表，每个元素包含step、thought、action、observation字段）；(5) 支持获取完整轨迹用于调试和展示。判定为'不通过'的情况：不记录执行轨迹；只记录最终结果不记录中间推理过程；轨迹结构不完整缺少Thought/Action/Observation任一。
- [ ] [07] 【配置完整性】判断依据文件：<file>/workspace/input/output/config.py</file>。配置文件必须适配ReAct架构，移除Workflow特有配置并新增ReAct配置。具体要求：(1) 新增最大推理迭代步数配置（如max_iterations）；(2) 保留LLM相关配置（model、temperature、max_tokens等）；(3) 保留搜索工具配置（web_search_top_k、knowledge_base_top_k、arxiv_search_top_k等）；(4) 移除或不再使用Workflow特有的固定节点配置（如node_timeout、max_retries_per_node等固定流程控制参数）；(5) 保留业务逻辑相关配置：news_date_restrict_days（新闻时间限制）、result_quality_threshold（质量过滤阈值）、min_results_after_filter（降级触发阈值）、source_quota_per_type（多源配额）、rewrite_drift_threshold（漂移检测阈值）、max_summary_length（摘要长度限制）；这些配置在ReAct架构中同样需要被Agent或工具使用。判定为'不通过'的情况：缺少最大迭代步数配置；删除了LLM或搜索工具的核心配置；仍保留大量Workflow特有的流程编排配置；丢失了业务逻辑相关配置项。
- [ ] [08] 【移除固定流程编排】判断依据文件：<file>/workspace/input/output/react_agent.py</file>（或所有输出文件）。重构后的代码必须彻底移除Workflow架构的固定流程编排模式。具体要求：(1) 不存在原有的固定节点类（QueryAnalysisNode、SearchPlanNode、SearchExecutionNode、ResultRankingNode、SummaryGenerationNode）；(2) 不存在固定的节点列表按序执行逻辑；(3) 不存在WorkflowState在固定节点间传递的模式；(4) 搜索规划不再依赖固定的intent_tool_mapping映射表；(5) 代码体现ReAct的核心特征：根据推理动态决策，而非预定义流程。判定为'不通过'的情况：保留了固定节点类结构只是换了名字；仍存在固定的节点顺序执行逻辑；intent到tool的映射仍是硬编码规则。
- [ ] [09] 【查询改写语义漂移检测迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 或 <file>/workspace/input/output/tools.py</file>。原Workflow中 QueryAnalysisNode 实现了查询改写后的语义漂移检测逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 存在计算两个查询字符串词级相似度（如Jaccard重叠率）的函数或方法；(2) 改写后的查询与原始查询相似度低于阈值（rewrite_drift_threshold）时，回退使用原始查询，而非使用改写后的漂移查询；(3) 漂移检测阈值从配置中读取（config.rewrite_drift_threshold），不能硬编码；(4) 漂移检测结果（是否回退）需要在执行轨迹或状态中有所体现，便于调试；(5) 子查询拆分或后续搜索应基于漂移检测后最终采用的查询（回退后用原始查询，未回退用改写查询）。判定为'不通过'的情况：完全丢弃了漂移检测逻辑；漂移时使用了改写后的错误查询而非回退到原始查询；阈值硬编码而非从配置读取。
- [ ] [10] 【搜索结果质量过滤与降级兜底迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file> 或 <file>/workspace/input/output/tools.py</file>。原Workflow中 SearchExecutionNode 实现了质量过滤和降级兜底逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 工具调用返回结果后，按 relevance_score 阈值（result_quality_threshold）过滤低质量结果；(2) 过滤后有效结果数低于 min_results_after_filter 时，触发降级：放宽阈值（阈值减半）在原始结果上重新过滤，而非在已过滤结果上再次过滤；(3) 降级逻辑的阈值计算正确（threshold / 2），且 threshold 为 0 时跳过过滤；(4) 过滤结果的顺序与原始结果顺序一致（过滤不改变排列顺序）；(5) 质量过滤的结果（包括是否触发降级）需在执行轨迹的Observation中有所体现。判定为'不通过'的情况：完全丢弃了质量过滤逻辑；降级时在已过滤结果上再次过滤（导致结果更少）；阈值减半计算错误；过滤改变了结果顺序。
- [ ] [11] 【多源配额均衡迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。原Workflow中 ResultRankingNode 实现了多源配额均衡逻辑，ReAct架构必须保留并正确迁移此能力。具体要求：(1) 在收集到足够搜索结果后（通常在finish之前），对结果按来源（source字段）分组，每个来源最多保留 source_quota_per_type 条结果；(2) 配额截取应在按相关性排序之后进行（先排序再截取各来源Top-N）；(3) 各来源截取后的结果合并时需再次按 relevance_score 排序，不能简单拼接；(4) 某来源结果数不足配额时保留全部，不报错；(5) 配额值从配置中读取（config.source_quota_per_type），不能硬编码。判定为'不通过'的情况：完全丢弃了多源配额逻辑；配额截取在排序之前进行（导致截取的不是各来源最优结果）；合并后未重新排序；配额值硬编码。
- [ ] [12] 【摘要句子边界截断迁移】判断依据文件：<file>/workspace/input/output/react_agent.py</file>。原Workflow中 SummaryGenerationNode 实现了摘要句子边界截断逻辑，ReAct架构在生成最终回答时必须保留并正确迁移此能力。具体要求：(1) 生成的最终回答（finish动作的answer参数，或兜底回答）超出 max_summary_length 时触发截断；(2) 截断必须在句子边界处进行（支持中英文句子结束标点：。！？.!?），不能硬截到字符中间；(3) 截断时预留省略号（"..."）的长度，即在 max_summary_length - 3 范围内寻找最后一个句子边界；(4) 若找不到句子边界则退而求其次在单词边界（空格）处截断；(5) 截断后追加"..."，并在状态或轨迹中标记 answer_truncated=True。判定为'不通过'的情况：完全丢弃了截断逻辑；截断时未预留省略号长度导致总长度超出限制；截断在字符中间而非句子/单词边界；未标记截断状态。
