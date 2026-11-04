#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R569 变异表 M1486–M1488：本轮新加的两把尺（离屏 alpha 的按倍率登记表 / 还原那条全局的扫描）。

判据对象 = `TransparencyForensicsTests`：
  · `testTheOffscreenAlphaAnswerIsRegisteredPerScale`（登记表真值表）
  · `testOffscreenChannelMatchesTheRegisteredAlphaAnswerForItsScale`（本机 2x 端到端）
  · `testTheChromeMetricScanKnowsWhatAViolationLooksLike`（分类器真值表 + 合成目录机制级正对照）

三把都改**尺**（本轮没有产品笔），各钉一种"看着像门、其实是洞"的坏法：
- M1486 扫描分类器恒判"不违规"        ⇒ 真值表第一行红 + 合成目录那支违规没被点名 ⇒ 两格同红。
- M1487 2x 那一档登记反了（说成保留 alpha）⇒ 本机端到端那格红（实测=涂成不透明黑）。
- M1488 登记表对所有倍率回 nil        ⇒ 真值表两行红，而端到端那格会走"具名不判"悄悄绿 ⇒
  这一把专门钉"未登记就什么都不判"这个形状：真值表必须比端到端先红。

用法：python3 .scratch/motion-audit-2/mutate_r569.py M1486   （一次一把，跑完自动还原）
退出码：0=CAUGHT 且 RESTORE_CLEAN；1=空刀(PASSED)/没抓到/还原不干净；2=预检没过（判据本来就红）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TESTS = "ClipboardHistory/Tests/ClipboardHistoryAppTests/TransparencyForensicsTests.swift"

VIOLATES_OLD = ('        text.contains("WindowManager.showMainWindow()")\n'
                '            && !text.contains("restoreDetailContentTopInsetForTesting")')
REG_2X_OLD = '        if abs(scale - 2.0) < 0.01 { return .flattensToOpaqueBlack }'
REG_BOTH_OLD = ('        if abs(scale - 2.0) < 0.01 { return .flattensToOpaqueBlack }'
                '   // 本机 Retina，R568/R569 两跑同值\n'
                '        if abs(scale - 1.0) < 0.01 { return .preservesAlpha }'
                '          // CI runner 1x，R569 现读')
ARMS = [
    ("M1486", "扫描分类器恒判不违规 ⇒ 门看不见任何东西", TESTS,
     VIOLATES_OLD, "        false", "swift"),
    ("M1487", "2x 那一档登记写反 ⇒ 本机端到端必须红", TESTS,
     REG_2X_OLD,
     "        if abs(scale - 2.0) < 0.01 { return .preservesAlpha }", "swift"),
    ("M1488", "登记表一律回 nil ⇒ 端到端走具名不判而真值表先红", TESTS,
     REG_BOTH_OLD,
     "        return nil", "swift"),
]

FILTER = ("TransparencyForensicsTests/testTheOffscreenAlphaAnswerIsRegisteredPerScale"
          "|TransparencyForensicsTests/testOffscreenChannelMatchesTheRegisteredAlphaAnswerForItsScale"
          "|TransparencyForensicsTests/testTheChromeMetricScanKnowsWhatAViolationLooksLike")


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
        print("用法: mutate_r569.py " + "|".join(a[0] for a in ARMS))
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
        if ("CHROME_METRIC" in line or "TRANSPARENCY_CHANNEL" in line
                or "OFFSCREEN_ALPHA" in line or "error: -[" in line):
            print("  读数:", line.strip()[:220])
    clean = open(path, "rb").read() == orig
    print("RESTORE_CLEAN=" + ("yes" if clean else "NO"))
    if code != "CAUGHT" or not clean:
        print(out[-1200:])
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
