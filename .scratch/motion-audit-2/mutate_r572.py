#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R572 变异表 M1499–M1501：本轮落的是折叠规格 §3 第②段的 **650** ——
那条两档一致的离屏通道对**产品真实视图树**到底算什么。

判据对象（三格都在 `TransparencyForensicsTests`）：
  · `testTheAlphaLayerChannelDrawsProductTreesWhereTheOldChannelDrawsThem`
    （同一棵树、同一块栅格，两通道**逐点同类** ⇒ 异类数必须为 0）
  · `testTheAlphaLayerChannelKeepsRealTransparencyOfTheProductOverlayTree`
    （浮层那棵树里旧通道判为真透明的那颗探针，新通道也必须读 0）
  · `testTheProductMainTreeStillGivesTheAlphaChannelNoTransparentObject`
    （主窗那棵今天没有真透明对象：旧通道选不出透明探针、新通道也不许读出透明）

三把各钉本轮一条**读数**（都是这一轮真读到过的事，不是想象的坏法）：
- M1499 把「不预先铺底」那根杠杆撤掉（render 前铺一层不透明黑）
        ⇒ 透明那一侧被涂成 a=255 ⇒ 逐点异类跳起来、透明探针红。（与 R571 的 M1495 同一根杠杆，
          这一把钉的是它对**产品树**那一半。）
- M1500 把内存行序当回底朝上（`topY` 再翻一次）
        ⇒ 同一棵树被读成两棵不同的树 ⇒ 逐点异类红。
        本轮真实自伤：第一版就是这么写的，读数 142/5434 差点被我写成"两条通道在边缘带就是不同数"的契约。
- M1501 把「先走一遍旧通道」这个前置摘掉
        ⇒ 新通道对产品树整幅读不到内容 ⇒ 「找不到不透明探针」红（这一条钉的是 650 的真结论：
          这条路**必须**先让 AppKit 把内容画一次，否则 a=0 是「没画」而不是「归零」）。

用法：python3 .scratch/motion-audit-2/mutate_r572.py M1499   （一次一把，跑完自动还原）
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

RENDER_OLD = "        layer.render(in: context)"
READER_OLD = "            let o = topY * pixelsWide * 4 + x4(topX)"
WARM_OLD = (
    "        let rep = try XCTUnwrap(view.bitmapImageRepForCachingDisplay(in: view.bounds),\n"
    '                                "\\(tree.name)：旧通道拿不到位图 ⇒ 这一格没有内容")\n'
    "        view.cacheDisplay(in: view.bounds, to: rep)\n"
)
WARM_NEW = (
    "        let rep = try XCTUnwrap(view.bitmapImageRepForCachingDisplay(in: view.bounds),\n"
    '                                "\\(tree.name)：旧通道拿不到位图 ⇒ 这一格没有内容")\n'
)

ARMS = [
    ("M1499", "render 前铺一层不透明黑（撤掉「不预先铺底」那根杠杆）⇒ 透明被涂成 a=255 ⇒ 逐点异类/透明探针红",
     H, RENDER_OLD,
     "        context.setFillColor(CGColor(red: 0, green: 0, blue: 0, alpha: 1))\n"
     "        context.fill(CGRect(x: 0, y: 0, width: pixelsWide, height: pixelsHigh))\n"
     "        layer.render(in: context)",
     "swift"),
    ("M1500", "把内存行序当回底朝上（topY 再翻一次）⇒ 同一棵树被读成两棵不同的树 ⇒ 逐点异类红",
     H, READER_OLD,
     "            let o = (pixelsHigh - 1 - topY) * pixelsWide * 4 + x4(topX)",
     "swift"),
    ("M1501", "摘掉「先走一遍旧通道」这个前置 ⇒ 新通道对产品树读不到内容 ⇒「找不到不透明探针」红",
     H, WARM_OLD, WARM_NEW, "swift"),
]

FILTER = ("TransparencyForensicsTests/testTheAlphaLayerChannelDrawsProductTreesWhereTheOldChannelDrawsThem"
          "|TransparencyForensicsTests/testTheAlphaLayerChannelKeepsRealTransparencyOfTheProductOverlayTree"
          "|TransparencyForensicsTests/testTheProductMainTreeStillGivesTheAlphaChannelNoTransparentObject")


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
        print("用法: mutate_r572.py " + "|".join(a[0] for a in ARMS))
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
        if ("TRANSPARENCY_PRODUCT_ALPHA" in line or "error: -[" in line):
            print("  读数:", line.strip()[:250])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
