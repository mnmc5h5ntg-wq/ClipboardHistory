#!/bin/bash
# R99 的验证电池（内容驱动，不驱动退出码）。
# 沿用 R92 立的两条规矩：① 每条先写变量再 echo（`echo "X=$?"` 之前插赋值会把 $? 吃掉）；
# ② 摘要里任何一格没打出「KEY=数字」就计入 MISSING —— "0 个缺陷"比红更坏。
# 沿用 R98 的两条教训：③ 不用任何 bash 4 语法（这台机器是 3.2.57，`${v^^}` 会让循环断掉、
#    而摘要照样打 `MUT_EXIT=0` ⇒ 一道恒真的门）；④ "少一张表"与"某张表非零"一样算红。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=$REPO/.scratch/motion-audit-2/r99_verify.log
: > "$OUT"
say() { printf '%s\n' "$*" >> "$OUT"; }

cd "$REPO/ClipboardHistory" || exit 1

say "== 1) 构建（必须 0 告警）"
env -u SDKROOT swift build --build-tests > /tmp/r99_v_build.log 2>&1
BUILD_EXIT=$?
BUILD_WARN=$(grep -c "warning:" /tmp/r99_v_build.log)
say "BUILD_EXIT=$BUILD_EXIT BUILD_WARNING_LINES=$BUILD_WARN"

say "== 2) 全量 swift test"
env -u SDKROOT swift test > /tmp/r99_v_test2.log 2>&1
TEST_EXIT=$?
TEST_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r99_v_test2.log | tail -1 | sed 's/^[ \t]*//')
say "TEST_EXIT=$TEST_EXIT 最后一行汇总: $TEST_SUMMARY"

say "== 3) 在屏那一卷（本机，带 CLIPBOARD_HISTORY_UI_INTERACTION=1）"
rm -rf /tmp/r99_v_probe
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r99_v_probe \
  CLIPBOARD_HISTORY_PROBE_PULSE=/tmp \
  swift test --filter UIInteractionProbeTests > /tmp/r99_v_probe2.log 2>&1
PROBE_EXIT=$?
PROBE_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r99_v_probe2.log | tail -1 | sed 's/^[ \t]*//')
say "PROBE_EXIT=$PROBE_EXIT 汇总: $PROBE_SUMMARY"

say "== 3.5) 重新拍一遍帧（本轮产品改了「推荐」那一屏 ⇒ 帧必须与基线对账）"
rm -rf /tmp/r99_shots; mkdir -p /tmp/r99_shots
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r99_shots env -u SDKROOT swift test --filter UICaptureTests > /tmp/r99_v_capture.log 2>&1
CAPTURE_EXIT=$?
PNG_COUNT=$(ls /tmp/r99_shots/*.png 2>/dev/null | wc -l | tr -d ' ')
say "CAPTURE_EXIT=$CAPTURE_EXIT 帧数=$PNG_COUNT 目录内文件=$(ls /tmp/r99_shots | wc -l | tr -d ' ')"
grep -E "^CARD_(ABOVE|BELOW)_SUMMARY" /tmp/r99_v_capture.log >> "$OUT"
cd "$REPO" || exit 1
if [ "${UPDATE_FRAMES:-0}" = "1" ]; then
  PYTHONUTF8=1 python3 scripts/frame_baseline.py update /tmp/r99_shots \
    > /tmp/r99_v_frames.log 2>&1
else
  PYTHONUTF8=1 python3 scripts/frame_baseline.py check /tmp/r99_shots --against working \
    --allow-missing content-wide-1100x800-light.png --allow-missing content-wide-1100x800-dark.png \
    > /tmp/r99_v_frames.log 2>&1
fi
FRAMES_EXIT=$?
say "FRAMES_EXIT=$FRAMES_EXIT $(grep -E '^FRAME_BASELINE_' /tmp/r99_v_frames.log | tr '\n' ' ')"

say "== 5) 脚本电池"
if [ "${SKIP_PY:-0}" = "1" ]; then
  PY_EXIT=0
  say "PY_EXIT=0 SKIPPED=1（pass-1 不跑脚本电池：新守卫在台账写盘前必然红）"
else
  PYTHONUTF8=1 python3 -m unittest discover -s scripts/tests > /tmp/r99_v_py.log 2>&1
  PY_EXIT=$?
  say "PY_EXIT=$PY_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r99_v_py.log | tr '\n' ' ')"
fi

say "== 6) 七张变异表（本轮一张 r99 四刀；欠的六张照跑）"
TABLES="r95_rhythm r94_order r96_triage r97_card r98_seed r98_card r99"
MUT_EXIT=0
MISSING_TABLE=0
for tag in $TABLES; do
  script=$(printf '%s' "$tag" | sed 's/^/mutate_/')
  PYTHONUTF8=1 python3 ".scratch/motion-audit-2/$script.py" > "/tmp/r99_v_mut_$tag.log" 2>&1
  code=$?
  line=$(grep -E '^MUTATE_TABLE' "/tmp/r99_v_mut_$tag.log" | tail -1)
  if [ -z "$line" ]; then
    MISSING_TABLE=1
    line='没有 MUTATE_TABLE 行'
  fi
  [ "$code" -eq 0 ] || MUT_EXIT=1
  TABLES="$TABLES | $tag(exit=$code): $line"
done
[ "$MISSING_TABLE" -eq 0 ] || MUT_EXIT=1
say "MUT_EXIT=$MUT_EXIT 表=$TABLES"

say "== 7) 台账编号守卫"
PYTHONUTF8=1 python3 -m unittest scripts.tests.test_ledger_ids > /tmp/r99_v_ledger.log 2>&1
LEDGER_EXIT=$?
say "LEDGER_EXIT=$LEDGER_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r99_v_ledger.log | tr '\n' ' ')"

say "== 8) 曲线仪器（七维自评的读数通道，尺腿不判产品）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/curve_from_ledger.py > /tmp/r99_v_curve.log 2>&1
VIS_EXIT=$?
say "VIS_EXIT=$VIS_EXIT $(grep -E '^(ROUNDS=|CURVE_|ROUND_WITHOUT_SCORE)' /tmp/r99_v_curve.log | tr '\n' ' ')"

say "== 9) 摘要缺值算红"
MISSING=0
for key in BUILD_EXIT TEST_EXIT PROBE_EXIT CAPTURE_EXIT FRAMES_EXIT PY_EXIT MUT_EXIT LEDGER_EXIT VIS_EXIT; do
  line=$(grep -E "^$key=" "$OUT" | tail -1)
  if ! printf '%s' "$line" | grep -qE '^[A-Z_]+=[0-9]+'; then
    MISSING=$((MISSING+1)); printf '摘要缺值：%s\n' "$line" >> "$OUT"
  fi
done
say "SUMMARY_MISSING=$MISSING"

if [ "$BUILD_EXIT" -eq 0 ] && [ "$BUILD_WARN" -eq 0 ] && [ "$TEST_EXIT" -eq 0 ] \
   && [ "$PROBE_EXIT" -eq 0 ] && [ "$CAPTURE_EXIT" -eq 0 ] && [ "$FRAMES_EXIT" -eq 0 ] && [ "$PY_EXIT" -eq 0 ] \
   && [ "$MUT_EXIT" -eq 0 ] && [ "$LEDGER_EXIT" -eq 0 ] && [ "$VIS_EXIT" -eq 0 ] \
   && [ "$MISSING" -eq 0 ]; then
  say "VERIFY_OK=1"
else
  say "VERIFY_OK=0"
fi
