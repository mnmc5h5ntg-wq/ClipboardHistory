#!/bin/zsh
# R559 验证链（顺序不许换）：重捕帧 → 帧基线对账 → 全量 → 预检三读
# 判据与四把刀已经跑过（见 /tmp/r559-knife-*.log），这一段从"重捕"开始。
# 规矩：预检必须串行（它自己起 swift，和别的 swift 卷并行会撞锁假报 NOT_RUN_TIMEOUT）。
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== CAPTURE VOLUME (重捕帧 + 兄弟判据读数) ==="
mkdir -p /tmp/r559-frames
cd ClipboardHistory
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r559-frames swift test --filter "UICaptureTests" > /tmp/r559-capture.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r559-capture.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账 ==="
python3 scripts/frame_baseline.py compare /tmp/r559-frames --against working > /tmp/r559-compare.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE|CHANGED" /tmp/r559-compare.log | head -8

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r559-full.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r559-full.log | tail -2
cd ..

echo "=== PRECHECK 三读（串行）==="
python3 .scratch/motion-audit-2/mutate_needle_precheck.py > /tmp/r559-precheck.log 2>&1
echo "PRECHECK_EXIT=$?"
grep -a -E "NEEDLE_PRECHECK|ARM_TOTAL" /tmp/r559-precheck.log | tail -2
python3 scripts/hidden_arms.py > /tmp/r559-hidden.log 2>&1
grep -a -E "HIDDEN_ARMS" /tmp/r559-hidden.log | tail -1
echo "=== CHAIN DONE ==="
