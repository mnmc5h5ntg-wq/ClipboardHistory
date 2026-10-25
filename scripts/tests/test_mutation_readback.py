#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R362 / BACKLOG 426：刀的落刀回读判**预期 diff**，不判"替换串出现过几次"。

R350 的现场：替换串在文件别处本来就有 ⇒ `after.count(repl) == 1` 不成立，刀没落下去，
而跑器只能说"回读不匹配"（读起来像锚点坏了）。正确判据是
`after == before.replace(needle, repl)` 且 before 里 needle 恰好一次。
"""
import importlib.util
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / u".scratch" / u"motion-audit-2" / u"readback.py"


def load():
    spec = importlib.util.spec_from_file_location(u"readback_under_test", str(TOOL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SingleSubstitutionTests(unittest.TestCase):
    def test_exact_replacement_lands(self):
        tool = load()
        before = u"a = 1\nb = 2\nc = 3\n"
        self.assertTrue(tool.single_substitution_lands(before, u"b = 2", u"b = 9", u"a = 1\nb = 9\nc = 3\n"))

    def test_repl_appearing_elsewhere_does_not_block_the_knife(self):
        """R350 的形状：替换串在别处本来就有 —— 旧判法 `count(repl)==1` 在这里假红。"""
        tool = load()
        before = u"x = 0\ny = 0\nkeep = 0\n"
        # 把第二行改成一个**别处也出现**的串
        after = u"x = 0\nkeep = 0\nkeep = 0\n"
        self.assertEqual(2, after.count(u"keep = 0"))
        self.assertTrue(tool.single_substitution_lands(before, u"y = 0", u"keep = 0", after),
                        u"repl 全局出现两次，但盘上恰好是预期的那一份 ⇒ 必须放行")

    def test_an_extra_change_is_refused(self):
        tool = load()
        before = u"a = 1\nb = 2\n"
        after = u"a = 7\nb = 9\n"     # 第二处也被动了
        self.assertFalse(tool.single_substitution_lands(before, u"b = 2", u"b = 9", after))

    def test_no_change_is_refused(self):
        tool = load()
        before = u"a = 1\n"
        self.assertFalse(tool.single_substitution_lands(before, u"a = 1", u"a = 1", before),
                         u"变异文与原文相同 = 空刀，不算落刀")

    def test_ambiguous_or_empty_needle_is_refused(self):
        tool = load()
        before = u"a = 1\na = 1\n"
        self.assertFalse(tool.single_substitution_lands(before, u"a = 1", u"a = 2", before.replace(u"a = 1", u"a = 2", 1)))
        self.assertFalse(tool.single_substitution_lands(before, u"", u"x", u"x"))
        self.assertFalse(tool.single_substitution_lands(before, u"not-there", u"x", before))


if __name__ == u"__main__":
    unittest.main()
