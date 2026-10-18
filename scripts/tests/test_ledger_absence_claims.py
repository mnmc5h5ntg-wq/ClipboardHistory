# -*- coding: utf-8 -*-
"""清账表里"靠缺席立论"的那些格，其证据必须仍然成立（R165）。

这一支防的是一件很具体的事：动效账里有一大类结论是"这一屏没有加载态 / 这层没有禁用分支"，
它们的证据是**某关键字在某文件里 0 次**。散文里的"实测 0 处"不会自己保鲜 ——
哪天有人真加了那条分支，表里那格就成了谎话，而**没有一格会红**。
所以这里把缺席声明变成会红的格子，并给它自己配正对照（假声明必须被抓出来）。
"""
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ledger_absence_claims as mod


def write_table(rows, directory):
    path = os.path.join(directory, 'table.json')
    with io.open(path, 'w', encoding='utf-8') as handle:
        json.dump({'rows': rows}, handle, ensure_ascii=False)
    return path


class LedgerAbsenceClaimsTests(unittest.TestCase):
    def setUp(self):
        self.rows = mod.load_rows()
        self.claims = mod.parse_claims(self.rows)

    def test_the_committed_table_carries_a_roster(self):
        self.assertGreaterEqual(len(self.claims), 10,
                                '只解析到 %d 条缺席声明 ⇒ 文法漂了或表被清空，这一支就空转了' % len(self.claims))

    def test_every_claim_still_holds(self):
        problems = mod.check(self.claims)
        self.assertEqual([], problems[:6],
                         '%d 条"靠缺席立论"的格子里有不成立的：先重新判那一格，再改表' % len(problems))

    def test_parser_is_strict_about_the_grammar(self):
        # 松散写法（有空格、用中文逗号）不算声明 —— 宁可不认，也不要把散文当证据
        loose = [{'surface': 'A', 'state': '加载', 'evidence': u'缺席: X.swift = ProgressView'}]
        self.assertEqual([], mod.parse_claims(loose))

    def test_a_stale_claim_is_named_not_swallowed(self):
        """正对照：声明一个**确实存在**的标识符 ⇒ 必须报问题（否则这一支是恒真的门）。"""
        claims = [('A', '加载', 'scripts/ledger_absence_claims.py', 'def main')]
        problems = mod.check(claims)
        self.assertEqual(1, len(problems), problems)
        self.assertIn(u'理由过期', problems[0])
        self.assertIn('A × 加载', problems[0])

    def test_an_unresolvable_pointer_is_named(self):
        problems = mod.check([('B', '禁用', 'Sources/NoSuchFile.swift', 'disabled')])
        self.assertEqual(1, len(problems), problems)
        self.assertIn(u'解析不到', problems[0])

    def test_empty_roster_is_red_not_green(self):
        """名单为空 = 红（R99）：解析器坏掉时不许安静地给 0 条然后全绿。"""
        directory = tempfile.mkdtemp(prefix='r165-')
        original = mod.TABLE
        try:
            mod.TABLE = write_table([{'surface': 'A', 'state': '加载', 'evidence': 'no claim here'}],
                                    directory)
            # argv 必须显式给空列表：不传的话 argparse 会去读 sys.argv（unittest 的参数会把它惹红）
            self.assertEqual(1, mod.main([]), '表里没有一条缺席声明时 main 必须给非 0')
        finally:
            mod.TABLE = original

    def test_the_committed_table_is_the_generators_own_output(self):
        """表只能由生成器写（共享登记表的老规矩）：手改 JSON 会在这里红。"""
        import subprocess
        root = os.path.dirname(os.path.dirname(os.path.abspath(mod.__file__)))
        generator = os.path.join(root, '.scratch', 'motion-audit-2', 'make_surface_ledger.py')
        if not os.path.exists(generator):
            self.skipTest('生成器不在这台机器上（.scratch 未入库）⇒ 这一格无从对照')
        before = io.open(mod.TABLE, encoding='utf-8').read()
        subprocess.run([sys.executable, generator], cwd=root, check=True,
                       capture_output=True)
        after = io.open(mod.TABLE, encoding='utf-8').read()
        self.assertEqual(before, after,
                         '已提交的表与生成器的输出不一致 ⇒ 有人手改了 JSON，改回生成器')


if __name__ == '__main__':
    unittest.main()
