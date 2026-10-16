#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""台账编号一致性守卫（R94 开）。

为什么会有这支：R94 要往 `AGENT_DECISIONS.md` 追加 D-152 时，先 grep 了一下现有编号，
发现最后一条是 **D-150（R92）** —— 而 R93 的两处轮次标题里都写着"D-151"：

    AGENT_UI_AUDIT.md:4771        ## 第 95 轮 · R93：… / D-151
    AGENT_VISUAL_ITERATION.md:7620 ## Round 93 · … / D-151

⇒ 那是一条**被引用却不存在的决定**。它比"少写一条决定"更坏：下一个人（或下一个我）
按编号去查依据，查到的是一个空号，而两处标题的措辞让人以为那里写着结论。
根因很朴素：`ledgers_r93.py` 的 `STAGES` 里根本没有 decisions 那一格，
标题里的"D-151"是手抄的（R89 那条"台账正文里的数字与轮次标签不许手抄"的同一个形状，
只是这次抄的是一个还不存在的号）。

判什么：
  ① 轮次标题里出现的每一个 `D-\\d{3}`，都必须在 `AGENT_DECISIONS.md` 里有 `### D-xxx（RNN）` 那条正文；
  ② 决定条目自己的轮次标签必须与它写在哪儿无关 —— 只查号存在，不查内容（内容归人读）；
  ③ 编号必须连续（中间空一号 = 有人手抄了一个还没落盘的号，或者删过一条没改引用）。
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DECISIONS = REPO / "AGENT_DECISIONS.md"
ROUND_HEADERS = (REPO / "AGENT_UI_AUDIT.md", REPO / "AGENT_VISUAL_ITERATION.md")
# 只认真正的定义行。**第一版写成 `^### (D-\d{3})（(R\d+)）`，只匹配到 36 条**，
# 于是 92 条被引用的编号里 83 条"缺失" —— 那是一堵假正例的墙，会把守卫直接推回去删掉。
# 实测这份台账的形状：老条目是 `## D-000 基线与分支（2026-10-08）`（121 条），
# 近来的轮次写成 `### D-150（R92）标题`（36 条），另有 `### D-037 追补：…` 这种补记行。
# ⇒ 定义 = 二/三级标题 + 编号开头；轮次标签只写在括号里，不作为闸门的一部分。
DEC_DEF = re.compile(r"^#{2,3} (D-\d{3})\b", re.M)
# 轮次标题行：`## 第 95 轮 · R93：…` / `## Round 93 · …`
HEADER = re.compile(r"^## (?:第 \d+ 轮|Round \d+) ·.*$", re.M)
CITED = re.compile(r"\bD-(\d{3})\b")


def defined_ids(text=None):
    if text is None:
        text = DECISIONS.read_text(encoding="utf-8")
    return [m.group(1) for m in DEC_DEF.finditer(text)]


def cited_ids(path):
    text = path.read_text(encoding="utf-8")
    out = []
    for header in HEADER.findall(text):
        out += CITED.findall(header)
    return out


def cited_everywhere():
    return {('D-' + n) for path in ROUND_HEADERS for n in cited_ids(path)}


class LedgerIdTests(unittest.TestCase):
    def test_every_decision_cited_in_a_round_header_exists(self):
        """① 引用要能落到一条正文上。"""
        defined = set(defined_ids())
        self.assertTrue(defined, "一条决定都没抓到 ⇒ 正则坏了，这条守卫是空的")
        missing = sorted(cited_everywhere() - defined)
        self.assertEqual([], missing,
                         "这些编号被轮次标题引用，但 `AGENT_DECISIONS.md` 里没有对应条目："
                         + "、".join(missing)
                         + " ⇒ 要么补上那条决定，要么把标题里的号改成真实存在的那条；不许删守卫")

    def test_decision_numbers_have_no_gaps(self):
        """③ 连续编号：空一号说明有人抄了一个还没落盘的号，或删过一条却没改引用。"""
        nums = sorted(int(x[2:]) for x in defined_ids())
        self.assertTrue(nums, "没有决定条目")
        holes = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)]
        self.assertEqual([], holes, f"D-xxx 有空号：{holes}（最后一条是 D-{nums[-1]:03d}）")

    def test_the_guard_itself_is_not_vacuous(self):
        """正对照：把一条**确实被标题引用过**的决定从定义里抹掉，①必须只抓到它。

        没有这一格，①可以靠"引用集与定义集同时为空"永远绿（R85 那一族：初值即期望）。
        选靶子不能拿"最后一条"随手当：它未必被引用过（那就什么都测不到），
        所以要挑一个确实在引用集里的 —— 这里取编号最大的那条。
        """
        defined = set(defined_ids())
        cited = cited_everywhere()
        pool = sorted(defined & cited)
        self.assertGreaterEqual(len(pool), 3, "被引用又落盘的决定少于 3 条 ⇒ 样本不够，这条测试是空的")
        victim = pool[-1]
        text = DECISIONS.read_text(encoding="utf-8")
        stripped = re.sub(r"^#{2,3} " + victim + r"\b", "## 已删（" + victim + "）", text, count=1, flags=re.M)
        self.assertNotEqual(text, stripped, f"抹掉 {victim} 的定义行没生效 ⇒ 定义行的形状与正则不一致")
        after = set(m.group(1) for m in DEC_DEF.finditer(stripped))
        # 判的是**增量**：抹掉它之后，缺失集只许多出它这一条。
        # （第一版写成"缺失集正好等于 [victim]"，而仓库此刻真的还缺 D-151 ⇒ 两条红叠在一起，
        #  读日志的人会以为正对照在报同一个缺陷 —— 增量形状让这两件事各说各的。）
        self.assertEqual(set(cited - defined) | {victim}, cited - after,
                         f"抹掉 {victim} 之后守卫没有恰好多抓它一条 ⇒ 它不是在判'引用有没有落盘'")

    def test_citation_regex_does_not_match_prose_ids(self):
        """守卫不许命中正文里的引用（R53 那一族：region() 先命中守卫自己写的名字）。"""
        sample = "正文里提到 D-034 与 D-999，但它们不是定义行\n### D-034（R7）标题\n"
        self.assertEqual(["D-034"], [m.group(1) for m in DEC_DEF.finditer(sample)])


if __name__ == "__main__":
    unittest.main()
