#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R577 变异表 M1516：本轮落的是折叠规格 §3 第②段 / BACKLOG **651** 欠着的最后一个解释②
——「`wantsLayer` 只在窗口上屏之后才置」。

判据对象：`UICaptureTests/testTheThreeArmsOnOneTreeSettleExplanationTwoAboutOnScreenVersusDisplayPass`
（通道串 `SAME_TREE_ONSCREEN` / `EXPLANATION2` / `SAME_TREE_ONSCREEN_SUMMARY`）。
本机 2x 现读：甲（从未上屏、什么都不做）= `子层=-1 采样=0`（连 layer 都没建出来）、
乙A（只上屏 `orderFrontRegardless` + 跑一拍）= `子层=2 不透明=20160 全透明=0`、
乙B（**从未上屏**、只走 `window.display()`）= 与乙A **逐字相同**
⇒ `解释②=被否_不走显示通路只上屏建不出而display就建得出`（分水岭是**显示通路那一步**，不是"上屏"）。
诊断腿（同一棵树上先上屏再 display）与独立乙A逐字相同 ⇒ 上轮那句「被支持」读的是**累计形状**，
它把"上屏"与"display"两件事捆在一起，于是把 display 的功劳记给了上屏。

两把刀。M1516 钉 dispatch ② 要的那一句「把②的证人摘掉，这条判据必须红」；M1517 钉「没驱动不许读成结论」。
- M1516 摘掉**乙E**（不上屏、不跑 runloop、只调一次 `window.display()`）那一步 ⇒ 乙E 退回冷态，
        而乙C（只跑 runloop）仍建得出 ⇒ 分类器翻成「被否_只有跑一拍runloop那臂建得出」
        ⇒ 与登记声明（2.00x = 被否_display 单独就够）不符 ⇒ 红。
        ⚠ 这一把是**第二次下刀**：第一版把刀落在乙B（display + 跑 runloop）上，结果 `display()` 摘掉后
        乙B 照旧读到有树 ⇒ **空刀（PASSED）**，并且当场推翻了我自己刚写下的结论 ——
        "有树"不是 `display()` 给的，而是同一臂里另一件事（跑一拍 runloop）。
        于是本轮把自变量拆成 {上屏?, display?, runloop?} 三件事、一次只动一件，重测之后才有乙E/乙D 这一对。
- M1517 把「所有臂逐字相同 ⇒ 尺坏」那一支改成误判成「被否_display」⇒ 合成负对照当场红
        （dispatch ② 那句「两臂读数逐字相同 = 尺坏」的形状必须被认出来，不许被读成结论）。

用法：python3 .scratch/motion-audit-2/mutate_r577.py M1516   （跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

H = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"

DISPLAY_OLD = ('        let displayNoRunloopWindow = makeMainTreeWindow()\n'
               '        displayNoRunloopWindow.window.display()\n')
DISPLAY_NEW = ('        let displayNoRunloopWindow = makeMainTreeWindow()\n'
               '        _ = displayNoRunloopWindow.window.contentView // 刀：display 那一步没走\n')

BROKEN_OLD = '        if displayed == cold && onScreenNotDisplayed == cold && runloopOnly == cold { return .rulerBroken }\n'
BROKEN_NEW = '        if displayed == cold && onScreenNotDisplayed == cold && runloopOnly == cold { return .refutedDisplayPass }\n'

ARMS = [
    ("M1516", "摘掉乙E（不上屏、不跑 runloop、只走 display）那一步 ⇒ 层树证人没了 ⇒ 实测翻成被否_runloop 而声明是被否_display ⇒ 红",
     H, DISPLAY_OLD, DISPLAY_NEW, "swift"),
    ("M1517", "把分类器里「所有臂逐字相同 = 尺坏」那一支改成误判成被否 ⇒ 合成负对照当场红（尺不许把没驱动读成结论）",
     H, BROKEN_OLD, BROKEN_NEW, "swift"),
]

FILTER = ("UICaptureTests/testTheThreeArmsOnOneTreeSettleExplanationTwoAboutOnScreenVersusDisplayPass")


def run_tests():
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=PKG, capture_output=True, text=True, env=ENV, timeout=1800)
    out = proc.stdout + proc.stderr
    if "error:" in out and "Executed " not in out:
        return "ERROR", out
    if "Executed " not in out:
        return "DID-NOT-RUN", out
    return ("PASSED" if proc.returncode == 0 else "CAUGHT"), out


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == wanted), None)
    if arm is None:
        print("用法: mutate_r577.py " + "|".join(a[0] for a in ARMS))
        return 2
    mid, why, rel, old, new, kind = arm
    path = os.path.join(ROOT, rel)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, out = run_tests()
    print("预检:", code)
    if code != "PASSED":
        print(out[-1500:])
        return 2
    if text.count(old) != 1:
        print("needle 命中 %d ⇒ 不是恰好一次，不下刀" % text.count(old))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
    try:
        code, out = run_tests()
    finally:
        open(path, "wb").write(orig)
    print("%s: %s | %s" % (mid, code, why))
    for line in out.splitlines():
        if ("SAME_TREE_ONSCREEN" in line or "EXPLANATION2" in line
                or "error: -[" in line or "XCTAssert" in line):
            print("  读数:", line.strip()[:260])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
