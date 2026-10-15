#!/bin/bash
# R88 的验证（第 90 轮）。本轮只动 CI 那两步与报告脚本，Swift 侧一行没动 ⇒
# 逐条实跑能跑的，跑不了的**写成有名字的 NOT-RUN**，不许省成"看起来全绿"。
set -u
REPO=/Users/wangziyi/Codex_Project0
LOG=/tmp/r88_verify
SUM=$LOG/summary.log
rm -rf "$LOG"; mkdir -p "$LOG"

step() { echo "=== $1 ==="; }

step "动了哪些非台账文件（本轮应当只有 ci.yml + 两个脚本）"
git -C "$REPO" diff --name-only HEAD | grep -v '^AGENT_\|^CHANGELOG\|^\.scratch' > "$LOG/touched.txt"
cat "$LOG/touched.txt"
echo "TOUCHED_NON_LEDGER=$(wc -l < "$LOG/touched.txt" | tr -d ' ')" >> "$SUM"
if git -C "$REPO" diff --name-only HEAD | grep -q '^ClipboardHistory/Sources/'; then
  echo "PRODUCT_TOUCHED=1" >> "$SUM"
else
  echo "PRODUCT_TOUCHED=0（⇒ 不换装、帧基线按构造不变）" >> "$SUM"
fi

step "脚本自测（python3 -m unittest discover -s scripts/tests）"
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
echo "PY_EXIT=$?" >> "$SUM"
grep -aE "^Ran [0-9]+ tests|^OK$|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUM"
echo >> "$SUM"

step "机制对照（旧形状留孤儿 / 新形状收干净 / 接线 / bash -n）"
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/r88_watchdog_shape.py ) > "$LOG/shape.log" 2>&1
echo "SHAPE_EXIT=$?" >> "$SUM"
grep -aE "^  (CAUGHT|ESCAPED)|^R88 对照" "$LOG/shape.log" | tr '\n' ' ' | sed 's/^/SHAPE=/  ' >> "$SUM"
echo >> "$SUM"

step "变异电池（八刀）"
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r88_watchdog.py ) > "$LOG/battery.log" 2>&1
echo "BATTERY_EXIT=$?" >> "$SUM"
grep -aE "^汇总" "$LOG/battery.log" | sed 's/^/BATTERY=/' >> "$SUM"

step "NOT-RUN（本轮没跑的东西，逐条点名）"
echo "NOT_RUN=swift_build（Swift 侧一行没动，见 PRODUCT_TOUCHED；CI 那一步会自己跑）" >> "$SUM"
echo "NOT_RUN=swift_test_full（同上，801 例由本轮 push 触发的 run 覆盖）" >> "$SUM"
echo "NOT_RUN=motion_floor_gate / capture_gate / frame_baseline（都要求 Swift 产物；本轮零 Swift 改动）" >> "$SUM"
echo "NOT_RUN=runner 上的 set -m 真效果（只有下一次 CI 才知道 —— 那正是本轮要读的那一格）" >> "$SUM"

echo
cat "$SUM"
