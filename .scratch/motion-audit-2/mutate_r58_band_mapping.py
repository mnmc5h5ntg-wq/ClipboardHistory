#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R58 变异对照：分带映射的方向、嵌套守卫、以及 CI 那份白名单。

R58 修的是 BACKLOG 80：`changedFraction(band:)` 把归一化带**上下颠倒**了，
于是这个文件里 7 处 `band:` 量的都是镜像位置。修它本身是一行；
这一轮真正要钉住的是三件"看起来已经好了"的事：

  M295 把 y 映射倒回去（就是本轮修掉的那个形状）  ⇒ 真值表该红（顶边那条带读不到顶边的差异）。
  M296 把 x 也倒回去                              ⇒ 真值表该红在横轴那一格。
       M295/M296 是一对：只测纵轴，横轴哪天被"顺手翻一下"没人知道。
  M297 让带永远不生效（退化成整幅）                ⇒ 真值表该红（"分带"与"不分带"读出一个数）。
       这一支钉的是"分带这件事本身还在不在"——只判方向的电池会放走一个把裁剪删掉的实现。
  M298 把嵌套框重新套回带捕获那一卷上              ⇒ 嵌套守卫该红。
       这是本轮实际改掉的那处（`testSlidingRoleSettlesWithinItsBudget`）：
       它读起来仍然是"横幅那一条"，实际量的是带里 9.5pt 的一条窄缝，
       而**两条判据都还绿** —— 没有这支变异，这件事会在下一轮再发生一次。
  M299 CI 的读数摘录退回硬编码前缀白名单           ⇒ 自检的 `family_not_in_any_list` 该红。
       白名单的问题是它随每一轮变旧：R55 的 MOTION_GRAB、R57 的 MOTION_BAND 都没进去，
       于是 run 38570965657 里"runner 上带捕获成没成功"在日志里查不到（BACKLOG 83）。
  M300 把嵌套守卫的谓词改成永远返回空数组          ⇒ 它自带的正对照该红。
       没有这一支，"守卫"可以退化成一段什么都不做的代码而全绿（本仓库反复记过的那一族）。

**知道没被钉住的**：`changeGrid`（R2 那台分带归因网格）现在行序对了，
但没有任何判据钉住"网格第 0 行是画面顶边"——它的输出只是给人读的一串字符。
本轮翻过这条映射之后，历史上所有**按行**读过的网格结论都要重看一遍
（M1 那条"斜坡来自右侧详情区"是按**列**读的，不受影响）。记 BACKLOG 84。

用法：`python3 .scratch/motion-audit-2/mutate_r58_band_mapping.py [--measure] [M295 …]`
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
BASE_ENV["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r58-mut"

TRUTH = "MotionFilmstripTests.testBandRectMapsToTheEndItClaims"
NEST = "MotionFilmstripTests.testNoTestFramesABandInsideABandCapturedFilm"
SELFTEST = ["python3", "-m", "unittest", "scripts.tests.test_ci_report_selftest"]

MUTATIONS = [
    ("M295", "y 映射倒回去（本轮修掉的那个形状）", TESTS, "swift",
     "            yStart = max(0, Int(band.minY * CGFloat(a.height)))\n"
     "            yEnd = min(a.height, Int(band.maxY * CGFloat(a.height)))",
     "            yStart = max(0, Int((1 - band.maxY) * CGFloat(a.height)))   // MUTANT\n"
     "            yEnd = min(a.height, Int((1 - band.minY) * CGFloat(a.height)))",
     TRUTH, ["顶边"]),
    ("M296", "x 映射也被倒回去", TESTS, "swift",
     "            xStart = max(0, Int(band.minX * CGFloat(a.width)))\n"
     "            xEnd = min(a.width, Int(band.maxX * CGFloat(a.width)))",
     "            xStart = max(0, Int((1 - band.maxX) * CGFloat(a.width)))   // MUTANT\n"
     "            xEnd = min(a.width, Int((1 - band.minX) * CGFloat(a.width)))",
     TRUTH, ["最左"]),
    ("M297", "带永远不生效（分带退化成整幅）", TESTS, "swift",
     "        if let band {",
     "        if let band, band.height < 0 {   // MUTANT：分支永远走 else",
     TRUTH, ["整幅读数不是 0.2", "顶边"]),
    ("M298", "把嵌套框重新套回带捕获那一卷", TESTS, "swift",
     "        guard Self.premisePictureChanged(film.motionFrames, band: nil) else {",
     "        guard Self.premisePictureChanged(film.motionFrames,"
     " band: CGRect(x: 0.05, y: 0.02, width: 0.90, height: 0.20)) else {",
     NEST, ["窄缝"]),
    ("M299", "CI 的读数摘录退回硬编码前缀白名单", CI, "ci",
     '          grep -E "^MOTION_" /tmp/motion.log | head -120 || true',
     '          grep -E "MOTION_(SUMMARY|RESOLVE_SUMMARY|NATIVE)" /tmp/motion.log | head -24 || true',
     None, ["family_not_in_any_list"]),
    ("M300", "嵌套守卫的谓词永远返回空数组", TESTS, "swift",
     "        return passed.filter { bandFilms.contains($0) }",
     "        return []   // MUTANT：谓词退化成什么都不报",
     NEST, ["明显的嵌套现场上什么都没报"]),
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
    for kind, filter_name in (("swift", TRUTH), ("swift", NEST), ("ci", None)):
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
    code, _, _ = run("swift", TRUTH)
    print("还原后复跑（分带真值表）：" + code)
    if dirty or bad or code != "ESCAPED":
        raise SystemExit("R58_MUTATION_PROBLEM")


main()
