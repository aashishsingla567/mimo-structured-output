import os
import time
import json
import logging
from dataclasses import dataclass
from typing import Any, Type, TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ValidationError

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
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed: float = 0.0
    attempts: int = 0


@dataclass
class ExtractionConfig:
    """Tuneable knobs for the extraction pipeline."""

    model: str = os.environ.get("MIMO_MODEL", "mimo-v2.5")
    max_attempts: int = 3
    max_completion_tokens: int = 5120
    temperature: float = 0
    top_p: float = 1
    base_url: str = os.environ.get(
        "MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1"
    )


def get_client(config: ExtractionConfig | None = None) -> OpenAI:
    """Create an OpenAI client from env vars."""
    cfg = config or ExtractionConfig()
    client = OpenAI(base_url=cfg.base_url, api_key=os.environ["MIMO_API_KEY"])
    log.info("Client initialised (base_url=%s, model=%s)", cfg.base_url, cfg.model)
    return client


def extract_structured(
    client: OpenAI,
    document: str,
    schema: Type[T],
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
    total_in = 0
    total_out = 0
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
        usage = resp.usage
        if usage:
            in_tok = usage.prompt_tokens
            out_tok = usage.completion_tokens
            total_in += in_tok
            total_out += out_tok
            log.info(
                "Tokens — in: %d, out: %d (cumulative: %d / %d)",
                in_tok,
                out_tok,
                total_in,
                total_out,
            )
        else:
            log.warning("No usage info in response")

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
                input_tokens=total_in,
                output_tokens=total_out,
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
