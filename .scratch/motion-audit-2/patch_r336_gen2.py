#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 生成器的第二支补丁：把第七条 U（名册那三朵红）接到 ITERATION / STATE / CHANGELOG 三本上。

规矩与第一支一样：**只在正文末尾追加**，参数只往元组末尾追加。
往中间插会让占位符与参数按位置错配 —— 那正是 R334/R335 各浪费一整步的那一种坏法。
写完立刻用 `format_arity_check.py` 数一遍占位符，不靠肉眼。
"""
import ast
import io
import sys

P = u"/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/ledgers_r336.py"
s = io.open(P, encoding=u"utf-8").read()
EDITS = []


def rep(old, new, tag):
    global s
    n = s.count(old)
    if n != 1:
        sys.stderr.write(u"锚点命中 %d 次（要 1 次）[%s]：%s\n" % (n, tag, old[:70]))
        sys.exit(1)
    s = s.replace(old, new)
    EDITS.append(tag)


# 1. ITERATION：一句不占参数（数字住在 U-1134，两处各摆一遍就会漂）
rep(u'可读性那两把尺照旧签（暗 %s:1 / 亮 %s:1，反侧两档 0 颗）。\n\n七维度自评：',
    u'可读性那两把尺照旧签（暗 %s:1 / 亮 %s:1，反侧两档 0 颗）。\n\n'
    u'还有一件**我自己的**事值得写下来：新增 `MD_RENDER_COST` 那一行时没同时登记\n'
    u'「按文件按标记」那份名册，于是全量卷第一次跑就红在三格（数与出处都在 U-1134）。这一格问的\n'
    u'从来不是"读数走哪条通道"，而是"这些读数有没有名字" —— 我把它当成捕获卷那份名册而漏了它，\n'
    u'红得完全正确。三格同一笔改到现读，而不是分三笔（分笔会让中间那一跑是红的，谁都不能引用）。\n'
    u'\n七维度自评：',
    u"ITER_SENTENCE")

# 2. STATE：正文末尾 + 参数末尾（4 个占位符对 4 个参数）
rep(u'Python 的 `re` 只是我自己在本机的猜测，**不算读数**。\n\n""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N,',
    u'Python 的 `re` 只是我自己在本机的猜测，**不算读数**。\n\n'
    u'本轮的自伤（写成出处，不写成缺陷）：新增读数 `MD_RENDER_COST` 时没同时登记那张\n'
    u'「按文件按标记」的名册，全量卷第一次跑就红三朵 —— 现读 量到的名单=%s 对 登记的=%s、\n'
    u'本文件行数 %s（量/登记）、全表总数 %s（量/登记）；同一笔把三格改到现读，\n'
    u'新日志里这一朵红消失（`grep -c` 现读 0）⇒ 登记生效（U-%d）。\n\n'
    u'""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N,',
    u"STATE_TAIL")

rep(u'       ROWS_LINE, NEW_READINGS, ROUND + 1)',
    u'       ROWS_LINE, NEW_READINGS, ROUND + 1,\n'
    u'       ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL, UG)',
    u"STATE_ARGS")

# 3. CHANGELOG：正文末尾 + 参数末尾（5 个占位符对 5 个参数）
rep(u'- 帧基线同一笔更新：`CHANGED=4`（只有 HTML 夹具那两张 × 两档），`MISSING=0 ADDED=0`。\n\n""" % (ROUND, UA, UMAX, PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK)',
    u'- 帧基线同一笔更新：`CHANGED=4`（只有 HTML 夹具那两张 × 两档），`MISSING=0 ADDED=0`。\n'
    u'- 自曝一条工具面（U-%d）：新增 `MD_RENDER_COST` 而没登记「按文件按标记」那份名册 ⇒ 全量卷红三朵\n'
    u'  （量到的名单=%s 对 登记的=%s、本文件行数 %s、全表总数 %s），同一笔改到现读并把"红消失"钉成现读。\n\n'
    u'""" % (ROUND, UA, UMAX, PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK,\n'
    u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL)',
    u"CHG_TAIL")

io.open(P, u"w", encoding=u"utf-8").write(s)
ast.parse(s)
print(u"R336_GEN_PATCH2 edits=%d %s" % (len(EDITS), u",".join(EDITS)))
