#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""每一张变异表的汇总正则，都必须认得出**单数**的 XCTest 汇总行（R346 / BACKLOG 422）。

为什么要有它（R345 现读）：`mutate_r345.py` 第一次跑就 `PRECHECK_FAILED` —— 两个单格各只跑 1 个用例，
XCTest 打的是 `Executed 1 test, with 0 failures`（**单数**），而表里的正则写的是 `Executed (\\d+) tests,`
⇒ 没匹配 ⇒ 被当成"编译没过 / 根本没跑"⇒ **假红**。R346 现读：55 张表里有 9 张是这种形状。

判法（对每一张表都做，不是挑一张）：把表里所有含 `Executed (` 的字符串常量当正则编译，
喂两条**真实形状**的汇总行 —— 单数与复数 —— 两条都必须匹配到。判据不读表名、不白名单：
新写的表只要正则写错，这一格就红。
"""
import ast
import glob
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)          # scripts/
REPO = os.path.dirname(ROOT)
TABLES = sorted(glob.glob(os.path.join(REPO, ".scratch", "motion-audit-2", "mutate_*.py")))

SINGULAR = u"Test Case '-[X.Class case]' failed: Executed 1 test, with 0 failures (0 unexpected) in 0.1 (0.1) seconds"
PLURAL = u"Executed 9 tests, with 1 failure (0 unexpected) in 0.1 (0.1) seconds"


class MutationSummaryRegex(unittest.TestCase):
    def test_every_table_recognises_both_summary_shapes(self):
        self.assertGreaterEqual(len(TABLES), 40, u"表的地板：现读只有 %d 张，扫错目录了？" % len(TABLES))
        blind = []
        checked = 0
        for path in TABLES:
            src = io.open(path, encoding=u"utf-8").read()
            pats = [n.value for n in ast.walk(ast.parse(src))
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    # 只认**以汇总行开头**的那条常量：刀里的 needle 也会嵌着 "Executed ("（r262 那一格），
                    # 那是被变异进产品的源码行，不是运行器的汇总正则。
                    and n.value.lstrip().startswith(u"Executed (")]
            for s in pats:
                rx = re.compile(s)
                checked += 1
                if not rx.search(SINGULAR) or not rx.search(PLURAL):
                    blind.append((os.path.basename(path), s[:48]))
        self.assertGreater(checked, 0, u"一条 `Executed (` 正则都没扫到 ⇒ 这把尺没有对象")
        self.assertEqual([], blind,
                         u"这些表的汇总正则认不出单数（或复数）形状 ⇒ 单格只有一个用例时会被判成'没解析到 ⇒ 红'：%s"
                         % (u"; ".join(u"%s:%s" % b for b in blind),))


if __name__ == u"__main__":
    unittest.main()
