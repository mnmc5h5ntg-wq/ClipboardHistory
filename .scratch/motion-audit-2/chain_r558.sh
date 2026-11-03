#!/bin/zsh
# R558 验证链（顺序不许换）：四把刀 → 重捕帧+对账 → 全量 → 预检三读
set -u
cd /Users/wangziyi/Codex_Project0

for K in label_hard_cut sandwich_no_margin sandwich_one_sided borrowed_red_returns; do
  echo "=== KNIFE mutate_r558_$K ==="
  python3 ".scratch/motion-audit-2/mutate_r558_$K.py" > "/tmp/r558-knife-$K.log" 2>&1
  echo "EXIT=$?"
  grep -a -E "^预检:|^M14[0-9][0-9]:|RESTORE_CLEAN|needle 命中" "/tmp/r558-knife-$K.log" | head -4
done

echo "=== CAPTURE VOLUME (重捕帧) ==="
mkdir -p /tmp/r558-frames2
cd ClipboardHistory
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r558-frames2 swift test --filter "UICaptureTests" > /tmp/r558-capture2.log 2>&1
echo "CAPTURE_EXIT=$?"
grep -a -E "Executed [0-9]+ tests, with" /tmp/r558-capture2.log | tail -1
cd ..

echo "=== FRAME BASELINE 对账 ==="
python3 scripts/frame_baseline.py compare /tmp/r558-frames2 --against working > /tmp/r558-compare2.log 2>&1
echo "COMPARE_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r558-compare2.log | head -6

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r558-full2.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r558-full2.log | tail -2
cd ..

echo "=== PRECHECK 三读 ==="
python3 .scratch/motion-audit-2/mutate_needle_precheck.py > /tmp/r558-precheck3.log 2>&1
echo "PRECHECK_EXIT=$?"
grep -a -E "NEEDLE_PRECHECK|ARM_TOTAL" /tmp/r558-precheck3.log | tail -2
python3 scripts/hidden_arms.py > /tmp/r558-hidden3.log 2>&1
grep -a -E "HIDDEN_ARMS" /tmp/r558-hidden3.log | tail -1
echo "=== CHAIN DONE ==="
