#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R591 / 靶 1：`ci_skipped_causes.py` 的判据卷 —— 「这一步为什么没出声」要拆成两种**修法相反**的成因。

为什么这一卷存在（R590 ⑦/③ 那一格的更正，forward 不回头改历史）：
R590 读到 `42159607721` 里 `STEP[10]–[14]` 全是 `skipped`，写成「第③态 = 这一步本就没跑 ⇒ 这一维今天没人判」。
本轮现读逐字复核（`gh run view 42159607721 --json jobs`）：那五步的 skipped 与 `STEP[9] failure` 同时出现，
而 `ci.yml` 里那几步**没有 `if: always()`**（全文只有 R89 那一段与本轮新加的四处有）⇒
成因是**被上游红连带**，不是"这台机器没对象"。两种成因的修法相反：前者改接线（`if: always()` 或具名豁免），
后者改名册/机器维度（658/659 那一族）。并成一条就是把"尺从没被调用"读成"尺判了但没东西可判"。

判的格子（每格都用合成语料，绝不跨格复用临时目录）：
  ① 真 `ci.yml` 现读：证据型步骤 >0，无声=0、空豁免=0 ⇒ 绿；
  ② 正对照：证据型步骤没有 always() 也不在名册里 ⇒ 必须红；
  ③ 负对照：不印通道串的步骤**不是证据型**，没有 always() 也不算违规（否则规矩退化成"每步都要 always()"）；
  ④ 注释行里提一个通道名 ≠ 这一步会印它（扫描面不许把注释当对象，R580 那一族）；
  ⑤ 豁免必须同时有名字与理由；理由为空 ⇒ 红；
  ⑥ 豁免**必须真会命中**：名字不在现读证据步骤里、或那一步已经带 always() ⇒ 空豁免，比没豁免更坏；
  ⑦ run 模式：`skipped` 而台账本轮那一节没给成因名字 ⇒ 红；给了 `第③甲` / `第③乙` 且带步骤号或名字 ⇒ 绿；
  ⑧ 只在**本轮那一节**里找成因（历史节里写过同样的话不算，R569 那一族）；
  ⑨ 清单为空 / 台账节读不到 ⇒ 具名「没对象」，退出码 2，不许读成绿。
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'scripts'))

import ci_skipped_causes as C   # noqa: E402


CI_SAMPLE = """      - name: Toolchain
        run: |
          swift --version
      - name: Evidence step with always
        if: always()
        run: |
          echo "FOO_RESULT=ok 红=0"
      - name: Evidence step without always
        run: |
          echo "BAR_RESULT=ok 红=0"
      - name: Quiet step
        run: |
          echo 只是打一句话
"""


def rows(names_always):
    """把 (名字, 有没有 always) 摊成 judge_static 需要的最小结构 —— 只用来构造期望，不替代真解析。"""
    return [{"name": n, "always": a} for n, a in names_always]


class StaticTests(unittest.TestCase):
    def test_the_real_workflow_has_no_silent_evidence_step(self):
        v = C.judge_static(C.read(C.CI_YML), C.load_exemptions())
        self.assertGreater(v["evidence"], 0, u"现读一个证据型步骤都没有 ⇒ 这把尺没对象，不许报绿")
        self.assertEqual([], v["silent"],
                         u"证据型步骤没有 always() 也不在名册里：%s" % [s["name"] for s in v["silent"]])
        self.assertEqual([], v["dead"], u"空豁免（名字对不上或已带 always()）：%s" % (v["dead"],))
        self.assertEqual([], v["bad_rows"])

    def test_positive_control_a_silent_evidence_step_goes_red(self):
        v = C.judge_static(CI_SAMPLE, [])
        self.assertEqual(2, v["evidence"], u"证据型步骤要按正文印不印通道串来认")
        self.assertEqual(1, len(v["silent"]), u"没有 always() 的那一步必须被点名：%s" % (v["silent"],))
        self.assertEqual("Evidence step without always", v["silent"][0]["name"])

    def test_negative_control_a_step_that_prints_nothing_is_not_evidence(self):
        v = C.judge_static(CI_SAMPLE, [])
        names = [s["name"] for s in v["silent"]]
        self.assertNotIn("Quiet step", names, u'不印通道串的步骤被当成证据型 ⇒ 规矩退化成"每步都要 always()"')
        self.assertNotIn("Toolchain", names)

    def test_comment_lines_do_not_count_as_channels(self):
        """注释里提 `FOO_RESULT=` 不等于这一步会印它（扫描面不许把注释当对象）。"""
        body = '# 这一格从前印 FOO_RESULT=ok 后来删掉了\n'
        self.assertEqual([], C.prints_channels(body), u"注释被当成了读数")
        self.assertEqual(1, len(C.prints_channels('echo "FOO_RESULT=ok"\n')))

    def test_exemption_needs_both_name_and_reason(self):
        v = C.judge_static(CI_SAMPLE, [{"name": "Evidence step without always", "reason": "  "}])
        self.assertEqual(1, len(v["bad_rows"]), u"理由为空的豁免被当成了放行")
        self.assertEqual(1, len(v["silent"]))

    def test_dead_exemption_is_red(self):
        """豁免必须真会命中：名字对不上、或那一步已经带 always() ⇒ 空豁免算红。"""
        v = C.judge_static(CI_SAMPLE, [{"name": "No Such Step", "reason": u"不存在"}])
        self.assertEqual(1, len(v["dead"]), v["dead"])
        v2 = C.judge_static(CI_SAMPLE, [{"name": "Evidence step with always", "reason": u"它已经有 always()"}])
        self.assertEqual(1, len(v2["dead"]), v2["dead"])

    def test_live_exemption_clears_the_silence(self):
        v = C.judge_static(CI_SAMPLE, [{"name": "Evidence step without always", "reason": u"上游只有 Build，红时没产物"}])
        self.assertEqual([], v["silent"])
        self.assertEqual([], v["dead"])
        self.assertEqual(1, v["exempted"])

    def test_broken_roster_is_not_read_as_no_exemptions(self):
        d = tempfile.mkdtemp(prefix="r591_roster_")
        p = os.path.join(d, "bad.json")
        io.open(p, "w", encoding="utf-8").write("{not json")
        self.assertIsNone(C.load_exemptions(p), u"名册读不出来时必须返回 None（⇒ 主函数具名不判），不许当成「没有豁免」")


class RunModeTests(unittest.TestCase):
    LEDGER = (u"# 台账\n\n"
              u"## R591 状态（2026-11-06 · 第 590 轮）\n\n"
              u"正文。\n\n"
              u"## R590 状态（2026-11-06 · 第 589 轮）\n\n"
              u"· 第③甲 步=11 名=Frame baseline vs working manifest（历史里写过，不算本轮的具名）\n\n"
              u"## R589 状态（略）\n\n旧文。\n")

    def test_skipped_without_a_cause_name_is_red(self):
        rows = C.parse_steps_dump("9 failure Release script tests\n"
                                  "11 skipped Frame baseline vs working manifest (fixture-set gate)\n")
        v = C.judge_run(rows, self.LEDGER.split(u"## R590")[0].replace(
            u"正文。", u"· 今天没有具名。"))
        self.assertEqual(1, v["skipped"])
        self.assertEqual(1, len(v["unnamed"]), u"skipped 而没有成因名字 ⇒ 必须红")

    def test_cause_name_clears_it_only_when_it_names_this_step(self):
        rows = C.parse_steps_dump("11 skipped Frame baseline vs working manifest (fixture-set gate)\n")
        section = (u"## R591 状态（x）\n"
                   u"· 第③甲 步=11 名=Frame baseline vs working manifest ⇒ 被 STEP[9] 的红连带\n")
        v = C.judge_run(rows, section)
        self.assertEqual([], v["unnamed"], v)

    def test_a_generic_parenthetical_does_not_name_the_step(self):
        """只写「今天有 skipped」而不点名这一步 ⇒ 不算具名（否则任何一句带 ③甲 的话都能糊过去）。"""
        rows = C.parse_steps_dump("11 skipped Frame baseline vs working manifest (fixture-set gate)\n")
        section = u"## R591 状态（x）\n· 第③甲 今天有步骤被连带跳过\n"
        v = C.judge_run(rows, section)
        self.assertEqual(1, len(v["unnamed"]), u"没点名的具名不许放行")

    def test_history_section_is_not_reused(self):
        rows = C.parse_steps_dump("11 skipped Frame baseline vs working manifest (fixture-set gate)\n")
        sec = C.latest_section(self.LEDGER, u"R591")
        self.assertIsNotNone(sec)
        self.assertNotIn(u"第③甲 步=11", sec, u"本轮那一节里混进了历史节的具名 ⇒ 切片范围错了")
        v = C.judge_run(rows, sec)
        self.assertEqual(1, len(v["unnamed"]), u"历史节写过同样的话，不许替本轮作证（R569 那一族）")

    def test_latest_section_missing_is_not_judged(self):
        self.assertIsNone(C.latest_section(self.LEDGER, u"R7777"))


class MainTests(unittest.TestCase):
    def test_empty_steps_dump_is_a_named_absence(self):
        d = tempfile.mkdtemp(prefix="r591_steps_")
        p = os.path.join(d, "s.txt")
        io.open(p, "w", encoding="utf-8").write("\n")
        rc = C.main([u"--mode", u"run", u"--steps", p, u"--round", u"R591"])
        self.assertEqual(2, rc, u"一行都没解析出来时报 2（没对象），不许报绿")

    def test_missing_steps_file_is_a_named_absence(self):
        rc = C.main([u"--mode", u"run", u"--steps", "", u"--round", u"R591"])
        self.assertEqual(2, rc)

    def test_static_mode_on_real_repo_is_green_and_prints_the_scope(self):
        rc = C.main([u"--mode", u"static"])
        self.assertEqual(0, rc)


if __name__ == '__main__':
    unittest.main()
