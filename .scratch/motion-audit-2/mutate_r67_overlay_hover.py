#!/usr/bin/env python3
"""R67 的变异对照：浮层那一行新加的悬停档，判据有没有牙（BACKLOG 95 那一族）。

被判的三条判据（都在 `UICaptureTests`）：
  testOverlayHoverTintIsPaintedAndConfinedToItsRow      像素：alpha 抬升够 / 只在这行 / 极性对 / 宽度内缩
  testOverlayHoverFillSharesTheSelectionPillsOutline    逐行轮廓：与选中药丸同一形状（R67b 补的那一格）
  testOverlayHoverPolicyIsATruthTableAndSharesItsTokenWithTheSidebar
                                                        真值表 + 令牌同一性 + 两处跨文件守卫

为什么 M369 是这批里最值钱的一刀：它是本轮**真实存在过**的形状（第一版就是直角满高），
而它从 M363–M368 六刀的判据下全部逃掉了 —— 宽度判据只看总范围，42…797 与 44…795 差 2px 在容差内。
"总范围相同、轮廓不同"这一族错只能由逐行尺抓到（R15 那一族的新成员）。

每一刀只动一个地方，动完必须**红在指定的那一格**。三条"电池自己会骗人"的规矩沿用 R64/R66：
① 基线必须先全绿；② 每刀落地要回读确认（原文不在了 **且** 变异文在场）；
③ 汇总把"没抓到 / 没跑成 / 没落地"分开设计数。

跑完自动还原；还原用**按内容还原**（不是 `git checkout --`，那些文件已入库但同一轮里
可能还有别的未提交改动 —— R61 那一族踩过）。

用法：`python3 .scratch/motion-audit-2/mutate_r67_overlay_hover.py`
"""
import os
import re
import subprocess
import sys

REPO = "/Users/wangziyi/Codex_Project0"
QPC = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/QuickPickController.swift"
LOCK = "/tmp/r67_mutation.lock"

PIXEL = "testOverlayHoverTintIsPaintedAndConfinedToItsRow"
OUTLINE = "testOverlayHoverFillSharesTheSelectionPillsOutline"
TABLE = "testOverlayHoverPolicyIsATruthTableAndSharesItsTokenWithTheSidebar"
BOTH = "UICaptureTests/testOverlayHover"
CASES = [PIXEL, OUTLINE, TABLE]

# (编号, 说明, 文件, 过滤, 原文, 变异后)
MUTATIONS = [
    ("M363", "让这一档永远不画（`showsHoverTint` 恒 false）⇒ 真值表与像素两格都必须红"
             "（这就是改之前产品的样子：浮层根本没有指针反馈）",
     QPC, BOTH,
     "        isHovered && !isSelected",
     "        false"),

    ("M364", "选中时也画（把 hover 叠到那颗蓝药丸上）⇒ 必须红在真值表那一格",
     QPC, BOTH,
     "        isHovered && !isSelected",
     "        isHovered"),

    ("M365", "把 alpha 从令牌上摘下来，写死 0.01 ⇒ 必须同时红在两格："
             "真值表那格的令牌同一性 + 像素那格的抬升地板（0.01×255=2.6 < 7.65）",
     QPC, BOTH,
     "    static let hoverFillAlpha = CGFloat(VisualFill.hover)",
     "    static let hoverFillAlpha = CGFloat(0.01)"),

    ("M366", "把墨写成死白（不跟外观翻面）⇒ 亮档必须红在极性那一格",
     QPC, BOTH,
     "        NSColor.labelColor.withAlphaComponent(QuickPickController.hoverFillAlpha(dark: dark)).setFill()",
     "        NSColor.white.withAlphaComponent(QuickPickController.hoverFillAlpha(dark: dark)).setFill()"),

    ("M367", "取消内缩（灰铺满整格，与选中药丸两种宽度）⇒ 必须红在宽度那一格",
     QPC, BOTH,
     "    static let hoverFillInset: CGFloat = 10",
     "    static let hoverFillInset: CGFloat = 0"),

    ("M368", "`rebuildRows` 不再清悬停（打字时那层灰会留在错误的一行上）⇒ "
             "像素判据抓不到（判据里没有真鼠标），必须由那条调用点守卫红",
     QPC, TABLE,
     "            (rowView as? QuickPickRowView)?.clearHover()",
     "            _ = rowView"),

    # —— R67b：看了画面才有的那一族（轮廓）。M369 就是 R67 第一版的实际形状。
    ("M369", "回到 R67 第一版：直角（半径 0）⇒ 必须红在轮廓那一格。"
             "这一刀是本轮的『真缺陷复现』：宽度判据（M367 那一格）对它是绿的，"
             "因为 42…797 与 44…795 只差 2px 在容差内 —— 只有逐行轮廓能看见方与圆的 11px 之差",
     QPC, OUTLINE,
     "    static let hoverFillCornerRadius: CGFloat = VisualRadius.card",
     "    static let hoverFillCornerRadius: CGFloat = 0"),

    ("M370", "圆角太小（3pt，实测内缩跨度约 5px 而药丸 11px）⇒ 轮廓那一格必须红。"
             "这一刀钉住『不许把 6pt 那种差不多圆的数挑进来』：R67 第二版就是 6pt，它当时是红的",
     QPC, OUTLINE,
     "    static let hoverFillCornerRadius: CGFloat = VisualRadius.card",
     "    static let hoverFillCornerRadius: CGFloat = 3"),

    ("M371", "圆角太大（14pt > 行高一半，圆成胶囊）⇒ 轮廓那一格必须红。"
             "只测『太小』会漏掉另一侧：判据是逐行绝对差，两侧都该有牙",
     QPC, OUTLINE,
     "    static let hoverFillCornerRadius: CGFloat = VisualRadius.card",
     "    static let hoverFillCornerRadius: CGFloat = 14"),
]


def read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    with open(os.path.join(REPO, path), "w", encoding="utf-8") as handle:
        handle.write(text)


def run(filter_expression):
    env = dict(os.environ)
    env.pop("SDKROOT", None)
    proc = subprocess.run(["swift", "test", "--filter", filter_expression],
                          cwd=os.path.join(REPO, "ClipboardHistory"), env=env,
                          capture_output=True, text=True, timeout=3600)
    return proc.stdout + proc.stderr, proc.returncode


def verdicts_of(text, cases):
    out = {}
    for case in cases:
        if re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' failed" % re.escape(case), text):
            out[case] = "red"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' passed" % re.escape(case), text):
            out[case] = "green"
        elif re.search(r"Test Case '-\[[^\]]*\b%s\b[^\n]*' skipped" % re.escape(case), text):
            out[case] = "skipped"
        else:
            out[case] = "absent"
    return out


def failure_messages(text, cases):
    hits = []
    for line in text.splitlines():
        if "error: -[" in line and any(case in line for case in cases):
            hits.append(line[:200])
    return hits


def main():
    if os.path.exists(LOCK):
        print("DRIFT-LOCK %s 已存在 ⇒ 另有一批在跑" % LOCK)
        return 2
    with open(LOCK, "w") as handle:
        handle.write(str(os.getpid()))
    results = []
    try:
        originals = {path: read(path) for _, _, path, _, _, _ in MUTATIONS}
        print("=== 基线（未变异）：两格判据都必须绿 ===")
        text, _ = run(BOTH)
        base = verdicts_of(text, CASES)
        for case, mark in base.items():
            print("   %-58s = %s" % (case[:58], mark))
        if any(mark != "green" for mark in base.values()):
            print("DRIFT-BASELINE 基线不绿 ⇒ 后面每一条『红』都不是证据，整批作废")
            for line in failure_messages(text, CASES)[:6]:
                print("     " + line)
            return 1

        for tag, note, path, case_filter, needle, replacement in MUTATIONS:
            print("\n%s %s" % (tag, note))
            source = read(path)
            if needle not in source:
                print("   DRIFT-NOT-APPLIED 变异原文找不到 ⇒ 这条没跑")
                results.append((tag, "NOT-APPLIED"))
                continue
            write(path, source.replace(needle, replacement, 1))
            after = read(path)
            if needle in after or replacement not in after:
                print("   DRIFT-NOT-APPLIED 回读证明这一刀没落地")
                write(path, originals[path])
                results.append((tag, "NOT-APPLIED"))
                continue
            print("   落地确认（%s）" % os.path.basename(path))
            try:
                text, _ = run(case_filter)
                marks = verdicts_of(text, CASES)
                reds = [case for case, mark in marks.items() if mark == "red"]
                compile_failed = "error:" in text and not reds
                if reds:
                    print("   CAUGHT 红在：%s" % " ".join(r[:44] for r in reds))
                    results.append((tag, "CAUGHT"))
                elif compile_failed:
                    print("   NOT-RUN 编译没过（这一刀没测到任何东西）")
                    print("     " + "\n     ".join(
                        [l for l in text.splitlines() if "error:" in l][:3]))
                    results.append((tag, "NOT-RUN"))
                elif any(mark == "skipped" for mark in marks.values()):
                    print("   NOT-RUN 被 skip 了：%s" % marks)
                    results.append((tag, "NOT-RUN"))
                else:
                    print("   ESCAPED 全绿：%s" % marks)
                    results.append((tag, "ESCAPED"))
                for line in failure_messages(text, CASES)[:3]:
                    print("     " + line)
            finally:
                write(path, originals[path])
                print("   已还原（逐字节相同：%s）" % (read(path) == originals[path]))

        print("\n=== 汇总 ===")
        counts = {}
        for tag, mark in results:
            counts[mark] = counts.get(mark, 0) + 1
            print("   %-6s %s" % (tag, mark))
        print("   抓到=%d 逃掉=%d 没跑成=%d 未落地=%d"
              % (counts.get("CAUGHT", 0), counts.get("ESCAPED", 0),
                 counts.get("NOT-RUN", 0), counts.get("NOT-APPLIED", 0)))
        return 0 if counts.get("ESCAPED", 0) == 0 and counts.get("NOT-APPLIED", 0) == 0 else 1
    finally:
        os.unlink(LOCK)


if __name__ == "__main__":
    sys.exit(main())
