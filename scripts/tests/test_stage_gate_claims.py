# -*- coding: utf-8 -*-
"""R588 / 靶 1：`scripts/stage_gate_claims.py` —— 台账里「第③段落了件」这类断言必须配闸门全过的证人。

为什么这一支要存在（不是措辞洁癖）：R587 的收口自陈与台账写了「段号=②/③」与「段号仍是第②③段」，
而那一笔 `git diff --name-only HEAD~2 HEAD -- Sources/` 为空、两条具名阻塞一条没撤 ⇒ 那句话让下一轮
读成「§3 第③段闸门已过」。台账是下一轮唯一的事实源，所以这条要**会红**，不能靠我记着。

钉五件事（都各自会红，且都有合成正对照）：
① 判法是纯函数 `classify_line` 的五档真值表（注释里的分类法等于没有）；
② **枚举写法要认得**：`第②③段` 里并不含子串 `第③段` —— 第一版就是这么漏掉 ITERATION 那一行的
   （R586 靶 B 那一课的同一族：名字不是属性，段才是）；
③ **反向陈述不许当断言**：「第③段着色器一字未写 / 未动」必须绿，否则守卫会把规矩本身读成违规；
④ 判**最新一节**，历史节只数不判（同 `red_name_reconciliation.py`：这一支只管未来）；
   但 R587 那一节要能用 `--section R587` 单独判 ⇒ 「这条守卫抓得住当年那句假话」是**永久证人**，
   不随轮次漂；
⑤ 切不出轮次节 ⇒ 不判并点名（不许退回全文去判历史 —— 那是把合法的历史讨论读成违规，
   最容易被人当成"门太严"而关掉）。
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from scripts.stage_gate_claims import (BLOCKERS, classify_line, main, scan,   # noqa: E402
                                       sections, verdict, witnesses)

STATE = os.path.join(REPO, "AGENT_STATE.md")
SPEC = os.path.join(REPO, "docs", "FOLD_DUO_SPEC_2026-11-03.md")

# 合成样本里的形状要用**拼接**写：直接写出来会被"扫台账"的那一支数进自己的正文（R578 那一课）。
FAKE_NUM = u"段号" + u"=" + u"③"
CLAIM_ENUM = u"段号仍是第②" + u"③段"
CLAIM_OPEN = u"第③段" + u"已开工"
NEG_LINE = u"第③段" + u"着色器一字未写"


def STAGE3_MENTION():
    return u"第③段" + u"的着色器仍归下一轮定向"


def state_with(body, head=u"## R900 状态（合成）\n"):
    return head + body + u"\n\n## R899 状态（旧的）\n无关一行\n"


class TruthTableTests(unittest.TestCase):
    def test_classify_line_is_a_five_way_truth_table(self):
        cases = [
            (u"这一行没有段号", u"无关"),
            (u"· 推进：`capture_scale` 报分布", u"无关"),
            (FAKE_NUM + u"，靶 B", u"冒充段号"),
            (CLAIM_ENUM + u"。", u"断言"),
            (CLAIM_OPEN + u"了一半", u"断言"),
            (NEG_LINE + u"（闸门没过）", u"反向陈述"),
            (u"§4 里提到 " + STAGE3_MENTION(), u"提及"),
        ]
        got = [(raw, classify_line(raw)) for raw, _ in cases]
        self.assertEqual([expect for _, expect in cases], [k for _r, k in got],
                         u"真值表翻面逐字：%s" % got)

    def test_enumerated_form_is_recognised_which_substring_would_miss(self):
        """正对照：`第②③段` 不含子串 `第③段` ⇒ 只按子串认的尺会读成「无关」。"""
        self.assertFalse(u"第③段" in CLAIM_ENUM)
        self.assertEqual(u"断言", classify_line(CLAIM_ENUM))

    def test_negation_scopes_to_the_sentence_not_the_regex_span(self):
        """「段号仍是第②段（第③段一字未动）」是**守规矩**的句子：反向词在括号里、在匹配段之外。"""
        self.assertEqual(u"反向陈述", classify_line(
            u"段号仍是第②段（第③段一字未动，证人见 STATE 本节①）。"))
        self.assertEqual(u"断言", classify_line(
            u"段号仍是第②段（第③段已经推进了一半）。"))

    def test_negated_statement_is_not_a_claim(self):
        """反面对照：把规矩本身读成违规的守卫会被关掉 ⇒ 这一格就是防那一步。"""
        self.assertEqual(u"无关", classify_line(u"第①段 一步切换已完成"))
        self.assertEqual(u"反向陈述", classify_line(NEG_LINE))


class QuotingTests(unittest.TestCase):
    """引用与主干的分别：守卫搜的两个串也是**讲这条规矩本身**时避不开的词。

    没有这一档，写手就只能改措辞躲守卫（那是把门调松）；有了这一档，规矩是
    「引用里的段号字样不算断言，句子主干里的才算」。
    ⚠ 代价写在仪器里：把一句真断言整段包进「」可以躲过谓词那一支 ——
      但 `冒充段号` 那一支走的是**原文**（不摘引用），所以那个形状无论如何都红。
    """

    def test_a_quoted_stage_token_is_not_an_assertion(self):
        self.assertEqual(u"无关", classify_line(
            u"本轮起写手一律用「本节③」，段号只在有证人时以「第②段/第③段」出现。"))
        self.assertEqual(u"断言", classify_line(u"段号只在有证人时以第②③段出现。"),
                         u"摘掉引用之后主干仍然要红，否则这一档就是把门调松")

    def test_the_fake_shape_reds_even_inside_quotes(self):
        self.assertEqual(u"冒充段号", classify_line(u"上一轮写的是「段号=③」那种形状"))


class WitnessTests(unittest.TestCase):
    def test_witnesses_are_two_independent_channels(self):
        wit = witnesses(u"三问全过 ⇒ 可以动第③段\n", u"…%s 仍在…\n" % BLOCKERS[0])
        self.assertEqual(True, wit[u"三问全过在规格里"])
        self.assertEqual([BLOCKERS[0]], wit[u"仍挂着的阻塞"])

    def test_a_negated_pass_line_is_not_a_witness(self):
        """规格里写「三问仍未全过」不许被当成证人（否则守卫自己造证人）。"""
        wit = witnesses(u"⇒ 三问仍未全过 ⇒ 第③段继续不开工。\n", u"")
        self.assertEqual(False, wit[u"三问全过在规格里"])

    def test_verdict_requires_both_witnesses(self):
        wit = {u"三问全过在规格里": True, u"仍挂着的阻塞": list(BLOCKERS)}
        reds = verdict([CLAIM_OPEN], [], wit)
        self.assertEqual(1, len(reds), reds)
        self.assertIn(BLOCKERS[0], reds[0])
        wit_ok = {u"三问全过在规格里": True, u"仍挂着的阻塞": []}
        self.assertEqual([], verdict([CLAIM_OPEN], [], wit_ok))
        self.assertTrue(verdict([], [FAKE_NUM], wit_ok), u"冒充段号一律红，证人齐了也不放行")


class ScopeTests(unittest.TestCase):
    def test_only_the_newest_section_is_judged(self):
        text = state_with(u"- %s\n" % CLAIM_OPEN)
        rows, claims, fakes, scope = scan(text)
        self.assertEqual(u"R900", scope)
        self.assertEqual(1, len(claims))
        old = state_with(u"干净的一行\n", head=u"## R900 状态（合成）\n")
        text2 = (u"## R901 状态（新）\n干净\n\n" + text)
        _r2, c2, _f2, scope2 = scan(text2)
        self.assertEqual(u"R901", scope2)
        self.assertEqual([], c2, u"历史节里的假话不许把最新一节一起判红")

    def test_unparseable_headings_do_not_fall_back_to_whole_file(self):
        """切不出节 ⇒ 不判并点名（退回全文会把合法的历史讨论读成违规）。"""
        rows, claims, fakes, scope = scan(u"## 轮次标题形状换了\n- %s\n" % CLAIM_OPEN)
        self.assertEqual([], claims)
        self.assertEqual(u"未切节_不判", scope)

    def test_section_flag_pins_a_historical_witness(self):
        text = (u"## R901 状态\n干净\n\n" + state_with(u"- %s\n" % FAKE_NUM, head=u"## R900 状态\n"))
        _r, _c, fakes, scope = scan(text, section=u"R900")
        self.assertEqual(u"R900", scope)
        self.assertEqual(1, len(fakes))


class RealLedgerTests(unittest.TestCase):
    def test_r587_section_is_a_permanent_witness_that_this_guard_would_have_caught(self):
        """R587 那一节里确有「段号=②/③」⇒ 用 --section 判它，红必须是**永久**读数。"""
        rc, out = self.run_cli(["--section", "R587"])
        self.assertEqual(1, rc, out)
        self.assertIn(u"冒充段号", out)

    def test_newest_section_must_be_clean(self):
        """本轮之后每一轮都受这条管：最新一节不许有冒充段号，也不许有无证的第③段断言。"""
        rc, out = self.run_cli([])
        self.assertEqual(0, rc, out)

    def run_cli(self, extra):
        buf = io.StringIO()
        real_out = sys.stdout
        sys.stdout = buf
        try:
            rc = main([u"--state", STATE, u"--spec", SPEC] + list(extra))
        finally:
            sys.stdout = real_out
        return rc, buf.getvalue()

    def test_sections_helper_splits_both_ledger_heading_shapes(self):
        text = u"## R587 状态（x）\na\n## R586 补记（y）\nb\n"
        self.assertEqual([u"R587", u"R586"], [n for n, _b in sections(text)])
        iter_text = u"## Round 584 · R587（第 586 轮）\na\n## Round 583 · R586\nb\n"
        self.assertEqual([u"R587", u"R586"], [n for n, _b in sections(iter_text)])


class SyntheticRunTests(unittest.TestCase):
    def test_guard_reds_on_a_synthetic_claim(self):
        d = tempfile.mkdtemp(prefix="r588-stage-")
        st = os.path.join(d, "S.md")
        sp = os.path.join(d, "spec.md")
        io.open(st, "w", encoding="utf-8").write(state_with(u"- %s，仪器也补了\n" % CLAIM_OPEN))
        io.open(sp, "w", encoding="utf-8").write(u"⇒ 三问仍未全过。\n")
        rc, out = run_main(["--state", st, "--spec", sp, "--iter", st])
        self.assertEqual(1, rc, out)
        self.assertIn(u"三问全过", out)

    def test_guard_greens_when_the_claim_has_both_witnesses(self):
        d = tempfile.mkdtemp(prefix="r588-stage-")
        st = os.path.join(d, "S.md")
        sp = os.path.join(d, "spec.md")
        io.open(st, "w", encoding="utf-8").write(state_with(u"- %s，仪器也补了\n" % CLAIM_OPEN))
        io.open(sp, "w", encoding="utf-8").write(u"三问全过 ⇒ 可以动第③段。\n")
        rc, out = run_main(["--state", st, "--spec", sp, "--iter", st])
        self.assertEqual(0, rc, out)

    def test_missing_inputs_are_not_a_pass(self):
        rc, out = run_main(["--state", os.path.join(tempfile.gettempdir(), "no-such-r588.md"),
                            "--spec", SPEC])
        self.assertEqual(2, rc, out)
        self.assertIn(u"STAGE_GATE_INPUT_MISSING", out)


def run_main(argv):
    buf = io.StringIO()
    real = sys.stdout
    sys.stdout = buf
    try:
        rc = main(argv)
    finally:
        sys.stdout = real
    return rc, buf.getvalue()


if __name__ == "__main__":
    unittest.main()
