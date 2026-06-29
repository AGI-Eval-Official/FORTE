---
id: uiux-021
name: uiux-021
category: uiux
grading_type: llm_judge
timeout_seconds: 2400
input_modality: document
workspace_files:
- source: input/交互行为痛点及优化规则.md
  dest: input/交互行为痛点及优化规则.md
- source: input/页面级交互规范.docx
  dest: input/页面级交互规范.docx
- source: input/用户交互行为日志.xlsx
  dest: input/用户交互行为日志.xlsx
- source: skills/design-spec-skill/SKILL.md
  dest: skills/design-spec-skill/SKILL.md
- source: skills/design-spec-skill/references/shared-rules.md
  dest: skills/design-spec-skill/references/shared-rules.md
- source: skills/design-spec-skill/references/android-rules.md
  dest: skills/design-spec-skill/references/android-rules.md
- source: skills/design-spec-skill/references/mini-program-rules.md
  dest: skills/design-spec-skill/references/mini-program-rules.md
- source: skills/design-spec-skill/references/mobile-rules.md
  dest: skills/design-spec-skill/references/mobile-rules.md
- source: skills/design-spec-skill/references/ios-rules.md
  dest: skills/design-spec-skill/references/ios-rules.md
- source: skills/design-spec-skill/references/h5-rules.md
  dest: skills/design-spec-skill/references/h5-rules.md
- source: skills/ux-competitive-analysis/SKILL.md
  dest: skills/ux-competitive-analysis/SKILL.md
- source: skills/ux-competitive-analysis/references/default-rules.md
  dest: skills/ux-competitive-analysis/references/default-rules.md
solution_files:
- source: solution/交互规范优化方案参考答案.csv
  dest: solution/交互规范优化方案参考答案.csv
- source: solution/rubrics.md
  dest: solution/rubrics.md
rubric_file_paths:
- /workspace/input/交互规范优化方案.csv
- /workspace/solution/交互规范优化方案参考答案.csv
rubrics:
- id: '01'
  content: 输出的<file>/workspace/input/交互规范优化方案.csv</file>中，表头顺序依次为：页面名称、交互元素、痛点类型、优先级、痛点分析、优化建议
  weight: 1
- id: '02'
  content: 输出的<file>/workspace/input/交互规范优化方案.csv</file>中，A、B、C、D列的内容与<file>/workspace/solution/交互规范优化方案参考答案.csv</file>中A、B、C、D列的内容一致
  weight: 1
---

## Prompt

打开`/workspace/input/`文件夹，

其中`用户交互行为日志.xlsx`是后台导出的近期用户交互行为日志，

请根据`交互行为痛点及优化规则.md`，梳理近期出现的交互痛点对应的交互元素及优化优先级，并结合失败原因进行痛点分析，给出优化建议。整理为：
```
/workspace/input/交互规范优化方案.csv
```
表头顺序为：页面名称、交互元素、痛点类型、优先级、痛点分析、优化建议

输出的表格行顺序先按优先级排列（P0-P1-P2-P3-P4,P0排最前），优先级一致的行再按`页面级交互规范.docx`中交互元素出现的先后顺序排列，如仍有内容一致行，按照`交互行为痛点及优化规则.md`中痛点类型出现的先后顺序排列。

不要问我任何问题，也不要让我做出进一步决策。如果遇到任何问题和决策点，请你自行解决。

## Grading Criteria

- [ ] [01] 输出的<file>/workspace/input/交互规范优化方案.csv</file>中，表头顺序依次为：页面名称、交互元素、痛点类型、优先级、痛点分析、优化建议
- [ ] [02] 输出的<file>/workspace/input/交互规范优化方案.csv</file>中，A、B、C、D列的内容与<file>/workspace/solution/交互规范优化方案参考答案.csv</file>中A、B、C、D列的内容一致
