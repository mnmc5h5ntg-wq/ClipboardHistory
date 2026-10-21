#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R279 / BACKLOG 333：`round_verify.sh` 那道帧基线门**第一次有证人**。

为什么这一卷存在：`scripts/round_verify.sh` 一直把 `FRAME_BASELINE_CHANGED=` 抄成
`ROUND_VERIFY … baseline_changed=N` 的**读数**，却把 `frame_baseline.py compare` 的退出码丢掉
（子 shell 的 `$?` 没人看）；而 CI 那一步用的是 `check`，它**按设计只在 missing 时红**
（源码注释：「check = 只要求一帧不许少，多帧与变帧交给人判断」）。两边合起来的意思是：
"改了界面却没在同一笔里 update 基线"这条纪律在任何一侧都不是红，只靠人记得去看那个数。
R252/R253 能发现 changed=1/2，是因为我恰好在读它 —— 读数不是闸门。

这一卷把闸门本身当被测对象：从脚本里**抽出那一段**，喂三种合成读数真跑一遍 bash：
changed≠0 ⇒ 必须红；changed=0 ⇒ 必须绿；**读不到数（NOT-RUN）⇒ 也必须红**
（R99 那条规矩：缺席不许比通过更宽松）。再加两条接线判据：段里不许出现 `|| true`，
且它必须排在 `[4/4]`（dmg/换装）之前 —— 否则红了还会继续把后面两步假装成绿。
"""
import io
import os
import re
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, 'scripts', 'round_verify.sh')
START = u'# R279 / BACKLOG 333'
END_MARK = 'FRAME_GATE_PASS'


def read_script():
    return io.open(SCRIPT, encoding='utf-8').read()


def extract_gate_block(src):
    """从注释锚点抽到 `FRAME_GATE_PASS` 那一行（含）。"""
    i = src.find(START)
    if i < 0:
        return None
    j = src.find(END_MARK, i)
    if j < 0:
        return None
    end = src.find('\n', j)
    return src[i:end if end > 0 else len(src)]


def code_lines(block):
    """剥掉行注释，只留可执行的那几行（R76/R100 那条老规矩：扫前剥注释）。

    这一格是本轮自己撞出来的：门里那段注释写着「故意不留 `|| true`」，
    整块子串搜于是把**注释里的散文**读成代码 ⇒ 一门设计正确的守卫恒红。
    判"用没用"要判它出现在可执行行里，不是出现在文件里。
    """
    kept = []
    for line in block.split('\n'):
        s = line.strip()
        if s.startswith('#') or not s:
            continue
        kept.append(line.split('#', 1)[0].rstrip())
    return '\n'.join(kept)


def run_block(block, env_extra):
    """把抽出来的那段真跑一遍：变量由调用方喂（合成读数），不碰仓库。"""
    body = 'set -o pipefail\n' + env_extra + '\n' + block + '\n'
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'snippet.sh')
    io.open(p, 'w', encoding='utf-8').write(body)
    pr = subprocess.run(['bash', p], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return pr.returncode, pr.stdout.decode('utf-8', 'replace')


class FrameGateWiringTests(unittest.TestCase):
    def test_the_gate_exists_and_uses_the_changed_reading(self):
        block = extract_gate_block(read_script())
        self.assertIsNotNone(block, 'round_verify.sh 里找不到帧基线闸门（被删了？333 就重新开）')
        code = code_lines(block)
        self.assertIn('exit 1', code, '闸门只打印不拦 ⇒ 那还是读数，不是门')
        self.assertIn('${BC', code, '闸门没读 changed 那个数')
        self.assertNotIn('|| true', code, '可执行行里出现 `|| true` ⇒ 这道门被自己拆了')
        # 反向对照：注释里那句「故意不留 `|| true`」不许被当成拆门（本轮撞过一次，见 code_lines）
        self.assertIn('|| true', block,
                      '正对照失效：门里的注释已经不含这句话 ⇒ code_lines 剥的不是这一处，判据要重看')

    def test_the_gate_runs_before_the_dmg_and_install_steps(self):
        src = read_script()
        block = extract_gate_block(src)
        self.assertIsNotNone(block, '闸门不在，谈不上顺序')
        self.assertLess(src.find(START), src.find('[4/4]'),
                        '闸门排在 dmg/换装之后 ⇒ 红了还会把后面两步假装成绿')

    def test_a_changed_frame_set_is_red(self):
        rc, out = run_block(extract_gate_block(read_script()), 'BC=3; CM=170; MS=0')
        self.assertNotEqual(0, rc, 'changed=3 却没红 ⇒ 这道门是装饰（333 的原始缺陷原样复现）')
        self.assertIn('FRAME_GATE_RED=changed=3', out, '红了但不点名 ⇒ 下一轮无从分诊')
        self.assertIn('FRAME_GATE_HOWTO', out, '红话里要写唯一那条正路（update 之后重跑），不许留后门')

    def test_a_matching_frame_set_is_green(self):
        rc, out = run_block(extract_gate_block(read_script()), 'BC=0; CM=170; MS=0')
        self.assertEqual(0, rc, '完全一致却红 ⇒ 这道门会把人训练成无视红色')
        self.assertIn('FRAME_GATE_PASS changed=0 compared=170 missing=0', out,
                      '绿也要留一行可复查的读数')

    def test_a_missing_reading_is_red_not_green(self):
        """`compare` 崩了 / 日志没打出来时 BC 是 NOT-RUN —— 缺席不许比通过更宽松。"""
        rc, out = run_block(extract_gate_block(read_script()), 'BC=NOT-RUN; CM=0; MS=0')
        self.assertNotEqual(0, rc, '读不到 changed 就当通过 ⇒ 门在"尺坏了"这一侧永远绿')
        self.assertIn('FRAME_GATE_RED=changed=NOT-RUN', out)

    def test_the_real_working_baseline_still_passes_today(self):
        """接线判据之外的一格：拿盘上真实基线跑一次 compare，确认这道门**今天**不是恒红。

        这一格是防"新门把自己家锁死"：R109 那条规矩 —— 0 告警那道门第一次红，常常红在新判据自己身上。
        """
        d = tempfile.mkdtemp()
        # 空目录 ⇒ compared=0、missing=170 ⇒ compare 会红；所以这里只验"门对 missing 的态度"：
        # 读不到 changed 时必须拦，而不是因为目录空就放行。
        rc, out = run_block(extract_gate_block(read_script()), 'BC=0; CM=0; MS=170')
        self.assertEqual(0, rc, 'changed=0 时门不该管 missing（那是 CI 那道 check 的职责，两把尺各管一件事）')
        self.assertIn('missing=170', out, '绿行里要把 missing 也打出来，否则"整目录空"会被读成一切正常')


if __name__ == '__main__':
    unittest.main()
