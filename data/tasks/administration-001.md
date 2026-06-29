---
id: administration-001
name: administration-001
category: administration
grading_type: llm_judge
timeout_seconds: 2400
input_modality: document
workspace_files:
- source: input/3月20日-4月20日入职时间表.csv
  dest: input/3月20日-4月20日入职时间表.csv
- source: input/入职物资权限软件分配.pdf
  dest: input/入职物资权限软件分配.pdf
- source: skills/company-admin-policy/SKILL.md
  dest: skills/company-admin-policy/SKILL.md
- source: skills/company-admin-policy/references/safety-regulations.md
  dest: skills/company-admin-policy/references/safety-regulations.md
- source: skills/meeting-minutes-generator/SKILL.md
  dest: skills/meeting-minutes-generator/SKILL.md
solution_files:
- source: solution/rubrics.md
  dest: solution/rubrics.md
- source: solution/入职资产匹配表参考答案.csv
  dest: solution/入职资产匹配表参考答案.csv
rubric_file_paths:
- /workspace/input/answer/入职资产匹配表.csv
- /workspace/solution/入职资产匹配表参考答案.csv
rubrics:
- id: '01'
  content: <file>/workspace/input/answer/入职资产匹配表.csv</file>的内容与<file>/workspace/solution/入职资产匹配表参考答案.csv</file>的内容完全一致。
  weight: 1
---

## Prompt

现在需要你根据员工入职时间表（`/workspace/input/3月20日-4月20日入职时间表.csv`）和资产分配文档（`/workspace/input/入职物资权限软件分配.pdf`），为员工自动匹配对应的办公物资和权限，生成的入职资产匹配表保存为`/workspace/input/answer/入职资产匹配表.csv`

要求如下：
1. 将`3月20日-4月20日入职时间表`中的内容复制到新表格中，删除掉表格中不在3月20日（含）-4月20日（含）的新员工的对应行。

2. 删除`紧急联系人`列。

3. 按照入职时间从早到晚进行排序。

4. 在末尾依次新增五列，列名为：`电脑`、`显示器`、`其余物资`、`软件权限空间`、`独立工位`，注意：
   - `其余物资`的部分仅输出具体物资名称，不要保留具体物资后括号内的内容
   - `独立工位`列填写`是`或`否`

5. 表格中内容列举都使用半角逗号分隔（如：大象 IM,学城文档,Microsoft 365），列举内容按照在分配文档中出现的顺序排列。

请直接执行操作，不要问我任何问题，也不要让我做出进一步决策。如果遇到任何问题和决策点，请你自行解决。

## Grading Criteria

- [ ] [01] <file>/workspace/input/answer/入职资产匹配表.csv</file>的内容与<file>/workspace/solution/入职资产匹配表参考答案.csv</file>的内容完全一致。
