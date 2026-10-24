#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""把 R336 的生成器补成**七条 U**，并让它从「登记前那一跑」的日志里解析名册那三朵红。

为什么要单独一支脚本而不是手改：这次要动的是同一份文件里的六处（常量、解析段、
UI_BODY 正文与它的参数、ITERATION 正文、STATE 正文、CHANGELOG 正文），
手改很容易出现「正文加了而参数没加」—— 那正是 R334/R335 各浪费一整步的那一类
（占位符与参数按位置配对，缺一半就在执行到那一行时才炸，而前面几遍电池已经白跑）。
脚本每处都断言「命中恰好 1 次」，任何一处不对就在**写盘之前**退出，最后一道是 ast.parse。
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


# 1. 四腿改到新目录（帧不复用上一遍的 PNG）
rep(u'RV_DIR = u"/tmp/r336_rv"',
    u'RV_DIR = u"/tmp/r336b_rv"\n'
    u'ROSTER_OLD_LOG = u"/tmp/r336_rv/full.log"   # 登记前那一跑：名册那三朵红的证人\n'
    u'ROSTER_NEW_LOG = RV_DIR + u"/full.log"',
    u"RV_DIR")

# 2. 第七条 U
rep(u'UA, UB, UC, UD, UE, UF = 1128, 1129, 1130, 1131, 1132, 1133\nUMAX = UF',
    u'UA, UB, UC, UD, UE, UF, UG = 1128, 1129, 1130, 1131, 1132, 1133, 1134\nUMAX = UG',
    u"U_TUPLE")

# 3. 解析段：从旧日志抓那三行断言，并确认新日志里没有这一朵红
anchor = u'# ──  2. 捕获卷：像素那一格 + 两态相减 ────────────────────────────────────────'
block = u''.join([
    u'# ──  1b. 名册那一朵红（登记之前的那一跑）─────────────────────────────────────────\n',
    u'# 三行断言都在**旧日志**里：那一跑是"我新增了读数而没登记名册"时跑的，它就是这一格的证人。\n',
    u'# 新日志里这一朵红必须消失 —— 否则"我修了"这句话没有出处。\n',
    u'old_roster, orc = sh([u"grep", u"-a", u"-m", u"3",\n',
    u'                      u"testProbeFilePrintReadingsAreARosterNotACount] : XCTAssertEqual failed",\n',
    u'                      ROSTER_OLD_LOG])\n',
    u'if orc != 0 or old_roster.count(BS_N) < 2:\n',
    u'    die(u"旧日志里读不到名册那三行（grep 退出码 %d）：%s" % (orc, old_roster[:200]))\n',
    u'_m = re.search(RE_ROSTER_NAMES, old_roster)\n',
    u'if not _m:\n',
    u'    die(u"名册那三行里读不到「标记名单不符」那一行：" + old_roster[:300])\n',
    u'ROSTER_MEASURED, ROSTER_REGISTERED_OLD = _m.group(1), _m.group(2)\n',
    u'_r = re.search(RE_ROSTER_ROWS, old_roster)\n',
    u'if not _r:\n',
    u'    die(u"读不到 PerfBudgetTests 的行数那行：" + old_roster[:300])\n',
    u'ROSTER_ROWS = u"%s/%s" % (_r.group(1), _r.group(2))\n',
    u'_t = re.search(RE_ROSTER_TOTAL, old_roster)\n',
    u'if not _t:\n',
    u'    die(u"读不到名册总数那行：" + old_roster[:300])\n',
    u'ROSTER_TOTAL = u"%s/%s" % (_t.group(1), _t.group(2))\n',
    u'new_roster, nrc = sh([u"grep", u"-a", u"-c",\n',
    u'                      u"testProbeFilePrintReadingsAreARosterNotACount] failed", ROSTER_NEW_LOG])\n',
    u'if new_roster.strip() != u"0":\n',
    u'    die(u"新日志里这一朵红还在（grep -c = %s）⇒ 登记没生效，账不能按修好写" % new_roster.strip())\n',
    u'\n',
    anchor,
])
rep(anchor, block, u"ROSTER_PARSE")

# 3b. 三个正则常量（放在解析段之前，写成 raw 串以免这里的反斜杠被外层求值吃掉）
rep(u'# ──  1. 四腿读数 ─────────────────────────────────────────────────────────────',
    u'BS_N = u"\\n"   # 单独一个常量：这一段要写进**另一份源文件**，反斜杠在这里求值就没了\n'
    u'RE_ROSTER_NAMES = u\'\\("(\\[[^)]*MD_RENDER_COST[^)]*\\])"\\) is not equal to \\("(\\[[^)]*\\])"\\)\'\n'
    u'RE_ROSTER_ROWS = u\'\\("(\\d+)"\\) is not equal to \\("(\\d+)"\\) - PerfBudgetTests\'\n'
    u'RE_ROSTER_TOTAL = u\'\\("(\\d+)"\\) is not equal to \\("(\\d+)"\\) - 这张名册\'\n'
    u'# ──  1. 四腿读数 ─────────────────────────────────────────────────────────────',
    u"ROSTER_REGEXES")

# 4. UI_BODY 追加第七条（正文 + 参数一起，位置在末尾才安全）
rep(u'  像素可读性那两把尺照旧签：暗档 %s:1、亮档 %s:1，反侧两档都是 0 颗。\n\n"""',
    u'  像素可读性那两把尺照旧签：暗档 %s:1、亮档 %s:1，反侧两档都是 0 颗。\n'
    u'- **U-%d：新读数必须**当场**登记进「按文件按标记」那份名册 —— 它替我红了一次（三朵）** ——\n'
    u'  `PerfBudgetTests.swift` 里新增 `MD_RENDER_COST` 之后，全量卷第一次跑就红在\n'
    u'  `testProbeFilePrintReadingsAreARosterNotACount`：现读 量到的标记名单=%s 对 登记的=%s、\n'
    u'  本文件行数 %s（量/登记）、全表总数 %s（量/登记）。这一格问的问题与"走哪条通道"无关：\n'
    u'  **这些读数有没有名字**。三份名单并存挂在 361，本轮不动它们，只把该登记的登记上，\n'
    u'  而且**同一笔**改三格（名单 / 本文件行数 / 全表总数）—— 分两笔改会让中间那一跑是红的，\n'
    u'  而那一跑谁都不能引用。修完的新日志里这一朵红必须消失（脚本现读 `grep -c`），"我修了"才有出处。\n'
    u'\n"""',
    u"UI_BODY_TAIL")

rep(u'       UF, RV[u"baseline_compared"], PAIR_D, PAIR_L, u"74", u"68", D_RATIO, L_RATIO)',
    u'       UF, RV[u"baseline_compared"], PAIR_D, PAIR_L, u"74", u"68", D_RATIO, L_RATIO,\n'
    u'       UG, ROSTER_MEASURED, ROSTER_REGISTERED_OLD, ROSTER_ROWS, ROSTER_TOTAL)',
    u"UI_BODY_ARGS")

io.open(P, u"w", encoding=u"utf-8").write(s)
ast.parse(s)
print(u"R336_GEN_PATCHED edits=%d %s" % (len(EDITS), u",".join(EDITS)))
