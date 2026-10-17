#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 的变异表：新加的"一轮必须同时写进三本账"那道守卫的牙（M655-M656）。

  M655 把 CHANGELOG 里**本轮**那条标题删掉 => 守卫必须红（这正是 R138 真实发生过的形状：
       那一轮第一次提交时 CHANGELOG 整条没落上，其余四处落了盘。R143 起标题按 STATE 现取，
       写死某一轮的刀会随窗口滑动过期）
  M656 把窗口 LOOKBACK 从 3 改成 1 => "只查本轮"时半批已写会漏，那条名册下限自检必须响

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r139.py [M655 ...]
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
GUARD = os.path.join(ROOT, "scripts/tests/test_round_batch_consistency.py")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
TESTS = "test_round_batch_consistency.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

def newest_round_heading(text):
    """M655 的 needle：本轮（STATE 自报的 R 号）在 CHANGELOG 里的那一行**标题**。

    为什么不再写死某一轮（R143 修的第二处死刀）：守卫查的是"最近 LOOKBACK 轮"，窗口会往前滑。
    写死 R138 的标题，等窗口滑过 R138 之后，删掉它守卫当然不红 ⇒ M655 报 PASSED，
    一张表的牙就这样随时间烂掉而没人看见（"旧代码上得到的 CAUGHT 不能替新代码作证"的兄弟：
    **刀也会过期**）。现在按 STATE 的本轮号现取标题行，命中数不等于 1 就直接退出 —— 那是没跑，不是通过。
    """
    state = read(STATE)
    m = re.search(u"最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮", state)
    if not m:
        raise SystemExit("M655 落不了刀：读不到 AGENT_STATE 的本轮 R 号（这不是通过，是没跑）")
    hits = [line + u"\n" for line in text.split(u"\n")
            if line.startswith(u"### ") and (u"（R%s / " % m.group(1)) in line]
    if len(hits) != 1:
        raise SystemExit("M655 落不了刀：本轮 R%s 在 CHANGELOG 的标题命中 %d 行（要恰好 1 行）"
                         % (m.group(1), len(hits)))
    return hits[0]


ARMS = [
    # 第一版的替换串是 `### （R138 的标题被删掉了）` —— 它**自己带着 R138**，
    # 于是守卫照样绿，刀等于没下（U-459：删除型变异的替换串不许留着被测 token，
    # 这条规矩早就记过，这次是它在我眼皮底下第二次生效）。改成整行删掉。
    ("M655", CHANGELOG, newest_round_heading,
     u"", "CAUGHT"),
    # R143 修死刀：这一把的 needle 原来就是裸的 `LOOKBACK = 3`，而 U-462 那次补记把**同一串字**
    # 写进了守卫自己的文档注释（磁盘上 `LOOKBACK = 3`），于是 count==2 ⇒ DID-NOT-RUN ⇒
    # R139 这张表今天整张跑不动，而台账里那句"两臂 CAUGHT"早就不可复现了。
    # 锚点改成整行（前后带换行）：注释里那串两边是反引号，不会被当成声明行命中（R99/R100 那一族）。
    ("M656", GUARD, "\nLOOKBACK = 3\n", "\nLOOKBACK = 1\n", "CAUGHT"),
]


def read(p):
    return open(p, encoding="utf-8").read()


def save(p, text):
    open(p, "w", encoding="utf-8").write(text)


def run():
    proc = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "scripts/tests", "-p", TESTS],
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
    originals = {p: read(p) for _, p, _, _, _ in ARMS}
    results, tally, mismatch, not_run = [], {}, 0, 0
    for name, path, needle, replacement, expect in ARMS:
        if wanted and name not in wanted:
            continue
        if callable(needle):
            needle = needle(originals[path])
        hits = originals[path].count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]" % (name, hits))
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", "", ""))
            continue
        save(path, originals[path].replace(needle, replacement, 1))
        verdict, out = run()
        save(path, originals[path])
        tally[verdict] = tally.get(verdict, 0) + 1
        mismatch += 0 if verdict == expect else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        names = sorted({l.split()[1] for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))})
        print("%s: %s 红掉的测试=%s" % (name, verdict, ",".join(names) or "-"))
        results.append((name, expect, verdict, "", names[0] if names else ""))
    restored = "yes" if all(read(p) == originals[p] for p in originals) else "仍不干净"
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and not_run == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
