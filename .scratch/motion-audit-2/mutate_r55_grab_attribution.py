#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R55 变异对照：抓帧成本归因（三档分档 + 接线 + 那条面积前提）。

R55 做的事是"把一条含糊的 skip 行拆成可判读的归因"，而含糊判据的变异对照有个特有的坑：
**纯函数红了不代表线上有数**。所以这一支电池一半打在分档逻辑上，另一半打在线与前提上。

  M269 分档侧：`overshoot <= allowance` 改成 `<`
       ⇒ 真值表那一格（100/92 差正好 8）该红。钉的是"余量边界inclusive"。
  M270 分档侧：`grabDominates` 那一档整个删掉（回落到 `outsideTheGrab`）
       ⇒ 该红，而且红在**真读数那一格**（97/87.9）。
       这一支就是本轮的靶：两档版本曾经把"抓帧解释了 91%"报成"不是抓帧的锅"，
       而这个建议会把 BACKLOG 77 的修法引到错误的方向上。
  M271 分档侧：`worstIntervalMilliseconds > 0` 那道 guard 摘掉
       ⇒ 该红（0/5 会从 unknown 变成 probeBound）。钉的是"除零不许产出一个看起来像读数的数"。
  M272 接线侧：结论行里的归因换成空串
       ⇒ 接线守卫该红。这一支是 M269–M271 都测不到的那种坏法：**函数还在，没人调它**。
  M273 接线侧：`Film` 不接抓帧器的数（写死 −1）
       ⇒ 接线守卫该红。真值表**不会**红 —— 它测的是纯函数，读不到这里。
  M274 前提侧：面积那条测量里 `cacheDisplay` 不真的画
       ⇒ 面积判据该红在"抓取没执行"那一格，而不是掉进"这台机器太快"的早退分支绿着走。
       这一支是本轮新加的那格前提断言的存在理由。
  M275 判据侧：`grabAreaCostRatioFloor` 从 1.5 改成 1.0
       ⇒ 该红（恒真自检那一格）。地板 =1 就是"面积毫无关系也算通过"。
  M276 尺子侧：`Grabber.tick` 不再 append 计时
       ⇒ 接线守卫该红（空数组那一格）。

**知道没被钉住的**：`MOTION_GRAB` 那行 print 本身。删掉它没有任何判据会红 ——
它是诊断输出，不承载结论；本轮刻意不为它加守卫（加了就是"守卫数量"而非"判据内容"）。
代价写进 BACKLOG 77：读不到抓帧数的那次运行，归因会退回 `grab-unmeasured` 而不是报错。

用法：`python3 .scratch/motion-audit-2/mutate_r55_grab_attribution.py [--measure] [M269 …]`
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
MOTION_ENV = dict(BASE_ENV, CLIPBOARD_HISTORY_UI_MOTION="1")

TABLE = "MotionFilmstripTests.testGrabAttributionIsATruthTable"
WIRE = "MotionFilmstripTests.testGrabAttributionIsWiredIntoTheCoarseNotRunLines"
AREA = "MotionFilmstripTests.testGrabCostScalesWithCapturedArea"

MUTATIONS = [
    ("M269", "分档侧：余量边界从 <= 改成 <", TESTS, BASE_ENV,
     "            if overshoot <= allowanceMilliseconds {",
     "            if overshoot < allowanceMilliseconds {   // MUTANT",
     TABLE, ["probeBound"]),
    ("M270", "分档侧：grabDominates 那一档删掉（两档版）", TESTS, BASE_ENV,
     "            return explained >= dominatesRatio\n"
     "                ? .grabDominates(explainedRatio: explained, overshootMilliseconds: overshoot)\n"
     "                : .outsideTheGrab(explainedRatio: explained, overshootMilliseconds: overshoot)",
     "            return .outsideTheGrab(explainedRatio: explained, overshootMilliseconds: overshoot)   // MUTANT",
     TABLE, ["grabDominates"]),
    ("M271", "分档侧：间隔≤0 那道 guard 摘掉", TESTS, BASE_ENV,
     # R373 / BACKLOG 367：classify 挪进 `GrabAttribution` 之后参数名从 worstInterval 改成 clockInterval，
     # 旧针命中 0 ⇒ rot。重钉到今天的 guard。
     "            guard worstGrabMilliseconds >= 0, clockIntervalMilliseconds > 0 else { return .unknown }",
     "            guard worstGrabMilliseconds >= 0 else { return .unknown }   // MUTANT",
     TABLE, ["unknown"]),
    ("M272", "接线侧：结论行里的归因换成空串", TESTS, BASE_ENV,
     # R373：调用点的参数名同样改成 clockIntervalMilliseconds。
     "                    + Self.grabAttributionLabel(clockIntervalMilliseconds: worstInRun,\n"
     "                                                worstGrabMilliseconds: film.worstGrabMilliseconds))",
     "                    + (\"\" /* MUTANT: 归因从结论行摘掉 */))",
     WIRE, ["只接了 0 次归因"]),
    ("M273", "接线侧：Film 不接抓帧器的数", TESTS, BASE_ENV,
     "\n                    worstGrabMilliseconds: grabber.worstGrabMilliseconds)",
     "\n                    worstGrabMilliseconds: -1)   // MUTANT",
     WIRE, ["线没接上"]),
    ("M274", "前提侧：面积测量不真的画", TESTS, MOTION_ENV,
     "            if let rep = host.bitmapImageRepForCachingDisplay(in: rect) {\n"
     "                host.cacheDisplay(in: rect, to: rep)\n"
     "            }",
     "            if let rep = host.bitmapImageRepForCachingDisplay(in: rect) {\n"
     "                _ = rep   // MUTANT: 取了 rep 但没画\n"
     "            }",
     AREA, ["夹具坏了"]),
    ("M275", "判据侧：面积地板从 1.5 改成 1.0", TESTS, MOTION_ENV,
     "    static let grabAreaCostRatioFloor: Double = 1.5",
     "    static let grabAreaCostRatioFloor: Double = 1.0   // MUTANT",
     AREA, ["恒真"]),
    ("M276", "尺子侧：Grabber 不再记录每次抓帧耗时", TESTS, BASE_ENV,
     "        grabMilliseconds.append(Double(DispatchTime.now().uptimeNanoseconds - began.uptimeNanoseconds) / 1_000_000)",
     "        // MUTANT: 不 append",
     WIRE, ["空数组"]),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if line.startswith("FAIL:") or "error: -[" in line or "XCTAssert" in line]


def run(filter_name, env):
    proc = subprocess.run(["swift", "test", "--filter", filter_name],
                          cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    out = proc.stdout + proc.stderr
    verdicts = [l for l in out.splitlines() if "Test Case" in l and ("passed" in l or " failed" in l)]
    if not verdicts:
        return ("BROKEN-MUTATION" if "error:" in out else "DID-NOT-RUN"), out, []
    failed = [l.split("]")[0].replace("Test Case '-[", "") for l in verdicts if " failed" in l]
    if "error:" in out and not failed:
        return "BROKEN-MUTATION", out, []
    return ("CAUGHT" if proc.returncode != 0 else "ESCAPED"), out, failed


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
    # 锚点先数一遍：电池跑到第六支才发现锚点不唯一，前面烧掉的构建就白烧了。
    for mid, desc, path, env, old, new, filter_name, needles in MUTATIONS:
        n = open(path, encoding="utf-8").read().count(old)
        if n != 1:
            raise SystemExit("预检中止：%s 的锚点出现 %d 次（要 1 次）\n  %s" % (mid, n, old[:160]))
    # 三条判据在干净树上都必须绿（AREA 要开 motion 环境变量，否则是 skip 而不是跑）。
    for filter_name, env in ((TABLE, BASE_ENV), (WIRE, BASE_ENV), (AREA, MOTION_ENV)):
        code, out, _ = run(filter_name, env)
        if code != "ESCAPED":
            raise SystemExit("预检 %s 失败：%s\n%s" % (filter_name, code, out[-2500:]))
        print("预检 OK " + filter_name.split(".")[-1])
    results = []
    for mid, desc, path, env, old, new, filter_name, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        try:
            code, out, failed = run(filter_name, env)
        finally:
            ok = restore(path, original)
        messages = failure_messages(out)
        hit = [needle for needle in needles if any(needle in m for m in messages)]
        right = code == "CAUGHT" and len(hit) >= 1
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO"))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s 还原干净=%s" % (mid, desc, code, right, failed, ok))
        if measure or not right or code != "CAUGHT":
            for line in messages[:8]:
                print("   MSG| " + line.strip()[:320])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "yes" or r[1] != "CAUGHT"]
    dirty = [r for r in results if r[3] != "yes"]
    print("红得不对/未抓到=%d  还原不干净=%d" % (len(bad), len(dirty)))
    code, _, _ = run(TABLE, BASE_ENV)
    print("还原后复跑（真值表）：" + code)
    if dirty or bad or code != "ESCAPED":
        raise SystemExit("R55_MUTATION_PROBLEM")


main()
