# -*- coding: utf-8 -*-
"""R310：`scripts/hidden_arms.py` 的尺真身 + 双向棘轮（BACKLOG 364）。

形状照 `test_ledger_readings.py`：合成样本给**已知答案**（活针 / 死针 / 抽不出各一张表），
真产物那一格只判"上界必须恰好等于现读值"；两个方向的正对照都在（变多要响、变少也要响）。
"""
import io
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import hidden_arms as ha  # noqa: E402

SYNTH = os.path.join(REPO, "scripts", "tests", "fixtures", "hidden_arms_synth")


class SyntheticTests(unittest.TestCase):
    """已知答案：三张表各自应当落进哪一格，事先写死在这里。"""

    def setUp(self):
        self.info, self.rot_rows, self.opaque_rows = ha.scan(SYNTH)

    def test_live_needle_is_judged_and_not_rot(self):
        self.assertEqual(3, self.info[u"tables"], u"三张合成表都要被看见")
        self.assertEqual(2, self.info[u"judged"], u"活针 + 死针 两臂可判，实际 %s" % self.info[u"judged"])
        self.assertEqual(1, self.info[u"rot"], u"只许死针那一臂算腐烂")
        self.assertEqual(1, self.info[u"opaque"], u"藏在 lambda 里那一臂必须被登记成「抽不出」，"
                                                 u"不许静默丢掉（那就是 364 原本的形状）")

    def test_the_rot_arm_is_attributed_by_name(self):
        names = {n for n, _arm, _c in self.rot_rows}
        self.assertEqual({u"mutate_r_synthdead.py"}, names,
                         u"腐烂必须可归因到表，否则台账只能写「有几把坏了」：%s" % (self.rot_rows,))

    def test_constant_propagation_is_what_keeps_false_positives_out(self):
        """把常量传播摘掉 ⇒ 变量里的活针会被判成"抽不出候选"⇒ 数就变了。

        这一格钉的是 R310 的第一版假正例（152 rot 里包含当天刚全 CAUGHT 的 r308/r309）：
        不做传播就"看不见针"，做了传播才有 701 可判臂。
        """
        with io.open(os.path.join(SYNTH, "mutate_r_synthlive.py"), encoding="utf-8") as h:
            tree = ha.ast.parse(h.read())
        cmap = ha.const_map(tree)
        self.assertIn(u"NEEDLE", cmap, u"常量传播没把 NEEDLE 解析出来 ⇒ 分箱又坏了")
        self.assertEqual([u"def main(argv):"], cmap[u"NEEDLE"])


class RealRepoRatchetTests(unittest.TestCase):

    def test_the_ceilings_equal_the_live_readings(self):
        """双向棘轮：上界必须**恰好**等于现读值（只判一个方向 = 另一半没有牙）。"""
        info, rot_rows, _opaque = ha.scan()
        self.assertEqual([], ha.verdict(info),
                         u"现读 rot=%s 抽不出=%s 与上界不符（明细 %s）"
                         % (info[u"rot"], info[u"opaque"], rot_rows[:6]))
        self.assertGreater(info[u"judged"], 500,
                           u"可判臂只剩 %s ⇒ 分箱退化了，这一格正在量的东西变少了" % info[u"judged"])

    def test_positive_control_both_directions_fire(self):
        """正对照的基准必须是**真产物现读**，不是上界自己（拿上界当基准就成了同义反复）。

        两个方向各造一次不符：只测一个方向的话，另一方向可以靠"永远不响"蒙过去。
        """
        live, _rot_rows, _opaque_rows = ha.scan()
        self.assertEqual([], ha.verdict(live), u"真产物自己都不放过 ⇒ 上一格与这一格在说两件事")
        up = ha.verdict(dict(live, rot=live[u"rot"] + 1))
        down = ha.verdict(dict(live, rot=live[u"rot"] - 1))
        self.assertIn(u"HIDDEN_ROT_DRIFT", [p.split()[0] for p in up], u"变多不响 ⇒ 腐烂可以随便长")
        self.assertIn(u"HIDDEN_ROT_DRIFT", [p.split()[0] for p in down],
                      u"变少不响 ⇒ 修好了却不降上界，下一次真烂回去也没人知道")
        self.assertIn(u"HIDDEN_OPAQUE_DRIFT",
                      [p.split()[0] for p in ha.verdict(dict(live, opaque=live[u"opaque"] + 1))])


if __name__ == u"__main__":
    unittest.main()
