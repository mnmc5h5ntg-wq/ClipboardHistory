#!/bin/zsh
# R560 验证链（顺序不许换）：重捕帧 + 判据卷 → 帧基线对账 → 全量 → 预检三读（串行）
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== CAPTURE VOLUME (重捕帧 + 兄弟判据读数) ==="
mkdir -p /tmp/r560-frames
cd ClipboardHistory
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r560-frames swift test --filter "UICaptureTests" > /tmp/r560-capture.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r560-capture.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账 ==="
python3 scripts/frame_baseline.py compare /tmp/r560-frames --against working > /tmp/r560-compare.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE|changed|missing|added" /tmp/r560-compare.log | head -12

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r560-full.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r560-full.log | tail -2
cd ..

echo "=== PRECHECK 三读（串行）==="
python3 .scratch/motion-audit-2/mutate_needle_precheck.py > /tmp/r560-precheck3.log 2>&1
echo "PRECHECK_EXIT=$?"
grep -a -E "NEEDLE_PRECHECK|ARM_TOTAL" /tmp/r560-precheck3.log | tail -2
python3 scripts/hidden_arms.py > /tmp/r560-hidden3.log 2>&1
grep -a -E "HIDDEN_ARMS" /tmp/r560-hidden3.log | tail -1
echo "=== CHAIN DONE ==="
