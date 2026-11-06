#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R567 变异表 M1476–M1479：折叠几何第①段，D5/D7 的四种坏法各钉一条判据。

判据对象 = `FoldGeometryReanchorTests`（4 格，真窗口从产品入口进）+ `MainWindowFoldMotionTests` 的政策真值表。
每把刀只改**产品**那一行：不碰判据、不碰任何地板/容差/期望。

- M1476 折叠档退回旧值（424 → 420）   ⇒ 「折叠宽 = 展开宽的一半」红（424→420，出容差）。
- M1477 比例不随状态翻（恒用展开比） ⇒ 「折叠后 ratio = 424/600」红（0.706667 vs 1.413333）。
- M1478 列宽回到可拖区间（250~340）   ⇒ 侧栏宽红 **+** 「拖到 300 拖不动」那半红（行为证人）。
- M1479 折叠顺手写高度                ⇒ 「折叠不许动整窗高」红（632 → 560）。

用法：python3 .scratch/motion-audit-2/mutate_r567.py M1476   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

POLICY = "ClipboardHistory/Sources/ClipboardHistoryApp/Models/MainWindowCollapsePolicy.swift"
CONTROLLER = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/MainWindowCollapseController.swift"
CONTENT = "ClipboardHistory/Sources/ClipboardHistoryApp/Views/ContentView.swift"

# R594 重钉：这一行从前是三个值全钉成常量的那一档；R594 把列宽改成跟当前窗口宽之后
# 钉死值不在了，但**这一把刀要证的还是"列宽回到可拖区间"** ⇒ 起点换成现在这一行，终点一字未改。
COLUMN_OLD = ("                .navigationSplitViewColumnWidth(min: 200, ideal: MainWindowCollapsePolicy.columnWidth(contentWidth: MainWindowCollapsePolicy.expandedWidthDefault), max: .infinity)")
FRAME_OLD = ("        var frame = window.frame\n"
             "        let top = frame.maxY\n"
             "        frame.size.width = width")

# 形状按预检认得的第一种：(编号, 说明, 文件, 原文, 变异文, 目标测试类)
ARMS = [
    ("M1476", "折叠档退回旧值 420 ⇒ 一半关系断", POLICY,
     "static let collapsedWidthDefault: CGFloat = 424",
     "static let collapsedWidthDefault: CGFloat = 420", "swift"),
    ("M1477", "折叠后不翻锁比值 ⇒ 竖 √2 那一半没落地", CONTROLLER,
     "window.contentAspectRatio = MainWindowCollapsePolicy.aspectRatio(collapsed: isCollapsed)",
     "window.contentAspectRatio = MainWindowCollapsePolicy.expandedAspectRatio", "swift"),
    ("M1478", "列宽回到可拖区间 ⇒ 50/50 与拖不动一起红", CONTENT,
     COLUMN_OLD,
     "                .navigationSplitViewColumnWidth(min: 250, ideal: 280, max: 340)", "swift"),
    # 第一版把这行写成「无条件 frame.size.height = 560」⇒ PASSED（空刀）：`applyGeometry`
    # 在建窗时也会走一次，两态被一起压成 560，被测的那条"折叠前后高不变"根本没动。
    # 现在写成只在折叠那一支改高 ⇒ 才是真正的「折叠顺手改了高度」。
    ("M1479", "折叠时顺手写高度 ⇒ 违反「高度不变」", CONTROLLER,
     FRAME_OLD,
     FRAME_OLD + "\n        if isCollapsed { frame.size.height = 560 }", "swift"),
]

# 判据两把尺一起跑：AppKit 那一把（`FoldGeometryReanchorTests`）+ 像素那一把
# （`UICaptureTests/testTheSeamInTheRenderedFrameSitsAtHalfTheContentWidth`）。后者不是另开一刀的对象
# —— 同一处坏法不该铸两把刀（R559 那条），这里要的是**同一条刀必须两只尺都红**。
FILTER = ("FoldGeometryReanchorTests|MainWindowFoldMotionTests"
          "|UICaptureTests/testTheSeamInTheRenderedFrameSitsAtHalfTheContentWidth")


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
        print("用法: mutate_r567.py " + "|".join(a[0] for a in ARMS))
        return 2
    mid, why, rel, old, new, _kind = arm
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
        if ("FOLD_GEOMETRY" in line or "FOLD_SEAM_PIXEL" in line
                or "error: -[" in line):
            print("  读数:", line.strip()[:210])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
