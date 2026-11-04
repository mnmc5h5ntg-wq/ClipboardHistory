#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R571 变异表 M1495–M1498：本轮落的是折叠规格 §3 第②段 §4 第三问那条**新离屏通道**（646 第一条出路）。

判据对象：
  · `TransparencyForensicsTests/testTheAlphaLayerChannelSeparatesTrueBlackFromTransparentAtBothScales`
    （图层渲进自建 alpha 上下文：2x 与 1x 在同一台机器上都读到 `黑半区 a=255 / 透明半区 a=0 / 分得出=1`）
  · `WindowChromeLayoutTests/testTheProductMainWindowPathPublishesACredibleInset`
    （上一轮那格把"可信"写成本机的固定下界 28，runner 给 24 ⇒ 把一台合法机器读成产品缺陷；
     本轮换成恒等式 + 可信性两条与机器无关的判法）

四把各钉一种坏法：
- M1495 把上下文的 alpha 平面摘掉（noneSkipLast）⇒ 分得出=0 ⇒ 钉住"这条通道的 alpha 是我自己带的那块缓冲给的"。
  ⚠ 第一版下的是 `hosting.layer?.isOpaque = true`，读数逐字不变（两档仍 分得出=1）⇒ **空刀，撤掉不登记不占号**；
  ⚠ 前两版下刀都是**空刀**（`hosting.layer?.isOpaque = true` 与 `bitmapInfo = noneSkipLast` 两次读数逐字不变）⇒ 都撤掉、不登记不占号；
  这两条反面事实进账：保 alpha 的杠杆不在图层 isOpaque、也不在 bitmapInfo 那一位上，而在"这块缓冲没有预先铺底"。
- M1496 把探针的黑半区也画成透明            ⇒ 正对照那一格必须红（"整幅都没画"不许当"保住了 alpha"）。
- M1497 alpha 从错误的字节位读              ⇒ 黑半区读到 a=0 ⇒ 正对照红 ⇒ 钉的是"这条通道的读法真的在读 alpha 平面"。
- M1498 改**产品**：把发布的让位量夹到 20    ⇒ 恒等式（发布值 == 公式对本次实测算出的值）红。

用法：python3 .scratch/motion-audit-2/mutate_r571.py M1495   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

H = "ClipboardHistory/Tests/ClipboardHistoryAppTests/TransparencyForensicsTests.swift"
S = "ClipboardHistory/Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift"

CTX_OLD = "        layer.render(in: context)"
PROBE_OLD = "                Color.black"
READER_OLD = "Int(bytes[o + 3])"
PUBLISH_OLD = "        if next != detailContentTopInset { detailContentTopInset = next }"

ARMS = [
    ("M1495", "渲染前先给上下文铺一层不透明底（旧通道做的事）⇒ 透明半区被涂成 a=255 ⇒ 分得出=0", H,
     CTX_OLD,
     "        context.fill(CGRect(x: 0, y: 0, width: pw, height: ph))\n        layer.render(in: context)",
     "swift"),
    ("M1496", "探针黑半区也画成透明 ⇒ 正对照必须抓住「整幅都没画」", H,
     PROBE_OLD, "                Color.clear", "swift"),
    ("M1497", "alpha 从错误的字节位读 ⇒ 钉住这条通道真的在读 alpha 平面", H,
     READER_OLD, "Int(bytes[o + 2])", "swift"),
    ("M1498", "产品把发布的让位量夹到 20 ⇒ 恒等式（发布 == 公式对实测算出的那个值）必须红", S,
     PUBLISH_OLD,
     "        if next != detailContentTopInset { detailContentTopInset = min(next, 20) }", "swift"),
]

FILTER = ("TransparencyForensicsTests/"
          "testTheAlphaLayerChannelSeparatesTrueBlackFromTransparentAtBothScales"
          "|WindowChromeLayoutTests/testTheProductMainWindowPathPublishesACredibleInset")


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
        print("用法: mutate_r571.py " + "|".join(a[0] for a in ARMS))
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
        if ("TRANSPARENCY_CHANNEL" in line or "CHROME_PUBLISH_TRACE" in line
                or "error: -[" in line):
            print("  读数:", line.strip()[:230])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
