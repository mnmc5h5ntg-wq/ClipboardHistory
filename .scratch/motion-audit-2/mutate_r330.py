#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R330 的变异表：三把刀钉"真机那把尺读的是不是它声称的那个对象"（M957…M959）。

R330 的读数：真机现读 页底 51 / 轨道 81 / 选中那颗 48，差 = -33.0（臂 A），
点过另一颗之后 洞从 x2..170 搬到 x172..240、差 = -32.0（臂 B）⇒ 377 是真缺陷。
而这把尺在同一趟里自曝三次（列电平取 max / 只判横向 / 页底从行内众数取），
每一次都是**尺坏**而不是产品坏 —— 所以这一支表打的不是产品，是那把新尺自己。

  M957 两趟参照改回"行内众数"      ⇒ 亮半更宽那一格必须红（臂 B 那次翻向的复现）
  M958 实心度地板降到 0             ⇒ 文字行冒充控件那一格必须红（真机报过差 -99.0 的假阳性）
  M959 列电平从中位改回 max         ⇒ 字墨劫持那一格必须红（真机第一版的差 -78.4）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r330.py [M957 … M959]
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
RULER = os.path.join(ROOT, "scripts", "real_screen_filter_pill.py")
TESTS = os.path.join(ROOT, "scripts", "tests")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["PYTHONUTF8"] = "1"
ENV["PYTHONDONTWRITEBYTECODE"] = "1"

CLS = u"test_real_screen_filter_pill.RealScreenFilterPillTests"   # unittest 要**模块.类**全名
REF_TEST = u"test_referenceComesFromOutsideTheControlEvenWhenHalvesAreUnequal"
SOLID_TEST = u"test_textRowAloneIsNotAControl"
MEDIAN_TEST = u"test_columnLevelIsTheMedianSoGlyphInkCannotHijackIt"

# ① 第二趟的参照换回"这一行自己的众数" ⇒ 两半区各占一半时它是掷硬币。
NEEDLE_957 = u"        got = measure_row(profile, page, stride, scale, DELTA)\n"
REPL_957 = u"        got = measure_row(profile, mode_level(profile, DELTA), stride, scale, DELTA)\n"

# ② 实心度闸拿掉 ⇒ 一条两头各一块字的标题行能过全部四道横向闸。
NEEDLE_958 = u"MIN_SOLIDITY = 0.20 "
REPL_958 = u"MIN_SOLIDITY = 0.00 "

# ③ 列电平从中位退回 max ⇒ 字墨把整列抬走。
NEEDLE_959 = u"        out.append((x, vals[len(vals) // 2]))"
REPL_959 = u"        out.append((x, max(vals)))"

ARMS = [
    ("M957", u"尺：两趟参照退回行内众数 ⇒ 偏置面前必须红", RULER,
     NEEDLE_957, REPL_957, REF_TEST, CLS + u"." + REF_TEST),
    ("M958", u"尺：实心度地板归零 ⇒ 文字行冒充控件必须红", RULER,
     NEEDLE_958, REPL_958, SOLID_TEST, CLS + u"." + SOLID_TEST),
    ("M959", u"尺：列电平退回 max ⇒ 字墨劫持那一格必须红", RULER,
     NEEDLE_959, REPL_959, MEDIAN_TEST, CLS + u"." + MEDIAN_TEST),
]
TARGETS = sorted({a[2] for a in ARMS})


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text, bump=None):
    open(path, "w", encoding="utf-8").write(text)
    if bump is not None:
        os.utime(path, (bump, bump))


def run_suite(filt):
    u"""跑**一卷 python 判据**（不是 swift）：这一支表打的正是那把 python 尺。

    结论只认 python 自己打的行，并且**先把"根本没跑成"挑出来**：
    第一版这里被一个坏 filter 骗过一次 —— `RealScreenFilterPillTests.test_x` 少了模块名，
    unittest 把它做成 `_FailedTest` 的 loader 错，照样打 `Ran 1 test`，
    于是基线读起来是绿的（R330 / 空对账那一族）。所以现在：
      · 出现 `Failed to import test module` / `_FailedTest` ⇒ 直接判"没跑成"（n 归 -1）；
      · `FAILED (...)` 括号里 failures 与 errors 的**全部**数字相加，读不到就 -1；
      · 读不到 `Ran N tests` ⇒ -1，不许把"没解析到"当成"零失败"。
    """
    proc = subprocess.run([sys.executable, "-m", "unittest", "-v", filt],
                          cwd=TESTS, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    if "Failed to import test module" in out or "_FailedTest" in out:
        return -1, False, [u"NO_SUMMARY_LINE（filter 解析不出用例，是 loader 错）"], out, 0
    ran = [int(m.group(1)) for m in re.finditer(r"Ran (\d+) tests?", out)]
    n = max(ran) if ran else -1
    failures = -1
    m = re.search(r"^FAILED \(([^)]*)\)", out, re.M)
    if m:
        failures = sum(int(v) for v in re.findall(r"\d+", m.group(1)))
    elif re.search(r"^OK", out, re.M):
        failures = 0
    names = sorted({g.group(1) for g in re.finditer(r"^(?:FAIL|ERROR): (\S+)", out, re.M)})
    skipped = len(re.findall(r"\bskipped\b", out))
    if n < 0:
        return -1, False, [u"NO_SUMMARY_LINE（读不到 Ran 那一行）"], out, skipped
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
            print(u"PRECHECK_FAILED 基线里 %s 被 skip（skipped=%d）⇒ 缺 PIL 的机器上这支表没牙" % (filt, skipped))
            return 1
        if red or n <= 0:
            restore()
            print(u"PRECHECK_FAILED 未落刀时 %s 基线不绿（Ran=%d 红=%s）"
                  % (filt, n, u", ".join(names)))
            return 1
        print(u"BASELINE_GREEN %s Ran=%d" % (filt.split(".")[-1], n))

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
            print(u"%s NOT_RUN 读不到 Ran 那一行（python 尺的结论通道坏了）" % arm_id)
        elif skipped:
            not_run += 1
            print(u"%s NOT_RUN 落刀后被 skip（skipped=%d）⇒ 不许记成 CAUGHT" % (arm_id, skipped))
        elif "Traceback (most recent call last)" in out and "AssertionError" not in out:
            not_run += 1
            print(u"%s NOT_RUN 落刀后是异常而不是断言红 ⇒ 刀坏了，重下" % arm_id)
        elif red and any(expected in name for name in names):
            caught += 1
            print(u"%s CAUGHT %s（Ran=%d）红在：%s" % (arm_id, why[:34], n, u", ".join(names)))
        elif red:
            mismatch += 1
            print(u"%s MISMATCH 红了但不是它那条（Ran=%d）红在：%s" % (arm_id, n, u", ".join(names)))
        else:
            mismatch += 1
            print(u"%s PASSED 刀等于没下（Ran=%d，全绿）⇒ 这一环没有证人" % (arm_id, n))

    for filt in sorted({a[6] for a in arms}):
        n, red, names, out, skipped = run_suite(filt)
        if red or n <= 0 or skipped:
            print(u"RESTORE_FAILED %s Ran=%d 红=%s skip=%d" % (filt, n, u", ".join(names), skipped))
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
