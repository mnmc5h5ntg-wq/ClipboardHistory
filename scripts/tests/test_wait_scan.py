#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`wait_scan.py` 的判据卷（R268 / BACKLOG 318）。

正负对照都喂**人造语料**（把被搜的串从被测文本里拼出来，R64 那条规矩），
真仓库那一格只判名册，不重复人造语料已经判过的形状。
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

import wait_scan  # noqa: E402


class FindingsTests(unittest.TestCase):
    def test_a_bare_wall_clock_bet_is_named_with_its_test(self):
        text = '\n'.join([
            'final class ThingTests: XCTestCase {',
            '    func testWaiting() throws {',
            '        pump' + 'Main(seconds: 0.8)',
            '        XCTAssertNil(subject.lastWriteError)',
            '    }',
            '}',
        ])
        bets, steps, untils = wait_scan.findings(text)
        self.assertEqual(1, len(bets), '固定挂钟赌注必须数出来：' + repr(bets))
        self.assertEqual('testWaiting', bets[0][0], '要能点名它住在哪个测试里，否则名册没法对账')
        self.assertEqual('wall_clock_bet', bets[0][1])
        self.assertEqual((0, 0), (steps, untils))

    def test_a_literal_sleep_is_the_other_kind_of_bet(self):
        bets, _, _ = wait_scan.findings('    func testX() { Thread.sleep(for' +
                                        'TimeInterval: 0.6) }')
        self.assertEqual(['testX'], [b[0] for b in bets])
        self.assertEqual('literal_sleep', bets[0][1])

    def test_a_named_constant_sleep_is_a_poll_step_not_a_bet(self):
        # `ArchiveReloadWait.pollInterval` 那种：形状一样，但它跑在 while 条件里，
        # 上限由轮询次数签，所以不许被这把尺当成赌注。
        bets, _, _ = wait_scan.findings(
            '    func testY() { Thread.sleep(forTimeInterval: Wait.pollInterval) }')
        self.assertEqual([], bets, '具名常量被读成赌注 ⇒ 名册会红在它自己的既有轮询上')

    def test_a_comment_does_not_feed_the_scanner(self):
        bets, steps, _ = wait_scan.findings(
            '        // 以前这里是 pumpMain(seconds: 0.4)，现在改成轮询\n'
            '        // Thread.sleep(forTimeInterval: 0.6) 也不能回来\n')
        self.assertEqual([], bets, '注释里的历史说明不是调用点（D-235 那一族假绿）')

    def test_a_url_inside_a_string_does_not_cut_the_line(self):
        # 朴素的 `split('//')` 会把这行切成 `let s = "https:`，
        # 于是**写在后面的那处赌注**永远数不到 —— 尺要在反方向有牙。
        line = '        let s = "https://example.com/x"  pump' + 'Main(seconds: 0.2)'
        self.assertIn('pumpMain', wait_scan.strip_comment(line))
        bets, _, _ = wait_scan.findings(line)
        self.assertEqual(1, len(bets), '字符串里的 // 不许把行截断')

    def test_a_declaration_is_not_a_call_site(self):
        bets, steps, untils = wait_scan.findings('\n'.join([
            '    private func pump' + 'Main(seconds: TimeInterval) {',
            '    private func pumpRunLoop' + 'Step(seconds: TimeInterval) {',
            '    private func poll' + 'Until(cell: String) {',
        ]))
        self.assertEqual((0, 0, 0), (len(bets), steps, untils),
                         '把 helper 起成两个名字之后，数错声明就会让尺红在自己的定义上')

    def test_the_two_shapes_have_two_names(self):
        _, steps, untils = wait_scan.findings('\n'.join([
            '        while !done, Date() < deadline { pumpRunLoop' + 'Step(seconds: 0.05) }',
            '        let fired = poll' + 'Until(cell: "x") { true }',
        ]))
        self.assertEqual(1, steps)
        self.assertEqual(1, untils)


class RosterTests(unittest.TestCase):
    def test_the_roster_is_bidirectional(self):
        bets = [('A.swift', 'testKept', 'literal_sleep', 12)]
        unregistered, stale = wait_scan.judge(
            bets, windows=[('A.swift', 'testKept', '正面证人在同格'),
                           ('B.swift', 'testGone', '已经删掉的格子')])
        self.assertEqual([], unregistered)
        self.assertEqual(1, len(stale), '名册里那格已经不在了也必须红（R227 同族）')

    def test_an_unregistered_bet_is_named_not_silently_allowed(self):
        unregistered, stale = wait_scan.judge(
            [('C.swift', 'testNew', 'wall_clock_bet', 3)],
            windows=[('D.swift', 'testOther', '不相干')])
        self.assertEqual(1, len(unregistered))
        self.assertEqual(1, len(stale))

    def test_a_window_living_outside_the_scanned_root_is_not_stale(self):
        # R269 现读：把尺指向 Sources/ 时，名册里那格（住在 Tests/）一度被报成"名册失配=1"。
        # 那是作用域坏了，不是账坏了 ⇒ 名册只在**这次走到的文件**里对账。
        unregistered, stale = wait_scan.judge([], windows=[('Tests.swift', 'testX', '窗口')],
                                              present={'Other.swift'})
        self.assertEqual(([], []), (unregistered, stale))
        unregistered, stale = wait_scan.judge([], windows=[('Tests.swift', 'testX', '窗口')],
                                              present={'Tests.swift'})
        self.assertEqual(1, len(stale), '文件在这次扫描里、格子却没了 ⇒ 仍要红')

    def test_the_product_sources_scan_clean(self):
        # 319：产品侧到底有没有「睡一段挂钟等异步产物」的形状 —— 现读，不是推理。
        root = os.path.join(wait_scan.REPO, 'ClipboardHistory', 'Sources')
        self.assertTrue(os.path.isdir(root), '产品源码目录不在 ⇒ 这一格无从判定')
        bets, steps, untils = wait_scan.scan(root)
        unregistered, stale = wait_scan.judge(bets, present=set(
            os.path.basename(x) for x in wait_scan.swift_files(root)))
        self.assertEqual([], unregistered, '产品里有未登记的固定挂钟等待：' + repr(unregistered))
        self.assertEqual([], stale, '名册漏进了产品扫描里：' + repr(stale))
        self.assertEqual(0, len(bets), '产品侧现读赌注颗数变了，要把这一格的期望改成现读值并写明成因')

    def test_the_real_repository_matches_the_roster_exactly(self):
        bets, steps, untils = wait_scan.scan(wait_scan.DEFAULT_ROOT)
        unregistered, stale = wait_scan.judge(bets)
        self.assertEqual([], unregistered,
                         '还有没登记的固定挂钟等待：' + repr(unregistered))
        self.assertEqual([], stale, '名册失配：' + repr(stale))
        # 颗数钉死（D-250：间隙用 assertEqual，不用 assertLessEqual）
        self.assertEqual(1, len(bets), '观察窗口颗数：' + repr(bets))
        self.assertEqual(2, steps, '轮询步进调用点颗数')
        self.assertEqual(4, untils, 'pollUntil 调用点颗数')


class CommandLineTests(unittest.TestCase):
    def test_missing_root_fails_instead_of_reporting_zero(self):
        # `X=0` 形式的通过是空对账（R140）：根目录不存在时不许 exit 0。
        code = wait_scan.main(['--root', os.path.join(SCRIPTS, 'no_such_dir_at_all')])
        self.assertEqual(1, code)

    def test_the_summary_line_has_the_shape_the_ledger_parses(self):
        import subprocess
        out = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'wait_scan.py')],
                             stdout=subprocess.PIPE, cwd=SCRIPTS)
        text = out.stdout.decode('utf-8', 'replace')
        line = [l for l in text.splitlines() if l.startswith('WAIT_SCAN ')]
        self.assertEqual(1, len(line), '结论行要恰好一行：' + repr(text))
        self.assertRegex(line[0], wait_scan.LINE_SHAPE)
        self.assertEqual(0, out.returncode, line[0])

    def test_the_tool_derives_its_repo_root_instead_of_hardcoding_it(self):
        with io.open(os.path.join(SCRIPTS, 'wait_scan.py'), encoding='utf-8') as handle:
            source = handle.read()
        self.assertNotIn('/Users/', source, 'runner 上这会把尺换成 FileNotFoundError')


if __name__ == '__main__':
    unittest.main()
