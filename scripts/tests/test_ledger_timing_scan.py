#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`ledger_timing_scan.py` 的判据卷（R270 / BACKLOG 320）。

正负对照都喂**人造语料**；真仓库那一格只钉"抄值 = 0"这个结论。
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

import ledger_timing_scan as scan  # noqa: E402

PRODUCT_OK = 'final class DailyCopyLedger {\n    static let visibilityGrace: TimeInterval = 0.15\n}\n'
TEST_READS = ('final class T: XCTestCase {\n'
              '    func testX() {\n'
              '        pumpWindow(cell: "success-no-republish",\n'
              '                   milliseconds: Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000))\n'
              '    }\n}\n')
TEST_LITERAL = ('final class T: XCTestCase {\n'
                '    func testX() {\n'
                '        pumpWindow(cell: "success-no-republish", milliseconds: 600)\n'
                '        XCTAssertNil(x)\n'
                '    }\n}\n')


class ScanTests(unittest.TestCase):
    def test_a_copied_literal_window_is_named(self):
        grace, windows, copied = scan.scan(PRODUCT_OK, TEST_LITERAL)
        self.assertEqual('0.15', grace)
        self.assertEqual(1, len(windows))
        self.assertFalse(windows[0][2], '裸 600 却没读常量 ⇒ 必须判成没读')
        bad = scan.judge(grace, windows, copied)
        self.assertEqual(1, len(bad), '抄值那条要红：' + repr(bad))

    def test_a_window_that_reads_the_product_constant_is_clean(self):
        grace, windows, copied = scan.scan(PRODUCT_OK, TEST_READS)
        self.assertEqual(1, len(windows))
        self.assertTrue(windows[0][2])
        self.assertEqual([], scan.judge(grace, windows, copied))
        self.assertEqual(0, copied)

    def test_a_missing_product_constant_is_not_silently_zero(self):
        # 读不到真相时不许报"没问题"（R140 的空对账）：windows=0 也一样要红。
        bad = scan.judge(None, [], 0)
        self.assertEqual(1, len(bad), '常量声明被删掉 ⇒ 必须点名，而不是给一个空的 PASS')

    def test_a_comment_does_not_count_as_a_copied_value(self):
        text = TEST_READS.replace('    func testX() {',
                                  '    func testX() {\n        // 上一版把 0.15 抄在这里\n')
        grace, windows, copied = scan.scan(PRODUCT_OK, text)
        self.assertEqual(0, copied, '注释里的历史说明不是抄值（D-235 那一族假绿）')
        self.assertTrue(windows[0][2])

    def test_a_copied_value_outside_the_window_line_is_still_found(self):
        text = TEST_READS + '\nlet other = 0.15\n'
        grace, _, copied = scan.scan(PRODUCT_OK, text)
        self.assertEqual(1, copied, '抄值不只发生在 pumpWindow 那一行')

    def test_the_real_repository_has_no_copied_schedule_value(self):
        with io.open(scan.PRODUCT, encoding='utf-8') as h:
            product = h.read()
        with io.open(scan.TEST, encoding='utf-8') as h:
            test = h.read()
        grace, windows, copied = scan.scan(product, test)
        bad = scan.judge(grace, windows, copied)
        self.assertEqual([], bad, '320 还没做完：' + repr(bad))
        self.assertGreaterEqual(len(windows), 1, '一个窗口都没扫到 ⇒ 这把尺在量空气')
        self.assertEqual('0.15', grace)


class CommandLineTests(unittest.TestCase):
    def test_missing_file_fails_instead_of_reporting_zero(self):
        self.assertEqual(1, scan.main(['--product', os.path.join(SCRIPTS, 'nope.swift'),
                                       '--test', scan.TEST]))

    def test_the_summary_line_has_the_shape_the_ledger_parses(self):
        import subprocess
        out = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'ledger_timing_scan.py')],
                             stdout=subprocess.PIPE, cwd=SCRIPTS)
        line = out.stdout.decode('utf-8', 'replace').strip().splitlines()[0]
        self.assertRegex(line, r'^TIMING_SCAN product_grace=[0-9.]+ windows=\d+ 读常量=\d+ 抄值=\d+ 判=PASS$')
        self.assertEqual(0, out.returncode, line)

    def test_the_tool_derives_its_repo_root_instead_of_hardcoding_it(self):
        with io.open(os.path.join(SCRIPTS, 'ledger_timing_scan.py'), encoding='utf-8') as h:
            source = h.read()
        self.assertNotIn('/Users/', source)


if __name__ == '__main__':
    unittest.main()
