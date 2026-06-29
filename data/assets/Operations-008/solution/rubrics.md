# Rubrics

> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则改任务整体判定为不通过。**

## 文件读取路径

```path
/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx
```

```json
[
  {
    "id": "01",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中必须包含流程图",
    "weight": 1
  },
  {
    "id": "02",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图需要保证闭环，开始节点数量为1",
    "weight": 1
  },
  {
    "id": "03",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图必须在发起外呼拨号之前存在外呼时段合规判断节点，且该节点的不合规出边必须指向停止外呼类终态，不得直接进入拨号流程",
    "weight": 1
  },
  {
    "id": "04",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图需要有区分是否接通的判断节点，同时有接通/未接通两条出边",
    "weight": 1
  },
  {
    "id": "05",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图在未接通分支下需要有今日已拨次数是否达上限的判断节点，节点需要对同一客户每日拨打不得超过 3 次，1小时内不得超过 1 次进行判断，且达上限的出边必须指向停止外呼类终态，未达上限的出边才能指向重拨队列",
    "weight": 1
  },
  {
    "id": "06",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图在接通分支下必须存在录音告知处理节点（告知客户本次通话将被录音），且该节点必须出现在身份确认节点之前，不得在录音告知之前进行任何身份询问或信息收集操作",
    "weight": 1
  },
  {
    "id": "07",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图必须保证身份确认节点出现在开场告知/还款引导节点之前，不得在确认身份前进入任何涉及欠款信息的处理节点",
    "weight": 1
  },
  {
    "id": "08",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图必须存在身份确认节点，且该节点必须同时包含本人接通和非本人接通两条出边",
    "weight": 1
  },
  {
    "id": "09",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图在非本人接听分支下必须存在第三方是否要求不再联系的判断节点，且该节点的 是 出边必须指向加入禁呼名单终态",
    "weight": 1
  },
  {
    "id": "10",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图在本人接听确认后需要有区分用户态度的判断节点，且该节点至少有承诺还款和拒绝（含软拒绝/硬拒绝）两条出边",
    "weight": 1
  },
  {
    "id": "11",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图在接通分支下必须存在无效通话的处理路径（即客户接通后立即挂断或无法沟通的情形），该路径必须进入今日已拨次数判断节点，未达上限时才能安排重拨",
    "weight": 1
  },
  {
    "id": "12",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图需要保证以下场景有路径通向转人工：硬拒绝、投诉/异议、情绪激动超30秒",
    "weight": 1
  },
  {
    "id": "13",
    "content": "输出的<file>/workspace/input/外呼流程-M1逾期用户AI外呼催收流程图.docx</file>中的流程图所有终态节点必须能归入PTP登记、转人工跟进、安排重拨、停止外呼（达上限）、加入禁呼名单、案件升级六种结果之一",
    "weight": 1
  }
]
```