#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 / BACKLOG 222：`scripts/heatmap_frame_levels.py`（热图真帧通道证人）的性质。

这支脚本存在的理由：判据量的是**离屏单格**，产品真帧里格子压在卡片材质上，
两条通道的逐档墨色相减偏在 **R 那一列**（R198 实测 6…21/255，G/B ≤1），
于是"最大通道差"这把尺在亮档最低那一格多报了 8/255（判据 25.41 对真帧 21，地板 18）。

钉四件事：
① 两颗尺的**矩阵常数必须一致**（跨运行时对账：从 Swift 源码里读出来比，不在这里抄第二份）；
② 中性灰是不动点（与 Swift 那条恒等式同一条，防的就是 R198 那个量纲 bug 的 python 版）；
③ 读不到输入必须 exit 2，**不许被读成通过**（R140 那一族：分母为 0 的"没问题"）；
④ 真帧那侧塌一档 / 偏差不再只压在 R 那一列 ⇒ 各自 exit 1 并点名是哪一档。
"""
import importlib.util
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPT = os.path.join(REPO, "scripts", "heatmap_frame_levels.py")
SWIFT = os.path.join(REPO, "ClipboardHistory", "Tests", "ClipboardHistoryAppTests",
                     "HeatmapHoverEvidenceTests.swift")
# 档位词表只有一份真值（R587 / 靶 B）。旧版这里自己写第二份 `('dark', 'light')`，
# 顺序还与判定侧相反 —— 而脚本又在第一个 stop 处就 return，于是"哪一档被点名"其实是**循环顺序**
# 决定的。本轮把两处一起修：词表一份、stop 不再短路（见 test_log_covering_only_one_appearance…）。
sys.path.insert(0, os.path.join(REPO, 'scripts'))
from tier_vocabulary import TIERS  # noqa: E402
TAGS = TIERS
RUNGS = [(243, 243, 243), (215, 232, 255), (180, 210, 255), (130, 180, 255), (59, 142, 255)]


def load_module():
    spec = importlib.util.spec_from_file_location("hfl_for_r201", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(args):
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONUTF8'] = '1'
    p = subprocess.run([sys.executable, SCRIPT] + args, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, env=env, cwd=REPO)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def ink(t):
    return ', '.join(str(v) for v in t)


def write_log(path, inks, before, after, tags=TAGS):
    """写一份**两档齐全**的判据日志（脚本要求两档都对得上，缺一档就是输入不全）。"""
    lines = []
    for tag in tags:
        for i in range(4):
            lines.append(u'HEAT_ADJACENT_CVD %s/1x b%d→b%d 像素=49 前墨=(%s) 后墨=(%s) '
                         u'模拟前=%.2f 模拟后=%.2f 保住=80%%'
                         % (tag, i, i + 1, ink(inks[i]), ink(inks[i + 1]), before[i], after[i]))
    io.open(path, 'w', encoding='utf-8').write(u'\n'.join(lines) + u'\n')


def write_strip(path, bg, rungs, cell=20, gap=6):
    """竖条帧：顶部一段 >30px 的背景（会被当夹具背景排掉）+ 5 格等高的格子。"""
    from PIL import Image
    h = 40 + len(rungs) * (cell + gap)
    im = Image.new('RGB', (60, h), bg)
    y = 40
    for c in rungs:
        for yy in range(y, y + cell):
            for xx in range(10, 50):
                im.putpixel((xx, yy), c)
        y += cell + gap
    im.save(path)


def steps_of(mod, rungs):
    b = [float(mod.maxdelta(rungs[i - 1], rungs[i])) for i in range(1, 5)]
    a = [float(mod.maxdelta(mod.deutan(rungs[i - 1]), mod.deutan(rungs[i]))) for i in range(1, 5)]
    return b, a


class MatrixParityTests(unittest.TestCase):

    def test_the_two_rulers_use_the_same_matrix(self):
        src = io.open(SWIFT, encoding='utf-8').read()
        parts = src.split('static func simulateDeuteranopia', 1)
        self.assertEqual(2, len(parts), '读不到 simulateDeuteranopia ⇒ 这颗对账尺的对象没了')
        seg = parts[1].split('\n    }', 1)[0]
        rows = re.findall(r'encodeSRGB\(([0-9.]+) \* lin\.([rgb]) \+ ([0-9.]+) \* lin\.([rgb])\)', seg)
        self.assertEqual(3, len(rows), 'Swift 那边只认出 %d 行系数（要 3）⇒ 它换了写法，这里要跟着改' % len(rows))
        # 必须按**通道**归位再比：Swift 那行写的是 `0.700 * lin.g + 0.300 * lin.r`（g 先写），
        # 直接按书写顺序取两个数会跟 python 侧的 (r, g) 顺序对不上 —— 第一版就是这么误报分叉的。
        got = []
        for c1, ch1, c2, ch2 in rows:
            coef = {'r': 0.0, 'g': 0.0}
            coef[ch1] = float(c1)
            coef[ch2] = float(c2)
            got.append((coef['r'], coef['g']))
        want = [tuple(row[:2]) for row in load_module().VIENOT_DEUTAN]
        self.assertEqual(want, got, '两颗尺的矩阵常数分叉了：python=%s swift=%s' % (want, got))

    def test_grey_is_a_fixed_point_on_the_python_side(self):
        mod = load_module()
        for v in (0, 64, 128, 200, 255):
            self.assertEqual((v, v, v), mod.deutan((v, v, v)),
                             u'中性灰过完模拟变了 ⇒ 行和不为 1 或某一路量纲没统一')

    def test_red_green_collapse_is_reproduced(self):
        mod = load_module()
        rg_raw = mod.maxdelta((255, 0, 0), (0, 255, 0))
        rg_sim = mod.maxdelta(mod.deutan((255, 0, 0)), mod.deutan((0, 255, 0)))
        by_sim = mod.maxdelta(mod.deutan((0, 0, 255)), mod.deutan((255, 255, 0)))
        self.assertLess(rg_sim, rg_raw, u'红绿分离没被压小 ⇒ 模拟没接电')
        self.assertLess(rg_sim, by_sim, u'红绿分离不比蓝黄小 ⇒ 这不是 deuteranopia')


class InputHygieneTests(unittest.TestCase):

    def test_missing_shots_dir_exits_two_not_zero(self):
        code, out = run(['--shots', os.path.join(tempfile.gettempdir(), 'no-such-shots-r201'),
                         '--judgment-log', SCRIPT])
        self.assertEqual(2, code, u'读不到帧却退 %s ⇒ 会被读成通过：%s' % (code, out[:200]))
        self.assertIn('HEAT_FRAME_INPUT_MISSING', out)

    def test_missing_judgment_log_exits_two(self):
        d = tempfile.mkdtemp(prefix='r201-shots-')
        code, out = run(['--shots', d, '--judgment-log', os.path.join(d, 'none.log')])
        self.assertEqual(2, code, out[:200])
        self.assertIn(u'判据日志', out)

    def test_log_covering_only_one_appearance_is_not_a_pass(self):
        """两档的帧都在、判据日志只覆盖一档 ⇒ 另一档必须被点名，且**与词表顺序无关**。

        R587 之前这一格只在 `('dark','light')` 那个顺序下成立：脚本在第一个 stop 处就 `return 2`，
        于是"缺席那一档被点名"依赖的是循环顺序而不是契约。本轮把词表收成一份真值（`('light','dark')`）
        时它当场变红 ⇒ 红得对，只是红在脚本身上（门是既有的这一格，不是我新加的）。
        现在两档各当一次"在场"，各要求对方被点名。
        """
        mod = load_module()
        b, a = steps_of(mod, RUNGS)
        for present in TIERS:
            absent = [t for t in TIERS if t != present][0]
            with self.subTest(日志覆盖=present):
                d = tempfile.mkdtemp(prefix='r201-one-')
                lg = os.path.join(d, 'j.log')
                for tag in TIERS:      # 帧两档都在 ⇒ 唯一缺的只有日志那一档（旧版是空目录，缺的是帧）
                    write_strip(os.path.join(d, 'heatmap-cell-strip-still-90x140-%s.png' % tag),
                                (255, 255, 255), RUNGS)
                write_log(lg, RUNGS, b, a, tags=(present,))
                code, out = run(['--shots', d, '--judgment-log', lg])
                self.assertEqual(2, code, out[:300])
                self.assertIn(absent, out,
                              u'日志只覆盖 %s 时，%s 那一档没被点名（顺序漏判）：%s' % (present, absent, out[:400]))
                self.assertIn(u'判据日志里没有 %s 那 4 对' % absent, out, out[:400])
                self.assertIn('HEAT_FRAME_VERDICT not-run=1', out,
                              u'一档输入不足却打出别的结论：%s' % out[:400])

    def test_help_runs(self):
        code, out = run(['--help'])
        self.assertEqual(0, code, out[:200])


class VerdictTests(unittest.TestCase):

    def setUp(self):
        try:
            from PIL import Image  # noqa F401
        except ImportError:
            raise unittest.SkipTest('PIL 不可用 ⇒ 造不出合成帧，这一格记 NOT-RUN（不是通过）')
        self.d = tempfile.mkdtemp(prefix='r201-verdict-')
        self.mod = load_module()

    def both_strips(self, rungs):
        for tag in TAGS:
            write_strip(os.path.join(self.d, 'heatmap-cell-strip-still-90x140-%s.png' % tag),
                        (255, 255, 255), rungs)

    def test_identical_channels_are_green(self):
        b, a = steps_of(self.mod, RUNGS)
        self.both_strips(RUNGS)
        lg = os.path.join(self.d, 'j.log')
        write_log(lg, RUNGS, b, a)
        code, out = run(['--shots', self.d, '--judgment-log', lg])
        self.assertEqual(0, code, out)
        self.assertIn('HEAT_FRAME_VERDICT ok', out)
        self.assertIn(u'最大 |R|=0', out)

    def test_collapsed_frame_rung_reds(self):
        """真帧里第 1 档与空格并成同一档 ⇒ 必须红，且不许靠降地板解决。"""
        b, a = steps_of(self.mod, RUNGS)
        collapsed = list(RUNGS)
        collapsed[1] = (242, 243, 243)   # 与空格只差 1/255：**不能**用完全同色，同色会被 set 去重成 4 档
        self.both_strips(collapsed)
        lg = os.path.join(self.d, 'j.log')
        write_log(lg, RUNGS, b, a)
        code, out = run(['--shots', self.d, '--judgment-log', lg])
        self.assertEqual(1, code, u'真帧塌成一档而脚本没红：%s' % out)
        self.assertIn(u'掉到地板', out)

    def test_offset_in_another_column_reds(self):
        """偏移不再只压在 R 那一列（这里让蓝通道整列偏 30）⇒ 两通道口径变了，要响。"""
        b, a = steps_of(self.mod, RUNGS)
        shifted = [(r[0], min(255, r[1] + 40), r[2]) for r in RUNGS]   # 偏 G 那一列（B 早就贴 255，加不上去）
        self.both_strips(shifted)
        lg = os.path.join(self.d, 'j.log')
        write_log(lg, RUNGS, b, a)
        code, out = run(['--shots', self.d, '--judgment-log', lg])
        self.assertEqual(1, code, out[:300])
        self.assertIn(u'不再只压在 R 那一列', out)


if __name__ == '__main__':
    unittest.main()
