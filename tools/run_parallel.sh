#!/usr/bin/env bash
# Parallel runner behind `make all-parallel` and `make livekit-sdk`.
#
# The limit is not CPU, it is the shared dev agent: at most 3 live calls in
# flight (livekitSdk.kbRun.parallel, approved for the shared deployment). So the
# fastest safe schedule keeps exactly 3 single-call lanes busy, and runs
# everything that starts no agent side by side. In waves, each finishing before
# the next starts:
#
#   1 offline     no network                       all at once
#   2 endpoints   API + LiveKit server, no agent   the rate-limit tests in `api`
#                                                  stay isolated from other
#                                                  endpoint traffic
#   3 live        3 lanes, one call each at a time
#   4 kb run      the 48-call KB run - 3 at a time on its own
#   5 concurrency 3 calls at once on purpose, so it runs alone
#
# One log per lane in report/data/logs/, a pass/fail line per target as each ends,
# and both reports at the end: report/index.html and report/playwright/.
# Continues past failures; exits 1 if any target failed.
#
#   tools/run_parallel.sh all   everything (api, judge, sdk, browser)
#   tools/run_parallel.sh live  real agent calls only (KB-judged), visible browser, no offline,
#                               LIVE_PARALLEL (default 8) calls at a time
#   tools/run_parallel.sh sdk   the LiveKit SDK suite (sdk/), plus the two browser
#                               specs that watch the page's call from the LiveKit
#                               server (ui/tests/livekit) - so it has a Playwright
#                               report too
set -uo pipefail
cd "$(dirname "$0")/.."

PROFILE=${1:-all}
LOGS=report/data/logs
mkdir -p "$LOGS" report/data/junit
# Each lane's pytest / Playwright run would rebuild report/index.html as it
# ends (tools/report_hook.py); in parallel that is several writers at once.
# Off here, built once at the end.
export LKQA_NO_REPORT=1
STATUS=$LOGS/status.tsv
: >"$STATUS"
# The sub-makes must not re-run `fresh` and wipe what an earlier wave wrote.
export MAKELEVEL=${MAKELEVEL:-1}
[ "$MAKELEVEL" = "0" ] && export MAKELEVEL=1

lane() { # lane <name> <target>... : targets one after another, one log per lane
  local name=$1 t start r
  shift
  for t in "$@"; do
    start=$SECONDS
    echo "=================== make $t" >>"$LOGS/$name.log"
    make --no-print-directory "$t" >>"$LOGS/$name.log" 2>&1
    r=$?
    printf '%s\t%s\t%s\t%s\n' "$name" "$t" "$r" $((SECONDS - start)) >>"$STATUS"
    printf '  %-10s %-24s %-4s %5ss   log: %s\n' "$name" "$t" "$([ "$r" = 0 ] && echo ok || echo FAIL)" \
      $((SECONDS - start)) "$LOGS/$name.log"
  done
}

wave() { # wave <title> "<lane> <target>..." ... : lanes in parallel, then wait
  local title=$1 spec start=$SECONDS
  shift
  echo "=== wave: $title"
  for spec in "$@"; do
    # shellcheck disable=SC2086 # spec is "<lane> <target>..." on purpose
    lane $spec &
  done
  wait
  echo "    wave done in $((SECONDS - start))s"
}

T0=$SECONDS
case "$PROFILE" in
all)
  wave "1 offline" "check check" "catalog catalog" "judge judge-offline" "lk-offline livekit-offline" "types check-types"
  wave "2 endpoints (no agent)" "api api livekit-contract" "lk-auth livekit-auth"
  # Lanes balanced on measured times (2026-09-28): grounding 15m + phrasing ~7m |
  # conversation 2m + voice 2m + resilience ~5m | browser 10m + interview 16m.
  wave "3 live calls (3 lanes)" \
    "lane-a livekit-grounding livekit-phrasing" \
    "lane-b livekit-conversation livekit-voice livekit-resilience" \
    "lane-c ui-all livekit-interview"
  wave "4 KB run (3 calls at a time)" "kb livekit-kb"
  wave "5 concurrency (3 calls at once)" "conc livekit-concurrency"
  make --no-print-directory oracle DIR=report/data/recordings >"$LOGS/oracle.log" 2>&1 || true
  ;;
sdk)
  wave "1 offline" "lk-offline livekit-offline"
  wave "2 endpoints (no agent)" "lk-contract livekit-contract" "lk-auth livekit-auth"
  wave "3 live calls (3 lanes)" \
    "lane-a livekit-grounding" \
    "lane-b livekit-conversation livekit-voice livekit-resilience livekit-phrasing" \
    "lane-c livekit-interview livekit-browser"
  wave "4 KB run (3 calls at a time)" "kb livekit-kb"
  wave "5 concurrency (3 calls at once)" "conc livekit-concurrency"
  ;;
live)
  # Real agent calls only, each answer judged against resources/kb - no offline
  # checks, no endpoint-only tests. The browser lane runs HEADED (visible).
  # LIVE_PARALLEL calls at a time (default 8, set 2026-09-30): with 7 or more,
  # every step gets its own lane (7 calls at once), then the KB run takes
  # LIVE_PARALLEL at a time. Below 7, the steps share 3 lanes.
  PAR=${LIVE_PARALLEL:-8}
  echo "=== live calls in flight: up to $PAR"
  if [ "$PAR" -ge 7 ]; then
    wave "1 live calls (7 lanes)" \
      "grounding livekit-grounding" "phrasing livekit-phrasing" "interview livekit-interview" \
      "browser ui-live-headed" "conversation livekit-conversation" "voice livekit-voice" \
      "resilience livekit-resilience"
  else
    wave "1 live calls (3 lanes)" \
      "lane-a livekit-grounding livekit-phrasing" \
      "lane-b livekit-conversation livekit-voice livekit-resilience" \
      "lane-c ui-live-headed livekit-interview"
  fi
  export KB_PARALLEL=$PAR
  wave "2 KB run ($PAR calls at a time)" "kb livekit-kb"
  wave "3 concurrency (3 calls at once, by design)" "conc livekit-concurrency"
  make --no-print-directory oracle DIR=report/data/recordings >"$LOGS/oracle.log" 2>&1 || true
  ;;
*)
  echo "usage: $0 all|sdk|live" >&2
  exit 2
  ;;
esac

failed=$(awk -F'\t' '$3 != 0 {print "  " $2 "  (" $1 ", " $4 "s)"}' "$STATUS")
echo "=== finished in $(((SECONDS - T0) / 60))m $(((SECONDS - T0) % 60))s   logs: $LOGS/"
LKQA_NO_REPORT=0 make --no-print-directory report-html 2>&1 | tail -4
# The shareable single file, dated, so each run you send has its own name.
if [ -f report/qa-report.html ]; then
  mkdir -p report/share
  share=report/share/qa-report-$(date +%Y%m%d-%H%M).html
  cp report/qa-report.html "$share"
  echo "  SHARE THIS FILE    $share ($(du -h "$share" | cut -f1)) - self-contained, tokens redacted"
fi
if [ -n "$failed" ]; then
  echo "failed:"
  echo "$failed"
  exit 1
fi
echo "every target passed"
