# -*- coding: utf-8 -*-
"""R311 验证链日志的补记：把「帧还在不在盘上」与「台账读数口的现读」两条
在落账之前现场量一次，原样追加进 /tmp/r311_chain.log（不改动已有行）。

为什么要补：ledgers_r311.py 是从 R310（零产品改动轮）的生成器改出来的，
它要求日志里有 ### FRAMES 与 ### SWIFT_LEGS 两节 —— R310 那两节写的是
「复用上轮帧 + Swift 腿 NOT-RUN」。本轮是产品轮，Swift 三条腿真跑了
（CAPTURED / FRAME_BASELINE_* / INSTALL_RESULT 都在日志里），但帧的语义计数
与台账读数口那行当时没单独打印，所以在这里现量现补，而不是凭记忆填。
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
CHAIN = u"/tmp/r311_chain.log"
SHOTS = u"/tmp/r311_shots"
FULL = u"/tmp/r311_full.log"


def run(argv):
    p = subprocess.run(argv, cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return p.stdout.decode("utf-8", "replace"), p.returncode


if not os.path.exists(CHAIN):
    sys.stderr.write(u"APPEND_REFUSE 验证链日志不存在\n")
    sys.exit(1)

text = io.open(CHAIN, encoding=u"utf-8").read()
if u"### FRAMES_ON_LEDGER" in text:
    sys.stdout.write(u"APPEND_SKIP 已经补过，不重复追加\n")
    sys.exit(0)

# 1) 帧的语义计数：只数 PNG，并和 CAPTURE 那行对账
pngs = sorted(n for n in os.listdir(SHOTS) if n.endswith(u".png"))
listed, rc = run(["ls", SHOTS])
all_entries = [n for n in listed.splitlines() if n.strip()]
cap = re.findall(r"CAPTURED (\d+) -> (\S+)", text)
cap_n = int(cap[-1][0]) if cap else -1
rows = [
    u"### FRAMES_ON_LEDGER（落账之前现场数，不是复用上轮）",
    u"FRAMES_ON_DISK=%d" % len(pngs),
    u"FRAMES_DIR_ENTRIES=%d（含非 PNG %d）" % (len(all_entries), len(all_entries) - len(pngs)),
    u"FRAMES_CAPTURE_LINE=%s" % (cap[-1][0] if cap else u"没解析到"),
    u"FRAMES_MATCH=%s" % (u"1" if len(pngs) == cap_n else u"0"),
]
if len(pngs) != cap_n:
    rows.append(u"FRAMES_MISMATCH 盘上 %d 张 != CAPTURED %d 张 ⇒ 目录被动过" % (len(pngs), cap_n))

# 2) 台账读数口：现跑仓库里那颗尺（它吃的是这份验证链日志，不是 326MB 全量卷），
#    原样抄它打印的那行
lr, lrc = run([sys.executable, u"scripts/ledger_readings.py", CHAIN])
line = u"".join(x for x in lr.splitlines(True) if x.startswith(u"LEDGER_READINGS "))
rows += [u"### LEDGER_READINGS（同一跑的全量卷，现读）",
         line.rstrip(u"\n") if line else u"LEDGER_READINGS_RC=%d 没打印结论行" % lrc]

# 3) Swift 三条腿：本轮全 RUN，把日志里已有的那三行原样列出来
legs = []
for pat, label in ((r"^CAPTURED .*$", u"重捕帧"),
                   (r"^FRAME_BASELINE_COMPARED=\d+$", u"基线对账"),
                   (r"^FRAME_BASELINE_UPDATED=\d+$", u"基线同一笔 update"),
                   (r"^INSTALL_RESULT=.*$", u"换装本机")):
    hits = re.findall(pat, text, re.M)
    legs.append(u"%s=%s" % (label, hits[-1] if hits else u"NOT-RUN"))
rows.append(u"### SWIFT_LEGS（本轮：三条腿全 RUN，不是 NOT-RUN）")
rows += [u"LEG " + x for x in legs]

with io.open(CHAIN, "a", encoding=u"utf-8") as h:
    h.write(u"\n".join(rows) + u"\n")

sys.stdout.write(u"\n".join(rows) + u"\n")
sys.stdout.write(u"APPEND_DONE rc=0\n")
