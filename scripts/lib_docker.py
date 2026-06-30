"""Docker-based OpenClaw execution for FORTE.

Each (model, task, run) runs in its own agent container; the in-container
judge step then runs in the same container after the agent exits (dual mount:
agent CWD = `/workspace/input`; `solution/` is copied in just before judge
starts).
"""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


DEFAULT_IMAGE = "forte-agent:latest"

# Set on `docker run` so cleanup can find containers regardless of name pattern.
FORTE_CONTAINER_LABEL = "forte=1"
OPENCLAW_HOME = Path(__file__).parent.parent / "openclaw_config"
CONTAINER_OPENCLAW_HOME = "/home/node/.openclaw"
# The agent's working root IS the input tree. The input tree is seeded at
# CONTAINER_INPUT_ROOT and the openclaw agent is given that as its
# --workspace/CWD, so a relative `output/x.md` lands where the rubric expects
# (/workspace/input/output/...). skills/ go to the agent HOME
# (~/.openclaw/skills), NOT into the gradeable workspace. solution/ is NEVER
# copied in (judge-only).
CONTAINER_WORKSPACE = "/workspace"
CONTAINER_INPUT_ROOT = "/workspace/input"
ENV_FILE = OPENCLAW_HOME / ".env"


class DockerContainer:
    """Manages a single Docker container for task execution.

    Each container's ~/.openclaw is its own native (container-local) dir; only
    the openclaw config file(s) are mounted in read-only, so concurrent
    containers never stomp on each other's agent store or session files.
    """

    def __init__(
        self,
        container_name: str,
        image: str = DEFAULT_IMAGE,
        env_file: Optional[Path] = None,
        openclaw_home: Optional[Path] = None,
    ):
        self.container_name = container_name
        self.image = image
        self.env_file = env_file or ENV_FILE
        self.openclaw_home = openclaw_home or OPENCLAW_HOME
        self._running = False
        self._config_files: List[Path] = []

    def start(self) -> None:
        """Start the Docker container in detached mode.

        The container's ~/.openclaw is its *native* (container-local) dir, owned
        by node (uid 1000). After the container is up we `docker cp` the openclaw
        config file(s) into it and chown them to node, so openclaw owns both the
        home and the config and can freely create state/, agents/, sessions/ and
        atomically rewrite openclaw.json.

        Why not bind-mount: on macOS Docker Desktop the host user is uid 501 and
        cannot chown to the container's uid 1000; a *directory* bind-mount of
        ~/.openclaw surfaces as root-owned through virtiofs, so openclaw can't
        create /home/node/.openclaw/state (EACCES); and a *read-only single-file*
        mount of openclaw.json breaks `openclaw agents add`, which rewrites it via
        atomic rename (EBUSY). Copying the config in after start sidesteps all of
        these.
        """
        # Remove existing container with same name if any
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            capture_output=True,
            check=False,
        )

        # The real config files to inject (skip .env — passed via --env-file;
        # skip *.example templates; skip the agents/ store — created fresh inside
        # the container). Copied in after start (see below), not mounted.
        self._config_files = [
            item
            for item in self.openclaw_home.iterdir()
            if item.is_file()
            and item.name != ".env"
            and not item.name.endswith(".example")
        ]

        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "--label", FORTE_CONTAINER_LABEL,
        ]
        # Optional explicit DNS servers (comma/space separated) for environments
        # where Docker's embedded DNS can't resolve (e.g. a broken Docker Desktop
        # resolver). Unset by default → ships unchanged; both the agent's gateway
        # call and the in-container judge's call_api need name resolution.
        dns_env = os.environ.get("DOCKER_DNS", "").strip()
        if dns_env:
            for server in re.split(r"[,\s]+", dns_env):
                if server:
                    cmd += ["--dns", server]
        if self.env_file.exists():
            cmd += ["--env-file", str(self.env_file)]
        cmd.append(self.image)
        # Keep container alive with a long sleep
        cmd += ["sleep", "infinity"]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to start container {self.container_name}: {result.stderr}"
            )
        self._running = True
        logger.info("Started container: %s", self.container_name)

        # Wait for container to be ready
        self._wait_ready()

        # Copy the openclaw config file(s) into the container's native home and
        # chown to node, so openclaw owns the config and can rewrite it.
        self.exec(["mkdir", "-p", CONTAINER_OPENCLAW_HOME], user="0")
        for cfg in self._config_files:
            self.copy_to(cfg, f"{CONTAINER_OPENCLAW_HOME}/{cfg.name}")
        self.exec(["chown", "-R", "node:node", CONTAINER_OPENCLAW_HOME], user="0")

    def _wait_ready(self, timeout: float = 30.0) -> None:
        """Wait until the container is running and responsive."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", self.container_name],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip() == "true":
                return
            time.sleep(0.5)
        raise RuntimeError(f"Container {self.container_name} did not become ready in {timeout}s")

    def exec(
        self,
        cmd: List[str],
        timeout: Optional[float] = None,
        workdir: Optional[str] = None,
        user: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        """Execute a command inside the container.

        If ``user`` is set (e.g. ``"0"`` for root), runs as that user via ``docker exec -u``.
        Default is the image USER (often ``node``).
        """
        docker_cmd = ["docker", "exec"]
        if user:
            docker_cmd += ["-u", user]
        if workdir:
            docker_cmd += ["-w", workdir]
        docker_cmd.append(self.container_name)
        docker_cmd.extend(cmd)

        try:
            return subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                args=docker_cmd,
                returncode=-1,
                stdout=exc.stdout or "",
                stderr=f"Command timed out after {timeout}s",
            )

    def copy_to(self, local_path: Path, container_path: str) -> None:
        """Copy a file or directory from host into the container."""
        result = subprocess.run(
            ["docker", "cp", str(local_path), f"{self.container_name}:{container_path}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to copy {local_path} to {self.container_name}:{container_path}: "
                f"{result.stderr}"
            )

    def start_gateway(self, ready_timeout: float = 60.0) -> None:
        """Start the openclaw gateway as a persistent background process.

        Why: when `openclaw agent` is left to auto-spawn its own gateway, the
        spawned gateway dies immediately with a 1006 abnormal closure and
        openclaw silently runs its EMBEDDED FALLBACK agent (which ignores the
        configured workspace and writes to a bogus host-shaped path). A
        pre-started, long-lived gateway accepts the agent's ws connection
        cleanly and the real provider model runs. Verified: auto-spawn → 1006
        even on a 5s task; pre-started gateway → `[ws] ⇄ res ✓ agent`, real
        output, correct input-root writes.
        """
        # Launch detached inside the container; logs to a file we can poll.
        self.exec([
            "sh", "-c",
            "nohup openclaw gateway > /tmp/openclaw-gateway.log 2>&1 &",
        ])
        deadline = time.time() + ready_timeout
        while time.time() < deadline:
            log = self.exec(["sh", "-c", "cat /tmp/openclaw-gateway.log 2>/dev/null"])
            text = log.stdout or ""
            if "[gateway] ready" in text:
                return
            if "EADDRINUSE" in text or "address already in use" in text:
                # A gateway is already listening; treat as ready.
                return
            time.sleep(0.5)
        tail = (self.exec(["sh", "-c", "tail -20 /tmp/openclaw-gateway.log 2>/dev/null"]).stdout or "")
        raise RuntimeError(
            f"openclaw gateway did not become ready in {ready_timeout}s. "
            f"Last log:\n{tail}"
        )

    def copy_from(self, container_path: str, local_path: Path) -> None:
        """Copy a file or directory from the container to host."""
        local_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["docker", "cp", f"{self.container_name}:{container_path}", str(local_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            logger.warning(
                "Failed to copy %s:%s to %s: %s",
                self.container_name,
                container_path,
                local_path,
                result.stderr,
            )

    def stop(self) -> None:
        """Stop and remove the container."""
        subprocess.run(
            ["docker", "rm", "-f", self.container_name],
            capture_output=True,
            check=False,
        )
        self._running = False
        logger.info("Stopped container: %s", self.container_name)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def _container_dest_for(dest_rel: str) -> str:
    """Route a workspace_files `dest` to its real in-container path.

    - `skills/...`  -> ~/.openclaw/skills/...  (agent HOME); NOT part of the
      gradeable workspace.
    - everything else (input/...) -> under /workspace, so `input/PRD.md` lands at
      CONTAINER_INPUT_ROOT/PRD.md and the agent's CWD (=input root) sees it flat.
    """
    if dest_rel == "skills" or dest_rel.startswith("skills/"):
        rel = dest_rel[len("skills"):].lstrip("/")
        return f"{CONTAINER_OPENCLAW_HOME}/skills/{rel}".rstrip("/")
    return f"{CONTAINER_WORKSPACE}/{dest_rel}"


def prepare_docker_workspace(
    skill_dir: Path,
    task,
    container: DockerContainer,
    asset_dirs: Optional[List[Path]] = None,
) -> str:
    """Seed the agent's working tree inside the container. Returns the agent CWD.

    The input tree IS the agent's working root (CONTAINER_INPUT_ROOT), so a
    rubric path like /workspace/input/output/x.md corresponds to the agent's
    relative `output/x.md`. skills/ go to the agent HOME (~/.openclaw/skills),
    not the gradeable workspace. solution/ is judge-only and never copied in.
    """
    # Create the workspace + input root inside container (root-owned at the FS
    # root; chowned back to node at the end). The empty input root must exist so
    # the agent's relative writes (e.g. output/) resolve under it.
    container.exec(["mkdir", "-p", CONTAINER_INPUT_ROOT], user="0")
    container.exec(["mkdir", "-p", f"{CONTAINER_OPENCLAW_HOME}/skills"], user="0")

    # Asset search directories (in priority order)
    if asset_dirs:
        asset_search_dirs = list(asset_dirs)
    else:
        asset_search_dirs = [
            skill_dir / "assets",
            skill_dir / "generated_assets",
        ]

    for file_spec in task.workspace_files:
        if "content" in file_spec:
            # Write inline content to a temp file, then copy in
            with tempfile.NamedTemporaryFile(mode="w", suffix=".tmp", delete=False) as tmp:
                tmp.write(file_spec["content"])
                tmp_path = Path(tmp.name)
            dest = _container_dest_for(file_spec["path"])
            # Ensure parent dir exists inside container
            parent = "/".join(dest.split("/")[:-1])
            container.exec(["mkdir", "-p", parent], user="0")
            container.copy_to(tmp_path, dest)
            tmp_path.unlink()
            continue

        source_rel = file_spec["source"]
        dest = _container_dest_for(file_spec["dest"])
        parent = "/".join(dest.split("/")[:-1])
        container.exec(["mkdir", "-p", parent], user="0")

        source_found = None
        for asset_dir in asset_search_dirs:
            # Task-specific subfolder takes priority over global path
            for candidate in [
                asset_dir / task.task_id / source_rel,
                asset_dir / source_rel,
            ]:
                if candidate.exists():
                    source_found = candidate
                    break
            if source_found:
                break

        if source_found is None:
            searched = [
                path
                for d in asset_search_dirs
                for path in [str(d / task.task_id / source_rel), str(d / source_rel)]
            ]
            raise FileNotFoundError(
                f"Asset file '{source_rel}' not found in any of: {searched}"
            )

        container.copy_to(source_found, dest)

    # Recreate any empty input subdirs (e.g. output/) — collect_files() skips
    # empty dirs, so seed them here.
    for asset_dir in asset_search_dirs:
        input_tree = asset_dir / task.task_id / "input"
        if input_tree.is_dir():
            for sub in input_tree.rglob("*"):
                if sub.is_dir() and not any(sub.iterdir()):
                    rel = sub.relative_to(input_tree).as_posix()
                    container.exec(["mkdir", "-p", f"{CONTAINER_INPUT_ROOT}/{rel}"], user="0")
            break

    # Stage general-purpose skills (e.g. Anthropic's docx/pptx/xlsx/pdf) into
    # the same ~/.openclaw/skills/ tree as the task-specific skills. Populated
    # by scripts/install-anthropic-skills.sh; absent by default so the repo
    # ships nothing third-party.
    extra_skills_root = Path(__file__).parent.parent / "data" / "extra_skills"
    if extra_skills_root.is_dir():
        for skill_dir_entry in sorted(extra_skills_root.iterdir()):
            if not skill_dir_entry.is_dir() or skill_dir_entry.name.startswith("."):
                continue
            dest = f"{CONTAINER_OPENCLAW_HOME}/skills/{skill_dir_entry.name}"
            container.copy_to(skill_dir_entry, dest)

    for root in (CONTAINER_WORKSPACE, f"{CONTAINER_OPENCLAW_HOME}/skills"):
        chown_result = container.exec(["chown", "-R", "1000:1000", root], user="0")
        if chown_result.returncode != 0:
            logger.warning(
                "chown 1000:1000 on %s failed: %s",
                root, chown_result.stderr or chown_result.stdout,
            )

    return CONTAINER_INPUT_ROOT

MAX_PROMPT_ERROR_RETRIES = 5


def _transcript_ends_on_prompt_error(transcript: List[Dict[str, Any]]) -> bool:
    """True if the agent loop ended on a terminal `openclaw:prompt-error`.

    openclaw records a `custom` entry with customType `openclaw:prompt-error` and
    data.error like "request timed out" when the gateway drops an in-flight LLM
    request, then ends the loop — usually BEFORE the agent writes its output. If
    no assistant message with content follows the last such entry, the run is a
    silent failure (exit 0, status success, but no work done) and must be retried.
    Distinguishes recovered (followed by an assistant message with content) from
    terminal (the last entry, with no assistant content after it).
    """
    if not transcript:
        return False
    last_pe = -1
    for i, entry in enumerate(transcript):
        if entry.get("customType") == "openclaw:prompt-error":
            last_pe = i
    if last_pe < 0:
        return False
    for entry in transcript[last_pe + 1:]:
        if (
            entry.get("type") == "message"
            and entry.get("message", {}).get("role") == "assistant"
            and entry.get("message", {}).get("content")
        ):
            return False  # recovered: real assistant content after the error
    return True


def execute_task_in_docker(
    *,
    task,
    model_id: str,
    run_id: str,
    skill_dir: Path,
    timeout_multiplier: float = 1.0,
    image: str = DEFAULT_IMAGE,
    verbose: bool = False,
    asset_dirs: Optional[List[Path]] = None,
    thinking_level: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a single task inside a dedicated Docker container.

    Creates a container, sets up the agent, copies workspace files,
    runs the prompt, collects transcript and workspace artifacts, then tears down.

    Args:
        asset_dirs: Optional list of directories to search for asset files.
                    If None, defaults to skill_dir/assets and skill_dir/generated_assets.
    """
    from lib_agent import normalize_model_id, slugify_model

    model_slug = slugify_model(model_id)
    container_name = f"{model_slug}-{run_id}-{task.task_id}"
    agent_id = f"bench-{model_slug}"
    session_id = f"{task.task_id}_{int(time.time() * 1000)}"
    timeout_seconds = task.timeout_seconds * timeout_multiplier

    logger.info("🐳 [%s] Starting Docker container for task: %s", container_name, task.task_id)

    container = DockerContainer(container_name=container_name, image=image)
    start_time = time.time()
    stdout = ""
    stderr = ""
    exit_code = -1
    timed_out = False
    transcript: List[Dict[str, Any]] = []
    workspace_snapshot_dir: Optional[Path] = None
    judge_outcome: Optional[Dict[str, Any]] = None
    prompt_error_retries = 0

    try:
        container.start()

        # Prepare workspace files inside container
        prepare_docker_workspace(skill_dir, task, container, asset_dirs=asset_dirs)

        # Create the openclaw agent inside the container (delete first in case
        # copied openclaw.json already lists this agent id)
        normalized_model = normalize_model_id(model_id)
        container.exec(["openclaw", "agents", "delete", agent_id, "--force"])
        add_result = container.exec([
            "openclaw", "agents", "add", agent_id,
            "--model", normalized_model,
            "--workspace", CONTAINER_INPUT_ROOT,
            "--non-interactive",
        ])
        if add_result.returncode != 0:
            msg = (
                f"openclaw agents add failed (exit {add_result.returncode}). "
                f"stdout: {add_result.stdout!r} stderr: {add_result.stderr!r}"
            )
            logger.error("🐳 [%s] %s", container_name, msg)
            raise RuntimeError(msg)

        # Clean up any prior sessions for this agent inside the container.
        # Use lowercase since openclaw normalizes agent IDs to lowercase internally.
        agent_id_lower = agent_id.lower()
        container.exec([
            "sh", "-c",
            f"rm -rf {CONTAINER_OPENCLAW_HOME}/agents/{agent_id_lower}/sessions/*.jsonl "
            f"{CONTAINER_OPENCLAW_HOME}/agents/{agent_id_lower}/sessions/*.jsonl.lock "
            f"{CONTAINER_OPENCLAW_HOME}/agents/{agent_id_lower}/sessions/sessions.json",
        ])

        if verbose:
            logger.info("   [VERBOSE] Container: %s", container_name)
            logger.info("   [VERBOSE] Agent: %s, Model: %s", agent_id, normalized_model)
            logger.info("   [VERBOSE] Timeout: %.0fs", timeout_seconds)

        # Pre-start the gateway so `openclaw agent` connects to a live, long-lived
        # gateway instead of auto-spawning one that dies with a 1006 closure and
        # falls back to the embedded agent (which bypasses the real model).
        container.start_gateway()

        # Execute the task. Retry on a terminal `openclaw:prompt-error`
        # ("request timed out"): the gateway drops the in-flight request and
        # openclaw ends the loop before any work is written, producing a silent
        # exit-0 zero. Each retry runs a FRESH session so the agent starts clean.
        prompt_error_retries = 0
        for attempt in range(1, MAX_PROMPT_ERROR_RETRIES + 1):
            if attempt > 1:
                session_id = f"{task.task_id}_{int(time.time() * 1000)}"
                # Clean any prior session state so the retry starts fresh.
                container.exec([
                    "sh", "-c",
                    f"rm -rf {CONTAINER_OPENCLAW_HOME}/agents/{agent_id_lower}/sessions/*.jsonl "
                    f"{CONTAINER_OPENCLAW_HOME}/agents/{agent_id_lower}/sessions/*.jsonl.lock "
                    f"{CONTAINER_OPENCLAW_HOME}/agents/{agent_id_lower}/sessions/sessions.json",
                ])
                logger.warning(
                    "🐳 [%s] gateway prompt-error on %s; retry %d/%d (fresh session %s)",
                    container_name, task.task_id, attempt, MAX_PROMPT_ERROR_RETRIES, session_id,
                )
            agent_cmd = [
                "openclaw", "agent",
                "--agent", agent_id,
                "--session-id", session_id,
                "--message", task.prompt,
            ]
            if thinking_level:
                agent_cmd.extend(["--thinking", thinking_level])
            result = container.exec(
                agent_cmd,
                timeout=timeout_seconds,
                workdir=CONTAINER_INPUT_ROOT,
            )
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
            timed_out = "timed out" in stderr

            # Collect transcript from container for this attempt
            transcript = _collect_transcript_from_container(container, agent_id, session_id, start_time)

            # A real timeout (agent killed at the wall-clock cap) is NOT a gateway
            # drop — don't retry it. Only retry the transient prompt-error case.
            if timed_out or not _transcript_ends_on_prompt_error(transcript):
                break
            prompt_error_retries = attempt

        if not timed_out and getattr(task, "min_wait_seconds", 0) > 0:
            logger.info(
                "🐳 [%s] agent exited; sleeping %ds for async side effects before snapshot",
                container_name, task.min_wait_seconds,
            )
            time.sleep(task.min_wait_seconds)

        # Snapshot the agent's working tree (= the input root) to a local temp
        # dir for grading. The snapshot ROOT thus equals the rubric's
        # /workspace/input virtual root (see lib_grading path_map).
        workspace_snapshot_dir = Path(f"/tmp/forte/{run_id}/{task.task_id}")
        if workspace_snapshot_dir.exists():
            shutil.rmtree(workspace_snapshot_dir)
        workspace_snapshot_dir.mkdir(parents=True, exist_ok=True)
        container.copy_from(CONTAINER_INPUT_ROOT + "/.", workspace_snapshot_dir)

        # Run the LLM judge INSIDE this same container (it has LibreOffice)
        # before teardown, so the host stays a thin orchestrator and never needs
        # the judge's Python deps or soffice. solution/ is copied in only now,
        # after the agent has finished — the agent never sees it.
        if task.grading_type in ("llm_judge", "hybrid"):
            try:
                from lib_grading import run_incontainer_judge  # deferred: avoid import cycle
                judge_outcome = run_incontainer_judge(container, task, transcript, verbose=verbose)
            except Exception as exc:
                logger.error("🐳 [%s] in-container judge failed for %s: %s",
                             container_name, task.task_id, exc)
                judge_outcome = {"error": f"in-container judge raised: {type(exc).__name__}: {exc}"}

        if verbose:
            logger.info("   [VERBOSE] Exit code: %s", exit_code)
            logger.info("   [VERBOSE] Execution time: %.2fs", time.time() - start_time)
            if stdout:
                logger.info("   [VERBOSE] Stdout (first 1000 chars):\n%s", stdout[:1000])
            if stderr:
                logger.info("   [VERBOSE] Stderr:\n%s", stderr[:1000])
            logger.info("   [VERBOSE] Transcript entries: %d", len(transcript))

    except Exception as exc:
        logger.error("🐳 [%s] Container execution failed: %s", container_name, exc)
        stderr += f"\nDocker execution error: {exc}"
    finally:
        container.stop()

    execution_time = time.time() - start_time
    usage = _extract_usage(transcript)

    # A gateway prompt-error that survived all retries: the final transcript still
    # ends on a terminal `openclaw:prompt-error`. Surface it so the anomaly layer
    # flags the run (GATEWAY_PROMPT_ERROR) instead of letting it be a silent zero.
    gateway_prompt_error = (not timed_out) and _transcript_ends_on_prompt_error(transcript)

    status = "success"
    if timed_out:
        status = "timeout"
    if not transcript:
        status = "error"
    if exit_code not in (0, -1) and not timed_out:
        status = "error"

    return {
        "agent_id": agent_id,
        "task_id": task.task_id,
        "status": status,
        "transcript": transcript,
        "usage": usage,
        "workspace": str(workspace_snapshot_dir) if workspace_snapshot_dir else "",
        "judge_outcome": judge_outcome,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "prompt_error_retries": prompt_error_retries,
        "gateway_prompt_error": gateway_prompt_error,
        "execution_time": execution_time,
        "stdout": stdout,
        "stderr": stderr,
    }


def _collect_transcript_from_container(
    container: DockerContainer,
    agent_id: str,
    session_id: str,
    started_at: float,
) -> List[Dict[str, Any]]:
    """Collect transcript JSONL from inside the container."""
    # openclaw normalizes agent IDs to lowercase internally
    agent_sessions = f"{CONTAINER_OPENCLAW_HOME}/agents/{agent_id.lower()}/sessions"

    # Try sessions.json first to find the real session ID
    result = container.exec(["cat", f"{agent_sessions}/sessions.json"])
    resolved_path = None

    if result.returncode == 0 and result.stdout.strip():
        try:
            sessions_payload = json.loads(result.stdout)
            if isinstance(sessions_payload, dict):
                # Find the most recent session
                newest_sid = None
                newest_ts = -1
                for entry in sessions_payload.values():
                    if not isinstance(entry, dict) or "sessionId" not in entry:
                        continue
                    updated_at = entry.get("updatedAt", 0)
                    if isinstance(updated_at, (int, float)) and updated_at > newest_ts:
                        newest_ts = updated_at
                        newest_sid = entry["sessionId"]
                if newest_sid:
                    resolved_path = f"{agent_sessions}/{newest_sid}.jsonl"
        except json.JSONDecodeError:
            pass

    # Fallback: list .jsonl files and pick the newest
    if not resolved_path:
        ls_result = container.exec(["sh", "-c", f"ls -t {agent_sessions}/*.jsonl 2>/dev/null"])
        if ls_result.returncode == 0 and ls_result.stdout.strip():
            resolved_path = ls_result.stdout.strip().split("\n")[0]

    # Last resort: try our session ID
    if not resolved_path:
        resolved_path = f"{agent_sessions}/{session_id}.jsonl"

    # Read the transcript
    cat_result = container.exec(["cat", resolved_path])
    if cat_result.returncode != 0:
        logger.warning(
            "Could not read transcript from container %s at %s: %s",
            container.container_name,
            resolved_path,
            cat_result.stderr,
        )
        return []

    transcript: List[Dict[str, Any]] = []
    for line in cat_result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            transcript.append(json.loads(line))
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse transcript line: %s", exc)
            transcript.append({"parse_error": str(exc), "skipped": True})

    logger.info(
        "🐳 Collected %d transcript entries from container %s",
        len(transcript),
        container.container_name,
    )
    return transcript


def _extract_usage(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sum token usage and cost from transcript (same logic as lib_agent)."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "request_count": 0,
    }
    for entry in transcript:
        if entry.get("type") != "message":
            continue
        msg = entry.get("message", {})
        if msg.get("role") != "assistant":
            continue
        totals["request_count"] += 1
        usage = msg.get("usage", {})
        totals["input_tokens"] += usage.get("input", 0)
        totals["output_tokens"] += usage.get("output", 0)
        totals["cache_read_tokens"] += usage.get("cacheRead", 0)
        totals["cache_write_tokens"] += usage.get("cacheWrite", 0)
        totals["total_tokens"] += usage.get("totalTokens", 0)
        cost = usage.get("cost", {})
        totals["cost_usd"] += cost.get("total", 0.0)
    return totals

def cleanup_containers(prefix: str = "forte-") -> int:
    """Kill and remove all FORTE Docker containers (matched by label).

    Containers are labeled at creation with ``forte=1`` (see FORTE_CONTAINER_LABEL).
    The ``prefix`` argument is deprecated and ignored; kept for backward compatibility.

    Also cleans up the per-container openclaw home copies under
    /tmp/forte/docker_homes/.

    Returns the number of containers removed.
    """
    _ = prefix  # deprecated, unused
    # List matching containers (running or stopped)
    result = subprocess.run(
        [
            "docker", "ps", "-a",
            "--filter", f"label={FORTE_CONTAINER_LABEL}",
            "--format", "{{.Names}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.warning("Failed to list containers: %s", result.stderr)
        return 0

    names = [n.strip() for n in result.stdout.splitlines() if n.strip()]
    if not names:
        logger.info("No forte containers to clean up")
        return 0

    for name in names:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=False)

    logger.info("Removed %d container(s): %s", len(names), ", ".join(names))

    # Clean up host-side openclaw home copies
    docker_homes = Path("/tmp/forte/docker_homes")
    if docker_homes.exists():
        shutil.rmtree(docker_homes, ignore_errors=True)
        logger.info("Cleaned up %s", docker_homes)

    return len(names)
