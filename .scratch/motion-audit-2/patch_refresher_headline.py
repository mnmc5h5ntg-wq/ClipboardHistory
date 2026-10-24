#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""让 refresh_report_section1.py 也负责**标题那一格**（它停旧数了，而闸门是有的）。

R336 现读：标题写着 `R9–R331，332 节自评`，而 ITERATION 最新一节是 Round 333（334 节）
⇒ `test_final_report_headline` 报 `FINAL_REPORT_HEADLINE_STALE`（允许落后 1 轮）。
这一支刷新器原来的注释说"标题故意不动"，理由是那道门只朝一个方向红
（`claimed > last_round` 才红）。**那条前提已经变了**：守卫现在两头都判（R222 之后加了
`LAG_ROUNDS` 那一支），于是"故意不动"从一条理由变成一格定时红 —— 而它每两轮必红一次，
红在**写盘之后**（生成器把 §1 刷完、电池才发现标题旧了）。
处置：把标题两格也交给仪器推导（两个数都从盘上现读），并把这段理由写回 docstring。
"""
import ast
import io
import sys

P = u"/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/refresh_report_section1.py"
s = io.open(P, encoding=u"utf-8").read()
EDITS = []


def rep(old, new, tag):
    global s
    n = s.count(old)
    if n != 1:
        sys.stderr.write(u"锚点命中 %d 次（要 1 次）[%s]\n" % (n, tag))
        sys.exit(1)
    s = s.replace(old, new)
    EDITS.append(tag)


# 1. docstring：把"故意不动"那段换成现状与理由
rep(u'''范围**只有 §1**，标题那一行故意不动 —— 理由由既有守卫自己签：''',
    u'''范围是 §1 **加标题那一行**（R336 起）。

标题那一格原来"故意不动"，理由写在这里：''',
    u"DOC_HEAD")

rep(u'''所以标签与单位不一致这件事留在 344/345 里显式记账，不在这一支里顺手改。''',
    u'''所以标签与单位不一致这件事留在 344/345 里显式记账，不在这一支里顺手改。

**但"不动"这条前提已经过期**（R336 现读）：那道守卫现在两头都判 —— 除了
`FINAL_REPORT_HEADLINE_AHEAD`，还有 `FINAL_REPORT_HEADLINE_STALE`（落后超过 `LAG_ROUNDS` 就红）。
于是"故意不动"变成一格**每两轮必红一次**的债，而且它红在写盘之后（生成器刷完 §1、
电池才发现标题旧了）。处置不是把地板放宽，是这一支把标题两格也交给仪器：
· `R9–R<NNN>` ← 仪器 `rounds=9..N` 的 N（与守卫同一个 Round 口径）
· `M 节自评` ← 现读 `AGENT_VISUAL_ITERATION.md` 里 `^## Round ` 的节数
两个数都不是手抄，也不与 §1 的 `n=`（有分数的轮数）混用：334 节 vs n=326 是两个分母，
把它们当成一个数正是 D-038 那一族要防的。''',
    u"DOC_REASON")

# 2. 常量：标题锚点与节数来源
rep(u'''CELL = re.compile(''',
    u'''ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
# 标题那一行：`… 审计 R9–R<NNN>，<M> 节自评）`。整行锚定，裸子串会命中正文里的转述。
TITLE = re.compile(u"^(# 最终报告 · .*审计 R9–R)(\\d+)(，)(\\d+)( 节自评）)", re.M)
CELL = re.compile(''',
    u"TITLE_CONST")

# 3. refresh()：加标题
rep(u'''    out = (report_text[:m.start()] + m.group(1) + n + m.group(3) + hi + m.group(5)
           + n + m.group(7) + hi + report_text[m.end():])
    if write:
        wr(REPORT, out)
    return out, True''',
    u'''    out = (report_text[:m.start()] + m.group(1) + n + m.group(3) + hi + m.group(5)
           + n + m.group(7) + hi + report_text[m.end():])
    # 标题那一格：轮号用仪器尾轮，节数用 ITERATION 现读（两个分母各推各的，见文件头）
    sections = str(len(re.findall(u"(?m)^## Round ", rd(ITER))))
    t = TITLE.search(out)
    if not t:
        die(u"标题那一格解不出来 ⇒ 先打印原文再钉锚点，别硬改（守卫会报 UNPARSEABLE）")
    out = (out[:t.start()] + t.group(1) + hi + t.group(3) + sections + t.group(5)
           + out[t.end():])
    changed = changed or (t.group(2), t.group(4)) != (hi, sections)
    if write:
        wr(REPORT, out)
    return out, changed''',
    u"REFRESH_TITLE")

rep(u'''    if (m.group(2), m.group(4), m.group(6), m.group(8)) == (n, hi, n, hi):
        return report_text, False''',
    u'''    changed = (m.group(2), m.group(4), m.group(6), m.group(8)) != (n, hi, n, hi)
    if not changed and len(re.findall(TITLE, report_text)) == 1:
        t0 = TITLE.search(report_text)
        if (t0.group(2), t0.group(4)) == (hi, str(len(re.findall(u"(?m)^## Round ", rd(ITER))))):
            return report_text, False''',
    u"REFRESH_EARLY_EXIT")

# 4. 结论行：把标题的数打出来（不许再写"标题=未动"）
rep(u'''          + u" n=" + inst[0] + u" 尾轮=" + inst[2] + u" 标题=未动（Round 口径，由既有守卫签）")''',
    u'''          + u" n=" + inst[0] + u" 尾轮=" + inst[2]
          + u" 标题=R9–R" + inst[2] + u"，"
          + str(len(re.findall(u"(?m)^## Round ", rd(ITER)))) + u" 节（Round 口径，与守卫同源）")''',
    u"MAIN_LINE")

io.open(P, u"w", encoding=u"utf-8").write(s)
ast.parse(s)
print(u"REFRESHER_PATCHED edits=%d %s" % (len(EDITS), u",".join(EDITS)))
