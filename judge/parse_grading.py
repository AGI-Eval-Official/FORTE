"""parse_grading_response — extract thinking / analysis / result_json from judge output.

Strip <think>...</think>, take the LAST ```json fenced block, fall back to the
last bare {...} that looks like a result, parse with json_repair.
"""

import re


def parse_grading_response(response):
    """Parse the grading model's response into (thinking, analysis, result_json).

    Expected response shape:
        <think>...</think> analysis text ... ```json { ... } ```

    Returns:
        (thinking, analysis, result_json)
        result_json is None on parse failure.
    """
    # 1. 提取 thinking 部分
    thinking = ""
    remaining = response
    think_match = re.search(r"<think>(.*?)</think>", response, re.DOTALL)
    if think_match:
        thinking = think_match.group(1).strip()
        remaining = response[think_match.end():]

    # 2. 从 remaining 中提取最后一个 ```json ... ``` 代码块
    json_blocks = re.findall(
        r"```json\s*(.*?)(?:^|\n)[ \t]*```",
        remaining,
        re.DOTALL,
    )

    result_json = None
    if json_blocks:
        raw_json = json_blocks[-1].strip()
        try:
            import json_repair
            result_json = json_repair.loads(raw_json)
        except Exception:
            print(f"警告: JSON 解析失败，原始内容: {raw_json[:200]}...")

    # 2.1 如果没有匹配到 ```json 代码块，尝试匹配裸 JSON 对象
    if result_json is None:
        brace_matches = list(re.finditer(r"\{", remaining))
        if brace_matches:
            for m in reversed(brace_matches):
                candidate = remaining[m.start():]
                try:
                    import json_repair
                    parsed = json_repair.loads(candidate)
                    if isinstance(parsed, dict) and ("results" in parsed or "all_pass" in parsed):
                        result_json = parsed
                        break
                except Exception:
                    continue

    # 3. 分析文本 = remaining 去掉最后一个 json 代码块后的内容
    analysis = remaining
    if json_blocks:
        last_json_start = remaining.rfind("```json")
        if last_json_start != -1:
            analysis = remaining[:last_json_start].strip()

    return thinking, analysis, result_json
