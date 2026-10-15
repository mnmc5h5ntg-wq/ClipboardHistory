"""`scripts/probe_coverage_gate.py` 的自测（R62 / BACKLOG 92 / U-93）。

为什么需要这支闸门：R61 修「程序化选中视口外的行时列表不跟随」，那三条行为判据全住在
`UIInteractionProbeTests` 里，而 CI 那一步的读数是
`ui suite exit: 137  executed: 0  已下结论的用例: 0` —— 整卷一条都没跑完，步骤打一句
「在屏探针在无头 runner 上不可用」就 `exit 0`。那句话是真的，但它让
「61 的回归在 CI 上没人看」变成了一件没人再说的事。

测的是形状，不是耗时：每条红都对应一种"缺席被藏起来"的形状，且各自只能在那一格红。
`RUNNER_FIXTURE` 是 run 38603034761 那一步的逐字片段（`fixtures/r62_runner_ui.log`），
它当的是**正对照** —— 闸门必须对这份日志"绿"，而且绿的那一行里必须把缺席的判据逐条点名；
如果哪天它绿得什么都不说，第一条测试就会红。
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.probe_coverage_gate import analyse, main, source_cases

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r62_runner_ui.log"
RUNNER_FIXTURE = FIXTURE.read_text(encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift"
EXPECTATIONS = REPO / "scripts/probe_coverage_expectations.json"

CASES_A = ["testAlpha", "testBeta"]
LIST_A = {"testAlpha": {"runner": "can"}, "testBeta": {"runner": "cannot", "reason": "无头 runner 上窗口起不来"}}
CONCLUDED_BOTH = """
Test Case '-[M.T testAlpha]' passed (1.000 seconds).
Test Case '-[M.T testBeta]' passed (1.000 seconds).
"""


def reds_for(source=CASES_A, expectations=None, log=""):
    _, reds = analyse(source, expectations if expectations is not None else LIST_A, log)
    return reds


def codes(text):
    """把红清单里的状态名抽出来 —— 断言"红在哪一格"，而不是只断言"红了"。"""
    return {line.split()[0] for line in text}


class ProbeCoverageGateTest(unittest.TestCase):

    def test_real_ci_log_is_green_but_names_every_absent_judge(self):
        """正对照：真 CI 那份日志必须判成"没有新盲区"，同时把缺席逐条点名。

        这条同时钉住两件相反的事 —— 闸门不许因为整卷没跑就无脑红（那是 R36 之前那种
        "恒红的守卫最后被人删掉"），也不许绿得像什么都没发生。
        """
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["cases"]
        reading, reds = analyse(source_cases(SOURCE.read_text(encoding="utf-8")),
                                expectations, RUNNER_FIXTURE)
        self.assertEqual([], reds, f"真 CI 的日志不该判出红：{reds}")
        self.assertEqual(0, reading["concluded"], "这份日志里一条用例都没下结论")
        self.assertEqual(reading["source_cases"], len(reading["absent"]),
                         "缺席清单必须覆盖全部在屏判据，否则「没人跑」会被读成「都跑过了」")
        for judge in ("testOffScreenProgrammaticSelectionIsRevealedAndNotJumped",
                      "testRowIndexDriftDoesNotMoveTheViewport",
                      "testIntakeBehindATallPinnedBlockRevealsTheNewRow"):
            self.assertIn(judge, reading["absent"], f"R61 那三条判据里的 {judge} 没被点名 ⇒ 缺席被藏起来了")

    def test_registration_covers_every_probe_case_in_the_source(self):
        """登记与源码必须同一批：少一条就是 UNLISTED（新加判据不许静默免检）。"""
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["cases"]
        source = source_cases(SOURCE.read_text(encoding="utf-8"))
        self.assertTrue(source, "源码里一条 test 都没抓到 ⇒ 正则坏了，这条测试也是空的")
        missing = [n for n in source if n not in expectations]
        self.assertEqual([], missing, f"这些在屏判据没有登记：{missing}")
        stale = [n for n in expectations if n not in source]
        self.assertEqual([], stale, f"清单里有已经不存在的用例（免检牌会攒起来）：{stale}")

    def test_new_unregistered_case_is_red(self):
        reds = reds_for(source=CASES_A + ["testBrandNewJudge"])
        self.assertIn("UNLISTED", codes(reds), "新加一条在屏判据而清单没动 ⇒ 必须红")
        self.assertTrue(any("testBrandNewJudge" in r for r in reds), "红必须指名是哪一条")

    def test_stale_registration_is_red(self):
        expectations = dict(LIST_A)
        expectations["testDeletedLongAgo"] = {"runner": "cannot", "reason": "旧"}
        reds = reds_for(expectations=expectations)
        self.assertIn("STALE", codes(reds))

    def test_cannot_without_reason_is_red(self):
        expectations = {"testAlpha": {"runner": "can"},
                        "testBeta": {"runner": "cannot"}}
        reds = reds_for(expectations=expectations)
        self.assertIn("REASONLESS", codes(reds), "「跑不了」可以，「跑不了且说不清为什么」不行")

    def test_bad_runner_field_is_red(self):
        expectations = {"testAlpha": {"runner": "maybe"}, "testBeta": {"runner": "cannot", "reason": "x"}}
        self.assertIn("BAD_RUNNER_FIELD", codes(reds_for(expectations=expectations)),
                      "拼错的登记等于没登记")

    def test_registered_can_but_absent_is_red(self):
        reds = reds_for(log="Building for debugging...\nBuild complete! (0.09s)\n")
        self.assertIn("NOT_RUN", codes(reds), "说今天能跑却没跑成 ⇒ 必须红，不能滑进「已知边界」")

    def test_registered_cannot_but_concluded_is_red(self):
        """runner 哪天跑得动了，清单必须跟着改 —— 否则 cannot 会变成永久免检牌。"""
        reds = reds_for(log=CONCLUDED_BOTH)
        self.assertIn("NOW_RUNS", codes(reds))

    def test_assertion_red_is_named_not_just_an_exit_code(self):
        log = ("Test Case '-[M.T testAlpha]' failed (2.000 seconds).\n"
               "error: -[M.T testAlpha] : XCTAssertEqual failed: (\"[2, 60]\") is not equal to (\"[60]\")\n")
        reds = reds_for(log=log, expectations={"testAlpha": {"runner": "can"},
                                              "testBeta": {"runner": "can"}})
        self.assertIn("FAILED", codes(reds))
        self.assertTrue(any("testAlpha" in r for r in reds), "红必须说得出是哪条判据")

    def test_source_scan_ignores_names_mentioned_in_prose(self):
        """守卫不许命中自己，也不许命中注释里提到的用例名（R53 那一族）。"""
        text = """
        // 见 testGhostFromAComment() 的讨论 —— 注释里的调用形状也不算定义。
        func testRealOne() throws {}
        """
        self.assertEqual(["testRealOne"], source_cases(text))

    def test_missing_inputs_are_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            for argv in (
                [os.path.join(tmp, "nope.log"), "--expectations", str(EXPECTATIONS), "--source", str(SOURCE)],
                [str(FIXTURE), "--expectations", os.path.join(tmp, "nope.json"), "--source", str(SOURCE)],
                [str(FIXTURE), "--expectations", str(EXPECTATIONS), "--source", os.path.join(tmp, "nope.swift")],
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = main(argv)
                self.assertEqual(2, code, f"读不到输入却返回 {code} ⇒ 会被当成通过")

    def test_help_runs(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                main(["--help"])
        self.assertEqual(0, caught.exception.code)


if __name__ == "__main__":
    unittest.main()
