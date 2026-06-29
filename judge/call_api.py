"""call_api — judge LLM call over an OpenAI-compatible gateway.

Images and PDFs are passed as base64 `data:` URIs in `image_url` content blocks.

PRESERVED SEMANTICS:
  Retry on failures; a response that ends with "</think>" (thinking
  interruption, no final answer) is treated as failure and retried.
  RETRYABLE_STATUS_CODES + exponential backoff are kept.
  full_content = "<think>" + reasoning + "</think>" + content, so that
  parse_grading_response can strip the think block downstream.

Config via env (no secrets in code):
  JUDGE_BASE_URL   e.g. https://openrouter.ai/api/v1   (the /chat/completions
                   path is appended; a bare host also works)
  JUDGE_API_KEY    bearer token
  JUDGE_MODEL      model id (default arg model_name overrides if passed)
  JUDGE_HEADERS    optional JSON object of extra request headers.
"""

import os
import time
import json
import base64
import mimetypes

import requests


MAX_RETRIES = 10
RETRY_BACKOFF_BASE = 2  # 指数退避基数（秒）
MAX_RETRY_WAIT = 30     # 单次重试最大等待时间（秒）
RETRYABLE_STATUS_CODES = {400, 429, 500, 502, 503, 504}


def path_to_data_uri(file_path: str, default_mime: str = "image/png") -> str:
    """Read a local file and return a base64 `data:` URI.

    Used to feed image/PDF files to the OpenAI-compatible judge gateway. PDFs
    get `data:application/pdf;base64,...`; images get their guessed image/* mime.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = default_mime
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime_type};base64,{b64}"


def _resolve_endpoint(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return base_url + "/chat/completions"


def call_api(system_prompt, prompt, image_urls=None, pdf_urls=None,
             model_name=None, reasoning_effort="minimal", use_code_exec=False,
             max_retries=MAX_RETRIES):
    """Call the judge model over an OpenAI-compatible gateway, with retries.

    Args:
        system_prompt: judge system prompt.
        prompt: judge user prompt text.
        image_urls: list of image URLs / base64 data URIs (image channel).
        pdf_urls: list of PDF URLs / base64 data URIs (pdf channel).
        model_name: model id; falls back to env JUDGE_MODEL.

    Returns:
        (full_content, prompt_tokens, completion_tokens)
        full_content = "<think>" + reasoning + "</think>" + content.

    Raises:
        the last exception after all retries are exhausted.
    """
    image_urls = image_urls or []
    pdf_urls = pdf_urls or []

    base_url = os.environ.get("JUDGE_BASE_URL")
    api_key = os.environ.get("JUDGE_API_KEY")
    model = model_name or os.environ.get("JUDGE_MODEL")
    if not base_url or not api_key:
        raise ValueError(
            "judge call requires JUDGE_BASE_URL and JUDGE_API_KEY in the environment."
        )
    if not model:
        raise ValueError("judge call requires a model id (model_name arg or JUDGE_MODEL env).")

    url = _resolve_endpoint(base_url)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    # Optional gateway-specific extra headers.
    extra_headers = os.environ.get("JUDGE_HEADERS")
    if extra_headers:
        try:
            headers.update(json.loads(extra_headers))
        except (ValueError, TypeError) as e:
            print(f"[call_api] ignoring malformed JUDGE_HEADERS: {e}")

    # OpenAI-compatible user content: images, then PDFs, then text.
    user_content = []
    for image_url in image_urls:
        user_content.append({"type": "image_url", "image_url": {"url": image_url}})
    for pdf_url in pdf_urls:
        user_content.append({"type": "image_url", "image_url": {"url": pdf_url}})
    user_content.append({"type": "text", "text": prompt})

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 1.0,
        "max_tokens": 32768,
    }

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            responses_raw = requests.post(url, headers=headers, json=body, timeout=(300, 3600))
            responses_raw.raise_for_status()

            data = responses_raw.json()
            reasoning_content, content, prompt_tokens, total_tokens = _process_response(data)

            full_content = "<think>" + reasoning_content + "</think>" + content
            completion_tokens = total_tokens - prompt_tokens
            print(f"prompt_tokens: {prompt_tokens}, completion_tokens: {completion_tokens}")

            # thinking 中断：只有思考过程、没有最终回答 → 重试
            if full_content.endswith("</think>"):
                print("Warning: 模型输出仅包含思考过程但没有最终回答，可能是 thinking 中断了。重试")
                assert False

            return full_content, prompt_tokens, completion_tokens

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            print(f"Response body: {e.response.text if e.response is not None else 'N/A'}")
            if status_code is not None and status_code not in RETRYABLE_STATUS_CODES:
                print(f"[call_api] HTTP {status_code} 不可重试，直接抛出: {e}")
                raise
            last_exception = e
            print(f"[call_api] HTTP 错误 (HTTP {status_code})，第 {attempt}/{max_retries} 次重试: {e}")

        except requests.exceptions.ConnectionError as e:
            last_exception = e
            print(f"[call_api] 连接错误，第 {attempt}/{max_retries} 次重试: {e}")

        except requests.exceptions.Timeout as e:
            last_exception = e
            print(f"[call_api] 请求超时，第 {attempt}/{max_retries} 次重试: {e}")

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            last_exception = e
            print(f"[call_api] 响应解析失败，第 {attempt}/{max_retries} 次重试: {e}")

        except AssertionError as e:
            last_exception = e
            print(f"[call_api] 输出格式不符合预期，第 {attempt}/{max_retries} 次重试: {e}")

        except Exception as e:
            last_exception = e
            print(f"[call_api] 未知异常，第 {attempt}/{max_retries} 次重试: {e}")

        if attempt < max_retries:
            wait_time = min(RETRY_BACKOFF_BASE ** attempt, MAX_RETRY_WAIT)
            print(f"[call_api] 等待 {wait_time}s 后重试...")
            time.sleep(wait_time)

    print(f"[call_api] 已达最大重试次数 ({max_retries})，放弃请求。")
    raise last_exception


def _process_response(data):
    """Extract (reasoning_content, content, prompt_tokens, total_tokens) from an
    OpenAI-compatible chat/completions response.

    Reasoning may arrive as `message.reasoning_content` or `message.reasoning`
    on gateways that expose it; absent that it is "".
    """
    choice = data["choices"][0]
    message = choice["message"]
    content = message.get("content") or ""
    reasoning_content = message.get("reasoning_content") or message.get("reasoning") or ""

    usage = data.get("usage", {}) or {}
    prompt_tokens = usage.get("prompt_tokens", 0) or 0
    total_tokens = usage.get("total_tokens", 0) or 0

    return reasoning_content, content, prompt_tokens, total_tokens
