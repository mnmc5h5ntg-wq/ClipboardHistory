#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R130 的变异表：BACKLOG 155 那台「间隔分解」仪器的三格牙（M639-M641）。

本轮做的事：给 ⑤ 那条判据（省下的抓帧成本必须进采样率）配一台**读数仪器** ——
`bandIntervalFacts` 把「间隔 − 抓帧 = 这台机器的调度地板」这个分解交出来，
并显式允许「无从分解」这一格（间隔比抓帧还短说明两个量不是同一卷测的）。
本机第一次跑就给出 `带地板=5.03ms 整窗地板=4.99ms 谁细=带` —— 也就是在这台机器上
两臂的地板几乎相同，间隔差全部由抓帧成本解释。这正是 155 欠了 27 轮的那个形状。

三刀（都期望 CAUGHT）：
  M639 摘掉「间隔<抓帧」那一格 => 不同卷的两个量会被当成一次真实的"带更贵"来定罪
  M640 把哨兵值判据从 `== .greatestFiniteMagnitude` 改成 `isInfinite` => 「没帧」整格静默漏掉
       （这一格不是假想：我第一版就是写成 isInfinite 的，真值表前两行把它抓回来了）
  M641 「谁细」从比间隔改成比抓帧 => 尺读错了对象，而 155 的红正是这一格

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r130.py [M639 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
SRC = os.path.join(ROOT, "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
TRUTH = "MotionFilmstripTests/testBandIntervalFactsRulerIsATruthTable$"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M639", "摘掉「间隔<抓帧」那一格 => 不同卷的量会被当成一次真实的『带更贵』",
     '        if !who.isEmpty { return .notComparable(which: who.joined(separator: "/")) }',
     "        if false { return .notComparable(which: who.joined(separator: \"/\")) }", "CAUGHT"),
    ("M640", "哨兵值判据换成 isInfinite => 『任何一臂没有两帧』整格静默漏掉",
     "        if bandInterval == .greatestFiniteMagnitude || fullInterval == .greatestFiniteMagnitude {",
     "        if bandInterval.isInfinite || fullInterval.isInfinite {", "CAUGHT"),
    ("M641", "『谁细』改成比抓帧而不是比间隔 => 尺读错了对象",
     "                             bandFiner: bandInterval <= fullInterval)",
     "                             bandFiner: bandGrab <= fullGrab)", "CAUGHT"),
]


def read():
    return open(SRC, encoding="utf-8").read()


def save(text):
    open(SRC, "w", encoding="utf-8").write(text)


def run():
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", TRUTH],
                          cwd=os.path.join(ROOT, "ClipboardHistory"), env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    # 「0 failures」不是判据：filter 打偏时 swift test 也会安静地跑 0 条（U-423 同一族）。
    ran = re.search(r"Executed (\d+) test?", out)
    if not ran or int(ran.group(1)) == 0:
        return "DID-NOT-RUN", out
    if re.search(r"error: -\[", out):
        return "CAUGHT", out
    m = re.search(r"with 0 failures \(0 unexpected\)", out)
    if not m:
        return "DID-NOT-RUN", out
    return "PASSED", out


def main():
    wanted = set(sys.argv[1:])
    original = read()
    results, tally, mismatch, not_run = [], {}, 0, 0
    for name, note, needle, replacement, expect in ARMS:
        if wanted and name not in wanted:
            continue
        hits = original.count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]" % (name, hits))
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", note, ""))
            continue
        save(original.replace(needle, replacement, 1))
        verdict, out = run()
        save(original)
        tally[verdict] = tally.get(verdict, 0) + 1
        ok = verdict == expect
        mismatch += 0 if ok else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        first = ""
        for line in out.splitlines():
            if line.startswith("    ") and "error: -[" in line:
                first = line.strip()[:170]
                break
        print("%s: %s %s" % (name, verdict, note))
        results.append((name, expect, verdict, note, first))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R130 汇总 ===")
    for name, expect, verdict, note, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
