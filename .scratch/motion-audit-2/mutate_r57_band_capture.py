#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R57 变异对照：带捕获（把抓帧成本降下来那一改）与它的**位置**判据。

R57 做的事是"横幅那两臂从判不到变成判得到"，靠的是把捕获区域从整窗收到顶部一条带。
这种改动最像成功的样子是：**带在错的地方，但所有读数都变好了**。
本轮真的撞上过这一次 —— 第一版的 `bannerBand` 按 AppKit"原点在左下"写，
而 `NSHostingView` 是翻转的，于是带抓到了窗口底部，而四条"有没有变化"的前提一条都没拦住
（横幅撤走之后下面整块列表在位移，位移也是变化）。所以这九支里六支打在"带在不在该在的地方"。

  M286 把带挪回窗口底部（本轮真实犯过的那次）  ⇒ 该红在**位置同一性**那条（"同一头 … 的像素不同"）。
       这一支是本轮的判据本体：它红了，才说明"带在错地方"这件事从今天起是**会红的**。
  M287 `captureRect` 变成装饰（永远抓整窗 bounds） ⇒ 该红在①（帧高没变小）。
       钉的是"我传了个 rect"和"抓的真是那个 rect"是两件事。
  M288 同一性里把头尾两次比较对调               ⇒ 该红在同一头那条（0.954 > 0.005）。
  M289 同一性里两条都比同一头（另一条恒真）     ⇒ 该红在另一头那条（0.000 < 0.5）。
       M288/M289 是**一对**：只钉住一边，另一边就能悄悄变成装饰。
       本仓库"自适应阈值恒真"那一族说的就是这件事 —— 一条"两头都一样"的判据什么都没在量。
  M290 `MOTION_BAND` 那行退回 print             ⇒ R56 的源码扫描该红（"只走 stdout"）。
       新加的读数必须走同一条通道，否则它在 CI 里和 stdout 一起丢。
  M291 登记表里 `notice-banner` 的 must_judge 退回 false ⇒ 脚本测试该红（地板不是常数 2）。
  M292 闸门里 must_judge 集合算成空（地板=0）   ⇒ 脚本测试该红（红在 floor 那一格）。
       M291/M292 是"修好之后闸门真的关上了"这一半：本轮把两臂从放行改回要求，
       如果没人测这条改动的后果，那它和没改一样。
  M293 撤掉 dismiss 那一臂的 `captureRect:`      ⇒ 接线守卫该红（"不再声明 captureRect"）。
       A/B 那条判据**看不见这一坏**：它自己构造场景，只管"带值不值"，不管"这一臂用没用带"。
  M294 登记表里偷偷把 dismiss 臂放行              ⇒ 同一条接线守卫该红（它比对登记表的方向）。
       M293/M294 一起钉的是"带捕获、接线、登记表"三件事必须同向 ——
       少任何一件，"横幅两臂都判得到"就退回一句注释。

**知道没被钉住的**：带的高度（48pt）本身没有判据 —— 它现在装得下横幅（实测 38pt + 分隔线），
但横幅哪天变高（多行文案 + 动作按钮）就会溢出带外，而带外的变化仍然会让"有变化"那几条绿着过去。
今天拦得住它的是 `bandMustHoldChangeFraction`（首尾差 0.02，实测 0.885，掉一半以下才红），
不是"带必须盖住横幅"。记进 BACKLOG 81。

用法：`python3 .scratch/motion-audit-2/mutate_r57_band_capture.py [--measure] [M286 …]`
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
REPO = os.path.join(ROOT, "ClipboardHistory")
TESTS = os.path.join(REPO, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
GATE_PY = os.path.join(ROOT, "scripts/motion_floor_gate.py")
REGISTRY = os.path.join(ROOT, "scripts/motion_floor_expectations.json")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
# 这一对必须在这里显式给：少一个开关，探针就 `Test skipped`，
# 而 skipped 在 harness 里是"DID-NOT-RUN"（预检会拦住）—— 曾经有一支电池就是
# 这样绿着跑完 0 支变异的：判据没跑 ≠ 判据没红。
BASE_ENV["CLIPBOARD_HISTORY_UI_MOTION"] = "1"
BASE_ENV["CLIPBOARD_HISTORY_MOTION_OUT"] = "/tmp/r57-mut"

AB = "MotionFilmstripTests.testBandCaptureIsCheaperAndStillSeesTheMotion"
WIRING = "MotionFilmstripTests.testBandCaptureIsWiredIntoBothBannerArms"
CHANNEL = "MotionFilmstripTests.testMotionReadingsUseTheFileChannel"
GATE_TESTS = ["python3", "-m", "unittest", "scripts.tests.test_motion_floor_gate"]

MUTATIONS = [
    ("M286", "带挪回窗口底部（本轮真实犯过的那次）", TESTS, "swift",
     "            let y = view.isFlipped ? 0 : max(0, view.bounds.height - height)",
     "            let y = view.isFlipped ? max(0, view.bounds.height - height) : 0   // MUTANT",
     AB, ["同一头"]),
    ("M287", "captureRect 变成装饰（永远抓整窗）", TESTS, "swift",
     "        let capture = fullCapture ? nil : scenario.captureRect?(host)",
     "        let capture: NSRect? = nil   // MUTANT",
     AB, ["rect 被忽略了"]),
    ("M288", "位置同一性把头尾对调", TESTS, "swift",
     "        return (diff(from: 0), diff(from: b.height - a.height))",
     "        return (diff(from: b.height - a.height), diff(from: 0))   // MUTANT",
     AB, ["同一头"]),
    ("M289", "位置同一性两条都比同一头（另一条恒真）", TESTS, "swift",
     "        return (diff(from: 0), diff(from: b.height - a.height))",
     "        return (diff(from: 0), diff(from: 0))   // MUTANT",
     AB, ["两头一模一样"]),
    ("M290", "MOTION_BAND 退回 print（不走文件通道）", TESTS, "swift",
     '        emit("MOTION_BAND dismiss 带：',
     '        print("MOTION_BAND dismiss 带：',
     CHANNEL, ["只走 stdout"]),
    ("M291", "登记表把 notice-banner 放回放行", REGISTRY, "gate",
     '    "notice-banner": {\n      "must_judge": true,',
     '    "notice-banner": {\n      "must_judge": false,',
     None, ["testRegistryIsStrictAgain"]),
    ("M292", "闸门算出的地板是 0（must_judge 集合被清空）", GATE_PY, "gate",
     '    must_judge = {name for name, spec in arms.items() if spec.get("must_judge")}',
     "    must_judge = set()   // MUTANT",
     None, ["testFloorIsTheMustJudgeCountNotTwo"]),
    ("M293", "撤掉 dismiss 那一臂的 captureRect（接线断在一臂上）", TESTS, "swift",
     "                     captureRect: Scenario.bannerBand) { store in\n"
     "                store.dismissPasteFailure()",
     "                     captureRect: nil) { store in   // MUTANT\n"
     "                store.dismissPasteFailure()",
     WIRING, ["不再声明 captureRect"]),
    ("M294", "登记表与守卫不同向（dismiss 臂偷偷放行）", REGISTRY, "swift",
     '    "notice-banner-dismiss": {\n      "must_judge": true,',
     '    "notice-banner-dismiss": {\n      "must_judge": false,',
     WIRING, ["不是 must_judge=true"]),
]


def run(kind, filter_name):
    if kind == "swift":
        argv, cwd = ["swift", "test", "--filter", filter_name], REPO
    else:
        argv, cwd = GATE_TESTS, ROOT
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
    for kind, filter_name in (("swift", AB), ("swift", WIRING), ("swift", CHANNEL), ("gate", None)):
        code, out, _ = run(kind, filter_name)
        if code != "ESCAPED":
            raise SystemExit("预检 %s/%s 失败：%s\n%s" % (kind, filter_name, code, out[-2500:]))
        print("预检 OK " + (filter_name or "motion_floor_gate"))
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
    code, _, _ = run("swift", AB)
    print("还原后复跑（带捕获 A/B）：" + code)
    if dirty or bad or code != "ESCAPED":
        raise SystemExit("R57_MUTATION_PROBLEM")


main()
