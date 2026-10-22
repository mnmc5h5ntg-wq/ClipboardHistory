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

echo "[1/4] swift build --build-tests"
# R293 自曝：这里原来只 `swift build` ⇒ 编译的是产品目标，测试目标从来没编过，
# 于是 `build_warnings=0` 是一半覆盖的尺。CI 的 STEP[4] 带的正是 `--build-tests`
# （workflow 注释里写着 R59/BACKLOG 87 就为这件事改过 CI，本机四件套漏了同一个坑），
# runner 那朵告警红（UICaptureHarness 的 withUnsafeBytes unused）因此在本机绿了三轮。
# 0 告警那道门由 `scripts/warning_gate.sh` 独立成支（R296 / BACKLOG 343）：它印读数，**并且**能拦。
# 原来这里只把 `$W` 印进汇总行，从不 exit 非零 ⇒「0 告警」一直是散文不是门。
# 拦下就停在这里：有告警的一跑不该继续产其余读数，否则那一句会变成事后追述。
bash "$ROOT/scripts/warning_gate.sh" "$RUN" > "$RUN/warning_gate.log" 2>&1
GATE=$?
cat "$RUN/warning_gate.log"
if [ "$GATE" -ne 0 ]; then
  echo "ROUND_VERIFY ABORTED_AT_WARNING_GATE exit=$GATE（门本体 scripts/warning_gate.sh，正文 $RUN/warning_gate.log）"
  exit 1
fi
W=$(grep -oE "warnings=[0-9]+" "$RUN/warning_gate.log" | tail -1 | grep -oE "[0-9]+"); W=${W:-NOT-RUN}

echo "[2/4] 全量 swift test（日志只留 ${RUN}）"
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

# R279 / BACKLOG 333：这一格以前**只把 changed 抄成读数，从不拦人**。
# `frame_baseline.py compare` 的退出码在这里被丢掉了（子 shell 的 $? 没人看），而 CI 那一步用的是
# `check`（按设计只在 missing 时红）⇒ "改了界面却没在同一笔里 update 基线"这条纪律在**任何一侧都不是红**，
# 只靠人记得去看 ROUND_VERIFY 里那个 baseline_changed=。R252/R253 那两轮能发现 changed=1/2，
# 是因为我恰好在读那个数 —— 读数不是闸门。
# 现在它是闸门：changed≠0 就停在这一步（后面的 dmg/换装不再假装绿）。修法只有一条正路：
# 跑 `python3 scripts/frame_baseline.py update "$RUN/frames"` 之后重跑本脚本 ——
# 故意不留 `|| true`、不留环境变量后门（豁免一旦能被环境变量关掉，它就会腐烂成噪声）。
if [ "${BC:-NOT-RUN}" != "0" ]; then
  echo "FRAME_GATE_RED=changed=${BC} compared=${CM} missing=${MS} ⇒ 界面/夹具变了却没在同一笔里 update 基线（或帧数漂了）"
  echo "FRAME_GATE_HOWTO=python3 scripts/frame_baseline.py update \"$RUN/frames\" 之后重跑 scripts/round_verify.sh"
  exit 1
fi
echo "FRAME_GATE_PASS changed=0 compared=${CM} missing=${MS}"

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
