#!/bin/bash
# R98 的验证电池（内容驱动，不驱动退出码）。
# 沿用 R92 立的两条规矩：① 每条先写变量再 echo（`echo "X=$?"` 之前插赋值会把 $? 吃掉）；
# ② 摘要里任何一格没打出「KEY=数字」就计入 MISSING —— "0 个缺陷"比红更坏。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=$REPO/.scratch/motion-audit-2/r98_verify.log
: > "$OUT"
say() { printf '%s\n' "$*" >> "$OUT"; }

cd "$REPO/ClipboardHistory" || exit 1

say "== 1) 构建（必须 0 告警）"
env -u SDKROOT swift build --build-tests > /tmp/r98_v_build.log 2>&1
BUILD_EXIT=$?
BUILD_WARN=$(grep -c "warning:" /tmp/r98_v_build.log)
say "BUILD_EXIT=$BUILD_EXIT BUILD_WARNING_LINES=$BUILD_WARN"

say "== 2) 全量 swift test"
env -u SDKROOT swift test > /tmp/r98_v_test2.log 2>&1
TEST_EXIT=$?
TEST_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r98_v_test2.log | tail -1 | sed 's/^[ \t]*//')
say "TEST_EXIT=$TEST_EXIT 最后一行汇总: $TEST_SUMMARY"

say "== 3) 在屏那一卷（本机，带 CLIPBOARD_HISTORY_UI_INTERACTION=1）"
rm -rf /tmp/r98_v_probe
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r98_v_probe \
  CLIPBOARD_HISTORY_PROBE_PULSE=/tmp \
  swift test --filter UIInteractionProbeTests > /tmp/r98_v_probe2.log 2>&1
PROBE_EXIT=$?
PROBE_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r98_v_probe2.log | tail -1 | sed 's/^[ \t]*//')
say "PROBE_EXIT=$PROBE_EXIT 汇总: $PROBE_SUMMARY"

say "== 3.5) 重新拍一遍帧（本轮产品改了「推荐」那张卡片 ⇒ 帧必须与基线一致）"
rm -rf /tmp/r98_shots; mkdir -p /tmp/r98_shots
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r98_shots env -u SDKROOT swift test --filter UICaptureTests > /tmp/r98_v_capture.log 2>&1
CAPTURE_EXIT=$?
# 帧数只数 PNG：`ls | wc -l` 会把 capture-readings.log 也算进去（R96 pass-1 就是这样 125 vs 124）
PNG_COUNT=$(ls /tmp/r98_shots/*.png 2>/dev/null | wc -l | tr -d ' ')
say "CAPTURE_EXIT=$CAPTURE_EXIT 帧数=$PNG_COUNT 目录内文件=$(ls /tmp/r98_shots | wc -l | tr -d ' ')"
# 种子通道的读数：判据重渲染的那张 vs 交付的那张，逐字节
grep -E "^SEED_GUARD" /tmp/r98_v_capture.log | head -6 >> "$OUT"
grep -cE "^SEED_GUARD " /tmp/r98_v_capture.log | sed 's/^/SEED_GUARD_LINES=/' >> "$OUT"
cd "$REPO" || exit 1
PYTHONUTF8=1 python3 scripts/frame_baseline.py check /tmp/r98_shots --against working \
  --allow-missing content-wide-1100x800-light.png --allow-missing content-wide-1100x800-dark.png \
  > /tmp/r98_v_frames.log 2>&1
FRAMES_EXIT=$?
say "FRAMES_EXIT=$FRAMES_EXIT $(grep -E '^FRAME_BASELINE_' /tmp/r98_v_frames.log | tr '\n' ' ')"

say "== 5) 脚本电池"
if [ "${SKIP_PY:-0}" = "1" ]; then
  PY_EXIT=0
  say "PY_EXIT=0 SKIPPED=1（pass-1 不跑脚本电池：新守卫在台账写盘前必然红）"
else
  PYTHONUTF8=1 python3 -m unittest discover -s scripts/tests > /tmp/r98_v_py.log 2>&1
  PY_EXIT=$?
  say "PY_EXIT=$PY_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r98_v_py.log | tr '\n' ' ')"
fi

say "== 6) 六张变异表（本轮两张：种子通道 7 刀 + 产品腿 2 刀；欠的四张照跑）"
# R98 pass-1 的教训（U-248）：这一段第一版写的是 `eval "MUT_${tag^^}_EXIT=$?"`，
# 而这台机器的 bash 是 **3.2.57**（macOS 自带），`${var^^}` 是 bash 4 的大写展开 ⇒
# 循环在第一张表之后就断了：只有 `r98_v_mut_r95_rhythm.log` 存在，而 `MUT_EXIT` 停在初值 0，
# 摘要里那一格打成 `MUT_EXIT=0`（后面连表名都没有）—— **一道看起来有牙、实际恒真的门**。
# 所以这里①不用任何 bash 4 语法，②结论行必须把六张表各自的 `MUTATE_TABLE` 原文贴出来，
# ③"少一张表"与"某张表非零"一样算红（缺行不是通过）。
TABLES="r95_rhythm r94_order r96_triage r97_card r98_seed r98_card"
MUT_EXIT=0
MISSING_TABLE=0
for tag in $TABLES; do
  script=$(printf '%s' "$tag" | sed 's/^/mutate_/')
  PYTHONUTF8=1 python3 ".scratch/motion-audit-2/$script.py" > "/tmp/r98_v_mut_$tag.log" 2>&1
  code=$?
  line=$(grep -E '^MUTATE_TABLE' "/tmp/r98_v_mut_$tag.log" | tail -1)
  if [ -z "$line" ]; then
    MISSING_TABLE=1
    line='没有 MUTATE_TABLE 行'
  fi
  [ "$code" -eq 0 ] || MUT_EXIT=1
  TABLES="$TABLES | $tag(exit=$code): $line"
done
[ "$MISSING_TABLE" -eq 0 ] || MUT_EXIT=1
say "MUT_EXIT=$MUT_EXIT 表=$TABLES"   # R98：中间必须有空格，`MUT_EXIT=(\S+)` 才不会读到下一格的开头

say "== 7) 台账编号守卫"
PYTHONUTF8=1 python3 -m unittest scripts.tests.test_ledger_ids > /tmp/r98_v_ledger.log 2>&1
LEDGER_EXIT=$?
say "LEDGER_EXIT=$LEDGER_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r98_v_ledger.log | tr '\n' ' ')"

say "== 8) 看图仪器（卡片边界与『什么算一张卡片』，尺腿不判产品）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/r97_stats_visual.py /tmp/r98_shots \
  > .scratch/motion-audit-2/r98_stats_readings.log 2>&1
VIS_EXIT=$?
say "VIS_EXIT=$VIS_EXIT 候选块=$(grep -c '候选' .scratch/motion-audit-2/r98_stats_readings.log) 自检=$(grep -c 'SELF-CHECK OK' .scratch/motion-audit-2/r98_stats_readings.log) 失败自检=$(grep -c 'SELF-CHECK FAIL' .scratch/motion-audit-2/r98_stats_readings.log)"

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
