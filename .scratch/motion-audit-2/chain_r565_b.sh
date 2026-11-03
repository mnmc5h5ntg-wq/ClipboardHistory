#!/bin/zsh
# R565 补段验证链（顺序不许换）：build 告警 → 判据卷（重捕帧）→ 帧基线对账 → 全量 → 预检三读（串行）
# 与 chain_r565.sh 同一形状，只是日志与帧目录换成 -补 后缀。
# 换装这一格本轮**跳过并具名**：这一段产品 0 文件（只动 Tests/scripts），装在跑的那一份
# 已经是 A 笔 f6c2a1d 的包 ⇒ 换装没有对象，而重装会打断用户正在用的那一扇窗。
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== BUILD ==="
cd ClipboardHistory
swift build --build-tests > /tmp/r565-补-build.log 2>&1
echo "BUILD_EXIT=$?"
grep -ac "warning:" /tmp/r565-补-build.log | sed 's/^/BUILD_WARNINGS=/'
grep -ac "error:" /tmp/r565-补-build.log | sed 's/^/BUILD_ERRORS=/'

echo "=== CAPTURE VOLUME ==="
mkdir -p /tmp/r565-补-frames
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r565-补-frames swift test --filter "UICaptureTests" > /tmp/r565-补-capture.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r565-补-capture.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账 ==="
python3 scripts/frame_baseline.py compare /tmp/r565-补-frames --against working > /tmp/r565-补-compare.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r565-补-compare.log | head -6

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r565-补-full.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r565-补-full.log | tail -2
cd ..

echo "=== PRECHECK 三读（串行）==="
python3 .scratch/motion-audit-2/mutate_needle_precheck.py > /tmp/r565-补-precheck.log 2>&1
echo "PRECHECK_EXIT=$?"
grep -a -E "NEEDLE_PRECHECK|ARM_TOTAL" /tmp/r565-补-precheck.log | tail -2
grep -a -E "bad=[1-9]|BAD " /tmp/r565-补-precheck.log | tail -3
python3 scripts/hidden_arms.py > /tmp/r565-补-hidden.log 2>&1
echo "HIDDEN_EXIT=$?"
grep -a -E "HIDDEN_ARMS" /tmp/r565-补-hidden.log | tail -1
echo "=== CHAIN DONE ==="
