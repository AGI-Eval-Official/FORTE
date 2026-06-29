<p align="center">
  <img src="figs/logo.png" alt="FORTE logo" width="320">
</p>

# FORTE: Full-Cycle Office Real-World Task Evaluation

FORTE（**F**ull-cycle **O**ffice **R**eal-world **T**ask **E**valuation）是一个面向 AI agents 的通用评测基准，覆盖 15 个企业职能序列的日常办公生产力任务。
每个任务包含一份 `.md` 任务描述文件 + 多模态办公环境（xlsx / docx / pptx / pdf / csv / 图片 / 源码）。
任务完成得分由 **LLM judge** 对照专家标注的 rubrics 给 agent 的工作区产物打分。
英文版介绍 见 [README.md](README.md)。

**数据集**：完整 benchmark 共 180 条任务，覆盖 15 个企业职能序列，每个序列至少 10 条。本仓库为每个序列展示一条 demo task，配套提供评测依赖的输入文件，skills 以及 rubrics；其中 SRE 序列的 skills 依赖内部网关，因此未在仓库中提供。除仓库中提供的与职能序列相关的 skills 外，建议大家再安装一些通用 skills（例如辅助 office 文件读写与理解的 skills）来提升模型的任务表现。例如，[Anthropic skills 仓库](https://github.com/anthropics/skills/tree/main) 提供了高质量的通用 skills，如 [`docx`](https://github.com/anthropics/skills/tree/main/skills/docx)、[`pptx`](https://github.com/anthropics/skills/tree/main/skills/pptx)、[`xlsx`](https://github.com/anthropics/skills/tree/main/skills/xlsx) 和 [`pdf`](https://github.com/anthropics/skills/tree/main/skills/pdf)。

**Leaderboard**: 详情见 [FORTE Leaderboard](https://AGI-Eval-Official.github.io/FORTE/)（基于完整 180 条数据集的评测结果）。

## 概览

| 维度 | FORTE |
|---|---|
| 任务数据            | 单 `.md` + YAML frontmatter；正文段固定为 `## Prompt` / `## Grading Criteria` |
| 模态 | 文本 + xlsx + docx + pptx + pdf + csv + 图片 |
| 职能序列 | Marketing, Sales, BA, Operations, Dev, SRE, HR, Finance, PM, Legal, Algorithm, QA, UI/UX, Administration, General |
| 打分方法 | LLM-as-judge，all-or-nothing （每一条 rubric 都通过才算 `score = 1`） |
| 指标 | Avg@3, Pass@3, Pass^3 |
| Agent 运行环境 | 单个 Docker 镜像里的 [OpenClaw](https://github.com/openclaw/openclaw) |
| 运行依赖 | Python 3.10+ 标准库 + `docker` CLI |

## 数据集布局

```
data/
├── tasks/
│   └── <task_id>.md           # 单 .md：frontmatter + ## Prompt + ## Grading Criteria
└── assets/
    └── <task_id>/
        ├── input/             # agent 启动时看到的工作区
        ├── solution/          # judge 用的参考答案，agent 看不到
        └── skills/            # 可选；会被放进 agent HOME 的 ~/.openclaw/skills
```

`<task_id>.md` 中的内容格式：

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
    content: <rubric 描述；可以含 <file>…</file> 标签>
    weight: 1
---
## Prompt
<给 agent 的指令>

## Grading Criteria
- [ ] <rubric 01 的可读摘要>
```

`rubric_file_paths` 和 `<file>...</file>` 标签使用容器内的两个虚拟根：

- `/workspace/input/...`：agent 的工作目录
- `/workspace/solution/...`：参考答案，仅 judge 阶段读取

## 快速开始

依赖：

- Docker
- Python 3.10+（仅标准库）

1. 配置 agent 和 judge 共用的 OpenAI 兼容网关：

```bash
cp openclaw_config/openclaw.json.example openclaw_config/openclaw.json
cp openclaw_config/.env.example          openclaw_config/.env
```

然后编辑这两份文件，填入网关 URL 和 API key。密钥应只放在这些本地配置文件里。

2. （可选但推荐）安装 Anthropic 通用办公 skills（`docx` / `pptx` / `xlsx` / `pdf`）。
runner 启动每个 agent 容器时，会自动把 `data/extra_skills/` 下的所有 skill
连同任务自带的职能 skill 一起放入容器的 `~/.openclaw/skills/`，给 agent
更强的 Office 文档处理能力。

```bash
bash scripts/install-anthropic-skills.sh
# 也可以只装一部分，或者钉一个上游 tag：
#   SKILLS="docx xlsx" bash scripts/install-anthropic-skills.sh
#   ANTHROPIC_SKILLS_REF=v1.2.3 bash scripts/install-anthropic-skills.sh
```

下载到 `data/extra_skills/`。需要更新时重新跑一次脚本即可。

3. 构建 agent 镜像。

macOS 用户可以使用 Docker Desktop 或 Colima。如果使用 Docker Desktop，请先启动
Docker Desktop；如果使用 Colima，请改用 `colima start`。同时确认当前 Docker
context 指向你启动的那个 daemon。

```bash
# Docker Desktop:
open -a Docker
# 如有需要，从 `docker context ls` 里选择 Docker Desktop 对应的 context，
# 通常是下面两者之一：
# docker context use desktop-linux
# docker context use default

# 如果使用 Colima 而不是 Docker Desktop，改用这一行：
# colima start
# docker context use colima

docker info
bash docker/fetch-lo.sh
docker build -f docker/Dockerfile.agent -t forte-agent:latest docker/
```

Linux 用户需要先启动 Docker 服务。如果当前用户不在 `docker` 用户组里，请给
Docker 命令加上 `sudo`。

```bash
sudo systemctl start docker
docker info
bash docker/fetch-lo.sh
docker build -f docker/Dockerfile.agent -t forte-agent:latest docker/
```

Windows 用户建议使用 Docker Desktop 的 WSL 2 后端，然后在 WSL 终端里执行命令。

```bash
# 先在 Windows 里启动 Docker Desktop，然后在 WSL 终端中执行：
docker info
bash docker/fetch-lo.sh
docker build -f docker/Dockerfile.agent -t forte-agent:latest docker/
```

4. 运行：

```bash
bash scripts/run.sh   # 使用 openclaw.json 里的默认模型跑全部任务

# 或者直接调用 benchmark CLI，并显式指定模型：
python scripts/benchmark.py \
  --model your-gateway/claude-sonnet-4.6 \
  --dataset ./data \
  --runs 3 \
  --concurrency 1 \
  --output-dir ./results

# 可选：只跑一个任务、临时覆盖模型，或提高并发。
TASK_ID=administration-001 bash scripts/run.sh
MODEL=your-gateway/claude-sonnet-4.6 bash scripts/run.sh
RUNS=3 CONCURRENCY=2 bash scripts/run.sh
```

默认值：`MODEL` 从 `openclaw_config/openclaw.json` 的
`agents.defaults.model.primary` 读取（示例配置使用 `claude-sonnet-4.6`），
`RUNS=3`，`CONCURRENCY=1`。提高并发会同时启动更多 Docker 容器，请根据本机资源
和 API 限流情况谨慎调整。

每一次成功的 run 会在 `<output-dir>/<model_slug>/<task_id>[_run_N]/` 下产出：

| 文件 | 说明 |
|---|---|
| `grading.json`        | score（0/1）、每条 rubric 的结果、异常 |
| `openclaw_trace.json` | agent 的原始事件流 |
| `openai_messages.json`| 轨迹的 OpenAI chat-completions 视图 |
| `judge_prompt.json`   | judge 的实际输入（系统提示 + 用户提示 + 图片/PDF 清单） |
| `workspace/`          | agent 跑完后的工作目录快照 |

## 指标

每个任务跑 3 次。每次 run 的打分采用**全对得满分（all-or-nothing）**：只有
`## Grading Criteria` 里每一条 rubric 都通过，该 run 才得 1 分，否则 0 分。
排行榜报告 3 个指标，都是先在每个任务上算出来，然后跨任务做 macro 平均：

| 指标 | 含义 |
|---|---|
| `Avg@3`  | 3 次 run 的平均得分。 |
| `Pass@3` | 3 次 run 中至少有 1 次得分为 1 时记为 1，否则为 0。 |
| `Pass^3` | 3 次 run **全部**得分为 1 时记为 1，否则为 0；衡量一致性。 |

把 `./results/` 下所有模型的结果聚合：

```bash
python scripts/aggregate.py                           # 全部模型 + 全部任务，k=3
python scripts/aggregate.py --model your-gateway/claude-sonnet-4.6
python scripts/aggregate.py --tasks Finance-018,Legal-020
python scripts/aggregate.py --per-task                # 加一份 (模型, 任务) 维度的明细
python scripts/aggregate.py --json                    # 输出机器可读 JSON
```

## 代码结构

```
.
├── data/                       # 任务与素材（随仓库提供）
├── docker/
│   ├── Dockerfile.agent        # OpenClaw + LibreOffice + CJK 字体 + judge 依赖
│   ├── fetch-lo.sh             # 构建前预拉 LibreOffice 离线包
│   ├── agent-requirements.txt
│   └── judge-requirements.txt
├── openclaw_config/
│   ├── openclaw.json.example   # 网关配置模板
│   └── .env.example            # API key / 头部模板
├── scripts/                    # 宿主编排层（仅标准库）
│   ├── benchmark.py            # CLI 入口
│   ├── aggregate.py            # Avg@k / Pass@k / Pass^k 聚合脚本
│   ├── lib_docker.py           # 容器生命周期 + 工作区快照
│   ├── lib_agent.py            # OpenClaw agent 驱动
│   ├── lib_grading.py          # judge 启动器与结果聚合
│   ├── lib_tasks.py            # 任务 `.md` + frontmatter 解析
│   ├── lib_anomalies.py        # 异常检测规则
│   └── run.sh                  # 便捷 benchmark wrapper
├── judge/                      # 容器内 judge（系统提示、文件读取、打分）
├── figs/                       # logo
├── README.md / README_zh.md
└── LICENSE
```

## 致谢

本仓库基于 [QwenClawBench](https://github.com/SKYLENAGE-AI/QwenClawBench) 提供的基本框架进行构建。
我们同时感谢社区提供的其他开源贡献，如 [PinchBench](https://github.com/pinchbench/skill)、[Claw-Eval](https://github.com/claw-eval/claw-eval)、 [ZClawBench](https://huggingface.co/datasets/zai-org/ZClawBench) 以及 [WildClawBench](https://github.com/InternLM/WildClawBench)。

## Citation

如果此仓库对您有帮助，请引用：

```bibtex
@misc{FORTE,
    title        = {{FORTE}: Full-Cycle Office Real-World Task Evaluation for AI Agents Across 15 Corporate Professions},
    author       = {{LongCat Team}},
    howpublished = {\url{https://github.com/AGI-Eval-Official/FORTE}},
    month        = jun,
    year         = {2026}
}
```

## 许可协议

本项目采用 MIT 许可协议——详情请参阅 [LICENSE](./LICENSE) 文件。


## 支持

如有问题或需要支持，请在 GitHub 上提交 issue 或联系维护者。

- 高信 — `gaoxin60@meituan.com`
- 安晟男 — `anshengnan@meituan.com`
- 曹雪智 - `caoxuezhi@meituan.com`
- 刘佳兴 - `liujiaxing10@meituan.com`
- 李啸宇 - `lixiaoyu28@meituan.com`
- 李志峰 - `lizhifeng05@meituan.com`
- 王姿雯 - `wangziwen03@meituan.com`
- 魏玉槐 - `weiyuhuai@meituan.com`
- 张梓键 - `zhangzijian14@meituan.com`
- 朱明阳 - `zhumingyang09@meituan.com`
