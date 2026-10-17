#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R128 的变异表：按表面清账的闸门，两条"看着像判据其实恒真"的牙（M631-M632）。

本轮做的事：把 127 轮散在各轮正文里的「这一格加不加动效」变成一张数据表
（`docs/motion_surface_ledger.json`，18 行 / 162 格 / 未清账 144）+ 一把闸门
（`scripts/motion_surface_gate.py`）。闸门判的是行的形状，不判覆盖 —— 没判过的格子只数不红。
这张自检（`scripts/tests/test_motion_surface_gate.py`，9 条）是它唯一的牙所在，
所以两刀都打在"某一格判据被摘掉之后，还有没有测试会红"上。

两刀（都期望 CAUGHT）：
  M631 摘掉重格检查（`if key in seen` 改恒假）=> 同一个 (表面, 状态) 出现两行也没人报
  M632 把理由长度门限改成 -1（等于恒过）=> 三个字的理由也能算一条结论

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r128.py [M631 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
GATE = os.path.join(ROOT, "scripts/motion_surface_gate.py")
TESTS = "test_motion_surface_gate.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M633", "证据指针的形状判据改成恒过 => 「R14 说过」又能当结论用了",
     "        elif not evidence_is_checkable(evidence):", "        elif False:", "CAUGHT"),
    ("M634", "摘掉「名册扩张要付账」两格 => 加一个表面而不记账也没人报",
     '    for surface in surfaces:\n        if not any(r.get("surface") == surface for r in rows):',
     '    for surface in []:\n        if not any(r.get("surface") == surface for r in rows):', "CAUGHT"),
    ("M635", "地板从「已清账数」退回「总行数」=> not-measured 的占位行会把地板抬起来",
     "    cleared = [r for r in rows if (r.get(\"verdict\") or \"\") in cleared_verdicts]",
     "    cleared = list(rows)", "CAUGHT"),
]

def read():
    return open(GATE, encoding="utf-8").read()


def save(text):
    open(GATE, "w", encoding="utf-8").write(text)


def run():
    proc = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "scripts/tests",
                           "-p", TESTS],
                          cwd=ROOT, env=dict(ENV, PYTHONUTF8="1"),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    # 「OK」不是判据：`unittest discover` 在**一条测试都没匹配上**时也打印 `Ran 0 tests / OK`
    # （这台机器上栽过一次，见 feedback-ledger-writer-hygiene）。所以先看被计数物自己报的行数。
    ran = re.search(r"Ran (\d+) tests", out)
    if not ran or int(ran.group(1)) == 0:
        return "DID-NOT-RUN", out
    m = re.search(r"^(OK|FAILED)", out, re.M)
    if not m:
        return "DID-NOT-RUN", out
    return ("CAUGHT" if m.group(1) == "FAILED" else "PASSED"), out


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
            if line.startswith(("FAIL:", "ERROR:")):
                first = line[:150]
                break
        results.append((name, expect, verdict, note, first))
        print("%s: %s %s" % (name, verdict, note))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R128 汇总 ===")
    for name, expect, verdict, note, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
