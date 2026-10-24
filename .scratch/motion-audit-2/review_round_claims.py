#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""回顾用尺第二支：**同一轮的每一笔提交**里「产品 K 文件」那一句是不是同一个数。

为什么要有它（R336 回顾时现读撞到的）：一轮通常有两笔以上（代码半 / 代码半补 / 账半 / 追记），
而每一笔的标题都带着"第 N 轮 / Round M · 产品 K 文件"这半句。这半句在**一轮内部**说的必须是
同一件事：这一轮的产品面改了几个文件。它一旦在两笔里给出两个数，读 git log 的人就不知道
哪一句作数 —— 而 `scripts/product_streak.py` 只从"代码半"那一笔取数，所以台账内部对得上，
标题之间却可以互相打脸（现读：R334 代码半写 2、R334 账半写 0；R335 两笔都写 7）。

用法：`python3 .scratch/motion-audit-2/review_round_claims.py [N]`
退出码：0=每一轮内部只有一个数；1=有轮次内部不一致（打印轮号与两笔）。
**它不判**"这一轮的数与 git 派生的是否相同" —— 那一半是 review_commit_claims.py 的活。
"""
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 120


def sh(cmd):
    return subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode(u"utf-8", u"replace")


log = sh([u"git", u"log", u"-n", str(N), u"--format=%H%x09%s"])
by_round = {}
for line in log.splitlines():
    if u"\t" not in line:
        continue
    sha, subject = line.split(u"\t", 1)
    m = re.match(u"R(\\d+)(?: (\\S+?))?（.*?产品 (\\d+) 文件", subject)
    if not m:
        continue
    rnd, kind, claimed = m.group(1), (m.group(2) or u"其他"), m.group(3)
    by_round.setdefault(rnd, []).append((sha[:7], kind, int(claimed)))

bad = []
for rnd, rows in sorted(by_round.items(), key=lambda kv: -int(kv[0])):
    nums = set(r[2] for r in rows)
    if len(nums) > 1:
        bad.append((rnd, rows))

print(u"ROUND_CLAIM_REVIEW 扫了=%d 笔 / %d 轮 内部不一致=%d"
      % (len(log.splitlines()), len(by_round), len(bad)))
for rnd, rows in bad:
    print(u"  R%s: %s" % (rnd, u" | ".join(u"%s %s=%d" % r for r in rows)))
sys.exit(1 if bad else 0)
