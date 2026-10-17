#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R135 的变异表：那两格「不归它」挂在 API 默认值上，所以给守卫配两刀（M650-M651）。

  M650 把 `.menuBarExtraStyle(.menu)` 改成 `.window` => 推荐面板不再是真 NSMenu，守卫必须红
  M651 把那一行整条删掉 => 样式回到默认值本身，而"默认值不是契约"，守卫同样必须红
       （这一刀同时证明那条断言不是"读到 .menu 才算"的写法偏窄：删掉也要响）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r135.py [M650 ...]
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
SRC = os.path.join(ROOT, "ClipboardHistory/Sources/ClipboardHistoryApp/App.swift")
FILTER = "DocumentationAnchorTests/testMenuBarExtraStyleStillSaysMenuWhileTheLedgerSaysNotApplicable$"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M650", "样式改成 .window => 那两格『不执行』的前提没了，守卫要响",
     ".menuBarExtraStyle(.menu)", ".menuBarExtraStyle(.window)", "CAUGHT"),
    ("M651", "整行删掉 => 回到默认值，而默认值不是契约，守卫同样要响",
     "            .menuBarExtraStyle(.menu)\n", "", "CAUGHT"),
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
    ran = re.search(r"Executed (\d+) test", out)
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
        names = sorted(set(re.findall(r"error: -\[ClipboardHistoryAppTests\.\w+\s+(\w+)", out)))
        print("%s: %s %s 红掉的测试=%s" % (name, verdict, note, ",".join(names) or "-"))
        results.append((name, expect, verdict, note, names[0] if names else ""))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R135 汇总 ===")
    for name, expect, verdict, note, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and not_run == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
