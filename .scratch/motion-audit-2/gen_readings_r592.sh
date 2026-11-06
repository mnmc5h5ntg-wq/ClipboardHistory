#!/bin/bash
# R592 收尾用的读数生成：守卫 CLI + 通道五读 + 全量/捕获汇总 + 计数与 numstat。
# 全部现读，不许手填；任何一步失败就打印 rc，台账那一格会因"读数缺失"当场报错。
# 与 R591 那一版的差别只有一处：本轮**动了产品**，所以 numstat 与计数名册要覆盖产品树与新卷。
set -u
cd /Users/wangziyi/Codex_Project0
T=/tmp/r592
FR=/tmp/r592v2/frames
mkdir -p $T

PYTHONUTF8=1 python3 scripts/tier_reporting_shape.py > $T/tier_shape.txt 2>&1;  echo "tier rc=$?"
PYTHONUTF8=1 python3 scripts/stage_gate_claims.py    > $T/stage_gate.txt 2>&1;  echo "stage rc=$?"
CLIPBOARD_HISTORY_UI_SHOTS=$FR PYTHONUTF8=1 python3 scripts/identical_frame_witness.py > $T/pair_witness.txt 2>&1; echo "pair rc=$?"
cp /tmp/r592v2/baseline.log $T/gate_local.txt;                                   echo "gate copied rc=$?"

{
  echo "CAPTURE_LINES=$(wc -l < /tmp/r592v2/capture.log | tr -d ' ')"
  echo "FRAMES=$(ls $FR/*.png 2>/dev/null | wc -l | tr -d ' ')"
  # 门打的是 `ROUND_WARNING_GATE warnings=N …` 这一行，不是逐行 `warning:`；
  # 而日志文件不在盘上时必须印 `not-run` —— 空值槽会被下一轮读成 0（R590 那一族：没读到 ≠ 没有）。
  WG="$(grep -h 'ROUND_WARNING_GATE' /tmp/r592_verify/*.log /tmp/r592_verify/warninggate-build/*.log 2>/dev/null | tail -1)"
  if [ -z "$WG" ]; then
    echo "BUILD_WARNINGS=not-run（门日志不在盘上 ⇒ 这一格没判，不许读成 0）"
  else
    echo "BUILD_WARNINGS=$(printf '%s' "$WG" | sed 's/.*warnings=\([0-9]*\).*/\1/') 门原文=$WG"
  fi
} > $T/capture_summary.txt

{
  echo "FULL_TOTAL=$(grep -oE 'Executed [0-9]+ tests' /tmp/r592_verify/full.log | tail -1)"
  echo "FULL_SKIPPED=$(grep -oE 'with [0-9]+ tests skipped' /tmp/r592_verify/full.log | tail -1)"
  grep -E "Test Suite 'All tests' (passed|failed)" /tmp/r592_verify/full.log | tail -1
} > $T/full_summary.txt

{
  # 取**那一行身份**而不是汇总行：`tail -1` 拿到的是 `N valid identities found`，它只答"几个"、不答"是哪个"。
  echo "IDENTITY=$(security find-identity -v -p codesigning 2>/dev/null | grep -E '^[[:space:]]*[0-9]+\)' | tr -s ' ' | tr '\n' ';') 汇总=$(security find-identity -v -p codesigning 2>/dev/null | tail -1 | tr -s ' ') 取值时刻=$(date '+%H:%M:%S')"
  git ls-remote origin HEAD > /dev/null 2>&1
  echo "PUSH=$(git remote get-url origin) ls-remote_rc=$? 取值时刻=$(date '+%H:%M:%S')"
  echo "GITHUB_HTTP=$(curl -s -o /dev/null -m 8 -w '%{http_code}' https://github.com)"
  echo "API_HTTP=$(curl -s -o /dev/null -m 8 -w '%{http_code}' https://api.github.com)"
  echo "HEAD=$(git rev-parse --short HEAD)"
  echo "ORIGIN=$(git rev-parse --short origin/main)"
  echo "AHEAD=$(git rev-list --count origin/main..HEAD)"
  # 门打的是 `ROUND_WARNING_GATE warnings=N …` 这一行，不是逐行 `warning:`；
  # 而日志文件不在盘上时必须印 `not-run` —— 空值槽会被下一轮读成 0（R590 那一族：没读到 ≠ 没有）。
  WG="$(grep -h 'ROUND_WARNING_GATE' /tmp/r592_verify/*.log /tmp/r592_verify/warninggate-build/*.log 2>/dev/null | tail -1)"
  if [ -z "$WG" ]; then
    echo "BUILD_WARNINGS=not-run（门日志不在盘上 ⇒ 这一格没判，不许读成 0）"
  else
    echo "BUILD_WARNINGS=$(printf '%s' "$WG" | sed 's/.*warnings=\([0-9]*\).*/\1/') 门原文=$WG"
  fi
} > $T/channels.txt

: > $T/test_counts.txt
for f in test_repo_root_bundle test_install_local test_ci_channel_hygiene test_ci_shape_guard_wiring; do
  h=$(git show HEAD:scripts/tests/$f.py 2>/dev/null | grep -c 'def test_')
  n=$(grep -c 'def test_' scripts/tests/$f.py)
  echo "$f HEAD=$h NOW=$n" >> $T/test_counts.txt
done
# 产品侧那一卷的格数（Swift 侧没有 HEAD 版本的新文件 ⇒ HEAD=0 是逐字现读，不是猜）
for f in FoldGeometryMigrationTests FoldGeometryReanchorTests; do
  h=$(git show HEAD:ClipboardHistory/Tests/ClipboardHistoryAppTests/$f.swift 2>/dev/null | grep -c 'func test')
  n=$(grep -c 'func test' ClipboardHistory/Tests/ClipboardHistoryAppTests/$f.swift)
  echo "$f HEAD=$h NOW=$n" >> $T/test_counts.txt
done

{ echo "== 仓库根那一格的末态"; python3 scripts/repo_root_bundle.py . --staged "$(python3 -c "import sys;sys.path.insert(0,'scripts');import repo_root_bundle as g;print(g.makefile_stage('.'))")"; echo "== 工作树里还留着的构建产物"; git status --short -- Makefile scripts/install_local.sh | head -5; } > $T/repo_root_state.txt

git diff --numstat HEAD -- scripts/ .github/workflows/ci.yml Makefile \
  ClipboardHistory/Sources ClipboardHistory/Tests > $T/numstat.txt

echo '--- capture:'; cat $T/capture_summary.txt
echo '--- full:';   cat $T/full_summary.txt
echo '--- channels:'; cat $T/channels.txt
echo '--- counts:'; cat $T/test_counts.txt
echo '--- pair/stage/tier:'; grep -E '^IDENTICAL_PAIRS|^WITNESS_SCAN_SCOPE' $T/pair_witness.txt | head -2; cat $T/stage_gate.txt | head -2; head -1 $T/tier_shape.txt
echo '--- gate_local:'; grep -E '^FRAME_BASELINE_(COMPARED|CHANGED|DRIFT|RESULT|MISSING)' $T/gate_local.txt | head -6
echo '--- repo_root_state:'; cat $T/repo_root_state.txt
