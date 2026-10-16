#!/bin/bash
# R91 的验证（第 93 轮）。本轮动的是：在屏探针卷里那条僵尸拖选探针（删）、
# 一条机制级守卫（新增）、帧采样通道的证人（新增）。产品文件 0 个。
#
# 沿用 R90 的三条自己的规矩：
#  · 退出码由**内容**决定，不由最后一条命令决定；
#  · 摘要里"有键无值"算红；
#  · 脚本一旦开跑就不许边跑边改（bash 边读边执行 ⇒ 缝合运行，R91 现场踩过）。
set -u
REPO=/Users/wangziyi/Codex_Project0
LOG=/tmp/r91_verify
SUM=$LOG/summary.log
rm -rf "$LOG"; mkdir -p "$LOG"

echo "=== 动了哪些非台账文件 ==="
git -C "$REPO" status --porcelain | awk '{print $2}' | grep -v '^AGENT_\|^CHANGELOG\|^\.scratch' > "$LOG/touched.txt"
cat "$LOG/touched.txt"
TOUCHED=$(wc -l < "$LOG/touched.txt" | tr -d ' ')
echo "TOUCHED_NON_LEDGER=$TOUCHED" >> "$SUM"
if git -C "$REPO" status --porcelain | awk '{print $2}' | grep -q '^ClipboardHistory/Sources/'; then
  echo "PRODUCT_TOUCHED=1" >> "$SUM"
else
  echo "PRODUCT_TOUCHED=0（只动 Tests/ ⇒ 帧按构造不变，但仍实测一遍）" >> "$SUM"
fi

echo "=== 脚本自测 ==="
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
PY_EXIT=$?
echo "PY_EXIT=$PY_EXIT" >> "$SUM"
grep -aE "^Ran [0-9]+ tests|^OK$|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUM"
echo >> "$SUM"

echo "=== 变异电池（五刀；M509 是故意要逃的那一刀）==="
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r91_zombie.py ) > "$LOG/battery.log" 2>&1
BATTERY_EXIT=$?
echo "BATTERY_EXIT=$BATTERY_EXIT" >> "$SUM"
grep -aE "^汇总" "$LOG/battery.log" | sed 's/^/BATTERY=/' >> "$SUM"

echo "=== 构建（必须 0 告警）==="
( cd "$REPO/ClipboardHistory" && env -u SDKROOT swift build --build-tests ) > "$LOG/build.log" 2>&1
BUILD_EXIT=$?
BUILD_WARNINGS=$(grep -cE 'warning:|error:' "$LOG/build.log" | tr -d ' ')
echo "BUILD_EXIT=$BUILD_EXIT" >> "$SUM"
echo "BUILD_WARNINGS=$BUILD_WARNINGS" >> "$SUM"

echo "=== 全量 Swift 测试（在屏那一卷默认 skip，所以这一遍必须绿）==="
( cd "$REPO/ClipboardHistory" && env -u SDKROOT swift test ) > "$LOG/full.log" 2>&1
FULL_EXIT=$?
echo "SWIFT_TEST_EXIT=$FULL_EXIT" >> "$SUM"
grep -aE "Executed [0-9]+ tests" "$LOG/full.log" | tail -2 | tr -s ' \t' ' ' \
  | tr '\n' '|' | sed 's/^/SWIFT_TEST_TAIL=/' >> "$SUM"
echo >> "$SUM"

echo "=== 在屏那一卷（CI 原样：带 INTERACTION=1 与心跳通道；180 秒上限）==="
rm -rf /tmp/r91_probe /tmp/r91_probe_shots; mkdir -p /tmp/r91_probe /tmp/r91_probe_shots
( cd "$REPO/ClipboardHistory" && CLIPBOARD_HISTORY_UI_INTERACTION=1 \
    CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r91_probe_shots CLIPBOARD_HISTORY_PROBE_PULSE=/tmp/r91_probe \
    env -u SDKROOT swift test --filter UIInteractionProbeTests > "$LOG/probe.log" 2>&1 ) &
probe_pid=$!
( sleep 180; kill -9 $probe_pid 2>/dev/null; pkill -9 -f "usr/bin/xctest" 2>/dev/null ) &
watchdog=$!
wait $probe_pid; PROBE_EXIT=$?
kill -9 $watchdog 2>/dev/null
PROBE_PULSES=$(grep -c '^PROBE_PULSE ' /tmp/r91_probe/probe-pulse.log 2>/dev/null)
PROBE_PASSED=$(grep -cE "Test Case .*\]' passed" "$LOG/probe.log")
PROBE_FAILED=$(grep -cE "Test Case .*\]' failed" "$LOG/probe.log")
PROBE_SKIPPED=$(grep -cE "Test Case .*\]' skipped" "$LOG/probe.log")
PROBE_EXECUTED=$(grep -oE "Executed [0-9]+ tests" "$LOG/probe.log" | tail -1 | tr -dc '0-9')
echo "PROBE_EXIT=$PROBE_EXIT" >> "$SUM"
echo "PROBE_TALLY=心跳=${PROBE_PULSES:-?} executed=${PROBE_EXECUTED:-?} passed=${PROBE_PASSED:-?} skipped=${PROBE_SKIPPED:-?} failed=${PROBE_FAILED:-?}" >> "$SUM"
grep -aE "^FRAME_CHANNEL|^DRAG-LIMIT" "$LOG/probe.log" | tr '\n' '|' | sed 's/^/PROBE_READINGS=/' >> "$SUM"
echo >> "$SUM"
grep -aE "error: -\[" "$LOG/probe.log" | head -2 | cut -c1-200 | tr '\n' '|' | sed 's/^/PROBE_RED=/' >> "$SUM"
echo >> "$SUM"

echo "=== 捕获卷 + 帧基线对账 ==="
( cd "$REPO/ClipboardHistory" && rm -rf /tmp/r91_shots && mkdir -p /tmp/r91_shots \
  && env -u SDKROOT CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r91_shots swift test --filter UICaptureTests \
       > "$LOG/capture.log" 2>&1 )
CAPTURE_EXIT=$?
frames=$(find /tmp/r91_shots -name '*.png' 2>/dev/null | wc -l | tr -d ' ')
echo "CAPTURE_EXIT=$CAPTURE_EXIT" >> "$SUM"
echo "CAPTURE_FRAMES=$frames" >> "$SUM"
( cd "$REPO" && python3 scripts/frame_baseline.py check /tmp/r91_shots --against working \
    --allow-missing content-wide-1100x800-light.png \
    --allow-missing content-wide-1100x800-dark.png ) > "$LOG/baseline.log" 2>&1
BASELINE_EXIT=$?
echo "BASELINE_EXIT=$BASELINE_EXIT" >> "$SUM"
grep -aE "^FRAME_BASELINE_(COMPARED|CHANGED|MISSING|ADDED|AGAINST)" "$LOG/baseline.log" | tr '\n' ' ' | sed 's/^/BASELINE=/' >> "$SUM"
echo >> "$SUM"

echo "=== 本轮看图的仪器（正/反对照都在里面）==="
( cd "$REPO" && PYTHONUTF8=1 python3 "$REPO/.scratch/motion-audit-2/r91_focus_visual.py" ) > "$LOG/visual.log" 2>&1
VISUAL_EXIT=$?
echo "VISUAL_EXIT=$VISUAL_EXIT" >> "$SUM"
grep -aE "^===|NO_BLUE|带[0-9]|蓝区总跨度" "$LOG/visual.log" | tr '\n' '|' | sed 's/^/VISUAL=/' >> "$SUM"
echo >> "$SUM"

echo "=== NOT-RUN（逐条点名）==="
echo "NOT_RUN=BACKLOG 127 的定性（一行两个半宽 KeyViewProxy：产品无障碍结构 vs 探针期望没被正对照校准）—— 本轮只做到让它第一次跑出结论并点名" >> "$SUM"
echo 'NOT_RUN=BACKLOG 126 的决定性实验（真机窗口截图 vs 离屏帧）：这台机器现在做不了 —— screencapture 返回 2940x1912 全黑、pmset 报 UserIsActive 0 ⇒ 显示器睡着/无录屏权限。这一格是**没跑**，不是「真机也看不见」' >> "$SUM"
echo "NOT_RUN=BACKLOG 124 第②步（装机落后审计升成 scripts 判据 + CI 一步）" >> "$SUM"
echo "NOT_RUN=runner 上的两件事：① 在屏那一卷第一次能跑到 10 条结论吗（本机已证）② FRAME_CHANNEL 在 runner 上是 n=0 还是有 tick" >> "$SUM"
echo "NOT_RUN=换装：本轮产品文件 0 个 ⇒ 不换装（帧按构造不变，仍实测对账）" >> "$SUM"

FAILS=""
for key in TOUCHED_NON_LEDGER PRODUCT_TOUCHED PY_EXIT SCRIPT_TESTS BATTERY_EXIT BATTERY \
           BUILD_EXIT BUILD_WARNINGS SWIFT_TEST_EXIT SWIFT_TEST_TAIL PROBE_EXIT PROBE_TALLY \
           PROBE_READINGS CAPTURE_EXIT CAPTURE_FRAMES BASELINE_EXIT BASELINE VISUAL_EXIT VISUAL; do
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
grep -q "汇总：4 刀 CAUGHT / 1 逃掉 / 0 没跑成" "$LOG/battery.log" || FAILS="$FAILS 电池不是 4CAUGHT+M509故意逃"
# 本轮**唯一不许退让**的一条：在屏那一卷必须跑到 10 条结论（修僵尸探针就是为了这个）。
# 挂死（executed 空/小于 10）就是本轮的修法没生效，比任何断言红都严重。
[ "${PROBE_EXECUTED:-0}" -ge 10 ] 2>/dev/null || FAILS="$FAILS 在屏卷仍没跑完(executed=${PROBE_EXECUTED:-0})"
# 那条红必须是**有名字的**一条（BACKLOG 127），不许是两条以上、也不许是挂死。
[ "${PROBE_FAILED:-9}" = "1" ] || FAILS="$FAILS 在屏卷红数不是 1（failed=${PROBE_FAILED:-?}）"

echo
cat "$SUM"
if [ -n "$FAILS" ]; then
  echo "VERIFY_FAILED=$FAILS" | tee -a "$SUM"
  exit 1
fi
echo "VERIFY_OK=1（注意：在屏那一卷带着 1 条有名字的红 = BACKLOG 127，这是本轮想要的形状）" | tee -a "$SUM"
