# -*- coding: utf-8 -*-
"""R588 / 靶 3：`scripts/tier_reporting_shape.py` —— 档位循环必须逐档各自点名，缺席格必须可数。

来历：R587 把 `heatmap_frame_levels.py` 的词表合并之后，既有那格测试当场红 —— 根因是那支脚本
在**第一个 stop 处就 return**，所以"缺席那一档被点名"靠的是循环顺序。本轮现读全仓还剩两处：
`frame_recording_proof.py` 的取帧循环（缺帧就 return ⇒ 第二档永远不被点名）与
`hover_two_state_diff.py` 的 `rung_from_readings`（各自点名了，却**没有一格数得出少了几档**）。
两处都修掉了，这两条规则从此由守卫守着，不再靠"我记得下一轮要检查"。

钉四件事：
① R1（循环体里不许 return）与 R2（必须有可数的缺席格）是**两条独立的红**，各自有合成样本；
   只修一条时另一条必须还红 ⇒ 这才叫两条判据，不是一条判据的两个措辞。
② 词表的四种写法都要认得：`TIERS`、`list(TIERS)`、`('light','dark')`、`('dark','light')`
   —— 只认字面量元组的扫描器在有人改成 `list(TIERS)` 那天会读成「全仓 0 处」（假绿）。
③ **一个档位循环都没找到 ⇒ rc=2**，不许绿：那是扫描器没有对象，不是"全仓都合规"。
④ `.scratch/` 里的一次性脚本**只数不判**（同 R587 对 `sweep_r564_candidates.py` 的处置）⇒
   给临时目录塞一把坏循环，退出码必须不变。
"""
from __future__ import annotations

import ast
import io
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from scripts.tier_reporting_shape import (branch_groups, is_tier_iter, list_py, main, scan_file,   # noqa: E402
                                          tier_iter_names, verdict, verdict_branch)

TIERS = tier_iter_names()
SCRIPTS = os.path.join(REPO, "scripts")

# 合成样本里的形状要用**拼接**写，避免被别的扫描数进自己（R578 那一课）
BAD_RETURN = (u"def run(shots):\n"
              u"    for shade in TI" + u"ERS:\n"
              u"        if not exists(shade):\n"
              u"            print('X_NOT_RUN=%s' % shade)\n"
              u"            ret" + u"urn 1\n"
              u"    return 0\n")
NO_COUNT = (u"def run(shots):\n"
            u"    for shade in TI" + u"ERS:\n"
            u"        if not exists(shade):\n"
            u"            print('X_NOT_RUN=%s' % shade)\n"
            u"            cont" + u"inue\n"
            u"    return 0\n")
CLEAN = (u"def run(shots):\n"
         u"    stops = 0\n"
         u"    for shade in TI" + u"ERS:\n"
         u"        if not exists(shade):\n"
         u"            print('X_NOT_RUN=%s' % shade)\n"
         u"            stops += 1\n"
         u"            continue\n"
         u"    if stops:\n"
         u"        print('X_STOPS not-run=%d' % stops)\n"
         u"        return 1\n"
         u"    return 0\n")


def rows_of(src):
    d = tempfile.mkdtemp(prefix="r588-shape-")
    p = os.path.join(d, "synth.py")
    io.open(p, "w", encoding="utf-8").write(src)
    return scan_file(p, TIERS)[0]


class IterShapeTests(unittest.TestCase):
    def test_four_writings_of_the_tier_iterable_are_all_recognised(self):
        for src, label in ((u"for t in TIERS: pass", u"Name"),
                           (u"for t in list(TIERS): pass", u"list()"),
                           (u"for t in ('light', 'dark'): pass", u"元组正序"),
                           (u"for t in ('dark', 'light'): pass", u"元组反序")):
            node = ast.parse(src).body[0]
            self.assertTrue(is_tier_iter(node.iter, TIERS), u"%s 认不出来" % label)

    def test_an_unrelated_tuple_is_not_a_tier_loop(self):
        node = ast.parse(u"for t in ('a', 'b'): pass").body[0]
        self.assertFalse(is_tier_iter(node.iter, TIERS))
        node2 = ast.parse(u"for t in ('light',): pass").body[0]
        self.assertFalse(is_tier_iter(node2.iter, TIERS), u"只有一档的元组不算档位循环（词表被删剩一个也是读数）")


class RuleTests(unittest.TestCase):
    def test_r1_a_return_inside_a_tier_loop_is_red(self):
        rows = rows_of(BAD_RETURN)
        self.assertEqual(1, len(rows), rows)
        self.assertTrue(rows[0]["returns"], u"循环体里的 return 没被抓到 ⇒ R1 是空判")
        reds = verdict(rows)
        self.assertTrue(any(u"return" in r for r in reds), reds)

    def test_r2_naming_each_tier_without_a_count_is_red(self):
        """只修 R1（把 return 换成 continue）而没补可数格 ⇒ R2 必须还红：这是两条判据的证明。"""
        rows = rows_of(NO_COUNT)
        self.assertEqual(1, len(rows))
        self.assertEqual([], rows[0]["returns"], u"R1 已经修好了")
        self.assertFalse(rows[0]["countable"])
        reds = verdict(rows)
        self.assertEqual(1, len(reds), reds)
        self.assertIn(u"not-run=", reds[0])

    def test_a_compliant_loop_is_green(self):
        rows = rows_of(CLEAN)
        self.assertEqual([], verdict(rows), rows)


class RealRepoTests(unittest.TestCase):
    def test_live_instruments_have_no_bad_tier_loop(self):
        rows = []
        for p in list_py(SCRIPTS):
            if os.path.basename(p) == "tier_vocabulary.py" or (os.sep + "tests" + os.sep) in p:
                continue
            rows.extend(scan_file(p, TIERS)[0])
        self.assertTrue(rows, u"活仪器里一个档位循环都没有 ⇒ 扫描器读错了对象（词表改名了？写法换了？）")
        self.assertEqual([], verdict(rows), u"本轮修掉的两处又长回来了：%s" % rows)
        files = sorted({r["file"] for r in rows})
        self.assertIn(u"scripts/frame_recording_proof.py", files)
        self.assertIn(u"scripts/heatmap_frame_levels.py", files)
        self.assertIn(u"scripts/hover_two_state_diff.py", files)


class CliTests(unittest.TestCase):
    def test_real_repo_exits_zero(self):
        rc, out = run_main([])
        self.assertEqual(0, rc, out)
        self.assertIn(u"TIER_SHAPE_RESULT=ok", out)

    def test_no_tier_loop_at_all_is_not_a_pass(self):
        """③ 扫描器没有对象 ⇒ rc=2，不许绿。"""
        d = tempfile.mkdtemp(prefix="r588-empty-")
        io.open(os.path.join(d, "quiet.py"), "w", encoding="utf-8").write(u"x = 1\n")
        rc, out = run_main([u"--scripts", d, u"--scratch", d])
        self.assertEqual(2, rc, out)
        self.assertIn(u"TIER_SHAPE_RESULT=not-run", out)

    def test_scratch_is_counted_but_not_judged(self):
        """④ 一次性脚本里塞一把坏循环 ⇒ 退出码不变（范围规矩的负半证人）。"""
        live = tempfile.mkdtemp(prefix="r588-live-")
        io.open(os.path.join(live, "good.py"), "w", encoding="utf-8").write(CLEAN)
        scratch = tempfile.mkdtemp(prefix="r588-scratch-")
        io.open(os.path.join(scratch, "bad.py"), "w", encoding="utf-8").write(BAD_RETURN)
        rc, out = run_main([u"--scripts", live, u"--scratch", scratch])
        self.assertEqual(0, rc, out)
        self.assertIn(u"一次性脚本里的循环=1", out)


class BranchChainTests(unittest.TestCase):
    """R589 / 靶 A②：R3 —— 读了同一对量、印同一个通道前缀的一串 `if` 必须有『其余情况』分支。

    这一族与 R1（循环里的 return）同形：不穷尽 ⇒ 至少一种组合一行都不印，而静默与"量了没问题"
    在输出里逐字相同。R588 ⓪·3 在 runner 的门那一步现读到 `FRAME_BASELINE_SCALE*` 行数=0 就是实例，
    而上一版这把尺**只扫循环**，对 if 链是盲的 ⇒ 下面每一格都既是判据也是这把尺自己的正对照。
    """

    def _chains(self, src):
        return branch_groups(ast.parse(src, filename="synthetic.py"), "synthetic.py")

    def test_open_chain_reading_the_same_pair_is_red(self):
        src = (u"def f(a, b):\n"
               u"    if a and b and a != b:\n"
               u'        print("DEMONOTE_MISMATCH x")\n'
               u"    if not b:\n"
               u'        print("DEMONOTE_NOT_RUN y")\n')
        chains = self._chains(src)
        self.assertEqual(1, len(chains), chains)
        self.assertEqual(False, chains[0]["closed"])
        reds = verdict_branch(chains)
        self.assertEqual(1, len(reds), reds)
        self.assertIn(u"一行都不印", reds[0])
        self.assertIn(u"没有兜底", reds[0])

    def test_the_same_chain_with_a_catch_all_is_green(self):
        src = (u"def f(a, b):\n"
               u"    if a and b and a != b:\n"
               u'        print("DEMONOTE_MISMATCH x")\n'
               u"    elif not b:\n"
               u'        print("DEMONOTE_NOT_RUN y")\n'
               u"    else:\n"
               u'        print("DEMONOTE_MATCH z")\n')
        chains = self._chains(src)
        self.assertEqual(1, len(chains), chains)
        self.assertEqual(True, chains[0]["closed"])
        self.assertEqual([], verdict_branch(chains))

    def test_branches_reading_different_quantities_are_not_a_candidate(self):
        """各判各的量 ⇒ 不算"一组互斥分支"。这一格是负半：不许把挨着的两朵 if 都当对象，
        否则全仓每一条 `if` 都要写兜底，规矩就从"防静默"变成"逼出废话"。"""
        src = (u"def f(a, z):\n"
               u"    if a:\n"
               u'        print("DEMONOTE_ONE x")\n'
               u"    if z:\n"
               u'        print("DEMONOTE_TWO y")\n')
        self.assertEqual([], self._chains(src))

    def test_branches_that_print_no_channel_are_not_a_candidate(self):
        src = (u"def f(a, b):\n"
               u"    if a and b:\n"
               u"        do_thing()\n"
               u"    if not b:\n"
               u"        other()\n")
        self.assertEqual([], self._chains(src))

    def test_a_shared_label_is_not_a_shared_quantity(self):
        """两条分支都 `== "tie"` 只说明它们贴同一个标签，不是共读同一个量 ⇒ 不许当对象（否则候选数虚胖）。"""
        src = (u"def f(a, b):\n"
               u'    if a == "tie":\n'
               u'        print("DEMONOTE_TIE a")\n'
               u'    if b == "tie":\n'
               u'        print("DEMONOTE_TIE b")\n')
        self.assertEqual([], self._chains(src))

    def test_real_repo_chains_are_present_and_all_closed(self):
        """现读全仓：链必须**找得到**（找不到的 0 不是绿），且每一条都有兜底。"""
        chains = []
        for p in list_py(SCRIPTS):
            if (os.sep + "tests" + os.sep) in p:
                continue
            chains.extend(branch_groups(ast.parse(io.open(p, encoding="utf-8").read(), filename=p),
                                         os.path.relpath(p, REPO)))
        self.assertTrue(chains, u"分支链=0 ⇒ 这把尺对 if 链是盲的，不许读成「全仓都穷尽」")
        self.assertEqual([], verdict_branch(chains), u"本轮修掉的那两处又长回来了：%s" % chains)
        files = sorted({c["file"] for c in chains})
        self.assertIn(u"scripts/frame_baseline.py", files)
        self.assertIn(u"scripts/real_screen_control_chroma.py", files)

    def test_cli_names_zero_chains_as_a_dimension_that_was_not_judged(self):
        """`分支链=0` 必须**具名**成"这一维不判"，不许混进那句 ok —— 两维都没对象才 rc=2（上面那格）。

        拦下"看不见"的位置有两处，这里证的是输出形状那一处；另一处是消费端：
        CI 的 `Release script tests` 里那行 `TIER_BRANCH_BLIND=1` 与本文件上面那格
        `test_real_repo_chains_are_present_and_all_closed`。
        """
        d = tempfile.mkdtemp(prefix="r589-nocat-")
        io.open(os.path.join(d, "good.py"), "w", encoding="utf-8").write(
            u"def f(a, b):\n"
            u"    for s in TI" + u"ERS:\n"
            u"        print(s, 'not-run=0')\n")
        rc, out = run_main([u"--scripts", d, u"--scratch", d])
        self.assertEqual(0, rc, out)
        self.assertIn(u"TIER_BRANCH_SCAN 分支链=0", out)
        self.assertIn(u"TIER_BRANCH_NOT_JUDGED=", out)
        self.assertIn(u"这一维不判", out)

    def test_extra_dir_is_counted_as_a_positive_control(self):
        """`--extra` 那一路是**盲不盲**的读数：合成违规必须被认出来并计数。"""
        live = tempfile.mkdtemp(prefix="r589-live2-")
        io.open(os.path.join(live, "good.py"), "w", encoding="utf-8").write(
            u"TI" + u"ERS = ('light', 'dark')\n"
            u"def f(a, b):\n"
            u"    for s in TI" + u"ERS:\n"
            u"        print(s, 'not-run=0')\n")
        extra = tempfile.mkdtemp(prefix="r589-extra-")
        io.open(os.path.join(extra, "bad.py"), "w", encoding="utf-8").write(
            u"def f(a, b):\n"
            u"    if a and b:\n"
            u'        print("DEMONOTE_MISMATCH x")\n'
            u"    if not b:\n"
            u'        print("DEMONOTE_NOT_RUN y")\n')
        rc, out = run_main([u"--scripts", live, u"--scratch", live, u"--extra", extra])
        self.assertIn(u"TIER_BRANCH_CONTROL 正对照链=1 其中应红=1 其中判成红=1", out)


def run_main(argv):
    buf = io.StringIO()
    real = sys.stdout
    sys.stdout = buf
    try:
        rc = main(argv)
    finally:
        sys.stdout = real
    return rc, buf.getvalue()


if __name__ == "__main__":
    unittest.main()
