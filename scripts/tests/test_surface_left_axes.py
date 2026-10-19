#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`scripts/surface_left_axes.py` 的电池（R209 看图那一轮）。

规矩：一把新尺进仓库，必须带"已知答案的对照"，而且**这一支不许自己造对照** ——
它跑的就是尺自带的 `--self-test`（真值表在尺里面，改坏判据会当场红）。
另两格钉的是"不许空对账"：帧不在 ⇒ 必须 NOT_RUN 而不是绿。
"""
import io
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, 'scripts', 'surface_left_axes.py')
SHOTS = '/tmp/shots_r207'


def run(*args, **kw):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    env.update(kw.pop('env', {}))
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


class CiExitTests(unittest.TestCase):
    """R210 / BACKLOG 234：接进 CI 之后，"该红"与"该跳"必须分得开 —— 两侧都要有证人。

    为什么单独钉这一族：无头 runner 的高窗只画一条下沿带（BACKLOG 201），
    把环境缺席报成产品结论就是 R154 那朵假红的形状；而反过来把真红也吞成 skipped，
    这一步就变成一条永远绿的装饰。两个方向各一格，谁也不许替谁签字。
    """

    def _tmp_frames(self, images):
        import tempfile, shutil
        from PIL import Image
        d = tempfile.mkdtemp(prefix='left-axes-')
        self.addCleanup(shutil.rmtree, d)
        for name, im in images.items():
            im.save(os.path.join(d, name))
        return d

    def test_real_frames_pass_and_report_ok(self):
        if not os.path.isdir(SHOTS):
            print(u'SKIPPED(本机)：帧目录不在 ⇒ 这一格 NOT-RUN')
            self.skipTest(u'%s 不在盘上' % SHOTS)
        code, out = run('--shots', SHOTS, '--ci')
        self.assertEqual(0, code, out)
        self.assertIn(u'LEFT_AXIS_CI verdict=ok', out)

    def test_absent_frames_are_skipped_not_red(self):
        d = self._tmp_frames({})
        code, out = run('--shots', d, '--ci')
        self.assertEqual(0, code, u'缺席不该让 CI 红：\n%s' % out)
        self.assertIn(u'LEFT_AXIS_CI verdict=skipped', out)
        self.assertIn(u'not_run=5', out, u'缺席要写成读数，不许只说"跳过了"：\n%s' % out)

    def test_missing_pillow_is_unavailable_not_red(self):
        code, out = run('--shots', SHOTS, '--ci', env={'SURFACE_LEFT_AXES_FORCE_NO_PIL': '1'})
        self.assertEqual(0, code, out)
        self.assertIn(u'LEFT_AXIS_CI verdict=unavailable', out)

    def test_a_real_violation_still_goes_red(self):
        """正对照的反面：造一张药丸只往右缩的帧 ⇒ 这一步必须真的能让 CI 红。"""
        from PIL import Image
        im = Image.new('RGB', (840, 600), (30, 30, 30))
        px = im.load()
        for y in range(104, 148):
            for x in range(74, 796):        # 左缘被推走 30px ⇒ 不对称
                px[x, y] = (60, 60, 60)
        st = Image.new('RGB', (1440, 1080), (30, 30, 30))
        sp = st.load()
        for y0 in (246, 296, 666):
            for y in range(y0, y0 + 28):
                for x in range(296, 1357):
                    sp[x, y] = (230, 230, 230)
        for y in range(326, 352):
            for x in range(296, 1117):
                sp[x, y] = (60, 120, 220)
        d = self._tmp_frames({u'quickpick-list-420x300-dark.png': im,
                              u'settings-stats-populated-720x540-dark.png': st})
        code, out = run('--shots', d, '--ci')
        self.assertEqual(1, code, u'真红被判成绿了（这一步会变成装饰）：\n%s' % out)
        self.assertIn(u'LEFT_AXIS_CI verdict=red', out)
        self.assertIn(u'ASYMMETRIC', out)


class WorkflowWiringTests(unittest.TestCase):
    """接线本身也要有证人：这一步存在、且**不是** continue-on-error（否则接了等于没接）。"""

    YAML = os.path.join(ROOT, '.github', 'workflows', 'ci.yml')

    def test_ruler_step_exists_and_has_teeth(self):
        with io.open(self.YAML, encoding='utf-8') as h:
            t = h.read()
        self.assertIn(u'Surface left-axis ruler', t)
        i = t.index(u'Surface left-axis ruler')
        block = t[i:i + 600]
        self.assertNotIn(u'continue-on-error', block.split(u'- name:')[0] + block.split(u'\n')[0],
                         u'尺那一步不许 continue-on-error：红了也不算数')
        self.assertIn(u'--ci', block)

    def test_pillow_install_is_allowed_to_fail(self):
        with io.open(self.YAML, encoding='utf-8') as h:
            t = h.read()
        i = t.index(u'Pillow for the frame rulers')
        self.assertIn(u'continue-on-error: true', t[i:i + 300],
                      u'装库这一步失败不该红整条流水线 —— 缺席由尺自己报成 unavailable')


if __name__ == '__main__':
    unittest.main()
