# Decision Intelligence LLM deployment runbook

Status: provider adapter foundation only. LLM remains optional and non-authoritative.

## Recommended first server setup: Groq Cloud

No LLM model weights are uploaded to the NEXUS server.

The server receives only:

1. NEXUS code containing `ReasoningModelPort` and the OpenAI-compatible adapter.
2. A server-side secret `GROQ_API_KEY` supplied outside Git/source control.
3. Provider configuration selecting `groq` and model `openai/gpt-oss-20b` initially.
4. Normal outbound HTTPS access to `https://api.groq.com/openai/v1` from the research/reasoning runtime only.

Suggested environment values (names are deployment wiring targets, not yet application startup wiring):

```text
NEXUS_REASONING_PROVIDER=groq
NEXUS_REASONING_MODEL=openai/gpt-oss-20b
NEXUS_REASONING_BASE_URL=https://api.groq.com/openai/v1
GROQ_API_KEY=<server secret only>
```

Never commit `GROQ_API_KEY`, print it, expose it to UI, pass it to Core domain, or make it available to exchange adapters.

## Local/offline fallback: Ollama

Ollama is optional and should normally run on an off-production research host with sufficient RAM/GPU rather than the small NEXUS runtime host.

Example compatible endpoint:

```text
NEXUS_REASONING_PROVIDER=ollama
NEXUS_REASONING_MODEL=gpt-oss:20b
NEXUS_REASONING_BASE_URL=http://127.0.0.1:11434/v1
```

If Ollama is hosted on another research machine, expose it only through an approved private network/TLS boundary. Do not open an unauthenticated Ollama endpoint to the public Internet.

## Failure behavior

If Groq/Ollama is unavailable or malformed, the adapter returns `ReasoningStatus.DEGRADED`. This must not stop:

```text
Intelligence → deterministic/ML Decision Core → Portfolio Risk → Core
```

No LLM response is a trading command, trusted fact, validation result, promotion approval, or Risk decision.

## Remaining before server activation

- wire provider config into an application composition root;
- store/read the API key through the approved secrets layer;
- add outbound-network policy for the reasoning runtime;
- certify one real Groq request in non-production research mode;
- record model/provider/prompt/policy/evidence hashes for each reasoning artifact;
- verify logs contain no API key or prompt-sensitive secrets;
- keep REAL/Restricted Live/Full Live permissions unchanged.

Official references:

- https://console.groq.com/docs/openai
- https://console.groq.com/docs/structured-outputs
- https://console.groq.com/docs/rate-limits
- https://docs.ollama.com/api/openai-compatibility
