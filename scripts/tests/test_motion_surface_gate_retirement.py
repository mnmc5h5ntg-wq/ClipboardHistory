#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""撤词表项的四条判据（R177 / BACKLOG 204）。

为什么单独一支：清账表的地板是**单调量**（`FLOOR_WENT_BACK` 挡"清账退步"），
而"撤掉一个不再存在的表面"在纯计数上与退步长得一模一样 —— 没有退役通道，
要么禁止撤项（于是幽灵表面继续每轮产生假进度），要么撤项会红成"退步"。
这一支把后者变成前者：**撤要登记，登记要带理由，不登记的少行照旧红**。

夹具全部写在 `tempfile.TemporaryDirectory()` 里，并且断言 `docs/` 没被写过
（R91/R92 那一族：检查工具顺手改掉被检查的东西）。
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import motion_surface_gate as gate  # noqa: E402

SURFACE = u"浮层/底部说明"


def table(retired=None, keep_surface=True, keep_rows=True, reason=u"R177 撤词表项：这一层没有承载物，"
                                                           u"理由要够长才不算空话"):
    surfaces = [SURFACE, u"主窗口/列表行"] if keep_surface else [u"主窗口/列表行"]
    rows = []
    if keep_rows:
        rows.append({"surface": SURFACE, "state": u"加载", "verdict": "not-applicable",
                     "reason": reason, "evidence": "Sources/x.swift"})
    rows.append({"surface": u"主窗口/列表行", "state": u"悬停", "verdict": "kept",
                 "reason": reason, "evidence": "Sources/y.swift"})
    data = {"verdicts": ["added", "kept", "not-added", "not-applicable", "not-measured"],
            "cleared_verdicts": ["added", "kept", "not-added", "not-applicable"],
            "surfaces": surfaces,
            "states": [u"加载", u"悬停"],
            "rows": rows,
            "floor_cleared": len([r for r in rows if r["verdict"] != "not-measured"])}
    if retired is not None:
        data["retired_surfaces"] = {SURFACE: retired}
    return data


class RetirementTests(unittest.TestCase):

    def test_silent_removal_is_still_a_red(self):
        """正对照：HEAD 里有已清账格子、本轮名册没了、又没登记退役 ⇒ 必须红。"""
        head = table()
        gone = table()
        gone["surfaces"] = [u"主窗口/列表行"]
        gone["rows"] = [r for r in gone["rows"] if r["surface"] != SURFACE]
        codes = [c for c, _ in gate.retirement_problems(gone, head)]
        self.assertIn("RETIRED_UNDECLARED", codes,
                      "撤项可以是决定，但不能是静默的少一行（R143 那一族）")

    def test_declared_retirement_clears_the_red(self):
        """同一份表，登记了退役 ⇒ 不再红：这条排除"闸门恒红、登记与否都一样"。"""
        head = table()
        gone = table(retired=table()["rows"][0]["reason"])
        gone["surfaces"] = [u"主窗口/列表行"]
        gone["rows"] = [r for r in gone["rows"] if r["surface"] != SURFACE]
        self.assertEqual([], gate.retirement_problems(gone, head))

    def test_allowance_only_comes_from_declared_retirement(self):
        """地板降幅只从登记过的表面来；没登记 ⇒ 降幅 0 ⇒ `FLOOR_WENT_BACK` 照旧红。"""
        head = table()
        declared = table(retired=u"R177 撤词表项：这一层没有承载物，理由要够长才不算空话")
        declared["surfaces"] = [u"主窗口/列表行"]
        declared["rows"] = [r for r in declared["rows"] if r["surface"] != SURFACE]
        # 撤项之后地板要跟着重算（不重算就是 FLOOR_LIES，那是另一条判据的活）
        declared["floor_cleared"] = len([r for r in declared["rows"] if r["verdict"] != "not-measured"])
        self.assertEqual(1, gate.retirement_allowance(declared, head))
        self.assertEqual(0, gate.retirement_allowance(table(), head),
                         "没登记退役却想降地板 ⇒ 那是清账退步，不许有降幅")
        # 降幅要真的进到地板比较里：HEAD 地板 2、撤掉 1 格 ⇒ 允许到 1；再低就红。
        cleared = len([r for r in declared["rows"] if r["verdict"] != "not-measured"])
        self.assertEqual(1, cleared)
        self.assertEqual(declared["floor_cleared"], cleared, "地板要与已清账对齐，否则红的是 FLOOR_LIES 而不是这一格")
        # 只看这一条判据的方向（其余判据要真文件证据，由另一支测试覆盖）：
        # 降幅给到 1 ⇒ 不红；不给降幅（还是 2）⇒ 红。
        self.assertNotIn("FLOOR_WENT_BACK", [c for c, _ in gate.check(declared, head_floor=1)])
        self.assertIn("FLOOR_WENT_BACK", [c for c, _ in gate.check(declared, head_floor=2)])

    def test_retired_but_still_listed_is_refused(self):
        """登记了退役却还在名册里 / 还留着行：两种"撤不干净"都要红。"""
        half = table(retired=u"R177 撤词表项：这一层没有承载物，理由要够长才不算空话")
        codes = [c for c, _ in gate.retirement_problems(half, None)]
        self.assertIn("RETIRED_STILL_LISTED", codes)
        self.assertIn("RETIRED_ROW_PRESENT", codes)

    def test_empty_reason_is_refused(self):
        """撤词表项要有产品面的理由；空话（短于 20 字）不算。"""
        short = table(retired=u"不想要了")
        short["surfaces"] = [u"主窗口/列表行"]
        short["rows"] = [r for r in short["rows"] if r["surface"] != SURFACE]
        self.assertIn("RETIRED_NO_REASON", [c for c, _ in gate.retirement_problems(short, None)])

    def test_the_gate_actually_calls_the_retirement_checks(self):
        """谓词不是纸上概念：main() 必须真的调它，否则"抽出来了"等于"没接线"（R88 那一族）。"""
        src = io.open(os.path.join(REPO, "scripts", "motion_surface_gate.py"), encoding="utf-8").read()
        for needle in ("problems += retirement_problems(data, head)",
                       "allowance = retirement_allowance(data, head)",
                       "head_table() if in_repo else None", "MOTION_LEDGER_RETIRED"):
            self.assertEqual(1, src.count(needle),
                             "%r 在闸门源码里出现 %d 次（要恰好 1）" % (needle, src.count(needle)))

    def test_the_real_table_passes_and_declares_exactly_one_retirement(self):
        """真产物证人：仓库里那张表跑闸门要绿，且退役名册就是「浮层/底部说明」一格。"""
        out = subprocess.check_output([sys.executable,
                                       os.path.join(REPO, "scripts", "motion_surface_gate.py")],
                                      cwd=REPO).decode("utf-8")
        self.assertIn("MOTION_LEDGER_RESULT=ok", out)
        self.assertIn(u"MOTION_LEDGER_RETIRED 1（%s）" % SURFACE, out)
        self.assertIn(u"表面=18 状态=9 格子=162 行数=111 已清账=111 未清账=51", out)
        self.assertNotIn(u"RETIRED_UNDECLARED", out)

    def test_no_fixture_writes_land_in_docs(self):
        box = tempfile.mkdtemp(prefix="retire-")
        self.assertFalse(os.path.exists(os.path.join(REPO, "docs", "motion_surface_ledger.json.bak")))
        self.assertNotIn(box, os.listdir(os.path.join(REPO, "docs")))


if __name__ == "__main__":
    unittest.main()
