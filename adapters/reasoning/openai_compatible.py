"""OpenAI-compatible reasoning adapters for optional research/reasoning LLMs.

No exchange, Risk, Core execution, or credential-store dependency is allowed.
The injected transport keeps network I/O outside the decision domain and makes
adapter behavior deterministic in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Mapping, Protocol

from apps.decision_intelligence.domain.decision import (
    ReasoningRequest,
    ReasoningResult,
    ReasoningStatus,
)
from apps.decision_intelligence.ports.reasoning import ReasoningModelPort


class JSONTransport(Protocol):
    async def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: int,
    ) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class OpenAICompatibleReasoningConfig:
    provider: str
    model_id: str
    base_url: str
    api_key: str | None = None
    timeout_seconds: int = 30
    temperature: float = 0.0
    max_tokens: int = 1200

    def __post_init__(self) -> None:
        for name in ("provider", "model_id", "base_url"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("base_url must be http(s)")
        if self.timeout_seconds <= 0 or self.max_tokens <= 0:
            raise ValueError("timeout_seconds and max_tokens must be positive")
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")


class OpenAICompatibleReasoningAdapter(ReasoningModelPort):
    def __init__(
        self,
        *,
        config: OpenAICompatibleReasoningConfig,
        transport: JSONTransport,
    ) -> None:
        self._config = config
        self._transport = transport

    async def reason(self, request: ReasoningRequest) -> ReasoningResult:
        payload = {
            "model": self._config.model_id,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a NEXUS research reasoning model. Return JSON only. "
                        "You may analyze evidence and propose hypotheses, but you have no "
                        "authority to execute trades, change risk limits, or promote models."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "task": request.task,
                            "context": dict(request.structured_context),
                            "evidence_refs": request.evidence_refs,
                            "prompt_template_version": request.prompt_template_version,
                            "system_policy_version": request.system_policy_version,
                        },
                        sort_keys=True,
                        default=str,
                    ),
                },
            ],
        }
        if self._config.provider.lower() == "groq":
            payload["reasoning_format"] = "hidden"
        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        try:
            response = await self._transport.post_json(
                url=f"{self._config.base_url.rstrip('/')}/chat/completions",
                headers=headers,
                payload=payload,
                timeout_seconds=self._config.timeout_seconds,
            )
            output = _extract_json_object(response)
            output_hash = sha256(
                json.dumps(output, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()
            return ReasoningResult(
                request_id=request.request_id,
                status=ReasoningStatus.AVAILABLE,
                provider=self._config.provider,
                model_id=self._config.model_id,
                output=output,
                output_hash=output_hash,
                created_at=datetime.now(UTC),
                prompt_template_version=request.prompt_template_version,
                system_policy_version=request.system_policy_version,
            )
        except Exception as exc:  # fail-degraded: LLM is optional, never trading authority
            error_code = type(exc).__name__.upper()
            output = {"reasoning_available": False, "error_code": error_code}
            output_hash = sha256(json.dumps(output, sort_keys=True).encode("utf-8")).hexdigest()
            return ReasoningResult(
                request_id=request.request_id,
                status=ReasoningStatus.DEGRADED,
                provider=self._config.provider,
                model_id=self._config.model_id,
                output=output,
                output_hash=output_hash,
                created_at=datetime.now(UTC),
                prompt_template_version=request.prompt_template_version,
                system_policy_version=request.system_policy_version,
                error_code=error_code,
            )


def groq_config(*, model_id: str = "openai/gpt-oss-20b", api_key: str | None = None) -> OpenAICompatibleReasoningConfig:
    return OpenAICompatibleReasoningConfig(
        provider="groq",
        model_id=model_id,
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )


def ollama_config(*, model_id: str = "gpt-oss:20b", base_url: str = "http://127.0.0.1:11434/v1") -> OpenAICompatibleReasoningConfig:
    return OpenAICompatibleReasoningConfig(
        provider="ollama",
        model_id=model_id,
        base_url=base_url,
        api_key=None,
    )


def _extract_json_object(response: Mapping[str, object]) -> Mapping[str, object]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("reasoning response missing choices")
    first = choices[0]
    if not isinstance(first, Mapping):
        raise ValueError("reasoning response choice must be object")
    message = first.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("reasoning response missing message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("reasoning response missing content")
    decoded = json.loads(content)
    if not isinstance(decoded, Mapping):
        raise ValueError("reasoning output must be JSON object")
    return dict(decoded)
