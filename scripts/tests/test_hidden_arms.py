# -*- coding: utf-8 -*-
"""R310 立尺、R313 加第二箱：`scripts/hidden_arms.py` 的尺真身 + 双向棘轮（BACKLOG 364 / 366 / 367）。

形状照 `test_ledger_readings.py`：合成样本给**已知答案**（活针 / 死针 / 抽不出 / 已声明各一张表），
真产物那一格只判"上界必须恰好等于现读值"；两个方向的正对照都在（变多要响、变少也要响）。

R313 新增的是**已声明那一箱**（表自己写 `NEEDLES = {刀号: [针, …]}`）：
未声明那一箱的 `any(候选命中)` 只配当**下界**（366 现读证伪了两种把它做成上界的静态办法），
而声明之后可以逐根判 —— 于是"一臂两针、一活一死"这种漏报形状第一次有了正对照。
"""
import ast
import io
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import hidden_arms as ha  # noqa: E402

SYNTH = os.path.join(REPO, "scripts", "tests", "fixtures", "hidden_arms_synth")
TABLES = os.path.join(REPO, ".scratch", "motion-audit-2")


class SyntheticTests(unittest.TestCase):
    """已知答案：四张表各自应当落进哪一格，事先写死在这里。"""

    def setUp(self):
        # 显式喂一份 text：夹具的"活针/死针"不能依赖仓库此刻盘上有什么，
        # 否则别的表一改动，期望就跟着漂（那正是 366 那一族"对照不控"的形状）。
        self.text = u"def main(argv):\n    judged = rot = opaque = 0\n"
        self.info, self.rot_rows, self.opaque_rows = ha.scan(SYNTH, text=self.text)

    def test_live_needle_is_judged_and_not_rot(self):
        self.assertEqual(4, self.info[u"tables"], u"四张合成表都要被看见")
        self.assertEqual(1, self.info[u"rot"], u"只许死针那一臂算腐烂")
        self.assertEqual(1, self.info[u"opaque"], u"藏在 lambda 里那一臂必须被登记成「抽不出」，"
                                                 u"不许静默丢掉（那就是 364 原本的形状）")

    def test_declared_bin_reports_the_dead_needle_the_old_bin_misses(self):
        """正对照（BACKLOG 366 要的那一格）：一臂两根针、一根活一根死。

        旧估计量 `any(候选命中)` 看这一臂会报"活的" ⇒ rot 不 +1，**这就是漏报**；
        已声明那一箱逐根判 ⇒ 必须报"死了 1 根"。所以断言是两条一起写的：
        rot 里不许出现它，declared_dead 里必须是 1。
        """
        self.assertEqual(1, self.info[u"declared_dead"],
                         u"已声明那一箱必须逐根数出死针，现读 %s" % (self.info,))
        self.assertEqual(1, self.info[u"declared_arms"])
        self.assertNotIn(u"mutate_r_synthdeclared.py",
                         {n for n, _a, _c in self.rot_rows},
                         u"这一臂被 any() 洗活了 ⇒ 它跑进了下界箱，366 的漏报回来了")
        self.assertEqual([(u"mutate_r_synthdeclared.py", u"M997")],
                         [(n, a) for n, a, _needle in self.info[u"declared_rows"]])

    def test_the_rot_arm_is_attributed_by_name(self):
        names = {n for n, _arm, _c in self.rot_rows}
        self.assertEqual({u"mutate_r_synthdead.py"}, names,
                         u"腐烂必须可归因到表，否则台账只能写「有几把坏了」：%s" % (self.rot_rows,))

    def test_constant_propagation_is_what_keeps_false_positives_out(self):
        """把常量传播摘掉 ⇒ 变量里的活针会被判成"抽不出候选"⇒ 数就变了。

        这一格钉的是 R310 的第一版假正例（152 rot 里包含当天刚全 CAUGHT 的 r308/r309）：
        不做传播就"看不见针"，做了传播才有 700+ 可判臂。
        """
        with io.open(os.path.join(SYNTH, "mutate_r_synthlive.py"), encoding="utf-8") as h:
            tree = ha.ast.parse(h.read())
        cmap = ha.const_map(tree)
        self.assertIn(u"NEEDLE", cmap, u"常量传播没把 NEEDLE 解析出来 ⇒ 分箱又坏了")
        self.assertEqual([u"def main(argv):"], cmap[u"NEEDLE"])


class DeclarationHonestyTests(unittest.TestCase):
    """声明不许说谎：`NEEDLES[刀号]` 里写的针，必须是那一臂**真的**在用的那根。

    为什么要单独钉：新那一箱的可加总性完全建立在"声明 == 臂实际用的针"上。
    如果谁把 NEEDLES 写成另一串（比如复制粘贴错臂），尺会 happily 数出一堆"死针"或"活针"，
    而它量的已经不是刀了。这一格把声明拉回臂的候选集合里对账。
    """

    def _declared_tables(self):
        out = []
        for name in sorted(os.listdir(TABLES)):
            if not (name.startswith("mutate_r") and name.endswith(".py")):
                continue
            with io.open(os.path.join(TABLES, name), encoding="utf-8") as h:
                tree = ast.parse(h.read())
            cmap = ha.const_map(tree)
            nmap = ha.needle_map(tree, cmap)
            if nmap:
                out.append((name, tree, cmap, nmap))
        return out

    def test_there_are_declared_tables_and_not_only_the_fixtures(self):
        declared = self._declared_tables()
        self.assertGreaterEqual(len(declared), 2,
                                u"真表里一张都没声明 NEEDLES ⇒ 第二箱是空转的（现读 %d 张）" % len(declared))
        self.assertEqual(len(declared), ha.DECLARED_TABLES_CEILING,
                         u"声明面与棘轮不符 ⇒ 有人加/删了 NEEDLES 却没改上界")

    def test_every_declared_needle_is_a_real_candidate_of_that_arm(self):
        for name, tree, cmap, nmap in self._declared_tables():
            arms = {}
            for _var, elt in ha.arms_of(tree):
                # 刀号那一格只有 4~5 个字符，**过不了** `arm_candidates` 的 MIN_LEN=12，
                # 所以这里必须用 `arm_label_of` 取臂上的刀号 —— 与尺本体同一颗尺。
                # （这一格第一次跑就是栽在拿候选集找刀号上：`arms` 是空的，
                #   于是"声明悬空"的报错其实是**测试自己**在找错东西。）
                label = ha.arm_label_of(elt)
                if label:
                    arms.setdefault(label, []).extend(ha.arm_candidates(elt, cmap))
            for arm_id, needles in sorted(nmap.items()):
                self.assertIn(arm_id, arms,
                              u"%s 声明了 %s 的针，但没有任何一臂带着这个刀号 ⇒ 声明是悬空的（臂上找到的刀号：%s）"
                              % (name, arm_id, sorted(arms)[:8]))
                for needle in needles:
                    self.assertIn(needle, arms[arm_id],
                                  u"%s %s 声明的针不在那一臂的候选里 ⇒ 声明没在说这把刀：%r"
                                  % (name, arm_id, needle[:48]))


class RealRepoRatchetTests(unittest.TestCase):

    def test_the_ceilings_equal_the_live_readings(self):
        """双向棘轮：四个数都必须**恰好**等于现读值（只判一个方向 = 另一半没有牙）。"""
        info, rot_rows, _opaque = ha.scan()
        self.assertEqual([], ha.verdict(info),
                         u"现读 rot=%s 抽不出=%s 已声明死针=%s 已声明表=%s 与上界不符（明细 %s）"
                         % (info[u"rot"], info[u"opaque"], info[u"declared_dead"],
                            info[u"declared_tables"], rot_rows[:6]))
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
        # 新那一箱的两个方向也要各自响（否则"逐根数"这一箱可以靠不响蒙过去）
        self.assertIn(u"HIDDEN_DECLARED_DEAD_DRIFT",
                      [p.split()[0] for p in ha.verdict(dict(live, declared_dead=live[u"declared_dead"] + 1))])
        self.assertIn(u"HIDDEN_DECLARED_DEAD_DRIFT",
                      [p.split()[0] for p in ha.verdict(dict(live, declared_dead=live[u"declared_dead"] - 1))],
                      u"变少不响 ⇒ 把已声明死针清零（比如整箱被摘掉）也能蒙过去")
        self.assertIn(u"HIDDEN_DECLARED_TABLES_DRIFT",
                      [p.split()[0] for p in ha.verdict(dict(live, declared_tables=live[u"declared_tables"] - 1))],
                      u"悄悄删掉一张表的 NEEDLES = 把已判的臂退回下界箱 ⇒ 那是洗白，必须响")


if __name__ == u"__main__":
    unittest.main()
