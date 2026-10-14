#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R46 变异对照：新地板闸门的每一条规则，各关掉一次都该被自己的判据抓回来。

为什么这一族的变异对照比平时更要紧：这道闸门**本身就是判据的判据**。
它红不红决定 CI 上有没有人知道"今天少验了一臂"，所以每条规则都必须被证明
"关掉它，就有一格用例过不掉"。规则在、用例绿、但用例其实抓不到规则的失效 ——
那是 R34 的 U-56 那一族（守卫看着在，其实不咬）。

  M216 关掉 REASONLESS（not-run 不给理由也放行）      ⇒ "没理由的 not-run" 那格该红
  M217 地板退回旧版的写死 `judged<2`                  ⇒ "must_judge 数才是地板" 那格该红
  M218 NO_RESOLVE 改回 exit 0（旧版那张免检牌）        ⇒ "跑完却没有结论行" 那格该红
  M219 关掉 MISSING_KEY（少一臂的键不管）              ⇒ 少键那格该红
  M220 关掉 BAD_REASON（理由不查登记）                 ⇒ 换理由那格该红
  M221 解析器改成取**第一条** resolve 行               ⇒ "取最后一条" 那格该红
  M222 关掉 UNREGISTERED（清单外的臂也放行）           ⇒ 新盲区那格该红

needle 一律从 --measure 那一遍的失败消息原文里抄。
"""
import os
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
GATE = os.path.join(ROOT, "scripts/motion_floor_gate.py")

REASONLESS = '        if not seen:\n'
FLOOR = '    if facts["judged"] < floor:\n'
NO_RESOLVE = '而旧版这一步在这里 exit 0（免检牌）", True))'
MISSING = '    if missing:\n'
BAD_REASON = '        if unexpected:\n'
FIRST_MATCH = '            resolve = match\n'
UNREGISTERED = '        if spec is None:\n'

MUTATIONS = [
    ("M216", "REASONLESS 关掉", GATE, REASONLESS, "        if False:  # MUTANT\n",
     ["drift_without_reason: 结论行缺失 ['MOTION_FLOOR_REASONLESS']"]),
    ("M217", "地板退回写死的 2", GATE, FLOOR, '    if facts["judged"] < 2:  # MUTANT\n',
     ["under_covered: 结论行缺失 ['MOTION_FLOOR_UNDERCOVERED']", 'testFloorIsTheMustJudgeCountNotTwo']),
    ("M218", "没有结论行改成放行", GATE, NO_RESOLVE, NO_RESOLVE.replace("True))", "False))  # MUTANT"),
     ['no_resolve_line: 期望退出码 1，实际 0', "'MOTION_FLOOR_NO_RESOLVE' not found in"]),
    ("M219", "MISSING_KEY 关掉", GATE, MISSING, "    if False:  # MUTANT\n",
     ["'MOTION_FLOOR_MISSING_KEY' not found in"]),
    ("M220", "BAD_REASON 关掉", GATE, BAD_REASON, "        if False:  # MUTANT\n",
     ["'MOTION_FLOOR_BAD_REASON' not found in"]),
    ("M221", "解析器取第一条", GATE, FIRST_MATCH,
     "            resolve = match  # MUTANT\n            break\n",
     ['AssertionError: 9 != 3']),
    ("M222", "UNREGISTERED 关掉", GATE, UNREGISTERED, "        if False:  # MUTANT\n",
     ['ERROR: testUnregisteredArmIsRed']),
]


def failure_messages(out):
    return [line for line in out.splitlines()
            if line.startswith("FAIL:") or line.startswith("ERROR:") or "AssertionError" in line]


def run():
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"],
                          cwd=ROOT, capture_output=True, text=True, timeout=1200)
    out = proc.stdout + proc.stderr
    if "Ran " not in out:
        return "DID-NOT-RUN", out
    if "FAILED" in out:
        return "CAUGHT", out
    if "OK" in out:
        return "ESCAPED", out
    return "BROKEN-MUTATION", out


def apply(path, old, new):
    text = open(path, encoding="utf-8").read()
    n = text.count(old)
    if n != 1:
        raise SystemExit("注入中止：%s 出现 %d 次，不是 1 次 —— 电池与代码脱节" % (old.strip()[:60], n))
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
    code, out = run()
    if code != "ESCAPED":
        raise SystemExit("预检失败：" + code + "\n" + out[-2000:])
    print("预检 OK（未变异时脚本自测全绿）")
    results = []
    for mid, desc, path, old, new, needles in MUTATIONS:
        if wanted and mid not in wanted:
            continue
        original = apply(path, old, new)
        code, out = run()
        messages = failure_messages(out)
        hit = [needle for needle in needles if any(needle in message for message in messages)]
        right = bool(needles) and len(hit) == len(needles) and "待 --measure" not in needles
        ok = restore(path, original)
        failed = [line.split()[-1] for line in out.splitlines() if line.startswith("FAIL:")]
        results.append((mid, code, "MEASURE" if measure else ("yes" if right else "NO"),
                        "yes" if ok else "NO", ",".join(failed)))
        print("\n%s %s ⇒ %s 红得对=%s 红在 %s" % (mid, desc, code, "n/a" if measure else right, failed))
        if measure or not right or code != "CAUGHT":
            for line in messages[:6]:
                print("   MSG| " + line.strip()[:300])
    print("\n==== 汇总 ====")
    for row in results:
        print("  " + " | ".join(str(x) for x in row))
    bad = [r for r in results if r[1] != "CAUGHT"]
    wrong = [r for r in results if r[2] not in ("yes", "MEASURE")]
    dirty = [r for r in results if r[3] != "yes"]
    print("未被抓到=%d  红得不对=%d  还原不干净=%d" % (len(bad), len(wrong), len(dirty)))
    if dirty:
        raise SystemExit("RESTORE_CLEAN=no")
    if bad or wrong:
        raise SystemExit("MUTATION_UNCAUGHT=%d" % (len(bad) + len(wrong)))


main()
