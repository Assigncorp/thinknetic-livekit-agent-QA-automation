"""
Build report/index.html - the smoke run's report, for people who were not there.

    uv run --project tests/sdk python tools/build_report.py

Reads whatever the run left in report/data/ and never fails because a part is
missing (a stage that did not run is shown as "Did not run" and fails the
banner). Self-contained: inline CSS and JS, no network, readable on a phone.

Inputs
    report/data/junit-unit.xml      routing + validator unit tests (pytest)
    report/data/ui-results.json     Playwright JSON reporter
    report/data/kb-smoke.json       the live KB-steps call (tests/sdk/tests/test_kb_call.py)
    report/playwright/index.html    linked as "Technical details"
"""

from __future__ import annotations

import html
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"
DATA = REPORT / "data"
IST = ZoneInfo("Asia/Kolkata")

e = html.escape


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def run_meta() -> dict:
    branch = os.getenv("GITHUB_REF_NAME") or _git("rev-parse", "--abbrev-ref", "HEAD")
    commit = os.getenv("GITHUB_SHA") or _git("rev-parse", "HEAD")
    server, repo, run_id = (os.getenv(k, "") for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    return {
        "branch": branch or "unknown",
        "commit": commit[:7] if commit else "unknown",
        "commitUrl": f"{server}/{repo}/commit/{commit}" if server and repo and commit else "",
        "runUrl": f"{server}/{repo}/actions/runs/{run_id}" if server and repo and run_id else "",
        "startedAt": os.getenv("SMOKE_STARTED_AT", ""),
    }


def unit_results() -> dict | None:
    path = DATA / "junit-unit.xml"
    if not path.exists():
        return None
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    tests = failures = skipped = 0
    failed: list[str] = []
    for s in suites:
        for case in s.iter("testcase"):
            tests += 1
            if case.find("skipped") is not None:
                skipped += 1
            elif case.find("failure") is not None or case.find("error") is not None:
                failures += 1
                failed.append(f"{case.get('classname', '').split('.')[-1]}::{case.get('name')}")
    return {"tests": tests, "failures": failures, "skipped": skipped, "failed": failed,
            "passed": tests > 0 and failures == 0}


def ui_results() -> dict | None:
    path = DATA / "ui-results.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    tests: list[dict] = []

    def walk(suite: dict) -> None:
        for spec in suite.get("specs", []):
            for t in spec.get("tests", []):
                results = t.get("results", [])
                last = results[-1] if results else {}
                notes = t.get("annotations", []) + last.get("annotations", [])
                rooms = list(dict.fromkeys(a.get("description", "") for a in notes
                                           if a.get("type") == "livekit-room" and a.get("description")))
                tests.append({
                    "title": spec.get("title", ""),
                    "rooms": rooms,
                    "status": last.get("status", "skipped"),
                    "durationMs": last.get("duration", 0),
                    "retries": max(0, len(results) - 1),
                    "steps": [{"title": s.get("title", ""), "error": bool(s.get("error"))}
                              for s in last.get("steps", [])
                              if s.get("title") not in ("Before Hooks", "After Hooks", "Worker Cleanup")],
                    "error": (last.get("error") or {}).get("message", "") if last.get("status") != "passed" else "",
                    "attachments": [a.get("path", "") for a in last.get("attachments", []) if a.get("path")],
                })
        for child in suite.get("suites", []):
            walk(child)

    for s in data.get("suites", []):
        walk(s)
    passed = bool(tests) and all(t["status"] in ("passed", "expected") for t in tests)
    return {"tests": tests, "passed": passed}


def kb_results() -> dict | None:
    path = DATA / "kb-smoke.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2430;--muted:#5b6675;--line:#e3e7ec;--pass:#137a3e;--pass-bg:#e6f4ea;
--fail:#b42318;--fail-bg:#fdecea;--warn:#8a5a00;--warn-bg:#fff4dc;--accent:#2457c5;--agent:#eef2f7;--caller:#e7effd}
@media (prefers-color-scheme:dark){:root{--bg:#11151a;--card:#1a2028;--ink:#e6e9ee;--muted:#9aa5b4;--line:#2b333d;
--pass:#5fd08a;--pass-bg:#15301f;--fail:#ff8a7a;--fail-bg:#3a1c19;--warn:#f0c060;--warn-bg:#352a12;--accent:#8fb0ff;
--agent:#222a34;--caller:#1d2a44}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
main{max-width:1000px;margin:0 auto;padding:16px}
h1{font-size:1.5rem;margin:0}h2{font-size:1.2rem;margin:0 0 12px}h3{font-size:1rem;margin:16px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:0 0 16px}
.banner{border-radius:12px;padding:20px;margin:0 0 16px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.banner.pass{background:var(--pass-bg);color:var(--pass)}.banner.fail{background:var(--fail-bg);color:var(--fail)}
.banner .big{font-size:2.6rem;font-weight:800;letter-spacing:.04em}.banner p{margin:4px 0 0;color:var(--ink)}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 16px;margin:0}
.meta div{min-width:0}.meta dt{color:var(--muted);font-size:.8rem}.meta dd{margin:0;overflow-wrap:anywhere}
.pill{display:inline-block;border-radius:999px;padding:2px 10px;font-size:.8rem;font-weight:700;white-space:nowrap}
.pill.pass{background:var(--pass-bg);color:var(--pass)}.pill.fail{background:var(--fail-bg);color:var(--fail)}
.pill.skip{background:var(--warn-bg);color:var(--warn)}
ol.checks{list-style:none;padding:0;margin:0}ol.checks li{display:flex;gap:12px;align-items:flex-start;
padding:10px 0;border-top:1px solid var(--line)}ol.checks li:first-child{border-top:0}
.num{flex:0 0 28px;height:28px;border-radius:50%;display:grid;place-items:center;font-weight:700;font-size:.85rem}
.num.pass{background:var(--pass-bg);color:var(--pass)}.num.fail{background:var(--fail-bg);color:var(--fail)}
.grow{flex:1;min-width:0}.muted{color:var(--muted);font-size:.9rem}.time{color:var(--muted);font-size:.85rem;white-space:nowrap}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;vertical-align:top;padding:8px;border-top:1px solid var(--line)}th{color:var(--muted);font-weight:600}
td.kb{min-width:220px}td.said{min-width:200px}.kw{font-size:.82rem}.kw .ok{color:var(--pass)}.kw .no{color:var(--fail)}
.reason{color:var(--fail);font-size:.88rem;margin-top:4px}
.chat{display:flex;flex-direction:column;gap:8px}.bubble{max-width:85%;padding:8px 12px;border-radius:14px;overflow-wrap:anywhere}
.bubble.agent{background:var(--agent);align-self:flex-start;border-bottom-left-radius:4px}
.bubble.caller{background:var(--caller);align-self:flex-end;border-bottom-right-radius:4px}
.bubble .who{font-size:.75rem;color:var(--muted);display:block;margin-bottom:2px}
.tag{font-size:.72rem;border:1px solid var(--line);border-radius:6px;padding:0 6px;margin-left:6px;color:var(--muted)}
.rating{font-size:1.4rem;font-weight:800}
.ref{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0}
.ref dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:6px 16px;margin:0}
.ref dt{color:var(--muted);font-size:.78rem}.ref dd{margin:0;overflow-wrap:anywhere;font-family:ui-monospace,Menlo,monospace;font-size:.9rem}
.qa .q{background:var(--caller);border-radius:10px;padding:10px 12px;margin:6px 0 12px}
.qa ol{margin:6px 0;padding-left:22px}.qa li{margin:0 0 6px}
.banner .refs{margin:8px 0 0;padding-left:18px;color:var(--ink);font-size:.92rem}
.banner .refs code{background:rgba(255,255,255,.55)}
details{margin-top:8px}summary{cursor:pointer;color:var(--accent)}a{color:var(--accent)}
code{font-size:.85em;background:var(--bg);padding:1px 5px;border-radius:5px}
ul.plain{margin:6px 0;padding-left:20px}
@media (max-width:700px){.steps thead{display:none}.steps tr{display:block;border-top:1px solid var(--line);padding:8px 0}
.steps td{display:block;border:0;padding:4px 0;min-width:0}.steps td::before{content:attr(data-label);display:block;
color:var(--muted);font-size:.75rem;font-weight:600}.banner .big{font-size:2rem}}
"""


def pill(passed: bool | None, yes: str = "Pass", no: str = "Fail", none: str = "Did not run") -> str:
    if passed is None:
        return f'<span class="pill skip">{e(none)}</span>'
    return f'<span class="pill {"pass" if passed else "fail"}">{e(yes if passed else no)}</span>'


def secs(ms: int | None) -> str:
    if ms is None:
        return "-"
    return f"{ms / 1000:.1f} s" if ms < 120_000 else f"{ms / 60000:.1f} min"


def ist(iso: str) -> str:
    if not iso:
        return "-"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return iso
    return dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")


def render_steps_table(validation: dict) -> str:
    rows = []
    for item in validation.get("items", []):
        found = "".join(f'<span class="ok">✓ {e(k)}</span><br>' for k in item["keywordsFound"])
        missing = "".join(f'<span class="no">✗ {e(k)}</span><br>' for k in item["keywordsMissing"])
        reason = f'<div class="reason">{e(item["reason"])}</div>' if item["reason"] and item["result"] != "pass" else ""
        said = e(item["said"]) if item["said"] else '<span class="muted">nothing matching</span>'
        rows.append(
            f"<tr><td class=kb data-label='KB step / caution'><strong>{e(item['ref'])}</strong><br>"
            f"<span class=muted>{e(item['kbText'])}</span></td>"
            f"<td class=said data-label='What the agent said'>{said}</td>"
            f"<td class=kw data-label='Keywords found / missing'>{found}{missing}</td>"
            f"<td data-label='Result'>{pill(item['result'] == 'pass', 'Pass', item['resultLabel'])}{reason}</td></tr>")
    return ('<div class="table-wrap"><table class="steps"><thead><tr><th>KB step / caution</th><th>What the agent said</th>'
            '<th>Keywords found / missing</th><th>Result</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def render_chat(events: list[dict], rating: int | None) -> str:
    out = ['<div class="chat">']
    for ev in events:
        who = "Agent" if ev["role"] == "agent" else "Test caller"
        tag = f'<span class="tag">{e(ev["tag"])}</span>' if ev.get("tag") else ""
        text = e(ev["text"])
        if ev.get("tag") == "rating":
            text = f'<span class="rating">{text}</span>'
        out.append(f'<div class="bubble {ev["role"]}"><span class="who">{who} · {secs(ev.get("atMs"))}{tag}</span>{text}</div>')
    out.append("</div>")
    if rating is not None:
        out.append(f'<p class="muted">Random rating given by the test caller: <strong>{rating}</strong> (1–10).</p>')
    return "".join(out)


def room_ref(att: dict) -> str:
    """One line naming the call's LiveKit room - what to search for in LiveKit Cloud and the agent logs."""
    sid = f" · room ID {att['roomSid']}" if att.get("roomSid") else ""
    return f"room {att.get('room') or '-'}{sid}"


def render_reference(att: dict) -> str:
    return ('<div class="ref"><dl>'
            f'<div><dt>LiveKit room ID</dt><dd>{e(att.get("roomSid") or "not assigned")}</dd></div>'
            f'<div><dt>Room name</dt><dd>{e(att.get("room") or "-")}</dd></div>'
            f'<div><dt>Call started</dt><dd>{e(ist(att.get("startedAt", "")))}</dd></div>'
            f'<div><dt>Agent participant</dt><dd>{e(att.get("agentIdentity") or "never joined")}</dd></div>'
            '</dl></div>')


def render_qa(att: dict, fallback_question: str) -> str:
    asked = [ev["text"] for ev in att["events"] if ev.get("tag") == "question"]
    answer = att.get("answer") or [ev["text"] for ev in att["events"] if ev.get("tag") == "answer"]
    question = asked[-1] if asked else fallback_question
    q_note = "" if asked else ' <span class="muted">(not asked - the call ended before the question)</span>'
    a_html = ("<ol>" + "".join(f"<li>{e(t)}</li>" for t in answer) + "</ol>" if answer
              else '<p class="reason">No answer was received.</p>')
    return (f'<div class="qa"><h3>Question asked</h3><div class="q">“{e(question)}”{q_note}</div>'
            f'<h3>Answer received</h3><p class="muted">The agent\'s answer turns, in order '
            f'({len(answer)} turn{"" if len(answer) == 1 else "s"}).</p>{a_html}</div>')


def render_attempt(att: dict, entry: dict, open_: bool) -> str:
    cps = att["checkpoints"]
    items = []
    for i, cp in enumerate(cps, start=1):
        cls = "pass" if cp["passed"] else "fail"
        detail = f'<div class="muted">{e(cp["detail"])}</div>' if cp["detail"] else ""
        timing = f'at {secs(cp["atMs"])} · took {secs(cp["tookMs"])}' if cp["atMs"] is not None else "not reached"
        items.append(f'<li><span class="num {cls}">{i}</span><div class="grow"><strong>{e(cp["label"])}</strong>'
                     f' {pill(cp["passed"])}{detail}</div><span class="time">{timing}</span></li>')
    v = att.get("validation")
    steps = render_steps_table(v) if v else '<p class="muted">No answer was validated in this attempt.</p>'
    split = ""
    if v:
        segs = "".join(f"<li><code>[{s['index']}]</code> {e(s['text'])}</li>" for s in v["segments"])
        split = (f"<details><summary>How the answer was split into steps ({e(v['splitMethod'])}, "
                 f"{len(v['segments'])} parts)</summary><ol class=plain start=0>{segs}</ol></details>")
    err = f'<p class="reason">Error: {e(att["error"])}</p>' if att.get("error") else ""
    body = (f'<h3>Call reference</h3>{render_reference(att)}'
            f'{render_qa(att, entry.get("question", ""))}'
            f'<h3>The nine checks</h3><ol class="checks">{"".join(items)}</ol>{err}'
            f'<h3>The answer, step by step</h3>{steps}{split}'
            f'<h3>The call, as it happened</h3>{render_chat(att["events"], att.get("rating"))}'
            f'<p class="muted">Call length {secs(att["durationMs"])}</p>')
    title = (f'Attempt {att["number"]} {pill(att["passed"])} '
             f'<span class="time">{e(att.get("roomSid") or att.get("room") or "")}</span>')
    return f'<details{" open" if open_ else ""} class="card"><summary><strong>{title}</strong></summary>{body}</details>'


def build() -> str:
    meta = run_meta()
    unit, ui, kb = unit_results(), ui_results(), kb_results()
    parts_ok = [x["passed"] if x else False for x in (unit, ui, kb)]
    overall = all(parts_ok)

    sel = (kb or {}).get("selection", {})
    entry = (kb or {}).get("entry", {})
    started = meta["startedAt"] or (kb or {}).get("startedAt", "")
    finished = (kb or {}).get("finishedAt", "")
    duration = "-"
    if started and finished:
        try:
            d = datetime.fromisoformat(finished) - datetime.fromisoformat(started.replace("Z", "+00:00"))
            duration = secs(int(d.total_seconds() * 1000))
        except ValueError:
            pass

    failed_parts = [name for name, ok in zip(("unit checks", "website check", "phone-call check"), parts_ok) if not ok]
    summary = ("Everything checked out: the website works, and the support agent answered a real question "
               "correctly from its manual, step by step, and closed the call properly." if overall else
               "Something needs attention: " + ", ".join(failed_parts) + ". Details below.")
    commit = (f'<a href="{e(meta["commitUrl"])}">{e(meta["commit"])}</a>' if meta["commitUrl"] else e(meta["commit"]))
    run_link = f' · <a href="{e(meta["runUrl"])}">CI run</a>' if meta["runUrl"] else ""

    refs: list[str] = []
    for att in (kb or {}).get("attempts", []):
        if not att.get("passed"):
            refs.append(f'Phone-call check, attempt {att["number"]}: <code>{e(room_ref(att))}</code>')
    for t in (ui or {}).get("tests", []):
        if t["status"] != "passed":
            where = (", ".join(f"<code>room {e(r)}</code>" for r in t["rooms"]) if t["rooms"]
                     else "no call room - it failed before a call was started")
            refs.append(f"Website check: {where}")
    refs_html = ('<p><strong>Reference for what failed</strong></p><ul class="refs">'
                 + "".join(f"<li>{r}</li>" for r in refs) + "</ul>") if refs else ""
    banner = (f'<section class="banner {"pass" if overall else "fail"}"><div class="big">{"PASS" if overall else "FAIL"}</div>'
              f'<div class="grow"><h1>Agent smoke test</h1><p>{e(summary)}</p>{refs_html}</div></section>')
    meta_html = (
        '<section class="card"><dl class="meta">'
        f'<div><dt>Run time</dt><dd>{e(ist(started))}</dd></div>'
        f'<div><dt>Duration</dt><dd>{e(duration)}</dd></div>'
        f'<div><dt>Branch</dt><dd>{e(meta["branch"])}</dd></div>'
        f'<div><dt>Commit</dt><dd>{commit}{run_link}</dd></div>'
        f'<div><dt>Machine model tested</dt><dd>{e(sel.get("model", "-"))}</dd></div>'
        f'<div><dt>Serial number used</dt><dd>{e(sel.get("serial", "-"))}</dd></div>'
        f'<div><dt>Knowledge base file</dt><dd>{e(sel.get("kbFile", "-"))}</dd></div>'
        f'<div><dt>Why this serial is that model</dt><dd>{e(sel.get("sheet", "-"))} · {e(sel.get("hopperType", "-"))}'
        f'<br><span class="muted">{e(sel.get("classificationBasis", ""))}</span></dd></div>'
        '</dl></section>')

    overview = ('<section class="card"><h2>What was checked</h2><ol class="checks">'
                f'<li><span class="num {"pass" if parts_ok[0] else "fail"}">1</span><div class="grow"><strong>Unit checks</strong> '
                f'{pill(unit["passed"] if unit else None)}<div class="muted">Serial-to-model routing and the step-by-step '
                f'answer checker, tested without a live call'
                + (f' · {unit["tests"]} run, {unit["failures"]} failed' if unit else "") + '</div></div></li>'
                f'<li><span class="num {"pass" if parts_ok[1] else "fail"}">2</span><div class="grow"><strong>Website check</strong> '
                f'{pill(ui["passed"] if ui else None)}<div class="muted">The product page loads, everything on it is in '
                f'place, bad input is refused, and "Talk to me" starts a call'
                + "".join(f' · call room <code>{e(r)}</code>' for t in (ui or {}).get("tests", []) for r in t["rooms"])
                + '</div></div></li>'
                f'<li><span class="num {"pass" if parts_ok[2] else "fail"}">3</span><div class="grow"><strong>Phone-call check</strong> '
                f'{pill(kb["passed"] if kb else None)}<div class="muted">A test caller asked the agent a real question '
                f'and checked the answer against the manual'
                + (" · retried once" if kb and kb.get("retried") else "")
                + "".join(f' · <code>{e(room_ref(a))}</code>' for a in (kb or {}).get("attempts", []))
                + '</div></div></li></ol></section>')

    call = ""
    if kb:
        attempts = kb.get("attempts", [])
        retry_note = (f'<p class="muted">The first call failed, so it was tried once more in a fresh room. '
                      f'The verdict is the last attempt; every attempt is shown.</p>' if kb.get("retried") else "")
        call = ('<section class="card"><h2>The phone-call check</h2>'
                f'<p><strong>Question asked:</strong> “{e(sel.get("question", ""))}”</p>'
                f'<p class="muted">From the knowledge base section “{e(sel.get("kbSection", ""))}” '
                f'({len(entry.get("steps", []))} steps, {len(entry.get("cautions", []))} cautions) · '
                f'question <code>{e(sel.get("questionId", ""))}</code> · seed <code>{e(str(sel.get("seed", "")))}</code></p>'
                f'{retry_note}</section>'
                + "".join(render_attempt(a, entry, i == len(attempts) - 1) for i, a in enumerate(attempts)))
    else:
        call = '<section class="card"><h2>The phone-call check</h2><p>Did not run.</p></section>'

    ui_html = ""
    if ui:
        rows = []
        for t in ui["tests"]:
            steps = "".join(f'<li>{"✗ " if s["error"] else "✓ "}{e(s["title"])}</li>' for s in t["steps"])
            err = f'<p class="reason">{e(t["error"][:600])}</p>' if t["error"] else ""
            shots = "".join(
                f'<li><a href="{e(os.path.relpath(a, REPORT))}">{e(Path(a).name)}</a></li>'
                for a in t["attachments"] if a and Path(a).exists())
            shots = f"<p class=muted>Trace and screenshots:</p><ul class=plain>{shots}</ul>" if shots else ""
            room = ('<div class="ref"><dl><div><dt>Call room (LiveKit room name)</dt><dd>'
                    + (e(", ".join(t["rooms"])) if t["rooms"] else "no call was started") + '</dd></div></dl></div>')
            rows.append(f'<details class="card"{"" if t["status"] == "passed" else " open"}><summary><strong>{e(t["title"])}</strong> '
                        f'{pill(t["status"] == "passed")} <span class="time">{secs(t["durationMs"])}</span></summary>'
                        f'{room}{err}<ul class=plain>{steps}</ul>{shots}</details>')
        ui_html = '<section><h2>The website check</h2>' + "".join(rows) + "</section>"

    unit_html = ""
    if unit and unit["failed"]:
        unit_html = ('<section class="card"><h2>Unit checks that failed</h2><ul class=plain>' +
                     "".join(f"<li><code>{e(x)}</code></li>" for x in unit["failed"]) + "</ul></section>")

    tech = ('<section class="card"><h2>Technical details</h2><ul class=plain>'
            '<li><a href="playwright/index.html">Playwright report</a> (traces and screenshots on failure)</li>'
            '<li><a href="data/kb-smoke.json">Raw call data (JSON)</a></li>'
            + (f'<li>Re-run this exact call: <code>KB_SEED={e(str(sel.get("seed", "")))} make smoke</code></li>' if sel else "")
            + "</ul></section>")

    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            f"<title>Agent Smoke Test</title><style>{CSS}</style></head><body><main>"
            f"{banner}{meta_html}{overview}{call}{ui_html}{unit_html}{tech}"
            f"<p class=muted>Generated {e(datetime.now(timezone.utc).astimezone(IST).strftime('%d %b %Y, %I:%M %p IST'))}</p>"
            "</main></body></html>")


def main() -> int:
    REPORT.mkdir(parents=True, exist_ok=True)
    out = REPORT / "index.html"
    out.write_text(build(), encoding="utf-8")
    print(f"report -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
