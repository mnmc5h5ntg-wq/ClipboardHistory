#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R327 的变异表：三把刀钉的是"被拒的那一段要带差多少的数"这一格（M949…M951）。

本轮的产出很小，但它是**证伪的产物**：BACKLOG 384 写的修法①（把字墨并回洞）
在真帧上被现读推翻 —— 两版轨道档估计（非页底列众数 / 两帧同列且离页底最近）都没能把
被拒段救回来（洞宽仍 21%…25%，通过段 49%），第二版还把带子的连续性弄断
（过×15→过×12、取用从 14px 变成"无"⇒ 两条胶囊判据一起掉进 no-band 出口）⇒ 改动已撤回。

留在盘上的只有报告那一格：`movingHoleBand` 的每个候选段现在带"洞宽=NN%"
（该段各行 holeA/extent 的中位数）。之前"洞太窄"三个字是全部信息，
于是"地板定高了"与"对象没框全"两种坏法读不出区别 —— 修法相反，不能靠猜。

三把刀各拆一环，都指定"哪一条用例必须红"：

  M949 洞宽那一格恒为 -1（读不出）        ⇒ 证人必须红（报告出现"洞宽=无"）
  M950 分母从轨道列数换成洞自己的列数      ⇒ 证人必须红（100% 那一格是恒真句）
  M951 报告里整段不印洞宽                  ⇒ 证人必须红

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r327.py [M949 … M951]
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
REPORT_TEST = u"testRejectedSegmentCarriesItsHoleWidth"

# ① 那一格恒读不出。
NEEDLE_949 = u"                holeFractions.append(Double(r.holeA.count) / Double(Swift.max(1, r.extent.count)))\n"
REPL_949 = u"                holeFractions.append(-1)\n"

# ② 分母换成洞自己 ⇒ 恒 100%。
NEEDLE_950 = u"Double(Swift.max(1, r.extent.count))"
REPL_950 = u"Double(Swift.max(1, r.holeA.count))"

# ③ 报告里不印那一格。
NEEDLE_951 = (u"                + \" 洞宽=\" + (g.hole < 0 ? \"无\" : String(format: \"%.0f%%\", g.hole * 100.0)))\n")
REPL_951 = u"                )\n"

ARMS = [
    ("M949", u"尺：洞宽那一格恒读不出 ⇒ 证人必须红", FILM,
     NEEDLE_949, REPL_949, REPORT_TEST, PURE),
    ("M950", u"尺：分母用洞自己 ⇒ 100% 恒真，证人必须红", FILM,
     NEEDLE_950, REPL_950, REPORT_TEST, PURE),
    ("M951", u"尺：报告不印洞宽 ⇒ 证人必须红", FILM,
     NEEDLE_951, REPL_951, REPORT_TEST, PURE),
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
