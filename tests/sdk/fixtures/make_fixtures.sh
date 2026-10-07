#!/usr/bin/env bash
# Regenerates the caller WAVs the voice tests publish. macOS only (`say`), and
# only needed when livekitSdk.spokenQuestion changes - the WAVs are committed so
# the suite itself runs anywhere.
#
# 48 kHz, mono, 16-bit PCM: the format the SDK's AudioSource is created with,
# so the test pushes frames without resampling.
set -euo pipefail
cd "$(dirname "$0")"
CONFIG=../../../config/testbed.config.json
q=$(python3 -c "import json;print(json.load(open('$CONFIG'))['livekitSdk']['spokenQuestion']['text'])")
b=$(python3 -c "import json;print(json.load(open('$CONFIG'))['livekitSdk']['spokenQuestion']['bargeInText'])")
say -v Samantha -o fan-valve-pressure.wav --file-format=WAVE --data-format=LEI16@48000 --channels=1 "$q"
say -v Samantha -o barge-in.wav --file-format=WAVE --data-format=LEI16@48000 --channels=1 "$b"
ls -la *.wav
