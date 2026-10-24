#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R334 的变异表：三把刀钉"悬停那一档到底是谁的地板"（M970…M972）。

R334 做的事：393 把选中那颗抬到轨道之上之后，"鼠标停在另一段"与"那一段被选中"在暗档只差 4 级
（现读 contrast(66,70)=1.065 < 线 1.10）⇒ 悬停复现了选中（BACKLOG 396）。
修法是给胶囊单独一档 `VisualFill.pillHover`=0.045（暗档实测画在 60，落在可行窗口 59…63 里），
而"门只立暗档"这条决定不是注释：`hoverRungChoices` 把亮档的可行集**算成空集**（399）。

  M970 产品：把胶囊那一档改回全局的 0.08        ⇒ 暗档那条门必须红（396 回来）
  M971 尺：把"与选中同向且更弱"这条秩序撤掉      ⇒ 真值表必须红（亮档那句"空集"是秩序给的，不是几何给的）
  M972 门：把"只立暗档"那道 scope 去掉          ⇒ 亮档那一发必须替它说话（红在 light 那半）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r334.py [M970 … M972]
（三臂都跑捕获卷里的两格，单格 ~5s；M970 打在 Sources 上，M971/M972 打在 Tests 上。）
"""
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/wangziyi/Codex_Project0"
TOKENS = os.path.join(ROOT, "ClipboardHistory", "Sources", "ClipboardHistoryApp",
                      "Utilities", "VisualTokens.swift")
HARNESS = os.path.join(ROOT, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                       "UICaptureHarness.swift")
PKG = os.path.join(ROOT, "ClipboardHistory")
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
ENV["DEVELOPER_DIR"] = "/Applications/Xcode.app/Contents/Developer"

GATE_CELL = u"UICaptureTests/testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces"
TABLE_CELL = u"UICaptureTests/testHoverRungChoicesIsTheArithmeticBehindTheDarkOnlyGate"

# ① 产品：把胶囊那一档换回全局那一档 ⇒ 悬停(66) 与 选中(70) 又并成一档。
NEEDLE_970 = u"    static let pillHover: Double = 0.045"
REPL_970 = u"    static let pillHover: Double = 0.08"

# ② 尺：撤掉秩序 ⇒ 亮档的可行集不再空 —— 这一刀证明"空集"是秩序给的结论，不是随手写的。
NEEDLE_971 = (u"        let lo = min(idle, selected), hi = max(idle, selected)\n"
              u"        guard lo != hi else { return [] }\n"
              u"        return ((lo + 1)...(hi - 1)).filter {\n")
REPL_971 = (u"        let lo = 0, hi = 255\n"
            u"        guard lo != hi else { return [] }\n"
            u"        return (lo...hi).filter {\n")

# ③ 门：把"只立暗档"那道 scope 去掉 ⇒ 亮档那一发必须红（它今天被 scope 挡在外面）。
NEEDLE_972 = (u"            if appearance == .darkAqua {\n"
              u"                XCTAssertGreaterThanOrEqual(selVsHover, minimum,\n")
REPL_972 = (u"            if true {\n"
            u"                XCTAssertGreaterThanOrEqual(selVsHover, minimum,\n")

ARMS = [
    ("M970", u"产品：胶囊那一档换回全局 0.08 ⇒ 暗档门必须红（396 回来）", TOKENS,
     NEEDLE_970, REPL_970, u"testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces", GATE_CELL),
    ("M971", u"尺：撤掉『同向且更弱』的秩序 ⇒ 亮档『空集』那句必须红", HARNESS,
     NEEDLE_971, REPL_971, u"testHoverRungChoicesIsTheArithmeticBehindTheDarkOnlyGate", TABLE_CELL),
    ("M972", u"门：去掉『只立暗档』那道 scope ⇒ 亮档那一发必须替它说话", HARNESS,
     NEEDLE_972, REPL_972, u"testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces", GATE_CELL),
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
        # M972 的语义在"哪一个色档那半红"上：红名一样不代表红在对的那一发上，所以自己数一遍。
        light_lines = len(re.findall(u"(?m)^.*light：胶囊上", out))
        dark_lines = len(re.findall(u"(?m)^.*dark：胶囊上", out))
        if names and names[0].startswith(u"NO_SUMMARY_LINE"):
            not_run += 1
            print(u"%s NOT_RUN 读不到失败数（Executed=%d）" % (arm_id, n))
        elif skipped:
            not_run += 1
            print(u"%s NOT_RUN 落刀后被 skip（skipped=%d）⇒ 不许记成 CAUGHT" % (arm_id, skipped))
        elif "error: " in out and not red:
            not_run += 1
            print(u"%s NOT_RUN 落刀后编译报错而用例没红 ⇒ 刀坏了，重下" % arm_id)
        elif arm_id == u"M972" and not (light_lines > 0 and dark_lines == 0):
            mismatch += 1
            print(u"%s MISMATCH 红了，但不是亮档那一发（light 句=%d dark 句=%d）⇒ scope 没被拆掉"
                  % (arm_id, light_lines, dark_lines))
        elif red and any(expected in name for name in names):
            caught += 1
            extra = u"（light 句=%d，dark 句=%d）" % (light_lines, dark_lines) if arm_id == u"M972" else u""
            print(u"%s CAUGHT %s（Executed=%d）%s 红在：%s"
                  % (arm_id, why[:34], n, extra, u", ".join(names)))
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
