# Rubrics

> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则该任务整体判定为不通过。**

## 文件读取路径

```path
/workspace/input/新闻热点与技术前沿.md
```

```json
[
  {
    "id": "01",
    "content": "<file>/workspace/input/新闻热点与技术前沿.md</file>中包含至少 2 个不同时间戳的批次标题（如 '## [2026-xx-xx xx:xx] 第N次收集' 格式），表明多次执行均成功追加了内容",
    "weight": 1
  },
  {
    "id": "02",
    "content": "<file>/workspace/input/新闻热点与技术前沿.md</file>中包含国内外新闻热点1-3条（数量只能处于此范围内）",
    "weight": 1
  },
  {
    "id": "03",
    "content": "<file>/workspace/input/新闻热点与技术前沿.md</file>中包含科技/AI/互联网技术前沿动态1-3条（数量只能处于此范围内）",
    "weight": 1
  },
  {
    "id": "04",
    "content": "<file>/workspace/input/新闻热点与技术前沿.md</file>中每条内容包含标题和简短摘要",
    "weight": 1
  },
  {
    "id": "05",
    "content": "<file>/workspace/input/新闻热点与技术前沿.md</file>中两部分内容之间使用 `---` 分隔线分隔",
    "weight": 1
  }
]
```