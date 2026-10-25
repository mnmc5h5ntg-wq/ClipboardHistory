#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""§8 的行必须由**现在的**验证器打印（R352 / BACKLOG 397）。

背景：`ledger_rows.py` 的 ROWS 曾经要 `BUILD_EXIT` / `TEST_EXIT` / `CAPTURE_EXIT` / … / `VERIFY_OK`
十二个键，而 `scripts/round_verify.sh` 早就只打一行 `ROUND_VERIFY …=`。那十二格因此**长期**是
"!! 日志里没有这一格"——洞是真的，成因是那套多步验证器已退役。R352 把十二格退役、只留这一行。

这一格判两件事：
  ① 每一行 ROWS 里出现的 `KEY=` 名字，都必须出现在 `round_verify.sh` 最后那行 `ROUND_VERIFY` 里
     （**单一来源**：验证器不打的名字不许进表）；
  ② 退役那件事必须带着 BACKLOG 编号（`397`）写在表上方 —— 名字消失而不留出处 = 下一次没人知道为什么。
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ROWS_PY = os.path.join(ROOT, u".scratch", "motion-audit-2", "ledger_rows.py")
VERIFY = os.path.join(ROOT, u"scripts", "round_verify.sh")


def numbers_in(pattern):
    # 验证器那一行用的是**小写**键（`build_warnings=… swift_failures=…`）；表的正则里是裸字面量。
    return set(re.findall(r"([A-Za-z][A-Za-z0-9_]+)=", pattern))


class LedgerRowsKeys(unittest.TestCase):
    def test_every_row_key_is_printed_by_the_verifier(self):
        rows_src = io.open(ROWS_PY, encoding=u"utf-8").read()
        ver_src = io.open(VERIFY, encoding=u"utf-8").read()
        # 两处 `echo "ROUND_VERIFY …"`：早退那一行（ABORTED_AT_WARNING_GATE）与总结论行。
        # 取**最后**一处当键的单一来源；早退那行另算一种出口，不并进键名（它只带 exit=）。
        final = [l for l in ver_src.splitlines() if u"ROUND_VERIFY " in l and u"echo" in l]
        self.assertGreaterEqual(len(final), 1, u"验证器里一行 `ROUND_VERIFY` 都没有 ⇒ 这把尺没有对象")
        printed = numbers_in(final[-1])
        self.assertGreaterEqual(len(printed), 8, u"那一行读到的键太少（%d）⇒ 这把尺没对上对象" % len(printed))
        # 表里每一行：要么是通配（`.*` 收尾、没有硬编码键），要么它的键全在验证器那一行里
        pats = re.findall(r"r\"(\^[^\"]+)\"", rows_src)
        self.assertGreater(len(pats), 0, u"一行 ROWS 都没扫到")
        bad = []
        for pat in pats:
            keys = numbers_in(pat)
            if not keys:
                continue
            missing = keys - printed
            if missing:
                bad.append((pat[:40], sorted(missing)))
        self.assertEqual([], bad, u"这些行的键不在 `round_verify.sh` 的总结论行里：%s" % bad)

    def test_retirement_cites_a_backlog_number(self):
        rows_src = io.open(ROWS_PY, encoding=u"utf-8").read()
        head = rows_src[:rows_src.index(u"ROWS = [")]
        tail = rows_src[rows_src.index(u"ROWS = ["):]
        window = head[-1200:] + tail[:1200]
        self.assertIn(u"BACKLOG 397", window,
                      u"十二格退役这件事必须带 BACKLOG 编号（397），否则下一位读者不知道它们去哪了")


if __name__ == u"__main__":
    unittest.main()
