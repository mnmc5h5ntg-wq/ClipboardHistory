#!/bin/bash
# R336 的三条腿按顺序跑：判据卷读数 → 上一轮那十一把刀的回归 → 四腿全量验证。
# 顺序是承重的：变异表会把针注进 Sources，绝不能与 round_verify 同时在盘上跑。
# 每一腿的日志单独落盘，退出码单独打，方便事后按腿归因。
set -u
cd /Users/wangziyi/Codex_Project0/ClipboardHistory || exit 1
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer

echo "[A] 判据卷（HTML 四格 + Markdown 耗时）"
env -u SDKROOT swift test --filter "HtmlPreviewPolicyTests|HtmlSanitizerTests|HtmlPreviewPipelineTests|PerfBudgetTests" \
  > /tmp/r336_html.log 2>&1
echo "LEG_A_EXIT=$?"
grep -c "^MD_RENDER_COST \|^HTML_ALT \|^HTML_SANITIZE \|^HTML_TYPE " /tmp/r336_html.log | sed 's/^/LEG_A_ROWS=/'
tail -4 /tmp/r336_html.log | grep -E "Executed|failures" | sed 's/^/LEG_A_SUMMARY: /'

cd /Users/wangziyi/Codex_Project0 || exit 1
echo "[B] mutate_r335 回归（本轮动了同一个文件）"
PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 python3 .scratch/motion-audit-2/mutate_r335.py \
  > /tmp/r336_t_r335.log 2>&1
echo "LEG_B_EXIT=$?"
tail -1 /tmp/r336_t_r335.log | sed 's/^/LEG_B_LAST: /'
if ! git diff --quiet -- ClipboardHistory/Sources; then
  echo "LEG_B_SOURCES_DIRTY ⇒ 还原不干净，停在这里（不许带着变异体跑验证腿）"
  git diff --stat -- ClipboardHistory/Sources
  exit 1
fi
echo "LEG_B_RESTORE=clean"

echo "[C] 四腿全量验证（新目录，帧不复用）"
bash scripts/round_verify.sh /tmp/r336b_rv > /tmp/r336b_rv_driver.log 2>&1
echo "LEG_C_EXIT=$?"
tail -1 /tmp/r336b_rv/ROUND_VERIFY.log | sed 's/^/LEG_C_LINE: /'
echo "CHAIN_DONE"
