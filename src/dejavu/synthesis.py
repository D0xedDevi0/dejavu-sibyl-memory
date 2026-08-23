"""LLM-backed skill synthesis for THE FLEET (Lane 4 upgrade).

Plugs the SDK's `BYOKSummarizer` into an OpenAI-compatible endpoint so the
Learner's accepted skills are actual synthesized strategies mined from the
fleet's shared journal — not template text. Falls back to the local
deterministic summarizer on any failure: learning never breaks the fleet.

Endpoint resolution order:
  1. FLEET_LLM_URL env var (any OpenAI-compatible /v1 base)
  2. Hermes proxy on 127.0.0.1:8901/v1 if reachable
  3. None -> deterministic fallback
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request

log = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("FLEET_LLM_MODEL", "tencent/hy3:free")
PROXY_URL = "http://127.0.0.1:8901/v1"
# The Hermes proxy 403s default bot UAs (Python-urllib); send a plain client UA.
UA = "fleet-synth/1.0"


def _headers(extra: dict | None = None) -> dict:
    h = {"User-Agent": UA, "Authorization": "Bearer fleet"}
    if extra:
        h.update(extra)
    return h


def _probe(url: str, timeout: float = 4.0) -> bool:
    try:
        req = urllib.request.Request(f"{url}/models", headers=_headers())
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception:
        return False


def resolve_endpoint() -> str | None:
    url = os.environ.get("FLEET_LLM_URL")
    if url and _probe(url.rstrip("/")):
        return url.rstrip("/")
    if _probe(PROXY_URL):
        return PROXY_URL
    return None


def make_inference_fn(endpoint: str | None = None,
                      model: str | None = None,
                      timeout_s: int = 120):
    """Return inference_fn(prompt)->str for BYOKSummarizer, or None."""
    endpoint = endpoint or resolve_endpoint()
    if endpoint is None:
        log.info("[synth] no LLM endpoint available; using deterministic")
        return None
    model = model or DEFAULT_MODEL

    def infer(prompt: str) -> str:
        payload = json.dumps({
            "model": model,
            "max_tokens": 700,
            "messages": [
                {"role": "system", "content":
                    "You distill an agent fleet's repeated behavioral patterns "
                    "into a compact, reusable strategy skill. Output ONLY the "
                    "skill body: a one-line rule plus 2-4 bullet conditions. "
                    "No preamble."},
                {"role": "user", "content": prompt},
            ],
        }).encode()
        req = urllib.request.Request(
            f"{endpoint}/chat/completions", data=payload,
            headers=_headers({"Content-Type": "application/json"}))
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"]
        # Some reasoning models put prose in .reasoning and burn budget;
        # guard against empty content by falling back to reasoning tail.
        if not content.strip():
            raise ValueError("empty completion")
        return content.strip()

    return infer


def build_summarizer(*, enabled: bool | None = None):
    """Construct a BYOKSummarizer wired to the best available endpoint.

    Opt-in: set FLEET_SYNTH=1 (or pass enabled=True) so library code and the
    test suite stay hermetic/deterministic by default; the fleet CLI turns it
    on automatically. Returns None when disabled or no endpoint is up.
    """
    from sibyl_memory_client.learning import BYOKSummarizer
    if enabled is None:
        enabled = os.environ.get("FLEET_SYNTH", "") not in ("", "0", "false")
    if not enabled:
        return None
    fn = make_inference_fn()
    if fn is None:
        return None
    try:
        return BYOKSummarizer(fn, provider_label="nous-fleet")
    except Exception as e:
        log.warning("[synth] BYOK construction failed (%s); deterministic", e)
        return None
