#!/usr/bin/env bash
# R260（第 259 轮）两把刀，按 D-244 的规矩各钉一条轴 —— 修的是"亮档按下与选中糊成一档"（BACKLOG 308）。
#
#   M817 令牌轴：`VisualFillLift.selected` 0.02 → 0.0（= 修之前的形状）。
#         期望 ControlHoverLadderTests 的新格子红，且红名只有 light。
#         这一把就是把"红在改之前"变成可重跑的东西：它证明这条地板**有牙**，
#         而不是我写完断言之后它刚好绿。
#
#   M818 产物轴（重捕型）：保留令牌，把**调用点**改回直读 `VisualFill.selected`（绕开 SelectedInk）。
#         期望重捕后的帧与工作基线不一致 ⇒ 证明这批帧真的带着这一档的墨，
#         而不是只有纯函数在动。判据卷在这种情况下仍会绿（它读的是换算本身）——
#         这正是 D-240 那一族：调用点断了，只有产物能看见。
#
# 还原：整文件备份 + 逐字节 cmp（不是反向 sed）。
set -u
ROOT=/Users/wangziyi/Codex_Project0
TOK=$ROOT/ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift
SV=$ROOT/ClipboardHistory/Sources/ClipboardHistoryApp/Views/SettingsView.swift
BAK_TOK=/tmp/r260_tok_backup.swift
BAK_SV=/tmp/r260_sv_backup.swift
FR=/tmp/r260_arm_frames
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer

cp "$TOK" "$BAK_TOK"; cp "$SV" "$BAK_SV"
restore() {
  cp "$BAK_TOK" "$TOK"; cp "$BAK_SV" "$SV"
  if cmp -s "$BAK_TOK" "$TOK" && cmp -s "$BAK_SV" "$SV"; then echo "R260_RESTORE=clean"; else echo "R260_RESTORE=DIRTY"; fi
}
trap restore EXIT

insert() {  # $1=file $2=old $3=new $4=标签
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import io, sys
p, old, new, tag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
t = io.open(p, encoding='utf-8').read()
n = t.count(old)
if n != 1:
    print("%s_ANCHOR_HITS=%d（要求恰好 1 次）" % (tag, n)); raise SystemExit(3)
io.open(p, 'w', encoding='utf-8').write(t.replace(old, new, 1))
print("%s_INSERTED" % tag)
PY
}

echo "########## M817：令牌轴（lift.selected 0.02 → 0.0）##########"
insert "$TOK" 'static let selected: Double = 0.02' 'static let selected: Double = 0.0' M817 || exit 3
( cd "$ROOT/ClipboardHistory" && swift test --filter ControlHoverLadderTests ) > /tmp/r260_arm_m817.log 2>&1
RC=$?
NAMED=$(grep -c "pressed→selected 只剩" /tmp/r260_arm_m817.log)
LIGHTONLY=$(grep -c "light：pressed→selected" /tmp/r260_arm_m817.log)
echo "M817_EXIT=$RC 点名=$NAMED 只在亮档=$LIGHTONLY"
grep -E "XCTAssert.*failed" /tmp/r260_arm_m817.log | head -2 | cut -c1-150
if [ "$RC" -ne 0 ] && [ "$NAMED" -ge 1 ] && [ "$LIGHTONLY" = "$NAMED" ]; then echo "M817_CAUGHT=1"; else echo "M817_CAUGHT=0"; fi
cp "$BAK_TOK" "$TOK"; cmp -s "$BAK_TOK" "$TOK" && echo "M817_RESTORE=clean" || echo "M817_RESTORE=DIRTY"

echo "########## M818：产物轴（调用点绕开 SelectedInk → 重捕帧）##########"
insert "$SV" 'if isSelected { return SelectedInk.opacity(dark: colorScheme == .dark) }' \
             'if isSelected { return VisualFill.selected }' M818 || exit 3
rm -rf "$FR"; mkdir -p "$FR"
( cd "$ROOT/ClipboardHistory" && CLIPBOARD_HISTORY_UI_SHOTS="$FR" swift test --filter UICaptureTests ) > /tmp/r260_arm_capture.log 2>&1
CAP=$?
echo "M818_CAPTURE_EXIT=$CAP 帧数=$(ls "$FR"/*.png 2>/dev/null | wc -l | tr -d ' ')"
( cd "$ROOT" && python3 scripts/frame_baseline.py compare "$FR" --against working ) > /tmp/r260_arm_baseline.log 2>&1
grep -E "^FRAME_BASELINE_(CHANGED|MISSING|COMPARED)" /tmp/r260_arm_baseline.log
grep -E "^  changed" /tmp/r260_arm_baseline.log | head -6
NCH=$(grep -E "^FRAME_BASELINE_CHANGED=" /tmp/r260_arm_baseline.log | tail -1 | cut -d= -f2)
SEL=$(grep -E "^  changed" /tmp/r260_arm_baseline.log | grep -c "settings-")
if [ "$CAP" = 0 ] && [ "${NCH:-0}" -ge 1 ] && [ "$SEL" -ge 1 ]; then
  echo "M818_CAUGHT=1（断调用点 ⇒ $NCH 张帧变、其中 $SEL 张是设置窗口）⇒ 这批帧确实带着选中那一档的墨"
else
  echo "M818_CAUGHT=0（changed=${NCH:-NA} 设置窗口=${SEL:-NA}）⇒ 帧看不见这一档，账要改口"
fi
cp "$BAK_SV" "$SV"; cmp -s "$BAK_SV" "$SV" && echo "M818_RESTORE=clean" || echo "M818_RESTORE=DIRTY"
