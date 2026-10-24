#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 生成器的第四支补丁（下半）：规则 ④ 与"期望值先写错一次"接进七本账。

写法：正文只在**末尾**追加，参数只往元组**末尾**追加；ITERATION 那一段刻意不带数
（占位符按位置配对，往中间插就会错配 —— R334/R335 各浪费一整步的成因），数住在 U-1135 与 STATE。
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


def L(*lines):
    return u"\n".join(lines)


# ── UI_AUDIT：两条新 U ───────────────────────────────────────────────────────
old_tail = L(u'修完的新日志里这一朵红必须消失（脚本现读 `grep -c`），"我修了"才有出处。',
             u'', u'"""')
new_tail = L(u'修完的新日志里这一朵红必须消失（脚本现读 `grep -c`），"我修了"才有出处。',
             u'- **U-%d：说明留下了之后还要**自成一段** —— 看图腿量出上半场的修法只做了一半** ——',
             u'  同一把行距尺跑两遍（修之前的帧 / 修之后的帧，两档各一张）：紧挨着的两行从',
             u'  暗档 %s 处、亮档 %s 处（修之前暗档那串间距 %s pt）降到 %s 处与 %s 处。',
             u'  捕获卷那两把尺现读：`HTML_ALT_PARA dark 带=%s 紧挨=%s 行内距=%s 段距=%s`、',
             u'  `HTML_ALT_PARA light 带=%s 紧挨=%s 行内距=%s 段距=%s`。',
             u'  裸的行内文字会被并进**上一个块的行节奏**（20.0 对 31.5），所以规则 ④ 是：',
             u'  独占一行的图 ⇒ alt 包成 `<p>`；句中的图 ⇒ 就地替换（结构那一半现读',
             u'  `HTML_ALT_BLOCK 独占成段=%s 句中不包=%s 句中同句=%s`）。仓库外的 spike 顺手否掉',
             u'  一个看着更"保守"的选择：包 `<div>` **不产生段落距**（裸文字 17.0 / `<p>` 29.0 /',
             u'  `<div>` 17.0）⇒ 选 `<p>` 是量出来的，不是"随便挑一个块级标签"。',
             u'  两半各一把刀（M987 永远包段、M988 永远不包）—— 这两种坏法在屏幕上是相反的。',
             u'- **U-%d：期望值先写错了一次，而修的是**我的推导**，不是地板** ——',
             u'  那条像素门第一版写"紧挨必须 1 处"（我以为夹具里只剩列表内部那一档）。基线一跑就红在',
             u'  2 处：`乙项→alt` 也是 20.0。查下去**不是**规则 ④ 没生效（`alt→下一段` 已经从 20.0',
             u'  变成 31.5），而是这个渲染器**不给 `<ul>` 下边距** —— 列表后面紧跟的那一块本来就没有段前距。',
             u'  处置：期望换成从分块结构推出来的 2 处，把多出来那一处登记成现状（BACKLOG %d），',
             u'  并在同一格钉"两群分不开（差 <6pt）就必须红" —— 而不是把 26pt 的地板挪到 34pt 让它过。',
             u'', u'"""')
rep(old_tail, new_tail, "UI_TWO_BULLETS")

rep(L(u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL)'),
    L(u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL,',
      u'       UH, GB_D, GB_L, GS_D, GA_D, GA_L,',
      u'       PD_BANDS, PD_TIGHT, PD_LINE, PD_PARA,',
      u'       PL_BANDS, PL_TIGHT, PL_LINE, PL_PARA,',
      u'       BLOCK_STANDALONE, BLOCK_INLINE, BLOCK_SAME_SENTENCE,',
      u'       UI2, B_LIST)'),
    "UI_TWO_ARGS")

# ── ITERATION（不带数）──────────────────────────────────────────────────────
rep(u'谁都不能引用）。\n\n七维度自评：',
    L(u'谁都不能引用）。',
      u'',
      u'下半场是看图腿逼出来的：第一版把"图被撤之后说明要留下"做完了，看帧时觉得那句"好像跟下一段',
      u'挤在一起" —— 而**形容词不许进台账**，于是现造一把行距尺（复用这一卷已有的 `rowTierProfile`',
      u'+ `textBands`，不新造尺），把"挤在一起"量成"紧挨着的两行有几处"：修之前 3 处、修之后 2 处，',
      u'两档同向。修法就是规则 ④（独占一行的图 ⇒ alt 包成 `<p>`；句中的图 ⇒ 就地替换），',
      u'而 spike 顺手否掉了"包 `<div>`"这个看着更保守的选择 —— 它不产生段落距。',
      u'还有一次自曝：那条像素门我把期望写成 1 处，基线红在 2 处。查下去是渲染器不给 `<ul>` 下边距',
      u'（列表后面那一段本来就没有段前距），**不是**修法没生效。期望换成推导出来的 2，多出来那一处',
      u'登记成 BACKLOG 406 的现状 —— 挪地板是这一族里最便宜也最坏的那种修法。',
      u'',
      u'七维度自评：'),
    "ITER_BLOCK2")

# ── BACKLOG 406 ─────────────────────────────────────────────────────────────
rep(L(u'""" % (B_TITLE, ROUND, ROUND, TITLE_SCAN[0], TITLE_SCAN[1], TITLE_SCAN[2])'),
    L(u'""" % (B_TITLE, ROUND, ROUND, TITLE_SCAN[0], TITLE_SCAN[1], TITLE_SCAN[2])',
      u'',
      u'BL_LIST_ENTRY = u"""',
      u'**%d. 这个渲染器不给 `<ul>` 下边距：列表后面紧跟的那一段没有段前距（R%d 行距尺现读）**（R%d）',
      u'`HTML_ALT_PARA dark 带=%s 紧挨=%s 行内距=%s 段距=%s`、',
      u'`light 带=%s 紧挨=%s 行内距=%s 段距=%s`：',
      u'夹具里"乙项→它下面那一段"这一对的间距是 %s pt，而两个 `<p>` 之间是 %s / %s pt。',
      u'也就是说**列表块之后**的边界在屏幕上是隐形的 —— 与 R336 规则 ④ 修掉的那一半同族',
      u'（块边界读不出来），但成因不同：④ 是我们自己把文字塞成了行内，这一条是',
      u'`NSAttributedString(html:)` 的排版表。R%d 不修（修它要动整条 HTML 通道的段落样式），',
      u'处置是**把现状钉进判据**：`testHtmlAltLineIsItsOwnParagraphOnTheSurface` 的期望',
      u'"紧挨 2 处"里就有这一处 —— 将来谁给列表加了下边距，那一格会红，而他必须同时来改这条。',
      u'',
      u'""" % (B_LIST, ROUND, ROUND,',
      u'       PD_BANDS, PD_TIGHT, PD_LINE, PD_PARA, PL_BANDS, PL_TIGHT, PL_LINE, PL_PARA,',
      u'       PD_LINE, PD_PARA, PL_PARA, ROUND)'),
    "BL_406_TEXT")

rep(L(u'blg = blg.rstrip(u"\\n") + u"\\n\\n" + BL_TITLE.rstrip(u"\\n") + u"\\n"',
      u'wr(BLG, blg.rstrip(u"\\n") + u"\\n")'),
    L(u'blg = blg.rstrip(u"\\n") + u"\\n\\n" + BL_TITLE.rstrip(u"\\n") + u"\\n"',
      u'blg = blg.rstrip(u"\\n") + u"\\n\\n" + BL_LIST_ENTRY.rstrip(u"\\n") + u"\\n"',
      u'wr(BLG, blg.rstrip(u"\\n") + u"\\n")'),
    "BL_406_WRITE")

io.open(P, u"w", encoding=u"utf-8").write(s)
ast.parse(s)
print(u"R336_GEN_PATCH4b edits=%d %s" % (len(EDITS), u",".join(EDITS)))
