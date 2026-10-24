#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 生成器的第四支补丁（收尾）：CHANGELOG / STATE / 报告计数器 / §8 名单接上下半场。

和 4a/4b 同一条规矩：正文只在末尾追加、参数只在元组末尾追加。
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


# 1. CHANGELOG
rep(L(u'  （量到的名单=%s 对 登记的=%s、本文件行数 %s、全表总数 %s），同一笔改到现读并把"红消失"钉成现读。',
      u'- 回顾时量到并新开 %d：同一轮的两笔提交在标题里给出两个「产品 K 文件」（现读 %s 轮里 %s 轮不一致），修法与豁免名单一起写在条目里。',
      u'', u'""" % (ROUND, UA, UMAX, PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK,'),
    L(u'  （量到的名单=%s 对 登记的=%s、本文件行数 %s、全表总数 %s），同一笔改到现读并把"红消失"钉成现读。',
      u'- 回顾时量到并新开 %d：同一轮的两笔提交在标题里给出两个「产品 K 文件」（现读 %s 轮里 %s 轮不一致），修法与豁免名单一起写在条目里。',
      u'- 下半场（看图腿量出来的，不是新特性）：独占一行的 `<img>` 被撤之后 alt 包成 `<p>`，句中的图仍就地替换。',
      u'  行距尺现读 紧挨处数 修之前 暗/亮 = %s/%s → 修之后 = %s/%s；像素门 `HTML_ALT_PARA 行内距=%s 段距=%s`。',
      u'  新增判据 2 格（结构 + 像素）、刀 M987/M988；新开 %d：渲染器不给 `<ul>` 下边距（现状钉进判据）。',
      u'', u'""" % (ROUND, UA, UMAX, PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK,'),
    u"CHG_BLOCK2_TEXT")

rep(L(u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL,',
      u'       B_TITLE, TITLE_SCAN[1], TITLE_SCAN[2])'),
    L(u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL,',
      u'       B_TITLE, TITLE_SCAN[1], TITLE_SCAN[2],',
      u'       GB_D, GB_L, GA_D, GA_L, PD_LINE, PD_PARA, B_LIST)'),
    u"CHG_BLOCK2_ARGS")

# 2. STATE：末尾一段（带现读数）
rep(u'新日志里这一朵红消失（`grep -c` 现读 0）⇒ 登记生效（U-%d）。\n\n""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N,',
    L(u'新日志里这一朵红消失（`grep -c` 现读 0）⇒ 登记生效（U-%d）。',
      u'',
      u'下半场（同一轮里加的，因为它是**看图腿量出来的**，不是新特性）：规则 ④ —— 独占一行的图，',
      u'它的 alt 包成 `<p>`；句中的图就地替换。行距尺现读 紧挨处数 修之前 暗/亮 = %s/%s →',
      u'修之后 = %s/%s；`HTML_ALT_PARA dark 带=%s 行内距=%s 段距=%s`、',
      u'`light 带=%s 行内距=%s 段距=%s`；',
      u'`HTML_ALT_BLOCK 独占成段=%s 句中不包=%s 句中同句=%s`；刀加到 M984…M988（`CAUGHT=5/5`）。',
      u'另一次自曝：那条像素门的期望我先写成"紧挨 1 处"，基线红在 2 处 —— 多出来那一处是',
      u'**渲染器不给 `<ul>` 下边距**（登记成 %d 的现状，判据里同时钉"两群分不开就必须红"），',
      u'修的是我的推导，不是地板（U-%d）。',
      u'',
      u'""" % (ROUND, DATE, AUDIT_N, ITER_N, PRODUCT_N,'),
    u"STATE_BLOCK2_TEXT")

rep(L(u'       ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL, UG)'),
    L(u'       ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL, UG,',
      u'       GB_D, GB_L, GA_D, GA_L, PD_BANDS, PD_LINE, PD_PARA, PL_BANDS, PL_LINE, PL_PARA,',
      u'       BLOCK_STANDALONE, BLOCK_INLINE, BLOCK_SAME_SENTENCE, B_LIST, UI2)'),
    u"STATE_BLOCK2_ARGS")

# 3. 报告那一格：新开三单、BACKLOG 最大 406
rep(u'% (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D1, B_TITLE,',
    u'% (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D1, B_LIST,',
    u"REPORT_MAX406")

rep(u'"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开两单：%d 属性值含 `>` 的截断限制、%d 标题内两个产品数；"',
    u'"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开三单：%d 属性值含 `>` 的截断限制、%d 标题内两个产品数、%d 列表后面没有段前距；"',
    u"REPORT_THREE")

rep(u'                B_LEAK, B_TITLE, B_ALT, B_MDBUDGET,',
    u'                B_LEAK, B_TITLE, B_LIST, B_ALT, B_MDBUDGET,',
    u"REPORT_THREE_ARGS")

rep(u'u"帧基线同一笔更新：CHANGED=4（只有 HTML 夹具那两张 × 两档）。"',
    u'u"帧基线同一笔更新：累计 4 张变了（alt 那句 + 它自成一段），每张都只该是 HTML 夹具那两档。"',
    u"REPORT_FRAMES_CELL")

# 4. §8 搬运名单：把下半场两族当场声明进去（新读数接进它被打印的那一步）
rep(u'              u"HTML_INKREAD", u"HTML_ALT", u"MD_RENDER_COST", u"HTML_TYPE"])',
    u'              u"HTML_INKREAD", u"HTML_ALT", u"MD_RENDER_COST", u"HTML_TYPE",\n'
    u'              u"HTML_ALT_BLOCK", u"HTML_ALT_PARA"])',
    u"MUST_INCLUDE")

rep(u'NEW_READINGS = (u"`MD_RENDER_COST` 第一次进 §8（连同 `HTML_ALT`）—— 新读数族在它被打印的同一笔里接上，"',
    u'NEW_READINGS = (u"`MD_RENDER_COST` / `HTML_ALT` / `HTML_ALT_BLOCK` / `HTML_ALT_PARA` 第一次进 §8 —— '
    u'新读数族在它被打印的同一笔里接上，"',
    u"NEW_READINGS_TEXT")

io.open(P, u"w", encoding=u"utf-8").write(s)
ast.parse(s)
print(u"R336_GEN_PATCH4c edits=%d %s" % (len(EDITS), u",".join(EDITS)))
