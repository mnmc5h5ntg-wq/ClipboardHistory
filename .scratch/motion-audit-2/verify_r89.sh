#!/bin/bash
# R89 的验证（第 91 轮）。本轮只动 ci.yml 的看门狗与步骤顺序 ⇒ 能实跑的全跑，跑不了的点名。
set -u
REPO=/Users/wangziyi/Codex_Project0
LOG=/tmp/r89_verify
SUM=$LOG/summary.log
rm -rf "$LOG"; mkdir -p "$LOG"

echo "=== 动了哪些非台账文件 ==="
git -C "$REPO" diff --name-only HEAD | grep -v '^AGENT_\|^CHANGELOG\|^\.scratch' > "$LOG/touched.txt"
cat "$LOG/touched.txt"
echo "TOUCHED_NON_LEDGER=$(wc -l < "$LOG/touched.txt" | tr -d ' ')" >> "$SUM"
if git -C "$REPO" diff --name-only HEAD | grep -q '^ClipboardHistory/Sources/'; then
  echo "PRODUCT_TOUCHED=1" >> "$SUM"
else
  echo "PRODUCT_TOUCHED=0（⇒ 不换装、帧基线按构造不变）" >> "$SUM"
fi

echo "=== 脚本自测 ==="
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
echo "PY_EXIT=$?" >> "$SUM"
grep -aE "^Ran [0-9]+ tests|^OK$|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUM"
echo >> "$SUM"

echo "=== 机制对照（三形状 + 接线 + 顺序）==="
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/r89_watchdog_shape.py ) > "$LOG/shape.log" 2>&1
echo "SHAPE_EXIT=$?" >> "$SUM"
grep -aE "^  (CAUGHT|ESCAPED)|^R89 对照|^接线检查|^步骤顺序" "$LOG/shape.log" | tr '\n' ' ' | sed 's/^/SHAPE=/' >> "$SUM"
echo >> "$SUM"

echo "=== 变异电池（八刀）==="
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r89_watchdog.py ) > "$LOG/battery.log" 2>&1
echo "BATTERY_EXIT=$?" >> "$SUM"
grep -aE "^汇总" "$LOG/battery.log" | sed 's/^/BATTERY=/' >> "$SUM"

echo "=== 真机进程树（不是 bash 假树）：45 秒按 CI 原样收 ==="
( cd "$REPO" && bash .scratch/motion-audit-2/spike_r89_group_kill.sh /tmp/r89_tree 45 ) > "$LOG/tree.log" 2>&1
grep -aE "^PGID_OF_JOB|父壳收残留组|^残留=|最终残留|^log_bytes" "$LOG/tree.log" | tr '\n' ' ' | sed 's/^/TREE=/' >> "$SUM"
echo >> "$SUM"

echo "=== NOT-RUN（逐条点名）==="
echo "NOT_RUN=swift_build / swift_test_full / motion 与 capture 闸门 / frame_baseline（本轮零 Swift 改动；CI 那一步会自己跑）" >> "$SUM"
echo "NOT_RUN=runner 上的真实效果（`set -m` + 残留收杀在无头 macOS runner 上够不够，只有下一次 CI 知道）" >> "$SUM"
echo "NOT_RUN=BACKLOG 122 的每条判据心跳（本轮先修 R88 留下的两处不完整，一次只改一处）" >> "$SUM"

# 脚本自己的退出码必须反映**内容**：上一版最后一条命令是 `cat`，
# 于是电池 1 刀逃掉（BATTERY_EXIT=1）时 verify 仍然 exit 0 —— 后台任务"完成"被读成"全绿"。
FAILS=""
[ "${PY_EXIT:-1}" = "0" ] || FAILS="$FAILS PY_EXIT=$PY_EXIT"
[ "${SHAPE_EXIT:-1}" = "0" ] || FAILS="$FAILS SHAPE_EXIT=$SHAPE_EXIT"
[ "${BATTERY_EXIT:-1}" = "0" ] || FAILS="$FAILS BATTERY_EXIT=$BATTERY_EXIT"
grep -q "R89 形状收干净（残留=0）" "$LOG/shape.log" || FAILS="$FAILS 三形状里 R89 那一臂没收到干净"
grep -qE "^残留=0" "$LOG/tree.log" || FAILS="$FAILS 真机树: 残留不是 0"
grep -q "汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成" "$LOG/battery.log" || FAILS="$FAILS 电池不是 8/8"

echo
cat "$SUM"
if [ -n "$FAILS" ]; then
  echo "VERIFY_FAILED=$FAILS" | tee -a "$SUM"
  exit 1
fi
echo "VERIFY_OK=1" | tee -a "$SUM"
