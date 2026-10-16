#!/bin/bash
# R102 的验证电池（内容驱动，不驱动退出码）。
# 沿用 R92 立的两条规矩：① 每条先写变量再 echo（`echo "X=$?"` 之前插赋值会把 $? 吃掉）；
# ② 摘要里任何一格没打出「KEY=数字」就计入 MISSING —— "0 个缺陷"比红更坏。
# 沿用 R98 的两条教训：③ 不用任何 bash 4 语法（这台机器是 3.2.57，`${v^^}` 会让循环断掉、
#    而摘要照样打 `MUT_EXIT=0` ⇒ 一道恒真的门）；④ "少一张表"与"某张表非零"一样算红。
# R100 新增第 ⑨ 张变异表（横向内缩四刀 r100 + 收尾三刀 r100b），表数从 7 抬到 9；
# R102 加第 11 张（容器梯子五刀 r102：M568–M572）。
#   表数写死在下面（TABLE_COUNT），少一张就红 —— 与 R99 那条"七张"同构。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=$REPO/.scratch/motion-audit-2/r102_verify.log
# **不许裸截断**（R100 / pass-3 那一格学的）：上一版这里是 `: > "$OUT"`，于是 pass-2 那份全绿日志
# 在 pass-3 起步那一刻就没了 —— 而台账里"pass-1 的读数"这类句子从此**无法被复查**：
# 产物只有一份，引用的却是另一份。现在覆盖前先把上一份按 mtime 另存，
# 这样"我引用的那一份还在不在"这个问题以后有答案。
if [ -s "$OUT" ]; then
  PREVDIR=$(dirname "$OUT")
  STAMP=$(date -r "$OUT" +%Y%m%d-%H%M%S 2>/dev/null || echo unknown)
  cp "$OUT" "$PREVDIR/$(basename "$OUT" .log).$STAMP.prev.log"
fi
: > "$OUT"
say() { printf '%s\n' "$*" >> "$OUT"; }

cd "$REPO/ClipboardHistory" || exit 1

say "== 1) 构建（必须 0 告警）"
env -u SDKROOT swift build --build-tests > /tmp/r102_v_build.log 2>&1
BUILD_EXIT=$?
BUILD_WARN=$(grep -c "warning:" /tmp/r102_v_build.log)
say "BUILD_EXIT=$BUILD_EXIT BUILD_WARNING_LINES=$BUILD_WARN"

say "== 2) 全量 swift test"
env -u SDKROOT swift test > /tmp/r102_v_test2.log 2>&1
TEST_EXIT=$?
TEST_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r102_v_test2.log | tail -1 | sed 's/^[ \t]*//')
say "TEST_EXIT=$TEST_EXIT 最后一行汇总: $TEST_SUMMARY"

say "== 3) 在屏那一卷（本机，带 CLIPBOARD_HISTORY_UI_INTERACTION=1）"
rm -rf /tmp/r102_v_probe
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r102_v_probe \
  CLIPBOARD_HISTORY_PROBE_PULSE=/tmp \
  swift test --filter UIInteractionProbeTests > /tmp/r102_v_probe2.log 2>&1
PROBE_EXIT=$?
PROBE_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r102_v_probe2.log | tail -1 | sed 's/^[ \t]*//')
say "PROBE_EXIT=$PROBE_EXIT 汇总: $PROBE_SUMMARY"

say "== 4) 重新拍一遍帧（R102 新增两臂参照夹具 ⇒ 帧数 130→134，基线必须同提交 update）"
rm -rf /tmp/r102_shots; mkdir -p /tmp/r102_shots
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r102_shots env -u SDKROOT swift test --filter UICaptureTests > /tmp/r102_v_capture.log 2>&1
CAPTURE_EXIT=$?
PNG_COUNT=$(ls /tmp/r102_shots/*.png 2>/dev/null | wc -l | tr -d ' ')
say "CAPTURE_EXIT=$CAPTURE_EXIT 帧数=$PNG_COUNT 目录内文件=$(ls /tmp/r102_shots | wc -l | tr -d ' ')"
grep -E "^CARD_(ABOVE|BELOW)_(SUMMARY|CAPABILITY)" /tmp/r102_v_capture.log >> "$OUT"
grep -E "^CARD_INSET_(SUMMARY|ALL|CAPABILITY)" /tmp/r102_v_capture.log >> "$OUT"
# R102：容器梯子的读数必须进日志 —— 150 的答案只有这几行能给出（runner 上没有 PNG 可下载）
grep -E "^CARD_PROBE_ARM|^CARD_STATS_(CAPABILITY|DECLINED)" /tmp/r102_v_capture.log >> "$OUT"
cd "$REPO" || exit 1
if [ "${UPDATE_FRAMES:-0}" = "1" ]; then
  PYTHONUTF8=1 python3 scripts/frame_baseline.py update /tmp/r102_shots \
    > /tmp/r102_v_frames.log 2>&1
else
  PYTHONUTF8=1 python3 scripts/frame_baseline.py check /tmp/r102_shots --against working \
    --allow-missing content-wide-1100x800-light.png --allow-missing content-wide-1100x800-dark.png \
    > /tmp/r102_v_frames.log 2>&1
fi
FRAMES_EXIT=$?
say "FRAMES_EXIT=$FRAMES_EXIT $(grep -E '^FRAME_BASELINE_' /tmp/r102_v_frames.log | tr '\n' ' ')"

say "== 5) 脚本电池"
if [ "${SKIP_PY:-0}" = "1" ]; then
  PY_EXIT=0
  say "PY_EXIT=0 SKIPPED=1（pass-1 不跑脚本电池：新守卫在台账写盘前必然红）"
else
  PYTHONUTF8=1 python3 -m unittest discover -s scripts/tests > /tmp/r102_v_py.log 2>&1
  PY_EXIT=$?
  say "PY_EXIT=$PY_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r102_v_py.log | tr '\n' ' ')"
fi

say "== 6) 十一张变异表（本轮 r102 五刀；欠的十张照跑）"
# （历史注释：r100b 是 R100 收尾时补的第二张，它钉的是**这一轮新加的两样东西自己**：
#   M560/M561 —— 能力闸门（`XCTSkip` 那种"看起来像通过"的收场必须能被证伪）
#   M562     —— `CARD_FILL_CANDIDATES` 这条新读数通道的名次判据（BACKLOG 147）
# 一张表只管自己那几刀；分两张的理由写在 mutate_r100b.py 的文档串里（期望 verdict 不同）。
# **R101 之后 r100b 只剩 M561/M562**：M560 钉的那一行被本轮的角色拆分重写掉了，
# 它那一格由 r101 的 M564（被告归零 ⇒ skip）与 M565（参照归零 ⇒ 红）接手，两个方向各一刀。
# 这不是"表变松了"—— pass-1 就是因为 M560 命中 0 次而把电池打成 MUT_EXIT=1，
# DID-NOT-RUN 不算通过（R94），所以它是**响出来的**，不是被我发现后悄悄删掉的。
TABLES="r95_rhythm r94_order r96_triage r97_card r98_seed r98_card r99 r100 r100b r101 r102"
TABLE_COUNT=11
MUT_EXIT=0
MISSING_TABLE=0
RUN_TABLES=0
for tag in $TABLES; do
  script=$(printf '%s' "$tag" | sed 's/^/mutate_/')
  PYTHONUTF8=1 python3 ".scratch/motion-audit-2/$script.py" > "/tmp/r102_v_mut_$tag.log" 2>&1
  code=$?
  line=$(grep -E '^MUTATE_TABLE' "/tmp/r102_v_mut_$tag.log" | tail -1)
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

say "== 7) 台账编号守卫"
PYTHONUTF8=1 python3 -m unittest scripts.tests.test_ledger_ids > /tmp/r102_v_ledger.log 2>&1
LEDGER_EXIT=$?
say "LEDGER_EXIT=$LEDGER_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r102_v_ledger.log | tr '\n' ' ')"

say "== 8) 曲线仪器（七维自评的读数通道，尺腿不判产品）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/curve_from_ledger.py > /tmp/r102_v_curve.log 2>&1
VIS_EXIT=$?
say "VIS_EXIT=$VIS_EXIT $(grep -E '^(ROUNDS=|CURVE_|ROUND_WITHOUT_SCORE)' /tmp/r102_v_curve.log | tr '\n' ' ')"

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
