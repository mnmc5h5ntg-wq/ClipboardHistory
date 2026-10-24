#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R328 的变异表：三把刀钉的是"被拒的那一段要带分档"这一格（M952…M954）。

本轮的产出是把 BACKLOG 388 要的那份**转储**搬进仓库尺：`movingHoleBand` 的每个**被拒**候选段
现在带 `分档=k×列数`，箱号 = floor((列电平 − 页底) / delta)，所以**第 0 箱就是判据自己认的"洞"**。
为什么这件事值得三把刀：R327 之前，"洞太窄"与"洞宽=21%"都不回答"那一行里住着几级电平"，
于是我拿 /tmp 的临时尺看过一次就没留档（D-314），紧接着两轮改"洞的定义"而读数不变。
真帧现读（本机 2×）：被拒段 `分档=0×292,1×1,2×244,…,24×20` ⇒ 那一行 51% 的列在洞档、
41% 在轨道档、9% 在远高于轨道的字墨档 —— 三种东西混在同一行，所以它本来就不是一颗胶囊。

  M952 分档做成占位符（永远印"无"）        ⇒ 证人必须红（被拒段没带对象）
  M953 分箱宽度换成我发明的 64 级           ⇒ 真值表必须红（三档被洗成两档，且第 0 箱不再等于"洞"）
  M954 把"只给被拒段"改成"谁都给"           ⇒ 负半必须红（带上了就不携带信息）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r328.py [M952 … M954]
（三把都打在合成剖面的证人卷上，不需要 CLIPBOARD_HISTORY_UI_MOTION。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
FILM = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                    "MotionFilmstripTests.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PURE = u"MotionPillRampTests"
DUMP_TEST = u"testRejectedSegmentCarriesItsColumnLevelDump"
HIST_TEST = u"testLevelHistogramBinsByTheRulersOwnDelta"
NEG_TEST = u"testAcceptedSegmentDoesNotCarryADump"

# ① 分档做成占位符：形状还在，对象没了。
NEEDLE_952 = u'                line += " 分档=" + Self.levelHistogram(profile: profile, margin: margin, delta: delta)\n'
REPL_952 = u'                line += " 分档=无"\n'

# ② 分箱宽度换成 64 级：第 0 箱不再等于"洞"，三档被洗成两档。
NEEDLE_953 = u"            bins[Int(((value - margin) / delta).rounded(.down)), default: 0] += 1\n"
REPL_953 = u"            bins[Int(((value - margin) / 64.0).rounded(.down)), default: 0] += 1\n"

# ③ 把"只给被拒段"做成"谁都给"：负半证人必须红。
NEEDLE_954 = u'            if g.gate != "过" {\n'
REPL_954 = u'            if g.gate != "绝不会被选中的判定" {\n'

ARMS = [
    ("M952", u"尺：分档那一格做成占位符（印「无」）⇒ 证人必须红", FILM,
     NEEDLE_952, REPL_952, DUMP_TEST, PURE),
    ("M953", u"尺：分箱宽度从 delta 换成 64 级 ⇒ 三档被洗成两档，真值表必须红", FILM,
     NEEDLE_953, REPL_953, HIST_TEST, PURE),
    ("M954", u"尺：把「只给被拒段」做成「谁都给」⇒ 负半证人必须红", FILM,
     NEEDLE_954, REPL_954, NEG_TEST, PURE),
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
