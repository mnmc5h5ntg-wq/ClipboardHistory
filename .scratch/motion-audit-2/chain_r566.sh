#!/bin/zsh
# R566 验证链（顺序不许换）：build 告警 → 判据卷（重捕帧）→ 帧基线对账 → 全量
# 换装在本链之前已经做过（这一轮的靶就是签名/换装本身），日志 /tmp/r566-install.log。
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== BUILD ==="
cd ClipboardHistory
swift build --build-tests > /tmp/r566-build.log 2>&1
echo "BUILD_EXIT=$?"
grep -ac "warning:" /tmp/r566-build.log | sed 's/^/BUILD_WARNINGS=/'
grep -ac "error:" /tmp/r566-build.log | sed 's/^/BUILD_ERRORS=/'

echo "=== CAPTURE VOLUME ==="
mkdir -p /tmp/r566-frames
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r566-frames swift test --filter "UICaptureTests" > /tmp/r566-capture.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r566-capture.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账（本段不 update，见 BACKLOG 640）==="
python3 scripts/frame_baseline.py compare /tmp/r566-frames --against working > /tmp/r566-compare.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r566-compare.log | head -6

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r566-full.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r566-full.log | tail -2
cd ..
echo "=== CHAIN DONE ==="
