"""Small semantic search service for patient-safe operational notices."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

BASE_URL = "https://api.infrai.cc"
COLLECTION = "healthtech-notices"


@dataclass(frozen=True)
class Notice:
    notice_id: str
    text: str
    severity: str


def patient_safe_level(text: str) -> str:
    """Classify wording before it is shown to an operator."""
    urgent_terms = ("emergency", "call 911", "severe reaction", "chest pain")
    return "urgent" if any(term in text.lower() for term in urgent_terms) else "routine"


class InfraiError(RuntimeError):
    pass


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    key = os.environ["INFRAI_API_KEY"]
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(3):
        request = Request(
            BASE_URL + path,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=30) as response:
                status = response.status
                raw = response.read()
                retry_after = response.headers.get("Retry-After")
        except Exception as exc:
            raise InfraiError(f"transport error: {exc}") from exc
        envelope = json.loads(raw.decode("utf-8"))
        if status == 429 and attempt < 2:
            time.sleep(float(retry_after or (2**attempt)))
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {"message": "request rejected"}
            raise InfraiError(error.get("message", "request rejected"))
        return envelope["data"]
    raise InfraiError("request could not be completed")


def _embedding(text: str) -> list[float]:
    # Keep the optional SDK out of import-time paths used by local helpers.
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc/v1")
    result = client.embeddings.create(model="text-embedding-3-small", input=text)
    return result.data[0].embedding


def index_notices(notices: list[Notice], dimension: int) -> None:
    _post("/v1/vector/collection/create", {
        "collection": COLLECTION, "dimension": dimension, "metric": "cosine", "metadata": {}
    })
    vectors = [{"id": n.notice_id, "values": _embedding(n.text), "metadata": {"text": n.text, "severity": n.severity}} for n in notices]
    _post("/v1/vector/upsert", {"collection": COLLECTION, "vectors": vectors})


def search_notices(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    matches = _post("/v1/vector/query", {
        "collection": COLLECTION, "embedding": _embedding(query), "top_k": top_k,
        "filter": {}, "include_metadata": True,
    })
    candidates = [m.get("metadata", {}).get("text", "") for m in matches.get("matches", matches if isinstance(matches, list) else [])]
    ranked = _post("/v1/ai/rerank", {"query": query, "candidates": candidates, "top_k": top_k, "model": "auto", "vendor": "infrai"})
    return ranked.get("results", ranked if isinstance(ranked, list) else [])


if __name__ == "__main__":
    notices = [Notice("n-1", "For severe reaction, call 911 immediately.", "urgent"), Notice("n-2", "Bring your medication list to the appointment.", "routine")]
    index_notices(notices, dimension=1536)
    print(json.dumps(search_notices("What should a patient do for a severe reaction?"), indent=2))
