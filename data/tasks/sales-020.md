---
id: sales-020
name: sales-020
category: sales
grading_type: llm_judge
timeout_seconds: 2400
input_modality: text
workspace_files:
- source: input/客户画像调研问卷.csv
  dest: input/客户画像调研问卷.csv
- source: input/客户分类画像与差异化销售策略生成规则.md
  dest: input/客户分类画像与差异化销售策略生成规则.md
- source: skills/renewal-intent-stratifier/SKILL.md
  dest: skills/renewal-intent-stratifier/SKILL.md
- source: skills/renewal-intent-stratifier/reference/renewal-objection-playbook.md
  dest: skills/renewal-intent-stratifier/reference/renewal-objection-playbook.md
- source: skills/lead-conversion-analysis/SKILL.md
  dest: skills/lead-conversion-analysis/SKILL.md
- source: skills/lead-conversion-analysis/reference/reference.md
  dest: skills/lead-conversion-analysis/reference/reference.md
- source: skills/salesreport-server/SKILL.md
  dest: skills/salesreport-server/SKILL.md
- source: skills/salesreport-server/scripts/get_salesreport_server_path.sh
  dest: skills/salesreport-server/scripts/get_salesreport_server_path.sh
- source: skills/night-report-server/SKILL.md
  dest: skills/night-report-server/SKILL.md
- source: skills/night-report-server/scripts/get_night_report_server_path.sh
  dest: skills/night-report-server/scripts/get_night_report_server_path.sh
- source: skills/sales-exam-generator/SKILL.md
  dest: skills/sales-exam-generator/SKILL.md
- source: skills/sales-exam-generator/reference/extraction-rules.md
  dest: skills/sales-exam-generator/reference/extraction-rules.md
- source: skills/sales-exam-generator/reference/docx-format.md
  dest: skills/sales-exam-generator/reference/docx-format.md
- source: skills/sales-exam-generator/reference/prompt-rules.md
  dest: skills/sales-exam-generator/reference/prompt-rules.md
- source: skills/sales-assistant/SKILL.md
  dest: skills/sales-assistant/SKILL.md
- source: skills/sales-assistant/reference/outreach-email-rules.md
  dest: skills/sales-assistant/reference/outreach-email-rules.md
- source: skills/sales-assistant/reference/client-screening-rules.md
  dest: skills/sales-assistant/reference/client-screening-rules.md
- source: skills/sales-assistant/reference/sales-script-rules.md
  dest: skills/sales-assistant/reference/sales-script-rules.md
solution_files:
- source: solution/rubrics.md
  dest: solution/rubrics.md
rubric_file_paths:
- /workspace/input/answer/客户画像及销售策略.md
rubrics:
- id: '01'
  content: <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像表格的列名严格为：`样本ID`、`企业所在行业`、`企业规模`、`客户画像`
  weight: 1
- id: '02'
  content: <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为安全型的样本ID为：102、105、107，且客户画像表格中不含样本ID 106、110、111
  weight: 1
- id: '03'
  content: <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为敏捷型的样本ID为：103、108，且客户画像表格中不含样本ID 106、110、111
  weight: 1
- id: '04'
  content: <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为技术型的样本ID为：101、104、109，且客户画像表格中不含样本ID 106、110、111
  weight: 1
- id: '05'
  content: <file>/workspace/input/answer/客户画像及销售策略.md</file> 中'销售策略'部分，安全型、技术型、敏捷型客户的策略分别以`推荐话术`和`主推功能`作为独立标题
  weight: 1
- id: '06'
  content: <file>/workspace/input/answer/客户画像及销售策略.md</file> 中'客户分析'部分，分别以`画像分布`、`行业与规模特征`、`销售优先级建议`作为独立标题
  weight: 1
---

## Prompt

我司主营产品"企业级低代码开发平台"，问卷数据 `/workspace/input/客户画像调研问卷.csv` 收集了多维度的客户偏好评分。

阅览规则文档 `/workspace/input/客户分类画像与差异化销售策略生成规则.md` 的全部内容，

根据其中的数据清洗规则对问卷数据进行预处理，

再依据客户画像分类逻辑对客户进行归类，

最后按照输出报告规范制定差异化销售策略，

在 `/workspace/input/answer/客户画像及销售策略.md` 生成最终报告。

直接执行，不要问任何问题，也不要让我做出进一步决策。如果遇到任何问题和决策点，请你自行解决

## Grading Criteria

- [ ] [01] <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像表格的列名严格为：`样本ID`、`企业所在行业`、`企业规模`、`客户画像`
- [ ] [02] <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为安全型的样本ID为：102、105、107，且客户画像表格中不含样本ID 106、110、111
- [ ] [03] <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为敏捷型的样本ID为：103、108，且客户画像表格中不含样本ID 106、110、111
- [ ] [04] <file>/workspace/input/answer/客户画像及销售策略.md</file> 中客户画像为技术型的样本ID为：101、104、109，且客户画像表格中不含样本ID 106、110、111
- [ ] [05] <file>/workspace/input/answer/客户画像及销售策略.md</file> 中'销售策略'部分，安全型、技术型、敏捷型客户的策略分别以`推荐话术`和`主推功能`作为独立标题
- [ ] [06] <file>/workspace/input/answer/客户画像及销售策略.md</file> 中'客户分析'部分，分别以`画像分布`、`行业与规模特征`、`销售优先级建议`作为独立标题
