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
        # U-429：这一格必须落在**名册里存在**的组合上。上一版写的是 `禁用`，而我在 U-427
        # 把夹具名册收窄成 `["悬停", "聚焦"]` 之后，这个测试的红就不再是关于地板的，
        # 而是 UNKNOWN_CELL —— 断言仍然失败，失败的原因却整条换掉了，而两种红看起来一样。
        # 收窄任何名册之前，先 grep 谁把这个成员串写在了字面量里。
        data["rows"].append({"surface": "浮层/搜索框", "state": "悬停",
                             "verdict": "not-measured",
                             "reason": "这一格本轮没有依据，先占位，下一轮清账时替换成结论",
                             "evidence": "docs/motion_surface_ledger.json 的 verdict 词表"})
        self.assertEqual([], codes(gate.check(data)))
        data["floor_cleared"] = 3
        self.assertIn("BELOW_FLOOR", codes(gate.check(data)))


class ShapeRoundThreeTests(unittest.TestCase):
    """R129：一条规则只能有一份实现。"""

    def test_floor_lies_is_reported_exactly_once(self):
        """`FLOOR_LIES` 曾在两处各查一遍 ⇒ 同一条规则两份实现。

        两份的后果不是"更保险"：变异任何一份都被另一份掩盖（刀落下去还是绿的），
        而读数会印两遍，读的人以为发生了两件事。所以这里断言的是**次数**，不是成员。
        """
        lying = base()
        lying["floor_cleared"] = 9
        printed = [c for c, _ in gate.check(lying)]
        self.assertEqual(1, printed.count("FLOOR_LIES"),
                         "FLOOR_LIES 印了 %d 遍（应恰好 1 遍）：%s" % (printed.count("FLOOR_LIES"), printed))

    def test_a_place_holder_cell_must_still_be_a_real_cell(self):
        """占位行首先是**合法行**：它的表面与状态都得名册里有，否则红的是别的事。

        M638 就是打在这一格上的：只测「表面不在名册里」的那一臂时，
        把「状态不在名册里」那一格整条摘掉，全卷 0 红（我这一版就是这么写的，
        而它上一版的失败恰好是这格造成的）。⇒ 两个维度必须各有证人。
        """
        wrong_surface = base()
        wrong_surface["rows"].append({"surface": "不存在的表面", "state": "悬停",
                                      "verdict": "not-measured",
                                      "reason": "这一格本轮没有依据，先占位，下一轮清账时替换成结论",
                                      "evidence": "docs/motion_surface_ledger.json 的 verdict 词表"})
        self.assertIn("UNKNOWN_CELL", codes(gate.check(wrong_surface)))
        wrong_state = base()
        wrong_state["rows"].append({"surface": "主窗口/列表行", "state": "禁用",
                                    "verdict": "kept",
                                    "reason": "这一格的依据是真的，但状态名册里没有这一档",
                                    "evidence": "Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift"})
        self.assertIn("UNKNOWN_CELL", codes(gate.check(wrong_state)))


class ShapeRoundFourTests(unittest.TestCase):
    """R131：指针要真的指得到东西，缺席断言要真的缺席。"""

    def test_a_pointer_to_a_missing_file_is_named(self):
        """形状合法（含 `Sources/`）但文件不存在 ⇒ 读的人点不开，等于没有指针。"""
        data = base()
        data["rows"][0]["evidence"] = "Sources/ClipboardHistoryApp/Views/NoSuchRowViewsAnywhere.swift"
        self.assertIn("EVIDENCE_PATH_MISSING", codes(gate.check(data)))

    def test_an_absence_claim_that_is_false_is_named(self):
        """写着「那个文件里没有 struct」，而 struct 就在里面 ⇒ 这条理由在替没做的东西开脱。"""
        data = base()
        data["rows"][0]["evidence"] = (
            "Sources/ClipboardHistoryApp/Views/NoticeBanner.swift "
            "缺席:Sources/ClipboardHistoryApp/Views/NoticeBanner.swift=struct")
        self.assertIn("ABSENT_CLAIM_FALSE", codes(gate.check(data)))

    def test_an_absence_claim_that_holds_is_not_a_problem(self):
        """正对照：同一个文件、一个真的不在里面的词 ⇒ 不许红（否则这条判据是恒红的门）。"""
        data = base()
        data["rows"][0]["evidence"] = (
            "Sources/ClipboardHistoryApp/Views/NoticeBanner.swift "
            "缺席:Sources/ClipboardHistoryApp/Views/NoticeBanner.swift=zzzNoSuchToken")
        self.assertEqual([], codes(gate.check(data)))

    def test_an_absence_claim_on_a_missing_file_is_its_own_name(self):
        """文件都不在，缺席就无从验证 ⇒ 单独一个名字，不许混进 ABSENT_CLAIM_FALSE。"""
        data = base()
        data["rows"][0]["evidence"] = "缺席:Sources/ClipboardHistoryApp/Views/Gone.swift=whatever"
        found = codes(gate.check(data))
        self.assertIn("ABSENT_CLAIM_UNVERIFIABLE", found)
        self.assertNotIn("ABSENT_CLAIM_FALSE", found)

    def test_the_new_rules_are_not_vacuous_on_the_real_table(self):
        """新判据在真表上必须有对象：至少 10 行带着**能解析**的路径。

        为什么这条要单独存在：如果真表里一行路径都没有，上面四条就只在合成样本上成立
        （R36 那一族 —— 闸门红在自己的判据从没跑到东西上）。
        """
        import os
        data = json.load(io.open(str(LEDGER), encoding="utf-8"))
        resolved = 0
        for row in data["rows"]:
            for path in gate.PATH_RE.findall(row.get("evidence") or ""):
                if gate.resolve(path):
                    resolved += 1
                    break
        self.assertGreaterEqual(resolved, 10,
                                "真表里只有 %d 行带着解析得到的路径 ⇒ 新判据没在判东西" % resolved)


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
