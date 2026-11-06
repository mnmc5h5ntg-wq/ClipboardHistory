# -*- coding: utf-8 -*-
"""R593 / 靶 1：`frame_geometry_blind.py` 的接线判据卷。

这一支管两件事：① 守卫读的是不是它声称的那个对象（捕获通道，不是判据自己）；
② "默认变了而帧不动"这一格必须**会响** —— 用户点名的刀形状（产品变了而尺不响）由这里钉。
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import frame_geometry_blind as fgb  # noqa: E402


DEFAULTS = {u"expandedWidthDefault": 848.0, u"collapsedWidthDefault": 424.0,
            u"contentHeightDefault": 600.0}


class JudgeTableTest(unittest.TestCase):
    def test_the_three_verdicts_are_three_different_readings(self):
        # C：refs=0 且默认与登记一致 ⇒ ok，并且必须印出那行 blind 读数（不是只回 0）。
        reg = {u"policy_defaults": DEFAULTS, u"harness_policy_refs": 0}
        rc, lines = fgb.judge(DEFAULTS, 0, 4, {(720, 520)}, 356, reg)
        self.assertEqual(0, rc, u"一致时不该红：%s" % lines)
        self.assertTrue(any(l.startswith(u"FRAME_GEOMETRY_BLIND=policy-default") for l in lines),
                        u"绿的那一趟也要把盲区读数印出来，否则下一轮无从对账")
        # B：默认挪走 ⇒ 红，且红话里要点名是哪一档挪了。
        moved = {u"policy_defaults": {u"expandedWidthDefault": 750.0,
                                      u"collapsedWidthDefault": 420.0,
                                      u"contentHeightDefault": 600.0},
                 u"harness_policy_refs": 0}
        rc, lines = fgb.judge(DEFAULTS, 0, 4, {(720, 520)}, 356, moved)
        self.assertEqual(1, rc, u"默认变了而捕获侧引用仍是 0 ⇒ 这一格必须响（用户点名的刀形状）")
        self.assertIn(u"expandedWidthDefault", lines[-1], u"红话要点名是哪一档挪了，不许只说'变了'")
        # A：捕获侧真的引用了 ⇒ 反过来红，因为那条具名该撤而不是留着当永久豁免。
        rc, lines = fgb.judge(DEFAULTS, 3, 4, {(720, 520)}, 356, reg)
        self.assertEqual(1, rc, u"refs>0 而登记说盲 ⇒ 具名过期，红")
        self.assertIn(u"永久豁免", lines[-1])

    def test_a_missing_registry_is_not_run_and_not_pass(self):
        rc, lines = fgb.judge(DEFAULTS, 0, 4, {(720, 520)}, 356, None)
        self.assertEqual(2, rc, u"登记不在盘上是『没判』，不是『判过』（R590 那一族）")
        self.assertIn(u"not-run", lines[-1])

    def test_zero_frames_do_not_make_the_blind_claim_pass(self):
        # 扫描面 0 不算数：帧基线读不到 ⇒ 那一维只能是 not-run，不许读成"0 张与默认同档 ⇒ 盲"。
        rc, lines = fgb.judge(DEFAULTS, 0, 4, None, 0, {u"policy_defaults": DEFAULTS,
                                                        u"harness_policy_refs": 0})
        self.assertEqual(0, rc)
        self.assertIn(u"（没读到）", lines[0], u"帧档数取不到时要在读数里说出来，不许静默当 0 档")


class LiveRepoTest(unittest.TestCase):
    def test_the_capture_channel_really_is_blind_on_this_tree(self):
        """现读：捕获侧对那三个常量的引用必须是 0 —— 这条就是"帧逐字节相同不含信息"的证人。"""
        defaults = fgb.policy_defaults(os.path.join(ROOT, fgb.POLICY))
        self.assertIsNotNone(defaults, u"产品里读不到那三档默认常量 ⇒ 尺没有对象")
        self.assertEqual({u"expandedWidthDefault": 848.0, u"collapsedWidthDefault": 424.0,
                          u"contentHeightDefault": 600.0}, defaults,
                         u"产品默认几何与本轮登记的不是同一档 ⇒ 要么改账要么改产品，别只改判据")
        refs, files, hits = fgb.capture_refs(os.path.join(ROOT, fgb.FIXTURE_TESTS))
        self.assertGreaterEqual(files, 3, u"捕获侧一个文件都没扫到 ⇒ 扫描面塌了，0 引用不算证据")
        self.assertEqual(0, refs,
                         u"捕获通道引用了产品默认几何（%s）⇒ 盲区那条具名要撤，别再让它替这一维说话" % hits)

    def test_the_registry_agrees_with_the_live_policy(self):
        path = os.path.join(ROOT, fgb.REGISTRY)
        self.assertTrue(os.path.exists(path), u"登记文件不在盘上 ⇒ 这一维今天没人判")
        reg = json.loads(io.open(path, encoding=u"utf-8").read())
        self.assertEqual(fgb.policy_defaults(os.path.join(ROOT, fgb.POLICY)),
                         {k: float(v) for k, v in reg[u"policy_defaults"].items()},
                         u"登记的默认几何与产品不同源 ⇒ B 那一支会红，先把账对齐")
        self.assertEqual(0, int(reg[u"harness_policy_refs"]),
                         u"登记说捕获侧引用是 0，别在没重测的情况下改成别的数")

    def test_the_guard_selfcheck_rings_on_both_directions(self):
        self.assertTrue(fgb.selfcheck(ROOT), u"正对照没响 ⇒ 这把尺认不出自己该认的两种坏法")


if __name__ == u"__main__":
    unittest.main(verbosity=2)
