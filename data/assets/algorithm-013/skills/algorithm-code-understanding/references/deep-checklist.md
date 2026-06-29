# Deep Checklist

Use this checklist when the user asks for a deep algorithm explanation rather than a shallow code summary.

## A. Frame the exact question
Classify the request:
- Where is the algorithm implemented?
- How does the algorithm actually run step by step?
- Why is this branch, mask, cache, or heuristic needed?
- How does training differ from inference?
- Which code corresponds to a paper/module/concept?

## B. Build the runtime path
Find the real path, not just a relevant file:
- Entry script / command
- Config parse and override chain
- Registry/factory/build step
- Concrete class instantiation
- Forward/update/decode/search function
- Final aggregation/post-processing

## C. Trace algorithm state
For each important variable/tensor/state object, track:
- Where it is created
- Where it is transformed
- Which branch modifies it
- Where it affects the final result

Useful targets:
- hidden states
- attention scores or masks
- logits/probabilities
- beam state / cache / memory bank
- loss terms and coefficients
- candidate sets / thresholds / top-k top-p filters

## D. Watch common traps
- Definition exists but is never called in the active path
- Multiple implementations exist; config selects only one
- Helper function hides the real algorithmic step
- Training path and inference path diverge silently
- A heuristic/stability trick materially changes the algorithm
- Defaults in config disable a seemingly important module
- The user-provided file is downstream of the real implementation

## E. Explain at the right level
Match the answer depth to the user's question:
- Quick location question -> emphasize file path and call chain
- “How does it work?” -> explain step-by-step data flow
- “Why this design?” -> compare with alternatives and infer likely tradeoffs from code
- “Is this equivalent to X?” -> point out exact match vs approximate match vs divergence

## F. Confidence grading
- **High**: direct runtime path plus symbol-level evidence
- **Medium**: likely active path with partial verification
- **Low**: inferred from naming or local pattern only

## G. Answer discipline
- Put the answer first
- Cite concrete code locations for each important claim
- Mark uncertainty explicitly
- Ask only for the smallest missing artifact needed to continue
