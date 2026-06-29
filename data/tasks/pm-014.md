---
id: pm-014
name: pm-014
category: pm
grading_type: llm_judge
timeout_seconds: 2400
input_modality: document
workspace_files:
- source: input/功能测试报告.xlsx
  dest: input/功能测试报告.xlsx
- source: input/PRD_v2.5.md
  dest: input/PRD_v2.5.md
- source: input/线上兼容环境测试报告.xlsx
  dest: input/线上兼容环境测试报告.xlsx
- source: input/上线配置清单.xlsx
  dest: input/上线配置清单.xlsx
- source: skills/pm-metric-rca/SKILL.md
  dest: skills/pm-metric-rca/SKILL.md
- source: skills/pm-metric-rca/reference/metric-dimension-map.md
  dest: skills/pm-metric-rca/reference/metric-dimension-map.md
- source: skills/pm-metric-rca/reference/funnel-methodology.md
  dest: skills/pm-metric-rca/reference/funnel-methodology.md
- source: skills/pm-metric-rca/reference/glossary.md
  dest: skills/pm-metric-rca/reference/glossary.md
- source: skills/pm-metric-rca/reference/funnel-benchmark.md
  dest: skills/pm-metric-rca/reference/funnel-benchmark.md
- source: skills/prd-drafting/SKILL.md
  dest: skills/prd-drafting/SKILL.md
- source: skills/prd-drafting/assets/prd-template.md
  dest: skills/prd-drafting/assets/prd-template.md
- source: skills/prd-drafting/reference/example-us.md
  dest: skills/prd-drafting/reference/example-us.md
- source: skills/prd-drafting/reference/prd-writing-guide.md
  dest: skills/prd-drafting/reference/prd-writing-guide.md
- source: skills/persona-research/SKILL.md
  dest: skills/persona-research/SKILL.md
- source: skills/persona-research/evals/evals.json
  dest: skills/persona-research/evals/evals.json
- source: skills/persona-research/references/persona-templates.md
  dest: skills/persona-research/references/persona-templates.md
- source: skills/persona-research/references/industry-slots.md
  dest: skills/persona-research/references/industry-slots.md
- source: skills/persona-research/references/data-schema.md
  dest: skills/persona-research/references/data-schema.md
- source: skills/persona-research/references/industry-extensions.md
  dest: skills/persona-research/references/industry-extensions.md
- source: skills/competitive-analysis/SKILL.md
  dest: skills/competitive-analysis/SKILL.md
- source: skills/product-manual-generator/SKILL.md
  dest: skills/product-manual-generator/SKILL.md
- source: skills/product-manual-generator/reference/web-rules.md
  dest: skills/product-manual-generator/reference/web-rules.md
- source: skills/product-manual-generator/reference/create-rules.md
  dest: skills/product-manual-generator/reference/create-rules.md
- source: skills/product-manual-generator/reference/update-rules.md
  dest: skills/product-manual-generator/reference/update-rules.md
- source: skills/product-manual-generator/reference/miniprogram-rules.md
  dest: skills/product-manual-generator/reference/miniprogram-rules.md
- source: skills/product-manual-generator/reference/app-rules.md
  dest: skills/product-manual-generator/reference/app-rules.md
- source: skills/product-manual-generator/reference/product-manual-rules.md
  dest: skills/product-manual-generator/reference/product-manual-rules.md
- source: skills/product-manual-generator/reference/version-rules.md
  dest: skills/product-manual-generator/reference/version-rules.md
- source: skills/survey-designer/SKILL.md
  dest: skills/survey-designer/SKILL.md
- source: skills/survey-designer/evals/evals.json
  dest: skills/survey-designer/evals/evals.json
- source: skills/survey-designer/references/question-bank.md
  dest: skills/survey-designer/references/question-bank.md
- source: skills/survey-designer/references/output-formats.md
  dest: skills/survey-designer/references/output-formats.md
- source: skills/ab-test-analyst/SKILL.md
  dest: skills/ab-test-analyst/SKILL.md
- source: skills/ab-test-analyst/references/pricing-promotion-rules.md
  dest: skills/ab-test-analyst/references/pricing-promotion-rules.md
- source: skills/ab-test-analyst/references/push-notification-rules.md
  dest: skills/ab-test-analyst/references/push-notification-rules.md
- source: skills/ab-test-analyst/references/e-commerce-rules.md
  dest: skills/ab-test-analyst/references/e-commerce-rules.md
- source: skills/ab-test-analyst/references/onboarding-rules.md
  dest: skills/ab-test-analyst/references/onboarding-rules.md
- source: skills/ab-test-analyst/references/content-ui-rules.md
  dest: skills/ab-test-analyst/references/content-ui-rules.md
- source: skills/ab-test-analyst/references/recommendation-rules.md
  dest: skills/ab-test-analyst/references/recommendation-rules.md
- source: skills/diagram-generator/SKILL.md
  dest: skills/diagram-generator/SKILL.md
- source: skills/diagram-generator/references/format-selection-guide.md
  dest: skills/diagram-generator/references/format-selection-guide.md
- source: skills/diagram-generator/references/json-schema-guide.md
  dest: skills/diagram-generator/references/json-schema-guide.md
- source: skills/diagram-generator/references/no-mcp-fallback-direct-output.md
  dest: skills/diagram-generator/references/no-mcp-fallback-direct-output.md
- source: skills/diagram-generator/references/network-topology-examples.md
  dest: skills/diagram-generator/references/network-topology-examples.md
solution_files:
- source: solution/rubrics.md
  dest: solution/rubrics.md
rubric_file_paths:
- /workspace/input/上线合规校验报告.docx
rubrics:
- id: '01'
  content: 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，需包含以下相关内容：（1）上线结论评估：是否可上线的结论及原因说明；未提交测试的功能、测试不通过的功能、兼容测试为兼容问题的功能；风险分级；（2）上线改进计划：未提测功能的后期提测计划；针对不同风险分级的改进计划
  weight: 1
- id: '02'
  content: 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论评估部分,给出“不可上线”的结论或等价表述，并说明原因为存在以下任意情况：P0 功能提测率不达标、P0 功能测试通过率不达标、P1 功能完成率不达标、存在严重等级问题
  weight: 1
- id: '03'
  content: 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论评估部分的P0功能提测覆盖率为71.4%；P0功能用例通过率为93.4%，P1功能用例通过率为86.4%，P2功能用例通过率为85.7%；P0功能完成率为60.0%，P1功能完成率为40.0%，P2功能完成率为33.3%；综合用例通过率为89.7%
  weight: 1
- id: '04'
  content: 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论评估部分未提交测试的功能为：拦截通知推送、实验流量分配、实验报告导出、多语言包上传、翻译缺失兜底配置；测试不通过的功能为：敏感词过滤规则配置、实验数据看板、实验暂停与恢复、语言包版本管理；测试结论为兼容问题的功能如下：人工复核队列、审核规则模板管理、实验数据看板、界面语言预览、语言包版本管理
  weight: 1
- id: '05'
  content: 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论部分不同风险等级对应的功能如下：严重等级对应的功能有：审核日志查看、实验数据看板、界面语言预览、语言包版本管理；主要等级对应的功能有敏感词过滤规则配置、实验暂停与恢复；次要等级对应的功能有人工复核队列、审核规则模板管理
  weight: 1
---

## Prompt

AIPilot Console v2.5 即将迭代上线，以下为研发团队提交的上线配置清单、功能测试及线上兼容测试报告。
```
/workspace/input/上线配置清单.xlsx
/workspace/input/功能测试报告.xlsx
/workspace/input/线上兼容环境测试报告.xlsx
```
读取以上信息，并结合
```
/workspace/input/PRD_v2.5.md
```
给出**上线合规校验报告**，输出为：
```
/workspace/input/上线合规校验报告.docx
```
报告需要覆盖以下相关内容:
1. 上线结论评估：
- 是否可上线的结论及原因说明（需提供相关数据：包括P0功能提测覆盖率，各等级功能的功能用例通过率、功能完成率，综合用例通过率）
- 未提交测试的功能、测试不通过的功能、兼容测试为兼容问题的功能
- 风险分级：写明涉及不同风险等级的功能有哪些

2. 上线改进计划：
- 未提测功能的后期提测计划
- 针对不同风险分级的改进计划

不要问我任何问题，也不要让我做出进一步决策。

## Grading Criteria

- [ ] [01] 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，需包含以下相关内容：（1）上线结论评估：是否可上线的结论及原因说明；未提交测试的功能、测试不通过的功能、兼容测试为兼容问题的功能；风险分级；（2）上线改进计划：未提测功能的后期提测计划；针对不同风险分级的改进计划
- [ ] [02] 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论评估部分,给出“不可上线”的结论或等价表述，并说明原因为存在以下任意情况：P0 功能提测率不达标、P0 功能测试通过率不达标、P1 功能完成率不达标、存在严重等级问题
- [ ] [03] 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论评估部分的P0功能提测覆盖率为71.4%；P0功能用例通过率为93.4%，P1功能用例通过率为86.4%，P2功能用例通过率为85.7%；P0功能完成率为60.0%，P1功能完成率为40.0%，P2功能完成率为33.3%；综合用例通过率为89.7%
- [ ] [04] 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论评估部分未提交测试的功能为：拦截通知推送、实验流量分配、实验报告导出、多语言包上传、翻译缺失兜底配置；测试不通过的功能为：敏感词过滤规则配置、实验数据看板、实验暂停与恢复、语言包版本管理；测试结论为兼容问题的功能如下：人工复核队列、审核规则模板管理、实验数据看板、界面语言预览、语言包版本管理
- [ ] [05] 输出的<file>/workspace/input/上线合规校验报告.docx</file>中，上线结论部分不同风险等级对应的功能如下：严重等级对应的功能有：审核日志查看、实验数据看板、界面语言预览、语言包版本管理；主要等级对应的功能有敏感词过滤规则配置、实验暂停与恢复；次要等级对应的功能有人工复核队列、审核规则模板管理
