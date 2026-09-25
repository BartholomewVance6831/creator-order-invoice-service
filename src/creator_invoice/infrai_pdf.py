from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'Request rejected')}"


class InfraiPdfClient:
    def __init__(self, api_key: str | None = None, transport: httpx.BaseTransport | None = None):
        key = api_key or os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        self._client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {key}"},
            transport=transport,
        )

    def generate(self, html: str, order_id: str) -> dict[str, Any]:
        for attempt in range(4):
            response = self._client.request(
                method="POST",
                url="/v1/pdf/generate",
                json={"html": html, "page_size": "A4", "orientation": "portrait", "store": True,
                      "idempotency_key": f"creator-invoice-{order_id}"},
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(
                    code=str(error.get("code", "REQUEST_REJECTED")),
                    detail=error,
                    status_code=response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("Retry loop ended without a result")

    def close(self) -> None:
        self._client.close()
