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
        """这张表的**目的**：没判过的格子要能被数出来 —— 而"数出来"不等于"必须还剩一些"。

        R207 之前这里写的是 `cells > rows`（"仓库现状不该是 0 未清账"）。那一格在 162 格全部判完的那天
        会变成一张**永远会红的门**，而它当初真正要防的从来不是"判完"，是**缩表装完**：
        删掉一个表面、或把 rows 清空、或把 not-measured 混进已清账。
        那三件事现在各有各的牙，所以这里换成"判完必须是真判完"的四条对账：
        ① 行数 == 名册乘积（没有整格缺失）；② 没有一格还是 not-measured（占位不算判过）；
        ③ 已清账数 == 行数（清账口径与词表一致）；④ 地板 == 已清账数（地板只能被真判过的格子抬起来）。
        而"名册被缩"由 `FLOOR_WENT_BACK`（对 HEAD 的地板）与 `MOTION_LEDGER_RETIRED`（退役要登记）管，
        不由这条假装的"必须没判完"管。
        """
        data = json.load(io.open(str(LEDGER), encoding="utf-8"))
        cells = len(data["surfaces"]) * len(data["states"])
        cleared = set(data["cleared_verdicts"])
        rows = data["rows"]
        cleared_n = len([r for r in rows if (r.get("verdict") or "") in cleared])
        self.assertGreaterEqual(len(rows), data["floor_cleared"])
        self.assertLessEqual(cleared_n, cells, "已清账比名册乘积还多 ⇒ 有格子被重复判（重格另有 DUP_KEY）")
        placeholder = [r for r in rows if (r.get("verdict") or "") not in cleared]
        if cleared_n == cells:
            self.assertEqual([], placeholder,
                              "全表判完了却还有 %d 格不在已清账词表里 ⇒ 那是一格占了位置的空白" % len(placeholder))
            self.assertEqual(cells, len(rows),
                              "判完必须是每格都有一行：名册 %d 格、表里 %d 行" % (cells, len(rows)))
            self.assertEqual(data["floor_cleared"], cleared_n,
                              "地板（%s）不等于已清账（%s）⇒ 地板是被抬上去的还是被写下来的？"
                              % (data["floor_cleared"], cleared_n))


class FloorBaselineTests(unittest.TestCase):
    """R143 / BACKLOG 184：地板的单调性要压在**表外**的基准上。

    `BELOW_FLOOR` 的两个量（已清账行数、`floor_cleared`）住在同一份可写文件里，
    所以「删五行 + 同时把地板降五」这一刀它防不住 —— 而那张表的全部意义就是"清账只能往前"。
    新出口 `FLOOR_WENT_BACK` 拿 HEAD 那一版的地板当基准。三格各管一个方向：
    降了要红、读不到基准不许算红、以及**在本仓库里基准必须读得到**（否则这一格会静默变成没判）。
    """

    def test_a_lower_floor_than_head_is_named(self):
        shrunk = base()
        shrunk["floor_cleared"] = 1
        shrunk["rows"] = shrunk["rows"][:1]        # 删行 + 降地板：BELOW_FLOOR 在这一刀下是绿的
        problems = gate.check(shrunk, head_floor=2)
        self.assertIn("FLOOR_WENT_BACK", codes(problems))
        self.assertNotIn("BELOW_FLOOR", codes(problems),
                         u"这一刀的证人必须只有一个；两个都红说明沙箱夹具没造出「删行 + 降地板」的形状")

    def test_an_absent_baseline_is_not_a_red(self):
        same = base()
        self.assertEqual([], [c for c, _ in gate.check(same, head_floor=None) if c == "FLOOR_WENT_BACK"],
                         u"读不到基准 ⇒ 这一格没判，不许当成红（也不许当成通过——由下面那格钉住）")

    def test_the_repository_can_actually_read_the_baseline(self):
        """正对照的另一半：如果 `head_floor_cleared()` 在这台机器上永远返回 None，上面两格都白写。"""
        value = gate.head_floor_cleared()
        self.assertIsNotNone(value, u"读不到 HEAD 的 floor_cleared ⇒ FLOOR_WENT_BACK 是恒真的死格子")
        committed = json.loads(io.open(LEDGER, encoding="utf-8").read())
        self.assertLessEqual(value - gate.retirement_allowance(committed, gate.head_table()),
                             int(committed["floor_cleared"]),
                             u"HEAD 的地板（%s，已减登记过的退役降幅）比工作树（%s）还高 ⇒ 现在就是该红的时刻，不是基准坏了"
                             % (value, committed["floor_cleared"]))


class LoosePointerTests(unittest.TestCase):
    """R203：指针「存在但点不开」是第三种坏法，原来那条 PATH_RE 完全看不见它。

    为什么单独一类：R131 那四条只认 `Sources/…` 这种开头，于是真表里有 7 行写的是
    `MenuBarController.swift`（只给文件名）或 `Views/SearchField.swift`（少写包根），
    闸门一路绿灯，而按图去找的人什么也打不开 —— 形状合法 ≠ 指得到东西。
    """

    def test_a_basename_only_pointer_is_named(self):
        data = base()
        data["rows"][0]["evidence"] = "MenuBarController.swift 的 NSMenuItem 用法"
        self.assertIn("EVIDENCE_PATH_PARTIAL", codes(gate.check(data)))

    def test_a_path_missing_the_package_prefix_is_named(self):
        data = base()
        data["rows"][0]["evidence"] = "Views/SearchField.swift 的 `isActive`"
        self.assertIn("EVIDENCE_PATH_PARTIAL", codes(gate.check(data)))

    def test_the_same_pointer_written_as_a_whole_path_stays_green(self):
        """正对照：同一件事、写成整路径 ⇒ 不许红（否则这条判据是恒红的门，会把人推去删指针）。"""
        data = base()
        data["rows"][0]["evidence"] = ("Sources/ClipboardHistoryApp/Managers/MenuBarController.swift 的 NSMenuItem 用法；"
                                       "Sources/ClipboardHistoryApp/Views/SearchField.swift 的 `isActive`")
        self.assertEqual([], codes(gate.check(data)))

    def test_a_name_that_cannot_be_found_anywhere_is_still_missing(self):
        """分得开「写得松」与「根本没这文件」，后者不能被 PARTIAL 洗白。"""
        data = base()
        data["rows"][0]["evidence"] = "ThisFileHasNeverExistsAnywhere.swift"
        found = codes(gate.check(data))
        self.assertIn("EVIDENCE_PATH_MISSING", found)
        self.assertNotIn("EVIDENCE_PATH_PARTIAL", found)

    def test_an_ambiguous_basename_is_its_own_name(self):
        """同名两个文件时不许猜一个：给独立编号，否则「按文件名对上」会变成随机通过。"""
        import tempfile
        root = tempfile.mkdtemp(prefix="gate-amb-")
        gate._index_cache[(root, tuple(gate.INDEX_DIRS))] = {"Foo.swift": {"a/Foo.swift", "b/Foo.swift"}}
        code, msg = gate.path_problem("Foo.swift", root)
        self.assertEqual("EVIDENCE_PATH_AMBIGUOUS", code)
        self.assertIn("a/Foo.swift", msg)

    def test_the_lax_rule_has_objects_on_the_real_table(self):
        """新尺在真表上必须真的扫到东西：否则上面五格只在合成样本上成立（R36 那一族）。"""
        data = json.load(io.open(str(LEDGER), encoding="utf-8"))
        matched = sum(1 for row in data["rows"] if gate.PATH_RE_LAX.findall(row.get("evidence") or ""))
        self.assertGreaterEqual(matched, 40,
                                "真表里只有 %d 行带路径形状的指针 ⇒ lax 判据没在判东西" % matched)
        loose = sum(1 for row in data["rows"]
                    for p in gate.PATH_RE_LAX.findall(row.get("evidence") or "")
                    if gate.resolve(p) is None)
        self.assertEqual(0, loose, "已提交的表上还有 %d 条点不开的指针" % loose)


class AbsenceTokenBoundaryTests(unittest.TestCase):
    """R208 / BACKLOG 226：缺席断言要比**标识符**，不是比子串。

    来历（都是这台机器上真发生过的）：`HistorySidebarView.swift` 里没有任何 `.disabled(`，
    但它有 `focusEffectDisabled()` —— 忽略大小写的**子串**比较因此把
    `缺席:...HistorySidebarView.swift=disabled` 判成"词在里面"⇒ ABSENT_CLAIM_FALSE。
    红得不对还不是最坏的：最坏的是人会去换一个更怪的词来绕过，
    于是缺席断言挑的词与被讨论的东西脱钩（尺子量错对象，R90/R100 那一族）。
    """

    SIDEBAR = "Sources/ClipboardHistoryApp/Views/HistorySidebarView.swift"

    def test_a_word_only_embedded_in_a_longer_identifier_is_not_present(self):
        data = base()
        data["rows"][0]["evidence"] = u"缺席:" + self.SIDEBAR + u"=disabled"
        self.assertEqual([], codes(gate.check(data)),
                         u"focusEffectDisabled() 不该把 `disabled` 判成在场")

    def test_a_standalone_identifier_still_makes_the_claim_false(self):
        """牙还在：`allowsHitTesting` 在这个文件里是独立标识符（两处），写着"没有"必须红。"""
        data = base()
        data["rows"][0]["evidence"] = u"缺席:" + self.SIDEBAR + u"=allowsHitTesting"
        self.assertIn("ABSENT_CLAIM_FALSE", codes(gate.check(data)))

    def test_a_dotted_or_call_form_token_still_matches(self):
        """正向：调用形/带点的写法不许被边界规则误伤（否则整条判据变瞎，而且是"假清白"那一侧）。

        `ForEach(` 在 SettingsView 里出现 4 次，每一次后面紧跟的都是标识符 ——
        若两侧都无条件要求边界，这 4 次全都匹配不上，"没有 ForEach(" 就会绿着过（R208 的第一版就这么坏过，
        由 D-205 记下）。这一格是那条坏法的正对照。
        """
        settings = "Sources/ClipboardHistoryApp/Views/SettingsView.swift"
        for token in (u"ForEach(", u"Toggle(", u".disabled("):
            data = base()
            data["rows"][0]["evidence"] = u"缺席:" + settings + u"=" + token
            found = codes(gate.check(data))
            self.assertIn("ABSENT_CLAIM_FALSE", found,
                          u"%s 真在 SettingsView 里 ⇒ 写着「没有」必须红（实测各出现 4/9/4 次）" % token)

    def test_call_form_token_is_absent_when_the_file_really_has_none(self):
        """同一条放松不许把"假清白"换成"假在场"：侧栏里一次 `ProgressView(` 都没有 ⇒ 声明照旧过。

        这一格的词是**量出来**的（`ProgressView(` 在 HistorySidebarView.swift 出现 0 次）。
        我最初写的是 `ForEach(`，实测那文件里有 2 次 —— 于是这一格自己红了一次，
        正好把"形容词不是读数"那一族又钉了一遍（见 D-205）。
        """
        data = base()
        data["rows"][0]["evidence"] = u"缺席:" + self.SIDEBAR + u"=ProgressView("
        self.assertEqual([], codes(gate.check(data)),
                         u"HistorySidebarView.swift 里 `ProgressView(` 出现 0 次")

    def test_the_positive_control_is_still_green(self):
        data = base()
        data["rows"][0]["evidence"] = u"缺席:" + self.SIDEBAR + u"=zzzNoSuchTokenAtAll"
        self.assertEqual([], codes(gate.check(data)))


if __name__ == "__main__":
    unittest.main()
