#!/usr/bin/env bash
# R83 的全量验证：每一布的**原文读数**收进 .scratch/motion-audit-2/r83_verify_summary.log。
# 与 verify_r82.sh 同一套步骤，两处修好：
#   * FULL_TEST 改成直接读总汇总行（R82 那版用 `^Executed` 匹配不到带制表符的行，只能事后手补）；
#   * SKIPPED 也从同一行读，不再用"数 skipped 行"（那种数法会被撕裂的行骗）。
set -uo pipefail
REPO=/Users/wangziyi/Codex_Project0
CH=$REPO/ClipboardHistory
OUT=$REPO/.scratch/motion-audit-2
LOG=/tmp/r83
SHOTS=$LOG/shots
MOTION=$LOG/motion
SUMMARY=$OUT/r83_verify_summary.log
mkdir -p "$LOG" "$SHOTS" "$MOTION"
unset SDKROOT
export PYTHONUTF8=1
: > "$SUMMARY"

step() { echo; echo "########## $* ##########"; }

step "build --build-tests（告警必须为 0）"
( cd "$CH" && swift build --build-tests ) > "$LOG/build.log" 2>&1
echo "BUILD_WARNINGS=$(grep -c 'warning:' "$LOG/build.log")" >> "$SUMMARY"
echo "BUILD_EXIT=$?" >> "$SUMMARY"
tail -2 "$LOG/build.log"

step "全量 swift test"
( cd "$CH" && swift test ) > "$LOG/full.log" 2>&1
FULL_EXIT=$?
TOTAL=$(grep -aoE "Executed [0-9]+ tests, with [0-9]+ tests? skipped and [0-9]+ failures" "$LOG/full.log" | tail -1 | sed -E 's/Executed ([0-9]+) tests.*/\1/')
SKIPPED=$(grep -aoE "Executed [0-9]+ tests, with [0-9]+ tests? skipped and [0-9]+ failures" "$LOG/full.log" | tail -1 | sed -E 's/.*with ([0-9]+) tests? skipped.*/\1/')
FAILURES=$(grep -aoE "Executed [0-9]+ tests, with [0-9]+ tests? skipped and [0-9]+ failures" "$LOG/full.log" | tail -1 | sed -E 's/.*and ([0-9]+) failures.*/\1/')
echo "FULL_TEST=${TOTAL} tests / ${FAILURES} failures（${SKIPPED} skipped，swift test exit ${FULL_EXIT}）" >> "$SUMMARY"
echo "SKIPPED=${SKIPPED}" >> "$SUMMARY"
tail -2 "$LOG/full.log"

step "动效那一卷（MotionFilmstripTests 全类）"
( cd "$CH" && CLIPBOARD_HISTORY_UI_MOTION=1 CLIPBOARD_HISTORY_MOTION_OUT="$MOTION" \
    swift test --filter MotionFilmstripTests ) > "$LOG/motion.log" 2>&1
echo "MOTION_TEST_EXIT=$?" >> "$SUMMARY"
grep -aE "^MOTION_SHIMMER 扫" "$LOG/motion.log" | head -1 | sed 's/^/SHIM_READING=/' >> "$SUMMARY"
grep -aE "^MOTION_SHIMMER_FILM" "$LOG/motion.log" | head -1 | sed 's/^/FILM_PREMISE_READING=/' >> "$SUMMARY"
grep -aE "^MOTION_SHIMMER_WITNESS 等节拍" "$LOG/motion.log" | head -1 | sed 's/^/RATE_WITNESS_READING=/' >> "$SUMMARY"
grep -aE "^MOTION_SHIMMER_WITNESS 粗节拍" "$LOG/motion.log" | head -1 | sed 's/^/COARSE_WITNESS_READING=/' >> "$SUMMARY"
grep -aE "^LOOP_WITNESS_MIRROR" "$LOG/motion.log" | head -1 | sed 's/^/MIRROR_READING=/' >> "$SUMMARY"
grep -aE "^MOTION_NOT_RUN=loop-clock" "$LOG/motion.log" | head -1 | sed 's/^/LOCAL_LOOP_NOT_RUN=/' >> "$SUMMARY"

step "动效覆盖地板闸门（motion_floor_gate.py）"
( cd "$REPO" && python3 scripts/motion_floor_gate.py "$LOG/motion.log" \
    --expectations scripts/motion_floor_expectations.json ) > "$LOG/motion_gate.log" 2>&1
echo "MOTION_GATE_EXIT=$?" >> "$SUMMARY"
grep -aE "^MOTION_FLOOR_FACTS|^MOTION_FLOOR_REDS" "$LOG/motion_gate.log" | tr '\n' ' ' \
    | sed 's/[[:space:]]*$//' | sed 's/^/MOTION_FLOOR=/' >> "$SUMMARY"
cat "$LOG/motion_gate.log"

step "捕获那一卷（UICaptureTests）"
( cd "$CH" && CLIPBOARD_HISTORY_UI_SHOTS="$SHOTS" swift test --filter UICaptureTests ) \
    > "$LOG/frames-raw.log" 2>&1
echo "CAPTURE_TEST_EXIT=$?" >> "$SUMMARY"
sed '/colorspace/d' "$LOG/frames-raw.log" > "$LOG/frames.log"

step "捕获闸门（ci_capture_gate.py --readings）"
( cd "$REPO" && python3 scripts/ci_capture_gate.py "$LOG/frames.log" --min-passed 15 \
    --readings "$SHOTS/capture-readings.log" ) > "$LOG/capture_gate.log" 2>&1
echo "CAPTURE_GATE_EXIT=$?" >> "$SUMMARY"
grep -aE "^CAPTURE_GATE_RESULT" "$LOG/capture_gate.log" | head -1 | sed 's/^/CAPTURE_GATE=/' >> "$SUMMARY"
tail -3 "$LOG/capture_gate.log"

step "帧基线（frame_baseline.py check --against working）"
( cd "$REPO" && python3 scripts/frame_baseline.py check "$SHOTS" --against working ) \
    > "$LOG/baseline.log" 2>&1
echo "FRAME_BASELINE_EXIT=$?" >> "$SUMMARY"
grep -aE "^FRAME_BASELINE_" "$LOG/baseline.log" | tr '\n' ' ' | sed 's/[[:space:]]*$//' \
    | sed 's/^/FRAME_BASELINE=/' >> "$SUMMARY"; echo >> "$SUMMARY"
tail -3 "$LOG/baseline.log"

step "脚本自测（python3 -m unittest discover -s scripts/tests）"
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
echo "PY_EXIT=$?" >> "$SUMMARY"
grep -aE "^Ran [0-9]+ tests|^OK|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUMMARY"; echo >> "$SUMMARY"
tail -3 "$LOG/py.log"

echo
echo "=== 汇总（$SUMMARY）==="
cat "$SUMMARY"
