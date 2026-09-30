"""
`make report-html`: ONE self-contained HTML page for every suite -> report/index.html

Reads whatever the last runs left in report/data/ (nothing here runs a test):

  report/data/junit/*.xml          every pytest target (api, judge, sdk) - with each test's
                               testing type as a <property>, see the suites' conftest.py
  report/data/ui-results.json      Playwright's JSON reporter (the browser suite)
  report/data/kb-correctness.json  the KB-correctness run: expected value vs what the agent said
  report/data/livekit-sdk.*.json     live-call timings and report-only findings
  report/data/oracle-verdicts.json `make oracle`: every recorded call re-scored offline

Stdlib only, so it runs anywhere python3 does. Open the result straight from disk;
it links to report/playwright/ for traces, videos and screenshots.
"""

from __future__ import annotations

import html
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"          # what people open: index.html, playwright/, *.md
DATA = REPORT / "data"            # what the runs leave: junit, json, recordings, logs
TYPES = ["positive", "negative", "edge", "security", "nonfunctional"]
STATUSES = ["passed", "failed", "skipped"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------


def suite_of(classname: str, file_attr: str) -> str:
    for suite in ("api", "judge", "sdk"):
        if f"/{suite}/" in file_attr or classname.startswith(f"{suite}.") :
            return suite
    return "python"


def read_junit() -> list[dict]:
    """Latest result per test across every JUnit file (a later run wins)."""
    tests: dict[str, dict] = {}
    files = sorted((DATA / "junit").glob("*.xml"), key=lambda p: p.stat().st_mtime)
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        suite_name = path.stem
        for case in root.iter("testcase"):
            props = {p.get("name"): p.get("value") for p in case.iter("property")}
            status, message = "passed", ""
            for tag in ("failure", "error"):
                node = case.find(tag)
                if node is not None:
                    status, message = "failed", redact(node.get("message") or node.text or "")
            node = case.find("skipped")
            if node is not None and status == "passed":
                status, message = "skipped", redact(node.get("message") or "")
            file_attr = case.get("file") or ""
            classname = case.get("classname") or ""
            suite = "sdk" if "sdk" in suite_name or "livekit" in suite_name else (
                "judge" if suite_name.startswith(("judge", "oracle")) else (
                    "api" if suite_name.startswith(("api", "catalog", "ratelimit", "perf", "saturate")) else
                    suite_name.split("-")[-1]))
            key = f"{suite}::{classname}::{case.get('name')}"
            tests[key] = {
                "suite": suite,
                "id": f"{classname.replace('.', '/')}.py::{case.get('name')}" if classname else case.get("name"),
                "type": props.get("type", "unclassified"),
                "status": status,
                "message": message.strip(),
                "seconds": float(case.get("time") or 0),
                "source": path.name,
                "ran": mtime(path),
            }
    return list(tests.values())


def read_playwright() -> tuple[list[dict], str | None]:
    path = DATA / "ui-results.json"
    if not path.exists():
        return [], None
    data = json.loads(path.read_text(encoding="utf-8"))
    out: list[dict] = []

    def walk(suite: dict, titles: list[str]) -> None:
        here = titles + ([suite["title"]] if suite.get("title") and not suite["title"].endswith(".ts") else [])
        for spec in suite.get("specs", []):
            tags = set(spec.get("tags") or [])
            kind = next((t for t in TYPES if t in tags), "unclassified")
            for test in spec.get("tests", []):
                results = test.get("results") or []
                if not results:
                    # Listed, never executed (`playwright test --list` writes this
                    # file too) - not a result, so it must not read as "skipped".
                    continue
                last = results[-1]
                status = {"expected": "passed", "unexpected": "failed", "flaky": "passed",
                          "skipped": "skipped"}.get(test.get("status"), last.get("status", "skipped"))
                errors = last.get("errors") or ([last["error"]] if last.get("error") else [])
                message = "\n".join((e.get("message") or "") for e in errors)
                out.append({
                    "suite": "ui",
                    "id": f"{spec.get('file')}:{spec.get('line')} › {' › '.join(here[1:] + [spec['title']])}",
                    "type": kind,
                    "status": status,
                    "message": redact(_strip_ansi(message)).strip(),
                    # Screenshots Playwright took of a failure, embedded in the shareable file.
                    "screenshots": [a["path"] for a in last.get("attachments") or []
                                    if str(a.get("contentType", "")).startswith("image/") and a.get("path")],
                    "seconds": (last.get("duration") or 0) / 1000,
                    "source": "ui-results.json",
                    "ran": mtime(path),
                    "expectedFailure": test.get("expectedStatus") == "failed",
                })
        for child in suite.get("suites", []):
            walk(child, here)

    for suite in data.get("suites", []):
        walk(suite, [])
    return out, mtime(path)


def _strip_ansi(text: str) -> str:
    import re

    return re.sub(r"\x1b\[[0-9;]*m", "", text)


# Failure messages can carry credentials: VERIFIED 2026-09-28, an SDK assertion
# printed the whole session Grant, participant JWT included. The report is made
# to be shared, so every message goes through this first.
_SECRETS = [
    # Any JWT-shaped run, also a truncated one ("eyJhbG...eyJuYW" with the
    # signature cut off by a repr) - the header and claims alone are enough to leak.
    (re.compile(r"eyJ[A-Za-z0-9_-]{6,}(?:\.[A-Za-z0-9_-]*){0,2}"), "<token redacted>"),
    (re.compile(r"\b(?:sk-proj-|sk-|gsk_)[A-Za-z0-9_-]{16,}"), "<api key redacted>"),
    (re.compile(r"\bAPI[A-Za-z0-9]{10,}\b"), "<livekit key redacted>"),
    (re.compile(r"(?i)\b((?:api_?key|api_?secret|secret|password|authorization|token|participant_token)\s*[=:]\s*)['\"]?(?!<)[^\s'\",)<]{6,}"), r"\1<redacted>"),
]


def redact(text: str) -> str:
    for pattern, repl in _SECRETS:
        text = pattern.sub(repl, text)
    return text


def read_json(name: str) -> dict | None:
    path = DATA / name
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e4e3de;
--pass:#1f7a4d;--pass-bg:#e6f4ec;--fail:#b3261e;--fail-bg:#fbe9e7;--skip:#8a6d00;--skip-bg:#fdf5d8;
--accent:#2f5bd3;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;
--muted:#a3a29b;--line:#34332f;--pass:#6fd39e;--pass-bg:#15301f;--fail:#ff8a80;--fail-bg:#3a1714;
--skip:#e7c65a;--skip-bg:#332a0c;--accent:#8fb0ff}}
:root[data-theme="dark"]{--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;--muted:#a3a29b;--line:#34332f;
--pass:#6fd39e;--pass-bg:#15301f;--fail:#ff8a80;--fail-bg:#3a1714;--skip:#e7c65a;--skip-bg:#332a0c;--accent:#8fb0ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:28px 16px 64px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 12px}
.sub{color:var(--muted);margin:0 0 20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card .n{font-size:28px;font-weight:650;font-variant-numeric:tabular-nums}
.card .l{color:var(--muted);font-size:13px}
.ok{color:var(--pass)}.bad{color:var(--fail)}.warn{color:var(--skip)}
.banner{border-radius:10px;padding:14px 16px;margin:18px 0;font-weight:600}
.banner.ok{background:var(--pass-bg)}.banner.bad{background:var(--fail-bg)}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-weight:600;color:var(--muted);background:var(--card);position:sticky;top:0}
tr:last-child td{border-bottom:0}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600}
.pill.passed,.pill.PASS{background:var(--pass-bg);color:var(--pass)}
.pill.failed,.pill.FAIL,.pill.ERROR{background:var(--fail-bg);color:var(--fail)}
.pill.skipped,.pill.NOT{background:var(--skip-bg);color:var(--skip)}
code,.mono{font-family:var(--mono);font-size:12.5px}
details{margin:6px 0}summary{cursor:pointer}pre{white-space:pre-wrap;word-break:break-word;margin:6px 0 0;
font-family:var(--mono);font-size:12px;color:var(--muted)}
a{color:var(--accent)}.filters{margin:0 0 10px;display:flex;gap:8px;flex-wrap:wrap}
.filters button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;
padding:4px 12px;font:inherit;font-size:13px;cursor:pointer}.filters button[aria-pressed="true"]{border-color:var(--accent);color:var(--accent)}
.theme{float:right;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:4px 10px;cursor:pointer}
/* every count is a button: click it and the matching list opens right below */
button.card{font:inherit;color:inherit;text-align:left;cursor:pointer;width:100%}
button.card:hover,button.cnt:hover{border-color:var(--accent)}
button.card[aria-expanded="true"],button.cnt[aria-expanded="true"]{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent) inset}
button.cnt{font:inherit;font-variant-numeric:tabular-nums;min-width:2.4em;padding:2px 8px;border-radius:6px;
border:1px solid var(--line);background:var(--card);color:inherit;cursor:pointer}
button.cnt.bad{color:var(--fail);border-color:var(--fail)}button:disabled{opacity:.45;cursor:default;box-shadow:none}
.drill{margin:12px 0 4px;border:1px solid var(--accent);border-radius:10px;background:var(--card);overflow:hidden}
.drill[hidden]{display:none}
.drillhead{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:10px 14px;
border-bottom:1px solid var(--line);font-weight:600}
.drillhead button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:2px 10px;cursor:pointer;font:inherit}
.drill .tablewrap{border:0;border-radius:0;max-height:70vh;overflow:auto}
nav.toc{display:flex;gap:6px 14px;flex-wrap:wrap;margin:0 0 8px;font-size:13.5px}
td,pre,code,.mono{overflow-wrap:anywhere}\nimg.shot{display:block;max-width:100%;margin:8px 0;border:1px solid var(--line);border-radius:6px}
/* phones and narrow windows: every table row becomes a stacked card */
@media (max-width:760px){
main{padding:18px 12px 48px}h1{font-size:21px}h2{font-size:17px;margin-top:28px}
.cards{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.card .n{font-size:22px}
.tablewrap{overflow:visible}
table,thead,tbody,tr,th,td{display:block}thead{display:none}
tr{border-bottom:1px solid var(--line);padding:8px 10px}tr:last-child{border-bottom:0}
td{border:0;padding:3px 0;display:grid;grid-template-columns:7.5em minmax(0,1fr);gap:8px}
td::before{content:attr(data-label);color:var(--muted);font-size:12px;font-weight:600}
td>*{justify-self:start;max-width:100%;min-width:0}td>details,td>pre{justify-self:stretch}
td.num,th.num{text-align:left}
.theme{float:none;margin-bottom:8px}
}
"""

JS = """
const setTheme=t=>{document.documentElement.dataset.theme=t;try{localStorage.setItem('qa-theme',t)}catch(e){}};
try{const t=localStorage.getItem('qa-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}
document.getElementById('theme').onclick=()=>{const d=document.documentElement.dataset.theme;
const dark=d?d==='dark':matchMedia('(prefers-color-scheme: dark)').matches;setTheme(dark?'light':'dark')};
document.querySelectorAll('.filters').forEach(bar=>{const table=document.getElementById(bar.dataset.for);
bar.querySelectorAll('button').forEach(b=>b.onclick=()=>{bar.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed','false'));
b.setAttribute('aria-pressed','true');const want=b.dataset.v;table.querySelectorAll('tbody tr').forEach(tr=>{
tr.style.display=(want==='all'||tr.dataset.status===want||tr.dataset.type===want||tr.dataset.suite===want)?'':'none'})})});
// Stacked (phone) rows show their column name next to each value.
document.querySelectorAll('table').forEach(t=>{const heads=[...t.querySelectorAll('thead th')].map(th=>th.textContent);
t.querySelectorAll('tbody tr').forEach(tr=>[...tr.children].forEach((td,i)=>{if(heads[i])td.dataset.label=heads[i]}))});
// Drill-down: a count's data-drill is "key:value,key:value" matched against the
// data-* attributes of the rows of its source table; the matches are copied into
// the panel below the count. Clicking the same count again closes it.
const closeDrill=panel=>{panel.hidden=true;panel.innerHTML='';
document.querySelectorAll('[data-target="'+panel.id+'"]').forEach(x=>x.setAttribute('aria-expanded','false'))};
document.querySelectorAll('[data-drill]').forEach(b=>b.addEventListener('click',()=>{
const panel=document.getElementById(b.dataset.target);const open=b.getAttribute('aria-expanded')==='true';closeDrill(panel);
if(open)return;const spec=b.dataset.drill.split(',').filter(Boolean).map(p=>p.split(':'));
const src=document.getElementById(b.dataset.source||'all');
const rows=[...src.querySelectorAll('tbody tr')].filter(tr=>spec.every(([k,v])=>tr.dataset[k]===v));
const table=document.createElement('table');table.appendChild(src.querySelector('thead').cloneNode(true));
const body=document.createElement('tbody');rows.forEach(r=>{const c=r.cloneNode(true);c.style.display='';body.appendChild(c)});
table.appendChild(body);const wrap=document.createElement('div');wrap.className='tablewrap';wrap.appendChild(table);
const head=document.createElement('div');head.className='drillhead';
head.innerHTML='<span></span><button type="button" aria-label="Close list">×</button>';
head.firstChild.textContent=b.dataset.title+' — '+rows.length+(rows.length===1?' result':' results');
head.lastChild.onclick=()=>{closeDrill(panel);b.focus()};panel.append(head,wrap);panel.hidden=false;
b.setAttribute('aria-expanded','true');panel.scrollIntoView({block:'nearest',behavior:'smooth'})}));
"""


def count_button(n: int, drill: str, target: str, title: str, cls: str = "", source: str = "all") -> str:
    """A count that opens its own list below it (see JS: data-drill)."""
    dis = " disabled" if not n else ""
    return (f"<button type='button' class='cnt {cls}' data-drill='{esc(drill)}' data-target='{target}' data-source='{source}'"
            f" data-title='{esc(title)}' aria-expanded='false'{dis}>{n}</button>")


def pill(status: str) -> str:
    label = {"passed": "passed", "failed": "failed", "skipped": "skipped"}.get(status, status)
    cls = status.split()[0] if status else ""
    return f'<span class="pill {esc(cls)}">{esc(label)}</span>'


SHARE_NAME = "qa-report.html"
MAX_SHOT_BYTES = 1_500_000  # per screenshot; the shared file must stay attachable


def screenshots_html(t: dict) -> str:
    """A failed browser test's screenshots, inlined as data: URIs (share file only)."""
    import base64
    import mimetypes

    out = []
    for raw in (t.get("screenshots") or [])[:2]:
        path = Path(raw)
        if not path.is_file() or path.stat().st_size > MAX_SHOT_BYTES:
            continue
        kind = mimetypes.guess_type(path.name)[0] or "image/png"
        data = base64.b64encode(path.read_bytes()).decode()
        out.append(f"<img class='shot' alt='screenshot at failure' src='data:{kind};base64,{data}'>")
    return "".join(out)


def build() -> Path:
    """report/index.html (with links to report/playwright/ and report/data/) and
    report/qa-report.html - the same page as ONE self-contained file to send."""
    local, meta = render(share=False)
    shared, _ = render(share=True)
    out = REPORT / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(local, encoding="utf-8")
    (REPORT / SHARE_NAME).write_text(shared, encoding="utf-8")
    write_summary(*meta)
    return out


def render(share: bool) -> tuple[str, tuple]:
    py = read_junit()
    ui, ui_ran = read_playwright()
    tests = py + ui
    kb = read_json("kb-correctness.json")
    # One livekit-sdk*.json per SDK run (sdk/lkqa/report.py); findings from all of them.
    lk_files = sorted(DATA.glob("livekit-sdk*.json"))
    lk = {"findings": [f for p in lk_files for f in (read_json(p.name) or {}).get("findings", [])]}
    oracle = read_json("oracle-verdicts.json")
    interview = read_json("interview.json")

    by_suite: dict[str, Counter] = defaultdict(Counter)
    by_type: dict[str, Counter] = defaultdict(Counter)
    for t in tests:
        by_suite[t["suite"]][t["status"]] += 1
        by_type[t["type"]][t["status"]] += 1
    total = Counter(t["status"] for t in tests)
    failures = [t for t in tests if t["status"] == "failed"]
    generated = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")

    parts: list[str] = []
    add = parts.append
    add(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>QA Test Report</title><style>{CSS}</style></head><body><main>")
    add("<button class='theme' id='theme' type='button'>Theme</button>")
    add("<h1>Etnyre agent — QA test report</h1>")
    # The Playwright report is linked only when browser tests produced one: a
    # pytest-only run gets the HTML report alone (agreed 2026-09-28).
    ran_pw = (REPORT / "playwright" / "index.html").exists()
    # The shared file travels alone: links into report/ would be dead for its reader.
    has_pw = ran_pw and not share
    pw_line = ("Browser traces, videos and screenshots: <a href='playwright/index.html'>Playwright report</a>."
               if has_pw else
               "Shared copy: one self-contained file. Screenshots of failed browser tests are inside; "
               "Playwright traces and videos stay with the sender (report/playwright/)." if share and ran_pw else
               "Shared copy: one self-contained file." if share else
               "No browser tests in this run, so no Playwright report.")
    add(f"<p class='sub'>Generated {esc(generated)} from the last runs in <code>report/</code>. {pw_line}</p>")
    add("<nav class='toc'><a href='#by-suite'>By suite</a><a href='#by-type'>By type</a><a href='#failures'>Failures</a>"
        "<a href='#results'>All results</a>" + ("<a href='#kb'>KB correctness</a>" if kb else "")
        + ("<a href='#interview'>Interview</a>" if interview else "")
        + ("<a href='playwright/index.html'>Playwright report ↗</a>" if has_pw else "") + "</nav>")

    if not tests:
        add("<div class='banner bad'>No test results found. Run <code>make all</code> (or any make target) first.</div>")
    else:
        verdict_ok = not failures
        add(f"<div class='banner {'ok' if verdict_ok else 'bad'}'>"
            f"{'All ' + str(total['passed']) + ' executed tests passed' if verdict_ok else str(len(failures)) + ' failing test(s)'}"
            f" · {total['skipped']} skipped · {len(tests)} results across {len(by_suite)} suite(s)</div>")

        add("<div class='cards'>")
        for label, n, cls, drill in (("Passed", total["passed"], "ok", "status:passed"),
                                     ("Failed", total["failed"], "bad" if total["failed"] else "ok", "status:failed"),
                                     ("Skipped", total["skipped"], "warn", "status:skipped"), ("Results", len(tests), "", "")):
            dis = " disabled" if not n else ""
            add(f"<button type='button' class='card' data-drill='{drill}' data-target='drill-cards' data-source='all' "
                f"data-title='{label}' aria-expanded='false'{dis}><div class='n {cls}'>{n}</div><div class='l'>{label} ▾</div></button>")
        if kb:
            counts = Counter(c["verdict"] for c in kb.get("calls", []))
            for verdict, label, cls in (("PASS", "KB answers correct", "ok"), ("FAIL", "KB answers wrong", "bad"),
                                        ("NOT SCORED", "KB not scored", "warn")):
                n = counts.get(verdict, 0)
                dis = " disabled" if not n else ""
                add(f"<button type='button' class='card' data-drill='verdict:{verdict}' data-target='drill-cards' data-source='kbtable' "
                    f"data-title='{label}' aria-expanded='false'{dis}><div class='n {cls if n else ''}'>{n}</div>"
                    f"<div class='l'>{label} ▾</div></button>")
        add("</div><div class='drill' id='drill-cards' hidden></div>")

        # -- per suite
        add("<h2 id='by-suite'>By suite</h2><div class='tablewrap'><table><thead><tr><th>Suite</th>"
            + "".join(f"<th class='num'>{s}</th>" for s in STATUSES) + "<th>From</th></tr></thead><tbody>")
        sources = defaultdict(set)
        for t in tests:
            sources[t["suite"]].add(f"{t['source']} ({t['ran']})")
        names = {"api": "API (pytest)", "judge": "Judge + oracle (pytest)", "sdk": "LiveKit SDK (pytest)", "ui": "Browser (Playwright)"}
        for suite in sorted(by_suite, key=lambda s: ["api", "judge", "sdk", "ui"].index(s) if s in ["api", "judge", "sdk", "ui"] else 9):
            c = by_suite[suite]
            add(f"<tr><td>{esc(names.get(suite, suite))}</td>" + "".join(
                f"<td class='num'>{count_button(c[s], f'suite:{suite},status:{s}', 'drill-suite', f'{names.get(suite, suite)} · {s}', 'bad' if s == 'failed' and c[s] else '')}</td>"
                for s in STATUSES)
                + f"<td class='mono'>{esc(', '.join(sorted(sources[suite]))[:220])}</td></tr>")
        add("</tbody></table></div><div class='drill' id='drill-suite' hidden></div>")

        # -- per testing type
        add("<h2 id='by-type'>By testing type</h2><div class='tablewrap'><table><thead><tr><th>Type</th>"
            + "".join(f"<th class='num'>{s}</th>" for s in STATUSES) + "</tr></thead><tbody>")
        for kind in TYPES + ["unclassified"]:
            if kind not in by_type:
                continue
            c = by_type[kind]
            add(f"<tr><td>{esc(kind)}</td>" + "".join(
                f"<td class='num'>{count_button(c[s], f'type:{kind},status:{s}', 'drill-type', f'{kind} · {s}', 'bad' if s == 'failed' and c[s] else '')}</td>"
                for s in STATUSES) + "</tr>")
        add("</tbody></table></div><div class='drill' id='drill-type' hidden></div>")

        # -- failures
        add(f"<h2 id='failures'>Failures ({len(failures)})</h2>")
        if not failures:
            add("<p class='ok'>None.</p>")
        else:
            add("<div class='tablewrap'><table><thead><tr><th>Suite</th><th>Type</th><th>Test</th><th>Why</th></tr></thead><tbody>")
            for t in sorted(failures, key=lambda x: (x["suite"], x["id"])):
                msg = t["message"] or "(no message)"
                first = msg.splitlines()[0][:220] if msg else ""
                add(f"<tr><td>{esc(t['suite'])}</td><td>{esc(t['type'])}</td><td class='mono'>{esc(t['id'])}</td>"
                    f"<td><details><summary>{esc(first)}</summary><pre>{esc(msg[:4000])}</pre></details></td></tr>")
            add("</tbody></table></div>")

        # -- all tests, filterable
        add("<h2 id='results'>All results</h2><div class='filters' data-for='all'>"
            "<button type='button' aria-pressed='true' data-v='all'>All</button>"
            + "".join(f"<button type='button' aria-pressed='false' data-v='{s}'>{s}</button>" for s in STATUSES)
            + "".join(f"<button type='button' aria-pressed='false' data-v='{k}'>{k}</button>" for k in TYPES)
            + "".join(f"<button type='button' aria-pressed='false' data-v='{s}'>{s}</button>" for s in ("api", "judge", "sdk", "ui"))
            + "</div><div class='tablewrap'><table id='all'><thead><tr><th>Status</th><th>Suite</th><th>Type</th><th>Test</th>"
            "<th class='num'>Seconds</th></tr></thead><tbody>")
        for t in sorted(tests, key=lambda x: (x["suite"], x["id"])):
            note = " <span class='pill skipped'>expected-failure (known defect)</span>" if t.get("expectedFailure") else ""
            skip = f"<pre>{esc(t['message'][:400])}</pre>" if t["status"] == "skipped" and t["message"] else ""
            if t["status"] == "failed":
                msg = t["message"] or "(no message)"
                # Screenshots ride on this row (not the Failures table) because the
                # clickable counts copy their lists from here.
                shots = screenshots_html(t) if share else ""
                skip = f"<details><summary>{esc(msg.splitlines()[0][:220])}</summary><pre>{esc(msg[:4000])}</pre>{shots}</details>"
            add(f"<tr data-status='{t['status']}' data-type='{esc(t['type'])}' data-suite='{t['suite']}'>"
                f"<td>{pill(t['status'])}</td><td>{esc(t['suite'])}</td><td>{esc(t['type'])}</td>"
                f"<td class='mono'>{esc(t['id'])}{note}{skip}</td><td class='num'>{t['seconds']:.1f}</td></tr>")
        add("</tbody></table></div>")

    # -- KB correctness
    if kb:
        calls = kb.get("calls", [])
        counts = Counter(c["verdict"] for c in calls)
        add(f"<h2 id='kb'>KB correctness — live calls judged against <code>resources/kb</code></h2>"
            f"<p class='sub'>{esc(kb.get('finishedAt', ''))} · {counts.get('PASS', 0)} correct, {counts.get('FAIL', 0)} wrong, "
            f"{counts.get('NOT SCORED', 0)} not scored, {counts.get('ERROR', 0)} errors. "
            "Verdict by the deterministic oracle — no model. Recordings in <code>report/data/recordings/</code>.</p>")
        add("<div class='tablewrap'><table id='kbtable'><thead><tr><th>Verdict</th><th>Scenario</th><th>Question</th><th>KB value</th>"
            "<th>Agent's direct answer</th><th>Why / other values outside the entry</th></tr></thead><tbody>")
        order = {"FAIL": 0, "ERROR": 1, "NOT SCORED": 2, "PASS": 3}
        for c in sorted(calls, key=lambda c: (order.get(c["verdict"], 9), c["scenario"])):
            why = "; ".join(c.get("failures") or []) or c.get("error") or ""
            off = ", ".join(c.get("offScope") or [])
            detail = esc(why) + (f"<pre>outside this entry (reported only): {esc(off)}</pre>" if off else "")
            add(f"<tr data-verdict='{esc(c['verdict'])}'><td>{pill(c['verdict'])}</td><td class='mono'>{esc(c['scenario'])}</td><td>{esc(c.get('question', ''))}</td>"
                f"<td>{esc(', '.join(c.get('expected') or []))}</td><td>{esc(', '.join(c.get('stated') or []))}</td>"
                f"<td>{detail}</td></tr>")
        add("</tbody></table></div>")
        if kb.get("excludedDataDefects"):
            add(f"<p class='sub'>Excluded as data defects (their expected facts are not in their own KB entry): "
                f"{esc(', '.join(kb['excludedDataDefects']))}</p>")

    # -- adaptive interview
    if interview:
        rows = [q for c in interview.get("calls", []) for q in c.get("questions", [])]
        counts = Counter(q.get("verdict") for q in rows)
        add(f"<h2 id='interview'>Adaptive interview — LLM-written KB questions, judged</h2>"
            f"<p class='sub'>{esc(interview.get('finishedAt', ''))} · {esc(interview.get('provider'))} {esc(interview.get('model'))} · "
            f"{len(rows)} questions on {len(interview.get('calls', []))} calls: {counts.get('PASS', 0)} correct, "
            f"{counts.get('FAIL', 0)} wrong, {counts.get('INCONCLUSIVE', 0)} inconclusive, {counts.get('NOT ANSWERED', 0)} not answered. "
            "Each question follows the agent's previous answer and is asked only if its KB quote is verbatim in the KB file; "
            "each answer is judged by the deterministic oracle and by the LLM with the agreed auditor rubric.</p>")
        for c in interview.get("calls", []):
            add(f"<h3 class='mono'>{esc(c.get('kb'))} · serial {esc(c.get('serial'))}</h3><div class='tablewrap'><table><thead><tr>"
                "<th>#</th><th>Verdict</th><th>Question (LLM, from the KB)</th><th>KB quote</th><th>Agent's answer</th><th>Why</th></tr></thead><tbody>")
            for i, q in enumerate(c.get("questions", []), 1):
                judge = q.get("judge") or {}
                why = "; ".join((q.get("oracle") or {}).get("failures") or []) + " " + "; ".join(judge.get("objections") or [])
                flag = "" if judge.get("evidenceVerified", True) else "<br><span class='pill skipped'>judge evidence not found in answer — check by hand</span>"
                if judge.get("disputed"):
                    flag += "<br><span class='pill skipped'>disputed — the KB file states every objection; check by hand</span>"
                if judge.get("judgedBy"):
                    flag += f"<div class='mono'>judged by {esc(judge.get('judgedBy'))}</div>"
                verdict = q.get("verdict", "")
                add(f"<tr><td class='num'>{i}</td><td>{pill('PASS' if verdict == 'PASS' else ('FAIL' if verdict == 'FAIL' else 'NOT'))} {esc(verdict)}</td>"
                    f"<td>{esc(q.get('question'))}<div class='mono'>{esc(q.get('entry'))}</div></td><td>{esc(q.get('kbQuote'))}</td>"
                    f"<td><details><summary>{esc((q.get('answer') or '')[:140])}</summary><pre>{esc(q.get('answer'))}</pre></details></td>"
                    f"<td>{esc(why.strip())}{flag}</td></tr>")
            add("</tbody></table></div>")

    # -- LiveKit findings
    if lk and lk.get("findings"):
        add("<h2>LiveKit findings (report-only)</h2><div class='tablewrap'><table><thead><tr><th>ID</th><th>Finding</th></tr></thead><tbody>")
        seen = set()
        for f in lk["findings"]:
            key = (f.get("id"), f.get("summary"))
            if key in seen:
                continue
            seen.add(key)
            add(f"<tr><td class='mono'>{esc(f.get('id'))}</td><td>{esc(f.get('summary'))}</td></tr>")
        add("</tbody></table></div>")

    # -- oracle
    if oracle and oracle.get("totals"):
        tot = oracle["totals"]
        add(f"<h2>Oracle re-score of every recorded call</h2><p class='sub'>{len(oracle.get('calls', []))} calls · "
            f"{tot.get('pass', 0)} checks passed, {tot.get('fail', 0)} failed, {tot.get('notApplicable', 0)} not applicable "
            "(report-only; the SDK tests above apply the zero-tolerance gates).</p>")

    if not share:
        add("<h2>Where everything is</h2><ul>"
            + ("<li><a href='playwright/index.html'>Playwright HTML report</a> — browser runs with traces, video, screenshots</li>" if has_pw else "")
            + "<li><code>report/kb-correctness.md</code> (+ <code>data/kb-correctness.json</code>) — the KB table above</li>"
            "<li><code>report/interview.md</code> (+ <code>data/interview.json</code>) — the adaptive interview above</li>"
            "<li><code>report/data/livekit-sdk.*.json</code> — every live-call timing and finding</li>"
            "<li><code>report/data/recordings/</code> — one transcript per call (SDK and browser), re-scorable offline</li>"
            "<li><code>report/data/junit/</code> — the raw JUnit XML per make target</li></ul>")
    add(f"<script>{JS}</script></main></body></html>")
    return "".join(parts), (by_suite, total, failures, kb)


def write_summary(by_suite: dict[str, Counter], total: Counter, failures: list[dict], kb: dict | None) -> Path:
    """report/summary.md - the same totals in Markdown, for a CI job summary
    ($GITHUB_STEP_SUMMARY), where an HTML file cannot be shown inline."""
    lines = ["## QA test report", "",
             f"**{total['passed']} passed, {total['failed']} failed, {total['skipped']} skipped**", "",
             "| Suite | Passed | Failed | Skipped |", "|---|---|---|---|"]
    lines += [f"| {name} | {c['passed']} | {c['failed']} | {c['skipped']} |" for name, c in sorted(by_suite.items())]
    if kb and kb.get("calls"):
        verdicts = Counter(c.get("verdict", "?") for c in kb["calls"])
        lines += ["", "KB correctness: " + ", ".join(f"{v} {k}" for k, v in sorted(verdicts.items()))]
    if failures:
        lines += ["", "### Failures", ""]
        for t in failures[:40]:
            first = (t.get("message") or "").strip().splitlines()[:1]
            lines.append(f"- `{t['suite']}` {t['id']}" + (f" — {first[0][:200]}" if first else ""))
        if len(failures) > 40:
            lines.append(f"- … and {len(failures) - 40} more, in index.html")
    lines += ["", "Download the **qa-report** artifact: `index.html` (combined) and "
              "`playwright/index.html` (browser traces, video, screenshots)."]
    path = REPORT / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    path = build()
    pw = REPORT / "playwright" / "index.html"
    print("reports:")
    print(f"  HTML report        {path.relative_to(ROOT)}   (make report-all opens it)")
    print(f"  Shareable file     {(REPORT / SHARE_NAME).relative_to(ROOT)}   (one self-contained file to send; make report-share)")
    if pw.exists():
        print(f"  Playwright report  {pw.relative_to(ROOT)}   (make report opens it)")
    else:
        print("  Playwright report  not produced - this run had no browser tests")
