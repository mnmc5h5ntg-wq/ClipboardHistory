#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R129 的变异表：一条规则一份实现，名册成员不许被别处静默抽走（M636-M638）。

本轮做的事有两件，都是"闸门自己的形状"：
  ① 修掉推出去的那朵红：`test_not_measured_does_not_count_as_cleared` 里的占位行写的是
     `禁用` 这一状态，而我在 R128 把夹具名册收窄成 `["悬停", "聚焦"]`（U-427）之后，
     这条测试的红**换了对象** —— 不再是"占位行抬地板"，而是 UNKNOWN_CELL。断言仍然失败，
     失败的原因整条换掉，而两种红看起来一样（U-429）。
  ② 摘掉 `FLOOR_LIES` 的第二份实现（U-430）：同一条规则查两遍不是"更保险"，
     是变异任何一遍都被另一遍掩盖，且读数会印两遍。

三刀（都期望 CAUGHT）：
  M636 把 `floor > len(rows)` 改成 `floor >= len(rows)` => 名字册与地板相等这一合法形状被误判
  M637 把 `FLOOR_LIES` 那一格重新复制一遍 => 同一条规则两份实现（"次数"判据要能点名）
  M638 摘掉「状态不在名册里」那一格 => 名册成员被抽走之后，占位行的红会悄悄换成别的形状

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r129.py [M636 ...]
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

FLOOR_BLOCK = (
    '    elif floor > len(rows):\n'
    '        problems.append(("FLOOR_LIES",\n'
    '                         "floor_cleared=%d 大于实际行数 %d ⇒ 地板写成了愿望" % (floor, len(rows))))'
)
STATE_BLOCK = (
    '        if state not in states:\n'
    '            problems.append(("UNKNOWN_CELL", "%s：状态不在名册里" % where))'
)

ARMS = [
    ("M636", "地板判据从 > 改成 >= => 合法表被误判，而 FLOOR_LIES 从此包含「等于」这种没有愿望的写法",
     "    elif floor > len(rows):", "    elif floor >= len(rows):", "CAUGHT"),
    ("M637", "把 FLOOR_LIES 那一格再复制一遍 => 同一条规则两份实现，读数印两遍、变异被掩盖",
     FLOOR_BLOCK, FLOOR_BLOCK + "\n" + FLOOR_BLOCK.replace("    elif", "    if"), "CAUGHT"),
    ("M638", "摘掉「状态不在名册里」那一格 => 名册收窄之后，占位行的红不再点名（U-429 的形状）",
     STATE_BLOCK, '        if False:\n'
                  '            problems.append(("UNKNOWN_CELL", "%s：状态不在名册里" % where))', "CAUGHT"),
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
    # （这台机器上栽过一次，见 U-423）。所以先看被计数物自己报的行数。
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
        names = []
        for line in out.splitlines():
            if line.startswith(("FAIL:", "ERROR:")):
                if not first:
                    first = line[:150]
                names.append(line.split()[1])
        print("%s: %s %s 红掉的测试=%s" % (name, verdict, note, ",".join(sorted(set(names))) or "-"))
        results.append((name, expect, verdict, note, first))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R129 汇总 ===")
    for name, expect, verdict, note, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
