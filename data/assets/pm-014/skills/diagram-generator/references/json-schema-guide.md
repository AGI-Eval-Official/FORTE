# 流程图数据结构指南（三通道：A / B1 / B2）

用于统一流程图描述，并支持：
- 通道 A：MCP 工业级生成
- 通道 B1：无 MCP 预检直出
- 通道 B2：MCP 失效降级直出

## 根结构

```json
{
  "format": "mermaid|drawio|excalidraw",
  "title": "图标题",
  "diagramType": "flowchart|sequence|swimlane|state|activity|sop|approval|incident",
  "elements": [],
  "meta": {
    "author": "",
    "updatedAt": ""
  },
  "runtime": {
    "channel": "A|B1|B2",
    "mcpStatus": "available|not_found|failed",
    "degradeReason": "可选：超时/报错/无效返回"
  }
}
```

字段说明：
- `format`：目标输出格式（未指定时建议 `mermaid`）
- `title`：图标题
- `diagramType`：流程类型
- `elements`：节点与连线
- `meta`：可选元信息
- `runtime.channel`：本次落地通道（A/B1/B2）
- `runtime.mcpStatus`：MCP 状态（可用/未检测到/调用失败）
- `runtime.degradeReason`：仅 B2 建议填写失败原因

## 元素模型

### node

```json
{
  "id": "n-start",
  "type": "node",
  "name": "开始",
  "nodeType": "start|process|decision|io|subprocess|end|state",
  "owner": "可选：角色/系统",
  "lane": "可选：泳道",
  "geometry": {"x": 0, "y": 0, "width": 120, "height": 60},
  "style": {}
}
```

### edge

```json
{
  "id": "e-1",
  "type": "edge",
  "source": "n-start",
  "target": "n-end",
  "label": "可选：通过/失败/超时",
  "edgeType": "normal|yes|no|timeout|retry|exception",
  "style": {}
}
```

### lane（可选）

```json
{
  "id": "lane-1",
  "type": "lane",
  "name": "用户",
  "order": 1
}
```

## 最小可用约束

- `format`、`title`、`elements` 必填
- 节点 id 唯一
- 边的 `source/target` 必须存在
- 至少有一个起点和终点
- 决策节点至少 2 条带标签分支

## 通道 A 模板（MCP）

```json
{
  "diagram_spec": {
    "format": "drawio",
    "title": "发布上线流程",
    "diagramType": "sop",
    "elements": [
      {"id":"s","type":"node","name":"提交发布单","nodeType":"start"},
      {"id":"d1","type":"node","name":"检查是否通过","nodeType":"decision"},
      {"id":"ok","type":"node","name":"发布完成","nodeType":"end"},
      {"id":"e1","type":"edge","source":"s","target":"d1"},
      {"id":"e2","type":"edge","source":"d1","target":"ok","label":"通过"}
    ],
    "runtime": {
      "channel": "A",
      "mcpStatus": "available"
    }
  },
  "output_path": "diagrams/drawio/release-flow.drawio",
  "filename": "release-flow"
}
```

A 通道校验项：
- 工具调用成功
- 文件实际落盘
- 结构完整（起点/终点/分支）

## 通道 B1 模板（无 MCP 预检直出）

```json
{
  "format": "mermaid",
  "title": "采购审批流程",
  "diagramType": "approval",
  "elements": [
    {"id":"s","type":"node","name":"提交申请","nodeType":"start"},
    {"id":"d1","type":"node","name":"经理审批","nodeType":"decision"},
    {"id":"ok","type":"node","name":"审批通过","nodeType":"end"},
    {"id":"rej","type":"node","name":"驳回","nodeType":"end"},
    {"id":"e1","type":"edge","source":"s","target":"d1"},
    {"id":"e2","type":"edge","source":"d1","target":"ok","label":"通过"},
    {"id":"e3","type":"edge","source":"d1","target":"rej","label":"不通过"}
  ],
  "runtime": {
    "channel": "B1",
    "mcpStatus": "not_found"
  }
}
```

## 通道 B2 模板（MCP 失效降级直出）

```json
{
  "format": "drawio",
  "title": "发布上线流程",
  "diagramType": "sop",
  "elements": [
    {"id":"s","type":"node","name":"提交发布单","nodeType":"start"},
    {"id":"d1","type":"node","name":"检查是否通过","nodeType":"decision"},
    {"id":"ok","type":"node","name":"发布完成","nodeType":"end"},
    {"id":"e1","type":"edge","source":"s","target":"d1"},
    {"id":"e2","type":"edge","source":"d1","target":"ok","label":"通过"}
  ],
  "runtime": {
    "channel": "B2",
    "mcpStatus": "failed",
    "degradeReason": "generate_diagram timeout"
  }
}
```

B2 通道约束：
- 尽量复用 A 通道已解析结构，不重做需求理解
- 保持用户指定格式/路径/文件名优先级不变
- 补充 `degradeReason` 便于后续排查

## 常见错误

- 重复 id 导致结构冲突
- 决策节点分支不足
- 缺少起点/终点导致流程不闭合
- 边指向不存在节点导致断链
- B2 降级后丢失 A 通道已解析分支信息
