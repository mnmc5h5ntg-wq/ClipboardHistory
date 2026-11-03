#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R566 派生格：streak 两格都由门现读派生（本轮 565 − 564 = 1），一格不手抄。

门的原话：`PRODUCT_STREAK ledger_round=565 streak=1 … as_of=last=f6c2a1d last_round=564`
⇒ 这一格读成「本轮**之前**的连读零改动轮数」（as-of、严格小于，R334 起的口径），
  R565 那一笔产品提交（label 564）就是分界 ⇒ 本轮是 1，下一轮若再无产品文件就是 2。
"""
import io
import re
import sys

P = re.compile(u'产品面连续零改动轮数[ \\t]*=[ \\t]*\\*\\*(\\d+)\\*\\*')

t = io.open('AGENT_FINAL_REPORT.md', encoding='utf-8').read()
hits = list(P.finditer(t))
if len(hits) != 1:
    sys.stderr.write('ANCHOR_BAD report 命中=%d\n' % len(hits))
    sys.exit(1)
old = hits[0].group(0)
if old.endswith('**1**'):
    sys.stderr.write('ALREADY_PATCHED report\n')
    sys.exit(1)
t = t.replace(old, u'产品面连续零改动轮数 = **1**（`python3 scripts/product_streak.py` 现读 '
                   u'`ledger_round=565 streak=1 … as_of=last=f6c2a1d last_round=564`；as-of 口径 ⇒ 读成「R566 之前的连读轮数」，'
                   u'R566 产品 0 文件 ⇒ 下一轮是 2）', 1)
io.open('AGENT_FINAL_REPORT.md', 'w', encoding='utf-8').write(t)

s = io.open('AGENT_STATE.md', encoding='utf-8').read()
old_state = ('streak 台账落盘后由 `python3 scripts/product_streak.py --check` 现读。')
new_state = ('产品面连续零改动 **1** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ '
             '`PRODUCT_STREAK ledger_round=565 streak=1 sections=541 as_of=last=f6c2a1d last_round=564 newest=f6c2a1d newest_round=564`；'
             'as-of 口径：第 N 轮的格 = N −（标签 < N 的最后一笔产品提交的标签）= 565 − 564 ⇒ 说的是「本轮**之前**的连读轮数」，'
             '本轮产品 0 文件 ⇒ 下一轮会是 2；复核 `PRODUCT_STREAK_LEDGER_OK streak=1`）。')
if s.count(old_state) != 1:
    sys.stderr.write('ANCHOR_BAD state 命中=%d\n' % s.count(old_state))
    sys.exit(1)
s = s.replace(old_state, new_state, 1)
s = s.replace('电池 **待台账落盘后现读（本笔之后跑）**',
              '电池 **待本笔之后现读**（顺序：台账 → 派生格 → 电池，电池只抄它自己打印的 Ran/OK/FAILED）')
io.open('AGENT_STATE.md', 'w', encoding='utf-8').write(s)
print('DERIVED_CELLS_WRITTEN')
