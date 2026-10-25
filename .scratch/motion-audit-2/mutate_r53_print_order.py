#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R53 变异对照：`MOTION_NATIVE_MOVE 判定=` 的**打印位置**，以及取区域的助手自己。

这一族为什么必须变异：R50 加这行结论时把它留在 `requireAppWasActive` 后面，
于是 runner 每次跳过这一臂，日志就只剩"两臂读数有、结论行没有"——
R50 想消灭的含糊，被 R50 自己的排版选择重新造了出来（两次 run 实测：
38543090198 / 38543812477 都有四行 `MOTION_NATIVE`，零行 `MOTION_NATIVE_MOVE`）。
R53 把它挪到 skip 之前，并加一条顺序守卫。**顺序这种东西，没有变异就等于没有守卫。**

  M260 删掉那行结论打印                 ⇒ 守卫该红（"runner 一跳过就又没有任何结论"）
  M261 删掉 `requireAppWasActive` 那道闸 ⇒ 守卫该红（非激活进程的读数会被当成产品结论）
  M262 `region()` 换回 `contains`        ⇒ 守卫该红 —— **这一支是本轮最要紧的一支**：
       守卫自己要在源码里写下被守卫者的名字，`contains` 会先命中守卫自己那一行，
       于是区域变成守卫自己的函数体（里面当然没有 `XCTFail(`）。
       R53 第一版就是这么红的：三条断言里有两条是在读守卫自己写的字面量。
  M263 把 `notAnimated` 那格的 XCTFail 换成 print ⇒ 守卫该红（三态里最要紧的一格没人负责）

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0/ClipboardHistory"
FILM = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
# R371 / BACKLOG 367：旧名 `testNativeMove` 早已改成 `testNativeRowMoveIsVisibleToTheRuler`，
# 过滤串不跟着改 ⇒ 一整张表跑出 0 格（当年就是「没跑」被读成「没红」）。
# R371 更正：原过滤串 `testNativeMove` **本来就**匹配守卫的真名
# `testNativeMoveVerdictPrintsBeforeTheSkipGuards`，它不是腐烂源（我第一次归因错了，
# 一度把它改到探针 `testNativeRowMove…` 上，那一遍 4 臂全 ESCAPED —— 0 格被读成"没红"）。
# 真正的腐烂只有 M260：R355 把结论行从 `print(` 换成 `emit(`，针没跟着搬。
FILTER = "MotionFilmstripTests.(testNativeMoveVerdictPrints|testFadeAB)"

VERDICT_PRINT = ('        emit("MOTION_NATIVE_MOVE 判定=\\(verdictLabel) 峰值容差="\n'
                 '            + String(format: "%.3f", Self.nativeMovePeakTolerance)\n'
                 '            + "（同一卷的 insert 读数在上一行：insert 能看见多帧 ⇒ 通道不瞎）"\n'
                 '            + "；这一行只说读数怎么读，产品结论要过下面两道 skip 才算")\n')
SKIP_PAIR = ('            + "；这一行只说读数怎么读，产品结论要过下面两道 skip 才算")\n'
             '        try await requireObservableMotion(.layout)\n'
             '        try requireAppWasActive(probe.wasActive)\n')
SKIP_PAIR_KEEP = ('            + "；这一行只说读数怎么读，产品结论要过下面两道 skip 才算")\n'
                  '        try await requireObservableMotion(.layout)\n')
REGION_CONTAINS = "        guard let start = lines.firstIndex(where: {\n" \
                  "            $0.trimmingCharacters(in: .whitespaces).hasPrefix(trimmedDeclaration)\n" \
                  "        }) else {"
NOT_ANIMATED_FAIL = '        case .notAnimated(let a, let ap, let i, let ip):\n            XCTFail("两臂形状一致'

MUTATIONS = [
    ("M260", "删掉结论行", FILM, VERDICT_PRINT,
     "", ['结论行没了']),
    ("M261", "删掉 skip 那道闸", FILM, SKIP_PAIR,
     SKIP_PAIR_KEEP, ['skip 那道闸没了']),
    ("M262", "region() 换回 contains（会命中守卫自己）", FILM, REGION_CONTAINS,
     "        guard let start = lines.firstIndex(where: { $0.contains(declaration) }) else {",
     ['XCTFail 没了', '区域取不到']),
    ("M263", "notAnimated 那格从判红改成只打印", FILM, NOT_ANIMATED_FAIL,
     '        case .notAnimated(let a, let ap, let i, let ip):\n            print("两臂形状一致',
     ['XCTFail 没了']),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if line.startswith("FAIL:") or "error: -[" in line or "XCTAssert" in line]


def run():
    proc = subprocess.run(["swift", "test", "--filter", FILTER],
                          cwd=ROOT, capture_output=True, text=True, env=BASE_ENV, timeout=1800)
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
        raise SystemExit("注入中止：那段话出现 %d 次，不是 1 次 —— 电池与代码脱节\n  %s" % (n, old[:120]))
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
    # 先把**所有**锚点数一遍再跑第一次测试：M261 第一版的锚点（那两行 skip）在文件里出现 3 次，
    # 电池跑到它才中止，前面两次三分半的构建就白烧了。锚点数量是纯文本检查，没有理由放在后面。
    for mid, desc, path, old, new, needles in MUTATIONS:
        n = open(path, encoding="utf-8").read().count(old)
        if n != 1:
            raise SystemExit("预检中止：%s 的锚点出现 %d 次（要 1 次）\n  %s" % (mid, n, old[:120]))
    code, out, _ = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-2500:])
    print("预检 OK（未变异时三条守卫全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        try:
            code, out, failed = run()
        finally:
            ok = restore(path, original)
        messages = failure_messages(out)
        hit = [needle for needle in needles if any(needle in m for m in messages)]
        # 这一族的 needles 是"可接受的同义失败消息"列表（M262 有两种红法），所以是 any-of。
        right = code == "CAUGHT" and len(hit) >= 1
        results.append((mid, code, "yes" if right else "NO", "yes" if ok else "NO"))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s 还原干净=%s" % (mid, desc, code, right, failed, ok))
        if measure or not right or code != "CAUGHT":
            for line in messages[:8]:
                print("   MSG| " + line.strip()[:300])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[2] != "yes" or r[1] != "CAUGHT"]
    dirty = [r for r in results if r[3] != "yes"]
    print("红得不对/未抓到=%d  还原不干净=%d" % (len(bad), len(dirty)))
    code, out, _ = run()
    print("还原后复跑：" + code)
    if dirty or bad or code != "ESCAPED":
        raise SystemExit("R53_MUTATION_PROBLEM")


main()
