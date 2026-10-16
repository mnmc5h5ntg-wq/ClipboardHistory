"""`scripts/probe_coverage_gate.py` 的自测（R62 / BACKLOG 92 / U-93）。

为什么需要这支闸门：R61 修「程序化选中视口外的行时列表不跟随」，那三条行为判据全住在
`UIInteractionProbeTests` 里，而 CI 那一步的读数是
`ui suite exit: 137  executed: 0  已下结论的用例: 0` —— 整卷一条都没跑完，步骤打一句
「在屏探针在无头 runner 上不可用」就 `exit 0`。那句话是真的，但它让
「61 的回归在 CI 上没人看」变成了一件没人再说的事。

测的是形状，不是耗时：每条红都对应一种"缺席被藏起来"的形状，且各自只能在那一格红。
`RUNNER_FIXTURE` 是 run 38603034761 那一步的逐字片段（`fixtures/r62_runner_ui.log`），
`R94_FIXTURE` 是 run 38857388449 那一步的**形状重建**（名字/判定/顺序/计数逐字读来，
只有秒数是我补的 —— 那份夹具的头部把 provenance 写全了，两件事必须分开记）。
两份合起来当**双向**正对照：
  * 旧那份一条结论都没有 ⇒ 登记翻成 can 之后闸门必须**红，且红有名字**（NOT_RUN ×6）；
  * 新那份有六条结论 ⇒ 必须**绿**，且绿的那几行把缺席分成 stalled / queued。
如果哪天它绿得什么都不说，或者红得说不出是谁，第一条与第二条测试就会红。
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.probe_coverage_gate import analyse, execution_order, main, source_cases

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r62_runner_ui.log"
RUNNER_FIXTURE = FIXTURE.read_text(encoding="utf-8")
R94_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r94_runner_ui.log"
R94_LOG = R94_FIXTURE.read_text(encoding="utf-8")
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

    def test_r62_log_is_red_by_name_for_every_case_the_roster_says_can(self):
        """旧那份（一条结论都没有）配上翻过的名册 ⇒ 必须红，且每条红都带用例名。

        这条是 R94 改写的：原来它断言「真 CI 日志该绿」，那是**全 can=0 时代**的契约 ——
        名册里 `runner=can` 一条都没有时，"整卷没跑"就只能被 `PROBE_NOT_RUN` 点名而不能红
        （R62 当时的顾虑：恒红的守卫最后会被人删掉）。BACKLOG 134 把六条翻成 can 之后，
        同一份日志的正确处置**就是红**：登记说今天该跑到，而它没跑到。
        所以这里断言的不是"绿"，是两件相反的事 ——
          ① 红的只有 NOT_RUN，且名字与名册里 can 的那几条**逐一对应**（不许多也不许少）；
          ② `cannot` 的那几条**不**出现在红里（它们本来就没被承诺过，红了就是恒红守卫）。
        """
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["cases"]
        reading, reds = analyse(source_cases(SOURCE.read_text(encoding="utf-8")),
                                expectations, RUNNER_FIXTURE)
        can_names = sorted(n for n, e in expectations.items() if e.get("runner") == "can")
        self.assertTrue(can_names, "名册里一条 can 都没有 ⇒ 这条测试在替一个空契约作证，先红给你看")
        self.assertEqual({"NOT_RUN"}, codes(reds),
                         f"这份日志只该红在 NOT_RUN 这一格，实际红了：{reds}")
        self.assertEqual(can_names, sorted(r.split()[1].split("：")[0] for r in reds),
                         "红点名的用例必须正好是登记说 runner 跑得动的那几条")
        # 硬名字：R61 那三条行为判据 + R92 之前一直 skip 的那条帧率判据，
        # 全部来自 run 38857388449 的 NOW_RUNS 读数（见 fixtures/r94_runner_ui.log 头部）。
        for judge in ("testOffScreenProgrammaticSelectionIsRevealedAndNotJumped",
                      "testIntakeBehindATallPinnedBlockRevealsTheNewRow",
                      "testRowIndexDriftDoesNotMoveTheViewport"):
            self.assertIn(judge, reading["absent"], f"{judge} 没被缺席清单点名 ⇒ 缺席被藏起来了")
        self.assertEqual(0, reading["concluded"], "这份日志里一条用例都没下结论")
        self.assertEqual(reading["source_cases"], len(reading["absent"]),
                         "缺席清单必须覆盖全部在屏判据，否则「没人跑」会被读成「都跑过了」")

    def test_r94_log_is_green_and_separates_queued_from_open_not_closed(self):
        """新那份（六条有结论、一条开口没闭口）配上名册 ⇒ 必须绿，但绿得有内容。

        绿只说明"没有新盲区"；这一格真正要钉的是**缺席被分成两种**：
        开了口没闭口的（132 那一格）与一次都没轮到的（只能登记"排在它之后"）。
        R94 之前这两种在登记里是一句话，而那句话是我从字母序**推断**的。
        名字只许 `ui_probe_report.py` 出（两支闸门的分工，见 `NonRedundancyTests`），
        所以这里判的是**计数**与 queued 的名字，不是"谁挂住"。
        """
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))["cases"]
        source = source_cases(SOURCE.read_text(encoding="utf-8"))
        reading, reds = analyse(source, expectations, R94_LOG)
        self.assertEqual([], reds, f"runner 这次跑得动的都跑到了，不该再判红：{reds}")
        self.assertEqual(6, reading["concluded"], "读数是「本次下结论=6」，多一条少一条都算量错")
        self.assertEqual(7, reading["appeared"], "started=7：第 8 条根本还没露面")
        self.assertEqual(1, reading["open_not_closed"],
                         "开口没闭口的必须正好一条 —— 两条就是又一卷被吞，零条就是这把尺读不到运动")
        self.assertEqual(sorted(["testRowGesturesWorkInsideTheRealSidebarContainer",
                                 "testRowIndexDriftDoesNotMoveTheViewport",
                                 "testRowProxyCensusAsksTheConsequenceNotTheShape",
                                 "testSidebarListFocusRingAfterClick"]),
                         sorted(reading["queued"]),
                         "一次都没轮到的那四条要能被单独列出来 —— 登记里的「排在它之后」靠这一行才有出处")
        self.assertTrue(reading["prefix"], "结论是执行序的连续前缀；断了就说明执行序不是我读到的那样")

    def test_execution_order_reads_the_log_itself_not_the_alphabet(self):
        """执行序这把尺自己要先验：它读的是**露面顺序**，不是把名字排了个序。

        同一族的老账（R84 的坐标约定、R90 的通道事实）：一把尺如果悄悄按它想证明的东西排序，
        那它永远证明那个东西。这里喂一份**倒字母序**的日志，顺序必须跟着日志走。
        """
        log = ("Test Case '-[M.T testZulu]' passed (1.000 seconds).\n"
               "Test Case '-[M.T testAlpha]' started.\n"
               "Test Case '-[M.T testMike]' passed (1.000 seconds).\n")
        order, appeared, _interleaved = execution_order(log)
        self.assertEqual(["testZulu", "testAlpha", "testMike"], order, "顺序被排序了 ⇒ 量的不是执行序")
        self.assertEqual({"testZulu": True, "testAlpha": False, "testMike": True}, appeared)
        _, reds = analyse(order, {"testZulu": {"runner": "can"},
                                 "testAlpha": {"runner": "can"},
                                 "testMike": {"runner": "can"}}, log)
        self.assertEqual(["NOT_RUN testAlpha：登记为 runner=can，而这次日志里没有它的结论行"], reds,
                         "空洞在中间 ⇒ 只有它自己该红，别的都不许多嘴")
        reading, _ = analyse(order, {}, log)
        self.assertFalse(reading["prefix"], "前缀断了要说 false；写成 true 就是把诊断藏起来")

    def test_execution_order_with_nothing_appearing_is_not_a_vacuous_pass(self):
        """一条都没露面 ⇒ 「前缀」这个问题没有对象，读数必须是"无从判定"而不是 1。"""
        order, appeared, _interleaved = execution_order("Build complete! (12.3s)\n")
        self.assertEqual(([], {}), (order, appeared))
        reading, _ = analyse(["testAlpha"], {"testAlpha": {"runner": "cannot", "reason": "r"}}, "")
        self.assertIsNone(reading["prefix"], "空日志把前缀读成 True ⇒ 空洞的真话会冒充结论")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main([str(FIXTURE), "--expectations", str(EXPECTATIONS), "--source", str(SOURCE)])
        text = out.getvalue()
        self.assertEqual(1, code, "r62 那份配 can 登记必须红")
        self.assertIn("前缀=无从判定", text,
                      "『无从判定』这四个字必须出现在读数里，不然读日志的人会把它当成通过")

    def test_the_new_readings_are_printed_and_none_of_them_is_a_gate(self):
        """两行读数必须真被打出来（没人打印的读数等于没有读数），且**不许**因此多一条红，
        也不许在这一支里报出"挂住的是谁"那个名字 —— 那是另一支的活儿（`NonRedundancyTests`）。"""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main([str(R94_FIXTURE), "--expectations", str(EXPECTATIONS), "--source", str(SOURCE)])
        text = out.getvalue()
        for marker in ("PROBE_ORDER 露面=7/11 未闭口=1 前缀=1",
                       "PROBE_QUEUED 4/11 条一次都没轮到"):
            self.assertIn(marker, text, f"读数少了这一行：{marker}\n实际输出：{text}")
        self.assertNotIn("PROBE_ORDER_WARNING", text, "这份日志是连续前缀，警告不该出现")
        order_line = [l for l in text.splitlines() if l.strip().startswith("PROBE_ORDER ")][0]
        self.assertNotIn("testRightClickMenus", order_line,
                         "这一支开始点名『挂住的是谁』了 ⇒ 两支闸门的分工被抹掉，"
                         "那个名字归 ui_probe_report（它有两条通道互相签字）")

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


class InterleavedLogTests(unittest.TestCase):
    """BACKLOG 135（R94 的 M521 那一格）：一份日志里出现第二个写入者时会发生什么。

    来历：`/tmp/ui.log` 是 `swift test > … 2>&1` 的共享通道，R80b 那次是两行被缝成一行，
    这一次要防的是"同一例的 started 出现在它的结论之后"。第一版的写法把状态改回"未结论"，
    于是 `未闭口` 凭空 +1 —— 而登记里的成因那句话现在**依据的就是这个数**。
    现在的处置：结论是粘的，交错本身打成一条有名字的读数（不判红：它是关于日志的，不是关于产品的）。
    """

    LOG = ("Test Case '-[M.T testA]' started.\n"
           "Test Case '-[M.T testA]' passed (1.000 seconds).\n"
           "Test Case '-[M.T testA]' started.\n"
           "Test Case '-[M.T testB]' started.\n")

    def test_conclusion_is_sticky_and_the_interleave_is_named(self):
        order, appeared, interleaved = execution_order(self.LOG)
        self.assertEqual(["testA", "testB"], order)
        self.assertTrue(appeared["testA"], "结论被后来的 started 抹掉了 ⇒ 未闭口会凭空多一条")
        self.assertEqual(["testA"], interleaved)

    def test_open_count_is_not_inflated_and_the_reading_is_printed(self):
        expectations = {"testA": {"runner": "can"},
                        "testB": {"runner": "cannot", "reason": "r"}}
        reading, reds = analyse(["testA", "testB"], expectations, self.LOG)
        self.assertEqual(1, reading["open_not_closed"], "testB 才是唯一没闭口的那条")
        self.assertEqual(["testA"], reading["interleaved"])
        self.assertEqual([], reds, "交错是**关于日志**的诊断，不该变成产品红")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ui.log")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(self.LOG)
            exp = os.path.join(tmp, "exp.json")
            with open(exp, "w", encoding="utf-8") as handle:
                json.dump({"cases": expectations}, handle)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([path, "--expectations", exp, "--source", str(SOURCE)])
        self.assertIn(code, (0, 1), "退出码只许是绿或红，2 意味着有一份输入没被读到")
        text = out.getvalue()
        self.assertIn("PROBE_ORDER_INTERLEAVED 1 条", text, text)
