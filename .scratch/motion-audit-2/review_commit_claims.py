#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""回顾用的一支尺：最近 N 笔提交里，标题声称的「产品 K 文件」与 git 实际改的 Sources 文件数对不对。

为什么现在要它：用户要的是"慢慢地把这么长的工作回顾一遍"，而台账与提交里最容易被引用、
又最容易过期的一类数就是"产品 N 文件"。它有两条独立的来源（标题是我手写的那一句、
`/Sources/` 那一列是 git 派的），所以对得上不代表别处也对得上 —— 但只要对不上，
就是"下一轮引用了这个数的人拿到的是假数"。电池里那条 `product_streak.py --check` 只查
"连读的那一格"，不逐笔查标题，所以这一格要现场量。

用法：`python3 .scratch/motion-audit-2/review_commit_claims.py [N]`
"""
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 24


def sh(cmd):
    return subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode(u"utf-8", u"replace")


log = sh([u"git", u"log", u"-n", str(N), u"--format=%H%x09%s"])
rows = []
mismatch = 0
for line in log.splitlines():
    if u"\t" not in line:
        continue
    sha, subject = line.split(u"\t", 1)
    m = re.search(u"产品 (\\d+) 文件", subject)
    if not m:
        continue
    claimed = int(m.group(1))
    names = sh([u"git", u"show", u"--name-only", u"--format=", sha]).splitlines()
    actual = len(set(l for l in names if u"/Sources/" in l))
    kind = u"代码半补" if u"代码半补" in subject else (
        u"代码半" if u"代码半" in subject else u"其他")
    ok = claimed == actual
    if not ok:
        mismatch += 1
    rows.append((sha[:7], kind, claimed, actual, u"OK" if ok else u"MISMATCH",
                 subject[:46]))

print(u"COMMIT_CLAIM_REVIEW 笔数=%d 带产品格=%d 不符=%d" % (len(log.splitlines()), len(rows), mismatch))
for r in rows:
    print(u"%s %-8s 标题=%d git=%d %-8s %s" % r)
sys.exit(1 if mismatch else 0)
