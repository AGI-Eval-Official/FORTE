# Analysis Checklist

Use this checklist when the question requires deep verification.

## A. Paper decomposition
- Identify algorithm inputs/outputs and tensor shapes (if available).
- List every objective term and weighting coefficient.
- Record training schedule details (warmup, decay, EMA, clipping, sampling).
- Record inference-time differences from training.

## B. Code tracing strategy
- Locate executable entry (`train.py`, `main.py`, launcher scripts).
- Follow config load chain to final runtime values.
- Track model construction path to concrete class implementations.
- Track where each loss term is computed and aggregated.
- Track where optimizer/scheduler are instantiated and stepped.

## C. Equation-to-code trace
For each key equation in the paper:
1. Symbol meaning
2. Candidate code expression
3. Final file/function/line region
4. Notes on numerical tricks (eps, clamp, detach, stop-grad, mixed precision)

## D. Common mismatch patterns
- Paper omits engineering stabilizers present in code.
- Public repo differs from camera-ready paper version.
- Default config silently disables a paper component.
- Multi-stage training described in paper but single-stage shortcut in released script.
- Evaluation metric implementation differs from paper definition.

## E. Confidence grading
- **High**: direct symbolic match + active in runtime path
- **Medium**: logically equivalent but transformed/refactored
- **Low**: inferred from naming or partial evidence

## F. Answer discipline
- Put final answer first.
- Cite both paper and code evidence for each important claim.
- Mark unknowns explicitly; ask for exact missing files rather than broad requests.
