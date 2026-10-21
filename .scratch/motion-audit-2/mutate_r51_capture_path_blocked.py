#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R51 变异对照：采集路径那两条判据**重做之后**，每一条都要再拆一次。

为什么 R49 的电池不算数：那一轮立的判据一（目录快照）本身就是错的 —— 它把后台原子写的
`history.json.sb-XXXX` 当成"主线程同步写"，在全量跑与 CI 上都红了，而红得不对。
R51 把它换成"把写队列堵起来 + 对照组放开后必须出现"。换了做法就得重新证明它有牙，
顺便回答两个新问题（M251、M253）。

  M249 产品侧：`save` 不排队列、直接在调用线程执行写   ⇒ 「那次写发生在调用线程上」该红
       —— 目标里那句"采集路径上不许有同步磁盘写"唯一可信的证明就是这个。
  M250 判据侧：永远不 `blocked.signal()`               ⇒ 对照组「存档仍然没出现」该红
       —— 证明那两条"没写盘"不是靠"根本没接上盘"来绿的。
  M251 判据侧：造库数量 480 → 1                        ⇒ 新加的前提地板该红
       —— **这一支在 R51 第一版是绿的**：当时地板写成 `fullArchiveEntries - 20`，
          改小 `fullArchiveEntries` 时地板跟着缩到 -19，自适应阈值恒真。
          现在地板是独立的绝对数 400，这一支才第一次有判别力。
  M252 产品侧：账本永不落盘                            ⇒ 「账本始终没落盘」该红
       —— 阶段一那条"可回溯"要求的对照组：计数只活在内存里时必须有人拦。
  M253 灵敏度：**主线程快照成本 ×2**（expected=escape）⇒ 预计没有任何断言红
       —— 这一支不是"必须被抓到"，是**量尺的分辨率**：本机 median 2.49ms / 门槛 20ms
          ⇒ 2 倍成本仍在门槛之下。绿 = 这条时长判据只防得住数量级的退化，防不住 2 倍。
          把它写进账本而不是偷偷调门槛：收紧到 5ms 等于把 CI 那台更慢的机器判成产品缺陷
          （R38 那条规矩），而那才是真的"为过夹具改判据"。

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import os
import subprocess
import sys

# 包根由本文件自己的位置推 —— **不许写死本机绝对路径**（R276 / D-260 的第二次发作）：
# 这张表被 `mutate_r271.py` 在运行时读（needle 单一真相），而 `mutate_r271.py` 被脚本电池 import
# ⇒ runner 上 `os.path.relpath(这里的绝对路径, 仓库根)` 会算出 `../../../../wangziyi/Codex_Project0/...`
# 而不是仓库相对路径 ⇒ `test_the_static_mirror_equals_the_r51_needle` 在 run 39583125728 上红
# （STEP[9]「Release script tests」Ran 519 / failures=1，正文存 /tmp/r276_log1.txt）。
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HERE))
ROOT = os.path.join(REPO, "ClipboardHistory")
TESTS = os.path.join(ROOT, "Tests/ClipboardHistoryAppTests/CapturePathWriteBudgetTests.swift")
PERSIST = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/HistoryPersistence.swift")
LEDGER = os.path.join(ROOT, "Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift")
BASE_ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

TEST1 = "CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread"
TEST2 = "CapturePathWriteBudgetTests.testAddingACopyWithANearlyFullArchiveStaysInsideBudget"

SNAPSHOT = "        let snapshot = try saveSnapshot(from: entries)"
DISPATCH = "        saveQueue.async(execute: workItem)"
SIGNAL = "        blocked.signal()                        // 放开闸门"
ENTRIES = "    static let fullArchiveEntries = 480"
LEDGER_SAVE = "        saveQueue.asyncAfter(deadline: .now() + debounceSeconds, execute: workItem)"

# (编号, 说明, 文件, 锚点, 替换, 过滤器, 必须出现的失败消息, 预期)
MUTATIONS = [
    ("M249", "产品侧：写不排后台队列，在调用线程执行", PERSIST, DISPATCH,
     "        workItem.perform()   // MUTANT：同步写 = 搬回调用线程",
     TEST1, ['那次写发生在调用线程上'], "catch"),
    ("M250", "判据侧：闸门永远不放开（对照组坏掉）", TESTS, SIGNAL,
     "        // MUTANT：不放开闸门",
     TEST1, ['放开闸门之后存档仍然没出现'], "catch"),
    ("M251", "判据侧：造库数量 480 → 1", TESTS, ENTRIES,
     "    static let fullArchiveEntries = 1   // MUTANT",
     TEST2, ['造库没造满'], "catch"),
    ("M252", "产品侧：账本永不落盘", LEDGER, LEDGER_SAVE,
     "        workItem.cancel()   // MUTANT：计数只留在内存里",
     TEST1, ['账本始终没落盘'], "catch"),
    ("M253", "灵敏度：主线程快照成本 ×2", PERSIST, SNAPSHOT,
     "        let snapshot = try saveSnapshot(from: entries)\n"
     "        _ = try saveSnapshot(from: entries)   // MUTANT：×2 成本",
     TEST2, [], "escape"),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if line.startswith("FAIL:") or "error: -[" in line or "XCTAssert" in line]


def run(filter_name):
    try:
        proc = subprocess.run(["swift", "test", "--filter", filter_name],
                              cwd=ROOT, capture_output=True, text=True,
                              env=BASE_ENV, timeout=600)
    except subprocess.TimeoutExpired:
        return "HUNG", "(timeout 600s：判据把主线程等在自己的写上)", []
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


def readings(out):
    return [l.strip()[:160] for l in out.splitlines() if "CAPTURE_PATH" in l]


def main():
    measure = "--measure" in sys.argv
    wanted = {a for a in sys.argv[1:] if not a.startswith("--")}

    # 预检：两条判据在未变异时都必须全绿（M253 顺带拿基线读数）
    for filter_name in (TEST1, TEST2):
        code, out, failed = run(filter_name)
        if code != "ESCAPED":
            raise SystemExit("预检失败（%s）：%s\n%s" % (filter_name, code, out[-2500:]))
        print("预检 OK %s ⇒ 全绿 %s" % (filter_name.split(".")[-1], readings(out)))

    results = []
    for mid, desc, path, old, new, filter_name, needles, expect in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        try:
            code, out, failed = run(filter_name)
        finally:
            ok = restore(path, original)
        messages = failure_messages(out)
        hit = [needle for needle in needles if any(needle in m for m in messages)]
        if expect == "catch":
            verdict = "yes" if (code == "CAUGHT" and len(hit) == len(needles)) else "NO"
        else:  # escape：这一支要的是"看见尺子的分辨率"，红/绿都算结论
            verdict = "绿=只防数量级" if code == "ESCAPED" else "红=比声明的更灵敏"
        results.append((mid, code, verdict, "yes" if ok else "NO"))
        print("\n%s %s ⇒ %s  结论=%s  红在 %s  还原干净=%s"
              % (mid, desc, code, verdict, failed, ok))
        for line in readings(out):
            print("   RD | " + line)
        if measure or verdict == "NO" or code in ("BROKEN-MUTATION", "DID-NOT-RUN"):
            for line in messages[:8]:
                print("   MSG| " + line.strip()[:420])

    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    must_catch = [r for r in results if r[0] != "M253"]
    bad = [r for r in must_catch if r[2] != "yes"]
    dirty = [r for r in results if r[3] != "yes"]
    print("该红没红=%d  还原不干净=%d" % (len(bad), len(dirty)))
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad:
        raise SystemExit("MUTATION_UNCAUGHT=%d" % len(bad))


main()
