#!/bin/bash
# R245 的变异表执行器（BACKLOG 283 的答案）：**测试改在 shell 里跑**。
#
# 为什么换执行器：`swift test` / `python3 -m unittest` 经 python subprocess 起会撞上
#   error: 'clipboardhistory': Invalid manifest
# 今天四次复现，症状完全一致（rc=1、日志 21,663,809 字节），换 cwd（两条路径都不是符号链接）、
# 换 stdin（DEVNULL / PIPE）、套 bash -lc、套 script 伪 tty 都无效；而**同一条命令在 shell 里 rc=0**。
# 所以这不是判据坏，是"跑判据的那条路"坏。基线不可信的表不配出结论 ⇒ 与其把没跑成的刀记成
# ESCAPED（那是假绿的一种），不如换执行器重跑。
#
# 规矩照旧：needle 整串字面、命中恰好一次（arm_patch.py 把关）；跑完逐字节还原并 verify；
# 每种 runner 的基线先跑一次，不绿 ⇒ 整表拒绝出（exit 1）。
set -u
ROOT=/Users/wangziyi/Codex_Project0
MANI="$ROOT/.scratch/motion-audit-2/arms_r245/manifest.tsv"
PATCH="$ROOT/.scratch/motion-audit-2/arm_patch.py"
SWIFT_FILTER='UICaptureTests/testModeChipHoverFillIsVisibleOnItsOwnSurface'
LOGDIR=/tmp/r245_arms
mkdir -p "$LOGDIR"

module_of() {
  case "$1" in
    scripts/tests/test_final_report_headline.py) echo scripts.tests.test_final_report_headline ;;
    scripts/tests/test_hover_two_state_diff.py)  echo scripts.tests.test_hover_two_state_diff ;;
    scripts/hover_two_state_diff.py)             echo scripts.tests.test_hover_two_state_diff ;;
    *) echo "" ;;
  esac
}

run_kind() {   # run_kind <kind> <rel> <日志文件> ；返回测试退出码
  local kind="$1" rel="$2" log="$3" rc
  if [ "$kind" = "swift" ]; then
    ( cd "$ROOT/ClipboardHistory" && swift test --filter "$SWIFT_FILTER" ) > "$log" 2>&1
    rc=$?
  else
    ( cd "$ROOT" && PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1 python3 -m unittest -v "$(module_of "$rel")" ) > "$log" 2>&1
    rc=$?
  fi
  return $rc
}

reds_of() {    # reds_of <kind> <日志文件> —— 两种 runner 各认各的红名格式
  local kind="$1" log="$2"
  if [ "$kind" = "swift" ]; then
    grep -oE "Test Case '-\[[A-Za-z0-9_.]+ [A-Za-z0-9_]+\]' failed" "$log" \
      | sed -E "s/.* (.*)\]' failed/\1/" | sort -u
  else
    { grep -E '^FAIL: ' "$log" | awk '{print $2}' | sed -E 's/.*[.:]//';
      grep -E '^test_\S+.* \.\.\. FAIL' "$log" | awk '{print $1}'; } | sort -u
  fi
}

# ── 基线：每种 runner 各跑一次，不绿就整表拒绝 ─────────────────────────────
BASE_OK=1
for kind in swift python; do
  case $kind in
    swift) rel=ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift ;;
    python) rel=scripts/tests/test_hover_two_state_diff.py ;;
  esac
  run_kind "$kind" "$rel" "$LOGDIR/base_$kind.log"
  rc=$?
  nreds=$(reds_of "$kind" "$LOGDIR/base_$kind.log" | grep -c . )
  if [ "$rc" -ne 0 ] || [ "$nreds" -ne 0 ]; then
    echo "基线不绿：kind=$kind rc=$rc 红名=$nreds ⇒ 拒绝出表"
    BASE_OK=0
  else
    echo "基线绿：kind=$kind（$(grep -cE 'Ran [0-9]+ test|Executed [0-9]+ test' "$LOGDIR/base_$kind.log") 行汇总）"
  fi
done
[ "$BASE_OK" -eq 1 ] || exit 1

# ── 逐把刀 ──────────────────────────────────────────────────────────────────
N=0; CAUGHT=0; ESCAPED=0; NOTRUN=0; WRONG=0; DIRTY=0
printf '%-6s %-10s %-46s %-52s %s\n' 刀号 结论 红名 期望那一格 还原
while IFS="$(printf '\t')" read -r MID KIND REL OLDF NEWF WANT WHY; do
  [ -n "${MID:-}" ] || continue
  N=$((N+1))
  BK="$LOGDIR/$MID.backup"
  python3 "$PATCH" patch "$ROOT/$REL" "$OLDF" "$NEWF" "$BK" 2> "$LOGDIR/$MID.patch.err"
  prc=$?
  if [ "$prc" -ne 0 ]; then
    NOTRUN=$((NOTRUN+1))
    printf '%-6s %-10s %-46s %-52s %s\n' "$MID" NOT_RUN "$(head -1 "$LOGDIR/$MID.patch.err" | cut -c1-46)" "$WANT" yes
    continue
  fi
  run_kind "$KIND" "$REL" "$LOGDIR/$MID.log"
  python3 "$PATCH" restore "$ROOT/$REL" "$BK"
  python3 "$PATCH" verify "$ROOT/$REL" "$BK"; vrc=$?
  if [ "$vrc" -ne 0 ]; then DIRTY=$((DIRTY+1)); fi
  REDS=$(reds_of "$KIND" "$LOGDIR/$MID.log" | tr '\n' ',' )
  if [ -z "$REDS" ]; then
    ESCAPED=$((ESCAPED+1)); VERDICT=ESCAPED
  elif echo "$REDS" | tr ',' '\n' | grep -qx "$WANT"; then
    CAUGHT=$((CAUGHT+1)); VERDICT=CAUGHT
  else
    WRONG=$((WRONG+1)); VERDICT=WRONG_CELL
  fi
  [ "$vrc" -ne 0 ] && VERDICT="$VERDICT/RESTORE_DIRTY"
  printf '%-6s %-10s %-46s %-52s %s\n' "$MID" "$VERDICT" "$(echo "$REDS" | cut -c1-46)" "$WANT" "$([ $vrc -eq 0 ] && echo yes || echo NO)"
done < "$MANI"

echo "R245_MUTATE 刀=$N CAUGHT=$CAUGHT ESCAPED=$ESCAPED NOT_RUN=$NOTRUN 抓错格=$WRONG RESTORE_CLEAN=$([ $DIRTY -eq 0 ] && echo yes || echo NO)"
[ $N -gt 0 ] && [ $CAUGHT -eq $N ] && [ $ESCAPED -eq 0 ] && [ $NOTRUN -eq 0 ] && [ $WRONG -eq 0 ] && [ $DIRTY -eq 0 ]
