#!/usr/bin/env bash
# R255 / BACKLOG 295：把 D-236 的四件套钉成一条命令。
# 为什么存在：R248 / R249 / R253 连着三轮改了产品却没跑「全量卷 + 重捕帧 + 帧基线 + 换装本机」，
# 同一个漏第三次出现 ⇒ 它不能靠记忆，只能靠一支跑完并打**一行摘要**的脚本。
# 规矩：
#   ① 每一步都现读，摘要里只有读到的数，没有"应该没问题"；
#   ② 任何一步跑不动 ⇒ 那一格打 NOT-RUN（带原因）而不是省略；
#   ③ 全量日志（这台机器上 ~320MB）只留在 /tmp，绝不入库；
#   ④ 换装用 ditto 覆盖，不许 rm -rf 工作区外的东西；
#   ⑤ 帧基线只 compare 不 update —— 有没有变、变了哪张，交回本轮决定，脚本不替人签字。
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
RUN=${1:-/tmp/round_verify}
mkdir -p "$RUN"
export DEVELOPER_DIR=${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}
W=NA; T=NA; S=NA; F=NA; FR=NA; BC=NA; VER=NA; DMG=NA

echo "[1/4] swift build"
( cd "$ROOT/ClipboardHistory" && swift build ) > "$RUN/build.log" 2>&1
W=$(grep -c "warning:" "$RUN/build.log" 2>/dev/null); W=${W:-0}   # 不用 `|| echo 0`：grep -c 已经打 0，那半句会再补一行 ⇒ W 变成两行

echo "[2/4] 全量 swift test（日志只留 $RUN）"
( cd "$ROOT/ClipboardHistory" && swift test ) > "$RUN/full.log" 2>&1
LINE=$(grep -E "Executed [0-9]+ tests" "$RUN/full.log" | tail -1)
T=$(printf '%s' "$LINE" | grep -oE "Executed [0-9]+ test" | grep -oE "[0-9]+" | tail -1); T=${T:-NOT-RUN}
S=$(printf '%s' "$LINE" | grep -oE "with [0-9]+ tests? skipped" | grep -oE "[0-9]+" | tail -1); S=${S:-0}
F=$(printf '%s' "$LINE" | grep -oE "and [0-9]+ failures?" | grep -oE "[0-9]+" | tail -1); F=${F:-NOT-RUN}   # R255 现读修：汇总行的形状是「with 44 tests skipped and 0 failures」，按 "with N failures" 抓会永远抓不到 ⇒ 摘要里出现「有键无值」（R88 那一族）

echo "[3/4] 重捕帧 + 帧基线 compare"
rm -rf "$RUN/frames"; mkdir -p "$RUN/frames"
( cd "$ROOT/ClipboardHistory" && CLIPBOARD_HISTORY_UI_SHOTS="$RUN/frames" swift test --filter UICaptureTests ) > "$RUN/capture.log" 2>&1
FR=$(ls "$RUN/frames"/*.png 2>/dev/null | wc -l | tr -d ' ')
( cd "$ROOT" && python3 scripts/frame_baseline.py compare "$RUN/frames" --against working ) > "$RUN/baseline.log" 2>&1
BC=$(grep -E "^FRAME_BASELINE_CHANGED=" "$RUN/baseline.log" | tail -1 | cut -d= -f2); BC=${BC:-NOT-RUN}
CM=$(grep -E "^FRAME_BASELINE_COMPARED=" "$RUN/baseline.log" | tail -1 | cut -d= -f2); CM=${CM:-0}
MS=$(grep -E "^FRAME_BASELINE_MISSING=" "$RUN/baseline.log" | tail -1 | cut -d= -f2); MS=${MS:-0}

echo "[4/4] make dmg + 换装本机（ditto 覆盖）"
( cd "$ROOT" && make dmg ) > "$RUN/dmg.log" 2>&1
if grep -q "DMG created" "$RUN/dmg.log" 2>/dev/null; then DMG=ok; else DMG=failed; fi
if [ "$DMG" = ok ]; then
  SRC=$(ls -d /tmp/*_dmg/*.app 2>/dev/null | head -1)
  if [ -n "${SRC:-}" ]; then
    ditto "$SRC" "/Applications/$(basename "$SRC")" && VER=$(defaults read "/Applications/$(basename "$SRC")/Contents/Info" CFBundleShortVersionString 2>/dev/null)
  fi
fi
VER=${VER:-NOT-RUN}
echo "ROUND_VERIFY build_warnings=$W swift_executed=$T swift_skipped=$S swift_failures=$F frames=$FR baseline_compared=$CM baseline_changed=$BC baseline_missing=$MS dmg=$DMG installed_version=$VER dir=$RUN"
