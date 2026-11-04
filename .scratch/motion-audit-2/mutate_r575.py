#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R575 变异表 M1509–M1512：本轮落的是折叠规格 §3 第②段收尾的取证工作 ——
把 D12 那**八条逐帧硬判据**做成一张会红的表（判它的通道 / 通道的前置由谁满足 / 两档两机今天到不到数）。

判据对象（`UICaptureTests`）：
  · `testTheD12HardClausesEachNameAChannelThatEitherReadsOrIsNamed`
    八条声明 × 三条现扫探针 × 两条现量通道（逐帧像素 = 夹具必经点 `render` 的产物；离屏 alpha 图层 =
    产品浮层树走 651 丙臂前置之后）⇒ 实测态必须逐条等于声明态。
  · 现读（本机 2x）：`D12_CHANNEL_MAP_SUMMARY 条=8 runner可判=0 只能真机=1 今天无证人=7
    角度驱动文件数=0 折叠路径文件数=2 折叠期改alpha文件数=0 真机键=关`

四把各钉本轮一条**真读到的事**（不是想象的坏法）：
- M1509 从表里删掉一条声明 ⇒ 条数 8→7 ⇒ 「八条一条不许少」那格红。
        钉的是这张表最坏的失效方式：**少一行不会让那条判据消失，只会让下一轮以为它不存在**。
- M1510 把「屏上帧间隔不超标」那条的声明从 `只能真机` 改成 `runner可判` ⇒ 与实测不符 ⇒ 红。
        钉的是"声明可以悄悄抬高一档"这一族（把 env-off 的格子写成能判，验收就会在 runner 上永远空跑）。
- M1511 删掉分类函数里「通道拿不到读数」那一支 ⇒ 同一条落到 `今天无证人` ⇒ 与声明不符 ⇒ 红。
        钉的是 dispatch 要的那句话：**某条声称能判的通道拿不到读数就红**，不许悄悄换个态继续绿。
- M1512 把「折叠期改 alpha」那一扫的谓词改成只看 alpha 半边（丢掉与折叠路径的合取）⇒
        交集从 0 变 1 ⇒ 「透明区alpha归零」「框架只在透明之后缩一次」两条实测变 `runner可判` ⇒ 红。
        这一把钉的是**本轮自己犯过的错**：第一版谓词写的是「同文件里出现 Collapse 字样 + 出现 isOpaque」，
        于是 `AppDelegate`（建折叠控制器 + 按 D4a 写 isOpaque=false）被算成"折叠期间改 alpha"，
        两条声明当场被实测推翻 ⇒ 交集必须从两个独立数推出来，不能靠一个模糊的共现。

用法：python3 .scratch/motion-audit-2/mutate_r575.py M1509   （一次一把，跑完自动还原）
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

ROW8_OLD = ('            D12Clause(title: "屏上帧间隔不超标", channel: "真机60fps录屏", prerequisite: "不适用",\n'
            '                      needsRealScreen: true, declared: .realScreenOnly),\n')
DECL_OLD = 'needsRealScreen: true, declared: .realScreenOnly),'
DECL_NEW = 'needsRealScreen: true, declared: .judgeableOnRunner),'
BRANCH_OLD = '        if !channelReads { return needsRealScreen ? .realScreenOnly : .noWitnessToday }\n'
CONJ_OLD = '            return folds && alpha'
CONJ_NEW = '            return alpha'

ARMS = [
    ("M1509", "从八条表里删掉一条声明 ⇒ 条数 8→7 ⇒「八条一条不许少」红",
     H, ROW8_OLD, "", "swift"),
    ("M1510", "把「屏上帧间隔不超标」的声明从 只能真机 抬成 runner可判 ⇒ 与实测不符 ⇒ 红",
     H, DECL_OLD, DECL_NEW, "swift"),
    ("M1511", "删掉分类函数「通道拿不到读数」那一支 ⇒ 同一条落到 今天无证人 ⇒ 与声明不符 ⇒ 红",
     H, BRANCH_OLD, "", "swift"),
    ("M1512", "「折叠期改 alpha」那一扫丢掉与折叠路径的合取 ⇒ 交集 0→1 ⇒ 两条实测变 runner可判 ⇒ 红",
     H, CONJ_OLD, CONJ_NEW, "swift"),
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
        print("用法: mutate_r575.py " + "|".join(a[0] for a in ARMS))
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
        if ("D12_CHANNEL_MAP" in line or "error: -[" in line or "XCTAssert" in line):
            print("  读数:", line.strip()[:250])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
