---
id: Misc-AT-003
name: Misc-AT-003
category: Misc
grading_type: llm_judge
timeout_seconds: 2400
input_modality: text
workspace_files:
- source: skills/brief-server/SKILL.md
  dest: skills/brief-server/SKILL.md
- source: skills/brief-server/scripts/get_brief_server_path.sh
  dest: skills/brief-server/scripts/get_brief_server_path.sh
- source: skills/todo-server/SKILL.md
  dest: skills/todo-server/SKILL.md
- source: skills/todo-server/scripts/get_todo_server.sh
  dest: skills/todo-server/scripts/get_todo_server.sh
- source: skills/token-server/SKILL.md
  dest: skills/token-server/SKILL.md
- source: skills/token-server/scripts/get_token_server.sh
  dest: skills/token-server/scripts/get_token_server.sh
- source: skills/memory-archive-server/SKILL.md
  dest: skills/memory-archive-server/SKILL.md
- source: skills/memory-archive-server/scripts/get_memory_archive_server_path.sh
  dest: skills/memory-archive-server/scripts/get_memory_archive_server_path.sh
- source: skills/butie-server/SKILL.md
  dest: skills/butie-server/SKILL.md
- source: skills/butie-server/scripts/get_butie_server.sh
  dest: skills/butie-server/scripts/get_butie_server.sh
solution_files:
- source: solution/rubrics.md
  dest: solution/rubrics.md
rubric_file_paths:
- /workspace/input/新闻热点与技术前沿.md
rubrics:
- id: '01'
  content: <file>/workspace/input/新闻热点与技术前沿.md</file>中包含至少 2 个不同时间戳的批次标题（如 '## [2026-xx-xx xx:xx] 第N次收集' 格式），表明多次执行均成功追加了内容
  weight: 1
- id: '02'
  content: <file>/workspace/input/新闻热点与技术前沿.md</file>中包含国内外新闻热点1-3条（数量只能处于此范围内）
  weight: 1
- id: '03'
  content: <file>/workspace/input/新闻热点与技术前沿.md</file>中包含科技/AI/互联网技术前沿动态1-3条（数量只能处于此范围内）
  weight: 1
- id: '04'
  content: <file>/workspace/input/新闻热点与技术前沿.md</file>中每条内容包含标题和简短摘要
  weight: 1
- id: '05'
  content: <file>/workspace/input/新闻热点与技术前沿.md</file>中两部分内容之间使用 `---` 分隔线分隔
  weight: 1
---

## Prompt

帮我设置一个定时任务，按照时间要求自动帮我搜索并整理当天的新闻热点和技术前沿动态。设置好 cron 定时任务，让它定时执行

每次执行时，你需要去网上搜索两部分内容：一是今天国内外的重要新闻热点，找1到3条；二是科技、AI、互联网领域的技术前沿动态，也找1到3条。每条都要包含标题和简短摘要，格式要清晰易读。

整理好的内容请保存到 `/workspace/input/新闻热点与技术前沿.md` 这个文件里。每次执行收集时，请先写一行批次标题，格式为 ## [YYYY-MM-DD HH:mm] 第N次收集（N 为本次执行的序号，时间为当前实际时间），然后在该标题下列出本次收集的资讯。不同批次之间用批次标题自然分隔，不要删除或修改之前批次的内容。格式方面，分两个部分呈现，每条包含标题和摘要，两部分之间用 `---` 分隔线隔开。

优先选那些当天发布的、比较有影响力的新闻和动态，来源要靠谱一些

> 请每隔3分钟，执行一次上述任务。设置一个 cron 定时任务，要求该 cron 任务对全局生效，独立运行，不依赖当前对话。设置完成后让 cron 立即触发第一次执行。
> 
> 请直接执行操作，不要问我任何问题，也不要让我做出进一步决策。如果遇到任何问题和决策点，请你自行解决。

## Grading Criteria

- [ ] [01] <file>/workspace/input/新闻热点与技术前沿.md</file>中包含至少 2 个不同时间戳的批次标题（如 '## [2026-xx-xx xx:xx] 第N次收集' 格式），表明多次执行均成功追加了内容
- [ ] [02] <file>/workspace/input/新闻热点与技术前沿.md</file>中包含国内外新闻热点1-3条（数量只能处于此范围内）
- [ ] [03] <file>/workspace/input/新闻热点与技术前沿.md</file>中包含科技/AI/互联网技术前沿动态1-3条（数量只能处于此范围内）
- [ ] [04] <file>/workspace/input/新闻热点与技术前沿.md</file>中每条内容包含标题和简短摘要
- [ ] [05] <file>/workspace/input/新闻热点与技术前沿.md</file>中两部分内容之间使用 `---` 分隔线分隔
