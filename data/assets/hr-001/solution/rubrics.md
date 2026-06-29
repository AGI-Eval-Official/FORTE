# Rubrics

> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则该任务整体判定为不通过。**

## 文件读取路径

```path
/workspace/input/answer/外卖商户BD简历筛选.txt
/workspace/input/answer/文本评测简历筛选.txt
```

```json
[
  {
    "id": "01",
    "content": "<file>/workspace/input/answer/文本评测简历筛选.txt</file>以及<file>/workspace/input/answer/外卖商户BD简历筛选.txt</file>均需包含周伦、孙博文、李雨桐、王琳达、赵晨曦5名候选人的简历筛选结果",
    "weight": 1
  },
  {
    "id": "02",
    "content": "<file>/workspace/input/answer/文本评测简历筛选.txt</file>以及<file>/workspace/input/answer/外卖商户BD简历筛选.txt</file>第一句话均为：'通过xx人，不通过xx人'，且通过和不通过的人数之和均为5",
    "weight": 1
  },
  {
    "id": "03",
    "content": "<file>/workspace/input/answer/文本评测简历筛选.txt</file>和<file>/workspace/input/answer/外卖商户BD简历筛选.txt</file>中，每位候选人的【简历筛选结论】字段，仅能填写'通过'或'不通过'",
    "weight": 1
  },
  {
    "id": "04",
    "content": "<file>/workspace/input/answer/外卖商户BD简历筛选.txt</file>和<file>/workspace/input/answer/文本评测简历筛选.txt</file>中，在各自文件内筛选结论为不通过的候选人，每位候选人以姓名为标题，其下简历筛选内容包含且仅包含【简历筛选结论】、【JD 匹配条目】、【亮点证据】、【风险与疑点】这4个字段，字段名称保持一致。如缺失前述4个必要字段中任意一个，或改动了字段名称，或生成了其他字段，均视为不通过",
    "weight": 1
  },
  {
    "id": "05",
    "content": "<file>/workspace/input/answer/外卖商户BD简历筛选.txt</file>和<file>/workspace/input/answer/文本评测简历筛选.txt</file>中，在各自文件内筛选结论为通过的候选人，每位候选人以姓名为标题，其下简历筛选内容需包含且仅包含【简历筛选结论】、【JD 匹配条目】、【亮点证据】、【风险与疑点】、【追问清单】、【建议面试轮次/侧重点】这6个字段，字段名称保持一致。如缺失前述6个必要字段中任意一个，或改动了字段名称，或生成了其他字段，均视为不通过",
    "weight": 1
  },
  {
    "id": "06",
    "content": "<file>/workspace/input/answer/外卖商户BD简历筛选.txt</file>中，王琳达的筛选结论为不通过，且【风险与疑点】字段中明确指出其学历（高中）不满足岗位要求（大专及以上）",
    "weight": 1
  },
  {
    "id": "07",
    "content": "<file>/workspace/input/answer/文本评测简历筛选.txt</file>中，孙博文的筛选结论为不通过，且【风险与疑点】字段中明确指出其AI相关工作经验（8个月）不满足岗位必要项要求（1年以上）",
    "weight": 1
  }
]
```
