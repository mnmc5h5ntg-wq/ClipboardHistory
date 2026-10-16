#!/bin/bash
# R92 的验证（第 94 轮）。本轮动的是：
#  · 自检夹具覆盖作业共享 /tmp（修 + 三条新守卫 + 真值表）；
#  · 捕获闸门"没跑到用例"那句假成因（改成三支，标准一字未动）；
#  · 产品：设置窗口「数据」分区的分组语言（三段全进一张卡片，两条线挪进卡片内）。
#
# 沿用 R90/R91 的三条自己的规矩：
#  · 退出码由**内容**决定，不由最后一条命令决定（U-200 那一族，R91 又犯过一次）；
#  · 摘要里"有键无值"算红；
#  · 脚本一旦开跑就不许边跑边改（bash 边读边执行）；
#  · `set -u` 下 `echo "X=$?" >> 摘要` 只把数写进文件、**没有**留下 shell 变量，
#    末尾那一段判红再读 `$X` 就是 unbound（本轮第一次跑就是这么死的，verify_exit=1
#    而所有单项其实都是 0 —— 一个坏在收尾的验证脚本比没有脚本更糟，因为它会教人去看摘要而不是看退出码）。
set -u
REPO=/Users/wangziyi/Codex_Project0
LOG=/tmp/r92_verify
SUM=$LOG/summary.log
rm -rf "$LOG"; mkdir -p "$LOG"

echo "=== 动了哪些非台账文件 ==="
git -C "$REPO" status --porcelain | awk '{print $2}' \
  | grep -v '^AGENT_\|^CHANGELOG\|^\.scratch' > "$LOG/touched.txt"
cat "$LOG/touched.txt"
TOUCHED=$(wc -l < "$LOG/touched.txt" | tr -d ' ')
echo "TOUCHED_NON_LEDGER=$TOUCHED" >> "$SUM"
if grep -q '^ClipboardHistory/Sources/' "$LOG/touched.txt"; then
  echo "PRODUCT_TOUCHED=1（本轮确实改了产品：数据页容器）" >> "$SUM"
else
  echo "PRODUCT_TOUCHED=0" >> "$SUM"
fi

echo "=== 本轮的头条：自检跑完之后，作业共享 /tmp 里那四份日志必须一个都没被碰 ==="
for p in /tmp/frames.log /tmp/ui.log /tmp/motion.log /tmp/build.log; do
  printf 'R92-HERMETIC-MARKER %s\n' "$p" > "$p"
done
( cd "$REPO" && python3 -m unittest discover -s scripts/tests ) > "$LOG/py.log" 2>&1
PY_EXIT=$?
echo "PY_EXIT=$PY_EXIT" >> "$SUM"
grep -aE "^Ran [0-9]+ tests|^OK$|^FAILED" "$LOG/py.log" | tr '\n' ' ' | sed 's/^/SCRIPT_TESTS=/' >> "$SUM"
echo >> "$SUM"
SURVIVED=0
for p in /tmp/frames.log /tmp/ui.log /tmp/motion.log /tmp/build.log; do
  if grep -qa 'R92-HERMETIC-MARKER' "$p" 2>/dev/null; then SURVIVED=$((SURVIVED + 1)); fi
done
echo "HERMETIC_MARKERS_SURVIVED=$SURVIVED/4" >> "$SUM"

echo "=== 变异电池（六刀；M515 是故意要逃的那一刀 = 已知盲区）==="
( cd "$REPO" && PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r92_clobber.py ) > "$LOG/battery.log" 2>&1
BATTERY_EXIT=$?
echo "BATTERY_EXIT=$BATTERY_EXIT" >> "$SUM"
grep -aE "^汇总" "$LOG/battery.log" | sed 's/^/BATTERY=/' >> "$SUM"
grep -aE "^   预期 .* 实际" "$LOG/battery.log" | sed 's/^/BATTERY_MISMATCH=/' >> "$SUM"

echo "=== 构建（必须 0 告警）==="
( cd "$REPO/ClipboardHistory" && env -u SDKROOT swift build --build-tests ) > "$LOG/build.log" 2>&1
BUILD_EXIT=$?
echo "BUILD_EXIT=$BUILD_EXIT" >> "$SUM"
echo "BUILD_WARNINGS=$(grep -cE 'warning:' "$LOG/build.log" | tr -d ' ')" >> "$SUM"

echo "=== 全量 Swift 测试 ==="
( cd "$REPO/ClipboardHistory" && env -u SDKROOT swift test ) > "$LOG/full.log" 2>&1
SWIFT_TEST_EXIT=$?
echo "SWIFT_TEST_EXIT=$SWIFT_TEST_EXIT" >> "$SUM"
grep -aE "Executed [0-9]+ tests" "$LOG/full.log" | tail -2 | tr -s ' \t' ' ' \
  | tr '\n' '|' | sed 's/^/SWIFT_TEST_TAIL=/' >> "$SUM"
echo >> "$SUM"

echo "=== 捕获卷重跑一遍 + 帧基线（改完产品必须重新对账）==="
rm -rf /tmp/r92_verify_shots; mkdir -p /tmp/r92_verify_shots
( cd "$REPO/ClipboardHistory" && CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r92_verify_shots \
    env -u SDKROOT swift test --filter UICaptureTests ) > "$LOG/capture.log" 2>&1
CAPTURE_EXIT=$?
echo "CAPTURE_EXIT=$CAPTURE_EXIT" >> "$SUM"
grep -aE "Executed [0-9]+ tests" "$LOG/capture.log" | tail -1 | tr -s ' \t' ' ' \
  | sed 's/^/CAPTURE_TAIL=/' >> "$SUM"
( cd "$REPO/ClipboardHistory" && python3 ../scripts/frame_baseline.py check /tmp/r92_verify_shots \
    --against working --allow-missing content-wide-1100x800-light.png \
    --allow-missing content-wide-1100x800-dark.png ) > "$LOG/baseline.log" 2>&1
BASELINE_EXIT=$?
echo "BASELINE_EXIT=$BASELINE_EXIT" >> "$SUM"
grep -aE "^FRAME_BASELINE_" "$LOG/baseline.log" | tr '\n' ' ' | sed 's/^/BASELINE=/' >> "$SUM"
echo >> "$SUM"

echo "=== 数据页那把尺：改前 / 改后的关键读数（同一把尺，两份帧）==="
for pair in "before /tmp/r92_shots" "after /tmp/r92_shots_after"; do
  tag=${pair%% *}; dir=${pair##* }
  PYTHONUTF8=1 python3 "$REPO/.scratch/motion-audit-2/r92_data_visual.py" "$dir" \
    > "$LOG/visual_$tag.log" 2>&1
  grep -aE "卡片#1|分隔线=|Q2 最左|Q3 结论|PREMISE" "$LOG/visual_$tag.log" \
    | head -4 | tr '\n' '@' | sed "s/^/VISUAL_${tag}=/; s/@$//" >> "$SUM"
  echo >> "$SUM"
done

echo "=== 在屏那一卷今天不跑（R91 已量：删掉僵尸之后本机 13.8 秒跑到 10 条结论）==="
echo "NOT_RUN=1 在屏探针卷本轮没重跑：本轮没动 Tests/UIInteractionProbeTests.swift，" \
     "而它的产物是 CI 的读数而不是本机读数（R91 的 10 条结论已在台账）" >> "$SUM"
echo "NOT_RUN=2 「清空」那颗在真机 key 窗口里红不红：这条通道 appActive=false 判不了 ⇒ BACKLOG 130" >> "$SUM"
echo "NOT_RUN=3 统计页那套分组（0 卡片 + 1 条外线）本轮没并入 ⇒ BACKLOG 131" >> "$SUM"
echo "NOT_RUN=4 暗档侧栏逐行图标/标签：已结案的捕获通道盲区（BACKLOG 116/123），本轮未写新阈值" >> "$SUM"
echo "NOT_RUN=5 悬停/按下态这一屏：需要真机或 key 窗口，本轮未做" >> "$SUM"

echo "=== 摘要必须每个键都有值（'有键无值'算红）==="
MISSING=0
for k in TOUCHED_NON_LEDGER PRODUCT_TOUCHED PY_EXIT SCRIPT_TESTS HERMETIC_MARKERS_SURVIVED \
         BATTERY_EXIT BATTERY BUILD_EXIT BUILD_WARNINGS SWIFT_TEST_EXIT SWIFT_TEST_TAIL \
         CAPTURE_EXIT CAPTURE_TAIL BASELINE_EXIT BASELINE; do
  line=$(grep "^${k}=" "$SUM" || true)
  case "$line" in
    "${k}="|"${k}= ") echo "摘要缺值：$line"; MISSING=1;;
    "") echo "摘要没有这个键：$k"; MISSING=1;;
  esac
done
echo "SUMMARY_MISSING=$MISSING" >> "$SUM"

echo "================ 摘要 ================"
cat "$SUM"

OK=1
[ "$PY_EXIT" = "0" ] || { echo "红：脚本自测非 0"; OK=0; }
[ "$BUILD_EXIT" = "0" ] || { echo "红：构建非 0"; OK=0; }
[ "$(grep -c '^BUILD_WARNINGS=0$' "$SUM")" = "1" ] || { echo "红：构建有告警"; OK=0; }
[ "$SWIFT_TEST_EXIT" = "0" ] || { echo "红：全量 Swift 测试非 0"; OK=0; }
[ "$CAPTURE_EXIT" = "0" ] || { echo "红：捕获卷非 0"; OK=0; }
[ "$(grep -c 'FRAME_BASELINE_CHANGED=0' "$LOG/baseline.log")" = "1" ] || { echo "红：帧基线有 CHANGED"; OK=0; }
[ "$(grep -c 'FRAME_BASELINE_MISSING=0' "$LOG/baseline.log")" = "1" ] || { echo "红：帧基线有 MISSING"; OK=0; }
[ "$(grep -c 'HERMETIC_MARKERS_SURVIVED=4/4' "$SUM")" = "1" ] || { echo "红：自检仍然覆盖了共享 /tmp 的日志"; OK=0; }
[ "$BATTERY_EXIT" = "0" ] || { echo "红：变异电池有'预期不符'或'没跑成'"; OK=0; }
[ "$MISSING" = "0" ] || { echo "红：摘要里有键没值"; OK=0; }
if [ "$OK" = "1" ]; then
  echo "VERIFY_OK=1（注意：在屏那一卷本轮没跑，见 NOT_RUN=1；「清空」的红那一档判不了，见 NOT_RUN=2）"
else
  echo "VERIFY_OK=0"
fi
[ "$OK" = "1" ]
