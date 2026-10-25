#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 的变异表：快捷键录制器那一圈描边的判据（M660-M665），R143 审查轮又补了三把（M670-M672）。

九刀各打在哪里（下面这份是 R143 那次 `CAUGHT=9/9` 的原样读数，不是设想）：

  M660 静置态也画那一圈（`strokeWidth(isRecording:false)` 不再返回 0）
       ⇒ 「静置墨像素必须恰好 0」必须红。这一刀同时是旧帧的对照：它红了而帧还不变，
         说明帧基线量不到这一层（那才是真问题）。
  M661 录制态的颜色换成透明 ⇒ 「录制墨 > 0」与强度带都要红。
  M662 把描边换成整块填充 ⇒ 「内部不许有墨」要红（抓"圈 vs 填充"的那颗牙）。
  M663 撤掉 `.animation(..., value: isRecording)` 那一行 ⇒ **只红**源码守卫那一条
       （R42 那一族：声明了表达而没有驱动 ⇒ 那一格是它唯一的防线）。
  M664 把 `setRecording` 里的判等去掉 ⇒ **只红**「每次转换恰好一次回调」。
  M665 宽度归零 ⇒ 与 M661 红集相同（两把刀都把像素量降到 0，一个动颜色一个动宽度）。
  M670 把 `onRecordingChange` 的闭包抽干（状态不再外传）⇒ **只红**产品入口那一条。
  M671 overlay 钉死在 `isRecording:false` ⇒ 产品入口 + 接线守卫两条。
  M672 去掉 `makeFirstResponder` 失败就回退那道守卫 ⇒ **只红**
       `testRingDoesNotPromiseListeningWhenTheResponderChainRefuses`（R143 F7 的刀）。
       没有这一把，F7 那一处产品修复就只是"我说过我修了"。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r141.py [M660 ...]
退出码：0 = 该下的刀都下了且还原干净；1 = 有刀等于没下 / 预检就红 / 还原后仍红。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
PRODUCT = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                       "Views", "HotKeyRecorderView.swift")
FILTER = "HotKeyRecorderEvidenceTests"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    # 每一刀的 `edits` 是**一组**替换（一处改不动就整刀不下）。
    ("M660", [(u"        isRecording ? VisualStroke.highlight : 0",
               u"        isRecording ? VisualStroke.highlight : VisualStroke.highlight"),
              (u"        isRecording ? .controlAccentColor : .clear",
               u"        isRecording ? .controlAccentColor : .controlAccentColor")], "CAUGHT"),
    ("M661", [(u"        isRecording ? .controlAccentColor : .clear",
               u"        isRecording ? .clear : .clear")], "CAUGHT"),
    ("M662", [(u"            .strokeBorder(Color(nsColor: HotKeyRecorderEmphasis.strokeColor(isRecording: isRecording)),\n"
               u"                          lineWidth: HotKeyRecorderEmphasis.strokeWidth(isRecording: isRecording))",
               u"            .background(Color(nsColor: HotKeyRecorderEmphasis.strokeColor(isRecording: isRecording)))\n"
               u"            .frame(width: 128, height: 28)")], "CAUGHT"),
    ("M663", [(u"            .animation(MotionCatalog.animation(for: .emphasis), value: isRecording)\n",
               u"")], "CAUGHT"),
    ("M664", [(u"        guard isRecording != next else { return }\n", u"")], "CAUGHT"),
    ("M665", [(u"        isRecording ? VisualStroke.highlight : 0",
               u"        isRecording ? 0 : 0")], "CAUGHT"),
    # R143 审查轮补的两把（F2）：**按钮→状态→overlay 这条边**原来一把刀都没有 ——
    # 把闭包换成空实现，七条用例全绿，而功能整个是死的。
    ("M670", [(u"                                isRecording = recording",
               u"                                _ = recording")], "CAUGHT"),
    ("M671", [(u"            .overlay(HotKeyRecorderRing(isRecording: isRecording))",
               u"            .overlay(HotKeyRecorderRing(isRecording: false))")], "CAUGHT"),
    # F7：拿不到响应者链也亮"我在听"那一圈 —— 这一刀把那条守卫拆掉，产品入口那条用例必须红。
    ("M672", [(u"        if let window = window, !window.makeFirstResponder(self) {\n"
               u"            NSSound.beep()\n"
               u"            return\n"
               u"        }\n",
               u"        window?.makeFirstResponder(self)\n")], "CAUGHT"),
]


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        # 显式时间戳，且逐臂递增：源码必须比任何已编译产物新，否则"绿"是缓存说的。
        os.utime(path, (bump, bump))


def run_suite():
    """跑那一卷，返回 (跑了几个用例, 是否红, 红掉的用例名)。

    红必须是 `Executed >= 1 且失败` —— 一个用例都没跑起来不算红（那是探针坏了，
    把 DID-NOT-RUN 记成 CAUGHT 是本仓库记过的那一族）。
    """
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", FILTER],
                          cwd=os.path.join(ROOT, "ClipboardHistory"), env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = [int(m.group(1)) for m in re.finditer(r"Executed (\d+) tests?", out)]
    n = max(executed) if executed else 0
    # 红与否只准读**汇总行的失败数**：xctest 打的是
    #   Test Case '-[Target.Class testName]' failed
    # 类名与用例名之间是**空格**不是点。第一版按 `\.(test\w+)` 切，一个都没切到，
    # 于是五把刀全部"PASSED"、脚本 exit 1 却把每一刀都说成没牙 ——
    # 而这条坏法账本里已经记过（"红掉的测试名要按空格切"）。
    # `failures?` 与 `tests?` 都要能匹配单数：xctest 打的是
    #   Executed 6 tests, with 1 failure (0 unexpected)
    # 第一版按复数写，于是**只红一条**的臂全部读成"没有汇总行"，再被下面判成 PASSED ——
    # M663 与 M660 的第一版就是这么被冤枉成"判据没牙"的（复数能匹配、单数不能，
    # 而"红一条"恰恰是最常见的刀形）。
    summary = re.findall(r"Executed \d+ tests?, with (?:\d+ tests? skipped and )?(\d+) failures?", out)
    failures = sum(int(v) for v in summary) if summary else -1
    names = sorted({m.group(1).split()[-1].split(".")[-1]
                    for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    if failures < 0:
        return n, False, ["NO_SUMMARY_LINE（读不到失败数 ⇒ 这一跑不算红也不算绿）"]
    return n, (n >= 1 and failures > 0), names


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        # 打错一个臂号就会得到 `CAUGHT=0/0, RESTORE_CLEAN=yes` 与退出码 0 ——
        # 一把刀都没下也算过关（R143 审查轮 #1）。未知名字必须是硬错。
        print("ARG_ERROR 不认识这些臂号：%s（认识的是 %s）" % (", ".join(unknown), ", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print("ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
    original = read(PRODUCT)
    clock = [time.time() + 10.0]

    def restore():
        save(PRODUCT, original, bump=clock[0])
        clock[0] += 10.0

    restore()
    n, red, names = run_suite()
    if red or n == 0:
        restore()
        print("PRECHECK_FAILED 未落刀时基线不绿（Executed=%d 红=%s）⇒ 后面的 CAUGHT 不说明任何事"
              % (n, ", ".join(names)))
        return 1

    caught = 0
    for arm_id, edits, expect in arms:
        text = original
        ok = True
        for old, new in edits:
            if text.count(old) != 1:
                print("%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s ⇒ 刀没下，不许记成 CAUGHT"
                      % (arm_id, text.count(old), old.strip()[:40]))
                ok = False
                break
            text = text.replace(old, new)
        if not ok:
            continue
        save(PRODUCT, text, bump=clock[0])
        clock[0] += 10.0
        # **刀落没落要自己验**：重读盘上的内容，确认每一处 `old` 都不在了、每一处 `new` 都在。
        # 没有这一格，"文件没被改"与"改了但判据不灵"长得一模一样 —— 而后者会被记成
        # "这条判据没牙"，把尺冤枉一次（M663 第一次就是这么报的 PASSED）。
        on_disk = read(PRODUCT)
        if on_disk != text:
            print("%s NOT_RUN 盘上内容与要下的刀不一致（改了又被换回去？磁盘=%d 字节，要 %d 字节）"
                  % (arm_id, len(on_disk), len(text)))
            restore()
            continue
        n, red, names = run_suite()
        restore()
        if names and names[0].startswith("NO_SUMMARY_LINE"):
            print("%s NOT_RUN 读不到失败数（Executed=%d）⇒ 这一跑既不算红也不算绿" % (arm_id, n))
        elif red:
            caught += 1
            print("%s CAUGHT 红在（Executed=%d）：%s" % (arm_id, n, ", ".join(names)))
        else:
            print("%s PASSED 刀等于没下（Executed=%d，全绿）" % (arm_id, n))

    n, red, names = run_suite()
    restored = "yes" if (not red and n >= 1 and read(PRODUCT) == original) else "no"
    print("CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print("RESTORE_FAILED Executed=%d 红=%s" % (n, ", ".join(names)))
    return 0 if caught == len(arms) and restored == "yes" else 1


if __name__ == "__main__":
    sys.exit(main())
