#!/usr/bin/env bash
# 0 告警那道门的**本体**（R296 / BACKLOG 343）。
#
# 为什么单独成一支：`round_verify.sh` 原来只把告警数**印**在汇总行里（`build_warnings=$W`），
# 从不 exit 非零 —— 于是「0 告警」是一句散文而不是一个门（同一族先例：344 那句「停旧数会红」）。
# 这一支把门与读数分开：印读数，并且**只有门能放行**。
#
# 两个坑，都是现读撞上的：
# · 目标口径：必须与 CI 的 STEP[4] 编同一个目标（`swift build --build-tests`）。只编产品目标时
#   测试目标从来没进过编译器，告警可以挂在测试文件里绿三轮（R293 的 runner 红就是这么来的）。
# · 暖缓存：增量构建不重印**没被改动**的那批文件的告警 ⇒ 一次「0」可能只是「没重新看」。
#   所以 W=0 时要把这个 0 **挣出来**：换一条全新的 scratch-path 冷编一遍，数那一次的告警。
#   冷编只在「看起来干净」时发生 —— 有告警的那一跑不必再花这段时间。
#
# 用法：bash scripts/warning_gate.sh <运行目录>     退出码 0=干净，1=有告警，2=尺自己坏了
set -u
RUN="${1:-/tmp/warning_gate}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$RUN"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
if command -v xcrun >/dev/null 2>&1; then
  SDKROOT="$(xcrun --sdk macosx --show-sdk-path 2>/dev/null)" || SDKROOT=""
  [ -n "$SDKROOT" ] && export SDKROOT
fi

INC="$RUN/build-warnings.log"
( cd "$ROOT/ClipboardHistory" && swift build --build-tests ) > "$INC" 2>&1
INC_RC=$?
W_INC=$(grep -c "warning:" "$INC" 2>/dev/null); W_INC=${W_INC:-0}
COLD=not-needed
COLD_P=
W="$W_INC"
# 构建自己失败 ⇒ 这把尺没有对象：不许把「一条告警都没数到」读成「0 告警」（R100 那一族：
# 仪器坏在哪个方向，结论就往哪个方向假）。
if [ "$INC_RC" -ne 0 ]; then
  echo "ROUND_WARNING_GATE warnings=NOT-RUN cold=not-needed exit=2 增量构建退出 $INC_RC ⇒ 门没有对象，不许读成干净"
  tail -6 "$INC"
  exit 2
fi

if [ "$W_INC" -eq 0 ]; then
  COLD="$RUN/build-warnings-cold.log"
  ( cd "$ROOT/ClipboardHistory" && swift build --build-tests --scratch-path "$RUN/warninggate-build" ) > "$COLD" 2>&1
  COLD_RC=$?
  W_COLD=$(grep -c "warning:" "$COLD" 2>/dev/null); W_COLD=${W_COLD:-0}
  COLD_P="$W_COLD"
  W="$W_COLD"          # 冷编那一次的数才算数：它不依赖上一轮的构建缓存
  if [ "$COLD_RC" -ne 0 ]; then
    echo "ROUND_WARNING_GATE warnings=NOT-RUN cold=$COLD_P exit=2 冷编退出 $COLD_RC ⇒ 门没有对象，不许读成干净"
    tail -6 "$COLD"
    exit 2
  fi
  # 冷编没报错也没留下任何可判正文 ⇒ 是尺坏了（它可能根本没跑到编译器）
  if [ "$W_COLD" -eq 0 ] && ! grep -qE "Build complete|Compiling|warning:|error:" "$COLD"; then
    echo "ROUND_WARNING_GATE warnings=NOT-RUN cold=$COLD_P exit=2 冷编没有可判正文 ⇒ 这一格不许读成 0"
    exit 2
  fi
fi

echo "ROUND_WARNING_GATE warnings=$W incremental=$W_INC cold=${COLD_P:-$COLD} target=build-tests"
if [ "$W" -gt 0 ]; then
  echo "ROUND_WARNING_GATE_FAIL 见下方逐行原文（前 12 条）"
  grep -n "warning:" "$INC" "$COLD" 2>/dev/null | head -12
  exit 1
fi
exit 0
