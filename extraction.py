import os
import time
import json
import logging
from dataclasses import dataclass, field
from typing import Any, TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from utils import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    ENV_API_KEY,
    ENV_BASE_URL,
    ENV_MODEL,
    MAX_ATTEMPTS,
    MAX_COMPLETION_TOKENS,
    TokenUsage,
    merge_usages,
)

load_dotenv()

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _coerce_nested_json_strings(obj: Any) -> Any:
    """Recursively parse JSON strings into dicts/lists so Pydantic can validate them."""
    if isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, (dict, list)):
                return _coerce_nested_json_strings(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
        return obj
    if isinstance(obj, dict):
        return {k: _coerce_nested_json_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_coerce_nested_json_strings(item) for item in obj]
    return obj


@dataclass
class ExtractionResult:
    """Result of a structured extraction call."""

    data: dict
    usage: TokenUsage | None = None
    elapsed: float = 0.0
    attempts: int = 0

    @property
    def input_tokens(self) -> int:
        return self.usage.prompt_tokens if self.usage else 0

    @property
    def output_tokens(self) -> int:
        return self.usage.completion_tokens if self.usage else 0

    @property
    def cached_tokens(self) -> int:
        return self.usage.cached_tokens if self.usage else 0


@dataclass
class ExtractionConfig:
    """Tuneable knobs for the extraction pipeline."""

    model: str = field(default_factory=lambda: os.environ.get(ENV_MODEL, DEFAULT_MODEL))
    max_attempts: int = MAX_ATTEMPTS
    max_completion_tokens: int = MAX_COMPLETION_TOKENS
    temperature: float = 0
    top_p: float = 1
    base_url: str = field(
        default_factory=lambda: os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL)
    )


def get_client(config: ExtractionConfig | None = None) -> OpenAI:
    """Create an OpenAI client from env vars."""
    cfg = config or ExtractionConfig()
    client = OpenAI(base_url=cfg.base_url, api_key=os.environ[ENV_API_KEY])
    log.info("Client initialised (base_url=%s, model=%s)", cfg.base_url, cfg.model)
    return client


def extract_structured(
    client: OpenAI,
    document: str,
    schema: type[T],
    tool_name: str,
    tool_description: str,
    config: ExtractionConfig | None = None,
) -> ExtractionResult:
    """
    General-purpose structured extraction from OCR / document text.

    Pipeline:
      1. Build system + user messages from the document
      2. Register a tool whose JSON schema matches `schema`
      3. Call the LLM with forced tool_choice
      4. Parse + validate the tool call arguments against `schema`
      5. On failure, append the validation error and retry (up to max_attempts)
      6. Return the parsed data along with token / timing stats

    Args:
        client:          OpenAI client
        document:        Raw OCR text or any document string
        schema:          Pydantic BaseModel subclass defining the output shape
        tool_name:       Name for the tool function
        tool_description: Description for the tool function
        config:          Optional ExtractionConfig overrides

    Returns:
        ExtractionResult with .data (dict) and usage stats

    Raises:
        RuntimeError if all attempts fail
    """
    cfg = config or ExtractionConfig()

    # ── Build tool schema ────────────────────────────────────────────────
    tool = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": schema.model_json_schema(),
        },
    }
    log.info("Tool registered: %s", tool_name)

    # ── Build messages ───────────────────────────────────────────────────
    messages = [
        {
            "role": "system",
            "content": (
                "You must call the function exactly once. "
                "Do not answer in plain text. "
                "Return only values that satisfy the schema."
            ),
        },
        {
            "role": "user",
            "content": document,
        },
    ]
    log.info("Messages prepared (%d initial)", len(messages))

    # ── Retry loop ───────────────────────────────────────────────────────
    last_error = None
    usages: list[TokenUsage] = []
    start = time.perf_counter()

    for attempt in range(1, cfg.max_attempts + 1):
        log.info("── Attempt %d/%d ──", attempt, cfg.max_attempts)

        if last_error:
            messages.append(
                {
                    "role": "user",
                    "content": f"Fix the previous output. Validation error: {last_error}",
                }
            )
            log.info("Appended retry feedback")

        # ── Call LLM ─────────────────────────────────────────────────────
        log.info("Calling %s …", cfg.model)
        call_start = time.perf_counter()

        resp = client.chat.completions.create(
            model=cfg.model,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": tool_name}},
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            max_completion_tokens=cfg.max_completion_tokens,
            stream=False,
            extra_body={"thinking": {"type": "disabled"}},
        )

        call_elapsed = time.perf_counter() - call_start
        log.info("LLM responded in %.2fs", call_elapsed)

        # ── Token usage ──────────────────────────────────────────────────
        usage = TokenUsage.from_api_usage(resp.usage)
        usages.append(usage)
        log.info(
            "Tokens — in: %d (cached: %d), out: %d",
            usage.prompt_tokens,
            usage.cached_tokens,
            usage.completion_tokens,
        )

        # ── Extract tool call ────────────────────────────────────────────
        msg = resp.choices[0].message
        if not msg.tool_calls:
            last_error = "Model did not return a tool call."
            log.warning("No tool_calls — %s", last_error)
            continue

        raw_args = msg.tool_calls[0].function.arguments
        log.info("Raw args: %s", raw_args[:300])

        # ── Validate ─────────────────────────────────────────────────────
        try:
            args = json.loads(raw_args)
            args = _coerce_nested_json_strings(args)
            parsed = schema.model_validate(args)
            log.info("Validation passed")
            log.info("Parsed: %s", parsed.model_dump())
            elapsed = time.perf_counter() - start
            return ExtractionResult(
                data=parsed.model_dump(),
                usage=merge_usages(usages),
                elapsed=elapsed,
                attempts=attempt,
            )
        except (ValidationError, json.JSONDecodeError) as e:
            last_error = str(e)
            log.warning("Validation failed: %s", last_error[:200])

    # ── All attempts exhausted ───────────────────────────────────────────
    elapsed = time.perf_counter() - start
    log.error("All %d attempts failed", cfg.max_attempts)
    raise RuntimeError(
        f"Could not get valid structured output after {cfg.max_attempts} attempts: "
        f"{last_error}"
    )
