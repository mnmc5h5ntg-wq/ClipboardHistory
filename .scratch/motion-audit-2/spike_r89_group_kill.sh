#!/bin/bash
# R89 的机制测量：R88 那套 `set -m` + `kill -9 -- -$pid` 在 runner 上**没够到** xctest
# （CI run 38825657419 的 `PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑`）。
# 这一支要量的是"为什么没够到"，办法是把三层进程各自的 pid / ppid / pgid 打出来。
#
# 要分的两种解释（都长得像"组杀无效"，处置完全不同）：
#   ① `set -m` 在 GitHub 那种非交互 `bash -e {0}` 里根本没生效 ⇒ 后台任务没自成进程组，
#      `kill -- -$pid` 里的 $pid 不是组号，于是它要么杀错组、要么什么都没杀；
#   ② `set -m` 生效了，但 SwiftPM 自己给 `xctest` 另开了进程组（setpgid/setsid）
#      ⇒ 那个孩子**不在**驱动进程的组里，组杀天然够不到它。
# ① 的修法是换写法（比如显式 `setsid`/自己 setpgid）；② 的修法是**照 pid 树收**
# （pkill -P 逐层，或直接量到 xctest 的 pgid 再杀那个组）。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=${1:-/tmp/r89_group}
DELAY=${2:-90}
rm -rf "$OUT"; mkdir -p "$OUT/shots"
LOG="$OUT/ui.log"
cd "$REPO/ClipboardHistory" || exit 1

tree() {
  ps -eo pid,ppid,pgid,sess,command | grep -E "swift-test|swift build|xctest -XCTest ClipboardHistoryAppTests" | grep -v grep
}

set -m
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS="$OUT/shots" \
  swift test --filter UIInteractionProbeTests > "$LOG" 2>&1 &
pid=$!
echo "驱动 pid=$pid  我自己的 pgid=$(ps -o pgid= -p $$ | tr -d ' ')"
sleep "$DELAY"
echo "=== 收掉之前（pid ppid pgid sess command）==="
tree
# 关键一格：$pid 到底等不等于它的进程组号？不等于就说明 set -m 没生效（解释 ①）
echo "PGID_OF_JOB=$(ps -o pgid= -p "$pid" | tr -d ' ')  PID_OF_JOB=$pid"
kill -9 -"$pid" 2>/dev/null || echo "组杀返回非零（说明这个组号不存在）"
# ↓↓ 与 ci.yml 现在的顺序一致：残留孩子的组由**父壳**在 wait 之后收，不塞进 killer 子壳
for child in $(pgrep -f "xctest -XCTest ClipboardHistoryAppTests" 2>/dev/null || true); do
  cpgid=$(ps -o pgid= -p "$child" 2>/dev/null | tr -d ' ' || true)
  if [ -n "$cpgid" ]; then echo "父壳收残留组 $cpgid（孩子 pid=$child）"; kill -9 -"$cpgid" 2>/dev/null || true; fi
done
sleep 2
echo "=== 组杀之后 ==="
tree || true
echo "=== 父壳收完之后还剩几个（这里必须是 0）==="
LEFT=$(pgrep -f "xctest -XCTest ClipboardHistoryAppTests" | head -1)
if [ -n "${LEFT:-}" ]; then
  LEFTPGID=$(ps -o pgid= -p "$LEFT" | tr -d ' ')
  echo "残留 xctest pid=$LEFT pgid=$LEFTPGID ⇒ 杀整个 $LEFTPGID 组"
  kill -9 -"$LEFTPGID" 2>/dev/null || true
else
  echo "残留=0 ⇒ 组杀其实够到了（那 CI 那一格红的是别的原因）"
fi
sleep 1
echo "=== 最终残留 ==="
pgrep -f "xctest -XCTest ClipboardHistoryAppTests" | wc -l | tr -d ' '
echo "log_bytes=$(wc -c < "$LOG" | tr -d ' ') started=$(grep -c 'Test Case.*started' "$LOG" || true)"
