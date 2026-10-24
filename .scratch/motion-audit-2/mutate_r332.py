#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R332 的变异表：两把刀钉"真机那格的三种缺席分不分得开"（M963…M964）。

R332 的读数：用户授权退出 App 跑 393 的 before/after，显示器开着（pmset 现读 turned on），
而区域截图报 could not create image from rect，ioreg 里 SecureInput 属主=loginwindow ⇒ 会话是锁着的。
旧的那一句把三种缺席压成一句"探针截图失败"，读起来像通道坏了 ⇒ 拆成 display_off / screen_locked /
capture_failed 三颗，并配判据卷（test_real_screen_probe 现读 Ran 8 tests OK）。

  M963 拿掉锁屏那一支 ⇒ 三种缺席塌成两种、锁屏被报成通道坏了，那一格必须红
  M964 拿掉 region_ok 这一支 ⇒ "开着、没锁、还是截不出来"被放行，那一格必须红

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r332.py [M963 M964]
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
HARNESS = os.path.join(ROOT, "scripts", "real_screen_sidebar_icons.py")
TESTS = os.path.join(ROOT, "scripts", "tests")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

CLS = u"test_real_screen_probe.DisplayChannelCauseTests"
THREE = u"test_the_three_absences_get_three_different_causes"
OTHER = u"test_another_app_holding_secure_input_is_not_a_lock_screen"

# ① 拿掉"锁屏"那一支 ⇒ 锁屏落到 capture_failed 上，两种修法相反的缺席在读数上同形。
NEEDLE_963 = (u'    if secure_owner == "loginwindow":\n'
              u'        return False, "screen_locked"\n')
REPL_963 = u''

# ② 拿掉"通道坏了"那一支 ⇒ 开着、没锁、截不出来也被放行。
NEEDLE_964 = (u'    if not region_ok:\n'
              u'        return False, "capture_failed"\n')
REPL_964 = u''

ARMS = [
    ("M963", u"尺：锁屏那一支被拿掉 ⇒ 三种缺席塌成两种，必须红", HARNESS,
     NEEDLE_963, REPL_963, THREE, CLS + u"." + THREE),
    ("M964", u"尺：capture_failed 那一支被拿掉 ⇒ 通道坏了被放行，必须红", HARNESS,
     NEEDLE_964, REPL_964, OTHER, CLS + u"." + OTHER),
]
TARGETS = sorted({a[2] for a in ARMS})


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        os.utime(path, (bump, bump))


def run_suite(filt):
    proc = subprocess.run([sys.executable, "-m", "unittest", "-v", filt],
                          cwd=TESTS, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    executed = [int(m.group(1)) for m in re.finditer(r"Ran (\d+) tests?", out)]
    n = max(executed) if executed else 0
    summary = re.findall(r"FAILED \((?:failures=(\d+))?", out)
    failures = int(summary[0]) if summary else (0 if re.search(r"^OK", out, re.M) else -1)
    names = sorted({m.group(1) for m in re.finditer(r"^(?:FAIL|ERROR): (\S+)", out, re.M)})
    skipped = len(re.findall(r"skipped=", out))
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
