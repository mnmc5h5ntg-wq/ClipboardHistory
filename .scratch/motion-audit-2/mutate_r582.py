#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R582 变异表 M1529/M1530/M1531：本轮落的是**按机器登记**与**对账口径**这两件新仪器各自会红的那一半。

判据对象：
- `UICaptureTests/testTheD12HardClausesEachNameAChannelThatEitherReadsOrIsNamed`（新通道串 `D12_SHAPE_SCAN_REGISTRY`）
- `UICaptureTests/testTheD12ShapeScanRegistryIsPerMachineAndCannotMuteTheRulers`（机器键三档 + 判法四分支 + 两棵临时树）
- `scripts.tests.test_red_name_reconciliation`（对账门的真值表 + 端到端）

本机现读（`/tmp/r582/d12_filter.log`）：
`D12_SHAPE_SCAN … 折叠路径剥注释=1 折叠路径带注释=2 折叠路径差=1 …`
`D12_SHAPE_SCAN_REGISTRY 机器=local:macbook-air.local 登记=1_2 实测=1_2 判=一致 红路=无 另一台已登记=否`
`D12_SHAPE_SCAN_REGISTRY_TABLE 机器键三档=一致 判法四分支=齐 临时树=2 注释树两档=0_1 真码树两档=1_1 解耦=登记一致而地板读0`
`RED_NAME_MEASURE 节=R581 红名=11 计入行=6 编号去重=6 不计入=0 未标=5 口径=无`（与上一轮手写的 11/6/对不上 5 逐字相同）
`RED_NAME_MEASURE 节=R580 红名=16 计入行=11 编号去重=9 …`（与那轮手写的 16/9 相同 ⇒ 门的口径认的是同一个对象）

三把刀各钉一条，且**各只动一对量的一边**（落刀前自问句写在每臂的理由里）：
- M1529 只动**登记**那一边：把本机登记值从 (1,2) 改成 (9,9)，实测一字未动
        ⇒ 主判据那条登记比对必须红；而 `D12_SHAPE_SCAN` 那四对读数与两档断言**不该跟着红**
        （这一条就是"登记只管数值、不能让尺变哑"的证人 —— 红的必须是登记那一格）。
- M1530 只动**实测的剥注释那一侧**：把 `shapeScanReadingPair` 的 stripped 钉成 0（带注释那一侧不动）
        ⇒ 地板断言 `折叠路径剥注释>=1` 必须红、临时树那两档必须红；
        而登记比对读到的实测变成 (0,2) ⇒ 也会判「翻了」⇒ 两格一起红是对的（同一条坏法在两处都有牙），
        关键是**带注释那一侧一字未动** ⇒ 与 M1529 不是同一边。
- M1531 只动**门**那一边：把「未标必须红」改恒假（`return 0`）⇒ 对账门的端到端那一格必须红；
        分类器本身未动 ⇒ 数还是那些数，坏的是"数完不判"。

用法：python3 .scratch/motion-audit-2/mutate_r582.py M1529   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
逐把的 `rc/caught/clean/预检` 写进 `/tmp/r582/knife_status.txt`（派单 ③①：输出不接 head、每把单独取退出码、
rc 由被测命令直接产生 —— 这个文件里的 rc 就是 `run()` 那一次 subprocess 的返回码，中间没有 echo）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
STATUS = "/tmp/r582/knife_status.txt"

ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

T_SWIFT = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"
T_GATE = "scripts/red_name_reconciliation.py"
FILTER = "UICaptureTests/testTheD12"
GATE_TEST = "scripts.tests.test_red_name_reconciliation"

# —— M1529：只动登记那一边（实测一字未动）。
REG_OLD = '        case "local:macbook-air.local", "github-runner": return (1, 2)\n'
REG_NEW = '        case "local:macbook-air.local": return (9, 9)\n'

# —— M1530：只动实测的剥注释那一边（带注释那一侧不动）。
PAIR_OLD = '        let stripped = strippingScan(true)\n'
PAIR_NEW = '        let stripped = 0\n'

# —— M1531：只动门那一边（分类器不动）。
GATE_OLD = '    return 0 if unmarked == 0 else 1\n'
GATE_NEW = '    return 0\n'

ARMS = [
    ("M1529", "登记值 (1,2) 改成 (9,9)，实测未动 ⇒ 登记比对必须红，而两档断言不许跟着红（解耦的证人）",
     T_SWIFT, REG_OLD, REG_NEW, "swift"),
    ("M1530", "把实测的剥注释那一侧钉成 0，带注释那一侧未动 ⇒ 地板那条必须红、临时树两档必须红",
     T_SWIFT, PAIR_OLD, PAIR_NEW, "swift"),
    ("M1531", "把「未标必须红」改恒假，分类器未动 ⇒ 对账门的端到端那一格必须红",
     T_GATE, GATE_OLD, GATE_NEW, "python"),
]


def run(kind):
    if kind == "swift":
        proc = subprocess.run(["swift", "test", "--filter", FILTER],
                              cwd=PKG, capture_output=True, text=True, env=ENV, timeout=2400)
    else:
        proc = subprocess.run([sys.executable, "-m", "unittest", GATE_TEST],
                              cwd=ROOT, capture_output=True, text=True, env=ENV, timeout=900)
    out = proc.stdout + proc.stderr
    if kind == "swift":
        if "error:" in out and "Executed " not in out:
            return "ERROR", proc.returncode, out
        if "Executed " not in out:
            return "DID-NOT-RUN", proc.returncode, out
    else:
        if "Ran " not in out:
            return "DID-NOT-RUN", proc.returncode, out
    return ("PASSED" if proc.returncode == 0 else "CAUGHT"), proc.returncode, out


def record(line):
    with open(STATUS, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    arm = next((a for a in ARMS if a[0] == wanted), None)
    if arm is None:
        print("用法: mutate_r582.py " + "|".join(a[0] for a in ARMS))
        return 2
    mid, why, rel, old, new, kind = arm
    path = os.path.join(ROOT, rel)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    code, pre_rc, out = run(kind)
    print("%s 预检: %s (rc=%d)" % (mid, code, pre_rc))
    precheck = code
    if code != "PASSED":
        print(out[-1500:])
        record("r582/%s precheck=%s 未落刀" % (mid, code))
        return 2
    hits = text.count(old)
    if hits != 1:
        print("needle 命中 %d ⇒ 不是恰好一次，不下刀" % hits)
        record("r582/%s needle=%d 未落刀" % (mid, hits))
        return 1
    open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
    try:
        code, post_rc, out = run(kind)
    finally:
        open(path, "wb").write(orig)
    print("%s: %s (rc=%d) | %s" % (mid, code, post_rc, why))
    for line in out.splitlines():
        if ("D12_SHAPE_SCAN" in line or "XCTAssert" in line or "register" in line.lower()
                or "RED_NAME" in line or "AssertionError" in line or "error: -[" in line
                or "Ran " in line or "Executed " in line):
            print("  读数:", line.strip()[:300])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    record("r582/%s rc=%d caught=%d clean=%d precheck=%s post=%s"
           % (mid, post_rc, 1 if code == "CAUGHT" else 0, 1 if clean else 0, precheck, code))
    if code != "CAUGHT" or not clean:
        print(out[-1500:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
