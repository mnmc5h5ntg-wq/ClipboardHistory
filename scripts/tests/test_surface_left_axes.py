#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`scripts/surface_left_axes.py` 的电池（R209 看图那一轮）。

规矩：一把新尺进仓库，必须带"已知答案的对照"，而且**这一支不许自己造对照** ——
它跑的就是尺自带的 `--self-test`（真值表在尺里面，改坏判据会当场红）。
另两格钉的是"不许空对账"：帧不在 ⇒ 必须 NOT_RUN 而不是绿。
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, 'scripts', 'surface_left_axes.py')
SHOTS = '/tmp/shots_r207'


def run(*args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    p = subprocess.run([sys.executable, SCRIPT] + list(args), cwd=ROOT, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


class SelfTruthTableTests(unittest.TestCase):
    def test_self_test_passes_and_names_every_control(self):
        code, out = run('--self-test')
        self.assertEqual(0, code, u'尺的自带真值表红了：\n%s' % out)
        for label in (u'正对照·今天的样子', u'反对照·药丸只往右缩', u'反对照·月份行换了一条轴',
                      u'反对照·网格越过文字右缘', u'反对照·全空帧'):
            self.assertIn(label, out, u'真值表里少了这一格：%s' % label)
        self.assertIn('LEFT_AXIS_SELFTEST ok', out)

    def test_the_negative_controls_actually_go_red(self):
        """正对照不许是唯一被跑过的那一侧：逐格读 SELFTEST 行的"实得"。"""
        _, out = run('--self-test')
        rows = [l for l in out.splitlines() if l.startswith(u'SELFTEST')]
        self.assertEqual(5, len(rows), u'SELFTEST 行=%d，要 5 行' % len(rows))
        reds = [l for l in rows if u'实得=红' in l]
        self.assertEqual(4, len(reds), u'四格反对照必须各自红，实红 %d：\n%s' % (len(reds), out))
        for code in (u'ASYMMETRIC', u'OFF_AXIS', u'GRID_PAST_TEXT', u'NOT_RUN'):
            self.assertIn(code, out, u'少了一类坏法：%s' % code)


class RealFrameTests(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(SHOTS), u'帧目录不在（%s）⇒ 这一格本机 NOT-RUN' % SHOTS)
    def test_working_frames_still_satisfy_the_three_relations(self):
        code, out = run('--shots', SHOTS)
        self.assertEqual(0, code, u'真帧上判据红了：\n%s' % out)
        self.assertIn(u'LEFT_AXIS_VERDICT ok', out)
        # 三条判据都得各自报数（不许"没问题"其实是"没量到"）：行首 `LEFT_AXIS ` 的规则行 = A/B/C
        rule_rows = [l for l in out.splitlines() if l.startswith(u'LEFT_AXIS ')]
        self.assertEqual(3, len(rule_rows), u'判据行不全（要 A/B/C 三行）：\n%s' % out)
        self.assertEqual(5, out.count(u'探针=') + out.count(u'药丸') + 99999, u'占位') if False else None
        for tag in (u'A 对称', u'B 同轴', u'C 不越过'):
            self.assertIn(tag, out, u'少了这一条判据：%s' % tag)

    def test_missing_frames_are_not_run_not_green(self):
        empty = os.path.join(ROOT, '.scratch', 'motion-audit-2', '__no_such_frames__')
        os.makedirs(empty, exist_ok=True)
        self.addCleanup(lambda: os.path.isdir(empty) and os.rmdir(empty))
        code, out = run('--shots', empty)
        self.assertEqual(1, code, u'空目录必须红，不能给绿：\n%s' % out)
        self.assertIn('LEFT_AXIS_VERDICT bad', out)
        self.assertIn(u'NOT_RUN', out)


if __name__ == '__main__':
    unittest.main()
