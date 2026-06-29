"""grade_one — end-to-end judge pipeline for a single (task, run).

Rubric paths use the two virtual roots /workspace/input/... and
/workspace/solution/..., which are mapped to real host directories (the
post-run workspace snapshot and the host-side assets/<task>/solution dir) for
actual byte reads.

Flow:
  extract_model_response (done by caller; passed in as model_response)
  check_missing_files -> any missing => score 0, SKIP judge
  extract_files (xlsx style preserved, etc.)
  local image/pdf paths -> base64 data URIs for the OpenAI-compatible channel
  build_prompt
  call_api (retry + thinking-interruption)
  parse_grading_response
  all_pass -> score = 1 if all_pass else 0
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from .check import check_missing_files
from .file_readers import extract_files
from .build_prompt import build_prompt
from .call_api import call_api, path_to_data_uri
from .parse_grading import parse_grading_response


@dataclass
class GradeOutcome:
    score: int
    all_pass: bool
    result_json: Optional[dict]
    skipped_judge: bool = False
    missing_files: list = field(default_factory=list)
    # rendered judge inputs (for judge_prompt.json)
    system_prompt: str = ""
    user_prompt: str = ""
    image_count: int = 0
    pdf_count: int = 0
    # raw judge response (incl <think>), for diff analysis
    judge_raw_response: str = ""
    thinking: str = ""
    analysis: str = ""
    error: str = ""


def _translate(path: str, path_map: dict) -> str:
    """Map a virtual path (/workspace/input/...) to a real host path.

    Longest-prefix match against path_map keys. Returns the original path
    unchanged if no prefix matches (caller's check_missing_files will then flag
    it).
    """
    best = None
    for prefix in path_map:
        if path == prefix or path.startswith(prefix.rstrip("/") + "/"):
            if best is None or len(prefix) > len(best):
                best = prefix
    if best is None:
        return path
    real_root = path_map[best]
    rel = path[len(best):].lstrip("/")
    # preserve a trailing "*" (directory marker for check_missing_files / extract_files)
    return os.path.join(real_root, rel)


def grade_one(instruction, model_response, file_paths, rubrics_list, path_map,
              *, use_code_exec=False, model_name=None):
    """Grade a single run. Returns GradeOutcome.

    Args:
        instruction: task instruction text (## Prompt).
        model_response: the agent's final text response (already extracted).
        file_paths: rubric ```path block, virtual paths (/workspace/{input,solution}/...).
        rubrics_list: list of {id, content, ...}.
        path_map: {virtual_root: real_host_dir}, e.g.
            {"/workspace/input": <snapshot>, "/workspace/solution": <assets solution>}.
        use_code_exec: select SYSTEM_PROMPT_W_CODE_EXEC.
        model_name: judge model id (else env JUDGE_MODEL).
    """
    # Map virtual -> real, keep the pairing so we can re-key by virtual path.
    real_to_virtual = {}
    real_paths = []
    for vp in file_paths:
        rp = _translate(vp, path_map)
        real_paths.append(rp)
        real_to_virtual[os.path.abspath(rp.rstrip("*"))] = vp

    # Existence pre-check on real paths. Any missing => score 0, no judge.
    missing_real = check_missing_files(real_paths)
    if missing_real:
        missing_virtual = []
        for mp in missing_real:
            key = os.path.abspath(mp.rstrip("*"))
            missing_virtual.append(real_to_virtual.get(key, mp))
        return GradeOutcome(
            score=0, all_pass=False, result_json=None,
            skipped_judge=True, missing_files=missing_virtual,
        )

    # Read files (keyed by real path).
    extracted = extract_files(real_paths)
    if extracted is None:
        return GradeOutcome(
            score=0, all_pass=False, result_json=None,
            skipped_judge=True, missing_files=list(file_paths),
        )
    real_content, real_type = extracted

    # Re-key to virtual paths; convert image/pdf local paths -> base64 data URIs.
    file2content = {}
    file2type = {}
    for real_path, content in real_content.items():
        ftype = real_type.get(real_path, "text")
        vp = real_to_virtual.get(os.path.abspath(real_path))
        if vp is None:
            # extract_files may have expanded a "*" dir; rebuild the virtual path
            vp = _virtual_for_expanded(real_path, path_map)
        if ftype == "text":
            file2content[vp] = content
        else:
            # content is a local file path (image / compressed image / converted pdf)
            default_mime = "application/pdf" if vp.lower().endswith(".pdf") else "image/png"
            file2content[vp] = path_to_data_uri(content, default_mime=default_mime)
        file2type[vp] = ftype

    # Build judge prompt + channel manifests.
    system_prompt, user_prompt, image_urls, pdf_urls = build_prompt(
        instruction, model_response, file2content, file2type, rubrics_list,
        use_code_exec=use_code_exec,
    )

    # Call judge with retry / thinking-interruption handling.
    try:
        full_content, _pt, _ct = call_api(
            system_prompt, user_prompt, image_urls=image_urls, pdf_urls=pdf_urls,
            model_name=model_name, use_code_exec=use_code_exec,
        )
    except Exception as e:
        return GradeOutcome(
            score=0, all_pass=False, result_json=None,
            system_prompt=system_prompt, user_prompt=user_prompt,
            image_count=len(image_urls), pdf_count=len(pdf_urls),
            error=f"judge call failed: {type(e).__name__}: {e}",
        )

    # Parse judge response.
    thinking, analysis, result_json = parse_grading_response(full_content)

    # All-or-nothing.
    all_pass = bool(result_json.get("all_pass", False)) if result_json else False
    score = 1 if all_pass else 0

    return GradeOutcome(
        score=score, all_pass=all_pass, result_json=result_json,
        system_prompt=system_prompt, user_prompt=user_prompt,
        image_count=len(image_urls), pdf_count=len(pdf_urls),
        judge_raw_response=full_content, thinking=thinking, analysis=analysis,
    )


def _virtual_for_expanded(real_path: str, path_map: dict) -> str:
    """Best-effort virtual path for a file discovered by a "*" dir expansion."""
    abs_real = os.path.abspath(real_path)
    best_prefix = None
    best_root = None
    for prefix, root in path_map.items():
        abs_root = os.path.abspath(root)
        if abs_real == abs_root or abs_real.startswith(abs_root + os.sep):
            if best_root is None or len(abs_root) > len(best_root):
                best_root = abs_root
                best_prefix = prefix
    if best_prefix is None:
        return real_path
    rel = abs_real[len(best_root):].lstrip(os.sep).replace(os.sep, "/")
    return best_prefix.rstrip("/") + "/" + rel
