#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R581 变异表 M1527/M1528：本轮落的是折叠规格 §3 第②段 / BACKLOG **654** 里 A/B 那两把尺的**剥注释**。

判据对象（两条，`--filter UICaptureTests/testTheD12` 同时命中）：
- `UICaptureTests/testTheD12HardClausesEachNameAChannelThatEitherReadsOrIsNamed`（新通道串 `D12_SHAPE_SCAN`）
- `UICaptureTests/testTheD12LiveGateFlipsWhenAnInjectedObjectArrives`（新增档 1c/1d/1e）

本机现读（`/tmp/r581/d12_measure.log`）：
`D12_SHAPE_SCAN A剥注释=0 A带注释=0 A差=0 B剥注释=0 B带注释=0 B差=0 折叠路径剥注释=1 折叠路径带注释=2 折叠路径差=1 折叠alpha剥注释=0 折叠alpha带注释=0 折叠alpha差=0 折叠路径被注释喂着处数=1`
`D12_LIVE_GATE_PROBE 树=9 … 跨行注释A剥=0 跨行注释A带=1 跨行注释B剥=0 跨行注释B带=1 未闭合B=1 剥注释真值表=6格`
⇒ 派单 ② 预设的那一处尺病**是真的，但机制不是"没剥注释"**：R580 给 A/B 配的 `codeOnly` 里那个 `inBlock`
从来没被置成 true ⇒ 它只认**同一行内成对**的定界符 ⇒ 跨行的块注释照样能喂饱两把尺（1c 的带注释那一档
读到 1 就是这件事的实测大小）。今天产品树里 `/*` 出现 **0** 次 ⇒ A/B 两种读法都是 0（差 0 是量出来的，不是预期）。

两把刀各钉本轮一条真读到的事，且各只动一对量的一边：
- M1527 把**块注释**那一半能力摘掉（搜索目标改成永不出现的串）⇒ 1c 的"剥注释那一档必须读 0"红、
        1e 真值表里三格红；而**行注释**那一半未动 ⇒ 1b 与真值表第 1 格仍绿（证明两半是两个证人）。
- M1528 把"未闭合就停"改成"未闭合就一路吃到结尾"⇒ 1d 那档（字符串字面量里的开定界符之后真代码必须
        还看得见）红；而 1c 未动（它的注释是成对的 ⇒ 两条分支各钉一边，R567 那族"打在公共行上"的空刀形状）。

用法：python3 .scratch/motion-audit-2/mutate_r581.py M1527   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

T = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"

BLOCK_OLD = '        while let open = text.range(of: openBlock, range: searchFrom..<text.endIndex) {\n'
BLOCK_NEW = '        while let open = text.range(of: openBlock + "永不出现", range: searchFrom..<text.endIndex) {\n'

UNTERM_OLD = '            guard let close = text.range(of: closeBlock, range: open.upperBound..<text.endIndex) else { break }\n'
UNTERM_NEW = ('            guard let close = text.range(of: closeBlock, range: open.upperBound..<text.endIndex)\n'
              '                else { text.removeSubrange(open.lowerBound..<text.endIndex); break }\n')

ARMS = [
    ("M1527", "块注释那一半能力摘掉 ⇒ 跨行注释重新能喂饱 A/B ⇒ 1c 与真值表三格红（行注释那一半未动）",
     T, BLOCK_OLD, BLOCK_NEW, "swift"),
    ("M1528", "未闭合的开定界符改成一路吃到结尾 ⇒ 真代码被吃没 ⇒ 1d 红（1c 的成对分支未动）",
     T, UNTERM_OLD, UNTERM_NEW, "swift"),
]

FILTER = "UICaptureTests/testTheD12"


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
        print("用法: mutate_r581.py " + "|".join(a[0] for a in ARMS))
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
        if ("D12_SHAPE_SCAN" in line or "D12_LIVE_GATE_PROBE" in line
                or "error: -[" in line or "XCTAssert" in line):
            print("  读数:", line.strip()[:300])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
