#!/usr/bin/env bash
# R82 的全量验证：把每一布的**原文读数**收进 .scratch/motion-audit-2/r82_verify_summary.log，
# 台账脚本只许从那份文件里取数（不许手抄）。
set -uo pipefail
REPO=/Users/wangziyi/Codex_Project0
CH=$REPO/ClipboardHistory
OUT=$REPO/.scratch/motion-audit-2
LOG=/tmp/r82
SHOTS=$LOG/shots
MOTION=$LOG/motion
SUMMARY=$OUT/r82_verify_summary.log
mkdir -p "$LOG" "$SHOTS" "$MOTION"
unset SDKROOT
export PYTHONUTF8=1
: > "$SUMMARY"

step() { echo; echo "########## $* ##########"; }

step "build --build-tests（告警必须为 0）"
( cd "$CH" && swift build --build-tests ) > "$LOG/build.log" 2>&1
BUILD_EXIT=$?
grep -c "warning:" "$LOG/build.log" | sed 's/^/BUILD_WARNINGS=/' >> "$SUMMARY"
echo "BUILD_EXIT=$BUILD_EXIT" >> "$SUMMARY"
tail -3 "$LOG/build.log"

step "全量 swift test"
( cd "$CH" && swift test ) > "$LOG/full.log" 2>&1
FULL_EXIT=$?
TOTAL=$(grep -E "^Executed [0-9]+ tests" "$LOG/full.log" | tail -1 | sed -E 's/^Executed ([0-9]+) tests.*/\1/')
FAIL=$(grep -E "^Executed [0-9]+ tests" "$LOG/full.log" | tail -1 | sed -E 's/.*with ([0-9]+) failure.*/\1/')
SKIP=$(grep -c "^Test Case.*' skipped" "$LOG/full.log")
echo "FULL_TEST=${TOTAL} tests / ${FAIL} failures (exit ${FULL_EXIT})" >> "$SUMMARY"
echo "SKIPPED=${SKIP}" >> "$SUMMARY"
tail -2 "$LOG/full.log"

step "动效那一卷（MotionFilmstripTests 全类）"
( cd "$CH" && CLIPBOARD_HISTORY_UI_MOTION=1 CLIPBOARD_HISTORY_MOTION_OUT="$MOTION" \
    swift test --filter MotionFilmstripTests ) > "$LOG/motion.log" 2>&1
MOTION_EXIT=$?
grep -E "^MOTION_SHIMMER|^LOOP_" "$LOG/motion.log" | head -1 | sed 's/^/SHIM_READING=/' >> "$SUMMARY"
grep -E "^MOTION_SHIMMER_WITNESS 等节拍" "$LOG/motion.log" | head -1 | sed 's/^/RATE_WITNESS_READING=/' >> "$SUMMARY"
grep -E "^MOTION_SHIMMER_WITNESS 粗节拍" "$LOG/motion.log" | head -1 | sed 's/^/COARSE_WITNESS_READING=/' >> "$SUMMARY"
grep -E "^LOOP_WITNESS_MIRROR" "$LOG/motion.log" | head -1 | sed 's/^/MIRROR_READING=/' >> "$SUMMARY"
echo "MOTION_TEST_EXIT=$MOTION_EXIT" >> "$SUMMARY"

step "动效覆盖地板闸门（motion_floor_gate.py）"
( cd "$REPO" && python3 scripts/motion_floor_gate.py "$LOG/motion.log" \
    --expectations scripts/motion_floor_expectations.json ) > "$LOG/motion_gate.log" 2>&1
GATE_EXIT=$?
grep -E "^MOTION_FLOOR_FACTS|^MOTION_FLOOR_SUITE_RED|^MOTION_FLOOR_REDS" "$LOG/motion_gate.log" \
  | tr '\n' ' ' | sed 's/[[:space:]]*$//' | sed 's/^/MOTION_FLOOR=/' >> "$SUMMARY"
echo "MOTION_GATE_EXIT=$GATE_EXIT" >> "$SUMMARY"
cat "$LOG/motion_gate.log"

step "捕获那一卷（UICaptureTests）"
( cd "$CH" && CLIPBOARD_HISTORY_UI_SHOTS="$SHOTS" swift test --filter UICaptureTests ) \
    > "$LOG/frames-raw.log" 2>&1
CAP_EXIT=$?
sed '/colorspace/d' "$LOG/frames-raw.log" > "$LOG/frames.log"
echo "CAPTURE_TEST_EXIT=$CAP_EXIT" >> "$SUMMARY"

step "捕获闸门（ci_capture_gate.py --readings）"
( cd "$REPO" && python3 scripts/ci_capture_gate.py "$LOG/frames.log" --min-passed 15 \
    --readings "$SHOTS/capture-readings.log" ) > "$LOG/capture_gate.log" 2>&1
CG_EXIT=$?
grep -E "^CAPTURE_GATE_RESULT" "$LOG/capture_gate.log" | head -1 \
  | sed 's/^/CAPTURE_GATE=/' >> "$SUMMARY"
echo "CAPTURE_GATE_EXIT=$CG_EXIT" >> "$SUMMARY"
tail -4 "$LOG/capture_gate.log"

step "帧基线（frame_baseline.py check --against working）"
( cd "$REPO" && python3 scripts/frame_baseline.py check "$SHOTS" --against working ) \
    > "$LOG/baseline.log" 2>&1
FB_EXIT=$?
grep -E "^COMPARED=|^FRAME_BASELINE" "$LOG/baseline.log" | tail -1 | sed 's/^/FRAME_BASELINE=/' >> "$SUMMARY"
echo "FRAME_BASELINE_EXIT=$FB_EXIT" >> "$SUMMARY"
tail -3 "$LOG/baseline.log"

step "脚本自测（python3 -m unittest discover -s scripts/tests）"
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
PY_EXIT=$?
grep -E "^Ran [0-9]+ tests|^OK|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUMMARY"
echo "PY_EXIT=$PY_EXIT" >> "$SUMMARY"
tail -3 "$LOG/py.log"

echo
echo "=== 汇总（写进 $SUMMARY）==="
cat "$SUMMARY"
