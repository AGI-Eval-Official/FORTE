---
id: Marketing-012
name: Marketing-012
category: Marketing
grading_type: llm_judge
timeout_seconds: 2400
input_modality: document
workspace_files:
- source: input/广告识别规则.docx
  dest: input/广告识别规则.docx
- source: input/竞品广告监测任务说明.docx
  dest: input/竞品广告监测任务说明.docx
- source: skills/survey-report-generator/SKILL.md
  dest: skills/survey-report-generator/SKILL.md
- source: skills/channel-conversion-analyst/SKILL.md
  dest: skills/channel-conversion-analyst/SKILL.md
- source: skills/retail-server/SKILL.md
  dest: skills/retail-server/SKILL.md
- source: skills/retail-server/scripts/get_retail_server_path.sh
  dest: skills/retail-server/scripts/get_retail_server_path.sh
- source: skills/marketing-risk-monitor/SKILL.md
  dest: skills/marketing-risk-monitor/SKILL.md
- source: skills/catering-market-analysis/SKILL.md
  dest: skills/catering-market-analysis/SKILL.md
solution_files:
- source: solution/rubrics.md
  dest: solution/rubrics.md
rubric_file_paths:
- /workspace/input/竞品广告采集.xlsx
rubrics:
- id: '01'
  content: 输出<file>/workspace/input/竞品广告采集.xlsx</file>，该文件包含10个sheet，sheet名称分别为：CRM客户管理系统、企业CRM软件、SaaS云端CRM、进销存CRM一体化、销售漏斗管理系统、企业微信CRM集成、CRM系统哪个好、 销售自动化、线索管理软件、客户关系管理
  weight: 1
- id: '02'
  content: <file>/workspace/input/竞品广告采集.xlsx</file>中每个sheet均包含10行数据（不含表头）
  weight: 1
- id: '03'
  content: <file>/workspace/input/竞品广告采集.xlsx</file>中每个sheet的表头为：标题、类型、链接、摘要
  weight: 1
- id: '04'
  content: <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'类型'列仅包含'SEM广告'或'SEO自然'两种值，无其他值
  weight: 1
- id: '05'
  content: <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'链接'列均为合法URL格式（以http://或https://开头）
  weight: 1
- id: '06'
  content: <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'摘要'列均非空
  weight: 1
- id: '07'
  content: <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'标题'列均非空
  weight: 1
---

## Prompt

读取 `/workspace/input/竞品广告监测任务说明.docx` 中的任务要求和关键词列表，以及 `/workspace/input/广告识别规则.docx` 中的广告判定规则，执行竞品广告采集任务，将结果保存至：
```
/workspace/input/竞品广告采集.xlsx
```

请直接执行命令，不要问任何问题，也不要让我做出进一步决策。如果遇到任何问题和决策点，请你自行解决。

## Grading Criteria

- [ ] [01] 输出<file>/workspace/input/竞品广告采集.xlsx</file>，该文件包含10个sheet，sheet名称分别为：CRM客户管理系统、企业CRM软件、SaaS云端CRM、进销存CRM一体化、销售漏斗管理系统、企业微信CRM集成、CRM系统哪个好、 销售自动化、线索管理软件、客户关系管理
- [ ] [02] <file>/workspace/input/竞品广告采集.xlsx</file>中每个sheet均包含10行数据（不含表头）
- [ ] [03] <file>/workspace/input/竞品广告采集.xlsx</file>中每个sheet的表头为：标题、类型、链接、摘要
- [ ] [04] <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'类型'列仅包含'SEM广告'或'SEO自然'两种值，无其他值
- [ ] [05] <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'链接'列均为合法URL格式（以http://或https://开头）
- [ ] [06] <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'摘要'列均非空
- [ ] [07] <file>/workspace/input/竞品广告采集.xlsx</file>中所有sheet的'标题'列均非空
