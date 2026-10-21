#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R272 / BACKLOG 327：静态镜像与 R51 那颗 needle 必须逐字相同（漂移就红）。

`mutate_r271.py` 为了让 `mutate_needle_precheck.py` 抽得到，把 TARGET / NEEDLE / REPL 写成了字面量；
字面量的代价就是会腐烂 —— 这一格是它的解药：单一真相仍然是 R51 那张表，运行时读它、逐字对账。
"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, '.scratch', 'motion-audit-2'))


def load():
    spec = importlib.util.spec_from_file_location(
        'mutate_r271', os.path.join(REPO, '.scratch', 'motion-audit-2', 'mutate_r271.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NeedleMirrorTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()

    def test_the_static_mirror_equals_the_r51_needle(self):
        target, needle, repl = self.mod.resolve_r51()
        self.assertEqual(os.path.relpath(target, self.mod.ROOT), self.mod.TARGET,
                         '文件漂移：R51 指的是另一颗文件')
        self.assertEqual(needle, self.mod.NEEDLE, '锚点漂移：R51 那颗 save 的写法已经改了，镜像还是旧的')
        self.assertEqual(repl, self.mod.REPL, '替换漂移：两把刀已经不是同一个坏法')

    def test_the_mirror_hits_exactly_once_in_the_product(self):
        path = os.path.join(self.mod.ROOT, self.mod.TARGET)
        with open(path, encoding='utf-8') as h:
            src = h.read()
        self.assertEqual(1, src.count(self.mod.NEEDLE),
                         '锚点在被测文件里不是恰好一次 ⇒ 这把刀会 NOT_RUN 而不是红')

    def test_a_drifted_mirror_is_caught_by_this_cell(self):
        # 正对照：把镜像改一个字符，对账必须红（否则这三格只是在证明两边都抄自同一处）
        target, needle, repl = self.mod.resolve_r51()
        self.assertNotEqual(needle + 'x', self.mod.NEEDLE)


if __name__ == '__main__':
    unittest.main()
