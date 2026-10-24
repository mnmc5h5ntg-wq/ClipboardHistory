#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R333 的变异表：五把刀钉"药丸档重基之后那颗尺还有没有对象"（M965…M969）。

R333 做的事：391 的修法①落地（选中的那颗从材质换成 `unemphasizedSelectedContentBackgroundColor`），
而离屏尺原来的定义是"药丸 = 与页底同档的那一段"——那句话借的就是 377 那个缺陷的画法，
所以修法一落地尺子**没有红、是 skip**（`MOTION_NOT_RUN=pill-ramp-no-band` / `pill-band-unmeasured`，
现读 `行=520 候选行=0 判定分布=非候选×520`）。新的定义由两个 settled 臂的**镜像**量出两档，
极性无关。这一支表打的就是新定义的四环 + 产品那一发：

  M965 拆掉"不镜像"这道闸          ⇒ 两臂没换边也照样框药丸（定档没有对照物）
  M966 把 pill/track 两条对角线配错 ⇒ 真值表里"药丸=首帧左半"那一句必须红
  M967 把"两档分不开就不许框"放宽    ⇒ 洗淡了会被读成看得见（反例格必须红）
  M968 产品：把选中那颗压回轨道之下  ⇒ 暗档"同侧"门必须红（D-325 立的那条牙）
  M969 撤掉 halfLevels 的 4 列下限   ⇒ 空半区也会给出"两半"的数

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r333.py [M965 … M969]
（M968 打在产物上、跑的是捕获卷那一格，约 30s/臂；其余四臂跑合成帧卷，秒级。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
FILM = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                    "MotionFilmstripTests.swift")
TOKENS = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Utilities", "VisualTokens.swift")
HARNESS = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                       "UICaptureHarness.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

PURE = u"MotionPillRampTests"
SEGREF = u"UICaptureTests/testSystemSegmentedReferenceSaysWhichHalfTracksSelection"

# ① 新闸本身：两臂没换边也去框药丸。
NEEDLE_965 = u'        if !levels.mirror {\n            gate = "不镜像"\n'
REPL_965 = u'        if !levels.mirror && false {\n            gate = "不镜像"\n'

# ② 对角线配错：药丸不再是"首帧左半 = 末帧右半"那一对，而是同一臂的两半。
NEEDLE_966 = u"        let pill = (firstLeft + lastRight) / 2.0\n"
REPL_966 = u"        let pill = (firstLeft + firstRight) / 2.0\n"

# ③ 两档分不开时不许猜：把这道闸放宽到 delta 的百分之一。
NEEDLE_967 = u"              abs(pillLevel - trackLevel) >= delta else { return nil }"
REPL_967 = u"              abs(pillLevel - trackLevel) >= delta / 100 else { return nil }"

# ④ 产品那一发：把选中那颗压回轨道之下（= 377 在屏幕上判掉的画法）。
NEEDLE_968 = (u"    static let selectedSegment: Color = "
              u"Color(nsColor: .unemphasizedSelectedContentBackgroundColor)")
REPL_968 = (u"    static let selectedSegment: Color = "
            u"Color(nsColor: .underPageBackgroundColor)")

# ⑤ 半区下限：不足 4 列时平分出来有一边是空的。
NEEDLE_969 = u"              extent.count >= 4 else { return nil }"
REPL_969 = u"              extent.count >= 1 else { return nil }"

ARMS = [
    ("M965", u"尺：拆掉「不镜像」闸 ⇒ 没有对照物也要框药丸，证人必须红", FILM,
     NEEDLE_965, REPL_965, u"testReadingNamesArmsThatDoNotSwap", PURE),
    ("M966", u"尺：pill/track 两条对角线配错 ⇒ 真值表必须红", FILM,
     NEEDLE_966, REPL_966, u"testSettledLevelsNamePillByMirrorAndCarrySign", PURE),
    ("M967", u"尺：两档分不开也去框 ⇒ 「洗淡了」读成「看得见」，反例格必须红", FILM,
     NEEDLE_967, REPL_967, u"testPillRunRefusesSubFloorHole", PURE),
    ("M968", u"产品：选中那颗压回轨道之下 ⇒ 暗档同侧门必须红（D-325 的牙）", TOKENS,
     NEEDLE_968, REPL_968, u"testSystemSegmentedReferenceSaysWhichHalfTracksSelection", SEGREF),
    ("M969", u"尺：撤掉 halfLevels 的 4 列下限 ⇒ 空半区也给数，证人必须红", FILM,
     NEEDLE_969, REPL_969, u"testHalfLevelsRefusesAnExtentTooNarrowToSplit", PURE),
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
