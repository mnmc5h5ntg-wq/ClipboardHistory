#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R338 落盘之后，把 STATE 里 §8 那一格从"见下方结论行"换成**真结论行**。

生成器写那一格的时候还没跑搬运口（它在写盘之后才跑），所以那一格留了一个指不到东西的说法。
这一支把它换成现读，并且**按实记下缺的那 12 格**：`ledger_rows.py` 的 §8 表要的是各卷的汇总行
（构建 / 全量卷 / 捕获卷 / 脚本电池 / 变异表 / 曲线仪器 …），而本轮合并进去的日志只带读数族 ⇒
13 格里 12 格缺值。缺值就是缺值，不许用"看起来合理"的数补上（R92 立的规矩）。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/fix_r338_section8.py
"""
import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
STA = os.path.join(ROOT, u"AGENT_STATE.md")
ROWS = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"ledger_rows.py")
COMBINED = u"/tmp/r338_combined.log"

env = dict(os.environ)
env[u"PYTHONUTF8"] = u"1"
env[u"PYTHONDONTWRITEBYTECODE"] = u"1"
p = subprocess.run([sys.executable, ROWS, COMBINED, u"--must-include", u"HTML_ALT_SOURCE"],
                   cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = p.stdout.decode(u"utf-8", u"replace")
MUST = (re.findall(u"(?m)^READINGS_MUST_INCLUDE .*", out) or [None])[-1]
MISS = (re.findall(u"(?m)^ROWS_TOTAL=(\\d+) ROWS_MISSING=(\\d+)", out) or [None])[0]
FAM = (re.findall(u"(?m)^READINGS_FAMILIES 搬运=(\\d+) ", out) or [None])[0]
_fam_line = (re.findall(u"(?m)^READINGS_FAMILIES .*$", out) or [u""])[-1]
NFAM = str(len(re.findall(u"[A-Z][A-Z0-9_\\[]+:", _fam_line)))
if MUST is None or MISS is None or FAM is None or NFAM == u"0":
    sys.stderr.write(u"R338_S8_DIED 搬运口没给三行结论：" + out.strip()[-300:] + u"\n")
    sys.exit(1)
if u"缺=0" not in MUST:
    sys.stderr.write(u"R338_S8_DIED 本轮新族没被搬进 §8：" + MUST + u"\n")
    sys.exit(1)
TOTAL, MISSING = MISS

NEW = (u"§8 搬运：本轮新读数族 `HTML_ALT_SOURCE` 在它被打印的同一笔里接进名单 —— 现读 `%s`、"
       u"`ROWS_TOTAL=%s ROWS_MISSING=%s`（搬运 %s 行 / %s 族）。"
       u"**缺的那 %s 格按实记**：§8 表要的是各卷的汇总行（构建 / 全量卷 / 捕获卷 / 脚本电池 / 变异表 / "
       u"曲线仪器 …），而本轮喂给搬运口的合并日志只带读数族 ⇒ 缺值就是缺值，"
       u"不许用任何「看起来合理」的数补上（R92 的规矩），也不许把这一格写成「沿用上一遍」。"
       % (MUST, TOTAL, MISSING, FAM, NFAM, MISSING))

OLD_ANCHOR = (u"§8 搬运：本轮新读数族 `HTML_ALT_SOURCE` 在它被打印的同一笔里接进名单\n"
              u"（`READINGS_MUST_INCLUDE` 见下方结论行）。")
t = io.open(STA, encoding=u"utf-8").read()
if NEW in t:
    print(u"R338_S8_ALREADY §8 那一格已经是现读结论行")
    raise SystemExit(0)
if t.count(OLD_ANCHOR) != 1:
    sys.stderr.write(u"R338_S8_DIED 锚点命中 %d 次：%s\n" % (t.count(OLD_ANCHOR), OLD_ANCHOR[:60]))
    sys.exit(1)
io.open(STA, u"w", encoding=u"utf-8").write(t.replace(OLD_ANCHOR, NEW))
print(u"R338_S8_OK %s ROWS_TOTAL=%s ROWS_MISSING=%s 搬运=%s 族=%s" % (MUST, TOTAL, MISSING, FAM, NFAM))
