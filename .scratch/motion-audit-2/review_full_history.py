#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""**全历史**回顾尺：把几条"只在最近窗口里判"的守卫一次拉到整个台账长度上跑。

为什么要有它（用户点名：把这么长时间的工作与无数个提交慢慢回头复核一遍）：
仓库里那几条台账守卫（`test_ledger_ids.py` / `test_round_batch_consistency.py`）都带**回看窗口**
—— 窗口是对的（每轮都全量重扫三本大账，电池会从 50 秒变成几分钟），但它有一个副作用：
**窗口之外从来没人看过**。停在 R136 的报告标题、停在 D-149 的那一格，都是"最近若干轮没问题"
掩盖"更早的账早就漂了"的实例。这一支不改守卫、不放宽任何窗口，它只做一件事：
把同样的判据在全长度上跑一遍，把量到的落进台账（该开单的开单，该修的修）。

用法：`PYTHONUTF8=1 python3 .scratch/motion-audit-2/review_full_history.py`
退出码恒为 0（它是**读数**，不是闸门）；每一族打一行 `REVIEW_<名> …`，有发现就附前若干条。
"""
from __future__ import print_function

import io
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
AUD = u"AGENT_UI_AUDIT.md"
ITE = u"AGENT_VISUAL_ITERATION.md"
DEC = u"AGENT_DECISIONS.md"
BLG = u"AGENT_BACKLOG.md"
CHG = u"CHANGELOG.md"
STA = u"AGENT_STATE.md"
FRA = u"AGENT_FINAL_REPORT.md"
ALL = [AUD, ITE, DEC, BLG, CHG, STA, FRA]


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding=u"utf-8").read()


TEXT = dict((n, rd(n)) for n in ALL)


def show(tag, total, bad, samples=6, extra=u""):
    line = u"REVIEW_%s 总量=%d 发现=%d%s" % (tag, total, len(bad), extra)
    print(line)
    for s in bad[:samples]:
        print(u"  - " + s)
    if len(bad) > samples:
        print(u"  …另有 %d 条" % (len(bad) - samples))
    return bad


# ── 1. U：每一节标题声明的区间，是不是每一条都有定义行 ─────────────────────────
defs = set(int(m) for m in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", TEXT[AUD]))
ranges = re.findall(u"(?m)^## 第 (\\d+) 轮（R(\\d+)[^）]*?U-(\\d{3,4})…U-(\\d{3,4})", TEXT[AUD])
missing = []
for audit_n, r_no, lo, hi in ranges:
    want = range(int(lo), int(hi) + 1)
    gap = [u for u in want if u not in defs]
    if gap:
        missing.append(u"第 %s 轮（R%s）声明 U-%s…U-%s，缺定义 %d 条：%s"
                       % (audit_n, r_no, lo, hi, len(gap),
                          u",".join(str(x) for x in gap[:8])))
all_sections = len(re.findall(u"(?m)^## 第 \\d+ 轮", TEXT[AUD]))
show(u"U_RANGE", len(ranges), missing,
     extra=u"（标题声明了区间的节数 / 全文件 %d 节 ⇒ 没声明的不在这条的分母里）" % all_sections)

# ── 2. D：跨七本的每一处引用都要落到正文 ──────────────────────────────────────
ddefs = set(re.findall(u"(?m)^\\*\\*D-(\\d{3})（", TEXT[DEC]))
ddefs |= set(re.findall(u"(?m)^#{2,3} D-(\\d{3})", TEXT[DEC]))
ddefs = set(int(x) for x in ddefs)   # 第一版拿字符串比整数 ⇒ 333 条引用全部假报悬空
dref = {}
for name in ALL:
    for m in re.findall(u"D-(\\d{3})", TEXT[name]):
        dref.setdefault(int(m), set()).add(name)
dangling_d = [u"D-%d 被引用于 %s，但 AGENT_DECISIONS.md 没有正文"
              % (n, u",".join(sorted(fs))) for n, fs in sorted(dref.items()) if n not in ddefs]
show(u"D_REF", len(dref), dangling_d, extra=u"（定义 %d 条）" % len(ddefs))

# ── 3. BACKLOG：引用要落到真条目；同号两份正文要能看见 ─────────────────────────
bold_ids = [int(m) for m in re.findall(u"(?m)^\\*\\*(\\d{1,3})\\. ", TEXT[BLG])]
# 早期条目是裸编号（`14. **已结案（R10）**…`）。但文件里另有一处 1..11 的编号清单**不是条目号**，
# 所以：引用解析用并集（两种形状都要能落到条目），而"同号两份正文"只数无歧义的粗体形，
# "空号"只在 ≥100 那一段算（小于 100 的号会被别的编号清单污染 —— 尺的口径要写死）。
plain_ids = [int(m) for m in re.findall(u"(?m)^(\\d{1,3})\\. \\*\\*", TEXT[BLG]) if int(m) >= 12]
bdefs = bold_ids + plain_ids
dupes = sorted([n for n in set(bold_ids) if bold_ids.count(n) > 1])
bset = set(bdefs)
bref = {}
for name in ALL:
    for m in re.findall(u"BACKLOG (\\d{2,3})", TEXT[name]):
        bref.setdefault(int(m), set()).add(name)
dangling_b = [u"BACKLOG %d 被引用于 %s，但没有那一条目" % (n, u",".join(sorted(fs)))
              for n, fs in sorted(bref.items()) if n not in bset]
show(u"BL_REF", len(bref), dangling_b, extra=u"（条目 %d 条 / 最大 %d）" % (len(bset), max(bset)))
print(u"REVIEW_BL_DUP 同号两份正文=%d %s" % (len(dupes), dupes[:12]))
holes = sorted(set(range(100, max(bdefs) + 1)) - bset)
print(u"REVIEW_BL_HOLES 空号=%d %s" % (len(holes), holes[:20]))

# ── 4. 七维表：每一节都要恰好 7 行、同一量纲 ───────────────────────────────────
sections = re.split(u"(?m)^## Round (\\d+)", TEXT[ITE])
pairs = [(int(sections[i]), sections[i + 1]) for i in range(1, len(sections) - 1, 2)]
bad7 = []
for n, body in pairs:
    # `| 合计 | 82/105 |` 那一行**不是第八个维度**：R292 起有些节自己加了一行总分。
    # 第一版把它算进去 ⇒ 35 节"8 行、量纲 105"全是假警报（把 7×15 的分母当成混用量纲）。
    rows = [r for r in re.findall(u"(?m)^\\| ([^|]+) \\| (\\d+)/(\\d+) \\|", body)
            if u"合计" not in r[0] and u"总分" not in r[0]]
    if not rows:
        bad7.append(u"Round %d：没有七维表" % n)
        continue
    wrong_dim = [r[2] for r in rows if r[2] != u"15"]
    if len(rows) != 7 or wrong_dim:
        bad7.append(u"Round %d：%d 行%s" % (n, len(rows),
                    u"，量纲 %s" % sorted(set(wrong_dim)) if wrong_dim else u""))
# 七维表是后来才立的规矩：从**第一张有表的节**往前都不该被这条判（把历史判成 165 处缺陷
# 是尺的口径错，不是账错 —— 第一版就假报了这么多）。
with_table = [n for n, b in pairs if re.search(u"(?m)^\\| [^|]+ \\| \\d+/\\d+ \\|", b)]
first7 = min(with_table) if with_table else 10 ** 6
bad7_new = [x for x in bad7 if any(u"Round %d" % n == x[:7 + len(str(n))] for n in with_table)
             or any(x.startswith(u"Round %d：" % n) for n in with_table)]
print(u"REVIEW_SEVEN 规矩从 Round %d 起用；之前 %d 节没有表（历史形状，不判）"
      % (first7, len(pairs) - len(with_table)))
show(u"SEVEN_AFTER", len(with_table), bad7_new, samples=12)

# ── 5. 三本账的轮次配对：第 N 轮 ↔ Round N-3（映射漂了就是引用错轮）─────────────
audit_rounds = dict((int(a), int(r)) for a, r, _lo, _hi in ranges)
iter_rounds = set(n for n, _ in pairs)
mis = []
for audit_n, r_no in sorted(audit_rounds.items()):
    want = r_no - 3
    if want not in iter_rounds:
        mis.append(u"第 %d 轮（R%d）应有 Round %d，ITERATION 里没有" % (audit_n, r_no, want))
show(u"PAIR", len(audit_rounds), mis, samples=10)

# ── 6. 提交标题：同一轮内部的产品数只能有一个 ──────────────────────────────────
res = subprocess.run([sys.executable, u".scratch/motion-audit-2/review_round_claims.py", u"100000"],
                     cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = res.stdout.decode(u"utf-8", u"replace")
head = out.splitlines()[0] if out.splitlines() else u"读不到"
print(u"REVIEW_COMMIT_CLAIMS " + head)
for l in out.splitlines()[1:]:
    print(u"  - " + l.strip())

# ── 7. 报告：§13 那节说到的区间与活账的差距（它停过两次，每次都是几十轮）────────
latest_audit = max(int(m) for m in re.findall(u"(?m)^## 第 (\\d+) 轮", TEXT[AUD]))
secs = re.findall(u"(?m)^## (?:1[0-9]|[1-9])\\. R(\\d+) → R(\\d+)", TEXT[FRA])
last_sec = max((int(b) for _a, b in secs), default=0)
print(u"REVIEW_REPORT_RANGE 最新一节覆盖到 R%d，而 UI_AUDIT 已经写到第 %d 轮（R%d）⇒ 落后 %d 轮"
      % (last_sec, latest_audit, latest_audit + 1, latest_audit + 1 - last_sec))

# ── 8. STATE：每一轮的节标题唯一、按新→旧排、identity 行在 ────────────────────
sta_rounds = [int(m) for m in re.findall(u"(?m)^## R(\\d+) 状态", TEXT[STA])]
dup_sta = sorted([n for n in set(sta_rounds) if sta_rounds.count(n) > 1])
unordered = [u"%d 之后是更小的 %d" % (sta_rounds[i], sta_rounds[i + 1])
             for i in range(len(sta_rounds) - 1) if sta_rounds[i] < sta_rounds[i + 1]]
ident = len(re.findall(u"(?m)^最后更新：", TEXT[STA]))
print(u"REVIEW_STATE 节=%d 重复=%s 顺序倒置=%d identity 行=%d 覆盖 R%d…R%d"
      % (len(sta_rounds), dup_sta, len(unordered), ident,
         min(sta_rounds), max(sta_rounds)))
for l in unordered[:6]:
    print(u"  - " + l)

# ── 9. CHANGELOG：[Unreleased] 只许一处，条目要带轮次徽章 ──────────────────────
entries = re.findall(u"(?m)^### (.+)$", TEXT[CHG])
VOCAB = (u"Added", u"Fixed", u"Changed", u"Removed", u"Deprecated", u"Security", u"备注", u"Unreleased")
real = [e for e in entries if not any(e.strip().startswith(v) for v in VOCAB)]
no_badge = [e[:60] for e in real if not re.search(u"（R\\d+", e)]
print(u"REVIEW_CHANGELOG 全部 ###=%d 其中条目=%d 无轮次徽章=%d unreleased=%d"
      % (len(entries), len(real), len(no_badge), TEXT[CHG].count(u"\n## [Unreleased]\n")))
for e in no_badge[:6]:
    print(u"  - " + e)
