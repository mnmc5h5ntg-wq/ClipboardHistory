#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`scripts/motion_surface_gate.py` 的自检（R127）。

两种格子分开判：**不合法**（会红）与**没清账**（只数，不红）。
把"没判过"也判成红，下一轮就会为了绿去填满 162 格 —— 那才是这张表最坏的坏法。
"""
import io
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motion_surface_gate as gate

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "motion_surface_ledger.json"


def base():
    return {
        "verdicts": ["added", "kept", "not-added", "not-applicable", "not-measured"],
        "surfaces": ["主窗口/列表行", "浮层/搜索框"],
        "states": ["悬停", "聚焦"],   # 夹具自己也要过「每个状态至少一行」那一格（U-427）
        "cleared_verdicts": ["added", "kept", "not-added", "not-applicable"],
        "floor_cleared": 2,
        "rows": [
            {"surface": "主窗口/列表行", "state": "悬停", "verdict": "kept",
             "reason": "0.12s 底色与图标透明度已经量过，更快会读成闪烁",
             "evidence": "Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift；R14 / R15"},
            {"surface": "浮层/搜索框", "state": "聚焦", "verdict": "added",
             "reason": "焦点环两轴（alpha 与亮度）都配上之后才有判据",
             "evidence": "Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift；R76–R78"},
        ],
    }


def codes(problems):
    return sorted(set(c for c, _ in problems))


class ShapeTests(unittest.TestCase):
    def test_a_wellformed_table_has_no_problems(self):
        self.assertEqual([], gate.check(base()))

    def test_duplicate_cell_is_named(self):
        data = base()
        data["rows"].append(dict(data["rows"][0]))
        self.assertIn("DUP_KEY", codes(gate.check(data)))

    def test_unknown_surface_or_state_is_named(self):
        data = base()
        data["rows"][0]["surface"] = "主窗口/不存在的表面"
        data["rows"][1]["state"] = "飘走"
        self.assertIn("UNKNOWN_CELL", codes(gate.check(data)))

    def test_a_string_that_looks_like_a_verdict_is_not_one(self):
        data = base()
        data["rows"][0]["verdict"] = "大概保留了"
        self.assertIn("BAD_VERDICT", codes(gate.check(data)))

    def test_reasonless_and_evidenceless_are_two_different_problems(self):
        short = base()
        short["rows"][0]["reason"] = "就这样"
        self.assertIn("REASONLESS", codes(gate.check(short)))
        noevid = base()
        noevid["rows"][1]["evidence"] = "   "
        self.assertIn("EVIDENCELESS", codes(gate.check(noevid)))

    def test_floor_is_monotone_and_cannot_be_a_wish(self):
        shrunk = base()
        shrunk["rows"] = shrunk["rows"][:1]
        self.assertIn("BELOW_FLOOR", codes(gate.check(shrunk)))
        lying = base()
        lying["floor_cleared"] = 9
        self.assertIn("FLOOR_LIES", codes(gate.check(lying)))

    def test_empty_rosters_are_named_not_silently_ok(self):
        empty = base()
        empty["verdicts"] = []
        self.assertIn("BAD_TABLE", codes(gate.check(empty)))


class ShapeRoundTwoTests(unittest.TestCase):
    """R128 补的三格：指针要可复查、名册扩张要付账、地板只数已清账。"""

    def test_a_round_number_alone_is_not_a_checkable_pointer(self):
        data = base()
        data["rows"][0]["evidence"] = "R14 / R15"
        self.assertIn("EVIDENCE_SHAPE", codes(gate.check(data)))

    def test_a_file_or_backlog_pointer_is_checkable(self):
        data = base()
        data["rows"][0]["evidence"] = "Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift"
        data["rows"][1]["evidence"] = "BACKLOG 61 / R19"
        self.assertEqual([], codes(gate.check(data)))

    def test_adding_a_surface_without_a_row_is_named(self):
        """分母扩张必须付账 —— 否则覆盖率会悄悄被稀释，而这看起来像"还在推进"。"""
        data = base()
        data["surfaces"].append("新加的表面")
        self.assertIn("SURFACE_UNCOVERED", codes(gate.check(data)))

    def test_adding_a_state_without_a_row_is_named(self):
        data = base()
        data["states"].append("拖拽中")
        self.assertIn("STATE_UNCOVERED", codes(gate.check(data)))

    def test_not_measured_does_not_count_as_cleared(self):
        """占位行不许把地板抬起来：它数的是"判过了"，不是"写了字"。"""
        data = base()
        data["rows"].append({"surface": "主窗口/列表行", "state": "禁用",
                             "verdict": "not-measured",
                             "reason": "这一格本轮没有依据，先占位，下一轮清账时替换成结论",
                             "evidence": "docs/motion_surface_ledger.json 的 verdict 词表"})
        self.assertEqual([], codes(gate.check(data)))
        data["floor_cleared"] = 3
        self.assertIn("BELOW_FLOOR", codes(gate.check(data)))


class RealTableTests(unittest.TestCase):
    def test_the_committed_ledger_passes_its_own_gate(self):
        """正对照的对照：真表必须自己过闸门（不然上面那批形状都是在判空气）。"""
        self.assertTrue(LEDGER.exists(), "缺少 %s" % LEDGER)
        data = json.load(io.open(str(LEDGER), encoding="utf-8"))
        self.assertEqual([], [m for c, m in gate.check(data)],
                         "已提交的清账表过不了自己的闸门")

    def test_uncovered_cells_are_counted_not_forgotten(self):
        """这张表的**目的**：没判过的格子要能被数出来。"""
        data = json.load(io.open(str(LEDGER), encoding="utf-8"))
        cells = len(data["surfaces"]) * len(data["states"])
        self.assertGreater(cells, len(data["rows"]),
                           "格子总数必须大于已清账行数，否则这张表在假装全部判过")
        self.assertGreaterEqual(len(data["rows"]), data["floor_cleared"])


if __name__ == "__main__":
    unittest.main()
