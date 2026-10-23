#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R321 的变异表：三把刀钉的是**页底参照那三道闸**（M919-M921）。

这一轮修的是尺：`QUICKPICK_SELARM` 在 runner 上判红，而红的原因是"药丸右侧那一格
在 1× 那台机器上根本不是页底"（它落在滚动条槽上：暗档众数 (61,61,61) 占 65%，
而那一台自己的全帧页底档是 30）。修法是两块候选窗 + 三道闸。

闸写出来不等于有牙。三把刀各把一道闸拆掉，被拆的那一格必须**由指名它的用例红**：

  M919 拆第二道闸（档必须与全帧页底档同档） ⇒ `testRunnerShapedScrollerBandIsRejectedByName` 红
       —— 这一把同时是"错的参照物照样报出落点"那朵假绿的证人：runner 今天就是这样过了闸的。
  M920 把候选窗的偏移退回裸像素（不乘倍率） ⇒ `testPageBandOffsetsAreBackingScaleRelative` 红
  M921 把第一道闸（占比地板）松成恒不拦 ⇒ `testInkContaminatedBandsStillDeclineOnShareFloor` 红
       —— 拦下去的理由必须换成第二道闸，那一格的断言钉的是**理由**而不是"有没有红"。

三把都打在 `UICaptureHarness.swift` 的 `choosePageArm` / `pageBands` 上，判据在
`QuickPickSelectionArmTests`（9 格）；管线级那一卷 `testQuickPickSelectionPillAgainstSystemArms`
不在表里 —— 它本机两档都落在 nonKey，拆哪道闸它都不动（这正是"要配合成臂"的理由）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r321.py [M919 M920 M921]
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
FILTER = u"QuickPickSelectionArmTests"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

# ② 第二道闸整块不拦（`delta` 与页底档的差永远小于 Int.max ⇒ 槽也能当页底）。
NEEDLE_919 = u"            if delta >= minDelta {\n"
REPL_919 = u"            if delta >= Int.max {\n"

# ① 候选窗的偏移退回裸像素：2…12 直接当 px 用，不再按这一台的倍率换算。
NEEDLE_920 = (u"        let near = max(1, Int((2.0 * scale).rounded()))\n"
              u"        let far = max(near + 2, Int((12.0 * scale).rounded()))\n")
REPL_920 = (u"        let near = 2\n"
            u"        let far = 12\n")

# ① 占比地板松成恒不拦（墨混进窗里也照样放行）。
NEEDLE_921 = u"            if probe.share < floor {\n"
REPL_921 = u"            if probe.share < 0 {\n"

ARMS = [
    ("M919", u"尺：拆掉「这块窗得真的是页底」那道闸 ⇒ runner 那种槽必须重新被当成页底",
     HARNESS, NEEDLE_919, REPL_919, u"testRunnerShapedScrollerBandIsRejectedByName"),
    ("M920", u"尺：候选窗偏移退回裸像素 ⇒ 倍率换算那格必须红",
     HARNESS, NEEDLE_920, REPL_920, u"testPageBandOffsetsAreBackingScaleRelative"),
    ("M921", u"尺：把占比地板松成恒不拦 ⇒ 混墨那格必须红，而且红在「占比」这个理由上",
     HARNESS, NEEDLE_921, REPL_921, u"testInkContaminatedBandsStillDeclineOnShareFloor"),
]
TARGETS = sorted({a[2] for a in ARMS})


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
        print("ARG_ERROR 不认识这些臂号：%s（认识的是 %s）"
              % (", ".join(unknown), ", ".join(sorted(known))))
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
    print("BASELINE_GREEN Executed=%d（9 格真值表已签）" % n)

    caught = 0
    mismatch = 0
    not_run = 0
    for arm_id, why, target, old, new, expect in arms:
        text = read(target)
        if text.count(old) != 1:
            not_run += 1
            print("%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm_id, text.count(old), old.strip()[:40]))
            continue
        want_text = text.replace(old, new)
        save(target, want_text, bump=clock[0])
        clock[0] += 10.0
        if read(target) != want_text:
            restore()
            not_run += 1
            print("%s NOT_RUN 盘上内容与要下的刀不一致 ⇒ 不许记成 CAUGHT" % arm_id)
            continue
        n, red, names, out = run_suite()
        restore()
        if names and names[0].startswith("NO_SUMMARY_LINE"):
            not_run += 1
            print("%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif "error: " in out and not red:
            not_run += 1
            print("%s NOT_RUN 落刀后编译报错而用例没红 ⇒ 刀坏了，重下" % arm_id)
        elif red and any(expect in name for name in names):
            caught += 1
            print("%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:26], n, ", ".join(names)))
        elif red:
            mismatch += 1
            print("%s MISMATCH 红了但不是它那条（期望 %s，Executed=%d）红在：%s"
                  % (arm_id, expect, n, ", ".join(names)))
        else:
            mismatch += 1
            print("%s PASSED 刀等于没下（Executed=%d，全绿）⇒ 那道闸没有证人" % (arm_id, n))

    n, red, names, _ = run_suite()
    restored = "yes" if (not red and n >= 1
                         and all(read(q) == base for q, base in originals.items())) else "no"
    print("CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print("RESTORE_FAILED Executed=%d 红=%s" % (n, ", ".join(names)))
    if not_run or mismatch:
        print("NOT_RUN=%d MISMATCH=%d ⇒ 这支表不算过关" % (not_run, mismatch))
    return 0 if caught == len(arms) and restored == "yes" and not not_run and not mismatch else 1


if __name__ == "__main__":
    sys.exit(main())
