#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`red_name_reconciliation.py` 的真值表（R582 / 派单 ④：对账不许每轮手写"为什么不算"）。

六件事各钉一条，全是**合成**的账本文本（不读盘上那份，免得某一轮改措辞就把这条测试带崩）：
① 一行指向 `⑨·N` ⇒ 计入；
② **两行指同一个编号** ⇒ 计入行=2 而编号去重=1（上一轮手写的 红名 16 / 编号 9 就是这两个不同的口径，
   混用一个数就会下一轮拿错的对账）；
③ 带 `不计入对账口径` + 三类名字之一 ⇒ 不计入（可数）；
④ 带 token 但名字不在三类里 ⇒ **未标**（多一类豁免必须先改门，不许在账里随手发明）；
⑤ 什么都没标 ⇒ 未标 ⇒ 主函数退 1；
⑥ ⑨ 正文里那句"那一朵红"不是红名行 ⇒ 不许被数进来（R55 的 M276 那一族：守卫读到自己）。

另外两格是门本身的形状：名单为空必须红（R99）；口径一旦启用就不许在新节关掉。
刀 M1531 把「未标必须红」改恒假时，这里必须红。
"""
import io
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "scripts", "red_name_reconciliation.py")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import red_name_reconciliation as rec  # noqa: E402

HEAD = "## R900 状态（2026-11-06 · 第 899 轮 / Round 897 · 合成）\n"
REGIME = u"· **对账口径**（合成）：三类豁免写 `不计入对账口径`，其余一律进编号。\n"
BLOCK = u"- **红名对账**：\n"


def section(body, heading=HEAD):
    return heading + body


def counted(number):
    return u"  · 红名「X%d」→ ⑨·%d\n" % (number, number)


class TruthTable(unittest.TestCase):
    def test_counted_and_exempt_and_unmarked(self):
        lines = [
            counted(1),
            u"  · 红名「Y」→ **不计入对账口径**（契约名）\n",
            u"  · 红名「Z」→ 没写归属\n",
        ]
        rows, numbers, exempt, unmarked, samples = rec.classify(lines)
        self.assertEqual((rows, numbers, exempt, unmarked), (1, 1, 1, 1))
        self.assertEqual(len(samples), 1)

    def test_two_lines_one_number_are_different_regimes(self):
        """⑵ 这一格是本轮新加的口径：**行数与去重编号数必须分开报**。"""
        lines = [u"  · 红名「A」→ ⑨·2\n", u"  · 红名「B」→ ⑨·2\n"]
        rows, numbers, exempt, unmarked, _ = rec.classify(lines)
        self.assertEqual((rows, numbers, exempt, unmarked), (2, 1, 0, 0))

    def test_invented_category_is_not_exempt(self):
        lines = [u"  · 红名「A」→ **不计入对账口径**（这一类我本轮新发明的）\n"]
        rows, numbers, exempt, unmarked, _ = rec.classify(lines)
        self.assertEqual((rows, numbers, exempt, unmarked), (0, 0, 0, 1))

    def test_body_prose_is_not_counted_as_a_red_name(self):
        """⑹ ⑨ 正文里"那一朵红"这种句子不许进名单 —— 否则解释自己会被判成违规。"""
        body = u"⑨ **本轮自伤清单**：\n- 那一朵红名在别处也出现过（这句是散文）\n" + BLOCK + counted(3)
        lines = rec.red_name_lines(section(body))
        self.assertEqual(len(lines), 1)
        self.assertIn(u"⑨·3", lines[0])

    def test_all_three_named_categories_pass(self):
        for name in rec.NAMED_CATEGORIES:
            lines = [u"  · 红名「A」→ **%s**（%s）\n" % (rec.EXEMPT_TOKEN, name)]
            rows, numbers, exempt, unmarked, _ = rec.classify(lines)
            self.assertEqual((exempt, unmarked), (1, 0), name)


class EndToEnd(unittest.TestCase):
    """走真流水线：写一份合成账本，用子命令跑一遍，读它自己打印的那一行。

    为什么不只测纯函数：R550 那一族 —— 正则与真文件之间还有一次解析、一次切节，
    刀改坏那一半时纯函数测试仍然绿。
    """

    def run_gate(self, text, extra_args=()):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as handle:
            handle.write(text)
            path = handle.name
        try:
            proc = subprocess.run([sys.executable, SCRIPT, "--state", path] + list(extra_args),
                                  capture_output=True, text=True)
            return proc.returncode, proc.stdout
        finally:
            os.unlink(path)

    def test_unmarked_line_makes_the_gate_red(self):
        text = section(REGIME + BLOCK + counted(1) + u"  · 红名「漏的一条」→ 散文\n")
        rc, out = self.run_gate(text)
        self.assertEqual(rc, 1, out)
        self.assertIn(u"未标=1", out)
        self.assertIn(u"口径=已启用", out)

    def test_clean_block_passes(self):
        text = section(REGIME + BLOCK + counted(1)
                       + u"  · 红名「通道没跑」→ **不计入对账口径**（通道未跑）\n")
        rc, out = self.run_gate(text)
        self.assertEqual(rc, 0, out)
        self.assertIn(u"未标=0", out)

    def test_empty_roster_is_red_when_regime_is_on(self):
        """R99：名单为空不许读成"本轮没有红名"。"""
        text = section(REGIME + u"- ⑨ 本轮没有红名。\n")
        rc, out = self.run_gate(text)
        self.assertEqual(rc, 1, out)
        self.assertIn(u"RED_NAME_RECONCILIATION=EMPTY", out)

    def test_missing_regime_in_a_fresh_repo_does_not_judge(self):
        """只管未来：任何一节都没启用过口径 ⇒ 这一支给"不判"，不许拿它当红。"""
        text = section(BLOCK + counted(1) + u"  · 红名「A」→ 散文\n")
        rc, out = self.run_gate(text)
        self.assertEqual(rc, 0, out)
        self.assertIn(u"口径=未启用", out)

    def test_regime_cannot_be_closed_by_the_newest_round(self):
        """口径一旦启用就不许关：旧节有、最新节没有 ⇒ 红。"""
        old = section(REGIME + BLOCK + counted(1),
                      heading="## R899 状态（2026-11-05 · 合成）\n")
        new = section(BLOCK + counted(2))
        rc, out = self.run_gate(new + old)
        self.assertEqual(rc, 1, out)
        self.assertIn(u"REGIME_CLOSED", out)

    def test_newest_section_wins_when_sections_are_not_in_order(self):
        """盘上那份不是严格降序（`## R570 ⓪ 开工` 这类节夹在前面）⇒ 门必须按轮次号取最新。"""
        new = section(REGIME + BLOCK + counted(1))
        old = section(REGIME + BLOCK + counted(2) + u"  · 红名「漏的一条」→ 散文\n",
                      heading="## R901 状态（2026-11-06 · 合成）\n")
        rc, out = self.run_gate(new + u"## R570 ⓪ 开工（合成，节形状干扰）\n散文\n" + old)
        self.assertEqual(rc, 1, out)
        self.assertIn(u"节=R901", out)

    def test_measure_mode_never_changes_the_exit_code(self):
        text = section(REGIME + BLOCK + counted(1))
        rc, out = self.run_gate(text, extra_args=("--measure",))
        self.assertEqual(rc, 0, out)
        self.assertIn(u"RED_NAME_MEASURE", out)


class RealLedgerIsReadable(unittest.TestCase):
    """盘上那份真账必须解析得到（合成样本测不出标题漂）。"""

    def test_newest_section_parses_and_regime_state_is_known(self):
        with io.open(os.path.join(ROOT, "AGENT_STATE.md"), encoding="utf-8") as handle:
            text = handle.read()
        pairs = rec.sections(text)
        self.assertGreaterEqual(len(pairs), 1)
        name, body = rec.newest(pairs)
        self.assertRegex(name, r"^R\d{3}$")
        if rec.REGIME_TOKEN in body:
            self.assertGreaterEqual(len(rec.red_name_lines(body)), 1,
                                    u"%s 写了口径行却没有红名行 ⇒ 门会在空名单上假绿" % name)


if __name__ == "__main__":
    unittest.main()
