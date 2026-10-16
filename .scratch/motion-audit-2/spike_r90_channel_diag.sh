#!/bin/bash
# R90 的分诊：`heartbeat=0` 有两种成因，处置完全相反，只能靠"跑的过程中取样"分开。
#
#   ① 还没写：120 秒过去，第一条用例的 setUpWithError 根本没跑到（那 93 的答案就变成
#      "卡在 xctest 启动/第一条 setUp 之前"，心跳设计要重做）；
#   ② 写了但没落盘：SwiftPM 的驱动把孩子的 stdout/stderr **接进自己的管道**再转发，
#      于是 `write(2)` 虽然无缓冲，落到的却是驱动的管道，驱动被 SIGKILL ⇒ 整块丢。
#      那意味着"stderr 一定活得过 kill"这句前提是**错的**，122 要换成文件通道。
#
# 办法：不杀进程，跑的过程中每 20 秒取一次样（字节数 + 心跳数），最后再取一次。
# ①与②在这张表里长得不一样：② 会在"进程还活着"的时候就已经有心跳行落盘。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=${1:-/tmp/r90_diag}
rm -rf "$OUT"; mkdir -p "$OUT/shots"
LOG="$OUT/ui.log"
cd "$REPO/ClipboardHistory" || exit 1

env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS="$OUT/shots" \
  swift test --filter UIInteractionProbeTests > "$LOG" 2>&1 &
pid=$!
for i in 1 2 3 4 5 6; do
  sleep 20
  alive=$(pgrep -P "$pid" >/dev/null 2>&1 && echo 1 || echo 0)
  xalive=$(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests" >/dev/null 2>&1 && echo 1 || echo 0)
  printf 'SAMPLE t=%03ds bytes=%s heartbeat=%s started=%s xctest_alive=%s\n' \
    "$((i * 20))" "$(wc -c < "$LOG" | tr -d ' ')" \
    "$(grep -ac '^PROBE_HEARTBEAT ' "$LOG" 2>/dev/null || echo 0)" \
    "$(grep -ac "Test Case '-\[.*\]' started\." "$LOG" 2>/dev/null || echo 0)" "$xalive"
done
wait "$pid" && status=0 || status=$?
printf 'FINAL exit=%s bytes=%s heartbeat=%s started=%s concluded=%s\n' "$status" \
  "$(wc -c < "$LOG" | tr -d ' ')" \
  "$(grep -ac '^PROBE_HEARTBEAT ' "$LOG" 2>/dev/null || echo 0)" \
  "$(grep -ac "Test Case '-\[.*\]' started\." "$LOG" 2>/dev/null || echo 0)" \
  "$(grep -acE "Test Case '-\[.*\]' (passed|failed|skipped)" "$LOG" 2>/dev/null || echo 0)"
echo "--- 心跳行（最多 12 条）："
grep -a '^PROBE_HEARTBEAT ' "$LOG" 2>/dev/null | head -12
