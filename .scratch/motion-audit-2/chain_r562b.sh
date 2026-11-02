#!/bin/zsh
# R562 验证链第二段：帧基线 update（与台账同一笔提交）→ 复跑对账 → 全量卷 → 预检三读（串行）
set -u
cd /Users/wangziyi/Codex_Project0

echo "=== FRAME BASELINE update ==="
python3 scripts/frame_baseline.py update /tmp/r562-frames --against working > /tmp/r562-update.log 2>&1
echo "UPDATE_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r562-update.log | head -6

echo "=== FRAME BASELINE 复跑对账（update 之后）==="
python3 scripts/frame_baseline.py compare /tmp/r562-frames --against working > /tmp/r562-compare2.log 2>&1
echo "COMPARE2_EXIT=$?"
grep -a -E "FRAME_BASELINE" /tmp/r562-compare2.log | head -6

echo "=== FULL SUITE ==="
cd ClipboardHistory
swift test > /tmp/r562-full.log 2>&1
echo "FULL_EXIT=$?"
grep -a -E "Executed [0-9]{4} tests, with [0-9]+ (tests )?skipped" /tmp/r562-full.log | tail -2
cd ..

echo "=== PRECHECK 三读（串行）==="
python3 .scratch/motion-audit-2/mutate_needle_precheck.py > /tmp/r562-precheck3.log 2>&1
echo "PRECHECK_EXIT=$?"
grep -a -E "NEEDLE_PRECHECK|ARM_TOTAL" /tmp/r562-precheck3.log | tail -2
python3 scripts/hidden_arms.py > /tmp/r562-hidden3.log 2>&1
grep -a -E "HIDDEN_ARMS" /tmp/r562-hidden3.log | tail -1
echo "=== CHAIN2 DONE ==="
