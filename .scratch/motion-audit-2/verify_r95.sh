#!/bin/bash
# R95 的验证电池（内容驱动，不驱动退出码）。
# 沿用 R92 立的两条规矩：① 每条先写变量再 echo（`echo "X=$?"` 之前插赋值会把 $? 吃掉）；
# ② 摘要里任何一格没打出「KEY=数字」就计入 MISSING —— "0 个缺陷"比红更坏。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=$REPO/.scratch/motion-audit-2/r95_verify.log
: > "$OUT"
say() { printf '%s\n' "$*" >> "$OUT"; }

cd "$REPO/ClipboardHistory" || exit 1

say "== 1) 构建（必须 0 告警）"
env -u SDKROOT swift build --build-tests > /tmp/r95_v_build.log 2>&1
BUILD_EXIT=$?
BUILD_WARN=$(grep -c "warning:" /tmp/r95_v_build.log)
say "BUILD_EXIT=$BUILD_EXIT BUILD_WARNING_LINES=$BUILD_WARN"

say "== 2) 全量 swift test"
env -u SDKROOT swift test > /tmp/r95_v_test2.log 2>&1
TEST_EXIT=$?
TEST_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r95_v_test2.log | tail -1 | sed 's/^[ \t]*//')
say "TEST_EXIT=$TEST_EXIT 最后一行汇总: $TEST_SUMMARY"

say "== 3) 在屏那一卷（本机，带 CLIPBOARD_HISTORY_UI_INTERACTION=1）"
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r95_v_probe \
  CLIPBOARD_HISTORY_PROBE_PULSE=/tmp \
  swift test --filter UIInteractionProbeTests > /tmp/r95_v_probe2.log 2>&1
PROBE_EXIT=$?
PROBE_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r95_v_probe2.log | tail -1 | sed 's/^[ \t]*//')
say "PROBE_EXIT=$PROBE_EXIT 汇总: $PROBE_SUMMARY"

say "== 4) 帧基线（本轮改了产品 ⇒ 先确认新帧与 working 名单对得上）"
cd "$REPO" || exit 1
PYTHONUTF8=1 python3 scripts/frame_baseline.py check /tmp/r95_shots --against working \
  --allow-missing content-wide-1100x800-light.png --allow-missing content-wide-1100x800-dark.png \
  > /tmp/r95_v_frames.log 2>&1
FRAMES_EXIT=$?
say "FRAMES_EXIT=$FRAMES_EXIT $(grep -E '^FRAME_BASELINE_' /tmp/r95_v_frames.log | tr '\n' ' ')"

say "== 5) 脚本电池"
if [ "${SKIP_PY:-0}" = "1" ]; then
  PY_EXIT=0
  say "PY_EXIT=0 SKIPPED=1（pass-1 不跑脚本电池：新守卫在台账写盘前必然红）"
else
  PYTHONUTF8=1 python3 -m unittest discover -s scripts/tests > /tmp/r95_v_py.log 2>&1
  PY_EXIT=$?
  say "PY_EXIT=$PY_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r95_v_py.log | tr '\n' ' ')"
fi

say "== 6) 三张变异表（本轮：节奏四刀 + 上一轮欠的两张 Python 表）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r95_rhythm.py > /tmp/r95_v_mut_rhythm.log 2>&1
MUT_RHYTHM_EXIT=$?
PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r94_order.py > /tmp/r95_v_mut_order.log 2>&1
MUT_ORDER_EXIT=$?
PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r95_triage.py > /tmp/r95_v_mut_triage.log 2>&1
MUT_TRIAGE_EXIT=$?
MUTATE="节奏:$(grep -E '^MUTATE_TABLE' /tmp/r95_v_mut_rhythm.log) 序:$(grep -E '^MUTATE_TABLE' /tmp/r95_v_mut_order.log) 分诊:$(grep -E '^MUTATE_TABLE' /tmp/r95_v_mut_triage.log)"
# MUT_EXIT 取"三张里有没有非零"，别只取最后一张（那会把前两张的失败吞成 0）
MUT_EXIT=0
for e in $MUT_RHYTHM_EXIT $MUT_ORDER_EXIT $MUT_TRIAGE_EXIT; do
  [ "$e" -eq 0 ] || MUT_EXIT=1
done
say "MUT_EXIT=$MUT_EXIT（节奏=$MUT_RHYTHM_EXIT 序=$MUT_ORDER_EXIT 分诊=$MUT_TRIAGE_EXIT）$MUTATE"

say "== 7) 台账编号守卫"
PYTHONUTF8=1 python3 -m unittest scripts.tests.test_ledger_ids > /tmp/r95_v_ledger.log 2>&1
LEDGER_EXIT=$?
say "LEDGER_EXIT=$LEDGER_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r95_v_ledger.log | tr '\n' ' ')"

say "== 8) 看图仪器（设置「快捷键」逐元素，尺腿不判产品）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/r95_shortcuts_visual.py /tmp/r95_shots \
  > .scratch/motion-audit-2/r95_shortcuts_readings.log 2>&1
VIS_EXIT=$?
say "VIS_EXIT=$VIS_EXIT 卡片=$(grep -c '卡片#' .scratch/motion-audit-2/r95_shortcuts_readings.log) 控件=$(grep -c '控件' .scratch/motion-audit-2/r95_shortcuts_readings.log) 侧栏不判=$(grep -c 'SIDEBAR_BLIND' .scratch/motion-audit-2/r95_shortcuts_readings.log)"

say "== 9) 摘要缺值算红"
MISSING=0
for key in BUILD_EXIT TEST_EXIT PROBE_EXIT FRAMES_EXIT PY_EXIT MUT_EXIT LEDGER_EXIT VIS_EXIT; do
  line=$(grep -E "^$key=" "$OUT" | tail -1)
  if ! printf '%s' "$line" | grep -qE '^[A-Z_]+=[0-9]+'; then
    MISSING=$((MISSING+1)); printf '摘要缺值：%s\n' "$line" >> "$OUT"
  fi
done
say "SUMMARY_MISSING=$MISSING"

if [ "$BUILD_EXIT" -eq 0 ] && [ "$BUILD_WARN" -eq 0 ] && [ "$TEST_EXIT" -eq 0 ] \
   && [ "$PROBE_EXIT" -eq 0 ] && [ "$FRAMES_EXIT" -eq 0 ] && [ "$PY_EXIT" -eq 0 ] \
   && [ "$MUT_EXIT" -eq 0 ] && [ "$LEDGER_EXIT" -eq 0 ] && [ "$VIS_EXIT" -eq 0 ] \
   && [ "$MISSING" -eq 0 ]; then
  say "VERIFY_OK=1"
else
  say "VERIFY_OK=0"
fi
