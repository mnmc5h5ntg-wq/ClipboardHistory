#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R568 变异表 M1480–M1485：段②「透明与框架」+ 本轮修的两朵 runner 红，各钉一条坏法。

判据对象 = `TransparencyForensicsTests`（产品状态 / 命中让位）
          + `FoldGeometryReanchorTests/testTheHalfPointCaliberIsDerivedFromTheGridNotPicked`（真值表）
          + `UICaptureTests/testSeamArmOutcomeSeparatesBlankPageFromMissingSeam`（真值表）。

- M1480 撤掉产品自己那层不透明底衬        ⇒ 「带内 alpha 处处 255」红（实测退成 `半透明样本=18290/41475`），
  同一格的 `底衬=0` 也红 —— 这一刀就是 §4 第一条那个"材质会淡"的成因位。
- M1481 让底衬自己赢命中（hitTest 返回 self）⇒ 「底衬永远不吃命中」红（`空区命中=底衬3`）。
- M1482 窗口退回不透明（isOpaque = true）   ⇒ D4 前置那格第一条断言红。
- M1483 缝那把尺恒判「这台机器拍不出」      ⇒ 真值表红两条：`judged` 那行与 `seamGone` 那行
  （这就是"把真数改成不判＝藏红"的形状，必须一刀钉住）。
- M1484 列宽界值写成恒 100（不再由栅格推）  ⇒ 真值表红：1x 的真不对称被判成可接受。
- M1485 阴影那把尺把"两半一样暗"写成套形状  ⇒ 真值表红：`dragsRectangle` 那行落空（§4 第二条变成恒绿）。

用法：python3 .scratch/motion-audit-2/mutate_r568.py M1480   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

APPDELEGATE = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/AppDelegate.swift"
BACKING = "ClipboardHistory/Sources/ClipboardHistoryApp/Views/WindowBackingView.swift"
FOLD_TESTS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/FoldGeometryReanchorTests.swift"
TRANSPARENCY_TESTS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/TransparencyForensicsTests.swift"
HARNESS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"

WRAP_OLD = "window.contentView = WindowBackingContainer.wrapping(host)"
OPAQUE_OLD = ("        window.isOpaque = false\n"
              "        window.backgroundColor = .clear")
CALIBER_OLD = ("        static func columnDifferenceBound(scale: Double) -> Double {\n"
               "            halfPointIsRepresentable(scale: scale) ? exactTolerance : grid(scale: scale)\n"
               "        }")
SEAM_OLD = ("        if leftInk > 0 && rightInk > 0 && step >= 8.0 { return .judged }\n"
            "        if leftInk <= 0 && rightInk <= 0 && step < 8.0 { return .capabilityAbsent }")
SHADOW_OLD = ("        return right >= 0.02 ? .dragsRectangle(rightDarkness: right, leftDarkness: left)\n"
              "                             : .followsShape(rightDarkness: right, leftDarkness: left)")

ARMS = [
    ("M1480", "撤掉底衬 ⇒ §4 第一条那个「材质会淡」的成因位", APPDELEGATE,
     WRAP_OLD, "window.contentView = host  // MUTATE", "swift"),
    ("M1481", "底衬赢命中 ⇒ 点击落到一层什么都不画的东西上", BACKING,
     "override func hitTest(_ point: NSPoint) -> NSView? { nil }",
     "override func hitTest(_ point: NSPoint) -> NSView? { self }", "swift"),
    ("M1482", "窗口退回不透明 ⇒ D4 的让位没有可归零的 alpha", APPDELEGATE,
     OPAQUE_OLD, "        window.isOpaque = true", "swift"),
    # 这一刀改的是**尺**不是产品：M1483 把"没对象"这一支写成恒成立，
    # 于是真机那一档拍得出缝也会被说成"这台机器判不了" ⇒ 具名出口变成藏红的洞（R565 那一课）。
    ("M1483", "缝的尺恒判「拍不出」⇒ 具名出口吞掉真数", HARNESS,
     SEAM_OLD, "        return .capabilityAbsent", "swift"),
    ("M1484", "列界值不再由栅格推出 ⇒ 1x 的真不对称过关", FOLD_TESTS,
     CALIBER_OLD,
     "        static func columnDifferenceBound(scale: Double) -> Double { 100 }", "swift"),
    # 阴影那把尺的"没对象"那一支已经有 `noShadowAtAll` 那行钉着；这一刀钉的是**另一侧**：
    # 把"两半一样暗"（矩形阴影）写成"套形状" ⇒ §4 第二条那条断言就永远读不到它声称的那个东西。
    ("M1485", "阴影那把尺把矩形阴影说成套形状 ⇒ §4 第二条变成恒绿", TRANSPARENCY_TESTS,
     SHADOW_OLD,
     "        return .followsShape(rightDarkness: right, leftDarkness: left)", "swift"),
]

FILTER = ("TransparencyForensicsTests"
          "|FoldGeometryReanchorTests/testTheHalfPointCaliberIsDerivedFromTheGridNotPicked"
          "|UICaptureTests/testSeamArmOutcomeSeparatesBlankPageFromMissingSeam")


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
        print("用法: mutate_r568.py " + "|".join(a[0] for a in ARMS))
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
        if ("TRANSPARENCY" in line or "FOLD_GEOMETRY" in line
                or "SEAM" in line or "error: -[" in line):
            print("  读数:", line.strip()[:220])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
