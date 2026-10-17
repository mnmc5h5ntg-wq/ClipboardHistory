#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R137 的变异表：新加的"生成器与已提交表对账"那两支的牙（M652-M653）。

  M652 让生成器写出一份**与仓库不同**的表（rows 被清空）=> 对账那两支必须红
       （这正是 U-450 的形状：生成器坏了 / 数据漂了，而闸门拿着旧 JSON 报 ok）
  M653 把 BACKLOG 里 166 那个条目号改掉 => 表里对 `BACKLOG 166` 的引用悬空，守卫必须红
       （U-452 那一族的自动化版本）

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/mutate_r137.py [M652 ...]
"""
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
GEN = os.path.join(ROOT, ".scratch/motion-audit-2/make_surface_ledger.py")
DOC = os.path.join(ROOT, "AGENT_BACKLOG.md")
TESTS = "test_ledger_generator_output.py"
ENV = {k: v for k, v in os.environ.items() if k != "SDKROOT"}

ARMS = [
    ("M652", GEN, '    json.dumps(data, ensure_ascii=False, indent=2) + "\\n")',
     '    json.dumps(dict(data, rows=[]), ensure_ascii=False, indent=2) + "\\n")', "CAUGHT"),
    ("M653", DOC, "**166.", "**166Z.", "CAUGHT"),
]


def read(path):
    return open(path, encoding="utf-8").read()


def save(path, text):
    open(path, "w", encoding="utf-8").write(text)


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
        hits = originals[path].count(needle)
        if hits != 1:
            print("%s: DID-NOT-RUN needle 命中 [%d]" % (name, hits))
            not_run += 1
            results.append((name, expect, "DID-NOT-RUN", path, ""))
            continue
        save(path, originals[path].replace(needle, replacement, 1))
        verdict, out = run()
        save(path, originals[path])
        tally[verdict] = tally.get(verdict, 0) + 1
        mismatch += 0 if verdict == expect else 1
        not_run += 1 if verdict == "DID-NOT-RUN" else 0
        names = sorted({l.split()[1] for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))})
        print("%s: %s 红掉的测试=%s" % (name, verdict, ",".join(names) or "-"))
        results.append((name, expect, verdict, path, names[0] if names else ""))
    restored = "yes" if all(read(p) == originals[p] for p in originals) else "仍不干净"
    print("\n=== R137 汇总 ===")
    for name, expect, verdict, path, detail in results:
        print("  %s exp=%-8s got=%-11s %s %s" % (name, expect, verdict, "OK" if expect == verdict else "!!", detail))
    print("RESTORE_CLEAN=%s" % restored)
    print("MUTATE_TABLE n=%d caught=%d mismatch=%d not_run=%d"
          % (len(results), tally.get("CAUGHT", 0), mismatch, not_run))
    return 0 if (mismatch == 0 and not_run == 0 and restored == "yes" and results) else 1


if __name__ == "__main__":
    sys.exit(main())
