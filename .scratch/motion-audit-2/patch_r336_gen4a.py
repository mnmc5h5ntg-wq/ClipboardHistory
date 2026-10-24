#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 生成器的第四支补丁：下半场（规则 ④：alt 那句要**自成一段**）接进七本账。

上半场写的是"图被撤之后说明要留下"，下半场是看图腿量出来的：留下的那句被并进了
上一个块的行节奏（真帧 20.0pt 对 段落距 31.5/32.5），于是"留下"在屏幕上读起来仍像漏了一颗项目符号。
两条新 U：U-1135 = 规则 ④ 与它的 spike 反证（`<div>` 不产生段落距）；
U-1136 = **判据自己先窄了一次**（期望"紧挨 1 处"，现读 2 处，多的那一处是渲染器不给 `<ul>` 下边距，
登记成 BACKLOG 406 的现状而不是把地板挪到能过）。

所有数都从盘上的证人解析：
  /tmp/r336_html.log        —— HTML_ALT_BLOCK
  /tmp/r336c_rv/capture.log —— HTML_ALT_PARA 两档
  /tmp/r336b_rv/frames      —— 修之前的帧（行距尺跑它）
  /tmp/r336c_rv/frames      —— 修之后的帧
"""
import ast
import io
import re
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


# ── 1. 常量 ──────────────────────────────────────────────────────────────────
rep(u'UA, UB, UC, UD, UE, UF, UG = 1128, 1129, 1130, 1131, 1132, 1133, 1134\nUMAX = UG',
    u'UA, UB, UC, UD, UE, UF, UG = 1128, 1129, 1130, 1131, 1132, 1133, 1134\n'
    u'UH, UI2 = 1135, 1136\nUMAX = UI2',
    u"U_CONST")

rep(u'RV_DIR = u"/tmp/r336b_rv"', u'RV_DIR = u"/tmp/r336c_rv"\n'
    u'BEFORE_FRAMES = u"/tmp/r336b_rv/frames"   # 规则 ④ 之前的那一跑：行距那两格的"修之前"证人\n'
    u'RULER = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"line_gap_ruler.py")\n'
    u'GAP_BOX = [u"40", u"1240", u"110", u"620"]   # px（@2x）：正文列，右半边住着动作条',
    u"RV_DIR2")

rep(u'TABLES = [(u"mutate_r336", u"/tmp/r336_t_r336.log", u"3/3"),',
    u'TABLES = [(u"mutate_r336", u"/tmp/r336_t_r336.log", u"5/5"),',
    u"TABLE_WANT")

rep(u'ARMS_NEW = (u"M984", u"M985", u"M986")',
    u'ARMS_NEW = (u"M984", u"M985", u"M986", u"M987", u"M988")',
    u"ARMS_NEW")

rep(u'B_TITLE = 405          # 回顾时量到的：同一轮的两笔提交在标题里给出两个「产品 K 文件」',
    u'B_TITLE = 405          # 回顾时量到的：同一轮的两笔提交在标题里给出两个「产品 K 文件」\n'
    u'B_LIST = 406           # 现状钉：渲染器不给 <ul> 下边距 ⇒ 列表后面那一段没有段前距（行距尺量到的）',
    u"B_LIST")

rep(u'SEVEN = [13, 14, 14, 13, 13, 14, 13]',
    u'SEVEN = [14, 14, 14, 13, 13, 14, 13]   # 下半场：看图腿第一次给出一把可数的行距尺 + 一次 before/after',
    u"SEVEN")

# 七维表那一行要与 SEVEN 同步（写盘后有一格把表读回来对账）
rep(u'| 真实视觉审查 | 13/15 | 看了暗/亮两档的 html-rendered 与 html-source 四张；alt 那句是亲眼确认的，但没给"图很多"的页面做夹具 |',
    u'| 真实视觉审查 | 14/15 | 看图腿这次不只是"看了"：把"好像挤在一起"量成行距尺（修之前 3 处紧挨 / 修之后 2 处），'
    u'两档各一张 before/after；但仍未给"图很多"的页面做夹具 |',
    u"SEVEN_ROW")

# ── 2. 下半场的解析段 ────────────────────────────────────────────────────────
rep(u'# ──  4. 变异表（本轮三把 + 上一轮十一把的回归）───────────────────────────────',
    u'''# ──  3b. 下半场：alt 那句**自成一段**（结构 + 像素 + before/after）─────────────
ab = one(hl, u"HTML_ALT_BLOCK ", u"HTML_ALT_BLOCK")
BLOCK_STANDALONE, BLOCK_INLINE = tok(ab, u"独占成段="), tok(ab, u"句中不包=")
BLOCK_SAME_SENTENCE = tok(ab, u"句中同句=")
for flag, where in ((BLOCK_STANDALONE, u"独占成段"), (BLOCK_INLINE, u"句中不包"),
                    (BLOCK_SAME_SENTENCE, u"句中同句")):
    if flag != u"true":
        die(u"规则 ④ 的 %s 不是 true（读到 %s）⇒ 产品没修好，账不能按修好写" % (where, flag))

# 像素那一半：两档各一行，期望"紧挨 2 处"（① 列表内部；② 列表→下一块 = BACKLOG 406 的现状）。
# 这一格刻意**不**由"能不能过"来定数：它是从夹具的分块结构推出来的，推导写在判据的注释里。
def para_row(lines, tag):
    row = one(lines, u"HTML_ALT_PARA " + tag + u" ", u"HTML_ALT_PARA " + tag)
    return (num(row, u"带="), num(row, u"紧挨="), num(row, u"行内距="), num(row, u"段距="))

PD_BANDS, PD_TIGHT, PD_LINE, PD_PARA = para_row(cl, u"dark")
PL_BANDS, PL_TIGHT, PL_LINE, PL_PARA = para_row(cl, u"light")
if PD_TIGHT != u"2" or PL_TIGHT != u"2":
    die(u"紧挨的处数不是 2（暗=%s 亮=%s）⇒ 要么规则 ④ 漂了，要么 406 那条现状被修掉了；"
        u"两种都要先去看是哪一种，不许把期望挪到能过的地方" % (PD_TIGHT, PL_TIGHT))

# before/after：同一把尺跑两次（修之前的帧在 r336b，修之后在 r336c），数"紧挨"的处数。
def ruler_tight(frames_dir, tag):
    frame = os.path.join(frames_dir, u"detail-html-rendered-720x520-" + tag + u".png")
    if not os.path.exists(frame):
        die(u"行距尺的帧不在盘上：" + frame)
    out, rc = sh([sys.executable, RULER, frame] + GAP_BOX)
    steps = (re.findall(u"(?m)^LINE_GAP_STEPS_pt (.*)$", out) or [None])[-1]
    if steps is None:
        die(u"行距尺没打结论行（rc=%d）：" % rc + out[-200:])
    vals = [float(v) for v in steps.split(u",")]
    return s(len([v for v in vals if v < 26.0])), u",".join(u"%.1f" % v for v in vals)

GB_D, GS_D = ruler_tight(BEFORE_FRAMES, u"dark")
GB_L, GS_L = ruler_tight(BEFORE_FRAMES, u"light")
GA_D, _ = ruler_tight(RV_DIR + u"/frames", u"dark")
GA_L, _ = ruler_tight(RV_DIR + u"/frames", u"light")
if (GB_D, GB_L) != (u"3", u"3"):
    die(u"修之前那两格读到的紧挨不是 3（暗=%s 亮=%s）⇒ 「修之前」这一半失去了对象，"
        u"before/after 就成了空对账" % (GB_D, GB_L))
if (GA_D, GA_L) != (u"2", u"2"):
    die(u"修之后不是 2（暗=%s 亮=%s）⇒ 屏幕没换，而结构那一格是绿的（判定对了、屏幕没换那一族）"
        % (GA_D, GA_L))

# ──  4. 变异表（本轮五把 + 上一轮十一把的回归）───────────────────────────────''',
    u"PARSE_BLOCK2")

io.open(P, u"w", encoding=u"utf-8").write(s)
ast.parse(s)
print(u"R336_GEN_PATCH4a edits=%d %s" % (len(EDITS), u",".join(EDITS)))
