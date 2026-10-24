#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R337 的三本账引用闸门：把"全历史回顾"量到的三类洞变成会红的门。

来历（R337 用 `.scratch/motion-audit-2/review_full_history.py` 把判据拉到**全长度**跑了一遍）：
仓库里那几条台账守卫都带**回看窗口**（每轮全量重扫三本大账太慢，窗口是对的），
副作用是"窗口之外从来没人看过"。这一次全长度扫出来的三件事：

① `BACKLOG 166/167/169/170` 四处引用查无条目 —— 逐条查是**条目行形状**：
   写成 `**166.（…）`，点号后面没有空格，而 `test_ledger_ids.ITEM` 那支共享正则要求空格。
   ⇒ 条目已改到规范形状；这一格守着"引用必须落到 ITEM 认得的条目"，
     并且**复用 ITEM 本身**（另写一颗正则 = 第二个权威，那正是这次出洞的成因）。
② `AGENT_STATE.md` 有 10 轮没有自己的节（R257、R277、R278、R282…288）——
   STATE 是三本账里唯一没有守卫的那本（Skill 里就写着这句）。
   ⇒ 这一格按窗口判（最近 STATE_WINDOW 轮必须每轮一节），历史空洞登记在 BACKLOG 407，不放宽窗口。
③ 报告的**叙述节**停在 R298 而账已经写到 R336（落后 38 轮）。
   §1 那一格与标题那一格早有守卫（U-264 那一族），但**没人守叙述节** —— 而报告最该被读的
   恰恰是叙述节。⇒ 这一格量"最新一节覆盖到哪一轮"，落后超过 N 轮就红。

三格都配**内存里的正对照**（把数据改坏，检查必须点名）：没有正对照的守卫，
它报的"0 处"什么也不说明（R107 / R341 那一族）。
"""
from __future__ import annotations

import io
import os
import re
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, u"scripts", u"tests"))

# 同一颗尺：条目行的定义只许有一份。这里**导入**它，不复制 —— 复制就是第二个权威，
# 而"两处各判一遍然后漂开"正是 ① 这次的成因（BACKLOG 250/270 已经为同族改过两次）。
from test_ledger_ids import ITEM          # noqa: E402

LEDGERS = [u"AGENT_UI_AUDIT.md", u"AGENT_VISUAL_ITERATION.md", u"AGENT_DECISIONS.md",
           u"AGENT_BACKLOG.md", u"CHANGELOG.md", u"AGENT_STATE.md", u"AGENT_FINAL_REPORT.md"]

STATE_WINDOW = 40        # ②：最近这么多轮必须每轮有一节（窗口外的洞登记在 BACKLOG 407）
REPORT_LAG_FLOOR = 20    # ③：叙述节最多允许落后这么多轮（R337 现读落后 38 ⇒ 不放宽到 38）

# 只判 3〜4 位号：`ITEM` 那支共享正则的定义域就是 3〜4 位，而 1〜2 位的老条目
# 写成 `14. **已结案（R10）**` 那种裸编号形状，`ITEM` 认不出来 —— 拿一把只看得见
# 3 位号的尺去判"14 号不存在"，报出来的 289 处全是假警报（第一版就是这样）。
# 域要对齐，这是"名册要按扫描作用域对账"那条规矩的又一处。
CITED_BACKLOG = re.compile(u"BACKLOG (\\d{3,4})(?![0-9])")
STATE_SECTION = re.compile(u"(?m)^## R(\\d+) 状态")
ITER_SECTION = re.compile(u"(?m)^## Round (\\d+)")
# 报告的叙述节标题形如 `## 13. R222 → R298 这一段（…）`
REPORT_SECTION = re.compile(u"(?m)^## (?:1[0-9]|[1-9])\\. R(\\d+) → R(\\d+)")


def read(name):
    return io.open(os.path.join(REPO, name), encoding=u"utf-8").read()


def defined_backlog_ids(backlog_text):
    return set(int(m) for m in ITEM.findall(backlog_text))


def dangling_backlog_citations(texts):
    """返回 [(号, 引用它的文件)]：被引用却没有条目的 BACKLOG 号。"""
    ids = defined_backlog_ids(texts[u"AGENT_BACKLOG.md"])
    out = []
    for name in LEDGERS:
        missing = sorted({int(m) for m in CITED_BACKLOG.findall(texts[name])} - ids)
        for n in missing:
            out.append((n, name))
    return sorted(set(out))


def missing_state_sections(state_text, iter_text, window=STATE_WINDOW):
    """最近 window 轮（由 ITERATION 的 Round 派生：R = Round + 3）里 STATE 缺的节。"""
    rounds = sorted({int(m) for m in ITER_SECTION.findall(iter_text)})
    want = [r + 3 for r in rounds][-window:]
    have = {int(m) for m in STATE_SECTION.findall(state_text)}
    return sorted(set(want) - have)


def report_section_lag(report_text, latest_round_label):
    """叙述节覆盖到的最大轮号与"最新一轮"的差。"""
    tos = [int(b) for _a, b in REPORT_SECTION.findall(report_text)]
    if not tos:
        return None
    return int(latest_round_label) - max(tos)


class LedgerCitationTests(unittest.TestCase):
    def setUp(self):
        self.texts = dict((n, read(n)) for n in LEDGERS)

    def test_every_backlog_citation_resolves_to_an_entry(self):
        bad = dangling_backlog_citations(self.texts)
        self.assertEqual([], bad,
                         u"这些 BACKLOG 号被引用却没有条目（按 test_ledger_ids.ITEM 那支正则判）：%s"
                         % (u"; ".join(u"%d←%s" % (n, f) for n, f in bad),))

    def test_state_has_a_section_for_every_recent_round(self):
        missing = missing_state_sections(self.texts[u"AGENT_STATE.md"],
                                         self.texts[u"AGENT_VISUAL_ITERATION.md"])
        self.assertEqual([], missing,
                         u"AGENT_STATE.md 缺这些轮的节（窗口=%d）：%s ⇒ STATE 没有别的守卫，"
                         u"这一格就是它唯一的门" % (STATE_WINDOW, missing))

    def test_report_narrative_section_is_not_stale(self):
        latest = max(int(m) for m in ITER_SECTION.findall(self.texts[u"AGENT_VISUAL_ITERATION.md"])) + 3
        lag = report_section_lag(self.texts[u"AGENT_FINAL_REPORT.md"], latest)
        self.assertIsNotNone(lag, u"报告里找不到任何 `## N. Rxxx → Ryyy` 叙述节 ⇒ 这一格空转")
        self.assertLessEqual(lag, REPORT_LAG_FLOOR,
                             u"报告的叙述节停在 R%d 之前，而账已经写到 R%d（落后 %d 轮，地板 %d）"
                             u" ⇒ §1 与标题有守卫、叙述节没有，这就是它停过两次的原因"
                             % (latest - lag, latest, lag, REPORT_LAG_FLOOR))

    # ---- 正对照：三格各自都必须能被"把数据改坏"抓到 ---------------------------
    def test_the_three_checks_are_falsifiable(self):
        # ① 引用一个不存在的号
        t = dict(self.texts)
        # 造一个**确实不存在**的三位号（最大条目号由现读决定，不许假设）
        ids = defined_backlog_ids(self.texts[u"AGENT_BACKLOG.md"])
        ghost = next(n for n in range(500, 999) if n not in ids)
        t[u"AGENT_STATE.md"] = self.texts[u"AGENT_STATE.md"] + u"\n参见 BACKLOG %d 那一单\n" % ghost
        bad = [n for n, _f in dangling_backlog_citations(t)]
        self.assertIn(ghost, bad, u"①的正对照没被抓到 ⇒ 引用检查看不见新写的悬空引用")
        # ② 抹掉最近一轮的 STATE 节
        state = self.texts[u"AGENT_STATE.md"]
        latest = max(int(m) for m in STATE_SECTION.findall(state))
        # 注意：只在标题**后面**加字是没用的 —— `^## R336 状态` 仍然匹配（第一版就是这么假的）。
        # 正对照必须真的把那一节从门的眼皮底下拿掉：整行换掉。
        forged = re.sub(u"(?m)^## R%d 状态.*$" % latest,
                        u"## （正对照：这一节的标题被整行换掉）", state, count=1)
        self.assertNotEqual(forged, state, u"②的锚点漂了：改不到那一行就谈不上正对照")
        missing = missing_state_sections(forged, self.texts[u"AGENT_VISUAL_ITERATION.md"])
        self.assertIn(latest, missing, u"②的正对照没被抓到 ⇒ STATE 那格看不见缺节")
        # ③ 把叙述节的覆盖上界改旧
        rep = self.texts[u"AGENT_FINAL_REPORT.md"]
        pairs = [(int(a), int(b)) for a, b in REPORT_SECTION.findall(rep)]
        newest = max(b for _a, b in pairs)
        first_for_newest = min(a for a, b in pairs if b == newest)
        forged_rep = rep.replace(u"R%d → R%d" % (first_for_newest, newest),
                                 u"R%d → R%d" % (first_for_newest,
                                                 newest - REPORT_LAG_FLOOR - 5), 1)
        self.assertNotEqual(forged_rep, rep, u"③的锚点漂了：改不到叙述节的覆盖上界")
        latest_round = max(int(m) for m in
                           ITER_SECTION.findall(self.texts[u"AGENT_VISUAL_ITERATION.md"])) + 3
        lag = report_section_lag(forged_rep, latest_round)
        self.assertGreater(lag, REPORT_LAG_FLOOR,
                           u"③的正对照没被抓到 ⇒ 落后 %s 轮还判绿（地板 %d）" % (lag, REPORT_LAG_FLOOR))

    def test_the_item_regex_is_the_same_one_the_census_guard_uses(self):
        """①的前提是"条目形状只有一份定义"。这一格钉住那个前提本身。"""
        self.assertTrue(ITEM.match(u"**166. 标题**（R119）"), u"规范形状认不出 ⇒ 正则被改坏了")
        self.assertIsNone(ITEM.match(u"**166.（R119 结案）标题**"),
                          u"点号后没空格那种形状现在**应当**认不出（它正是本次出洞的写法）；"
                          u"如果哪天决定放宽正则，这一格会红，而必须同时改的是数据形状那一条")


if __name__ == u"__main__":
    unittest.main()
