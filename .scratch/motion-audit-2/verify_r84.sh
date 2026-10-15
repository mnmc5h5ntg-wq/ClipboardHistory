#!/usr/bin/env bash
# R84 的全量验证：每一布的**原文读数**收进 .scratch/motion-audit-2/r84_verify_summary.log。
# 与 verify_r83.sh 同一套步骤，两处跟着本轮改：
#   * 多收四行位置判据的原文读数（CONTROL / BAND / BAND_WITNESS / BAND_TRUTH_TABLE）；
#   * 自评曲线也在本脚本里跑，且每条 `tr '\n' ' '` 之后都补一个换行
#     （R83 那版把 `ADDED=0PY_EXIT=0` 缝成一行、又吞掉了 `CURVE=`，两处都是事后手补的）。
set -uo pipefail
REPO=/Users/wangziyi/Codex_Project0
CH=$REPO/ClipboardHistory
OUT=$REPO/.scratch/motion-audit-2
LOG=/tmp/r84
SHOTS=$LOG/shots
MOTION=$LOG/motion
SUMMARY=$OUT/r84_verify_summary.log
mkdir -p "$LOG" "$SHOTS" "$MOTION"
unset SDKROOT
export PYTHONUTF8=1
: > "$SUMMARY"

step() { echo; echo "########## $* ##########"; }

step "build --build-tests（告警必须为 0）"
( cd "$CH" && swift build --build-tests ) > "$LOG/build.log" 2>&1
BUILD_EXIT=$?
echo "BUILD_WARNINGS=$(grep -c 'warning:' "$LOG/build.log") BUILD_EXIT=$BUILD_EXIT" >> "$SUMMARY"
tail -2 "$LOG/build.log"

step "全量 swift test"
( cd "$CH" && swift test ) > "$LOG/full.log" 2>&1
FULL_EXIT=$?
LINE=$(grep -aoE "Executed [0-9]+ tests, with [0-9]+ tests? skipped and [0-9]+ failures" "$LOG/full.log" | tail -1)
TOTAL=$(echo "$LINE" | sed -E 's/Executed ([0-9]+) tests.*/\1/')
SKIPPED=$(echo "$LINE" | sed -E 's/.*with ([0-9]+) tests? skipped.*/\1/')
FAILURES=$(echo "$LINE" | sed -E 's/.*and ([0-9]+) failures.*/\1/')
echo "FULL_TEST=${TOTAL} tests / ${FAILURES} failures（${SKIPPED} skipped，swift test exit ${FULL_EXIT}）" >> "$SUMMARY"
tail -2 "$LOG/full.log"

step "动效那一卷（MotionFilmstripTests 全类）"
( cd "$CH" && CLIPBOARD_HISTORY_UI_MOTION=1 CLIPBOARD_HISTORY_MOTION_OUT="$MOTION" \
    swift test --filter MotionFilmstripTests ) > "$LOG/motion.log" 2>&1
MOTION_TEST_EXIT=$?
echo "MOTION_TEST_EXIT=$MOTION_TEST_EXIT" >> "$SUMMARY"
for pat in "^MOTION_SHIMMER 扫" "^MOTION_SHIMMER_FILM" "^MOTION_SHIMMER_WITNESS 等节拍" \
           "^MOTION_SHIMMER_WITNESS 粗节拍" "^MOTION_SHIMMER_BAND_CONTROL" "^MOTION_SHIMMER_BAND " \
           "^MOTION_SHIMMER_BAND_WITNESS" "^BAND_TRUTH_TABLE" "^LOOP_WITNESS_MIRROR" \
           "^MOTION_NOT_RUN=loop-clock" "^MOTION_SHIMMER_BAND_NOT_JUDGED"; do
    hit=$(grep -aE "$pat" "$LOG/motion.log" | head -1)
    [ -n "$hit" ] && echo "READ ${pat%% *} :: $hit" >> "$SUMMARY"
done

# 与 CI 那一步**同一个通道处理**：本机 `swift test` 会成块丢 stdout（R64 记过、R84 现场又踩一次：
# 闸门读到 `judged=None/None` 而测试其实全过）。CI 在跑闸门之前会把文件通道并进去
# （`.github/workflows/ci.yml` 里 `MOTION_CHANNEL_UNIONED=1` 那段），本地不并就等于
# 用一条与 CI 不同的通道判同一件事 ⇒ 假红只出现在我自己的验证脚本里。
if [ -s "$MOTION/motion-readings.log" ]; then
    FROM_STDOUT=$(grep -ac '^MOTION_' "$LOG/motion.log" || true)
    cat "$MOTION/motion-readings.log" >> "$LOG/motion.log"
    echo "MOTION_CHANNEL_UNIONED=1 stdout=$FROM_STDOUT 文件=$(wc -l < "$MOTION/motion-readings.log" | tr -d ' ')" >> "$SUMMARY"
fi

step "动效覆盖地板闸门（motion_floor_gate.py）"
( cd "$REPO" && python3 scripts/motion_floor_gate.py "$LOG/motion.log" \
    --expectations scripts/motion_floor_expectations.json ) > "$LOG/motion_gate.log" 2>&1
GATE_EXIT=$?
grep -aE "^MOTION_FLOOR_FACTS|^MOTION_FLOOR_REDS|^MOTION_FLOOR_REGISTERED" "$LOG/motion_gate.log" \
    | tr '\n' ' ' | sed 's/[[:space:]]*$//' | sed 's/^/MOTION_FLOOR=/' >> "$SUMMARY"
echo " MOTION_GATE_EXIT=$GATE_EXIT" >> "$SUMMARY"
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
echo >> "$SUMMARY"
tail -3 "$LOG/capture_gate.log"

step "帧基线（frame_baseline.py check --against working）"
( cd "$REPO" && python3 scripts/frame_baseline.py check "$SHOTS" --against working ) \
    > "$LOG/baseline.log" 2>&1
echo "FRAME_BASELINE_EXIT=$?" >> "$SUMMARY"
grep -aE "^FRAME_BASELINE_|^CHANGED|^MISSING|^ADDED" "$LOG/baseline.log" | tr '\n' ' ' \
    | sed 's/[[:space:]]*$//' | sed 's/^/FRAME_BASELINE=/' >> "$SUMMARY"
echo >> "$SUMMARY"
tail -4 "$LOG/baseline.log"

step "脚本自测（python3 -m unittest discover -s scripts/tests）"
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
echo "PY_EXIT=$?" >> "$SUMMARY"
grep -aE "^Ran [0-9]+ tests|^OK$|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUMMARY"
echo >> "$SUMMARY"
tail -3 "$LOG/py.log"

step "自评曲线守卫（curve_from_ledger.py）"
( cd "$REPO" && python3 .scratch/motion-audit-2/curve_from_ledger.py ) > "$LOG/curve.log" 2>&1
echo "CURVE_EXIT=$?" >> "$SUMMARY"
grep -aE "^GAPS=|^PHASE2" "$LOG/curve.log" | tr '\n' ' ' | sed 's/[[:space:]]*$//' \
    | sed 's/^/CURVE=/' >> "$SUMMARY"
echo >> "$SUMMARY"
tail -3 "$LOG/curve.log"

echo
echo "=== 汇总（$SUMMARY）==="
cat "$SUMMARY"
