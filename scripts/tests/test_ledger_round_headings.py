# -*- coding: utf-8 -*-
"""R574 / BACKLOG 653：七本台账里**逐字重复的轮次标题行**会红，而这一把尺自己不许空转。

存在的理由（同族第四次）：R573 写手补 U-2512 那一行时把 anchor 之后的整段抄了两遍，
`AGENT_UI_AUDIT.md` 从 15812 行涨到 31281 行。当时抓到它的是"U 号重复"那一格 ——
**碰巧在场的另一把尺**，而不是任何一把专门盯"同一轮标题出现两遍"的尺。
电池不扫这个，帧基线也不扫这个（台账不是像素）。

三条格子各管一件事：
1. 现读七本必须 0 重复，且解析到的标题数要够大（尺瞎了会安静地给 0 条然后全绿 ⇒ 用第 3 格钉）。
2. 正对照：往一份临时台账里塞一条**逐字相同**的标题 ⇒ 必须被抓出来并点名。
3. 合法形状不许被误判：`## 第 498 轮（…）` 与 `## 第 498 轮续一（…）`、`## Round 29 ·` 与
   `## Round 29d ·` 是不同的一行 ⇒ 按"轮次号相同"判会把它们读成重复（本轮第一次试写就犯了这个），
   这条格子钉的是"只判逐字相同"。
"""
import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ledger_round_headings as mod


class LedgerRoundHeadingsTests(unittest.TestCase):
    def write_book(self, directory, name, lines):
        path = os.path.join(directory, name)
        with io.open(path, 'w', encoding='utf-8') as handle:
            handle.write(u'\n'.join(lines) + u'\n')
        return path

    def test_live_books_have_no_verbatim_duplicate_heading(self):
        total, problems = mod.check(mod.REPO, mod.BOOKS)
        self.assertEqual([], problems[:6],
                         '%d 处逐字重复的 `## ` 标题：先分清是"同一轮写了续节"还是"补丁把整段抄了两遍"'
                         % len(problems))
        self.assertGreaterEqual(total, 1500,
                                '只解析到 %d 条标题 ⇒ 前缀漂了或名单被清空，这一支就空转了' % total)

    def test_forging_a_duplicate_line_is_caught(self):
        """正对照：塞一条逐字重复的轮次标题 ⇒ 必须红，并且点名是哪一本哪一行。"""
        directory = tempfile.mkdtemp(prefix='r574-')
        self.write_book(directory, 'a.md', [
            u'# 台账',
            u'## 第 573 轮（R574 · 2026-11-04 · U-2513…U-2520）：本轮的标题',
            u'- 正文一',
            u'## 第 573 轮（R574 · 2026-11-04 · U-2513…U-2520）：本轮的标题',
            u'- 正文二',
        ])
        total, problems = mod.check(directory, ['a.md'])
        self.assertEqual(1, len(problems), problems)
        self.assertIn(u'a.md', problems[0])
        self.assertIn(u'573', problems[0])
        self.assertEqual(2, int(total), '该书应有 2 条 `## ` 标题（同一对被抄了两遍）')

    def test_legal_continuation_headings_are_not_read_as_duplicates(self):
        """续节 / 带后缀的轮次是不同的一行 ⇒ 不许被读成重复（这条钉的是判法本身）。"""
        directory = tempfile.mkdtemp(prefix='r574-')
        self.write_book(directory, 'a.md', [
            u'## 第 498 轮（R499 · 2026-10-30 · 空轮 Round=0）：原节',
            u'## 第 498 轮续一（R499 续 · 2026-10-30）：录制帧底留白的相位分诊',
            u'## Round 29 · 判墨的尺补上"方向"',
            u'## Round 29d · 暗档侧栏那五行字是黑字黑底',
            u'### 不是二级标题的一行',
            u'### 不是二级标题的一行',
        ])
        total, problems = mod.check(directory, ['a.md'])
        self.assertEqual([], problems, problems)
        self.assertEqual(4, int(total), '三级标题不算对象（名单里只钉 `## `）')

    def test_empty_roster_is_red_not_green(self):
        directory = tempfile.mkdtemp(prefix='r574-')
        self.write_book(directory, 'a.md', [u'没有二级标题的一本书', u'- 只有散文'])
        original = mod.BOOKS
        try:
            mod.BOOKS = ['a.md']
            self.assertEqual(1, mod.main(['--root', directory]),
                             '一条标题都解析不到时 main 必须给非 0（R99：空名单不许给绿）')
        finally:
            mod.BOOKS = original

    def test_a_missing_book_is_named(self):
        directory = tempfile.mkdtemp(prefix='r574-')
        total, problems = mod.check(directory, ['no_such_ledger.md'])
        self.assertEqual(0.0, total)
        self.assertEqual(1, len(problems), problems)
        self.assertIn(u'读不到', problems[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
