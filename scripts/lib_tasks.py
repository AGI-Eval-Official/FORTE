"""Task loader for FORTE.

Parses each task `.md` file: YAML-like frontmatter (between `---` fences)
followed by markdown sections `## Prompt`, `## Grading Criteria`, ... The
frontmatter parser here is a deliberately narrow stdlib-only subset — it
covers the exact shapes our task .md files use (top-level scalars and lists,
block lists of inline mappings for `workspace_files` / `solution_files` /
`rubrics`, list-of-strings for `rubric_file_paths`). It is NOT a general YAML
implementation; full PyYAML behavior is not a goal (D3: host has zero Python
dependencies).
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any


logger = logging.getLogger(__name__)


def _unquote(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _parse_scalar(s: str) -> Any:
    s = s.strip()
    if not s:
        return ""
    if s[0] in ("'", '"') and len(s) >= 2 and s[-1] == s[0]:
        return s[1:-1]
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if s in ("null", "~", ""):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _frontmatter_loads(text: str) -> Dict[str, Any]:
    """Parse the YAML-like frontmatter we actually use.

    Supported shapes:
        key: scalar
        key:
        - scalar
        - scalar
        key:
        - inline_key: value
          inline_key2: value
        - inline_key: value
          ...

    Inline-mapping values are taken verbatim from after the first ':' on the
    line; quotes are stripped if they wrap the whole value. This is enough for
    rubric `content:` fields that contain `<file>...</file>`, full-width
    punctuation, backticks, and embedded `:` characters.
    """
    raw_lines = text.splitlines()
    lines: List[str] = []
    for ln in raw_lines:
        s = ln.rstrip()
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        lines.append(s)

    out: Dict[str, Any] = {}
    i = 0
    n = len(lines)

    while i < n:
        ln = lines[i]
        if not ln or ln[0] in (" ", "-"):
            i += 1
            continue
        key, _, rest = ln.partition(":")
        key = key.strip()
        rest = rest.strip()
        i += 1
        if rest:
            if rest == "[]":
                out[key] = []
            elif rest == "{}":
                out[key] = {}
            else:
                out[key] = _parse_scalar(rest)
            continue
        if i >= n:
            out[key] = None
            continue
        peek = lines[i]
        if peek.startswith("- "):
            # block list at column 0 ("- ...")
            items: List[Any] = []
            while i < n:
                ln2 = lines[i]
                if not ln2.startswith("- "):
                    break
                first = ln2[2:]
                if re.match(r"^[A-Za-z_][\w-]*\s*:", first):
                    item: Dict[str, Any] = {}
                    fkey, _, fval = first.partition(":")
                    item[fkey.strip()] = _parse_scalar(fval.strip()) if fval.strip() else None
                    i += 1
                    while i < n and lines[i].startswith("  ") and not lines[i].startswith("- "):
                        cont = lines[i].lstrip()
                        ckey, _, cval = cont.partition(":")
                        item[ckey.strip()] = _parse_scalar(cval.strip())
                        i += 1
                    items.append(item)
                else:
                    items.append(_parse_scalar(first))
                    i += 1
            out[key] = items
        else:
            out[key] = None

    return out


class Task:
    """A single benchmark task: prompt + assets + grading metadata."""

    def __init__(
        self,
        task_id: str,
        name: str,
        category: str,
        grading_type: str,
        timeout_seconds: int,
        workspace_files: List[Dict[str, str]],
        prompt: str,
        expected_behavior: str,
        grading_criteria: List[str],
        automated_checks: Optional[str] = None,
        llm_judge_rubric: Optional[str] = None,
        grading_weights: Optional[Dict[str, float]] = None,
        file_path: Optional[Path] = None,
        frontmatter: Optional[Dict[str, Any]] = None,
    ):
        self.task_id = task_id
        self.name = name
        self.category = category
        self.grading_type = grading_type
        self.timeout_seconds = timeout_seconds
        self.workspace_files = workspace_files
        self.prompt = prompt
        self.expected_behavior = expected_behavior
        self.grading_criteria = grading_criteria
        self.automated_checks = automated_checks
        self.llm_judge_rubric = llm_judge_rubric
        self.grading_weights = grading_weights
        self.file_path = file_path
        self.frontmatter = frontmatter or {}

    def __repr__(self) -> str:
        return f"Task(id={self.task_id}, name={self.name}, category={self.category})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'category': self.category,
            'grading_type': self.grading_type,
            'timeout_seconds': self.timeout_seconds,
            'workspace_files': self.workspace_files,
            'prompt': self.prompt,
            'expected_behavior': self.expected_behavior,
            'grading_criteria': self.grading_criteria,
            'has_automated_checks': self.automated_checks is not None,
            'has_llm_judge_rubric': self.llm_judge_rubric is not None,
            'grading_weights': self.grading_weights,
            'frontmatter': self.frontmatter,
        }


class TaskLoader:
    """Loads `<id>.md` files from a tasks/ directory."""

    def __init__(self, tasks_dir: Path):
        self.tasks_dir = tasks_dir
        logger.info(f"Initialized TaskLoader with directory: {tasks_dir}")

    def load_all_tasks(self) -> List[Task]:
        tasks = []
        task_files = sorted(self.tasks_dir.glob("*.md"))
        logger.info(f"Found {len(task_files)} task files")
        for task_file in task_files:
            try:
                task = self.load_task(task_file)
                tasks.append(task)
                logger.info(f"Successfully loaded task: {task.task_id}")
            except Exception as e:
                logger.error(f"Failed to load task from {task_file}: {e}", exc_info=True)
        logger.info(f"Successfully loaded {len(tasks)} tasks")
        return tasks

    def load_task(self, task_file: Path) -> Task:
        logger.debug(f"Loading task from: {task_file}")
        content = task_file.read_text(encoding='utf-8')

        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        if not frontmatter_match:
            raise ValueError(f"No YAML frontmatter found in {task_file}")

        frontmatter_text = frontmatter_match.group(1)
        body_text = frontmatter_match.group(2)

        # Strip tracing-only fields that may contain content the narrow parser
        # below cannot handle (multi-line XML, embedded colons, etc.). These
        # fields aren't read by host code.
        frontmatter_text = re.sub(
            r'^source_query:\s*.*?(?=\n\w+:\s|\n---|\Z)',
            '', frontmatter_text, flags=re.MULTILINE | re.DOTALL,
        )
        frontmatter_text = re.sub(r'^source_line_number:.*$', '', frontmatter_text, flags=re.MULTILINE)

        try:
            metadata = _frontmatter_loads(frontmatter_text)
        except Exception as e:
            raise ValueError(f"Invalid frontmatter in {task_file}: {e}")

        sections = self._parse_sections(body_text)
        grading_criteria = self._extract_grading_criteria(sections.get('Grading Criteria', ''))

        task = Task(
            task_id=metadata.get('id', ''),
            name=metadata.get('name', ''),
            category=metadata.get('category', ''),
            grading_type=metadata.get('grading_type', 'automated'),
            timeout_seconds=metadata.get('timeout_seconds', 120),
            workspace_files=metadata.get('workspace_files', []),
            prompt=sections.get('Prompt', '').strip(),
            expected_behavior=sections.get('Expected Behavior', '').strip(),
            grading_criteria=grading_criteria,
            automated_checks=sections.get('Automated Checks', None),
            llm_judge_rubric=sections.get('LLM Judge Rubric', None),
            grading_weights=metadata.get('grading_weights', None),
            file_path=task_file,
            frontmatter=metadata,
        )
        return task

    def _parse_sections(self, body: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        current_section: Optional[str] = None
        current_content: List[str] = []
        for line in body.split('\n'):
            header_match = re.match(r'^##\s+(.+)$', line)
            if header_match:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = header_match.group(1)
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        return sections

    def _extract_grading_criteria(self, criteria_text: str) -> List[str]:
        criteria = []
        for line in criteria_text.split('\n'):
            match = re.match(r'^-\s+\[[ x]\]\s+(.+)$', line.strip())
            if match:
                criteria.append(match.group(1))
        return criteria
