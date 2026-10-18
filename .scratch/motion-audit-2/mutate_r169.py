#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R168 的变异表：放行谓词的四根轴 + 活体调用点 + 门槛单一来源（M675-M679）。

每把刀都对准本轮真实写下的那条判断，不是凭空造的错法：

  M675 谓词少看一根轴（丢掉 `hostHeightPt == requested`）
       ⇒ "窗口没铺满"那种形状会被放行。这一把证明**第二根轴是承重的**，
         而不是 R167 那种"两种实现都绿"的空对照。
  M676 谓词丢掉高帧下界（`requested >= tallFixtureHeightFloor` 改成恒真）
       ⇒ 540 那一档（runner 上画得出来）也走出口 ⇒ 出口成了万能挡箭牌。
  M677 谓词丢掉族判据（`family == "settings"` 改成恒真）
       ⇒ 浮层/菜单栏的空帧也能被放行。
  M678 未画循环里**不调用**谓词（`let would = false`）
       ⇒ 行为一模一样、红一模一样，但 `testBlankFrameLoopCallsThePredicate` 必须红：
         "抽出来了却没接线"与"没抽"同形（R167 空对账那一族的正向版）。
  M679 `render` 的高帧门槛改回字面量 1000
       ⇒ 行为不变，但门槛从此有两个来源，下一次改一个忘一个时出口会悄悄换档。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r169.py [M675 ...]
退出码：0 = 选中的刀全 CAUGHT 且还原后绿；1 = 有刀等于没下（PASSED）或还原后仍红；2 = 臂号不认识。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
PKG = os.path.join(ROOT, "ClipboardHistory")
HARNESS = os.path.join(PKG, "Tests", "ClipboardHistoryAppTests", "UICaptureHarness.swift")
FILTER = "DailyCopyHeatmapWidthBudgetTests"   # 本轮判据卷
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TOKENS = os.path.join(PKG, "Sources", "ClipboardHistoryApp", "Utilities", "VisualTokens.swift")
POLICY = os.path.join(PKG, "Sources", "ClipboardHistoryApp", "Utilities", "DailyCopyHeatPolicy.swift")

ARMS = [
    # 令牌是承重的：改它必须有判据红（R169 的宽度预算整个建立在 cell / spacing 上）。
    ("M684", TOKENS,
     u"static let cell: CGFloat = 11",
     u"static let cell: CGFloat = 13", "CAUGHT"),
    # 预算的对照物是**夹具自己**：夹具变宽 ⇒ "多两周顶破"必须翻面（否则那条边界是抄来的数）。
    ("M685", HARNESS,
     u'Fixture("heatmap-populated", NSSize(width: 430, height: 250), contentMustFit: true)',
     u'Fixture("heatmap-populated", NSSize(width: 460, height: 250), contentMustFit: true)', "CAUGHT"),
    # 有人抬窗口周数 ⇒ 这条预算必须红，而不是等 `contentMustFit` 在捕获卷里才发现。
    ("M686", POLICY,
     u"static let defaultWindowWeeks = 26",
     u"static let defaultWindowWeeks = 28", "CAUGHT"),
]

FILTER = "DailyCopyHeatmapWidthBudgetTests"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}


def read(path):

    return open(path, encoding="utf-8").read()


def save(path, text):
    open(path, "w", encoding="utf-8").write(text)


def run_filter():
    """跑那一卷，返回 (跑了几个用例, 红的用例名列表, 是否崩在编译期)。"""
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", FILTER],
                          cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = re.findall(r"Executed (\d+) tests?, with (\d+) failure", out)
    ran = int(executed[-1][0]) if executed else 0
    failures = int(executed[-1][1]) if executed else 0
    red_names = sorted({m.group(1) for m in
                        re.finditer(r"Test Case '-\[.*\.\w+ (\w+)\]' failed", out)})
    build_broke = "error:" in out and ran == 0
    return ran, red_names, build_broke


def is_red():
    ran, names, build_broke = run_filter()
    return (ran >= 1 and bool(names)), names, ran, build_broke


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        print(u"ARG_ERROR 不认识这些臂号：%s（认识的是 %s）"
              % (", ".join(unknown), ", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print(u"ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2

    originals = {p: read(p) for p in (HARNESS, TOKENS, POLICY)}
    red, names, ran, build_broke = is_red()
    if red or build_broke or ran < 4:
        # `Ran 0` / 编译崩 / 用例少于 5 —— 都是"探针坏了"，此时后面的 CAUGHT 不说明任何事。
        print(u"PRECHECK_FAILED 未落刀时已红或跑不满 4 格：%s（ran=%d build_broke=%s）"
              % (", ".join(names) or u"-", ran, build_broke))
        return 1
    print(u"BASELINE_GREEN ran=%d" % ran)

    caught = 0
    for arm_id, target, old, new, expect in arms:
        text = read(target)
        hits = text.count(old)
        if hits != 1:
            print(u"%s NOT_RUN 锚点命中 %d 次（要 1 次）—— 刀没下，不许记成 CAUGHT" % (arm_id, hits))
            continue
        save(target, text.replace(old, new))
        red, names, ran, build_broke = is_red()
        for p, base in originals.items():
            save(p, base)
        if build_broke:
            print(u"%s NOT_RUN 编译崩，不是判据红 ⇒ 刀形不对，记 NOT_RUN 不记 CAUGHT" % arm_id)
        elif red and expect == "CAUGHT":
            caught += 1
            print(u"%s CAUGHT 红在：%s（ran=%d）" % (arm_id, ", ".join(names), ran))
        else:
            print(u"%s PASSED 刀等于没下（ran=%d 全绿）" % (arm_id, ran))

    red, names, ran, build_broke = is_red()
    restored = u"yes" if (not red and not build_broke and all(read(p) == b for p, b in originals.items())) else u"no"
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == u"no":
        print(u"RESTORE_FAILED 红在：%s" % u", ".join(names))
    return 0 if caught == len(arms) and restored == u"yes" else 1


if __name__ == "__main__":
    sys.exit(main())
