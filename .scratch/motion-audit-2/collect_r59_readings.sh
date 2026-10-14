#!/bin/sh
# R59 读数采集：先把整条 motion 卷跑一遍拿全量 MOTION_* 行，
# 再把本轮新增的三条测量单独连跑 5 次 —— 台账里那句"五次读数"必须有承载物。
#
# 两条通道都要留档（R56 的设计）：本机第一版这个脚本只 tee 了 stdout，
# 结果整条卷那一次 stdout 里一行 MOTION_ 都没有，而**文件通道**里有 ——
# 所以每一遍跑完必须把 motion-readings.log 拷出来，否则"这一遍的读数"会丢。
set -u
cd /Users/wangziyi/Codex_Project0/ClipboardHistory || exit 1
OUT=/tmp/r59-readings
mkdir -p "$OUT/file"
export CLIPBOARD_HISTORY_UI_MOTION=1
export CLIPBOARD_HISTORY_MOTION_OUT=/tmp/r59-motion

collect() {                       # $1 = 标签
  if [ -f /tmp/r59-motion/motion-readings.log ]; then
    cp /tmp/r59-motion/motion-readings.log "$OUT/file/$1.log"
  else
    : > "$OUT/file/$1.log"
    echo "MOTION_READINGS_FILE_ABSENT=1" >> "$OUT/file/$1.log"
  fi
}

rm -f /tmp/r59-motion/motion-readings.log
env -u SDKROOT swift test --filter MotionFilmstripTests > "$OUT/full.log" 2>&1
full_exit=$?
collect full

echo "### 本轮新增三条测量连跑 5 次" > "$OUT/repeats.md"
for i in 1 2 3 4 5; do
  rm -f /tmp/r59-motion/motion-readings.log
  env -u SDKROOT swift test --filter "MotionFilmstripTests.testBannerDismissColumnAsymmetryIsMeasured|MotionFilmstripTests.testBannerOutTracksWhetherItFadesOrSlides|MotionFilmstripTests.testBannerFrameStacksAreReadableEvidence" > "$OUT/rep$i.log" 2>&1
  collect "rep$i"     # 必须先拷再读：文件通道每个进程都会重开，下一遍就把这一遍的覆盖掉了
  echo "--- 第 $i 遍 (exit=$?)  stdout=$(grep -c 'MOTION_' "$OUT/rep$i.log" || true) 文件=$(grep -c '^MOTION_' "$OUT/file/rep$i.log" || true) ---" >> "$OUT/repeats.md"
  grep '^MOTION_' "$OUT/file/rep$i.log" >> "$OUT/repeats.md" || true
done

{
  echo "### 整条 MotionFilmstripTests（本机）exit=$full_exit"
  echo "--- stdout 通道里含 MOTION_ 子串的行：$(grep -c 'MOTION_' "$OUT/full.log" || true)"
  echo "--- stdout 通道里以 MOTION_ 开头的读数行：$(grep -c '^MOTION_' "$OUT/full.log" || true)"
  echo "--- 文件通道里的 MOTION_ 行数：$(grep -c '^MOTION_' "$OUT/file/full.log" || true)"
  grep '^MOTION_' "$OUT/file/full.log" || true
  grep 'MOTION_NOT_RUN' "$OUT/full.log" || true
  grep 'Executed ' "$OUT/full.log" | tail -1
} > "$OUT/full.md"
echo DONE
