#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R132 的变异表：真机色度那把尺的两个出口（M645-M646）。

本轮做的事：给 BACKLOG 139（"设置里的勾选框在帧里色度为 0"）装了一条**真机**判据
`scripts/real_screen_control_chroma.py` —— 同一张帧里拿侧栏选中那一行的强调蓝当参照，
问内容区的 `b-r` 落在哪一档。第一跑就判到 `accent_in_content`（比值 0.979、强蓝 2463 颗、
包围盒正好是勾选框那一列），139 于是结案成**离屏通道**那一族。

两刀都打在这把尺自己的两个出口上（都期望 CAUGHT）：
  M645 摘掉「目标行本来就选中着」那一格 => 一次成功的测量会被读成"尺坏了"（本轮真的这样翻过一次，U-438）
  M646 让包围盒的恒等式恒真 => `x=177..98` 这种倒过来的区间又能被当成结论印出去（U-439）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r132.py [M645 ...]
退出码：0 = 每一臂都拿到自己的期望，且还原干净。
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
SRC = os.path.join(ROOT, "scripts/real_screen_control_chroma.py")
TESTS = "test_real_screen_chroma_verdict.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M645", "摘掉「本来就选中」那一格 => 已经停在目标行时会被判成 unmeasured（假阴性）",
     '    if abs(before - target) <= tol:\n        return "already_selected"',
     '    if False:\n        return "already_selected"', "CAUGHT"),
    ("M646", "包围盒恒等式改成恒真 => min/max 印反也没人报（读数形状像结论，对象是错的）",
     "    return box[0] <= box[2] and box[1] <= box[3]",
     "    return True", "CAUGHT"),
]


def read():
    return open(SRC, encoding="utf-8").read()


def save(text):
    open(SRC, "w", encoding="utf-8").write(text)


def run():
    proc = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "scripts/tests",
                           "-p", TESTS],
                          cwd=ROOT, env=dict(ENV, PYTHONUTF8="1"),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
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
        mismatch += 0 if verdict == expect else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        names = sorted({l.split()[1] for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))})
        print("%s: %s %s 红掉的测试=%s" % (name, verdict, note, ",".join(names) or "-"))
        results.append((name, expect, verdict, note, names[0] if names else ""))
    restored = "yes" if read() == original else "仍不干净"
    print("\n=== R132 汇总 ===")
    for name, expect, verdict, note, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s %s"
              % (name, expect, verdict, "OK" if expect == verdict else "!!", note, detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
