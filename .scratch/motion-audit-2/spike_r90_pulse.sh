#!/bin/bash
# R90 的决定性一格：心跳换成**文件通道**之后，进程还活着的时候行在不在盘上。
#
# 上一版（stderr）的读数：40/60/80/100/120 秒 `heartbeat=0`，而 `sample` 证明进程已经跑进
# 第二条用例的方法体 ⇒ "stderr 活得过 kill"这句是错的（孩子写到的是驱动的管道）。
# 这一版要证的不是"它活得过 kill"（那由 R88 的管道结论反推），而是**它落盘了**：
# 只要行在活着时就在盘上，SIGKILL 之后它当然还在。
#
# 用法：bash spike_r90_pulse.sh <秒数>
set -u
REPO=/Users/wangziyi/Codex_Project0
DELAY=${1:-90}
OUT=/tmp/r90_pulse
rm -rf "$OUT"; mkdir -p "$OUT/shots"
LOG="$OUT/ui.log"
PULSE="$OUT/probe-pulse.log"
cd "$REPO/ClipboardHistory" || exit 1

set -m
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 \
    CLIPBOARD_HISTORY_UI_SHOTS="$OUT/shots" \
    CLIPBOARD_HISTORY_PROBE_PULSE="$OUT" \
  swift test --filter UIInteractionProbeTests > "$LOG" 2>&1 &
pid=$!
i=0
while [ "$i" -lt "$DELAY" ]; do
  sleep 15; i=$((i + 15))
  printf 'SAMPLE t=%03ds ui_bytes=%s pulse_lines=%s pulse_bytes=%s xctest=%s\n' \
    "$i" "$(wc -c < "$LOG" | tr -d ' ')" \
    "$(grep -ac '^PROBE_PULSE ' "$PULSE" 2>/dev/null || echo 0)" \
    "$(wc -c < "$PULSE" 2>/dev/null | tr -d ' ' || echo 0)" \
    "$(pgrep -f 'xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests' >/dev/null 2>&1 && echo alive || echo gone)"
  [ "$(pgrep -f 'xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests' >/dev/null 2>&1 && echo alive)" = "gone" ] && break
done
alive=$(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests" 2>/dev/null | wc -l | tr -d ' ')
kill -9 -"$pid" 2>/dev/null || true
kill -9 "$pid" 2>/dev/null || true
for child in $(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests" 2>/dev/null || true); do
  cpgid=$(ps -o pgid= -p "$child" 2>/dev/null | tr -d ' ' || true)
  [ -n "$cpgid" ] && kill -9 -"$cpgid" 2>/dev/null || true
done
wait "$pid" 2>/dev/null; status=$?
sleep 1
echo "=== 收完之后 exit=$status 收掉前 xctest 数=$alive"
echo "ui_bytes=$(wc -c < "$LOG" | tr -d ' ') pulse_lines=$(grep -ac '^PROBE_PULSE ' "$PULSE" 2>/dev/null || echo 0)"
echo "--- 心跳文件内容："
cat "$PULSE" 2>/dev/null
