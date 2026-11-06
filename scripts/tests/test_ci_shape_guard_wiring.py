# -*- coding: utf-8 -*-
"""R589 / 靶 A②+B：CI 里新接的那三条形状守卫，**接线本身**第一次有自己的判据卷。

为什么这一卷存在（R247 那一族的复发预防）：本轮往 `Release script tests` 末尾加了一段
（三条 CLI 调用 + 三种缺席分开说）。上一轮刚学到「只在测试里被调用的守卫，在 runner 上没有读数行」，
而如果这段接线自己漂了（改名、少一个 `fi`、把 `grep … && { … }` 写在 `bash -e` 下 ⇒ 假红），
今天没有任何一格会红 —— 只能等 CI 那一跑。所以这里把正文**抽出来、dedent、`bash -n`、对着临时帧目录真跑**。

判的三格（R242 的三分法，不许都算绿，也不许都算红）：
  ① 帧目录不存在/空 ⇒ `IDENTICAL_PAIR_REFUSED=no-shots` 或 `RESULT=not-run 本机行=0` ⇒ **这一步绿**，
     并且必须自己说出「这一维在 runner 上今天没人判」，不许被读成「runner 上没有副本」；
  ② 同一台机器、名册与语料对不上（本轮造的正是"缺边"）⇒ 这一步**必须响**（负半证人：
     ①那一支的绿不是无条件放行）；
  ③ 正文里每个新印出来的名字都要有出处 —— 守卫自己印的必须在守卫源码里存在，
     工作流自己 echo 的必须在本卷的名册里被数到（R579 那一课：名册要靠被引用才红）。
"""
from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CI = os.path.join(REPO, '.github', 'workflows', 'ci.yml')
START = 'for GUARD in scripts/tier_reporting_shape.py'
END = 'IDENTICAL_WITNESS_NOT_RUN=1'

# 本轮新印出来的名字（派单第三件事①逐条列的九个）
NEW_NAMES = (u'SHAPE_GUARD_EXIT', u'SHAPE_GUARD_READING_MISSING', u'TIER_BRANCH_BLIND',
             u'TIER_BRANCH_NOT_JUDGED', u'IDENTICAL_WITNESS_EXIT', u'IDENTICAL_WITNESS_NOT_RUN',
             u'IDENTICAL_WITNESS_READING_MISSING', u'REALSCREEN_OUTCOME_VERDICT',
             u'REALSCREEN_NOT_RUN')
# 由脚本自己印的那些：必须能在脚本源码里找到（找不到就是"印了一个没人产出的名字"）
PRINTED_BY = {
    u'TIER_BRANCH_NOT_JUDGED': u'scripts/tier_reporting_shape.py',
    u'REALSCREEN_OUTCOME_VERDICT': u'scripts/real_screen_control_chroma.py',
    u'REALSCREEN_NOT_RUN': u'scripts/real_screen_control_chroma.py',
}


def step_body(path=CI):
    """抽出本轮新加的那一段并 dedent；抽不到就抛（不许静默给绿）。"""
    text = io.open(path, encoding="utf-8").read()
    if START not in text:
        raise AssertionError(u"抽不到正文起点（%s）⇒ 接线被改名或整段被删，这一卷没有对象" % START)
    i = text.index(START)
    j = text.index(END, i)
    k = text.index(u"\n          fi", j) + len(u"\n          fi")
    raw = text[i:k]
    lines = [l[10:] if l.startswith(u" " * 10) else l.lstrip() for l in raw.split(u"\n")]
    body = u"\n".join(lines)
    for token in (u"tier_reporting_shape.py", u"stage_gate_claims.py", u"identical_frame_witness.py",
                  u"SHAPE_GUARD_EXIT", u"IDENTICAL_WITNESS_EXIT"):
        if token not in body:
            raise AssertionError(u"抽出来的正文里没有 %s ⇒ 抽取边界漂了" % token)
    return body


class BashShapeTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="r589_ci_wiring_")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.body = step_body()

    def test_the_extracted_step_body_is_valid_bash(self):
        path = os.path.join(self.dir, "step.sh")
        io.open(path, "w", encoding="utf-8").write(self.body)
        proc = subprocess.run([u"bash", u"-n", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertEqual(0, proc.returncode, proc.stdout.decode("utf-8", "replace"))

    def test_no_top_level_and_list_under_bash_e(self):
        """`grep … && { …; exit 1; }` 在 `bash -e` 下会在**没有红**的时候自己退出（假红）。
        本轮踩过一次，这一格是它的永久证人：所有"命中就拦"的写法必须是 `if … then … fi`。"""
        bad = []
        for n, line in enumerate(self.body.splitlines(), 1):
            s = line.strip()
            if s.startswith(u"#"):
                continue
            if re.search(r"^(grep|\[|if !)", s) and u" && {" in s:
                bad.append(u"L%d %s" % (n, s[:80]))
        self.assertEqual([], bad, u"这一段的 `A && { … }` 写法在 bash -e 下会自己退出：%s" % bad)

    def test_every_new_name_is_registered_somewhere(self):
        """九个新名字：工作流里印的必须在正文里，脚本印的必须在脚本源码里。"""
        missing = [n for n in NEW_NAMES if n not in self.body and n not in PRINTED_BY]
        self.assertEqual([], missing, u"这些名字既不在新接线正文里、也不是脚本自己印的：%s" % missing)
        for name, script in PRINTED_BY.items():
            src = io.open(os.path.join(REPO, script), encoding="utf-8").read()
            self.assertIn(name, src, u"%s 说 `%s` 由 %s 印，可那份源码里没有这个名字" % (name, name, script))

    def test_the_three_guards_are_invoked_as_cli_not_only_from_tests(self):
        """本轮的根因就是「守卫只在测试里被调用 ⇒ print 被 StringIO 吞在测试里」。
        这一格钉住修法：三条都要以 CLI 形式被 `"$PY"` 调用 —— 前两条走 `for GUARD in …`，
        第三条带帧目录参数，两种写法都要在正文里数到，不许有一条悄悄退回"只有测试跑它"。"""
        self.assertIn(u'for GUARD in scripts/tier_reporting_shape.py scripts/stage_gate_claims.py;',
                      self.body, u"两条形状守卫不再以 CLI 被调用 ⇒ runner 上没有它们的读数行")
        self.assertIn(u'"$PY" "$GUARD"', self.body, u"for 循环里的调用被改写 ⇒ 接线漂了")
        self.assertIn(u'"$PY" scripts/identical_frame_witness.py --shots /tmp/shots-ci',
                      self.body, u"副本名册那条没有以 CLI 被调用")


class ExecutionTests(unittest.TestCase):
    """真跑抽出来的正文：①缺席要走具名绿，②对不上必须响。"""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="r589_ci_run_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def _run(self, shots):
        body = step_body().replace(u"/tmp/shots-ci", shots)
        path = os.path.join(self.dir, "step.sh")
        io.open(path, "w", encoding="utf-8").write(u'PY="%s"\nset -o pipefail\n%s\n' % (sys.executable, body))
        proc = subprocess.run([u"bash", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=REPO)
        return proc.returncode, proc.stdout.decode("utf-8", "replace")

    def test_absent_frames_dir_is_a_named_absence_and_stays_green(self):
        rc, out = self._run(os.path.join(self.dir, "no-such-dir"))
        self.assertEqual(0, rc, out[-2500:])
        self.assertIn(u"IDENTICAL_WITNESS_NOT_RUN=1", out)
        self.assertIn(u"IDENTICAL_PAIR_REFUSED=no-shots", out)
        self.assertNotIn(u"IDENTICAL_WITNESS_EXIT=1", out)

    def test_the_same_machine_with_an_unmatched_corpus_must_go_red(self):
        """负半证人：①那一支的绿不是无条件放行。

        造一个只有两张帧的目录 ⇒ 现读名册那 8 行的帧全都不在语料里 ⇒ `名册帧缺失=8` ⇒ 这一步必须响。
        这一格与 `test_identical_frame_witness.MachineTests` 配对：那边证明"这台没登记过 ⇒ 不判"，
        这边证明"这台登记过却对不上 ⇒ 红"。
        """
        from PIL import Image
        shots = os.path.join(self.dir, "shots")
        os.mkdir(shots)
        for n in (u"a-10x10-dark.png", u"b-10x10-dark.png"):
            Image.new("RGB", (20, 20), (9, 9, 9)).save(os.path.join(shots, n))
        rc, out = self._run(shots)
        self.assertEqual(1, rc, out[-2500:])
        self.assertIn(u"IDENTICAL_PAIR_RED", out)
        self.assertIn(u"不在现读语料里", out)


if __name__ == u"__main__":
    unittest.main()
