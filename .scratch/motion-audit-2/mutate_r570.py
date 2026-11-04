#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R570 变异表 M1489–M1494：本轮新加的两把尺（捕获那一刻那条全局的直接读数 + 本机因果实验 + 真窗发布轨迹）。

判据对象：
  · `UICaptureTests/testTheChromeInsetReadingSpeaksOnlyWhenTheValueMoves`（读数该不该说话的 真值表）
  · `UICaptureTests/testTheInsetShapeClassifierSplitsTheFiveCasesItClaims`（形状的 真值表）
  · `UICaptureTests/testARealWindowChromeInsetBreaksCapturedDetailFramesTheWayTheRunnerSaw`（本机因果实验）
  · `WindowChromeLayoutTests/testTheRealWindowNeverPublishesAnInsetFromAnImpossibleMeasurement`（手搭真窗轨迹）
  · `WindowChromeLayoutTests/testTheProductMainWindowPathPublishesACredibleInset`（产品主窗路轨迹）

六把里五把改**尺**、一把改**产品**（M1494），各钉一种坏法：
- M1489 读数在非首拍时永远沉默        ⇒ 真值表里"漂出去要说""漂回来也要说"两行同红（通道装死）。
- M1490 形状分类器把"漂了且带子空"说成"还有墨" ⇒ 真值表一行红，而因果实验从此**永远不会**判出重现（藏红）。
- M1491 注入根本没走产品的发布函数     ⇒ 每一档实测都停在兜底值 ⇒ 正对照那格红 + 档位表与实测对不上。
- M1492 必经点计数器不涨              ⇒ "这条通道今天确实挂在拍帧路上"那句证人变红（连印都没有）。
- M1493 轨迹记录器什么都不记          ⇒ 两格轨迹都判不出发布 ⇒ 红（把"没发布"与"没记到"混成一件）。
- M1494 产品把发布值夹到 20（比可信下界小）⇒ 两格轨迹都必须红 ⇒ 钉的是"这一格真的在看产品发什么"，
  而不是只读我自己摆的哨兵。

用法：python3 .scratch/motion-audit-2/mutate_r570.py M1489   （一次一把，跑完自动还原）
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
W = "ClipboardHistory/Tests/ClipboardHistoryAppTests/WindowChromeLayoutTests.swift"
S = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift"

SPEAK_OLD = "        if deliberate { return .silent }"
SHAPE_OLD = "        return drawn ? .driftedButStillDrawn : .runnerShapeReproduced"
DRIVE_OLD = ("        WindowChromeMetrics.shared.noteTrafficLights(titlebarHeight: titlebarHeight,\n"
             "                                                     buttonHeight: buttonHeight)")
COUNT_OLD = "        calls += 1"
TRACE_OLD = "                self?.values.append(next)"
PUBLISH_OLD = "        if next != detailContentTopInset { detailContentTopInset = next }"

ARMS = [
    ("M1489", "读数在非首拍永远沉默 ⇒ 漂出去/漂回来两行证人同红（通道装死）", H,
     SPEAK_OLD, "        if deliberate || previous != nil || current != fallback { return .silent }",
     "swift"),
    ("M1490", "分类器把「漂了且带子空」说成「还有墨」 ⇒ 重现这一格永远不会红", H,
     SHAPE_OLD, "        return .driftedButStillDrawn", "swift"),
    ("M1491", "注入没走产品自己的发布函数 ⇒ 每一档都停在兜底值", H,
     DRIVE_OLD, "        _ = (titlebarHeight, buttonHeight)", "swift"),
    ("M1492", "必经点计数器不涨 ⇒ 「这条通道挂在拍帧路上」没有证人", H,
     COUNT_OLD, "        calls += 0", "swift"),
    ("M1493", "轨迹记录器什么都不记 ⇒ 「没发布」与「没记到」被混成一件", W,
     TRACE_OLD, "                self?.values = []", "swift"),
    ("M1494", "产品把发布值夹到 20（低于可信下界）⇒ 两格轨迹都必须红", S,
     PUBLISH_OLD,
     "        if next != detailContentTopInset { detailContentTopInset = min(next, 20) }", "swift"),
]

FILTER = ("UICaptureTests/(testTheChromeInsetReadingSpeaksOnlyWhenTheValueMoves"
          "|testTheInsetShapeClassifierSplitsTheFiveCasesItClaims"
          "|testARealWindowChromeInsetBreaksCapturedDetailFramesTheWayTheRunnerSaw)"
          "|WindowChromeLayoutTests/(testTheRealWindowNeverPublishesAnInsetFromAnImpossibleMeasurement"
          "|testTheProductMainWindowPathPublishesACredibleInset)")


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
        print("用法: mutate_r570.py " + "|".join(a[0] for a in ARMS))
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
        if ("INSET_CAUSAL" in line or "CHROME_PUBLISH_TRACE" in line
                or "CAPTURE_CHROME_INSET" in line or "error: -[" in line):
            print("  读数:", line.strip()[:230])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
