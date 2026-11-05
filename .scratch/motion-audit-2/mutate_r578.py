#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R578 变异表 M1518/M1519/M1520：本轮落的是折叠规格 §3 第②段 / BACKLOG **654** 那张映射表的
**「前置」那一列由实测同类性钉住** + BACKLOG 653/655 那条「漂移量不许当证人」的门
+ 那条「一条也没翻面」的**按行独立快照**。

判据对象：`UICaptureTests/testTheD12HardClausesEachNameAChannelThatEitherReadsOrIsNamed`
（本轮新增通道串 `D12_PREREQ` / `D12_REJUDGED`）。
本机 2x 现读：`前置实测=显示通路那一步 冷态子层=-1 只走显示通路子层=2 只上屏子层=-1 只走夹具快门子层=2
快门算不算显示通路的一个实例=是 带前置的行数=5 同类相符=5/5 漂移量被写成地板处数=0`
⇒ 八条**一条也没翻**：`D12_PREREQ` 那行给 `带前置的行数=5 同类相符=5/5`，`D12_REJUDGED` 那行给
`翻面=0 按行声明与快照相符=8/8 快照缺行=0 汇总与上轮逐字相同=1`，四个汇总数逐字不变，
而"没翻"这件事今天有证人：
第四臂（只做夹具快门那一步 `cacheDisplay`，不建窗、不上屏、不调 `window.display()`）实测建得出层树
⇒ 表里写的 `夹具快门cacheDisplay` 确实是"一次显示通路"的一个**具名实例**，不是记错功劳。

三把刀各钉本轮一条真读到的事：
- M1518 把「投影宽度按余弦律」那一行的前置写成 `上屏那一步` ⇒ 第四臂实测 `只上屏子层=-1`
        ⇒ `prerequisiteRowMatches` 走 `onScreenBuilds=false` 那一支 ⇒ 同类相符断言红。
        钉的是 dispatch ② 要的那句：前置名不许属于实测不成立的那一类。
        ⚠ 落刀前自问"我只动了这一对量的一边吗"：只改**声明**，实测三臂一字未动 ⇒ 差量确实只动一边。
- M1519 把离屏 alpha 通道"到不到数"的判据从 `(opaque + clear) > 0` 改成 `clear >= 17000`
        ⇒ 扫描门 `countDriftQuantityUsedAsFloor()` 读到 1 ⇒ 当场红（那个数跨会话会漂：
        本机 17180→17261，runner 同一跑两处 `未画比例=0.8495 / 0.8511`）。
        ⚠ 覆盖面照实说：这把刀钉的是**写法形状**（同名变量 + 整数阈值），改名绕开是可能的 ⇒
        账里不许写成"这个量已经不可能被当地板"。
- M1520 把 `d12RowCategoriesR577` 里「角度单调」那一行的快照抄成 `runner可判`（今天实测给的是
        `今天无证人`）⇒ 表体一字未动、`声明==实测` 那条旧断言仍绿，只有**新门**读到
        `按行声明与快照相符=7/8` ⇒ 红。它钉的是 dispatch ② 那句"翻面要有读数支持"的另一半：
        基线必须是独立抄本 —— 拿本轮自己那张表当基线时，改表的人不会让任何断言变红。
        ⚠ 这条是本轮**改代码之前**才抓到的：第一版 `翻面=` 打的是"分类有没有落全"、
        `同类相符=` 的分子分母同源于 `prereqChecked`（恒真门），两处都不读它声称的那个对象。

用法：python3 .scratch/motion-audit-2/mutate_r578.py M1518   （一次一把，跑完自动还原）
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

PREREQ_OLD = ('            D12Clause(title: "投影宽度按余弦律", channel: "逐帧像素", prerequisite: "夹具快门cacheDisplay",\n')
PREREQ_NEW = ('            D12Clause(title: "投影宽度按余弦律", channel: "逐帧像素", prerequisite: "上屏那一步",\n')

FLOOR_OLD = '        return (profile.samples > 0 && (profile.opaque + profile.clear) > 0,\n'
FLOOR_NEW = '        return (profile.samples > 0 && profile.clear >= 17000,\n'

SNAP_OLD = '        "角度单调": "今天无证人",\n'
SNAP_NEW = '        "角度单调": "runner可判",\n'

ARMS = [
    ("M1518", "把一行的前置写成「上屏那一步」而实测只上屏建不出层树 ⇒ 同类相符断言红",
     H, PREREQ_OLD, PREREQ_NEW, "swift"),
    ("M1519", "把漂移量写成地板（clear >= 17000）⇒ 扫描门读到 1 处 ⇒ 红",
     H, FLOOR_OLD, FLOOR_NEW, "swift"),
    ("M1520", "把按行快照里某一行的类别抄成今天实测支撑不了的那一态 ⇒ 表与快照相符 8/8→7/8 ⇒ 红"
              "（钉「翻面」这一格拿的是独立抄本，不是本轮自己那张表）",
     H, SNAP_OLD, SNAP_NEW, "swift"),
]

FILTER = "UICaptureTests/testTheD12HardClausesEachNameAChannelThatEitherReadsOrIsNamed"


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
        print("用法: mutate_r578.py " + "|".join(a[0] for a in ARMS))
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
        if ("D12_PREREQ" in line or "D12_REJUDGED" in line or "error: -[" in line
                or "XCTAssert" in line):
            print("  读数:", line.strip()[:260])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
