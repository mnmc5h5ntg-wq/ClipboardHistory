#!/bin/bash
# R88 spike（只读产品代码，不改仓库）：BACKLOG 93 剩下的那一格 ——
# `swift test` 被 SIGKILL 之后，"日志里一条用例都没开始"到底是
#   ① 进程真的没开始跑用例，还是
#   ② 用例其实在跑、而 stdout 被块缓冲整块带走
# 这两个成因，本机能不能分开？
#
# 为什么现在要重跑：R86 的 spike 只做过**一次**（50 秒、13 行 started 留住了），
# 一次成功证明的是"能留住"，不是"每次都留得住"（台账 U-184）。
# 这一版把"留住没有"当成**每次都要量的读数**，跑三个不同的收掉时刻，
# 并且同时读第二条通道（帧目录里有没有文件、mtime 在不在收掉之前）。
#
# 两条通道的分工是这个 spike 要回答的真正问题：
#   · stdout 的 started 行 ⇒ 能点名"挂在哪一条"，但可能整块丢；
#   · 帧文件 ⇒ 由探针自己写盘，SIGKILL 之后仍在盘上。
#     但它只覆盖 11 条用例里的 3 条（focus-chain / reveal-before / reveal-after），
#     所以"有帧"能证 ① 假，"没帧"证不了任何事 —— 这是单向证人，不许当成双向。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=${1:-/tmp/r88_spike}
rm -rf "$OUT"; mkdir -p "$OUT/shots"
cd "$REPO/ClipboardHistory" || exit 1

for DELAY in 40 90 150; do
  LOG="$OUT/ui-$DELAY.log"
  SHOTS="$OUT/shots/$DELAY"
  mkdir -p "$SHOTS"
  /usr/bin/time -p env -u SDKROOT \
    CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS="$SHOTS" \
    swift test --filter UIInteractionProbeTests > "$LOG" 2>&1 &
  pid=$!
  sleep "$DELAY"
  START_BEFORE=$(ls -1 "$SHOTS" 2>/dev/null | wc -l | tr -d ' ')
  kill -9 "$pid" 2>/dev/null
  wait "$pid" 2>/dev/null; status=$?
  # `wait` 之后再看一次：收掉的那一瞬间有没有新帧落盘
  sleep 1
  START_AFTER=$(ls -1 "$SHOTS" 2>/dev/null | wc -l | tr -d ' ')
  echo "SPIKE delay=${DELAY}s exit=${status} log_bytes=$(wc -c < "$LOG" | tr -d ' ') " \
       "started=$(grep -c 'Test Case.*started' "$LOG" 2>/dev/null || true) " \
       "concluded=$(grep -cE 'Test Case.*(passed|failed|skipped)' "$LOG" 2>/dev/null || true) " \
       "帧_收掉前=${START_BEFORE} 帧_收掉后=${START_AFTER} " \
       "探针独有帧=$(ls -1 "$SHOTS" 2>/dev/null | grep -cE '^(focus-after-tab|reveal-(before|after))' || true)"
done
echo "--- 报告脚本对这三份日志各说什么 ---"
for DELAY in 40 90 150; do
  echo -n "delay=${DELAY}s ⇒ "
  python3 "$REPO/scripts/ui_probe_report.py" "$OUT/ui-$DELAY.log" 2>&1 | head -3 | tr '\n' ' '
  echo
done
