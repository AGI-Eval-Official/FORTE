---
name: paper-code-understanding
description: Analyze an algorithm paper (PDF) together with its implementation repository to answer technical questions with code-grounded evidence. Use when the user provides a PDF paper plus source code and asks about algorithm ideas, module purpose, equation-to-code mapping, training/inference flow, complexity, or implementation details.
---

# Paper Code Understanding

## Overview
Act as a senior algorithm researcher + engineer. Extract the core method from the paper, map it to concrete code paths, and answer the user’s algorithm question with traceable evidence.

## Required inputs
Collect these before deep analysis:
- Paper PDF path or URL
- Repository path (or key subdirectories)
- User question (specific algorithm concern)
- Optional: commit/tag/branch, framework version, runtime config

If one required input is missing, request it once, clearly.

## Workflow

### 1) Frame the question
Restate the question as a verification target:
- What claim must be proven from paper + code?
- What kind of evidence is needed (equation, pseudocode, function path, config, experiment section)?

### 2) Read the paper efficiently
Extract these artifacts first:
- Problem definition and assumptions
- Core algorithm (key equations, pseudocode, architecture blocks)
- Training objective and loss terms
- Inference/update rules
- Complexity claims and ablation insights

Focus on method sections before appendix. Keep a short list of symbols and their meanings.

### 3) Build a paper-to-code map
Create a mapping table (mentally or explicitly):
- Concept/layer/loss term in paper
- Expected code location (module, class, function)
- Actual file path and symbol in repo
- Confidence (high/medium/low)

Start from likely entry points:
- Training/inference scripts
- Model definition directories (`models/`, `networks/`, `src/`)
- Loss/criterion modules
- Config files and experiment YAML/JSON

### 4) Verify implementation fidelity
Check whether code truly matches paper:
- Exact match: same math/logic
- Approximate match: equivalent but reparameterized/refactored
- Divergence: missing term, changed schedule, extra heuristic, silent default

Treat defaults and config overrides as first-class evidence.

### 5) Answer with traceable evidence
Provide:
1. Direct answer to the user’s question
2. Paper evidence (section/equation/figure references)
3. Code evidence (file path + function/class)
4. Any mismatch and impact
5. Practical guidance for reuse/modification

If evidence is incomplete, state uncertainty explicitly and list the minimum extra files needed.

## Output format
Use this structure when possible:

- **结论（先给答案）**
- **论文依据**: section/equation/figure
- **代码定位**: `path/to/file.py::Symbol`
- **一致性检查**: match / approximate / divergence
- **实现建议**: how to adapt or reuse
- **风险与假设**: version/config/data-dependent caveats

## Quality bar
- Do not claim “implemented” without concrete symbol-level code evidence.
- Prefer precise paths over vague directory names.
- Separate facts from inference.
- When multiple implementations exist (e.g., baseline vs optimized), identify which one answers the question.

## Use references
If needed, load `references/analysis-checklist.md` for a deeper checklist covering equation tracing, gradient/loss validation, and common mismatch patterns.
