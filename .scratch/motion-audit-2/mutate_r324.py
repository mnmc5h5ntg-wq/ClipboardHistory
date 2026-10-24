#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R324 的变异表：六把刀钉的是**行带定位器 + 钉色档**这一组（M931…M936）。

本轮的靶来自上一轮 CI（RUN=40032708615，STEP[19] 两朵红）：斜坡尺与过程证人在 runner 上
把**列表里的一行**当成了胶囊（`行带=346.0…352.0pt 轨道范围=25.0…299.0pt`），于是
一朵尺子红长得和产品缺陷一模一样（判成"回头"、三臂峰值相等）。同一轮在本机复跑时，
本机已经转到**亮档**（自动外观），那把尺连对象都没有（`候选行=0`）——
两件事修的是同一条缝：**这把尺必须知道自己在量哪张图**。

六把刀各自钉一环：

  M931 把场景钉的色档改成亮档          ⇒ 前提⓪红（"请求的那一档"与"尺有对象的那一档"必须相等）
  M932 把钉色档那三行整块撤掉          ⇒ 前提⓪红 —— **本机相关**：只有当机器自己在亮档时
       才咬得住（机器在暗档时撤掉钉 == 什么都没坏，PASSED 是正确答案，不是尺没牙）
  M933 拆掉"洞太窄"这道形状闸          ⇒ 字缝那格证人红
  M934 拆掉"宽度不稳"这道形状闸        ⇒ 刚体被拉长那格证人红
  M935 拆掉"不贴两端"这道形状闸        ⇒ runner 那一朵假红的形状（走在中间的洞）无人拦
  M936 让点名器不再剥注释              ⇒ 缺席点名的正对照红（注释里的工厂被数成场景）

M933…M935 打在 `MotionFilmstripTests` 的纯尺上，红却落在 `MotionPillRampTests` 的合成证人上 ——
**尺住在产物卷、证人住在纯函数卷**，所以每臂的 EXPECTED 用例名与 FILTER 都不同（表按臂取）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r324.py [M931 …]
（M931/M932 那一臂要 `CLIPBOARD_HISTORY_UI_MOTION=1`，表里已经带上；没设就会得到 skip，
 而 skip 在这一支表里是 NOT_RUN，不是过关。）
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
ENV["CLIPBOARD_HISTORY_UI_MOTION"] = u"1"

RAMP = u"MotionFilmstripTests/testFilterPillRampIsMonotone"
PURE = u"MotionPillRampTests"

# ① 场景请求的色档改成亮档：前提⓪两条（请求==要求 / 胶片==要求）都必须红。
NEEDLE_931 = u"                     appearance: .darkAqua,\n"
REPL_931 = u"                     appearance: .aqua,\n"

# ② 钉色档那三行整块撤掉（保留 `if let` 以免未用变量告警）。
NEEDLE_923_932 = (u"            NSApplication.shared.appearance = requested\n"
                  u"            window.appearance = requested\n"
                  u"            host.appearance = requested\n")
REPL_932 = u"            _ = requested\n"

# ③④⑤ 三道形状闸：闸条件恒假 ⇒ 变量仍然被用（不引入告警），但不再拦任何东西。
NEEDLE_933 = u"        if narrow {\n"
REPL_933 = u"        if narrow && false {\n"
NEEDLE_934 = u"        } else if abs(wA - wB) > tol {\n"
REPL_934 = u"        } else if abs(wA - wB) > tol && false {\n"
NEEDLE_935 = u"        } else if !oppositeEnds {\n"
REPL_935 = u"        } else if !oppositeEnds && false {\n"

# ⑥ 点名器不再剥注释：注释里那颗 `static func commentedOut() -> Scenario {` 会被数进来。
NEEDLE_936 = (u"    static func scenarioPinCensus(code: String) -> (pinned: [String], unpinned: [String]) {\n"
              u"        let lines = code.components(separatedBy: \"\\n\")\n"
              u"            .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix(\"//\") }\n")
REPL_936 = (u"    static func scenarioPinCensus(code: String) -> (pinned: [String], unpinned: [String]) {\n"
                   u"        let lines = code.components(separatedBy: \"\\n\")\n")

ARMS = [
    # 形状沿用预检认的那种：(刀号, 说明, 目标文件, needle, 变异文, 期望红名, 该臂的 --filter)
    ("M931", u"尺：场景钉的色档改成亮档 ⇒ 前提⓪必须红", FILM,
     NEEDLE_931, REPL_931, u"testFilterPillRampIsMonotone", RAMP),
    ("M932", u"尺：钉色档那三行整块撤掉 ⇒ 前提⓪必须红（只在机器自己处于亮档时咬得住）", FILM,
     NEEDLE_923_932, REPL_932, u"testFilterPillRampIsMonotone", RAMP),
    ("M933", u"尺：拆掉「洞太窄」闸 ⇒ 字缝那格证人必须红", FILM,
     NEEDLE_933, REPL_933, u"testMovingHoleReadingRejectsASlitTooNarrowForASegment", PURE),
    ("M934", u"尺：拆掉「宽度不稳」闸 ⇒ 刚体拉长那格证人必须红", FILM,
     NEEDLE_934, REPL_934, u"testMovingHoleReadingRejectsAStretchingHole", PURE),
    ("M935", u"尺：拆掉「不贴两端」闸 ⇒ runner 那朵假红的形状必须有人拦", FILM,
     NEEDLE_935, REPL_935, u"testMovingHoleReadingRejectsAHoleThatWandersInTheMiddle", PURE),
    ("M936", u"尺：点名器不剥注释 ⇒ 缺席点名的正对照必须红", FILM,
     NEEDLE_936, REPL_936, u"testScenarioPinCensusSeparatesPinnedFromUnpinnedAndSkipsComments", PURE),
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

    # 基线：两支 FILTER 都要绿，否则后面每一朵 CAUGHT 都不说明任何事。
    restore()
    for filt in sorted({a[6] for a in arms}):
        n, red, names, out, skipped = run_suite(filt)
        if skipped:
            restore()
            print(u"PRECHECK_FAILED 基线里 %s 被 skip（skipped=%d）⇒ 没设 CLIPBOARD_HISTORY_UI_MOTION=1"
                  % (filt, skipped))
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
            print(u"%s CAUGHT %s（Executed=%d）红在：%s" % (arm_id, why[:30], n, u", ".join(names)))
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
