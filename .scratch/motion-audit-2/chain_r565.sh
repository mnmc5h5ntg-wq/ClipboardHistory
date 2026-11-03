#!/bin/zsh
# R565 验证链（顺序不许换）：build 告警 → 判据卷（重捕帧）→ 帧基线对账 → 全量 → 预检三读（串行）
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== BUILD ==="
cd ClipboardHistory
swift build --build-tests > /tmp/r565-chain-build.log 2>&1
echo "BUILD_EXIT=$?"
grep -ac "warning:" /tmp/r565-chain-build.log | sed 's/^/BUILD_WARNINGS=/'
grep -ac "error:" /tmp/r565-chain-build.log | sed 's/^/BUILD_ERRORS=/'

echo "=== CAPTURE VOLUME ==="
mkdir -p /tmp/r565-frames
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r565-frames swift test --filter "UICaptureTests" > /tmp/r565-chain-capture.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r565-chain-capture.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账 ==="
python3 scripts/frame_baseline.py compare /tmp/r565-frames --against working > /tmp/r565-chain-compare.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r565-chain-compare.log | head -6

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r565-chain-full.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r565-chain-full.log | tail -2
cd ..

echo "=== PRECHECK 三读（串行）==="
python3 .scratch/motion-audit-2/mutate_needle_precheck.py > /tmp/r565-chain-precheck.log 2>&1
echo "PRECHECK_EXIT=$?"
grep -a -E "NEEDLE_PRECHECK|ARM_TOTAL" /tmp/r565-chain-precheck.log | tail -2
grep -a -E "bad=|BAD" /tmp/r565-chain-precheck.log | tail -3
python3 scripts/hidden_arms.py > /tmp/r565-chain-hidden.log 2>&1
echo "HIDDEN_EXIT=$?"
grep -a -E "HIDDEN_ARMS" /tmp/r565-chain-hidden.log | tail -1
echo "=== CHAIN DONE ==="
