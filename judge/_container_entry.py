"""_container_entry — run grade_one INSIDE the agent container.

The judge (grade_one) executes in the same Docker image as the agent, which
carries LibreOffice. The host orchestrator (scripts/
lib_grading.run_incontainer_judge) copies this package + a small inputs JSON into
the live container, runs:

    PYTHONPATH=/opt/lcjudge python3 -m judge._container_entry <inputs.json> <out.json>

and copies <out.json> back.

Inputs JSON keys: instruction, model_response, file_paths, rubrics_list,
path_map, use_code_exec, model_name. The JUDGE_BASE_URL / JUDGE_API_KEY /
JUDGE_MODEL credentials are read from the container env (injected at
`docker run` via --env-file; see lib_docker.DockerContainer.start).
"""

import sys
import json
from dataclasses import asdict

from .grade import grade_one


def main(argv):
    if len(argv) != 3:
        print("usage: python3 -m judge._container_entry <inputs.json> <out.json>",
              file=sys.stderr)
        return 2

    inputs_path, out_path = argv[1], argv[2]
    with open(inputs_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    try:
        outcome = grade_one(
            instruction=payload["instruction"],
            model_response=payload["model_response"],
            file_paths=payload["file_paths"],
            rubrics_list=payload["rubrics_list"],
            path_map=payload["path_map"],
            use_code_exec=payload.get("use_code_exec", False),
            model_name=payload.get("model_name") or None,
        )
        result = asdict(outcome)
    except Exception as e:  # surface to host as an error outcome, never crash silently
        result = {
            "score": 0,
            "all_pass": False,
            "result_json": None,
            "skipped_judge": False,
            "missing_files": [],
            "system_prompt": "",
            "user_prompt": "",
            "image_count": 0,
            "pdf_count": 0,
            "judge_raw_response": "",
            "thinking": "",
            "analysis": "",
            "error": f"in-container grade_one failed: {type(e).__name__}: {e}",
        }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
