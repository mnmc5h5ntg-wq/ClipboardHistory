#!/usr/bin/env bash
# R292 第二跑：第一跑的全量卷里有一颗计时预算红（PerfBudgetTests 500.24ms > 250ms），
# 成因先按 304 那一族处理 —— 那一跑期间我自己在本机并跑了嵌套电池（两支 540 颗的 python 卷），
# 是我给它添的负载。规矩：先隔离复跑那颗，通过才准重跑四件套；地板一条不放宽。
set -uo pipefail
cd /Users/wangziyi/Codex_Project0 || exit 2
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
echo "[A] 隔离复跑那颗计时预算红"
(cd ClipboardHistory && swift test --filter 'PerfBudgetTests/testImageComparisonCostStaysBounded') > /tmp/r292_perf_isolation.log 2>&1
A=$?
grep -a 'Executed 1 test' /tmp/r292_perf_isolation.log | tail -1
if [ $A -ne 0 ]; then echo "RERUN_REFUSED 隔离复跑仍红 ⇒ 这不是负载，是真回归（304 不许登记）"; exit 2; fi
echo "[B] 四件套第二跑（期间不再并跑任何卷）"
rm -rf /tmp/r292_verify
bash scripts/round_verify.sh /tmp/r292_verify > /tmp/r292_verify_run1.log 2>&1
grep -a '^ROUND_VERIFY ' /tmp/r292_verify_run1.log | tail -1
grep -qa 'swift_failures=0' /tmp/r292_verify_run1.log || { echo "RERUN_REFUSED 第二跑仍不是 0 failures"; exit 2; }
echo "[C] 交给收尾链"
bash .scratch/motion-audit-2/ship_r292.sh
