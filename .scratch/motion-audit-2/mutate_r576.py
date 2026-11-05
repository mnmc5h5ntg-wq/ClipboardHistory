#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R576 变异表 M1513–M1515：本轮落的是折叠规格 §3 第②段 / BACKLOG **651** 那条机器差 ——
把「主窗冷态 `子层=-1`（runner）vs `1`（本机）」做成**按机器登记的观测值**，并用三臂把三种解释分开排。

判据对象：`UICaptureTests/testTheLayerTreeColdStateIsRegisteredPerMachineAndTheThreeExplanationsAreSeparated`
（通道串 `LAYER_TREE_COLD` / `LAYER_TREE_COLD_MECH` / `LAYER_TREE_COLD_SUMMARY`）。
本机 2x 现读：主窗甲=层树建了没画进料、甲同进程第二次=同、乙（上屏那一步）=同、**丙（只递归 wantsLayer）=层树没建**、
浮层甲=层树建了没画进料、夹具那步之后未画比例=0.3586 ⇒ 解释①被否（同台乙/浮层建得出树）、③被否（第二次逐字同）、
②**未排干**（本机甲本来就有树 ⇒ 没有反差可判；那一台甲=层树没建，反差要由 runner 那一跑给）。

三把各钉本轮一条**真读到的事**：
- M1513 手改登记值（主窗 2.00x 那一支从"建了没画进料"改成"层树没建"）⇒ 本机实测与登记不符 ⇒ 红。
        钉 dispatch ② 那句「登记值只由那一跑自己改，不许本机手改」。
- M1514 摘掉夹具快门那一步（`contentView.cacheDisplay(in:to:)`）⇒ 未画比例=1.0 ⇒ 那条前置断言红。
        钉的是 651/653 那条结论的另一半：「第③段逐帧判据靠夹具必经前置」——前置没了就必须红，不许静默通过。
        ⚠ 这一把与 R574 的 M1505 打在**同一行**上（同一个必经点），但红的是**本轮新格的另一条断言**；
        两把各自有效，是因为两条断言读的是同一行的两个不同后果（产物 alpha vs 未画比例）。
- M1515 把解释③那一条从处置表里摘掉（不写进字典）⇒ 条数 3→2 ⇒「三种解释必须逐条给处置」红。
        钉的是"少一条解释就等于没排除"：把排不掉的解释删掉不是进展，是把问题藏起来。

撤掉不登记的探测刀（空刀，不占号）：把 `sameMachineCanBuildTree` 恒置 false ⇒ 解释①换成"等runner"，
但没有任何断言读它 ⇒ 不会红 ⇒ 空刀。

用法：python3 .scratch/motion-audit-2/mutate_r576.py M1513   （一次一把，跑完自动还原）
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

REG_OLD = '        if tree == "主窗" { return rounded == 2.00 ? .treeBuiltWithoutContents : .treeNotBuilt }'
REG_NEW = '        if tree == "主窗" { return rounded == 2.00 ? .treeNotBuilt : .treeNotBuilt }'
CAPTURE_OLD = ('            window.appearance?.performAsCurrentDrawingAppearance {\n'
               '                contentView.cacheDisplay(in: bounds, to: rep)\n'
               '            }\n')
CAPTURE_NEW = '            window.appearance?.performAsCurrentDrawingAppearance {\n            }\n'
EXPL_OLD = ('        out["③夹具顺序"] = (secondRenderSameProcess == mainArmA)\n'
            '            ? .ruledOut(by: "同进程第二次渲染与第一次逐字同") : .supported(by: "第二次与第一次不同")\n')
EXPL_NEW = ('        _ = (secondRenderSameProcess == mainArmA)\n'
            '            ? LayerTreeColdExplanationVerdict.ruledOut(by: "同进程第二次渲染与第一次逐字同")\n'
            '            : LayerTreeColdExplanationVerdict.supported(by: "第二次与第一次不同")\n')

ARMS = [
    ("M1513", "手改主窗 2.00x 的登记值 ⇒ 实测与登记不符 ⇒ 红（登记值只由那一跑改）",
     H, REG_OLD, REG_NEW, "swift"),
    ("M1514", "摘掉夹具快门那一步 cacheDisplay ⇒ 未画比例=1.0 ⇒ 前置那条断言红",
     H, CAPTURE_OLD, CAPTURE_NEW, "swift"),
    ("M1515", "把解释③从处置表里摘掉 ⇒ 条数 3→2 ⇒「三种解释逐条给处置」红",
     H, EXPL_OLD, EXPL_NEW, "swift"),
]

FILTER = ("UICaptureTests/testTheLayerTreeColdStateIsRegisteredPerMachineAndTheThreeExplanationsAreSeparated")


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
        print("用法: mutate_r576.py " + "|".join(a[0] for a in ARMS))
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
        if ("LAYER_TREE_COLD" in line or "error: -[" in line or "XCTAssert" in line):
            print("  读数:", line.strip()[:250])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
