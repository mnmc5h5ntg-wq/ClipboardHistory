#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R331 的变异表：三把刀钉"系统参照臂那格读的是不是它声称的那个对象"（M960…M962）。

R331 的读数：同一条离屏通道、同一个 200×60 取景、同一颗尺 ——
暗档 系统那颗 选中 74.0 / 未选 48.0 ⇒ 差 **+26.0**；自家 36.0 / 52.0 ⇒ 差 **−16.0** ⇒ 391 的方向是①。
而这一格本轮翻了两次自伤：第一版页底按"控件外的左右各 6 列"取，被自家那颗**满幅**胶囊把页底
读成了轨道（52.0），范围退化成整幅；更早一版把取样带写成 38%…62%，而 probeFrame 的内容贴着**下沿**
排（现读对象行带 66…120）。两次都是"尺读错对象"，不是"系统没画" ⇒ 这一支表打的正是那把新尺。

  M960 右臂夹具的 selection 从 1 改成 0 ⇒ 两臂同物，"两臂镜像"那一格必须红
  M961 representable 的 updateNSView 吞掉入参 ⇒ 同上，但坏在**产品胶水那一层**而不是夹具
  M962 页底从"顶部三行"改回"底部三行"（= 本轮第一次翻车的那一发）⇒ 看这一格抓不抓得住

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r331.py [M960 … M962]
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
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

CELL = u"UICaptureTests/testSystemSegmentedReferenceSaysWhichHalfTracksSelection"

# ① 右臂不再换 selection ⇒ 两臂是同一个对象。
NEEDLE_960 = u"SystemSegmentedProbe(selected: 1)"
REPL_960 = u"SystemSegmentedProbe(selected: 0)"

# ② 夹具给的值被 representable 吃掉（真实产品里"视图接了参数但没往下传"就是这一形）。
NEEDLE_961 = (u"        func updateNSView(_ control: NSSegmentedControl, context: Context) {\n"
              u"            control.selectedSegment = selected\n")
REPL_961 = (u"        func updateNSView(_ control: NSSegmentedControl, context: Context) {\n"
            u"            control.selectedSegment = 0\n")

# ③ 页底退回"底部三行"：对象贴着下沿排 ⇒ 底部三行是**对象**，页底被读成对象自己。
NEEDLE_962 = (u"                var vals: [Double] = []\n"
              u"                for y in 0..<3 {\n")
REPL_962 = (u"                var vals: [Double] = []\n"
            u"                for y in f.h - 3 ..< f.h {\n")

ARMS = [
    ("M960", u"夹具：两臂同一个 selection ⇒ 镜像那一格必须红", HARNESS,
     NEEDLE_960, REPL_960, u"testSystemSegmentedReferenceSaysWhichHalfTracksSelection", CELL),
    ("M961", u"胶水：updateNSView 吞掉入参 ⇒ 镜像那一格必须红", HARNESS,
     NEEDLE_961, REPL_961, u"testSystemSegmentedReferenceSaysWhichHalfTracksSelection", CELL),
    ("M962", u"尺：页底从对象自己身上取（本轮第一次翻车）⇒ 必须红", HARNESS,
     NEEDLE_962, REPL_962, u"testSystemSegmentedReferenceSaysWhichHalfTracksSelection", CELL),
]
TARGETS = sorted({a[2] for a in ARMS})


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        os.utime(path, (bump, bump))


def run_suite(filt):
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", filt],
                          cwd=PKG, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = [int(m.group(1)) for m in re.finditer(r"Executed (\d+) tests?", out)]
    n = max(executed) if executed else 0
    summary = re.findall(r"Executed \d+ tests?, with (?:\d+ tests? skipped and )?(\d+) failures?", out)
    failures = sum(int(v) for v in summary) if summary else -1
    names = sorted({m.group(1) for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    skipped = len(re.findall(r"Test Case '[^']+' skipped", out))
    if failures < 0:
        return n, False, [u"NO_SUMMARY_LINE（读不到失败数）"], out, skipped
    return n, (n >= 1 and failures > 0), names, out, skipped


def main():
    want = sys.argv[1:]
    known = {a[0] for a in ARMS}
    unknown = sorted(set(want) - known)
    if unknown:
        print(u"ARG_ERROR 不认识这些臂号：%s（认识的是 %s）"
              % (u", ".join(unknown), u", ".join(sorted(known))))
        return 2
    arms = [a for a in ARMS if not want or a[0] in want]
    if not arms:
        print(u"ARG_ERROR 一臂都没选中 ⇒ 不许读成过关")
        return 2
    originals = {path: read(path) for path in TARGETS}
    clock = [time.time() + 10.0]

    def restore():
        for path, base in originals.items():
            save(path, base, bump=clock[0])
        clock[0] += 10.0

    restore()
    for filt in sorted({a[6] for a in arms}):
        n, red, names, out, skipped = run_suite(filt)
        if skipped:
            restore()
            print(u"PRECHECK_FAILED 基线里 %s 被 skip（skipped=%d）" % (filt, skipped))
            return 1
        if red or n == 0:
            restore()
            print(u"PRECHECK_FAILED 未落刀时 %s 基线不绿（Executed=%d 红=%s）"
                  % (filt, n, u", ".join(names)))
            return 1
        print(u"BASELINE_GREEN %s Executed=%d" % (filt, n))

    caught = 0
    mismatch = 0
    not_run = 0
    for arm_id, why, target, old, new, expected, filt in arms:
        text = read(target)
        if text.count(old) != 1:
            not_run += 1
            print(u"%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm_id, text.count(old), old.strip()[:52]))
            continue
        want_text = text.replace(old, new)
        save(target, want_text, bump=clock[0])
        clock[0] += 10.0
        if read(target) != want_text:
            restore()
            not_run += 1
            print(u"%s NOT_RUN 盘上内容与要下的刀不一致 ⇒ 不许记成 CAUGHT" % arm_id)
            continue
        n, red, names, out, skipped = run_suite(filt)
        restore()
        if names and names[0].startswith(u"NO_SUMMARY_LINE"):
            not_run += 1
            print(u"%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif skipped:
            not_run += 1
            print(u"%s NOT_RUN 落刀后被 skip（skipped=%d）⇒ 不许记成 CAUGHT" % (arm_id, skipped))
        elif "error: " in out and not red:
            not_run += 1
            print(u"%s NOT_RUN 落刀后编译报错而用例没红 ⇒ 刀坏了，重下" % arm_id)
        elif red and any(expected in name for name in names):
            caught += 1
            print(u"%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:32], n, u", ".join(names)))
        elif red:
            mismatch += 1
            print(u"%s MISMATCH 红了但不是它那条（Executed=%d）红在：%s" % (arm_id, n, u", ".join(names)))
        else:
            mismatch += 1
            print(u"%s PASSED 刀等于没下（Executed=%d，全绿）⇒ 这一环没有证人" % (arm_id, n))

    for filt in sorted({a[6] for a in arms}):
        n, red, names, out, skipped = run_suite(filt)
        if red or n == 0 or skipped:
            print(u"RESTORE_FAILED %s Executed=%d 红=%s skip=%d" % (filt, n, u", ".join(names), skipped))
            print(u"CAUGHT=%d/%d, RESTORE_CLEAN=no" % (caught, len(arms)))
            return 1
    restored = "yes" if all(read(q) == base for q, base in originals.items()) else "no"
    print(u"CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print(u"RESTORE_FAILED 盘上内容与基线不一致")
    if not_run or mismatch:
        print(u"NOT_RUN=%d MISMATCH=%d ⇒ 这支表不算过关" % (not_run, mismatch))
    return 0 if caught == len(arms) and restored == "yes" and not not_run and not mismatch else 1


if __name__ == "__main__":
    sys.exit(main())
