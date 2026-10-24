#!/bin/bash
# R336 下半场的四条腿：两张变异表（本轮五把 + 上一轮十一把的回归）→ 重捕帧并对基线
# → 判据卷读数 → 四腿全量验证。
#
# 顺序是承重的：变异表会把针注进 Sources，绝不能与"捕帧/验证"同时在盘上跑。
# 还原是否干净**不由 git 判**（工作区本来就带着本轮那一笔未提交的产品改动），
# 由进入前/退出前的 diff 哈希对账 —— 上一版这里用 `git diff --quiet -- Sources` 判，
# 于是把自己的工作当成"还原不干净"，把验证腿挡掉了（那是假红，但更糟的是它会让人以为真脏了）。
set -u
cd /Users/wangziyi/Codex_Project0 || exit 1
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer

BEFORE=$(git diff -- ClipboardHistory/Sources | shasum | awk '{print $1}')
echo "SOURCES_DIFF_SHA_BEFORE=$BEFORE"

echo "[A] mutate_r336（本轮五把）"
PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 python3 .scratch/motion-audit-2/mutate_r336.py \
  > /tmp/r336_t_r336.log 2>&1
echo "LEG_A_EXIT=$?"; tail -1 /tmp/r336_t_r336.log | sed 's/^/LEG_A_LAST: /'

echo "[B] mutate_r335 回归（本轮动了同一个文件）"
PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 python3 .scratch/motion-audit-2/mutate_r335.py \
  > /tmp/r336_t_r335.log 2>&1
echo "LEG_B_EXIT=$?"; tail -1 /tmp/r336_t_r335.log | sed 's/^/LEG_B_LAST: /'

AFTER=$(git diff -- ClipboardHistory/Sources | shasum | awk '{print $1}')
echo "SOURCES_DIFF_SHA_AFTER=$AFTER"
if [ "$BEFORE" != "$AFTER" ]; then
  echo "LEG_RESTORE=MISMATCH ⇒ 停在这里（不许带着变异体跑验证腿）"
  git diff --stat -- ClipboardHistory/Sources
  exit 1
fi
echo "LEG_RESTORE=clean"

echo "[C] 重捕帧 + 对工作基线名单"
rm -rf /tmp/r336c_shots
( cd ClipboardHistory && CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r336c_shots \
  env -u SDKROOT swift test --filter UICaptureTests ) > /tmp/r336c_capture.log 2>&1
echo "LEG_C_EXIT=$?"
grep -a "CAPTURED" /tmp/r336c_capture.log | tail -1 | sed 's/^/LEG_C_CAP: /'
grep -a "^HTML_ALT_PARA\|^HTML_INKREAD .*html-rendered\|^HTML_PAIR_PROOF" /tmp/r336c_capture.log \
  | sed 's/^/LEG_C_ROW: /'
python3 scripts/frame_baseline.py check /tmp/r336c_shots --against working 2>&1 | tail -6 | sed 's/^/LEG_C_BASELINE: /'

echo "[D] 判据卷读数"
( cd ClipboardHistory && env -u SDKROOT swift test \
  --filter "HtmlPreviewPolicyTests|HtmlSanitizerTests|HtmlPreviewPipelineTests|PerfBudgetTests" ) \
  > /tmp/r336_html.log 2>&1
echo "LEG_D_EXIT=$?"
grep -c "^MD_RENDER_COST \|^HTML_ALT \|^HTML_ALT_BLOCK \|^HTML_SANITIZE \|^HTML_TYPE " /tmp/r336_html.log | sed 's/^/LEG_D_ROWS=/'
grep -E "Executed .* tests, with .* failures" /tmp/r336_html.log | tail -1 | sed 's/^/LEG_D_SUM: /'

echo "[E] 四腿全量验证 —— **不在这里跑**"
# 故意断开：帧基线要在看到"只有那两张 html 帧变了"之后**由人确认再 update**，
# 而 round_verify 的第 4 步现在是一道硬门（changed≠0 就停），把它接在同一条链尾
# 等于让链自己判自己失败。update 之后单独跑 round_verify。
echo "CHAIN2_DONE（下一步：核对 CHANGED 名单 → frame_baseline update → round_verify）"
