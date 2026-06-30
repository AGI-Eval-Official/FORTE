<p align="center">
  <img src="figs/logo.png" alt="FORTE logo" width="320">
</p>

# FORTE: Full-Cycle Office Real-World Task Evaluation

FORTE (**F**ull-cycle **O**ffice **R**eal-world **T**ask **E**valuation) is a
general agent benchmark for evaluating AI agents on daily office productivity
across 15 corporate professions. Each
task ships as a single `.md` file with task description plus a multi-modal office environment (xlsx / docx /
pptx / pdf / csv / images / source files), and is scored by an **LLM judge**
that checks the agent's workspace artifacts against a set of expert-annotated rubrics.
A [Chinese version of this README](README_zh.md) is also available.

**Dataset**: The full benchmark contains 180 tasks, with at least 10 tasks per profession across all 15 corporate professions. This repository ships one demo task per profession, bundled with the input files, skills, and rubrics the evaluation depends on. The SRE profession's skills are not included because they depend on internal gateways. In addition to the profession-specific skills shipped with each task, we recommend installing a set of general-purpose skills (e.g., skills that assist with reading and editing office documents) to further improve agent performance. For example, the [Anthropic skills repository](https://github.com/anthropics/skills/tree/main) provides high-quality general skills such as [`docx`](https://github.com/anthropics/skills/tree/main/skills/docx), [`pptx`](https://github.com/anthropics/skills/tree/main/skills/pptx), [`xlsx`](https://github.com/anthropics/skills/tree/main/skills/xlsx), and [`pdf`](https://github.com/anthropics/skills/tree/main/skills/pdf).

**Leaderboard**: See the [FORTE Leaderboard](https://AGI-Eval-Official.github.io/FORTE/), evaluated on the full 180-task dataset.

## Overview

| Dimension          | FORTE |
|---|---|
| Task expression    | Single `.md` + YAML frontmatter; sections `## Prompt`, `## Grading Criteria` |
| Modalities         | Text + xlsx + docx + pptx + pdf + csv + images |
| Professions        | Marketing, Sales, BA, Operations, Dev, SRE, HR, Finance, PM, Legal, Algorithm, QA, UI/UX, Administration, and General |
| Grading            | LLM-as-judge, all-or-nothing scoring (i.e., `score = 1` iff every rubric item passes) |
| Metrics            | Avg@3, Pass@3, Pass^3 |
| Agent runtime      | [OpenClaw](https://github.com/openclaw/openclaw) inside a single Docker image |
| Requirements       | Python 3.10+ stdlib + `docker` CLI. |

## Dataset layout

```
data/
├── tasks/
│   └── <task_id>.md           # single .md per task; frontmatter + ## Prompt + ## Grading Criteria
└── assets/
    └── <task_id>/
        ├── input/             # initial workspace contents the agent sees
        ├── solution/          # reference answers used only by the judge
        └── skills/            # optional; lands in the agent's HOME at ~/.openclaw/skills
```

The frontmatter shape in `<task_id>.md`:

```yaml
---
id: dev-012
name: dev-012
category: dev
grading_type: llm_judge
timeout_seconds: 2400
workspace_files:
  - source: input/<file>
    dest: input/<file>
solution_files:
  - source: solution/<file>
    dest: solution/<file>
rubric_file_paths:
  - /workspace/input/<file>
  - /workspace/solution/<file>
rubrics:
  - id: '01'
    content: <rubric description; may include <file>…</file> tags>
    weight: 1
---
## Prompt
<the instruction the agent receives>

## Grading Criteria
- [ ] <human-readable summary of rubric 01>
```

`rubric_file_paths` and `<file>...</file>` tags reference files under two
virtual roots inside the container:

- `/workspace/input/...` — the agent's working tree
- `/workspace/solution/...` — the reference answers (read only by the judge)

## Quickstart

Requirements:

- Docker
- Python 3.10+ (stdlib only)

1. Configure the OpenAI-compatible gateway used by both the agent and judge:

```bash
cp openclaw_config/openclaw.json.example openclaw_config/openclaw.json
cp openclaw_config/.env.example          openclaw_config/.env
```

Edit both files with your gateway URL and API key. Secrets should live only in
these local config files.

2. (Optional but recommended) Install the Anthropic general-purpose office
skills (`docx` / `pptx` / `xlsx` / `pdf`). The runner auto-stages anything
under `data/extra_skills/` into every agent container's `~/.openclaw/skills/`
alongside each task's profession-specific skills, so agents have stronger
Office file handling on top of the profession skills shipped with each task.

```bash
bash scripts/install-anthropic-skills.sh
# Pick a subset or pin a tag:
#   SKILLS="docx xlsx" bash scripts/install-anthropic-skills.sh
#   ANTHROPIC_SKILLS_REF=v1.2.3 bash scripts/install-anthropic-skills.sh
```

The cloned skills land under `data/extra_skills/`. Re-run the script to refresh from upstream.

3. Build the agent image.

macOS users can use Docker Desktop or Colima. If you use Docker Desktop, start
Docker Desktop first; if you use Colima, run `colima start` instead. Make sure
the active Docker context matches the daemon you started.

```bash
# Docker Desktop:
open -a Docker
# If needed, select the Docker Desktop context shown by `docker context ls`,
# commonly one of:
# docker context use desktop-linux
# docker context use default

# Or, if you use Colima instead of Docker Desktop:
# colima start
# docker context use colima

docker info
bash docker/fetch-lo.sh
docker build -f docker/Dockerfile.agent -t forte-agent:latest docker/
```

Linux users should start the Docker service first. If your user is not in the
`docker` group, prefix Docker commands with `sudo`.

```bash
sudo systemctl start docker
docker info
bash docker/fetch-lo.sh
docker build -f docker/Dockerfile.agent -t forte-agent:latest docker/
```

Windows users should use Docker Desktop with the WSL 2 backend, then run the
commands inside a WSL terminal.

```bash
# Start Docker Desktop from Windows first, then run these in WSL.
docker info
bash docker/fetch-lo.sh
docker build -f docker/Dockerfile.agent -t forte-agent:latest docker/
```

4. Run:

```bash
bash scripts/run.sh   # runs all tasks with the default model from openclaw.json

# Or run the benchmark CLI directly with an explicit model:
python scripts/benchmark.py \
  --model your-gateway/claude-sonnet-4.6 \
  --dataset ./data \
  --runs 3 \
  --concurrency 1 \
  --output-dir ./results

# Optional: run one task, override the model, or increase parallelism.
TASK_ID=administration-001 bash scripts/run.sh
MODEL=your-gateway/claude-sonnet-4.6 bash scripts/run.sh
RUNS=3 CONCURRENCY=2 bash scripts/run.sh
```

Defaults: `MODEL` is read from `agents.defaults.model.primary` in
`openclaw_config/openclaw.json` (the example config uses
`claude-sonnet-4.6`), `RUNS=3`, and `CONCURRENCY=1`. Higher concurrency starts
more Docker containers in parallel, so raise it only if your machine and API
rate limits can handle it.

Each completed run lands the following files under
`<output-dir>/<model_slug>/<task_id>[_run_N]/`:

| File                   | Notes                                                                 |
|---|---|
| `grading.json`         | score (0/1), per-rubric breakdown, anomalies                          |
| `openclaw_trace.json`  | raw agent event stream                                                |
| `openai_messages.json` | flattened OpenAI chat-completions view of the trace                   |
| `judge_prompt.json`    | exact judge inputs (system prompt + user prompt + image/pdf manifest) |
| `workspace/`           | snapshot of the agent's working directory after it finished           |

## Metrics

Each task is run 3 times. Per-run grading uses **all-or-nothing scoring**: a
run scores 1 only if every rubric in `## Grading Criteria` passes; otherwise
0. The leaderboard reports three metrics, all computed per task and then macro
averaged across tasks:

| Metric    | Meaning                                                       |
|---|---|
| `Avg@3`   | Mean score across the 3 runs.                                 |
| `Pass@3`  | 1 if at least one of the 3 runs scores 1, else 0.             |
| `Pass^3`  | 1 only if all 3 runs score 1, else 0 — a consistency measure. |

To aggregate results across all models in `./results/`:

```bash
python scripts/aggregate.py                           # all models, all tasks, k=3
python scripts/aggregate.py --model your-gateway/claude-sonnet-4.6
python scripts/aggregate.py --tasks Finance-018,Legal-020
python scripts/aggregate.py --per-task                # add per-(model, task) breakdown
python scripts/aggregate.py --json                    # machine-readable output
```

## Project layout

```
.
├── data/                       # tasks + assets (shipped with the repo)
├── docker/
│   ├── Dockerfile.agent        # OpenClaw + LibreOffice + CJK fonts + judge deps
│   ├── fetch-lo.sh             # pre-stages LibreOffice tarballs for the build
│   ├── agent-requirements.txt
│   └── judge-requirements.txt
├── openclaw_config/
│   ├── openclaw.json.example   # gateway config template
│   └── .env.example            # API keys / headers template
├── scripts/                    # host orchestrator (stdlib only)
│   ├── benchmark.py            # CLI entrypoint
│   ├── aggregate.py            # Avg@k / Pass@k / Pass^k aggregator
│   ├── lib_docker.py           # container lifecycle + workspace snapshot
│   ├── lib_agent.py            # OpenClaw agent driver
│   ├── lib_grading.py          # judge launcher + result aggregation
│   ├── lib_tasks.py            # task `.md` + frontmatter parser
│   ├── lib_anomalies.py        # anomaly detection rules
│   └── run.sh                  # convenience benchmark wrapper
├── judge/                      # in-container judge (system prompt, file readers, grader)
├── figs/                       # logo
├── README.md / README_zh.md
└── LICENSE
```

## Acknowledgement

This repo is built on top of [QwenClawBench](https://github.com/SKYLENAGE-AI/QwenClawBench).
We also acknowledge other open-source contributions from the community, such as [PinchBench](https://github.com/pinchbench/skill), [Claw-Eval](https://github.com/claw-eval/claw-eval), [ZClawBench](https://huggingface.co/datasets/zai-org/ZClawBench), and [WildClawBench](https://github.com/InternLM/WildClawBench).

## Citation

If you find this repo helpful or relevant to your research, please kindly cite:

```bibtex
@misc{FORTE,
    title        = {{FORTE}: Full-Cycle Office Real-World Task Evaluation for AI Agents Across 15 Corporate Professions},
    author       = {{LongCat Team}},
    howpublished = {\url{https://github.com/AGI-Eval-Official/FORTE}},
    month        = jun,
    year         = {2026}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.


## Support

For questions and support, please open an issue on GitHub or contact the maintainers.

- Xin Gao — `gaoxin60@meituan.com`
- Jiaxing Liu - `liujiaxing10@meituan.com`
- Linsen Guo - `guolinsen@meituan.com`
- Mingyang Zhu - `zhumingyang09@meituan.com`
- Shengnan An — `anshengnan@meituan.com`
- Xiaoyu Li - `lixiaoyu28@meituan.com`
- Xiping Cong - `congxiping@meituan.com`
- Xuezhi Cao - `caoxuezhi@meituan.com`
- Yuhuai Wei - `weiyuhuai@meituan.com`
- Yunke Zhao - `zhaoyunke@meituan.com`
- Zhifeng Li - `lizhifeng05@meituan.com`
- Zijian Zhang - `zhangzijian14@meituan.com`
- Ziwen Wang - `wangziwen03@meituan.com`
