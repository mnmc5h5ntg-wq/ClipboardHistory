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

import json  # noqa: E402
sys.path.insert(0, os.path.join(REPO, 'scripts'))
from ci_channel_hygiene import channel_glue_risks_workflow  # noqa: E402  ← R591 靶 2：一把尺只在一处定义
from frame_baseline import machine_key  # noqa: E402
START = 'for GUARD in scripts/tier_reporting_shape.py'
END = 'IDENTICAL_WITNESS_NOT_RUN=1'

# 本轮新印出来的名字（派单第三件事①逐条列的九个 + R591 两支新守卫的名字）
NEW_NAMES = (u'SHAPE_GUARD_EXIT', u'SHAPE_GUARD_READING_MISSING', u'TIER_BRANCH_BLIND',
             u'TIER_BRANCH_NOT_JUDGED', u'IDENTICAL_WITNESS_EXIT', u'IDENTICAL_WITNESS_NOT_RUN',
             u'IDENTICAL_WITNESS_READING_MISSING', u'REALSCREEN_OUTCOME_VERDICT',
             u'REALSCREEN_NOT_RUN',
             # R591：值槽粘连的扫描面 / skipped 的两种成因
             u'SHAPE_GUARD2_EXIT', u'CI_CHANNEL_GLUE_SCOPE', u'CI_CHANNEL_GLUE_SCRIPT_ONLY',
             u'CI_CHANNEL_GLUE_READING_PAREN', u'CI_CHANNEL_GLUE_PARTIAL', u'CI_CHANNEL_HYGIENE_RESULT',
             u'CI_SKIPPED_CAUSES', u'CI_SKIPPED_CAUSES_RESULT', u'CI_SKIPPED_NOT_JUDGED',
             u'CI_EVIDENCE_STEP_SKIPPABLE', u'CI_EVIDENCE_EXEMPT_DEAD', u'CI_EVIDENCE_EXEMPT_BADROW')
# 由脚本自己印的那些：必须能在脚本源码里找到（找不到就是"印了一个没人产出的名字"）
PRINTED_BY = {
    u'TIER_BRANCH_NOT_JUDGED': u'scripts/tier_reporting_shape.py',
    u'REALSCREEN_OUTCOME_VERDICT': u'scripts/real_screen_control_chroma.py',
    u'REALSCREEN_NOT_RUN': u'scripts/real_screen_control_chroma.py',
    u'CI_CHANNEL_GLUE_SCOPE': u'scripts/ci_channel_hygiene.py',
    u'CI_CHANNEL_GLUE_SCRIPT_ONLY': u'scripts/ci_channel_hygiene.py',
    u'CI_CHANNEL_GLUE_READING_PAREN': u'scripts/ci_channel_hygiene.py',
    u'CI_CHANNEL_GLUE_PARTIAL': u'scripts/ci_channel_hygiene.py',
    u'CI_CHANNEL_HYGIENE_RESULT': u'scripts/ci_channel_hygiene.py',
    u'CI_SKIPPED_CAUSES': u'scripts/ci_skipped_causes.py',
    u'CI_SKIPPED_CAUSES_RESULT': u'scripts/ci_skipped_causes.py',
    u'CI_SKIPPED_NOT_JUDGED': u'scripts/ci_skipped_causes.py',
    u'CI_EVIDENCE_STEP_SKIPPABLE': u'scripts/ci_skipped_causes.py',
    u'CI_EVIDENCE_EXEMPT_DEAD': u'scripts/ci_skipped_causes.py',
    u'CI_EVIDENCE_EXEMPT_BADROW': u'scripts/ci_skipped_causes.py',
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
                  u"SHAPE_GUARD_EXIT", u"IDENTICAL_WITNESS_EXIT",
                  u"ci_channel_hygiene.py", u"ci_skipped_causes.py", u"SHAPE_GUARD2_EXIT"):
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

    def test_no_channel_value_slot_is_glued_to_a_parenthetical_explanation(self):
        """R590 / ⓪ 现读：runner 上 `SHAPE_GUARD_EXIT … rc=` 后面那个值**被打成了两个替换符**。

        逐字原文（`gh run view 42159254212 --log`，字节级）：
            `rc=\xef\xbf\xbd\xef\xbf\xbd0=判过 / 1=红 / …`
        而脚本源码里那一行是 `rc=$g（0=判过 …）` ⇒ 值槽与非 ASCII 说明粘在一起时，runner 的日志通道
        会把这一段整体弄坏（R565 那条规矩的 bash 版：值槽只放一个词，说明另起一行）。
        本格判的是**接线正文里**这个形状；R591 靶 2 把尺本身搬到 `ci_channel_hygiene.py`
        （`channel_glue_risks_workflow` / `channel_glue_risks` ⇒ 全仓扫描面 + 看不见的那部分具名下界），
        这里只调用、不再自带第二条正则 —— 两处定义会各自漂移（R324 那条老规矩）。
        """
        hits, _unjudged = channel_glue_risks_workflow(self.body)
        self.assertEqual([], hits, u'接线正文里有通道把说明粘在值槽上 ⇒ runner 上读不到值：%s' % (hits,))
        self.assertGreaterEqual(
            len(channel_glue_risks_workflow(u'echo "X_EXIT=$v（0=ok）"\n')[0]), 1,
            u"正对照：这把尺必须认得出坏写法（否则本格的 0 不算数）")
        # 名字后面还有别的键那一形（M1572 第一次落刀抓到的是尺自己的盲）
        self.assertGreaterEqual(
            len(channel_glue_risks_workflow(u'echo "Y_EXIT guard=$g rc=$g（0=ok）"\n')[0]), 1,
            u"尺退回「名字紧跟 =」那一版时，第二个键上的粘连就看不见 ⇒ 这一格要响")

    def test_the_three_guards_are_invoked_as_cli_not_only_from_tests(self):
        """本轮的根因就是「守卫只在测试里被调用 ⇒ print 被 StringIO 吞在测试里」。
        这一格钉住修法：三条都要以 CLI 形式被 `"$PY"` 调用 —— 前两条走 `for GUARD in …`，
        第三条带帧目录参数，两种写法都要在正文里数到，不许有一条悄悄退回"只有测试跑它"。"""
        self.assertIn(u'for GUARD in scripts/tier_reporting_shape.py scripts/stage_gate_claims.py;',
                      self.body, u"两条形状守卫不再以 CLI 被调用 ⇒ runner 上没有它们的读数行")
        self.assertIn(u'"$PY" "$GUARD"', self.body, u"for 循环里的调用被改写 ⇒ 接线漂了")
        self.assertIn(u'"$PY" scripts/identical_frame_witness.py --shots /tmp/shots-ci',
                      self.body, u"副本名册那条没有以 CLI 被调用")
        # R591：两支新守卫也要以 CLI 被调用 —— 只在电池里跑的话，`run_main()` 会把它们的 print 吞进 StringIO，
        # runner 上就又变成"没有读数行"（R589 那一课的第二次复发预防）。
        self.assertIn(u'for GUARD2 in scripts/ci_channel_hygiene.py scripts/ci_skipped_causes.py;',
                      self.body, u"R591 那两支守卫不再以 CLI 被调用 ⇒ runner 上没有它们的读数行")
        self.assertIn(u'"$PY" "$GUARD2"', self.body, u"GUARD2 循环里的调用被改写 ⇒ 接线漂了")
        self.assertIn(u'[ "$g2" -eq 0 ] || exit 1', self.body,
                      u"GUARD2 的 rc 不再拦路 ⇒ 把硬门降级成了只报数（派单明令不许）")


class ExecutionTests(unittest.TestCase):
    """真跑抽出来的正文：①缺席要走具名绿，②对不上必须响。"""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="r589_ci_run_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def _run(self, shots, roster=None):
        body = step_body().replace(u"/tmp/shots-ci", shots)
        if roster:
            # 接线正文用的是盘上那份名册；负半证人要**换成本机自己的一行**，
            # 否则在名册里没有本机行的机器（runner）上，这一支永远走不到红。
            # 正文里那一串是**不带引号**的 `--shots /tmp/shots-ci`（上面刚换成临时目录），
            # 这里补上引号是因为临时目录名可能含空格 —— 第一次写这格时按带引号去替，活门当场拒绝。
            body = body.replace(u'--shots %s ' % shots,
                                 u'--shots "%s" --roster "%s" ' % (shots, roster))
            assert u"--roster" in body, u"替换没命中 ⇒ 正文的调用形状变了，这一格没有对象"
        path = os.path.join(self.dir, "step.sh")
        # **必须照 GitHub 默认的 shell 来**：runner 那一步是 `bash -e {0}` ⇒ 这里也得 `-e`。
        # R591 ⓪ 现读到的真缺陷就是这么漏掉的：正文里 `set -o pipefail` 我抄了、`-e` 没抄，
        # 于是工具**合法**返回 2 时本机继续跑下面的分支，runner 却直接 `exit code 2` 把整步打死。
        io.open(path, "w", encoding="utf-8").write(u'PY="%s"\nset -eo pipefail\n%s\n' % (sys.executable, body))
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

        R589 那一版在这里**抄了盘上名册**（8 行都 keyed `local:…`）⇒ 本机红、runner 上 `本机行=0`
        直接走 not-run 那一支，rc=0 ⇒ 负半证人在 runner 上没有牙（实测 42159254212 STEP[9] 红在此）。
        修法：名册由本测试自己造，machine 现读 `machine_key()` ⇒ 任何机器上都是"这台登记过却对不上"。
        这一格与 `test_identical_frame_witness.MachineTests` 配对：那边证明"这台没登记过 ⇒ 不判"，
        这边证明"这台登记过却对不上 ⇒ 红"。
        """
        from PIL import Image
        shots = os.path.join(self.dir, "shots")
        os.mkdir(shots)
        for n in (u"a-10x10-dark.png", u"b-10x10-dark.png"):
            Image.new("RGB", (20, 20), (9, 9, 9)).save(os.path.join(shots, n))
        roster = os.path.join(self.dir, "roster.json")
        io.open(roster, "w", encoding="utf-8").write(json.dumps({"schema": 1, "rows": [{
            u"members": [u"ghost-640x480-dark.png", u"ghost-640x480-dark-copy.png"],
            u"should_be_identical": u"是",
            u"cause": u"合成成因（负半证人：这两张帧根本不存在）",
            u"cause_refs": [u"U-TEST"], u"ticket": u"638",
            u"observed": {u"sha": u"0" * 12, u"members": 2, u"corpus_frames": 2},
            u"registered_by_round": u"R590", u"machine": machine_key()}]}, ensure_ascii=False))
        rc, out = self._run(shots, roster)
        self.assertEqual(1, rc, out[-2500:])
        self.assertIn(u"IDENTICAL_PAIR_RED", out)
        self.assertIn(u"不在现读语料里", out)


if __name__ == u"__main__":
    unittest.main()
