#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""报告 §1 那一格的轮数必须与 `curve_from_ledger.py` 现读相等（R293 / BACKLOG 344）。

为什么要有这一支：§1 停在「223 轮 / Round 221」而仪器现读 `PHASE2 n=283 rounds=9..290`，
差 60 轮没有任何东西红 —— 报告正文自己写着「停旧数会红」，而既有那道 headline 守卫
只管**标题**与 U 名册，从不读 §1 这四个数。承诺与门不是同一件事。

范围只到 §1：标题那一格由 `test_final_report_headline.py` 按 Round 口径签
（`FINAL_REPORT_HEADLINE_AHEAD` 拿它和 ITERATION 尾轮比大小），这一支不去抢
（345 记的就是上一次抢着改它、把单位换错成 R=Round+3 之后两门互咬）。

红的时候怎么修（别手抄数）：
    python3 .scratch/motion-audit-2/refresh_report_section1.py
"""
import io
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
UPDATER = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")

CELL = re.compile(u"^(\\| 阶段二 \\*\\*)(\\d+)( 轮\\*\\*审计（R9–R)(\\d+)"
                  u"(；以 `curve_from_ledger\\.py` 的 `PHASE2 n=)(\\d+)"
                  u"(` 为准，最新一节是 `AGENT_VISUAL_ITERATION\\.md` 的 Round )(\\d+)", re.M)


def read(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def load_updater():
    import importlib.util
    spec = importlib.util.spec_from_file_location(u"rs1", UPDATER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SectionOneMatchesInstrument(unittest.TestCase):
    def test_anchor_resolves_on_the_real_file(self):
        """锚点解不出来与数不对是两种病：前者必须响，否则守卫没有对象也报绿。"""
        self.assertIsNotNone(CELL.search(read(REPORT)),
                             u"§1 那一格形状变了 ⇒ 对账断线，改守卫或改回来")

    def test_internal_consistency_of_the_cell(self):
        m = CELL.search(read(REPORT))
        self.assertIsNotNone(m, u"锚点无对象")
        self.assertEqual(m.group(2), m.group(6),
                         u"同一格里 `**N 轮**` 与 `PHASE2 n=N` 必须同数，现在 "
                         + m.group(2) + u" 与 " + m.group(6))

    def test_cell_equals_instrument(self):
        pipe = subprocess.Popen([u"python3", UPDATER, u"--check"], cwd=ROOT,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=dict(os.environ, PYTHONUTF8=u"1",
                                         PYTHONDONTWRITEBYTECODE=u"1"))
        out = pipe.communicate()[0].decode("utf-8", "replace")   # communicate() 给的是 (stdout, stderr)，
        rc = pipe.returncode                                      # 不是 (returncode, stdout)——写反过一次
        self.assertEqual(0, rc,
                         u"§1 停在旧数而仪器已往前走 ⇒ 跑 "
                         + UPDATER.replace(ROOT + os.sep, u"") + u" 刷新：" + out.strip())

    def test_updater_has_teeth_and_is_idempotent(self):
        """正对照：把数改旧 ⇒ 刷新器必须点名；再刷一次 ⇒ 必须说「无」。"""
        mod = load_updater()
        inst = mod.instrument()
        text = read(REPORT)
        m = CELL.search(text)
        self.assertIsNotNone(m, u"锚点无对象 ⇒ 正对照没有对象")
        stale = (text[:m.start()] + m.group(0).replace(u"PHASE2 n=" + inst[0], u"PHASE2 n=999")
                 + text[m.end():])
        out, changed = mod.refresh(stale, inst, write=False)
        self.assertTrue(changed, u"改旧了却不点名 ⇒ 这一格是假的")
        self.assertIn(u"PHASE2 n=" + inst[0], out)
        _, changed2 = mod.refresh(out, inst, write=False)
        self.assertFalse(changed2, u"刷完还要再刷 ⇒ 不幂等")


if __name__ == "__main__":
    unittest.main()
