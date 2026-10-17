#!/bin/bash
# R105 的验证电池（内容驱动，不驱动退出码）。
# 沿用 R92 立的两条规矩：① 每条先写变量再 echo（`echo "X=$?"` 之前插赋值会把 $? 吃掉）；
# ② 摘要里任何一格没打出「KEY=数字」就计入 MISSING —— "0 个缺陷"比红更坏。
# 沿用 R98 的两条教训：③ 不用任何 bash 4 语法（这台机器是 3.2.57）；④ "少一张表"与"某张表非零"一样算红。
# 历史：R100 加第 9 张（横向内缩 r100 + 收尾 r100b）⇒ 7→9；R102 加第 11 张（容器梯子 r102）；
# R109 加第 16 张（157 的实验对象必须在帧内：M588 按实逃掉、M589/M590 CAUGHT），
#   并把 CARD_PROBE_GEOMETRY / CARD_PROBE_WHOLE* 接进读数通道。
# R106 加第 15 张（浮层幻影选中底 r109：M584/M585 CAUGHT、M586/M587 按实逃掉），
#   并把 QUICKPICK_FIELD_STATE / GREY_BAND / PHANTOM_* 接进读数通道。
# R105 加第 14 张（判据的收场形状 r109：M581 SKIPPED / M582 CAUGHT / M583 按实逃掉），
#   并把读数通道加上 QUICKPICK_AXIS_*（能力行与未判名单是这一轮的产物通道）。
# R103 加第 12 张（墨证人自己 r103），并把 R102 落盘的**断言包含对账**从手工动作升成电池里的一格
#   （`CONTAIN_EXIT`）：R101 那条 U-289 是"少一条断言、swift test 全绿"，
#   它的守卫工具已经存在却不进门 ⇒ 每一轮都得靠我记得去跑，而记不住的那一轮就是下一轮的红。
#   表数写死在下面（TABLE_COUNT），少一张就红 —— 与 R99 那条"七张"同构。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=$REPO/.scratch/motion-audit-2/r109_verify.log
# **不许裸截断**（R100 / pass-3 那一格学的）：覆盖前先把上一份按 mtime 另存，
# 这样"我引用的那一份还在不在"这个问题以后有答案。
if [ -s "$OUT" ]; then
  PREVDIR=$(dirname "$OUT")
  STAMP=$(date -r "$OUT" +%Y%m%d-%H%M%S 2>/dev/null || echo unknown)
  cp "$OUT" "$PREVDIR/$(basename "$OUT" .log).$STAMP.prev.log"
fi
: > "$OUT"
say() { printf '%s\n' "$*" >> "$OUT"; }

cd "$REPO/ClipboardHistory" || exit 1

say "== 0) 变异针自检（U-338：原来在第 6 步，即构建+全量测试+在屏探针+拍帧+脚本电池之后）"
# 挪到最前面的理由不是"顺手"：R109 pass-1 里这一格**确实红了**（`PRECHECK_EXIT=1 bad=1`，
# M568 的 needle 因为臂 2 的带子从 100pt 改到 260pt 而命中 0 次），但它红在第 25 分钟，
# 后面第 7 步的 `not_run=1` 只是把同一个事实再报一遍 —— 前面五步全白等。
# 它是纯静态的（读 16 张表的 needle 与被打字的那些源文件，1 秒、不建、不跑 swift），
# 所以它没有理由排在任何会构建的步骤后面。绝对路径：这一步还在 ClipboardHistory 里。
PYTHONUTF8=1 python3 "$REPO/.scratch/motion-audit-2/mutate_needle_precheck.py" > /tmp/r109_v_precheck.log 2>&1
PRECHECK_EXIT=$?
say "PRECHECK_EXIT=$PRECHECK_EXIT $(grep -E '^NEEDLE_PRECHECK' /tmp/r109_v_precheck.log | tr '\n' ' ')"

say "== 1) 构建（必须 0 告警）"
env -u SDKROOT swift build --build-tests > /tmp/r109_v_build.log 2>&1
BUILD_EXIT=$?
BUILD_WARN=$(grep -c "warning:" /tmp/r109_v_build.log)
say "BUILD_EXIT=$BUILD_EXIT BUILD_WARNING_LINES=$BUILD_WARN"

say "== 2) 全量 swift test"
env -u SDKROOT swift test > /tmp/r109_v_test.log 2>&1
TEST_EXIT=$?
TEST_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r109_v_test.log | tail -1 | sed 's/^[ \t]*//')
say "TEST_EXIT=$TEST_EXIT 最后一行汇总: $TEST_SUMMARY"

say "== 3) 在屏那一卷（本机，带 CLIPBOARD_HISTORY_UI_INTERACTION=1）"
rm -rf /tmp/r109_v_probe
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r109_v_probe \
  CLIPBOARD_HISTORY_PROBE_PULSE=/tmp \
  swift test --filter UIInteractionProbeTests > /tmp/r109_v_probe.log 2>&1
PROBE_EXIT=$?
PROBE_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r109_v_probe.log | tail -1 | sed 's/^[ \t]*//')
say "PROBE_EXIT=$PROBE_EXIT 汇总: $PROBE_SUMMARY"

say "== 4) 重新拍一遍帧（R105 没有产品像素改动 ⇒ 134 张必须逐字不变，含 R104 刚换的那 8 条）"
rm -rf /tmp/r109_shots; mkdir -p /tmp/r109_shots
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r109_shots env -u SDKROOT swift test --filter UICaptureTests > /tmp/r109_v_capture.log 2>&1
CAPTURE_EXIT=$?
PNG_COUNT=$(ls /tmp/r109_shots/*.png 2>/dev/null | wc -l | tr -d ' ')
say "CAPTURE_EXIT=$CAPTURE_EXIT 帧数=$PNG_COUNT 目录内文件=$(ls /tmp/r109_shots | wc -l | tr -d ' ')"
grep -E "^CARD_(ABOVE|BELOW)_(SUMMARY|CAPABILITY)" /tmp/r109_v_capture.log >> "$OUT"
grep -E "^CARD_INSET_(SUMMARY|ALL|CAPABILITY)" /tmp/r109_v_capture.log >> "$OUT"
# R103：证人的新成因读数必须进日志（`墨像素/最大偏离/参考条墨行` 是这一轮的产物通道）
grep -E "^CARD_PROBE_ARM|^CARD_STATS_(CAPABILITY|DECLINED)|^QUICKPICK_SEARCH_AXIS|^QUICKPICK_AXIS_|^QUICKPICK_FIELD_STATE|^QUICKPICK_GREY_BAND|^QUICKPICK_PHANTOM_|^CARD_PROBE_GEOMETRY|^CARD_PROBE_WHOLE|^CARD_PROBE_COLUMNS|^SELECTION_CHROMA|^SELECTION_KEYSTATE_" /tmp/r109_v_capture.log >> "$OUT"
cd "$REPO" || exit 1
if [ "${UPDATE_FRAMES:-0}" = "1" ]; then
  PYTHONUTF8=1 python3 scripts/frame_baseline.py update /tmp/r109_shots \
    > /tmp/r109_v_frames.log 2>&1
else
  PYTHONUTF8=1 python3 scripts/frame_baseline.py check /tmp/r109_shots --against working \
    --allow-missing content-wide-1100x800-light.png --allow-missing content-wide-1100x800-dark.png \
    > /tmp/r109_v_frames.log 2>&1
fi
FRAMES_EXIT=$?
say "FRAMES_EXIT=$FRAMES_EXIT $(grep -E '^FRAME_BASELINE_' /tmp/r109_v_frames.log | tr '\n' ' ')"

say "== 5) 脚本电池"
if [ "${SKIP_PY:-0}" = "1" ]; then
  PY_EXIT=0
  say "PY_EXIT=0 SKIPPED=1（pass-1 不跑脚本电池：新守卫在台账写盘前必然红）"
else
  PYTHONUTF8=1 python3 -m unittest discover -s scripts/tests > /tmp/r109_v_py.log 2>&1
  PY_EXIT=$?
  # 只读退出码 + 汇总行（R102 / U-295：unittest 的汇总走 stderr，`tail` 看到的永远是 stdout 的尾巴）
  say "PY_EXIT=$PY_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r109_v_py.log | tr '\n' ' ')"
fi

say "== 6) 变异针自检 —— 已并入第 0 步（U-338：它红了，但红在第 25 分钟）"

say "== 7) 十八张变异表（本轮 r109 四刀 M594–M597；欠的十七张照跑）"
TABLES="r95_rhythm r94_order r96_triage r97_card r98_seed r98_card r99 r100 r100b r101 r102 r103 r104 r105 r106 r107 r108 r109"
TABLE_COUNT=18
MUT_EXIT=0
MISSING_TABLE=0
RUN_TABLES=0
for tag in $TABLES; do
  script=$(printf '%s' "$tag" | sed 's/^/mutate_/')
  PYTHONUTF8=1 python3 ".scratch/motion-audit-2/$script.py" > "/tmp/r109_v_mut_$tag.log" 2>&1
  code=$?
  line=$(grep -E '^MUTATE_TABLE' "/tmp/r109_v_mut_$tag.log" | tail -1)
  if [ -z "$line" ]; then
    MISSING_TABLE=1
    line='没有 MUTATE_TABLE 行'
  fi
  RUN_TABLES=$((RUN_TABLES+1))
  [ "$code" -eq 0 ] || MUT_EXIT=1
  TABLES="$TABLES | $tag(exit=$code): $line"
done
[ "$MISSING_TABLE" -eq 0 ] || MUT_EXIT=1
# "少跑一张表"必须与"某张表非零"同样算红（R99 那条规矩，表数写死而不是从循环推）。
[ "$RUN_TABLES" -eq "$TABLE_COUNT" ] || MUT_EXIT=1
say "MUT_EXIT=$MUT_EXIT 跑了=$RUN_TABLES 期望=$TABLE_COUNT 表=$TABLES"

say "== 8) 台账编号守卫"
PYTHONUTF8=1 python3 -m unittest scripts.tests.test_ledger_ids > /tmp/r109_v_ledger.log 2>&1
LEDGER_EXIT=$?
say "LEDGER_EXIT=$LEDGER_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r109_v_ledger.log | tr '\n' ' ')"

say "== 9) 曲线仪器（七维自评的读数通道，尺腿不判产品）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/curve_from_ledger.py > /tmp/r109_v_curve.log 2>&1
VIS_EXIT=$?
say "VIS_EXIT=$VIS_EXIT $(grep -E '^(ROUNDS=|CURVE_|ROUND_WITHOUT_SCORE)' /tmp/r109_v_curve.log | tr '\n' ' ')"

say "== 10) 断言/读数包含对账（R101 的 U-289 ⇒ 工具已落盘，R103 让它进门）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/assertion_containment.py \
  ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift --ref HEAD \
  > /tmp/r109_v_contain.log 2>&1
CONTAIN_EXIT=$?
LOST=$(grep -E '^CONTAINMENT_LOST=' /tmp/r109_v_contain.log | tail -1 | sed 's/.*=//')
say "CONTAIN_EXIT=$CONTAIN_EXIT $LOST $(grep -E '^TOTAL_DROPPED=' /tmp/r109_v_contain.log | tr '\n' ' ')"

say "== 11) 摘要缺值算红"
MISSING=0
for key in BUILD_EXIT TEST_EXIT PROBE_EXIT CAPTURE_EXIT FRAMES_EXIT PY_EXIT PRECHECK_EXIT MUT_EXIT LEDGER_EXIT VIS_EXIT CONTAIN_EXIT; do
  line=$(grep -E "^$key=" "$OUT" | tail -1)
  if ! printf '%s' "$line" | grep -qE '^[A-Z_]+=[0-9]+'; then
    MISSING=$((MISSING+1)); printf '摘要缺值：%s\n' "$line" >> "$OUT"
  fi
done
say "SUMMARY_MISSING=$MISSING"

if [ "$BUILD_EXIT" -eq 0 ] && [ "$BUILD_WARN" -eq 0 ] && [ "$TEST_EXIT" -eq 0 ] \
   && [ "$PROBE_EXIT" -eq 0 ] && [ "$CAPTURE_EXIT" -eq 0 ] && [ "$FRAMES_EXIT" -eq 0 ] \
   && [ "$PY_EXIT" -eq 0 ] && [ "$MUT_EXIT" -eq 0 ] && [ "$LEDGER_EXIT" -eq 0 ] \
   && [ "$VIS_EXIT" -eq 0 ] && [ "$CONTAIN_EXIT" -eq 0 ] \
   && [ "$PRECHECK_EXIT" -eq 0 ] \
   && [ "$MISSING" -eq 0 ]; then
  say "VERIFY_OK=1"
else
  say "VERIFY_OK=0"
fi
