#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R580 变异表 M1523–M1526：本轮落的是折叠规格 §3 第②段 / BACKLOG **654** 那张 D12 映射表的**活门**。

判据对象（两条，`--filter UICaptureTests/testTheD12` 同时命中）：
- `UICaptureTests/testTheD12HardClausesEachNameAChannelThatEitherReadsOrIsNamed`（新通道串 `D12_LIVE_GATE`）
- `UICaptureTests/testTheD12LiveGateFlipsWhenAnInjectedObjectArrives`（新通道串 `D12_LIVE_GATE_PROBE`）

本机现读（`/tmp/r580/d12_after.log`）：
`D12_LIVE_GATE A按名字文件数=0 B按形状文件数=0 判=缺席 红路=无 待翻行数=7 本轮该翻=0 分母=8`
`D12_LIVE_GATE_PROBE 树=7 驱动行翻=5 alpha行翻=2 全翻=7 真机行被翻=否 瞎态判=现扫瞎_只有B认得_B=1 注释喂A=0 空态A=0 空态B=0 读不到处数=2 判法分支数=5 分母=8`
一次性探针（不入库，`/tmp/r580/probe_A_arrived.log`、`/tmp/r580/probe_blind_endtoend.log`）：
往产品树塞一份假驱动 ⇒ 主判据当场 6 朵红（五行逐条 + 那条「本轮该翻=5」）；换成「只在代码里出现真模糊 API」
⇒ `判=现扫瞎_只有B认得_B=1` 那条红路端到端点着。两份假文件都已删除，`git ls-files --others Sources` 为空。

四把刀各钉本轮一条真读到的事，落点全部在**环境无关的纯函数**上（runner 上同样红）：
- M1523 把活门「现扫瞎」那一条红路摘掉 ⇒ 注入 B 的形状时门被放行 ⇒ 合成档 4/4b 红。
        钉的是 dispatch 那句「把活门摘掉必须红」。落刀前自问"我只动了这一对量的一边吗"：
        只改「现扫瞎」那一支的匹配串，「目录读不到」那一支一字未动。
- M1524 把翻面机的驱动那一支摘掉（`&& rows.isEmpty`）⇒ 注入驱动后名单空 ⇒ 档 1/3 红。
        钉的是「那一行必须翻」这台机器本身；alpha 那一支一字未动（两半各钉一半，不捆臂 —— M1516 空刀的教训）。
- M1525 把 B 那把尺对任何源码都读成不命中 ⇒ 档 4 的 `B=1` 红。
        钉的是「第二条证人独立且真认得它声称的那个形状」；`.metal` 那条计数路径未动 ⇒ 4b 仍绿，
        正好证明这两条不是同一把尺。
- M1526 把 A 退回**不剥注释** ⇒ 档 1b 那句注释造出的假对象喂饱 A ⇒ 红。
        钉的是探针实测到的那条坏法（不剥注释时一句注释能凭空翻五行、并短路掉「现扫瞎」那条红）。

用法：python3 .scratch/motion-audit-2/mutate_r580.py M1523   （一次一把，跑完自动还原）
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

BLIND_OLD = '        if verdict.hasPrefix("现扫瞎") { return "对象已出现而按名字那把尺看不见_那张表翻不动" }\n'
BLIND_NEW = '        if verdict.hasPrefix("现扫瞎_这一支永不到来") { return "对象已出现而按名字那把尺看不见_那张表翻不动" }\n'

FLIP_OLD = '            if driverRows && angleArrived { out[row.title] = "runner可判" }\n'
FLIP_NEW = '            if driverRows && angleArrived && rows.isEmpty { out[row.title] = "runner可判" }\n'

# ⚠ 这两根的 needle 里用的局部量名是 `code` 而不是 `text`：本轮先写成 `let text = Self.codeOnly(rawText)`，
# 于是 R125 那把老刀 M628 的 needle（同一行文本，全仓唯一）命中数从 1 变 3 ⇒ needle 预检报 bad=1。
# 这是"接班者改了一行源码，前任的表就空转"那一族（预检存在的理由）。改的是**本轮新写的那两把**，
# 不动老表 —— 老表的 needle 由它自己的账守着。
SHAPE_OLD = ('        return code.contains("CIFilter") || code.contains("CIGaussianBlur")\n'
             '            || code.contains("AEAGaussianBlur") || code.contains("MTLRenderPipelineState")\n'
             '            || code.contains("CAFilter") || code.contains("layer.filters")\n')
SHAPE_NEW = '        return code.isEmpty   // 刀：B 那把尺对任何源码都读不出形状\n'

# R581 重钉：R581 把 A/B 两把尺从 `codeOnly` 换成 `stripShapeComments`（并加了 `stripping:` 参数）
# ⇒ 这根 needle 命中 0（`mutate_needle_precheck` 在**跑之前**抓到，bad=1）。针腐烂重钉必复跑旧表：
# 下面这对是同一件事在新形状上的钉子（A 退回不剥注释 ⇒ 1b 与 1c 都要红），needle 仍然只命中一次。
ANNO_OLD = ('        let code = stripping ? Self.stripShapeComments(rawText) : rawText\n'
            '        return code.contains("foldAngle") || code.contains("blurRadius")\n')
ANNO_NEW = ('        let code = rawText   // 刀：A 退回不剥注释\n'
            '        return code.contains("foldAngle") || code.contains("blurRadius")\n')

ARMS = [
    ("M1523", "活门「现扫瞎」那条红路摘掉 ⇒ 注入 B 的形状被放行 ⇒ 合成档 4/4b 红",
     T, BLIND_OLD, BLIND_NEW, "swift"),
    ("M1524", "翻面机驱动那一支摘掉 ⇒ 注入驱动后名单空 ⇒ 合成档 1/3 红",
     T, FLIP_OLD, FLIP_NEW, "swift"),
    ("M1525", "B 那把尺对源码恒不命中 ⇒ 瞎态注入档读不到形状 ⇒ 档 4 红（4b 的 .metal 计数未动）",
     T, SHAPE_OLD, SHAPE_NEW, "swift"),
    ("M1526", "A 退回不剥注释 ⇒ 一句注释造出假对象 ⇒ 档 1b 红",
     T, ANNO_OLD, ANNO_NEW, "swift"),
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
        print("用法: mutate_r580.py " + "|".join(a[0] for a in ARMS))
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
        if ("D12_LIVE_GATE" in line or "error: -[" in line or "XCTAssert" in line):
            print("  读数:", line.strip()[:300])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
