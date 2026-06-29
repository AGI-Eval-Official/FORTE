# Rubrics

> **通过标准：所有 rubric 均须满足，该任务才算通过。任一 rubric 不通过，则该任务整体判定为不通过。**

## 文件读取路径

```path
/workspace/input/竞品广告采集.xlsx
```

```json
[
  {
    "id": "01",
    "content": "输出<file>/workspace/input/竞品广告采集.xlsx</file>，该文件包含10个sheet，sheet名称分别为：CRM客户管理系统、企业CRM软件、SaaS云端CRM、进销存CRM一体化、销售漏斗管理系统、企业微信CRM集成、CRM系统哪个好、 销售自动化、线索管理软件、客户关系管理",
    "weight": 1
  },
  {
    "id": "02",
    "content": "<file>/workspace/input/竞品广告采集.xlsx</file>中每个sheet均包含10行数据（不含表头）",
    "weight": 1
  },
  {
    "id": "03",
    "content": "<file>/workspace/input/竞品广告采集.xlsx</file>中每个sheet的表头为：标题、类型、链接、摘要",
    "weight": 1
  },
  {
    "id": "04",
    "content": "<file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'类型'列仅包含'SEM广告'或'SEO自然'两种值，无其他值",
    "weight": 1
  },
  {
    "id": "05",
    "content": "<file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'链接'列均为合法URL格式（以http://或https://开头）",
    "weight": 1
  },
  {
    "id": "06",
    "content": "<file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'摘要'列均非空",
    "weight": 1
  },
  {
    "id": "07",
    "content": "<file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'标题'列均非空",
    "weight": 1
  }
]
```
