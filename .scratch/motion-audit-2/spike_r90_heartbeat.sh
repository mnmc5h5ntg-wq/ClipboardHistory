#!/bin/bash
# R90 的决定性一格：加了 stderr 心跳之后，被看门狗 `kill -9` 收掉的那份日志里**还在不在**。
#
# 为什么必须实测而不是推理：R88 我推理过"started 行会留在日志里"，被 R89 的 CI 读数打脸
# （SIGKILL 会整块带走块缓冲的 stdout）。`emit` 走 `FileHandle.standardError.write` = 直接
# write(2)，理论上不经缓冲 —— 但"理论上"不配给 BACKLOG 122 结案，只有这一支的读数配。
#
# 形状与 CI 那一步一致：`set -m` + 后台跑 + 到点收组 + 收残留孩子的组（R89 那一刀）。
# 用法：bash spike_r90_heartbeat.sh <输出目录> <秒数>
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=${1:-/tmp/r90_hb}
DELAY=${2:-120}
rm -rf "$OUT"; mkdir -p "$OUT/shots"
LOG="$OUT/ui.log"
cd "$REPO/ClipboardHistory" || exit 1

set -m
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS="$OUT/shots" \
  swift test --filter UIInteractionProbeTests > "$LOG" 2>&1 &
pid=$!
( sleep "$DELAY"
  alive=$(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests" 2>/dev/null | wc -l | tr -d ' ' || true)
  echo "${alive:-0}" > "$OUT/runner-alive"
  kill -9 -"$pid" 2>/dev/null || true
  kill -9 "$pid" 2>/dev/null || true ) &
killer=$!
wait "$pid" && status=0 || status=$?
kill "$killer" 2>/dev/null || true
for child in $(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests" 2>/dev/null || true); do
  cpgid=$(ps -o pgid= -p "$child" 2>/dev/null | tr -d ' ' || true)
  if [ -n "$cpgid" ]; then kill -9 -"$cpgid" 2>/dev/null || true; fi
done
sleep 1
orphans=$(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests" 2>/dev/null | wc -l | tr -d ' ' || true)

echo "=== 收完之后（退出码 $status，孤儿 ${orphans:-?}，收掉那一刻 runner 是否活着 $(cat "$OUT/runner-alive" 2>/dev/null || echo 未量到)）"
echo "log_bytes=$(wc -c < "$LOG" | tr -d ' ')"
echo "started=$(grep -c "Test Case '-\\[.*\\]' started\\." "$LOG" 2>/dev/null || echo 0)"
echo "heartbeat=$(grep -c '^PROBE_HEARTBEAT ' "$LOG" 2>/dev/null || echo 0)"
echo "concluded=$(grep -cE "Test Case '-\\[.*\\]' (passed|failed|skipped)" "$LOG" 2>/dev/null || echo 0)"
echo "--- 心跳前 5 行："
grep -a '^PROBE_HEARTBEAT ' "$LOG" 2>/dev/null | head -5
echo "--- 最后一条心跳："
grep -a '^PROBE_HEARTBEAT ' "$LOG" 2>/dev/null | tail -1
