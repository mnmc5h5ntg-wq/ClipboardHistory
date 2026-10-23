#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R320 的变异表：两把刀钉的是**正对照自己**（M917-M918）。

这一轮的结论是"热图 hover 提示在离屏产物里没有通道"（`HEATMAP_TOOLTIP_CHANNELS` 四屏×档全 0）。
一个"全 0"能定罪吗？只有当那把尺被证明读得到的时候 —— 所以本轮的牙不钉在产品上，
钉在**证人**上：把尺弄瞎一格，正对照那一格必须红（D-168 的正向用法 + R103 的"存在性判据"）。

  M917 让"没有记录"那一型文案不再被认成热图提示 ⇒ 对照里那条 accessibilityLabel 掉出计数 ⇒ 红
  M918 让整条无障碍通道读不到任何东西（`accessibilityLabel` 换成常量 nil）⇒ 对照红

两把都打在 `UICaptureHarness.swift` 的 `tooltipChannels` 上：它同时是这一轮那条 0 读数的分母。
跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r320.py [M917 M918]
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
HARNESS = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                       "UICaptureHarness.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
FILTER = u"UICaptureTests/testHeatmapTooltipChannelProbe"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

# 多行锚点：`if heatShaped(label) {` 这一行在本文件里出现两次（子树版与无障碍树版各一次），
# 单行锚会命中 2 ⇒ NOT_RUN（刀根本没下）。带上前面的 toolTip 那两行才是子树版那一条。
NEEDLE_917 = (u"            if v.toolTip?.isEmpty == false { anyTips += 1 }\n"
              u"            if heatShaped(v.toolTip) { tips += 1 }\n"
              u"            let label = v.accessibilityLabel()\n"
              u"            if label?.isEmpty == false { anyLabels += 1 }\n"
              u"            if heatShaped(label) {\n")
REPL_917 = (u"            if v.toolTip?.isEmpty == false { anyTips += 1 }\n"
            u"            if heatShaped(v.toolTip) { tips += 1 }\n"
            u"            let label = v.accessibilityLabel()\n"
            u"            if label?.isEmpty == false { anyLabels += 1 }\n"
            u"            if heatShaped(label) && label?.contains(\"复制\") == true {\n")
NEEDLE_918 = u"            let label = v.accessibilityLabel()\n"
REPL_918 = u"            let label: String? = nil\n"

ARMS = [
    ("M917", u"尺：把「没有记录」那一型文案不再认成热图提示 ⇒ 正对照的无障碍计数必须掉 ⇒ 红", HARNESS,
     NEEDLE_917, REPL_917, "CAUGHT"),
    ("M918", u"尺：把整条无障碍通道读成 nil ⇒ 正对照必须红（否则那条 0 读数是尺瞎了）", HARNESS,
     NEEDLE_918, REPL_918, "CAUGHT"),
]
TARGETS = sorted({a[2] for a in ARMS})
EXPECTED = u"testHeatmapTooltipChannelProbe"


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        os.utime(path, (bump, bump))


def run_suite():
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", FILTER],
                          cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = [int(m.group(1)) for m in re.finditer(r"Executed (\d+) tests?", out)]
    n = max(executed) if executed else 0
    summary = re.findall(r"Executed \d+ tests?, with (?:\d+ tests? skipped and )?(\d+) failures?", out)
    failures = sum(int(v) for v in summary) if summary else -1
    names = sorted({m.group(1) for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    if failures < 0:
        return n, False, ["NO_SUMMARY_LINE（读不到失败数）"], out
    return n, (n >= 1 and failures > 0), names, out


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        print("ARG_ERROR 不认识这些臂号：%s（认识的是 %s）" % (", ".join(unknown), ", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print("ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
    originals = {path: read(path) for path in TARGETS}
    clock = [time.time() + 10.0]

    def restore():
        for path, base in originals.items():
            save(path, base, bump=clock[0])
        clock[0] += 10.0

    restore()
    n, red, names, _ = run_suite()
    if red or n == 0:
        restore()
        print("PRECHECK_FAILED 未落刀时基线不绿（Executed=%d 红=%s）⇒ 后面的 CAUGHT 不说明任何事"
              % (n, ", ".join(names)))
        return 1
    print("BASELINE_GREEN Executed=%d（正对照已签）" % n)

    caught = 0
    for arm_id, why, target, old, new, expect in arms:
        text = read(target)
        if text.count(old) != 1:
            print("%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm_id, text.count(old), old.strip()[:40]))
            continue
        want_text = text.replace(old, new)
        save(target, want_text, bump=clock[0])
        clock[0] += 10.0
        if read(target) != want_text:
            restore()
            print("%s NOT_RUN 盘上内容与要下的刀不一致 ⇒ 不许记成 CAUGHT" % arm_id)
            continue
        n, red, names, out = run_suite()
        restore()
        if names and names[0].startswith("NO_SUMMARY_LINE"):
            print("%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif "error: " in out and not red:
            print("%s NOT_RUN 落刀后编译报错而用例没红 ⇒ 刀坏了，重下" % arm_id)
        elif red and EXPECTED in " ".join(names):
            caught += 1
            print("%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:26], n, ", ".join(names)))
        elif red:
            print("%s MISMATCH 红了但不是它那条（Executed=%d）红在：%s" % (arm_id, n, ", ".join(names)))
        else:
            print("%s PASSED 刀等于没下（Executed=%d，全绿）⇒ 那条 0 读数没有证人" % (arm_id, n))

    n, red, names, _ = run_suite()
    restored = "yes" if (not red and n >= 1
                         and all(read(q) == base for q, base in originals.items())) else "no"
    print("CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print("RESTORE_FAILED Executed=%d 红=%s" % (n, ", ".join(names)))
    return 0 if caught == len(arms) and restored == "yes" else 1


if __name__ == "__main__":
    sys.exit(main())
