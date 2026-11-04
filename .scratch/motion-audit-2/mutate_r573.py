#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R573 变异表 M1502–M1503：本轮落的是折叠规格 §3 第②段的 **651** ——
「哪个调用让哪一类层进入可 render 状态」从量到的**现象**收成**机制断言**。

判据对象（`TransparencyForensicsTests`）：
  · `testTheDisplayPassIsWhatMakesTheProductContainerTreeRenderable`
    （同一棵产品浮层树分三臂：甲 只根 `wantsLayer` ⇒ `不透明=0`；
      乙 递归 `wantsLayer` 不 display ⇒ `不透明=176`；丙 走过 display 通路 ⇒ `不透明=2096`；
      D 类 `CAMetalLayer` 产品源码引用文件数现读 0 ⇒ 只具名 `METAL_LAYER_NOT_RUN=no-shader-yet`，不编读数）
  · `testTheAlphaLayerChannelSeparatesTrueBlackFromTransparentAtBothScales`
    （R571 那一格：runner 现读两档都整幅 a=0 ⇒ 本轮给它补上同一个前置，并留一条冷态对照读数）

两把各钉一条**本轮真读到的机制**：
- M1502 在甲臂之前先走一遍 display ⇒ 甲臂读到非 0 ⇒ `甲.不透明 == 0` 红
        （钉的是"甲臂确实还是冷态"这个对照 —— 没有它，三臂就退化成一条）。
- M1503 把丙臂的前置摘掉 ⇒ 丙 == 乙 ⇒ `丙 > 乙` 那条严格链红
        （钉的是 651 的结论本身：只建层树不算，把内容画进 contents 的是 display 通路）。

**一把撤掉的空刀（不登记、不占号，反面事实进账）**：
- 把 乙 臂的 `forceLayer(view)` 摘掉 ⇒ 乙 读到 0（与甲同），而 `乙 >= 甲` 与 `丙 > 乙` 两条**都仍然成立**
  ⇒ 这条链对"递归 wantsLayer"那一步不敏感（因为丙臂自己会把它建起来）⇒ 落刀前自问"我只动了这一对量的一边吗"，
  这一次答案是"动了，但读数落回另一臂已经覆盖的位置" ⇒ 空刀。
- 另有一条**本机量不到的**：把 R571 那一格新加的前置摘掉 ⇒ 本机读数逐字不变（本机冷态就能画）
  ⇒ 这一把在本机是空刀，它的证人只能是 runner 那一跑（账里已具名 `OFFSCREEN_ALPHA_PREREQ_LOCAL_NOOP`）。

用法：python3 .scratch/motion-audit-2/mutate_r573.py M1502   （一次一把，跑完自动还原）
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
C = ".scratch/motion-audit-2/review_round_claims.py"

RULER_OLD = r'SUBJECT = re.compile(u"^R(\\d{2,4})(?:[ ：](.+?))?（.*?产品 (\\d+) 文件")'
RULER_NEW = r'SUBJECT = re.compile(u"^R(\\d{2,4})(?: (.+?))?（.*?产品 (\\d+) 文件")'

ARM_A_OLD = '        let cold = try arm("甲_只根wantsLayer")'
ARM_A_NEW = ('        view.cacheDisplay(in: view.bounds, to: rep)   // 变异：甲臂提前画一遍\n'
             '        let cold = try arm("甲_只根wantsLayer")')
PREREQ_OLD = ('        let treeOnly = try arm("乙_递归wantsLayer不display")\n'
              '        view.cacheDisplay(in: view.bounds, to: rep)\n')
PREREQ_NEW = '        let treeOnly = try arm("乙_递归wantsLayer不display")\n'

ARMS = [
    ("M1502", "甲臂之前先 display 一遍 ⇒ 甲读到非 0 ⇒「甲.不透明 == 0」红（钉住冷态对照本身）",
     H, ARM_A_OLD, ARM_A_NEW, "swift"),
    ("M1503", "摘掉丙臂的 display 前置 ⇒ 丙 == 乙 ⇒ 严格链红（钉 651 的机制结论）",
     H, PREREQ_OLD, PREREQ_NEW, "swift"),
    ("M1504", "把 `SUBJECT` 退回只认 ASCII 空格的那一版 ⇒ 合成正对照 R904（全角冒号紧跟轮次号）掉进 "
     "unparsed ⇒ `test_positive_control_...` 红（钉住 R573 对尺的放宽本身）",
     C, RULER_OLD, RULER_NEW, "python"),
]

FILTER = ("TransparencyForensicsTests/testTheDisplayPassIsWhatMakesTheProductContainerTreeRenderable"
          "|TransparencyForensicsTests/testTheAlphaLayerChannelSeparatesTrueBlackFromTransparentAtBothScales")


def run_python_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest",
                           "scripts.tests.test_round_claim_consistency", "-v"],
                          cwd=ROOT, capture_output=True, text=True, env=ENV, timeout=600)
    out = proc.stdout + proc.stderr
    if "Ran " not in out:
        return "DID-NOT-RUN", out
    return ("PASSED" if proc.returncode == 0 else "CAUGHT"), out


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
        print("用法: mutate_r573.py " + "|".join(a[0] for a in ARMS))
        return 2
    mid, why, rel, old, new, kind = arm

    def _kind_of(which):
        return next((a[5] for a in ARMS if a[0] == which), "swift")
    path = os.path.join(ROOT, rel)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    runner = run_python_tests if _kind_of(wanted) == "python" else run_tests
    code, out = runner()
    print("预检:", code)
    if code != "PASSED":
        print(out[-1500:])
        return 2
    if text.count(old) != 1:
        print("needle 命中 %d ⇒ 不是恰好一次，不下刀" % text.count(old))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
    try:
        code, out = runner()
    finally:
        open(path, "wb").write(orig)
    print("%s: %s | %s" % (mid, code, why))
    for line in out.splitlines():
        if ("TRANSPARENCY_PREREQ_MECHANISM" in line or "OFFSCREEN_ALPHA_LAYER_COLD" in line
                or "error: -[" in line or "AssertionError" in line or "unparsed" in line):
            print("  读数:", line.strip()[:250])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
