# -*- coding: utf-8 -*-
"""R594 靶 2 / BACKLOG 668：判的是**守卫自己**——那段"交给下一轮的预测"必须能被真调用。

来历都是本仓库自己栽过的：R593 那一段里两条 lambda 举着只定义在 `main()` 局部的名字
（下一轮一调用就 `NameError`，而没有任何守卫报过，因为那段只被读出来贴进台账）；
R590/R592 两次把"那一行没印出来"读成"预测命中"（判法在空输入上返回 True）。
"""
from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import prediction_block_guard as pbg  # noqa: E402

GOOD = u'''# -*- coding: utf-8 -*-
KNOWN = (u"testSomethingFloor",)
PREDICTIONS_R999 = [
    {u"主张": u"新步骤第一次有读数",
     u"判法": lambda g: any(l.startswith(u"BUNDLE_CONTENT_GATE_RESULT=ok") for l in g),
     u"通道": u"那一步的 stdout",
     u"取处": u"步骤正文"},
    {u"主张": u"红名集合不超出那一条",
     u"判法": lambda g: bool(g) and all(any(n in l for n in KNOWN) for l in g),
     u"通道": u"--log-failed 的红名行",
     u"取处": u"步骤正文"},
]
'''


class Writer(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="r594-predblock-")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def write(self, body, name="ci_status_r999.py"):
        path = os.path.join(self.dir, name)
        io.open(path, "w", encoding="utf-8").write(body)
        return path

    def problems(self, body):
        path = self.write(body)
        key, block, err = pbg.load_block(path)
        if err:
            return [err]
        return [p for e in block for p in pbg.judge_entry(e)]


class BlockLoadingTest(Writer):
    def test_good_block_has_no_problems_and_the_constants_come_with_it(self):
        path = self.write(GOOD)
        key, block, err = pbg.load_block(path)
        self.assertIsNone(err, err)
        self.assertEqual(u"PREDICTIONS_R999", key, u"要取**最新**那一段（现读，不靠位置猜）")
        self.assertEqual(2, len(block))
        self.assertEqual([], [p for e in block for p in pbg.judge_entry(e)])

    def test_missing_block_is_red_not_green(self):
        problems = self.problems(u"# -*- coding: utf-8 -*-\nX = 1\n")
        self.assertEqual(1, len(problems), u"读不到预测块必须红：%s" % problems)
        self.assertIn(u"名单为空", problems[0])

    def test_broken_module_is_reported_not_swallowed(self):
        problems = self.problems(u"this is not python ((\n")
        self.assertIn(u"载入脚本就崩", problems[0])

    def test_reference_to_a_name_that_only_lives_in_main_is_caught(self):
        # 这就是 R593 留下的形状：判法引用 `main()` 里的局部名 ⇒ 下一轮一调用就 NameError。
        body = (u"# -*- coding: utf-8 -*-\n"
                u"def main():\n    known = (u\"x\",)\n"
                u"PREDICTIONS_R999 = [{u\"主张\": u\"引用局部名\",\n"
                u"  u\"判法\": lambda g: any(n in l for n in known),\n"
                u"  u\"通道\": u\"stdout\", u\"取处\": u\"正文\"}]\n")
        problems = self.problems(body)
        self.assertTrue(problems, u"引用不存在的名字必须被抓到")
        self.assertIn(u"NameError", u" ".join(problems))


class TeethTest(Writer):
    def test_vacuous_on_empty_is_red(self):
        body = (u"# -*- coding: utf-8 -*-\n"
                u"PREDICTIONS_R999 = [{u\"主张\": u\"恒真\",\n"
                u"  u\"判法\": lambda g: all(u\"k\" in l for l in g),\n"
                u"  u\"通道\": u\"stdout\", u\"取处\": u\"正文\"}]\n")
        problems = self.problems(body)
        self.assertTrue(any(u"absence" in p for p in problems),
                        u"空输入判 True = 把没读到写成命中：%s" % problems)

    def test_hardcoded_true_is_red_twice(self):
        entry = {u"主张": u"坐死", u"判法": lambda g: True,
                 u"通道": u"stdout", u"取处": u"正文"}
        problems = pbg.judge_entry(entry)
        self.assertEqual(2, len(problems), u"空输入与无关输入两向都要响：%s" % problems)

    def test_missing_any_of_the_four_cells_is_named(self):
        for cell in (u"主张", u"判法", u"取处", u"通道"):
            entry = {u"主张": u"x", u"判法": lambda g: bool(g),
                     u"通道": u"stdout", u"取处": u"正文"}
            del entry[cell]
            problems = pbg.judge_entry(entry)
            self.assertTrue(any(cell in p for p in problems),
                            u"缺「%s」那一格必须点名：%s" % (cell, problems))

    def test_crash_on_absent_input_is_a_problem_not_a_pass(self):
        entry = {u"主张": u"max 空序列",
                 u"判法": lambda g: max(int(l) for l in g) > 3,
                 u"通道": u"stdout", u"取处": u"正文"}
        problems = pbg.judge_entry(entry)
        self.assertTrue(any(u"崩" in p for p in problems), u"喂空就崩要红：%s" % problems)


class LiveBlockTest(unittest.TestCase):
    """盘上那一份**必须**被真判一次（R579/R580 那一课：只测正则不测流水线的对照是假对照）。"""

    def test_the_real_handoff_block_passes_the_guard(self):
        path = pbg.newest_block_file()
        self.assertIsNotNone(path, u"盘上读不到任何 ci_status_r*.py ⇒ 交接通道没有对象")
        rc = pbg.main([u"--file", path])
        self.assertEqual(0, rc, u"交给下一轮的那一段没过守卫（红话在上面那几行）：%s" % path)

    def test_selftest_controls_all_fire(self):
        self.assertEqual(0, pbg.main([u"--selftest", u"--file", pbg.newest_block_file()]),
                         u"守卫自己的合成对照没过 ⇒ 它红了也不能算盘上那一段过了")
