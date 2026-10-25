#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R340 落盘之后的补齐：把"第二来源"这一发发现写进账，并把电池数改成落盘后那一跑。

为什么单独一支（而不是回头重跑 `ledgers_r340.py`）：六本已经落盘，重跑整支会把 CHANGELOG
再插一遍（它没有幂等守卫）。这一支只做四件事，每一件都 `once()`：
① 电池那一格从 634 改成落盘后的 637（新增的是 8 格，不是 5 格）；
② UI_AUDIT 那一节补一条 U-1171 并把标题区间改成 U-1163…U-1171；
③ BACKLOG 新开 418（豁免只买不红、买不到数对 —— 第三次应验）；
④ 报告的两处 U 上界 + §14 的电池数。
"""
import io
import os
import re
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
AUD = os.path.join(ROOT, u"AGENT_UI_AUDIT.md")
ITE = os.path.join(ROOT, u"AGENT_VISUAL_ITERATION.md")
BLG = os.path.join(ROOT, u"AGENT_BACKLOG.md")
CHG = os.path.join(ROOT, u"CHANGELOG.md")
STA = os.path.join(ROOT, u"AGENT_STATE.md")
FRA = os.path.join(ROOT, u"AGENT_FINAL_REPORT.md")
WRITTEN = []


def rd(p):
    return io.open(p, encoding=u"utf-8").read()


def wr(p, t):
    io.open(p, u"w", encoding=u"utf-8").write(t)
    WRITTEN.append(p)


def die(msg):
    print(u"FIX_R340_DIED " + msg)
    for p in WRITTEN:
        print(u"  已写盘：" + p)
    sys.exit(1)


def once(text, anchor, replacement, where):
    n = text.count(anchor)
    if n != 1:
        die(u"%s：锚点命中 %d 次（要 1 次）：%s" % (where, n, anchor[:80]))
    return text.replace(anchor, replacement)


B_OLD = u"Ran 634"
B_NEW = u"Ran 637"
N_OLD = u"（上一轮 629 → 本轮 634，新增 5 格全在这一支里）"
N_NEW = (u"（上一轮 629 → 本轮 637：`test_round_claim_consistency` 5 格 + "
         u"`test_sources_cell_second_source` 3 格）")

# ── ① 电池数 ─────────────────────────────────────────────────────────────────
for path in (AUD, ITE, CHG, STA, FRA):
    t = rd(path)
    before = t
    t = t.replace(B_OLD, B_NEW)
    t = t.replace(N_OLD, N_NEW)
    if t != before:
        wr(path, t)
for path in (AUD, ITE, STA, FRA):
    if B_OLD in rd(path):
        die(u"%s 里还留着旧的 634" % path)

# ── ② UI_AUDIT：U-1171 + 标题区间 ────────────────────────────────────────────
aud = rd(AUD)
TITLE_OLD = u"## 第 339 轮（R340 · 2026-10-25 · U-1163…U-1170）：回顾尺第二次升成窗口守卫 —— 而它第一次跑就抓到我自己那笔提交（U-1163…U-1170 · 产品 0 文件，判据账）"
TITLE_NEW = u"## 第 339 轮（R340 · 2026-10-25 · U-1163…U-1171）：回顾尺第二次升成窗口守卫 —— 而它第一次跑就抓到我自己那笔提交（U-1163…U-1171 · 产品 0 文件，判据账）"
aud = once(aud, TITLE_OLD, TITLE_NEW, u"UI_AUDIT 标题")

U1171 = u"""
- **U-1171：豁免只买"不红"，买不到"数对" —— 这是它第三次应验，而这次的形状是"报告里有一格连 --write 都写不成"**
  上一轮那笔产品提交 `fb2cea0` 的 subject 缺 `R<NNN>`，`test_commit_subject_hygiene` 走登记豁免之后不再红；
  但 `scripts/report_sources_cell.py` 从 subject 派生轮次，派生不出来就得到 `None` ⇒
  `build_row` 写出 `**R0**`，而它自己的复核比的是 `0 == None` ⇒ **那一格永远写不成**，
  报告里"最近一次动到 `Sources/` 的轮次"停在错的数上，而且**没有任何一条守卫会红**。
  修法不是把账改回 R338（那是拿错的数去迁就一把读不动的尺），而是给取数口加**第二个来源**：
  拿提交自己写的 U 区间去台账节标题里找同一区间，命中恰好一节才认（多段 / 0 节 / 多节一律 None，不许猜）；
  规则与 `product_streak.round_from_uranges` 同源，而轮次号**直接读那一节标题里的 `R<NNN>`**，
  不做「第 N 轮 + 1」的算术（那是第二份权威）。
  同轮把 `test_final_report_headline` 的 `round_from_subject` 也改成**调那个取数口**而不是自己再派生一遍 ——
  现读它当时退回上一笔能归因的 `d8e6486`（R338）判账，与工具算出的 R339 各说各话：
  **两份派生就是两份权威**，而这类分歧的红最后总会有一边被改成另一边，改到哪边看谁先跑。
  证人：`scripts/tests/test_sources_cell_second_source.py` 三格（合成台账的五种歧义 /
  最近一笔源码提交必须能派生出轮次 —— 这一格在修之前是红的 / 账与 git 必须一致）。

"""
anchor = u"- **U-1170：看图腿（零产品改动轮）先数帧再说话**"
i = aud.find(anchor)
if i < 0:
    die(u"找不到 U-1170 那一行")
j = aud.find(u"\n\n", i)
if j < 0:
    die(u"U-1170 之后找不到节尾")
aud = aud[:j] + u"\n" + U1171.rstrip(u"\n") + aud[j:]
wr(AUD, aud)

# ── ③ BACKLOG 418 ────────────────────────────────────────────────────────────
blg = rd(BLG)
if re.search(u"(?m)^\\*\\*418\\. ", blg):
    die(u"BACKLOG 418 已存在")
BL418 = u"""**418. 报告里「最后一次动到 Sources/ 的轮次」那一格，被一笔缺标签的提交卡成"连 --write 都写不成"：派生逻辑不许有两份**（R340 现读）
现读链条：`fb2cea0`（R339 产品轮）subject 缺 `R<NNN>` ⇒
① `test_commit_subject_hygiene` 已登记豁免（BACKLOG 416）⇒ 那一格不红；
② 但 `report_sources_cell.py` 从 subject 派生轮次得到 `None` ⇒ 写出 `**R0**`，
   复核比 `0 == None` ⇒ `SOURCES_CELL_REFUSED --write 之后文本没变`，rc=2；
③ 而 `test_final_report_headline` 自己又派生一遍，派生不出来就**退回上一笔能归因的提交**
   （`d8e6486` / R338）判账 ⇒ 与②各说各话，两边永远对不齐。
也就是说：**一处豁免 + 两处各自实现的派生**，合起来造出一个"没人报警的坏数"。
本轮做的：给取数口加第二来源（提交自己写的 U 区间 ↔ 台账节标题里的 `R<NNN>`，唯一命中才算），
并把③改成**调②那个函数**，不是再抄一份正则；配 `test_sources_cell_second_source.py` 三格
（其中"最近一笔源码提交必须能派生出轮次"这一格在修之前是红的 ⇒ 它是证人不是装饰）。
**还欠两件事**（不在本轮顺手做）：① 派生不出来时那一格该印什么（`R0` 是一个看起来像结论的假数，
应该改成显式的"号未读"并让守卫按缺席处置，而不是写 0）；② `NO_LABEL_ROSTER` 与
`UNPARSED_ROSTER` 是同一条自伤的两份名单，将来该收成一份（谁登记了 sha，另一份自动知道）。
"""
wr(BLG, blg.rstrip(u"\n") + u"\n\n" + BL418.rstrip(u"\n") + u"\n")

# ── ④ 报告的两处 U 上界 + §14 电池 ──────────────────────────────────────────
fr = rd(FRA)
fr = once(fr, u"U-31 … U-1170", u"U-31 … U-1171", u"报告 U 区间")
m = re.search(u"U 定义行最大 \\*\\*U-1170\\*\\*", fr)
if not m:
    die(u"报告 §14 里找不到 U 上界那一格")
fr = fr.replace(m.group(0), u"U 定义行最大 **U-1171**")
s14 = [ln for ln in fr.splitlines() if ln.startswith(u"- **判据与门的规模**") and u"最新的权威" in ln]
if len(s14) != 1:
    die(u"§14 那一格不是一处")
if u"本轮不落刀" not in s14[0]:
    die(u"§14 里没有本轮那一句（生成器写坏了？）")
new_s14 = (s14[0].replace(u"本轮不落刀（产品 0 文件，没有可打的产品改动 —— 写清而不是凑一把抓不到的刀）。",
                          u"本轮不落刀（产品 0 文件，没有可打的产品改动 —— 写清而不是凑一把抓不到的刀）。"
                          u"新门：`test_round_claim_consistency`（5 格）+ `test_sources_cell_second_source`（3 格）。")
           .replace(u"BACKLOG 最大 **417**", u"BACKLOG 最大 **418**"))
fr = once(fr, s14[0], new_s14, u"§14")
if re.search(u"(?m)^\\*\\*418\\. ", rd(BLG)) is None:
    die(u"418 没落盘")
wr(FRA, fr)

# ── 自检：编号最大号一致 ─────────────────────────────────────────────────────
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", rd(AUD)))
B_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{2,4})\\. ", rd(BLG)))
if (U_MAX, B_MAX) != (1171, 418):
    die(u"最大号不对：%d/%d" % (U_MAX, B_MAX))
if u"U-1171" not in rd(FRA):
    die(u"报告里没跟上 U-1171")
print(u"FIX_R340_OK U=%d BL=%d 电池=%s" % (U_MAX, B_MAX, (re.findall(u"Ran (\\d+) tests", rd(FRA)) or [u"?"])[-1]))
