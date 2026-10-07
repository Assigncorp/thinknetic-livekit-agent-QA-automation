"""
A free hosted LLM, over the OpenAI-compatible chat API that Groq and Google
Gemini both expose - so one stdlib client serves either, chosen by config.

  config livekitSdk.llm.provider   "groq" (default) | "gemini"
  .env   GROQ_API_KEY / GEMINI_API_KEY  - created by YOU, free:
         https://console.groq.com/keys   https://aistudio.google.com/apikey

Used only by the adaptive interview (tests/test_interview.py): to WRITE the next
caller question from the KB, and to JUDGE the agent's answer against the KB.
The deterministic oracle stays in charge of every figure regardless.

Data note, agreed 2026-09-28: the KB passages and the call transcripts in each
request are sent to the chosen provider.
"""

from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .bridge import testbed


class LlmUnavailable(RuntimeError):
    """No key, or the provider is unreachable. A reason to skip, never to pass."""


class LlmBadOutput(RuntimeError):
    """The model answered, but not in the shape asked for."""


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    model: str
    key_env: str


def _cfg() -> dict[str, Any]:
    return testbed.config()["livekitSdk"]["llm"]


def _provider(name: str) -> Provider:
    p = _cfg()["providers"][name]
    model = os.getenv("LLM_MODEL") if name == os.getenv("LLM_PROVIDER", _cfg()["provider"]) and os.getenv("LLM_MODEL") else p["model"]
    return Provider(name, p["baseUrl"].rstrip("/"), model, p["keyEnv"])


def chain() -> list[Provider]:
    """The primary provider, then the fallbacks - only those with a key set."""
    names = [os.getenv("LLM_PROVIDER", _cfg()["provider"])] + [n for n in _cfg().get("fallback", []) if n]
    seen, out = set(), []
    for n in names:
        if n in seen or n not in _cfg()["providers"]:
            continue
        seen.add(n)
        out.append(_provider(n))
    return out


def provider() -> Provider:
    """The provider the next request will go to."""
    live = [p for p in chain() if os.getenv(p.key_env) and p.name not in _exhausted]
    return live[0] if live else chain()[0]


_exhausted: set[str] = set()
last_used: str = ""


def available() -> tuple[bool, str]:
    if any(os.getenv(p.key_env) and p.name not in _exhausted for p in chain()):
        return True, ""
    p = chain()[0]
    if _exhausted:
        return False, f"daily quota used up on {sorted(_exhausted)} and no fallback key is set"
    return False, (
        f"{p.key_env} is not set in .env - the adaptive interview needs a free {p.name} key "
        f"({_cfg()['providers'][p.name]['keyUrl']}); set LLM_PROVIDER to switch provider"
    )


def _context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover
        return ssl.create_default_context()


# Groq sits behind Cloudflare, which answers Python's default "Python-urllib/x"
# user agent with 403 "error code: 1010" - VERIFIED 2026-09-28 with a valid key.
USER_AGENT = "thinknetic-livekit-qa/1.0 (+https://github.com/Assigncorp/thinknetic-livekit-agent-QA-automation)"


def _post(url: str, body: dict[str, Any], key: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json", "authorization": f"Bearer {key}", "user-agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(req, context=_context(), timeout=90) as resp:
        return json.loads(resp.read())


def _is_daily_quota(detail: str) -> bool:
    d = detail.lower()
    return any(k in d for k in ("per day", "tokens per day", "(tpd)", "requests per day", "(rpd)", "insufficient_quota", "exceeded your current quota"))


def chat_json(system: str, user: str, *, temperature: float, seed: int | None = None) -> dict[str, Any]:
    """One chat completion that must come back as a JSON object.

    Providers are tried in chain() order. A per-minute 429 waits out its
    Retry-After (bounded); a DAILY quota error marks that provider exhausted for
    this process and moves on to the next one at once - VERIFIED 2026-09-28,
    Groq's free tier: 200k tokens/day on gpt-oss-120b. Any other HTTP error is
    raised with its body, because "the judge said FAIL" and "the judge never
    ran" must never look alike. `last_used` names the provider/model that
    answered, so every verdict can say who gave it.
    """
    global last_used
    ok, why = available()
    if not ok:
        raise LlmUnavailable(why)
    retries = int(_cfg()["maxRetries"])
    errors: list[str] = []
    for p in [x for x in chain() if os.getenv(x.key_env) and x.name not in _exhausted]:
        body: dict[str, Any] = {
            "model": p.model,
            "temperature": temperature,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
        }
        if seed is not None:
            body["seed"] = seed
        data = None
        attempt = 0
        while attempt <= retries:
            try:
                data = _post(f"{p.base_url}/chat/completions", body, os.environ[p.key_env])
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:600]
                if exc.code == 429 and _is_daily_quota(detail):
                    _exhausted.add(p.name)
                    errors.append(f"{p.name}: daily quota used up")
                    break
                if exc.code == 429 and attempt < retries:
                    wait = float(exc.headers.get("retry-after") or 2 ** (attempt + 2))
                    time.sleep(min(wait, 60))
                    attempt += 1
                    continue
                if exc.code == 400 and ("temperature" in detail or "seed" in detail) and ("temperature" in body or "seed" in body):
                    # Some newer models accept only their default sampling.
                    body.pop("temperature", None)
                    body.pop("seed", None)
                    continue
                if exc.code in (401, 403):
                    raise LlmUnavailable(f"{p.name} rejected {p.key_env} (HTTP {exc.code}): {detail}") from exc
                raise LlmUnavailable(f"{p.name} HTTP {exc.code}: {detail}") from exc
            except urllib.error.URLError as exc:
                errors.append(f"{p.name} unreachable: {exc}")
                break
        if data is None:
            continue
        last_used = f"{p.name}/{p.model}"
        text = data["choices"][0]["message"]["content"] or ""
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            start, end = text.find("{"), text.rfind("}")
            if start < 0 or end <= start:
                raise LlmBadOutput(f"not JSON: {text[:200]!r}") from exc
            parsed = json.loads(text[start : end + 1])
        if not isinstance(parsed, dict):
            raise LlmBadOutput(f"expected a JSON object, got {type(parsed).__name__}")
        return parsed
    raise LlmUnavailable("no LLM provider could answer: " + "; ".join(errors or ["no key set"]))


def list_models(p: Provider | None = None) -> list[str]:
    """`make llm-check`: prove a key works and its configured model exists."""
    p = p or provider()
    req = urllib.request.Request(
        f"{p.base_url}/models", headers={"authorization": f"Bearer {os.environ[p.key_env]}", "user-agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, context=_context(), timeout=30) as resp:
        data = json.loads(resp.read())
    return sorted(m.get("id", "") for m in data.get("data", []))


if __name__ == "__main__":
    for p in chain():
        if not os.getenv(p.key_env):
            print(f"{p.name:7} {p.model:26} {p.key_env} MISSING")
            continue
        try:
            models = list_models(p)
            bare = [m.split("/", 1)[-1] for m in models]
            found = p.model in models or p.model in bare
            print(f"{p.name:7} {p.model:26} key ok, {len(models)} models, configured model {'FOUND' if found else 'NOT FOUND'}")
        except Exception as exc:  # noqa: BLE001
            print(f"{p.name:7} {p.model:26} FAILED: {exc}")
    reply = chat_json("Reply with a JSON object.", 'Return {"ok": true} as JSON.', temperature=0)
    print(f"round trip via {last_used}: {reply}")
