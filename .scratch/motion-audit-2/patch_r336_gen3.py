#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 生成器的第三支补丁：把回顾时量到的「同一轮两笔标题给出两个产品数」登记成 BACKLOG 405。

只加一条工单，不加 U、不加 D —— 这条是**量到的缺席**（还没立新规矩、也还没修），
它的正确落点是工单而不是结论。而"扫了几轮、有几轮不一致"必须由生成器**当场再扫一遍 git** 解析，
不许抄我几分钟前跑出来的那两个数（同一轮里我又提交了东西，抄过去的数下一格就过期）。

尺的退出码 1 在这一格**不是坏**：现状就是有不一致，那正是本条存在的原因 ⇒ 只解析、不判退出码。
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


# 1. 常量：只加工单号
rep(u'B_LEAK = 404           # 属性值里含 `>` ⇒ 标签正则先截断，剩下的属性文字漏进正文',
    u'B_LEAK = 404           # 属性值里含 `>` ⇒ 标签正则先截断，剩下的属性文字漏进正文\n'
    u'B_TITLE = 405          # 回顾时量到的：同一轮的两笔提交在标题里给出两个「产品 K 文件」',
    u"B_TITLE")

# 2. 当场重扫 git（放在清账门之前，因为 §5 之后就要用）
rep(u'gt, gtc = sh([sys.executable, GATE])',
    u'TITLE_SCAN_PY = os.path.join(ROOT, u".scratch", u"motion-audit-2", u"review_round_claims.py")\n'
    u'ts_out, ts_rc = sh([sys.executable, TITLE_SCAN_PY, u"200"])\n'
    u'_tm = re.search(u"扫了=(\\\\d+) 笔 / (\\\\d+) 轮 内部不一致=(\\\\d+)", ts_out)\n'
    u'if not _tm:\n'
    u'    die(u"回顾那把尺的第一行解析不了（退出码 %s）：" + ts_out[:200])\n'
    u'TITLE_SCAN = _tm.groups()   # (笔数, 轮数, 不一致的轮数) —— 退出码 1 是现状，不是坏，故不判\n'
    u'print(u"R336_TITLE_SCAN " + u"/".join(TITLE_SCAN))\n\n'
    u'gt, gtc = sh([sys.executable, GATE])',
    u"TITLE_SCAN")

# 3. BACKLOG 新条目
rep(u'wr(BLG, blg.rstrip(u"\\n") + u"\\n")',
    u'blg = blg.rstrip(u"\\n") + u"\\n\\n" + BL_TITLE.rstrip(u"\\n") + u"\\n"\n'
    u'wr(BLG, blg.rstrip(u"\\n") + u"\\n")',
    u"BLG_WRITE")

rep(u'# 401 / 402 的结案写进**它们自己那条**的追记（同号两份正文 = 读者不知道哪份作数）',
    u'''BL_TITLE = u"""
**%d. 标题里那半句「产品 K 文件」在同一轮的两笔提交里给出两个数（R%d 回顾时现读）**（R%d）
`python3 .scratch/motion-audit-2/review_round_claims.py 200` 现读：扫了 **%s 笔 / %s 轮**，
其中 **%s 轮内部不一致** —— R335 是 `代码半=7 / 账半=7 / 代码半补=0`，R334 是 `代码半=2 / 账半=0`。
两种语义都在被使用：K = **这一轮**的产品面文件数（台账那一格引用的就是它，也是
`scripts/product_streak.py` 从"代码半"那一笔并集派生的数），或 K = **这一笔提交**改的文件数。
读 `git log` 的人无从判断哪一句作数；而标题已经带着「第 N 轮 / Round M」这一串**轮次级**身份，
所以混用是自我矛盾的形状。
下一轮要做两件事：① 立一条 D 定义"轮次级 —— 本轮每一笔重复同一个数"；
② 把 `review_round_claims.py` 变成电池里会红的门，并把 R334/R335 这两轮写进**显式豁免名单**
（按扫描作用域对账；不许把窗口整体放宽 —— 放宽窗口 = 把已经发生的不一致洗成看不见）。
本条不是隐私洞也不是渲染缺陷，是审计链自己的可读性。

""" % (B_TITLE, ROUND, ROUND, TITLE_SCAN[0], TITLE_SCAN[1], TITLE_SCAN[2])

# 401 / 402 的结案写进**它们自己那条**的追记（同号两份正文 = 读者不知道哪份作数）''',
    u"BL_TITLE_TEXT")

# 4. CHANGELOG 一条（正文与参数都只往末尾追加）
rep(u'  （量到的名单=%s 对 登记的=%s、本文件行数 %s、全表总数 %s），同一笔改到现读并把"红消失"钉成现读。\n\n"""',
    u'  （量到的名单=%s 对 登记的=%s、本文件行数 %s、全表总数 %s），同一笔改到现读并把"红消失"钉成现读。\n'
    u'- 回顾时量到并新开 %d：同一轮的两笔提交在标题里给出两个「产品 K 文件」'
    u'（现读 %s 轮里 %s 轮不一致），修法与豁免名单一起写在条目里。\n\n"""',
    u"CHG_TITLE_TEXT")

rep(u'""" % (ROUND, UA, UMAX, PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK,\n'
    u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL)',
    u'""" % (ROUND, UA, UMAX, PRODUCT_N, MD_FIXED, MD_MARGINAL, MD_CAP_CHARS, MD_BIG, B_LEAK,\n'
    u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL,\n'
    u'       B_TITLE, TITLE_SCAN[1], TITLE_SCAN[2])',
    u"CHG_TITLE_ARGS")

# 5. 报告那一格：最大号换成 405，"新开一单"换成"两单"（两处参数各加一个，顺序按正文）
rep(u'% (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D1, B_LEAK,',
    u'% (BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D1, B_TITLE,',
    u"REPORT_MAX_ARG")

rep(u'"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开一单：%d 属性值含 `>` 的截断限制；"',
    u'"决定台账最大 **D-%d**，BACKLOG 最大 **%d**（本轮新开两单：%d 属性值含 `>` 的截断限制、%d 标题内两个产品数；"',
    u"REPORT_NEW_TEXT")

rep(u'                B_LEAK, B_ALT, B_MDBUDGET,',
    u'                B_LEAK, B_TITLE, B_ALT, B_MDBUDGET,',
    u"REPORT_NEW_ARGS")

# 6. §13 的"产品面"那一格与最终打印里的 BACKLOG 最大号
rep(u'u"401/402 结案，新开 %d；400 仍开（要动先得有笔画墨量尺）。"',
    u'u"401/402 结案，新开 %d 与 %d；400 仍开（要动先得有笔画墨量尺）。"',
    u"PROD_CELL_TEXT")

rep(u'               STREAK_N, B_LEAK))',
    u'               STREAK_N, B_LEAK, B_TITLE))',
    u"PROD_CELL_ARG")

rep(u'      % (PRODUCT_N, UA, UMAX, udefs, D1, B_LEAK,',
    u'      % (PRODUCT_N, UA, UMAX, udefs, D1, B_TITLE,',
    u"FINAL_PRINT")

# 7. STATE 的下一轮那一格补一句（纯文字 + 工单号，不含读数量的占位符 ⇒ 不动参数顺序）
rep(u'367/360/361/364 → ② 400 那条要动就得先造尺（笔画墨量），不许用形容词结案 →',
    u'367/360/361/364 → ② 400 那条要动就得先造尺（笔画墨量），不许用形容词结案 → '
    u'④ 405：把"标题里那半句产品数"立成定义并变成电池里会红的门（R334/R335 走显式豁免），'
    u'它比动效那一串便宜得多，而且是审计链自己的可读性 →',
    u"STATE_TITLE_LINE")

io.open(P, u"w", encoding=u"utf-8").write(s)
ast.parse(s)
print(u"R336_GEN_PATCH3 edits=%d %s" % (len(EDITS), u",".join(EDITS)))
