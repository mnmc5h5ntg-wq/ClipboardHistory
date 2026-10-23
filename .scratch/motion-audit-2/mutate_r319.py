#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R319 的变异表：三把刀，各自钉一条**不同**的轴（M914-M916）。

为什么是三把而不是"一条判据配一把"：本轮同时新装了一把**尺**（浮层选中底的两枚系统参照臂）
和一处**产品修法**（损坏原件的保全按内容幂等）。它们各有一种"看起来绿其实是坏"的形状：

  M914 尺的身份：把 key 那一档的参照臂解析换成非 key 那一枚 ⇒ 两臂塌成一枚 ⇒
       判定必须报「两臂不可分」⇒ 断言必须红。
       （没有这一把，"两枚参照色"可以退化成一枚而没有任何读数会说话。）
  M915 产品的牙：把悬停那档的真值表取反（`isSelected: !isSelected`）⇒ 自家半透明灰叠到
       选中那一行上 ⇒ 帧上的底色掉出两枚参照色之外 ⇒ 断言必须红。
       （这一把钉的是"选中底是系统画的那一档"这句话本身，不是它的形容词。）
  M916 幂等的守卫：把"字节相同就不再写"那个条件改成永假 ⇒ 跨过秒界的第二次载入又写一份 ⇒
       用例的「恰好一份」必须红。（它同时是 BACKLOG 374 的验收：红在**新**用例上，不是旧用例。）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r319.py [M914 M915 M916]
形状沿用 mutate_r142.py（基线先绿、锚点恰好命中一次、落刀后回读盘上内容、mtime 逐臂递增、
只有全部抓到且 RESTORE_CLEAN=yes 才退 0；认不出臂号 = ARG_ERROR 退 2）。
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
PKG = os.path.join(ROOT, "ClipboardHistory")
TESTS_DIR = os.path.join(PKG, "Tests", "ClipboardHistoryAppTests")
SOURCES_DIR = os.path.join(PKG, "Sources", "ClipboardHistoryApp")
HARNESS = os.path.join(TESTS_DIR, "UICaptureHarness.swift")
QUICKPICK = os.path.join(SOURCES_DIR, "Managers", "QuickPickController.swift")
PERSIST = os.path.join(SOURCES_DIR, "Managers", "HistoryPersistence.swift")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

SELARM = u"UICaptureTests/testQuickPickSelectionPillAgainstSystemArms"
RECOVERY = (u"HistoryPersistenceRecoveryTests/"
            u"testCorruptHistoryWithoutBackupPreservesOriginalAndReferencedImages")
BASELINE_FILTER = SELARM + u"|" + RECOVERY
# 每一刀必须红在**它自己那一条判据**上（D-244：只看"有没有红"会把"红了但在别处"读成抓到）。
FILTERS = {u"M914": SELARM, u"M915": SELARM, u"M916": RECOVERY}
EXPECTED = {u"M914": u"testQuickPickSelectionPillAgainstSystemArms",
            u"M915": u"testQuickPickSelectionPillAgainstSystemArms",
            u"M916": u"testCorruptHistoryWithoutBackupPreservesOriginalAndReferencedImages"}

ARMS = [
    ("M914", u"判据：两枚系统参照臂塌成一枚 ⇒ 判定必须报「两臂不可分」⇒ 红", HARNESS,
     u"            let key = Self.armResolved(.selectedContentBackgroundColor, appearanceName: appearance)",
     u"            let key = Self.armResolved(.unemphasizedSelectedContentBackgroundColor, appearanceName: appearance)",
     "CAUGHT"),
    # M915 的第一版针打在 `fill.isHidden = !showsHoverTint(isSelected: !isSelected,` 上，
    # 本机跑出来是 **PASSED**（刀等于没下）：离屏捕获里没有悬停，`showsHoverTint` 的
    # `isHovered && !isSelected` 在 isHovered=false 时无论 isSelected 怎么翻都是 false ⇒
    # 那一位翻转在这条通道上根本不可观察。改针打在**真值表本体**上（`isHovered || isSelected`），
    # 它才是"自家灰叠到选中那一行"这一族缺陷的形状。
    ("M915", u"产品：把悬停真值表改成「选中也算悬停」⇒ 自家灰叠到选中那一行 ⇒ 落点掉出两臂 ⇒ 红", QUICKPICK,
     u"        isHovered && !isSelected",
     u"        isHovered || isSelected",
     "CAUGHT"),
    ("M916", u"产品：把「字节相同就不再写」的幂等守卫改成永假 ⇒ 跨秒界的第二次载入又写一份 ⇒ 红", PERSIST,
     u"                if let existing = try? Data(contentsOf: sibling), existing == original {",
     u"                if let existing = try? Data(contentsOf: sibling), existing == original && name.isEmpty {",
     "CAUGHT"),
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
    names = sorted({m.group(1).split()[-1].split(".")[-1]
                    for m in re.finditer(r"Test Case '([^']+)' failed", out)})
    if failures < 0:
        return n, False, ["NO_SUMMARY_LINE（读不到失败数 ⇒ 既不算红也不算绿）"], out
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
    n, red, names, _ = run_suite(BASELINE_FILTER)
    if red or n == 0:
        restore()
        print("PRECHECK_FAILED 未落刀时基线不绿（Executed=%d 红=%s）⇒ 后面的 CAUGHT 不说明任何事"
              % (n, ", ".join(names)))
        return 1
    print("BASELINE_GREEN Executed=%d（两把尺的用例都在分母里）" % n)

    caught = 0
    for arm_id, why, target, old, new, expect in arms:
        text = read(target)
        if text.count(old) != 1:
            print("%s NOT_RUN 锚点命中 %d 次（要 1 次）：%s" % (arm_id, text.count(old), old.strip()[:40]))
            continue
        save(target, text.replace(old, new), bump=clock[0])
        clock[0] += 10.0
        if read(target) != text.replace(old, new):
            restore()
            print("%s NOT_RUN 盘上内容与要下的刀不一致 ⇒ 不许记成 CAUGHT" % arm_id)
            continue
        n, red, names, out = run_suite(FILTERS[arm_id])
        restore()
        if names and names[0].startswith("NO_SUMMARY_LINE"):
            print("%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif "error: " in out and not red:
            # 编译不过 = 刀坏，不是判据没牙（D-243）
            print("%s NOT_RUN 落刀后编译报错而用例没红 ⇒ 刀坏了，重下" % arm_id)
        elif red and EXPECTED[arm_id] in " ".join(names):
            caught += 1
            print("%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:24], n, ", ".join(names)))
        elif red:
            # 红了，但红在别的用例上 ⇒ 不算这把刀的牙（D-244）
            print("%s MISMATCH 红了但不是它那条（Executed=%d）红在：%s"
                  % (arm_id, n, ", ".join(names)))
        else:
            print("%s PASSED 刀等于没下（Executed=%d，全绿）⇒ 这一格要么尺没牙，要么刀打在不可观察的位上"
                  % (arm_id, n))

    n, red, names, _ = run_suite(BASELINE_FILTER)
    restored = "yes" if (not red and n >= 1
                         and all(read(q) == base for q, base in originals.items())) else "no"
    print("CAUGHT=%d/%d, RESTORE_CLEAN=%s" % (caught, len(arms), restored))
    if restored == "no":
        print("RESTORE_FAILED Executed=%d 红=%s" % (n, ", ".join(names)))
    return 0 if caught == len(arms) and restored == "yes" else 1


if __name__ == "__main__":
    sys.exit(main())
