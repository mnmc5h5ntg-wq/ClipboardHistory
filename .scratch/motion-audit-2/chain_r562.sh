#!/bin/zsh
# R562 验证链第一段：判据卷（重捕帧 + 全类读数）→ 帧基线对账（**只 compare，不 update**）
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== CAPTURE VOLUME (重捕帧 + 兄弟判据读数) ==="
mkdir -p /tmp/r562-frames
cd ClipboardHistory
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r562-frames swift test --filter "UICaptureTests" > /tmp/r562-capture.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r562-capture.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账（update 之前）==="
python3 scripts/frame_baseline.py compare /tmp/r562-frames --against working > /tmp/r562-compare.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r562-compare.log | head -8
echo "=== CHAIN1 DONE ==="
