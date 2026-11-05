#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R579 变异表 M1521/M1522：本轮落的是折叠规格 §3 第②段 / BACKLOG **656** 那两条新格子 ——
**品红正对照的取样区几何** + **材质那一档的外观档位纯函数**。

判据对象：`TransparencyForensicsTests/testTheMagentaControlRegionNeverSitsUnderTheWindowAndTheTierNeedsTwoChannels`
（新通道串 `MAGENTA_CONTROL_GEOMETRY`；这一格**不需要真机键** ⇒ CI 每轮都跑，几何与档位的契约在 runner 上也有证人）。

本机 2x 现读（`/tmp/r579/geometry2.log`）：
`MAGENTA_CONTROL_GEOMETRY 用例=5 窗口外区域=3 判为无对象=2 第一用例面积=600000pt2 最大面积=1066500pt2
档位真值=Dark|Light|不相符_窗口=Dark_偏好键=Light|未知_窗口=未知_偏好键=Dark`
真机键那一趟（`/tmp/r579/material.log`）：
`TRANSPARENCY_MATERIAL_TIER 窗口解析外观=NSAppearanceNameDarkAqua 偏好键=Dark 档位=Dark 正对照区域=有 正对照品红=361275/370800`
⇒ 品红在这台机器上**拍得到**（97.4% 的采样落进阈值）⇒ 656 那朵 `撤掉底衬 品红漏出=0` 的两种成因里，
「通道瞎了」这一支被排掉；剩「暗档材质把品红混合到阈值以下」。

两把刀各钉本轮一条真读到的事：
- M1521 把正对照的取样区从「窗口之外那条带」改成「整块背景板」⇒ 该区域与窗口相交 ⇒ 几何断言红。
        钉的是：正对照不许落在窗口底下 —— 那样读到的 0 颗品红会被解释成「通道拍不到品红」，
        而真实成因是材质（两种成因的修法相反）。落刀前自问"我只动了这一对量的一边吗"：只改取样区定义，
        窗口/背景板/阈值一字未动。
- M1522 把档位纯函数认暗档的那一句改成认不出的串（`contains("Dark")` → `contains("dar")`）⇒
        「NSAppearanceNameDarkAqua」走到 `hasSuffix("Aqua")` 那一支被读成 Light ⇒ 合成用例第 0 格当场红。
        钉的是：档位必须由两条通道共同给，认不出来必须报「未知/不相符」，不许悄悄归到某一档。
        ⚠ 这一把刻意落在**合成用例**上，因为这台机器今天只有一档 —— 落在那扇真窗的读数上的刀会在
        「两档恰好同值」时空掉（R577/R578 各有一把空刀的形状）。

用法：python3 .scratch/motion-audit-2/mutate_r579.py M1521   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

T = "ClipboardHistory/Tests/ClipboardHistoryAppTests/TransparencyForensicsTests.swift"

REGION_OLD = '            NSRect(x: max(backdrop.minX, windowRect.maxX), y: backdrop.minY,\n                   width: backdrop.maxX - max(backdrop.minX, windowRect.maxX), height: backdrop.height),\n'
REGION_NEW = '            NSRect(x: backdrop.minX, y: backdrop.minY,\n                   width: backdrop.width, height: backdrop.height),\n'

TIER_OLD = '        if resolvedWindowName.contains("Dark") { fromWindow = "Dark" }\n'
TIER_NEW = '        if resolvedWindowName.contains("dar") { fromWindow = "Dark" }\n'

ARMS = [
    ("M1521", "正对照取样区改成整块背景板（与窗口相交）⇒ 几何那条「不相交」断言红",
     T, REGION_OLD, REGION_NEW, "swift"),
    ("M1522", "档位纯函数认不出暗档那一句 ⇒ 合成用例第 0 格读到「不相符」⇒ 红",
     T, TIER_OLD, TIER_NEW, "swift"),
]

FILTER = "TransparencyForensicsTests/testTheMagentaControlRegionNeverSitsUnderTheWindowAndTheTierNeedsTwoChannels"


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
        print("用法: mutate_r579.py " + "|".join(a[0] for a in ARMS))
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
        if ("MAGENTA_CONTROL_GEOMETRY" in line or "error: -[" in line
                or "XCTAssert" in line):
            print("  读数:", line.strip()[:300])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
