#!/bin/bash
# R88 spike 第二版：**照 CI 的原样**收进程，量"杀父留子"到底发不发生。
#
# 为什么还要再跑一版：第一版在 `swift test` 前面套了 `/usr/bin/time -p`，
# 于是 `$!` 拿到的是 time 的 PID ⇒ 它只证明了"杀祖先会留下活着的 runner"。
# CI 那一行是 `swift test … > /tmp/ui.log 2>&1 & pid=$!; kill -9 $pid`，
# `$!` 是 `swift` 驱动进程（它再生 `swift-test`，`swift-test` 再生 `xctest`）
# —— 同一族，但那是**另一次测量**，不能靠第一版顶替。
#
# 这一版要回答的就一句：CI 的看门狗收掉 `swift` 之后，
#   ① `swift-test` / `xctest` 还活着吗？（活着 ⇒ "一条用例都没开始"是假话）
#   ② 日志里有 started 行吗？（R86 的 spike 说有 13 行，本轮第一版说 0 行 —— 那个差本身要记账）
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=${1:-/tmp/r88_ci_shape}
DELAY=${2:-120}
rm -rf "$OUT"; mkdir -p "$OUT/shots"
LOG="$OUT/ui.log"
cd "$REPO/ClipboardHistory" || exit 1

env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS="$OUT/shots" \
  swift test --filter UIInteractionProbeTests > "$LOG" 2>&1 &
pid=$!
echo "驱动进程 pid=$pid，将在 ${DELAY}s 后按 CI 的方式 kill -9 它本身"
sleep "$DELAY"
echo "=== 收掉之前，这一族里有谁 ==="
ps -eo pid,ppid,etime,command | grep -E "^[[:space:]]*[0-9]+" | grep -E "swift| xctest" | grep -v grep | head -10
kill -9 "$pid" 2>/dev/null
sleep 3
echo "=== 收掉 3 秒之后 ==="
ps -eo pid,ppid,etime,command | grep -E "^[[:space:]]*[0-9]+" | grep -E "swift-test| xctest" | grep -v grep | head -10
echo "=== 日志 ==="
echo "exit_of_kill_target=137(约定) log_bytes=$(wc -c < "$LOG" | tr -d ' ') " \
     "started=$(grep -c 'Test Case.*started' "$LOG" 2>/dev/null || true) " \
     "concluded=$(grep -cE 'Test Case.*(passed|failed|skipped)' "$LOG" 2>/dev/null || true) " \
     "帧=$(ls -1 "$OUT/shots" 2>/dev/null | wc -l | tr -d ' ')"
python3 "$REPO/scripts/ui_probe_report.py" "$LOG" 2>&1 | head -4
echo "=== 清理：把还活着的子进程收干净（这些是本轮 spike 自己起的） ==="
for p in $(ps -eo pid,command | grep -E "swift-test --filter UIInteractionProbeTests|xctest -XCTest ClipboardHistoryAppTests" | grep -v grep | awk '{print $1}'); do
  echo "kill $p"; kill -9 "$p" 2>/dev/null
done
sleep 1
ps -eo pid,command | grep -E "swift-test|xctest -XCTest Clipboard" | grep -v grep | head -3
echo "(上面为空 = 清干净)"
