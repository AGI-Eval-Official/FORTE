---
name: legal-risk-graph-builder
description: 当用户需要把法律分析文本转为结构化风险网络（风险节点、因果关系、关键路径、风险分级）时触发。本 SKILL 仅负责法律风险建模与评分，输出标准化 JSON 中间结果供下游能力复用。不适用于图形渲染、报告排版、文件命名与输出路径决策。
---

# Legal Risk Graph Builder

## SKILL 目的

将非结构化法律分析文本转换为可复用的风险图谱数据，形成“可计算、可追溯、可串联”的中间产物，供下游可视化与报告能力消费。

## 触发条件与职责边界

### 触发条件

当用户出现以下需求时触发：

- 法律风险结构化
- 风险节点抽取
- 风险传导分析
- 关键风险路径识别
- 风险分级/风险指数计算
- 将法律文本转为图谱/JSON

### 职责边界

- 本 SKILL 负责：
  - 从法律文本抽取风险节点和因果边
  - 对节点进行分类、评分和关键性识别
  - 计算路径级风险并输出结构化 JSON
- 本 SKILL 不负责：
  - 渲染雷达图/矩阵图/路径图/决策树
  - 生成 docx/ppt/pdf 等最终交付文件
  - 规定输出文件名、输出路径、排版样式
  - 安装或调用外部图形工具命令

## 输入要求

### 必填输入

- `legal_text`: string，法律分析正文（可来自合同纠纷、劳动争议、知识产权等场景）

### 选填输入

- `case_type`: string，案件类型
- `parties`: array，涉及主体
- `risk_dimensions`: array，风险维度候选（默认从合规/诉讼/财务/声誉/执行/运营中自动选择 4-6 个）
- `output_schema_version`: string，默认 `risk_graph_v1`

### 输入前提

- 输入文本应为可读中文内容
- 若上游输入为 docx/pdf/image，应先通过文本抽取类 SKILL 转成 `legal_text`

## 输出要求（中间结果）

输出统一为 JSON 对象，不绑定文件名和路径：

```json
{
  "schema_version": "risk_graph_v1",
  "risk_dimensions": ["合规风险", "诉讼风险", "财务风险", "执行风险"],
  "nodes": [
    {
      "id": "N1",
      "name": "交付验收标准不明确",
      "node_type": "fact",
      "evidence": "原文引用",
      "p": 0.7,
      "i": 0.8,
      "c": 0.4,
      "r": 0.3,
      "risk_score": 0.2352,
      "dimension": "执行风险"
    }
  ],
  "edges": [
    {
      "from": "N1",
      "to": "N2",
      "causal_type": "explicit",
      "confidence": "high",
      "weight": 0.9,
      "evidence": "原文引用"
    }
  ],
  "paths": [
    {
      "path_id": "P1",
      "node_ids": ["N1", "N2", "N4"],
      "path_risk": 0.127,
      "is_critical": true
    }
  ],
  "key_nodes": {
    "root": ["N1"],
    "amplifier": ["N2"],
    "controllable": ["N2"],
    "critical_path_nodes": ["N1", "N2", "N4"]
  },
  "quality_flags": [
    "存在低置信度隐含因果边 1 条，需人工复核"
  ]
}
```

## 领域规则

### 节点类型（四类）

- `fact`: 客观事实或状态（风险源头）
- `legal_judgment`: 需法律推理的判断（中间环节）
- `risk_outcome`: 法律后果（风险后果）
- `business_impact`: 业务影响（经营后果）

### 因果边与置信度

- 显式因果（high）：包含“导致/因此/若...则.../引发”等直接连接词
- 隐含因果（medium/low）：通过上下文关系推断，必须保留证据说明

### 权重规则

- 强传导：`0.9`
- 中传导：`0.6`
- 弱传导：`0.3`
- 条件传导：`0.1-0.9`（需在 evidence 中说明条件）

### 计算规则

- 节点风险指数：

```text
risk_score = p * i * (1 - c) * (1 - r)
```

- 路径传导风险值：

```text
path_risk = source_risk_score * Π(edge_weight)
```

- 多入边汇聚默认 OR：取最大入边传导值
- 明确“同时满足”时使用 AND：取入边传导值乘积

## 工作流

1. 读取并理解法律文本，识别案件背景、争议焦点、涉事主体
2. 抽取风险候选表述（风险描述、不确定性、后果、条件触发）
3. 生成节点并去重归一，每个节点必须绑定原文证据
4. 节点四分类并评估 `p/i/c/r`
5. 建立因果边：先显式、后隐含，并标注置信度与权重
6. 计算 `risk_score` 与 `path_risk`，识别关键节点和关键路径
7. 生成 `risk_graph_v1` JSON 结果与 `quality_flags`

## 判断规则（完成标准）

满足以下条件才算执行完成：

- 每个节点都包含 `id/name/node_type/evidence`
- 每条边都包含 `from/to/weight/confidence/evidence`
- 每个节点都完成 `p/i/c/r/risk_score` 计算
- 至少识别出一条风险路径；若无法形成路径，需在 `quality_flags` 说明原因
- 所有低置信度关系都必须明确标记，禁止伪确定性输出

## 异常处理

- 输入为空或不可读：返回结构化错误，指出缺失字段 `legal_text`
- 文本事实不足：输出最小图谱并在 `quality_flags` 标注“证据不足”
- 结论冲突：保留并行边，分别标注证据来源与置信度
- 无法判定权重：降级为 `0.3` 并标记“待人工复核”
- 超长文本：先分段抽取后汇总去重，防止遗漏关键节点


## Checklist

执行结束前完成以下自检：

- [ ] 是否严格只输出“风险图谱中间结果”，未越界到渲染和交付排版
- [ ] 是否所有节点/边都有原文证据可追溯
- [ ] 是否所有计算字段可复算
- [ ] 是否对低置信度关系给出明确标记
- [ ] 是否输出为标准 `risk_graph_v1` 结构
