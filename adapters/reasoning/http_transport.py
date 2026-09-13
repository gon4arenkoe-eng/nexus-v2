"""Small stdlib JSON HTTP transport for optional reasoning adapters."""

from __future__ import annotations

import asyncio
import json
from typing import Mapping
from urllib.request import Request, urlopen


class UrllibJSONTransport:
    async def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: int,
    ) -> Mapping[str, object]:
        return await asyncio.to_thread(
            self._post_json,
            url,
            dict(headers),
            dict(payload),
            timeout_seconds,
        )

    @staticmethod
    def _post_json(
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: int,
    ) -> Mapping[str, object]:
        request = Request(
            url,
            data=json.dumps(payload, default=str).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("JSON response must be an object")
        return decoded
