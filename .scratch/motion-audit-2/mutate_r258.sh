#!/usr/bin/env bash
# R258（第 257 轮）两把刀，各自钉一条**不同的**轴 —— 形状沿用 mutate_r254.sh（重捕型），
# 但两条臂问的是两句不同的话，谁也不替谁作证：
#
#   M815  令牌轴：`VisualFillLift.pressed` 0.03 → 0.015（= R256 修之前的真实形状）。
#         期望 ControlHoverLadderTests 的真值表红 —— 那一格断言的是"亮档按下 = 0.15"。
#   M816  产物轴：0.03 → 0.0（把台阶压平，亮档按下与悬停同 alpha）。
#         期望新判据 testPressRungIsOrderedAboveTheHoverRung 红（press 与 hover 读到同一灰阶）。
#
# 为什么两把都要：本轮新加的像素判据**对"抬量偏小"不敏感**（0.015 时台阶仍有 ~4 灰阶、
# 恒等式仍成立），它只对"台阶没了 / 接线断了"敏感。管大小的那一条住在真值表里。
# 这条分工是读数读出来的，不是设计出来的 —— M815 那批重捕帧就是证人。
#
# 还原：整文件备份 + 逐字节 cmp（不是反向 sed）。
set -u
ROOT=/Users/wangziyi/Codex_Project0
TOK=$ROOT/ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift
BAK=/tmp/r258_lift_backup.swift
FR=/tmp/r258_arm_frames
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer

[ -f "$TOK" ] || { echo "NO_TOKEN_FILE"; exit 1; }
cp "$TOK" "$BAK"
restore() { cp "$BAK" "$TOK"; if cmp -s "$BAK" "$TOK"; then echo "R258_RESTORE=clean"; else echo "R258_RESTORE=DIRTY"; fi; }
trap restore EXIT

insert() {  # $1 = old, $2 = new, $3 = 标签
  python3 - "$TOK" "$1" "$2" "$3" <<'PY'
import io, sys
p, old, new, tag = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
t = io.open(p, encoding='utf-8').read()
n = t.count(old)
if n != 1:
    print("%s_ANCHOR_HITS=%d（要求恰好 1 次）" % (tag, n))
    raise SystemExit(3)
io.open(p, 'w', encoding='utf-8').write(t.replace(old, new, 1))
print("%s_INSERTED %s -> %s" % (tag, old, new))
PY
}

echo "########## M815：令牌轴（0.03 → 0.015，R256 修前形状）##########"
insert 'static let pressed: Double = 0.03' 'static let pressed: Double = 0.015' M815 || exit 3
( cd "$ROOT/ClipboardHistory" && swift test --filter ControlHoverLadderTests ) > /tmp/r258_arm_pure.log 2>&1
PURE_RC=$?
NAMED=$(grep -cE "Test Case.*' failed" /tmp/r258_arm_pure.log)
grep -E "XCTAssert.*failed" /tmp/r258_arm_pure.log | head -3 | cut -c1-190
echo "M815_PURE_EXIT=$PURE_RC 红名数=$NAMED"
if [ "$PURE_RC" -ne 0 ] && [ "$NAMED" -ge 1 ]; then echo "M815_CAUGHT=1"; else echo "M815_CAUGHT=0"; fi

echo "########## M815 的重捕（同一位、修前形状 ⇒ 给看图与灵敏度分工当证人）##########"
rm -rf "$FR"; mkdir -p "$FR"
( cd "$ROOT/ClipboardHistory" && CLIPBOARD_HISTORY_UI_SHOTS="$FR" swift test --filter UICaptureTests ) > /tmp/r258_arm_capture.log 2>&1
echo "M815_RECAPTURE_EXIT=$? 帧数=$(ls "$FR"/*.png 2>/dev/null | wc -l | tr -d ' ')"
grep -E "PRESS_LADDER" /tmp/r258_arm_capture.log | head -4 | cut -c1-200

cp "$BAK" "$TOK"   # 先还原，再量恒等式敏感度（用修前那批帧 vs 本轮那批帧）
cmp -s "$BAK" "$TOK" && echo "M815_RESTORE=clean" || echo "M815_RESTORE=DIRTY"

echo "########## M816：产物轴（0.03 → 0.0，台阶压平）##########"
insert 'static let pressed: Double = 0.03' 'static let pressed: Double = 0.0' M816 || exit 3
( cd "$ROOT/ClipboardHistory" && swift test --filter 'UICaptureTests/testPressRungIsOrderedAboveTheHoverRung' ) > /tmp/r258_arm_pixel.log 2>&1
PIX_RC=$?
grep -E "XCTAssert.*failed|PRESS_LADDER_PROOF" /tmp/r258_arm_pixel.log | head -6 | cut -c1-200
NAMED2=$(grep -cE "Test Case.*' failed" /tmp/r258_arm_pixel.log)
echo "M816_PIXEL_EXIT=$PIX_RC 红名数=$NAMED2"
if [ "$PIX_RC" -ne 0 ] && [ "$NAMED2" -ge 1 ]; then echo "M816_CAUGHT=1"; else echo "M816_CAUGHT=0"; fi

echo "########## 基线对照：修前那批帧 vs 本轮帧（同一位）##########"
( cd "$ROOT" && python3 scripts/frame_baseline.py compare "$FR" --against working ) > /tmp/r258_arm_baseline.log 2>&1
grep -E "^FRAME_BASELINE|row-favorite-press" /tmp/r258_arm_baseline.log | head -8
