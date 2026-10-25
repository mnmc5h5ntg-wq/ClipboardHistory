#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R133 的变异表：⑤ 那三个出口各自的牙（M647-M649 / BACKLOG 174）。

三刀（都期望 CAUGHT，且**落在不同测试上** —— U-428 那格债）：
  M647 让"地板主导"这一格恒假 => 两行真测量里 runner 那一行不再落在第三个出口
  M648 让判定恒为"带更细"     => 合成样本里 coarser 那一格没人证
  M649 摘掉"没有帧"那一格     => 探针坏了会被读成产品结论（U-433 同一族）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r133.py [M647 ...]
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
SRC = os.path.join(ROOT, "ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift")
FILTER = "MotionFilmstripTests/testSamplingRateVerdict"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M647", "地板主导恒假 => 那台机器判不了这件事没人说出来",
     "        if floor > saved { return .floorDominant(schedulerMilliseconds: floor, savedMilliseconds: saved) }",
     "        if false { return .floorDominant(schedulerMilliseconds: floor, savedMilliseconds: saved) }",
     "CAUGHT"),
    ("M648", "判定恒为『带更细』=> 带更粗那一格失去证人（判据变成装饰）",
     "        return bandInterval <= fullInterval ? .finer : .coarser",
     "        return .finer", "CAUGHT"),
    # needle 要带上**下一行**：那一句哨兵判断在 `bandIntervalFacts` 与 `samplingRateVerdict`
    # 里字面相同（命中 2 次 ⇒ DID-NOT-RUN），只靠这一行分不清摘的是哪一格（U-442）。
    ("M649", "摘掉『没有帧』那一格 => 探针坏了会被读成产品结论",
     "        if bandInterval == .greatestFiniteMagnitude || fullInterval == .greatestFiniteMagnitude {\n            return .unpainted\n        }\n        let saved = fullGrab - bandGrab",
     "        let saved = fullGrab - bandGrab", "CAUGHT"),
]


def read():
    return open(SRC, encoding="utf-8").read()


def save(text):
    open(SRC, "w", encoding="utf-8").write(text)


def run():
    proc = subprocess.run(["env", "-u", "SDKROOT", "swift", "test", "--filter", FILTER],
                          cwd=os.path.join(ROOT, "ClipboardHistory"), env=ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    ran = re.search(r"Executed (\d+) test?", out)
    if not ran or int(ran.group(1)) == 0:
        return "DID-NOT-RUN", out
    if re.search(r"error: -\[", out):
        return "CAUGHT", out
    if re.search(r"with 0 failures \(0 unexpected\)", out):
        return "PASSED", out
    return "DID-NOT-RUN", out


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
        mismatch += 0 if verdict == expect else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        # 原文形状是 `error: -[ClipboardHistoryAppTests.MotionFilmstripTests testXxx] : ...`
        # —— 类名与用例名之间是**空格**，第一版按点切，于是三臂都印成"红掉的测试=-"：
        # 一个只会被读成"没红"的字段（U-441 同一族：缺席不许报成空）。
        names = sorted(set(re.findall(r"error: -\[ClipboardHistoryAppTests\.\w+\s+(\w+)", out)))
        print("%s: %s %s 红掉的测试=%s" % (name, verdict, note, ",".join(names) or "-"))
        results.append((name, expect, verdict, note, names[0] if names else ""))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R133 汇总 ===")
    for name, expect, verdict, note, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    # DID-NOT-RUN 不是通过：needle 打偏的那一臂等于这一格今天没判（U-442 顺手钉住退出码）
    return 0 if (mismatch == 0 and not_run == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
