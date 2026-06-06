"""Token usage tracking for API responses."""

from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token counts from an API response.

    For OpenAI-compatible providers (including MiMo):
      prompt_tokens INCLUDES cached_tokens.
      cached_tokens is a subset — not additive.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0

    @property
    def billable_input_tokens(self) -> int:
        """Tokens billed at cache-miss rate (prompt_tokens - cached_tokens)."""
        return max(0, self.prompt_tokens - self.cached_tokens)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @classmethod
    def from_api_usage(cls, usage) -> "TokenUsage":
        """Extract from OpenAI SDK Usage object (or None-safe mock)."""
        if usage is None:
            return cls()
        cached = 0
        if hasattr(usage, "prompt_tokens_details") and usage.prompt_tokens_details:
            cached = getattr(usage.prompt_tokens_details, "cached_tokens", 0) or 0
        return cls(
            prompt_tokens=usage.prompt_tokens or 0,
            completion_tokens=usage.completion_tokens or 0,
            cached_tokens=cached,
        )


def merge_usages(usages: list[TokenUsage]) -> TokenUsage:
    """Sum multiple TokenUsage objects (e.g. across retry attempts)."""
    return TokenUsage(
        prompt_tokens=sum(u.prompt_tokens for u in usages),
        completion_tokens=sum(u.completion_tokens for u in usages),
        cached_tokens=sum(u.cached_tokens for u in usages),
    )
