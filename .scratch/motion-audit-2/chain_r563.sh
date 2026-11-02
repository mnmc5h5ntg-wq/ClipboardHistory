#!/bin/zsh
# R563 验证链：build 告警 → 判据卷（重捕帧）→ 帧基线对账 → 全量 → 预检三读（串行）
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== BUILD ==="
cd ClipboardHistory
swift build --build-tests > /tmp/r563-build.log 2>&1
echo "BUILD_EXIT=$?"
grep -ac "warning:" /tmp/r563-build.log | sed 's/^/BUILD_WARNINGS=/'
grep -ac "error:" /tmp/r563-build.log | sed 's/^/BUILD_ERRORS=/'

echo "=== CAPTURE VOLUME ==="
mkdir -p /tmp/r563-frames
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r563-frames swift test --filter "UICaptureTests" > /tmp/r563-capture.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r563-capture.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账 ==="
python3 scripts/frame_baseline.py compare /tmp/r563-frames --against working > /tmp/r563-compare.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r563-compare.log | head -6

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r563-full.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r563-full.log | tail -2
cd ..

echo "=== PRECHECK 三读（串行）==="
python3 .scratch/motion-audit-2/mutate_needle_precheck.py > /tmp/r563-precheck3.log 2>&1
echo "PRECHECK_EXIT=$?"
grep -a -E "NEEDLE_PRECHECK|ARM_TOTAL" /tmp/r563-precheck3.log | tail -2
python3 scripts/hidden_arms.py > /tmp/r563-hidden3.log 2>&1
grep -a -E "HIDDEN_ARMS" /tmp/r563-hidden3.log | tail -1
echo "=== CHAIN DONE ==="
