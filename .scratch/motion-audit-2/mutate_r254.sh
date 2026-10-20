#!/usr/bin/env bash
# R254（第 253 轮）唯一一把刀 M814：**改产品墨的刀必须重跑帧**，否则它证明不了任何事。
# 为什么不能沿用 mutate_r245/247 那条「插刀 → 跑判据卷」的形状：判据卷读的是**已经落盘的帧**，
# 把 `VisualFillLift.hover` 从 0.04 改回 0.025 不会让旧帧变淡 ⇒ 直接跑判据只会 ESCAPED（假绿）。
# 所以这一把的通路是：插刀 → swift build → 重捕帧到独立目录 → 尺量那批新帧 → 期望 退出=1 且点名「低于地板」。
# 还原用整文件备份 + 逐字节比对（不是反向 sed）。
set -u
ROOT=/Users/wangziyi/Codex_Project0
TOK=$ROOT/ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift
BAK=/tmp/r246_lift_backup.swift   # 名字保留旧前缀会误导，改成本轮专用
BAK=/tmp/r254_lift_backup.swift
FR=/tmp/r254_arm_frames
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
cp "$TOK" "$BAK"
trap 'cp "$BAK" "$TOK"; cmp -s "$BAK" "$TOK" && echo "M814_RESTORE=clean" || echo "M814_RESTORE=DIRTY"' EXIT
python3 - "$TOK" <<'PY'
import io, sys
p = sys.argv[1]; t = io.open(p, encoding='utf-8').read()
a = 'static let hover: Double = 0.04'
assert t.count(a) == 1, t.count(a)
io.open(p, 'w', encoding='utf-8').write(t.replace(a, 'static let hover: Double = 0.025', 1))
print('M814_INSERTED lift 0.04 -> 0.025')
PY
rm -rf "$FR"; mkdir -p "$FR"
( cd "$ROOT/ClipboardHistory" && swift build 2>&1 | grep -cE "warning:" >/dev/null; CLIPBOARD_HISTORY_UI_SHOTS="$FR" swift test --filter UICaptureTests ) > /tmp/r254_arm_capture.log 2>&1
echo "ARM_CAPTURE_EXIT=$?  帧数=$(ls "$FR"/*.png 2>/dev/null | wc -l | tr -d ' ')"
( cd "$ROOT" && python3 scripts/hover_two_state_diff.py --shots "$FR" --control modechip-hover-idle-200x60-dark,modechip-hover-lit-200x60-dark ) > /tmp/r254_arm_ruler.log 2>&1
RC=$?
grep -E "row0-hover-720x520-light|FLOOR_RED" /tmp/r254_arm_ruler.log | cut -c1-170
NAMED=$(grep -c "row0-hover-720x520-light 的悬停在 WCAG 口径下" /tmp/r254_arm_ruler.log)
if [ "$RC" -ne 0 ] && [ "$NAMED" -ge 1 ]; then
  echo "M814_CAUGHT=1（尺 退出=$RC 且点名亮档那一行）⇒ R253 的 0.04 正是把这条读数顶过线的东西"
else
  echo "M814_CAUGHT=0（退出=$RC 点名=$NAMED）⇒ 这条读数不依赖那一次改动，账要改口"
fi
