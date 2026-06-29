---
name: algorithm-code-understanding
description: Understand and answer algorithm questions from code. Use when the user provides a code file, repository, or folder and asks how an algorithm works, where it is implemented, how data flows through it, why a design choice exists, how training/inference differs, or how a specific module/function realizes an algorithmic idea. Especially useful for tracing concrete implementation paths in real code instead of giving generic textbook explanations.
---

# Algorithm Code Understanding

## Overview
Act like a senior algorithm engineer reading unfamiliar production/research code. First understand the user's algorithm question precisely, then find the relevant implementation in the codebase, verify the actual execution path, and answer from code evidence rather than from prior assumptions.

## Required inputs
Collect these before deep analysis:
- Code file path, repository path, or target folder
- User question about algorithm logic
- Optional: branch/commit, config file, runtime entry point, framework version

If the path or the question is missing, ask once and keep the request narrow.

## Workflow

### 1) Turn the question into a verification target
Rewrite the request internally as something testable:
- What algorithmic claim must be explained or verified?
- Is the user asking about architecture, loss, search/sampling, data flow, state update, complexity, or a design tradeoff?
- What evidence would be sufficient: function path, call chain, tensor flow, config gate, or math-to-code mapping?

If the user asks a broad question, narrow it to the smallest code path that can answer it well.

### 2) Start from execution, not from names
Prefer real execution paths over semantic guessing.

Good starting points:
- User-provided file
- Repository entry points such as `train.py`, `main.py`, `infer.py`, `evaluate.py`, CLI launchers
- Model/loss/search directories such as `models/`, `modules/`, `layers/`, `ops/`, `solver/`, `engine/`
- Config files that select implementations

When possible, identify:
- The runtime entry
- The config load chain
- The concrete class/function that is actually instantiated
- The function where the algorithmic decision is made

### 3) Locate the relevant implementation
Search the codebase using the question's algorithmic vocabulary and nearby implementation clues.

Look for:
- Function/class names matching the user concept
- Call sites rather than only definitions
- Config keys or registry entries that activate a module
- Loss aggregation points, decoding/search loops, update rules, masking logic, normalization, sampling, caching

Keep a short candidate list with confidence levels:
- High: active runtime path with direct code evidence
- Medium: likely helper or equivalent implementation
- Low: naming match only

### 4) Trace the algorithm end-to-end
Trace enough of the path to answer the question, usually across these layers:
1. Input/state preparation
2. Core algorithm step
3. Parameter/control branches
4. Output/post-processing

For each important step, capture:
- File path
- Symbol name
- Role in the algorithm
- Key conditions or config flags

When useful, summarize the call chain explicitly, for example:
`train.py -> build_model() -> Decoder.forward() -> beam_search_step()`

### 5) Distinguish mechanism from scaffolding
Separate the true algorithmic logic from engineering support code.

Usually classify code into:
- Core algorithm: the essential update/search/attention/objective logic
- Support logic: shape transforms, device moves, logging, wrappers, registry code
- Optimization/stability tricks: caching, fused ops, clamp/eps, detach, masking, mixed precision, heuristics

If the code differs from a textbook or paper version, say so clearly.

### 6) Answer from code evidence
Use the code to answer the user's exact question. Prefer precise references over broad descriptions.

## Output format
Use this structure when possible:

- **结论（先给答案）**
- **代码定位**: `path/to/file.py::Symbol`
- **实现路径**: short call chain or execution flow
- **算法逻辑拆解**: the actual mechanism in code order
- **关键细节/技巧**: masks, caches, detach, normalization, thresholds, schedules, etc.
- **为什么这么写**: likely engineering or algorithmic reason
- **风险与边界**: config/version/path-dependent caveats

## Quality bar
- Do not answer only from textbook knowledge when code evidence is required.
- Do not stop at the first name match; verify the runtime path.
- Prefer concrete symbols and paths over vague directory references.
- Separate facts, inferences, and uncertainty.
- If multiple implementations exist, identify which one is active and why.
- If evidence is incomplete, say what extra file or entry point is needed.

## Use references
Load `references/deep-checklist.md` when the question needs a deeper investigation of call chains, tensor/state flow, losses, search loops, training-vs-inference differences, or implementation-vs-theory mismatches.
