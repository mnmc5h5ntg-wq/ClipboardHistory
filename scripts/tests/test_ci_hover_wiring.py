#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R247（第 246 轮 / Round 244）：CI 抓帧那一步的**正文**第一次有自己的判据卷。

为什么这一卷存在（BACKLOG 274 的 runner 半 / U-795）：run 39394134380 现读到
`HOVER_DIFF_CONTROL=` 给出**四个**名字（dark 与 light 各一颗 idle、一颗 lit），于是那一步响成
`HOVER_DIFF_CONTROL_INCOMPLETE=1`。修法是"按 (状态 × 色档) 各取一颗"，但**修法本身当时只有一个证人**：
我手工把正文抽出来跑了一遍（`/tmp/r246_step.sh`）。手工证人不会自己重跑 —— 这一卷就是那条手工腿的永久化：
它把 `ci.yml` 里那一段 bash **抽出来、dedent、`bash -n`、然后对着合成帧目录真跑**，
所以"接线又漂了"这件事以后是判据红，不是下一跑 CI 红。

三种缺席分开判（R242 的三分法，不许都算绿）：
  ① 有 idle 有 lit（同一档）      ⇒ 退出 0，且 `HOVER_DIFF_CONTROL=` 恰好是那两颗（不掺 light）
  ② 有帧但缺 idle（或缺 lit）     ⇒ 退出非 0，且点名 `HOVER_DIFF_CONTROL_INCOMPLETE=1`
  ③ 整目录没有 png               ⇒ 环境缺席：点名 `HOVER_DIFF_NOT_RUN=1`，**这一步是绿的**
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    from PIL import Image
except ImportError:                                    # 与 252 同一族：缺库要能被点名
    Image = None

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CI = os.path.join(REPO, '.github', 'workflows', 'ci.yml')

PAIR_A = 'glass-pill-hover-120x232-dark'              # 尺自己按帧名配的那一对
PAIR_B = 'glass-pill-120x232-dark'
CTRL_IDLE = 'modechip-hover-idle-200x60-dark'         # 正对照的两颗（同一档）
CTRL_LIT = 'modechip-hover-lit-200x60-dark'
OTHER_APPEARANCE = 'modechip-hover-lit-200x60-light'  # 故意在场：上一版的 grep 会把这颗也吃进去


def step_body(path=CI):
    """从 ci.yml 里抽出抓帧那一步的正文并 dedent。抽不到就抛（不许静默给绿）。"""
    text = io.open(path, encoding='utf-8').read()
    start_marker = 'n_png=$(ls /tmp/shots-ci/*.png'
    if start_marker not in text:
        raise AssertionError('抽不到正文起点（%s）⇒ 接线被改名或整步被删，这一卷没有对象' % start_marker)
    i = text.index(start_marker)
    j = text.index('[ "$hd" -eq 0 ] || exit 1', i) + len('[ "$hd" -eq 0 ] || exit 1')
    k = text.index('\n          fi', j) + len('\n          fi')
    raw = text[i:k]
    lines = [l[10:] if l.startswith(' ' * 10) else l.lstrip() for l in raw.split('\n')]
    body = '\n'.join(lines)
    for token in ('HOVER_DIFF_WIRED_AT', 'HOVER_DIFF_CONTROL=', 'hover_two_state_diff.py', 'fi'):
        if token not in body:
            raise AssertionError('抽出来的正文里没有 %s ⇒ 抽取边界漂了' % token)
    return body


def write_frame(dirpath, name, changed):
    """造一张 200x60 的灰底帧；changed=True 时点亮一整块（够 50 颗，尺的正对照门槛）。"""
    im = Image.new('RGB', (200, 60), (50, 50, 50))
    if changed:
        for x in range(40, 120):
            for y in range(10, 40):
                im.putpixel((x, y), (120, 120, 120))
    im.save(os.path.join(dirpath, name + '.png'))


class HoverWiringTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='ci_hover_wiring_')
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.script = os.path.join(self.dir, 'step.sh')

    def frames(self, names):
        """names: {帧名: 是否点亮}。临时目录每格自己造，绝不跨格复用（R91 那一族）。"""
        for name, changed in names.items():
            write_frame(self.dir, name, changed)

    def run_step(self):
        body = step_body().replace('/tmp/shots-ci', self.dir)
        io.open(self.script, 'w', encoding='utf-8').write('PY=%s\n%s\n' % (sys.executable, body))
        # 不用 text=True：这一步的 stdout 里会漏进非 UTF-8 字节（本轮实测在此抛 UnicodeDecodeError，
        # 位置在帧目录列完之后）。崩溃的证人不是判据 —— 所以按字节收，再 errors=replace 解码。
        proc = subprocess.run(['bash', self.script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.returncode, proc.stdout.decode('utf-8', 'replace')


@unittest.skipIf(Image is None, '缺 PIL：这一卷没有对象，要能被点名（252 的形状）')
class StepBodyTests(HoverWiringTestCase):
    def test_the_extracted_step_body_is_valid_bash(self):
        """抽取本身也要能被打红：`bash -n` 只查语法，它是"我抽对了吗"的第一道证人。"""
        body = step_body().replace('/tmp/shots-ci', self.dir)
        io.open(self.script, 'w', encoding='utf-8').write(body + '\n')
        proc = subprocess.run(['bash', '-n', self.script], capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, '抽出来的正文不是合法 bash：%s' % proc.stderr[:200])

    def test_extraction_boundary_is_unique_in_the_workflow(self):
        text = io.open(CI, encoding='utf-8').read()
        self.assertEqual(1, text.count('n_png=$(ls /tmp/shots-ci/*.png'),
                         '起点在 ci.yml 里不止一处 ⇒ 抽取会拿到第一处，而判的可能是另一处')


@unittest.skipIf(Image is None, '缺 PIL：这一卷没有对象，要能被点名（252 的形状）')
class ControlPairingTests(HoverWiringTestCase):
    def test_a_complete_pair_exits_zero_and_names_exactly_two_frames(self):
        self.frames({PAIR_A: True, PAIR_B: False, CTRL_IDLE: False, CTRL_LIT: True,
                     OTHER_APPEARANCE: True})
        rc, out = self.run_step()
        self.assertIn('HOVER_DIFF_CONTROL=%s,%s ' % (CTRL_IDLE, CTRL_LIT), out,
                      '正对照必须是**同一色档**的两颗；上一版的 grep 会把 -light 也吃进来（U-795 现读四个名字）\n%s' % out[-400:])
        self.assertEqual(0, rc, '完整一对不该红：%s' % out[-400:])

    def test_a_missing_idle_half_is_named_not_silently_green(self):
        self.frames({PAIR_A: True, PAIR_B: False, CTRL_LIT: True})
        rc, out = self.run_step()
        self.assertNotEqual(0, rc, '缺 idle 那一半时这一步必须响（274 的"接线坏了"出口）：%s' % out[-400:])
        self.assertIn('HOVER_DIFF_CONTROL_INCOMPLETE=1', out,
                      '要响也要说清是哪一种缺席：%s' % out[-400:])

    def test_a_missing_lit_half_is_named_too(self):
        """两半各证一次：只证一边会被"另一半恰好恒空"喂饱（R99 那族：0 有两种相反成因）。"""
        self.frames({PAIR_A: True, PAIR_B: False, CTRL_IDLE: False})
        rc, out = self.run_step()
        self.assertNotEqual(0, rc, '缺 lit 那一半时这一步必须响：%s' % out[-400:])
        self.assertIn('HOVER_DIFF_CONTROL_INCOMPLETE=1', out, '%s' % out[-400:])

    def test_an_empty_frames_dir_is_a_named_absence_and_stays_green(self):
        """环境缺席 ≠ 缺陷：这一格必须是"点名 + 退出 0"，否则 runner 少一个通道就变成产品红。"""
        rc, out = self.run_step()
        self.assertIn('HOVER_DIFF_NOT_RUN=1', out, '整目录没有 png 要按环境缺席记：%s' % out[-400:])
        self.assertEqual(0, rc, '环境缺席不该把这一步判红：%s' % out[-400:])


if __name__ == '__main__':
    unittest.main(verbosity=2)
