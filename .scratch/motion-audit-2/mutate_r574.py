#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R574 变异表 M1505–M1508：本轮落的是折叠规格 §3 第②段的 **653** ——
把 651 那张机制表用到「采集夹具那 356 帧走的这条通道」上（对象是夹具自己的必经点 `render`，
不是仓库外再搭一棵树：R98 数过所有拍帧路的必经点只有这一处，调用方各自复制就是「25 份迟早会漂开的副本」）。

判据对象：
  · `UICaptureTests/testTheFrameChannelPrerequisiteIsClassifiedPerTreeOnBothMachines`
    （两棵产品树各读：类 / 根类名 / 子层冷 / contents冷 / 通道未画比例 / 产物 alpha 三分数 / 三态前置判 / 产物判）
  · `scripts/tests/test_ledger_round_headings`（R574 ④ 的修复证人：七本台账里逐字重复的轮次标题行会红）

四把各钉本轮一条**真读到的数**：
- M1505 摘掉夹具快门那一步（`contentView.cacheDisplay(in:to:)`）⇒ 整幅没画 ⇒ 前置判=画不出 ⇒ 新格红。
        钉的是这一格的主结论：这条通道今天**靠那一步**把类 B 的树变成可 render（不是"它天生画得出"）。
- M1506 摘掉 `flattenedPNG` 写盘前那层窗口底色 ⇒ 产物留住 alpha ⇒ 产物判=产物留alpha ⇒ XCTAssertTrue 红。
        钉的是第二问：第③段那句「alpha 归零」今天不能拿 356 帧的**产物**判。
        这一把只动"产物"那一边，`metrics.transparent`（探针上下文，铺底之前就数好了）一字不动 ⇒ 不是同值空刀。
- M1507 把新尺的标题前缀换成永远不会命中的 `'###### '` ⇒ 现读七本解析到 0 条标题 ⇒ 正对照与现读两格都红
        （钉"尺瞎了必须红"，R99 的空名单不许给绿）。
- M1508 把 hosting view 的识别退回 `NSStringFromClass` 前缀（本轮第一版就是这么写的，当场把主窗那棵
        读成 0 个、类=C）⇒ 类=B 那格红 ⇒ 钉住"类判错会把整条前置结论带偏"。

用法：python3 .scratch/motion-audit-2/mutate_r574.py M1505   （一次一把，跑完自动还原）
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
R = "scripts/ledger_round_headings.py"

CAPTURE_OLD = ('            window.appearance?.performAsCurrentDrawingAppearance {\n'
               '                contentView.cacheDisplay(in: bounds, to: rep)\n'
               '            }\n')
CAPTURE_NEW = '            window.appearance?.performAsCurrentDrawingAppearance {\n            }\n'

PREFILL_OLD = ('        out.setFillColor(windowBackgroundColor(for: appearance))\n'
               '        out.fill(rect)\n')
PREFILL_NEW = '        // 变异：不铺底 ⇒ 产物留住通道里那些未画像素\n'

RULER_OLD = "HEADING_PREFIX = '## '"
RULER_NEW = "HEADING_PREFIX = '###### '"

HOSTING_OLD = '        String(describing: type(of: view)).hasPrefix("NSHostingView")'
HOSTING_NEW = '        NSStringFromClass(type(of: view)).hasPrefix("NSHostingView")'

ARMS = [
    ("M1505", "摘掉夹具快门那一步 cacheDisplay ⇒ 通道未画比例=1 ⇒ 前置判=画不出 ⇒ 新格红",
     H, CAPTURE_OLD, CAPTURE_NEW, "swift"),
    ("M1506", "摘掉写盘前那层窗口底色 ⇒ 产物留住 alpha ⇒ 「产物判=铺平」那条红（第③段判归零没有证人）",
     H, PREFILL_OLD, PREFILL_NEW, "swift"),
    ("M1508", "hosting view 退回按修饰过的 ObjC 名认 ⇒ 主窗那棵读成类 C ⇒ 类=B 那格红",
     H, HOSTING_OLD, HOSTING_NEW, "swift"),
    ("M1507", "新尺的标题前缀换成永不命中的 `'###### '` ⇒ 现读解析到 0 条标题 ⇒ 空名单那格与正对照都红",
     R, RULER_OLD, RULER_NEW, "python"),
]

FILTER = ("UICaptureTests/testTheFrameChannelPrerequisiteIsClassifiedPerTreeOnBothMachines")


def run_python_tests():
    proc = subprocess.run([sys.executable, "-m", "unittest",
                           "scripts.tests.test_ledger_round_headings", "-v"],
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
        print("用法: mutate_r574.py " + "|".join(a[0] for a in ARMS))
        return 2
    mid, why, rel, old, new, kind = arm
    path = os.path.join(ROOT, rel)
    orig = open(path, "rb").read()
    text = orig.decode("utf-8")

    runner = run_python_tests if kind == "python" else run_tests
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
        if ("FRAME_CHANNEL_MECHANISM" in line or "ROUND_HEADINGS" in line
                or "error: -[" in line or "AssertionError" in line):
            print("  读数:", line.strip()[:250])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
