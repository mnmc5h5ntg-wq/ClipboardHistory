#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""拿**真日志**验那三根正则，而不是等生成器跑起来才发现读不到。

为什么单独一支：生成器在解析段之前要先跑完四腿（十几分钟），而正则错一个引号就会
die 在几十秒之后 —— 那一遍四腿就白跑了。这里只做一件事：grep 出那三行，逐根正则配对。
"""
import io
import re
import subprocess
import sys

LOG = u"/tmp/r336_rv/full.log"
GEN = u"/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/ledgers_r336.py"

src = io.open(GEN, encoding=u"utf-8").read()
pats = {}
for name in (u"RE_ROSTER_NAMES", u"RE_ROSTER_ROWS", u"RE_ROSTER_TOTAL"):
    m = re.search(u"(?m)^" + name + u" = u'(.*)'$", src)
    if not m:
        sys.exit(u"生成器里读不到 " + name)
    pats[name] = m.group(1)

out = subprocess.run([u"grep", u"-a", u"-m", u"3",
                      u"testProbeFilePrintReadingsAreARosterNotACount] : XCTAssertEqual failed",
                      LOG], stdout=subprocess.PIPE).stdout.decode(u"utf-8", u"replace")
lines = [l for l in out.split(u"\n") if l.strip()]
print(u"GREP_LINES=%d" % len(lines))
for name, pat in sorted(pats.items()):
    m = re.search(pat, out)
    print(u"%s matched=%s groups=%s" % (name, bool(m), (m.groups() if m else None)))
    if not m:
        sys.exit(u"正则读不到真日志：" + name)
BS_N = src.count(u'old_roster.count(BS_N)')
print(u"BS_N_USES=%d 三行齐全=%s" % (BS_N, len(lines) == 3))
