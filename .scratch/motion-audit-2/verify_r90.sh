#!/bin/bash
# R90 的验证（第 92 轮）。本轮动的是：在屏探针的心跳通道（Swift 测试码）、报告器第二通道（Python）、
# CI 的两处目录接线。能实跑的全跑，跑不了的逐条点名。
#
# 一条自己的规矩沿用：脚本的退出码必须由**内容**决定（R89 的 verify 最后一条是 `cat`，
# 于是电池 1 刀逃掉它仍 exit 0 —— 见 U-199）。
set -u
REPO=/Users/wangziyi/Codex_Project0
LOG=/tmp/r90_verify
SUM=$LOG/summary.log
rm -rf "$LOG"; mkdir -p "$LOG"

echo "=== 动了哪些非台账文件 ==="
git -C "$REPO" status --porcelain | awk '{print $2}' | grep -v '^AGENT_\|^CHANGELOG\|^\.scratch' > "$LOG/touched.txt"
cat "$LOG/touched.txt"
echo "TOUCHED_NON_LEDGER=$(wc -l < "$LOG/touched.txt" | tr -d ' ')" >> "$SUM"
if git -C "$REPO" status --porcelain | awk '{print $2}' | grep -q '^ClipboardHistory/Sources/'; then
  echo "PRODUCT_TOUCHED=1" >> "$SUM"
else
  echo "PRODUCT_TOUCHED=0（只动 Tests/ ⇒ 帧按构造不变，但仍实测一遍）" >> "$SUM"
fi

echo "=== 脚本自测（判据本体）==="
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
PY_EXIT=$?
echo "PY_EXIT=$PY_EXIT" >> "$SUM"
grep -aE "^Ran [0-9]+ tests|^OK$|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUM"
echo >> "$SUM"

echo "=== 变异电池（八刀，harness = scripts/tests 全部）==="
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r90_pulse.py ) > "$LOG/battery.log" 2>&1
BATTERY_EXIT=$?
echo "BATTERY_EXIT=$BATTERY_EXIT" >> "$SUM"
grep -aE "^汇总" "$LOG/battery.log" | sed 's/^/BATTERY=/' >> "$SUM"

echo "=== 构建（必须 0 告警）==="
( cd "$REPO/ClipboardHistory" && env -u SDKROOT swift build --build-tests ) > "$LOG/build.log" 2>&1
BUILD_EXIT=$?
echo "BUILD_EXIT=$BUILD_EXIT" >> "$SUM"
BUILD_WARNINGS=$(grep -cE 'warning:|error:' "$LOG/build.log" | tr -d ' ')
echo "BUILD_WARNINGS=$BUILD_WARNINGS" >> "$SUM"

echo "=== 全量 Swift 测试（本轮零产品改动，但心跳是测试码，必须整卷跑）==="
( cd "$REPO/ClipboardHistory" && env -u SDKROOT swift test ) > "$LOG/full.log" 2>&1
FULL_EXIT=$?
echo "SWIFT_TEST_EXIT=$FULL_EXIT" >> "$SUM"
# 注意：`^Executed` 抓不到 —— SwiftPM 那两行前面有制表符缩进，第一版因此把这一格写成了空。
grep -aE "Executed [0-9]+ tests" "$LOG/full.log" | tail -2 | tr -s ' \t' ' ' \
  | tr '\n' '|' | sed 's/^/SWIFT_TEST_TAIL=/' >> "$SUM"
echo >> "$SUM"

echo "=== 捕获卷 + 帧基线对账（证明只动测试没有把帧改走）==="
( cd "$REPO/ClipboardHistory" && rm -rf /tmp/r90_shots && mkdir -p /tmp/r90_shots \
  && env -u SDKROOT CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r90_shots swift test --filter UICaptureTests \
       > "$LOG/capture.log" 2>&1 )
CAPTURE_EXIT=$?
echo "CAPTURE_EXIT=$CAPTURE_EXIT" >> "$SUM"
frames=$(find /tmp/r90_shots -name '*.png' 2>/dev/null | wc -l | tr -d ' ')
echo "CAPTURE_FRAMES=$frames" >> "$SUM"
( cd "$REPO" && python3 scripts/frame_baseline.py check /tmp/r90_shots --against working \
    --allow-missing content-wide-1100x800-light.png \
    --allow-missing content-wide-1100x800-dark.png ) > "$LOG/baseline.log" 2>&1
BASELINE_EXIT=$?
echo "BASELINE_EXIT=$BASELINE_EXIT" >> "$SUM"
grep -aE "^FRAME_BASELINE_(COMPARED|CHANGED|MISSING|ADDED|AGAINST)" "$LOG/baseline.log" | tr '\n' ' ' | sed 's/^/BASELINE=/' >> "$SUM"
echo >> "$SUM"

echo '=== 本轮的真实看图（读数落盘，不许只写「看过了」）==='
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/r90_stats_visual.py /tmp/r90_shots ) \
  > "$LOG/visual.log" 2>&1
VISUAL_EXIT=$?
echo "VISUAL_EXIT=$VISUAL_EXIT" >> "$SUM"
grep -aE "^CROSS_MODE|NO_BLUE_CELLS|COLUMN_SEGMENTS|BAND_COUNT_MISMATCH|CARD_SAMPLE_CONTAMINATED" \
  "$LOG/visual.log" | tr '\n' '|' | sed 's/^/VISUAL_SELFTEST=/' >> "$SUM"
echo >> "$SUM"
grep -aE "0 计数格" "$LOG/visual.log" | awk '!seen[$0]++' | head -4 | tr '\n' '|' \
  | sed 's/^/HEAT_EMPTY_CELL=/' >> "$SUM"
echo >> "$SUM"
grep -aE "ROW 快捷键|ROW 推荐" "$LOG/visual.log" | awk '!seen[$0]++' | head -4 | tr '\n' '|' \
  | sed 's/^/SIDEBAR_ROWS=/' >> "$SUM"
echo >> "$SUM"

echo "=== 心跳通道的本机实测（真产物，不是推理）==="
# 两个坑：① 这一格必须写成 `KEY=值`（上一版是 `PULSE_SPIKE 值`，摘要缺值那条守卫当场拦下）；
# ② `$(grep -c … || echo 0)` 会拿到**两个** 0 —— grep -c 没匹配时自己就打 0 并以 1 退出，
#    于是 `|| echo 0` 又补一个，换行塞进 printf 中间。
ui_bytes=$(wc -c < /tmp/r90_pulse/ui.log 2>/dev/null | tr -d ' ')
pulse_lines=$(grep -c '^PROBE_PULSE ' /tmp/r90_pulse/probe-pulse.log 2>/dev/null)
ui_started=$(grep -c "Test Case '-\\[.*\\]' started\\." /tmp/r90_pulse/ui.log 2>/dev/null)
echo "PULSE_SPIKE=ui_bytes=${ui_bytes:-缺文件} pulse_lines=${pulse_lines:-缺文件} ui_started=${ui_started:-缺文件}" >> "$SUM"
echo "（上面这一格读的是本轮早先那支 spike 的产物 /tmp/r90_pulse，不是重新跑一遍在屏卷）" >> "$SUM"
echo "pulse_fixture_lines=$(grep -c '^PROBE_PULSE ' "$REPO/scripts/tests/fixtures/r90_pulse_real.log" | tr -d ' ')" >> "$SUM"

echo "=== NOT-RUN（逐条点名）==="
echo "NOT_RUN=拖拽探针挂死本身的修法（BACKLOG 125：加看门狗 vs 改成直接调手势逻辑，本轮只做到能点名）" >> "$SUM"
echo "NOT_RUN=runner 上的两件事：① 心跳通道在无头 runner 上是否同样落盘 ② 换目录之后 Capture gate 是否复绿 —— 只有下一次 CI 知道" >> "$SUM"
echo 'NOT_RUN=第一次全量 swift test 的退出码不作数（那条 SWIFT_TEST_EXIT=0 量的是管道尾端的 tail）⇒ 本轮的数以上面 SWIFT_TEST_EXIT 那一行为准（U-200）' >> "$SUM"
echo "NOT_RUN=BACKLOG 124 第②步（装机落后审计升成 scripts 判据 + CI 一步）" >> "$SUM"
echo "NOT_RUN=BACKLOG 126：离屏捕获 vs 真机窗口截图那一次对照（本轮只做到把不一致量出来：亮档四枚图标 0 墨、推荐一枚纯黑）" >> "$SUM"
echo "NOT_RUN=暗档侧栏逐行读数：新仪器在暗档上 COLUMN_SEGMENTS=1 ⇒ NOT-RUN，那一格仍只有 R88 那一份（且身份错位）" >> "$SUM"

FAILS=""
# 摘要里"有键无值 / 键干脆没了"必须算红。上一版用 `grep -aE "^Executed"` 取汇总行，
# 而 SwiftPM 那两行前面带制表符缩进 ⇒ `SWIFT_TEST_TAIL` 整格静默消失（U-200 第三条）。
for key in TOUCHED_NON_LEDGER PRODUCT_TOUCHED PY_EXIT SCRIPT_TESTS BATTERY_EXIT BATTERY \
           BUILD_EXIT BUILD_WARNINGS SWIFT_TEST_EXIT SWIFT_TEST_TAIL CAPTURE_EXIT CAPTURE_FRAMES \
           BASELINE_EXIT BASELINE VISUAL_EXIT VISUAL_SELFTEST HEAT_EMPTY_CELL SIDEBAR_ROWS \
           PULSE_SPIKE pulse_fixture_lines; do
  grep -q "^${key}=." "$SUM" || FAILS="$FAILS 摘要缺值:$key"
done
[ "${PY_EXIT:-1}" = "0" ] || FAILS="$FAILS PY_EXIT=$PY_EXIT"
[ "${BATTERY_EXIT:-1}" = "0" ] || FAILS="$FAILS BATTERY_EXIT=$BATTERY_EXIT"
[ "${BUILD_EXIT:-1}" = "0" ] || FAILS="$FAILS BUILD_EXIT=$BUILD_EXIT"
[ "${BUILD_WARNINGS:-1}" = "0" ] || FAILS="$FAILS BUILD_WARNINGS=$BUILD_WARNINGS"
[ "${FULL_EXIT:-1}" = "0" ] || FAILS="$FAILS SWIFT_TEST_EXIT=$FULL_EXIT"
[ "${CAPTURE_EXIT:-1}" = "0" ] || FAILS="$FAILS CAPTURE_EXIT=$CAPTURE_EXIT"
[ "${BASELINE_EXIT:-1}" = "0" ] || FAILS="$FAILS BASELINE_EXIT=$BASELINE_EXIT"
[ "${VISUAL_EXIT:-1}" = "0" ] || FAILS="$FAILS VISUAL_EXIT=$VISUAL_EXIT"
[ "${frames:-0}" -ge 60 ] 2>/dev/null || FAILS="$FAILS CAPTURE_FRAMES=${frames:-?}"
grep -q "汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成" "$LOG/battery.log" || FAILS="$FAILS 电池不是 8/8"
# 看图这条不许空跑：正对照（空态量不到蓝）与反对照（两色模式色号不重叠）都要在输出里。
grep -q "CROSS_MODE" "$LOG/visual.log" || FAILS="$FAILS 看图仪器没跑出反对照"
[ "$(grep -c 'NO_BLUE_CELLS' "$LOG/visual.log")" -ge 2 ] || FAILS="$FAILS 正对照没走到（空态帧应各报一次）"

echo
cat "$SUM"
if [ -n "$FAILS" ]; then
  echo "VERIFY_FAILED=$FAILS" | tee -a "$SUM"
  exit 1
fi
echo "VERIFY_OK=1" | tee -a "$SUM"
