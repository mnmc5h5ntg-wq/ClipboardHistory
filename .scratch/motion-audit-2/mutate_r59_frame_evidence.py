#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R59 变异对照：逐帧图、图标跟踪、分栏测量、以及 CI 那句"为什么红"。

R59 做的事是"把已经存在的中间态变成看得见的东西"。这类改动的坏法不是算错，
而是**悄悄什么都没量**：图没写出来、写出来是一叠同一张、跟踪跟丢、两栏其实框了同一块。
所以五支全部打在"证据还在不在"上，没有一支是打在产品像素上（本轮产品零改动）。

  M301 `writeStack` 什么都不写           ⇒ 该红在"逐帧图没写出来"。
       这一支钉的是本轮台账里那句"我看了逐帧图"——没有它，那句话可以对着一个不存在的文件说。
  M302 `writeStack` 像 writeStrip 那样除二 ⇒ 该红在"又被缩过"。
       这正是本轮换掉 writeStrip 的理由：带卷只有 96px 高，除二之后横幅剩 38px，看不清。
  M303 图标的**跟踪区域**清空（x 40..<40）  ⇒ 该红在"跟踪没有对象"。
       第一版这支打的是判色阈值（r>120 → r>254），结果 **ESCAPED**：那颗图标本来就接近纯红，
       r=255 照样过 254 —— 一支打不坏任何东西的变异不是"判据没牙"，是电池自己空转（见 U-xx）。
       跟丢了的跟踪会给出一个干净的"质心不动 ⇒ 原地淡出"结论 —— 那是最坏的一种假绿。
  M304 两栏框成同一块（详情区宽度 0）     ⇒ 该红在"详情区那一侧最大相邻差"。
       没有这条前提，"两栏差 2–5 帧"可以是"其中一栏根本没在量"。
  M306 共享线的两道地板全拆掉          ⇒ 该红在真值表 (c)「整段没变化要自认作废」。
       这就是本轮我自己踩过一次的形状：两栏都是全零时，各自归一的线也是 0，
       `0 >= 0` 让每一帧都算"还在变"，"作废"那格反过来报成"两栏都动到最后一帧"。
  M307 共享线改成按**较小**峰值归一     ⇒ 该红在"共享线必须由较大那个峰值导出"。
       本轮的分栏结论就是从这条线上翻的：线不一样高的两栏比"谁先停"，比的是墨量。
  M305 CI 不打 XCTAssert 那句原文         ⇒ 自检 `red_test_prints_its_reason` 该红。
       现场：run 38576482491 里 `testTransitionsAreActuallyRunning` 红了 7.4s，
       而日志只有名字（BACKLOG 86）——"红要能读"这条 R36 定的规矩在 motion 那一步漏了半边。

用法：`python3 .scratch/motion-audit-2/mutate_r59_frame_evidence.py [--measure] [M301 … M307]`
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
REPO = os.path.join(ROOT, "ClipboardHistory")
TESTS = os.path.join(REPO, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
CI = os.path.join(ROOT, ".github/workflows/ci.yml")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
BASE_ENV["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
BASE_ENV["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r59-mut"

EVIDENCE = "MotionFilmstripTests.testBannerFrameStacksAreReadableEvidence"
TRACK = "MotionFilmstripTests.testBannerOutTracksWhetherItFadesOrSlides"
COLUMN = "MotionFilmstripTests.testBannerDismissColumnAsymmetryIsMeasured"
TRUTH = "MotionFilmstripTests.testSharedFloorColumnComparisonIsATruthTable"
SELFTEST = ["python3", "-m", "unittest", "scripts.tests.test_ci_report_selftest"]

MUTATIONS = [
    ("M301", "writeStack 什么都不写", TESTS, "swift",
     "        do { try data.write(to: url); return url } catch { return nil }",
     "        return nil   // MUTANT：图根本没落盘",
     EVIDENCE, ["逐帧图没写出来"]),
    ("M302", "writeStack 也按 width/2 画", TESTS, "swift",
     "        let fw = first.width, fh = first.height\n        let gap = Self.stackGap",
     "        let fw = first.width / 2, fh = first.height / 2   // MUTANT\n        let gap = Self.stackGap",
     EVIDENCE, ["又被缩过"]),
    # 第一版这里改的是判色阈值（r>120 → r>254），结果 **ESCAPED**：图标本来就接近纯红，
    # r=255 照样过 254 —— 一支打不坏任何东西的变异不是"判据没牙"，是电池自己空转。
    # 换成把**跟踪区域**清空（x 40..<40），这才是"布局一改，图标就出了窗口"的真实形状。
    ("M303", "图标的跟踪区域空了（布局一改就跟丢）", TESTS, "swift",
     "                for x in 40..<200 where x < bitmap.width {",
     "                for x in 40..<40 where x < bitmap.width {   // MUTANT",
     TRACK, ["跟踪没有对象"]),
    ("M304", "两栏框成同一块（详情区宽度 0）", TESTS, "swift",
     "        let detail = CGRect(x: 0.368, y: 0, width: 1 - 0.368, height: 1)",
     "        let detail = CGRect(x: 0.368, y: 0, width: 0, height: 1)   // MUTANT",
     COLUMN, ["详情区那一侧最大相邻差"]),
    # R59 后半段：两条自己证伪自己的读数（分栏时长、图标位移）各配一支。
    ("M306", "共享线塌成 0（回到本轮第一版那个 bug）", TESTS, "swift",
     """        guard peak(fractions) >= minimumVisibleChange else { return nil }
        // 第二道地板管的是**共享线自己塌到 0**：两栏全零时线也是 0，而 `0 >= 0`
        // 会让每一帧都算"还在变"，"作废"那格反而报成"两栏都动到最后一帧"
        // —— 真值表的 (c) 第一次就是这么红的。
        return fractions.lastIndex { $0 >= max(floor, minimumVisibleChange) }""",
     "        return fractions.lastIndex { $0 >= floor }   // MUTANT：两道地板都没有",
     TRUTH, ["自认作废"]),
    ("M307", "共享线改成按第一栏归一（又变成各量各的）", TESTS, "swift",
     "        (regions.map { peak($0) }.max() ?? 0) * stepFloorRatio",
     "        (regions.map { peak($0) }.min() ?? 0) * stepFloorRatio   // MUTANT",
     TRUTH, ["共享线必须由**较大**那个峰值导出"]),
    ("M305", "CI 不打 XCTAssert 那句原文", CI, "ci",
     '          grep -E "error: -\\[" /tmp/motion.log | head -12 || true',
     '          : "MUTANT 只报名字不报理由"',
     None, ["red_test_prints_its_reason"]),
]


def run(kind, filter_name):
    if kind == "swift":
        argv, cwd = ["swift", "test", "--filter", filter_name], REPO
    else:
        argv, cwd = SELFTEST, ROOT
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          env=BASE_ENV, timeout=1800)
    out = proc.stdout + proc.stderr
    if kind == "swift":
        verdicts = [l for l in out.splitlines()
                    if "Test Case" in l and ("passed" in l or " failed" in l)]
        if not verdicts:
            return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
        failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
        if "error:" in out and not failed:
            return "BROKEN-MUTATION", out, []
        return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed
    if "Ran " not in out:
        return "BROKEN-MUTATION", out, []
    names = [l.split()[1] for l in out.splitlines() if l.startswith("FAIL: ")]
    return ("ESCAPED" if out.strip().splitlines()[-1].startswith("OK") else "CAUGHT"), out, names


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:160]))
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(text.replace(old, new))
    return text


def restore(path, original):
    with open(path, "w", encoding="utf-8") as writer:
        writer.write(original)
    return open(path, encoding="utf-8").read() == original


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}
    for mid, desc, path, kind, old, new, filter_name, needles in MUTATIONS:
        n = open(path, encoding="utf-8").read().count(old)
        if n != 1:
            raise SystemExit("预检中止：%s 的锚点出现 %d 次（要 1 次）\n  %s" % (mid, n, old[:160]))
    for kind, filter_name in (("swift", EVIDENCE), ("swift", TRACK), ("swift", COLUMN), ("ci", None)):
        code, out, _ = run(kind, filter_name)
        if code != "ESCAPED":
            raise SystemExit("预检 %s/%s 失败：%s\n%s" % (kind, filter_name, code, out[-2500:]))
        print("预检 OK " + (filter_name or "ci_report_selftest"))
    results = []
    for mid, desc, path, kind, old, new, filter_name, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        try:
            code, out, failed = run(kind, filter_name)
        finally:
            ok = restore(path, original)
        hit = [needle for needle in needles if needle in out]
        right = code == "CAUGHT" and len(hit) >= 1
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO"))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s 命中=%s 还原干净=%s"
              % (mid, desc, code, right, failed[:3], hit, ok))
        if measure or not right:
            for line in [l for l in out.splitlines() if "error: -[" in l or "FAIL" in l
                         or "AssertionError" in l][:6]:
                print("   MSG| " + line.strip()[:300])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "yes" or r[1] != "CAUGHT"]
    dirty = [r for r in results if r[3] != "yes"]
    print("红得不对/未抓到=%d  还原不干净=%d" % (len(bad), len(dirty)))
    code, _, _ = run("swift", EVIDENCE)
    print("还原后复跑（逐帧图判据）：" + code)
    if dirty or bad or code != "ESCAPED":
        raise SystemExit("R59_MUTATION_PROBLEM")


main()
