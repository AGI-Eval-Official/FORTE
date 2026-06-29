# Rubrics

> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则改任务整体判定为不通过。**

## 文件读取路径

```path
/workspace/input/answer/客户画像及销售策略.md
```

```json
[
  {
    "id": "01",
    "content": "<file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像表格的列名严格为：`样本ID`、`企业所在行业`、`企业规模`、`客户画像`",
    "weight": 1
  },
  {
    "id": "02",
    "content": "<file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为安全型的样本ID为：102、105、107，且客户画像表格中不含样本ID 106、110、111",
    "weight": 1
  },
  {
    "id": "03",
    "content": "<file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为敏捷型的样本ID为：103、108，且客户画像表格中不含样本ID 106、110、111",
    "weight": 1
  },
  {
    "id": "04",
    "content": "<file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为技术型的样本ID为：101、104、109，且客户画像表格中不含样本ID 106、110、111",
    "weight": 1
  },
  {
    "id": "05",
    "content": "<file>/workspace/input/answer/客户画像及销售策略.md</file> 中'销售策略'部分，安全型、技术型、敏捷型客户的策略分别以`推荐话术`和`主推功能`作为独立标题",
    "weight": 1
  },
  {
    "id": "06",
    "content": "<file>/workspace/input/answer/客户画像及销售策略.md</file> 中'客户分析'部分，分别以`画像分布`、`行业与规模特征`、`销售优先级建议`作为独立标题",
    "weight": 1
  }
]
```
