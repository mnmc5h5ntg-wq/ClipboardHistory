#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`ci_read.py` 的断言红计数：两种形状都要数到（R105 / 一次真实的漏数）。

起因：run 38975204376 里那一跑有六行红，而这一格报的是"行=4 去重后=2"——
因为计数器只认 `XCTAssert…failed`，**裸 `XCTFail` 的行里没有这个词**。
后果不是"数字小一点"：我新写的那条判据在 runner 上整条失败，
而读数工具报"通道没有一行"（那半句是对的）同时报"只有 2 条红"（这半句让我以为没有新红）。
⇒ 一个只数自己认识的形状的红计数器，会把"新出现的那一类失败"归到"没有新失败"里去。
"""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "ci_read", Path(__file__).resolve().parents[1] / "ci_read.py")
ci_read = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci_read)

XCTASSERT = ('build-and-test\tSwift tests\t2026-10-16T22:36:23Z /Users/x/Harness.swift:10:1: '
             'error: -[S.T testFoo] : XCTAssertLessThanOrEqual failed: ("3") is greater than ("2") - 地板')
BARE_FAIL = ('build-and-test\tOffscreen frame capture\t2026-10-16T22:25:20Z '
             '/Users/x/Harness.swift:572: error: -[S.T testBar] : failed - light：搜索那一条带里一个墨像素都没有')
NOISE = 'build-and-test\tSwift tests\t2026-10-16T22:25:20Z Test Case "-[S.T testBaz]" passed (1.234 seconds).'


def rows():
    return [("build-and-test", "Swift tests", b.split("\t", 2)[2])
            for b in (XCTASSERT, BARE_FAIL, NOISE)]


class AssertionRedTests(unittest.TestCase):
    def test_both_shapes_are_counted(self):
        got = ci_read.assertion_reds(rows())
        self.assertEqual(2, len(got), "两种红各一条 ⇒ 计数器必须都数到：%r" % [g[:60] for g in got])
        self.assertTrue(any("XCTAssertLessThanOrEqual" in g for g in got))
        self.assertTrue(any("墨像素" in g for g in got), "裸 XCTFail 那一行必须被数到")

    def test_a_passing_line_is_not_a_red(self):
        self.assertEqual([], ci_read.assertion_reds([("j", "s", NOISE.split("\t", 2)[2])]))

    def test_the_real_run_shape_is_not_vacuous(self):
        """正对照：把裸 XCTFail 那一行删掉，计数必须掉到 1（否则这条测试什么都没判）。"""
        kept = [r for r in rows() if "XCTAssert" in r[2]]
        self.assertEqual(1, len(ci_read.assertion_reds(kept)))


if __name__ == "__main__":
    unittest.main()
