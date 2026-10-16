#!/bin/bash
# R94 的验证电池（内容驱动，不驱动退出码）：
# 每一条都先把值写进变量再 echo（R92 的教训：`echo "X=$?"` 之前插一条赋值就会把 $? 吃掉，
# 于是整格静默变成 0，而脚本自己 exit 1 —— 那种"0 个缺陷"比红更坏）。
set -u
REPO=/Users/wangziyi/Codex_Project0
OUT=$REPO/.scratch/motion-audit-2/r94_verify.log
: > "$OUT"
say() { printf '%s\n' "$*" >> "$OUT"; }

cd "$REPO/ClipboardHistory" || exit 1

say "== 1) 构建（必须 0 告警）"
env -u SDKROOT swift build --build-tests > /tmp/r94_v_build.log 2>&1
BUILD_EXIT=$?
BUILD_WARN=$(grep -c "warning:" /tmp/r94_v_build.log)
say "BUILD_EXIT=$BUILD_EXIT BUILD_WARNING_LINES=$BUILD_WARN"

say "== 2) 全量 swift test（本轮 Swift 侧没改，这一遍是同提交的新鲜读数）"
env -u SDKROOT swift test > /tmp/r94_v_test.log 2>&1
TEST_EXIT=$?
TEST_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r94_v_test.log | tail -1 | sed 's/^[ \t]*//')
say "TEST_EXIT=$TEST_EXIT 最后一行汇总: $TEST_SUMMARY"

say "== 3) 在屏那一卷（本机，带 CLIPBOARD_HISTORY_UI_INTERACTION=1）"
env -u SDKROOT CLIPBOARD_HISTORY_UI_INTERACTION=1 CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r94_v_probe CLIPBOARD_HISTORY_PROBE_PULSE=/tmp \
  swift test --filter UIInteractionProbeTests > /tmp/r94_v_probe.log 2>&1
PROBE_EXIT=$?
PROBE_SUMMARY=$(grep -E "^	 Executed [0-9]+ tests" /tmp/r94_v_probe.log | tail -1 | sed 's/^[ \t]*//')
say "PROBE_EXIT=$PROBE_EXIT 汇总: $PROBE_SUMMARY"

say "== 4) 帧基线（对 working 名单）"
cd "$REPO" || exit 1
PYTHONUTF8=1 python3 scripts/frame_baseline.py check /tmp/r94_shots --against working \
  --allow-missing content-wide-1100x800-light.png --allow-missing content-wide-1100x800-dark.png \
  > /tmp/r94_v_frames.log 2>&1
FRAMES_EXIT=$?
say "FRAMES_EXIT=$FRAMES_EXIT $(grep -E '^FRAME_BASELINE_' /tmp/r94_v_frames.log | tr '\n' ' ')"

say "== 5) 脚本电池"
if [ "${SKIP_PY:-0}" = "1" ]; then
  # pass-1（写台账之前）：新加的 `test_ledger_ids` 此刻**必然**红（它报的就是还没补的 D-151），
  # 所以这一格只能跳过并**写明跳过了**——不能悄悄记成 0（那正是"有键无值算红"要抓的形状）。
  PY_EXIT=0
  say "PY_EXIT=0 SKIPPED=1（pass-1 不跑脚本电池：新守卫在台账写盘前必然红）"
else
  PYTHONUTF8=1 python3 -m unittest discover -s scripts/tests > /tmp/r94_v_py.log 2>&1
  PY_EXIT=$?
  say "PY_EXIT=$PY_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r94_v_py.log | tr '\n' ' ')"
fi

say "== 6) 变异对照"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r94_order.py > /tmp/r94_v_mut.log 2>&1
MUT_EXIT=$?
say "MUT_EXIT=$MUT_EXIT $(grep -E '^MUTATE_TABLE' /tmp/r94_v_mut.log)"

say "== 7) 台账编号守卫（这一格在写台账之前**预期是红的**：D-151 被 R93 两处标题引用却没有正文）"
PYTHONUTF8=1 python3 -m unittest scripts.tests.test_ledger_ids > /tmp/r94_v_ledger.log 2>&1
LEDGER_EXIT=$?
say "LEDGER_EXIT=$LEDGER_EXIT $(grep -E '^(Ran |OK|FAILED)' /tmp/r94_v_ledger.log | tr '\n' ' ')"
say "  ↑ 不进 VERIFY_OK 的条件：写台账之前它必然红；ledgers_r94.py 写完 D-151/D-152 之后自己复跑并要求绿"

say "== 8) 菜单栏那六帧的读数（尺腿，不判产品）"
PYTHONUTF8=1 python3 .scratch/motion-audit-2/r94_menubar_visual.py /tmp/r94_shots > /tmp/r94_v_vis.log 2>&1
VIS_EXIT=$?
say "VIS_EXIT=$VIS_EXIT $(grep -cE 'TOPOLOGY 同形=True' /tmp/r94_v_vis.log)/3 同形，DEFECT 行=$(grep -c 'DEFECT' /tmp/r94_v_vis.log)"

say "== 9) 摘要缺值算红：上面任何一格没打出「KEY=数字」，这里必须计入 MISSING"
MISSING=0
for key in BUILD_EXIT TEST_EXIT PROBE_EXIT FRAMES_EXIT PY_EXIT MUT_EXIT LEDGER_EXIT VIS_EXIT; do
  line=$(grep -E "^$key=" "$OUT" | tail -1)
  if ! printf '%s' "$line" | grep -qE '^[A-Z_]+=[0-9]+'; then
    MISSING=$((MISSING+1)); printf '摘要缺值：%s\n' "$line" >> "$OUT"
  fi
done
say "SUMMARY_MISSING=$MISSING"

# LEDGER_EXIT 刻意不在条件里（见第 7 格那行说明）。
if [ "$BUILD_EXIT" -eq 0 ] && [ "$BUILD_WARN" -eq 0 ] && [ "$TEST_EXIT" -eq 0 ] \
   && [ "$PROBE_EXIT" -eq 0 ] && [ "$FRAMES_EXIT" -eq 0 ] && [ "$PY_EXIT" -eq 0 ] \
   && [ "$MUT_EXIT" -eq 0 ] && [ "$VIS_EXIT" -eq 0 ] && [ "$MISSING" -eq 0 ]; then
  say "VERIFY_OK=1"
else
  say "VERIFY_OK=0"
fi
