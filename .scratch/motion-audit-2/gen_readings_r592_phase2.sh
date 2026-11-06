#!/bin/bash
# R592 收尾读数（第二阶段）：捕获之后、全量之前能现读的那几格。
# 与 gen_readings_r592.sh 同一套规矩：全部现读、失败就打印 rc，台账那一格会因"读数缺失"当场报错。
set -u
cd /Users/wangziyi/Codex_Project0
T=/tmp/r592
FR=/tmp/r592v3
mkdir -p $T

# ① 产品文件数：本轮正文写的是"产品轮"，那一格必须由 git 现读，不许我手抄
{
  n=$(git status --porcelain -- ClipboardHistory/Sources | wc -l | tr -d ' ')
  echo "PROD_FILES=$n"
  git status --porcelain -- ClipboardHistory/Sources | sed 's/^/  /'
} > $T/prod_stat.txt

# ② 捕获卷汇总（帧数按盘上 png 现数，不抄测试自己打的数）
{
  echo "CAPTURE_LINES=$(wc -l < $FR/capture.log | tr -d ' ')"
  echo "FRAMES=$(ls $FR/*.png 2>/dev/null | wc -l | tr -d ' ')"
  # 门打的是 `ROUND_WARNING_GATE warnings=N …` 这一行，不是逐行 `warning:`；
  # 而日志文件不在盘上时必须印 `not-run` —— 空值槽会被下一轮读成 0（R590 那一族：没读到 ≠ 没有）。
  WG="$(grep -h 'ROUND_WARNING_GATE' /tmp/r592_verify/*.log /tmp/r592_verify/warninggate-build/*.log 2>/dev/null | tail -1)"
  if [ -z "$WG" ]; then
    echo "BUILD_WARNINGS=not-run（门日志不在盘上 ⇒ 这一格没判，不许读成 0）"
  else
    echo "BUILD_WARNINGS=$(printf '%s' "$WG" | sed 's/.*warnings=\([0-9]*\).*/\1/') 门原文=$WG"
  fi
  grep -E "Executed 233 tests" $FR/capture.log | tail -1
} > $T/capture_summary.txt

# ③ 本机那一门（帧基线 compare 的原文，含 changed 的逐张清单）
python3 scripts/frame_baseline.py compare $FR --against working > $T/baseline.log 2>&1; echo "gate rc=$?"
cp $T/baseline.log $T/gate_local.txt

# ④ 副本名册那一门（按机器登记，帧目录用本轮那一批）
CLIPBOARD_HISTORY_UI_SHOTS=$FR PYTHONUTF8=1 python3 scripts/identical_frame_witness.py > $T/pair_witness.txt 2>&1; echo "pair rc=$?"

# ⑤ 看图那一腿：本轮 vs 上一批（串行，绝不并发）
LOOK_NOW=$FR LOOK_PREV=/tmp/r592v2/frames LOOK_OUT=$T/look.txt PYTHONUTF8=1 \
  python3 .scratch/motion-audit-2/look_r590.py > $T/look_stdout.txt 2>&1; echo "look rc=$?"

# ⑥ 三道预检（串行）
{
  echo "== 1 刀针预检 $(date '+%H:%M:%S')"
  PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_needle_precheck.py 2>&1 | grep -E "^NEEDLE_PRECHECK|^ARM_TOTAL"
  echo "== 2 清账门"
  PYTHONUTF8=1 python3 scripts/ledger_absence_claims.py 2>&1 | grep -E "^LEDGER_ABSENCE"
  echo "== 3 红名对账（落盘前那一趟，落盘之后由 --post-land 复算）"
  PYTHONUTF8=1 python3 scripts/red_name_reconciliation.py 2>&1 | head -2
} > $T/prechecks.txt

# ⑦ 计数名册：本轮新增/改动的三卷，HEAD 与 NOW 都现读
: > $T/test_counts.txt
for f in test_repo_root_bundle test_install_local; do
  h=$(git show HEAD:scripts/tests/$f.py 2>/dev/null | grep -c 'def test_')
  n=$(grep -c 'def test_' scripts/tests/$f.py)
  echo "$f HEAD=$h NOW=$n" >> $T/test_counts.txt
done
for f in FoldGeometryMigrationTests FoldGeometryReanchorTests; do
  h=$(git show HEAD:ClipboardHistory/Tests/ClipboardHistoryAppTests/$f.swift 2>/dev/null | grep -c 'func test')
  n=$(grep -c 'func test' ClipboardHistory/Tests/ClipboardHistoryAppTests/$f.swift)
  echo "$f HEAD=$h NOW=$n" >> $T/test_counts.txt
done

# ⑧ 其余守卫 CLI 的当轮读数
PYTHONUTF8=1 python3 scripts/tier_reporting_shape.py > $T/tier_shape.txt 2>&1; echo "tier rc=$?"
PYTHONUTF8=1 python3 scripts/stage_gate_claims.py    > $T/stage_gate.txt 2>&1; echo "stage rc=$?"
PYTHONUTF8=1 python3 scripts/ci_skipped_causes.py    > $T/causes.txt 2>&1;     echo "causes rc=$?"
PYTHONUTF8=1 python3 scripts/ci_channel_hygiene.py   > $T/hygiene.txt 2>&1;    echo "hygiene rc=$?"
grep -E '^CI_CHANNEL_GLUE_SCOPE' $T/hygiene.txt > $T/glue_scope.txt

echo '--- prod:'; cat $T/prod_stat.txt
echo '--- capture:'; cat $T/capture_summary.txt
echo '--- gate:'; grep -E '^FRAME_BASELINE_(COMPARED|CHANGED|MISSING|RESULT|DRIFT)' $T/gate_local.txt | head -6
echo '--- pair:'; grep -E '^IDENTICAL_PAIRS|^WITNESS_SCAN_SCOPE' $T/pair_witness.txt
echo '--- look:'; head -5 $T/look.txt
echo '--- prechecks:'; cat $T/prechecks.txt
echo '--- counts:'; cat $T/test_counts.txt
echo '--- stage/causes/glue:'; head -2 $T/stage_gate.txt; head -1 $T/causes.txt; cat $T/glue_scope.txt
