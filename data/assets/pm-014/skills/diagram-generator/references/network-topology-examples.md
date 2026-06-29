# 流程模板补充（三通道对照：A / B1 / B2）

本文件提供同类需求在三种通道下的落地方式：
- 通道 A：MCP 工业级生成
- 通道 B1：无 MCP 预检直出
- 通道 B2：MCP 失效降级直出

## 场景 1：网络故障排查流程

### A 通道（MCP）示例载荷

```json
{
  "diagram_spec": {
    "format": "drawio",
    "title": "网络故障排查流程",
    "diagramType": "incident",
    "elements": [
      {"id":"s","type":"node","name":"收到告警","nodeType":"start"},
      {"id":"d1","type":"node","name":"是否主干故障","nodeType":"decision"},
      {"id":"n1","type":"node","name":"切换备链路","nodeType":"process"},
      {"id":"n2","type":"node","name":"接入侧排查","nodeType":"process"},
      {"id":"e","type":"node","name":"复盘归档","nodeType":"end"},
      {"id":"e1","type":"edge","source":"s","target":"d1"},
      {"id":"e2","type":"edge","source":"d1","target":"n1","label":"是"},
      {"id":"e3","type":"edge","source":"d1","target":"n2","label":"否"},
      {"id":"e4","type":"edge","source":"n1","target":"e"},
      {"id":"e5","type":"edge","source":"n2","target":"e"}
    ],
    "runtime": {"channel":"A","mcpStatus":"available"}
  },
  "output_path": "diagrams/drawio/network-incident.drawio"
}
```

### B1 通道（无 MCP）示例结构

```json
{
  "format": "mermaid",
  "title": "网络故障排查流程",
  "diagramType": "incident",
  "elements": [
    {"id":"s","type":"node","name":"收到告警","nodeType":"start"},
    {"id":"d1","type":"node","name":"是否主干故障","nodeType":"decision"},
    {"id":"n1","type":"node","name":"切换备链路","nodeType":"process"},
    {"id":"n2","type":"node","name":"接入侧排查","nodeType":"process"},
    {"id":"e","type":"node","name":"复盘归档","nodeType":"end"},
    {"id":"e1","type":"edge","source":"s","target":"d1"},
    {"id":"e2","type":"edge","source":"d1","target":"n1","label":"是"},
    {"id":"e3","type":"edge","source":"d1","target":"n2","label":"否"},
    {"id":"e4","type":"edge","source":"n1","target":"e"},
    {"id":"e5","type":"edge","source":"n2","target":"e"}
  ],
  "runtime": {"channel":"B1","mcpStatus":"not_found"}
}
```

### B2 通道（MCP 失效降级）示例结构

```json
{
  "format": "drawio",
  "title": "网络故障排查流程",
  "diagramType": "incident",
  "elements": [
    {"id":"s","type":"node","name":"收到告警","nodeType":"start"},
    {"id":"d1","type":"node","name":"是否主干故障","nodeType":"decision"},
    {"id":"n1","type":"node","name":"切换备链路","nodeType":"process"},
    {"id":"n2","type":"node","name":"接入侧排查","nodeType":"process"},
    {"id":"e","type":"node","name":"复盘归档","nodeType":"end"},
    {"id":"e1","type":"edge","source":"s","target":"d1"},
    {"id":"e2","type":"edge","source":"d1","target":"n1","label":"是"},
    {"id":"e3","type":"edge","source":"d1","target":"n2","label":"否"},
    {"id":"e4","type":"edge","source":"n1","target":"e"},
    {"id":"e5","type":"edge","source":"n2","target":"e"}
  ],
  "runtime": {
    "channel": "B2",
    "mcpStatus": "failed",
    "degradeReason": "generate_diagram returned invalid payload"
  }
}
```

## 场景 2：发布上线流程

### A 通道（MCP）示例载荷

```json
{
  "diagram_spec": {
    "format": "drawio",
    "title": "发布上线流程",
    "diagramType": "sop",
    "elements": [
      {"id":"s","type":"node","name":"提交发布单","nodeType":"start"},
      {"id":"d1","type":"node","name":"检查是否通过","nodeType":"decision"},
      {"id":"n1","type":"node","name":"灰度发布","nodeType":"process"},
      {"id":"d2","type":"node","name":"监控是否异常","nodeType":"decision"},
      {"id":"ok","type":"node","name":"全量发布完成","nodeType":"end"},
      {"id":"rb","type":"node","name":"回滚并重试","nodeType":"end"},
      {"id":"e1","type":"edge","source":"s","target":"d1"},
      {"id":"e2","type":"edge","source":"d1","target":"n1","label":"通过"},
      {"id":"e3","type":"edge","source":"d1","target":"rb","label":"失败"},
      {"id":"e4","type":"edge","source":"n1","target":"d2"},
      {"id":"e5","type":"edge","source":"d2","target":"ok","label":"正常"},
      {"id":"e6","type":"edge","source":"d2","target":"rb","label":"异常"}
    ],
    "runtime": {"channel":"A","mcpStatus":"available"}
  },
  "output_path": "diagrams/drawio/release-sop.drawio"
}
```

### B1/B2 直出共用结构建议

```json
{
  "format": "mermaid",
  "title": "发布上线流程",
  "diagramType": "sop",
  "elements": [
    {"id":"s","type":"node","name":"提交发布单","nodeType":"start"},
    {"id":"d1","type":"node","name":"检查是否通过","nodeType":"decision"},
    {"id":"n1","type":"node","name":"灰度发布","nodeType":"process"},
    {"id":"d2","type":"node","name":"监控是否异常","nodeType":"decision"},
    {"id":"ok","type":"node","name":"全量发布完成","nodeType":"end"},
    {"id":"rb","type":"node","name":"回滚并重试","nodeType":"end"},
    {"id":"e1","type":"edge","source":"s","target":"d1"},
    {"id":"e2","type":"edge","source":"d1","target":"n1","label":"通过"},
    {"id":"e3","type":"edge","source":"d1","target":"rb","label":"失败"},
    {"id":"e4","type":"edge","source":"n1","target":"d2"},
    {"id":"e5","type":"edge","source":"d2","target":"ok","label":"正常"},
    {"id":"e6","type":"edge","source":"d2","target":"rb","label":"异常"}
  ],
  "runtime": {
    "channel": "B1 或 B2",
    "mcpStatus": "not_found 或 failed",
    "degradeReason": "仅 B2 可填"
  }
}
```

## 场景 3：网络变更审批（泳道）

### A/B1/B2 共用结构建议

```json
{
  "format": "drawio",
  "title": "网络变更审批流程",
  "diagramType": "swimlane",
  "elements": [
    {"id":"n1","type":"node","name":"提交申请","nodeType":"start","lane":"申请人"},
    {"id":"n2","type":"node","name":"技术评估","nodeType":"process","lane":"网络工程师"},
    {"id":"n3","type":"node","name":"审批决策","nodeType":"decision","lane":"审批人"},
    {"id":"n4","type":"node","name":"执行变更","nodeType":"process","lane":"值班同学"},
    {"id":"n5","type":"node","name":"回滚并记录","nodeType":"process","lane":"值班同学"},
    {"id":"n6","type":"node","name":"变更完成","nodeType":"end","lane":"申请人"},
    {"id":"e1","type":"edge","source":"n1","target":"n2"},
    {"id":"e2","type":"edge","source":"n2","target":"n3"},
    {"id":"e3","type":"edge","source":"n3","target":"n4","label":"通过"},
    {"id":"e4","type":"edge","source":"n3","target":"n5","label":"拒绝"},
    {"id":"e5","type":"edge","source":"n4","target":"n6"},
    {"id":"e6","type":"edge","source":"n5","target":"n6"}
  ]
}
```

## 快速改图指令示例

- “先做 MCP 检测：有就工业级生成，没有就直接给我 mermaid。”
- “MCP 如果中途失败，不要中断，直接按当前结构降级输出 drawio。”
- “把发布流程新增‘回归测试’节点，并放在灰度前。”

## 三通道统一质量检查

- 决策节点 >= 2 条分支
- 异常链路可闭环
- 起点到终点可达
- 文件真实写入
- 命名统一（动作 + 对象）
