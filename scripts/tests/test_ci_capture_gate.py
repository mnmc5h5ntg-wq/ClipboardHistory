"""`scripts/ci_capture_gate.py` 的自测（R36 / BACKLOG 49 / U-59）。

这条闸门要判的是"**还有没有没被登记的红色**"，所以它的四件事必须分开测：
① 有红 ⇒ 必须 1（否则闸门就是装饰）；
② 只有已登记的 `*_NOT_RUN` ⇒ 必须 0（否则 report-only 换成了另一种"红了没人看"）；
③ **一个用例都没跑到** ⇒ 必须 1（"没跑"永远不是通过 —— 这一步以前就是死在这一格上）；
④ 判出绿的数量低于门 ⇒ 必须 1（把像素判据全改成 `throw XCTSkip` 也是一条红都没有）。

`RUNNER_FIXTURE` 不是手写的样例，是 run 38473962277 里那一步的**逐字日志片段**
（`scripts/tests/fixtures/r36_runner_capture.log`，用 `gh api .../jobs/115559876687/logs` 取的）。
它当的是**正对照**：闸门必须对这份日志红，而且红在那 4 行上、不多不少。
`CLEAN_LOG` 是**合成的**（把同一批行的红换成 `*_NOT_RUN`），它只证明"登记了就不挡"，
它**不**证明真 CI 已经是那个形状 —— 那要等下一次 CI 的日志，见 BACKLOG 49 的验收。
"""
import contextlib
import io
import os
import re
import tempfile
import unittest
from pathlib import Path

from scripts.ci_capture_gate import analyse, main

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r36_runner_capture.log"
RUNNER_FIXTURE = FIXTURE.read_text(encoding="utf-8")
HEADER_LINES = [line for line in RUNNER_FIXTURE.splitlines() if line.startswith("# ")]
BODY = "\n".join(line for line in RUNNER_FIXTURE.splitlines() if not line.startswith("# "))

CLEAN_LOG = """
Test Case '-[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews]' started.
CAPTURE_CAPABILITY settings族整体空白=是（族内最低未绘制 90.6% / 18 张） / 这一台见过黑带=否 / 底行墨尺活着=是（全帧最大 100.0%）
CAPTURE_NOT_RUN settings-privacy-excluded-720x1040-light.png 95% 未绘制，而 settings 族在这台机器上每一张都超过 85% ⇒ 记为未运行
MATERIAL_BLIND_NOT_RUN 这台机器 102 帧里一处黑带都没有，而名单上有 9 处 ⇒ 那一方向无从判起
Test Case '-[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews]' passed (20.100 seconds).
Test Case '-[ClipboardHistoryAppTests.UICaptureTests testCaptionTextStaysOnTheSecondaryTier]' passed (18.000 seconds).
Test Case '-[ClipboardHistoryAppTests.UICaptureTests testInkDirectionRulerReadsBothEnds]' skipped (0.001 seconds).
"""

NO_CASE_LOG = """
Building for debugging...
Build complete! (0.09s)
"""


def run_main(*arguments):
    """真跑一遍 `main()`，把退出码和 stdout 都拿回来（退出码是这条闸门唯一的产物）。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(list(arguments))
    return code, buffer.getvalue()


class CaptureGateFixtureTests(unittest.TestCase):
    def test_the_real_runner_log_is_caught_as_one_named_red_case(self):
        """正对照：那份**真被吞过**的日志必须判红，并且要能指名是谁。"""
        result = analyse(RUNNER_FIXTURE)
        self.assertEqual(4, len(result["reds"]), result["reds"])
        # 4 条断言行全属于**同一个用例** —— 所以"有名字的红"是 1 个，不是 4 个。
        self.assertEqual(["ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews"],
                         result["red_cases"])
        self.assertEqual(["ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews"],
                         result["failed_cases"])
        self.assertEqual([], result["crashed"], "有断言行的红不算崩溃臂：这一份要能读出消息")

    def test_the_verdict_tally_is_the_one_in_the_log(self):
        result = analyse(RUNNER_FIXTURE)
        self.assertTrue(result["ran_cases"])
        self.assertEqual(19, result["passed"])
        self.assertEqual(8, result["skipped"])
        self.assertEqual(1, len(result["failed_cases"]))

    def test_the_summary_line_counts_assertions_not_cases(self):
        """口径：`Executed 28 tests, with 8 tests skipped and 4 failures` 里那个 4 是**断言**条数。

        闸门故意不读这一行。读了就会把"1 个用例红"报成"4 个用例红"，
        而下一次有人拿这个数字去对账（本仓库真的对过账：见账本 D-038 那一族"单调量"的讨论）。
        这里把两件事同时钉住：那行在日志里、真实失败用例数是 1。
        """
        summary = re.search(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures",
                            RUNNER_FIXTURE)
        self.assertIsNotNone(summary, "夹具里应当有那行汇总")
        self.assertEqual(("28", "8", "4"), summary.groups())
        self.assertEqual(1, len(analyse(RUNNER_FIXTURE)["failed_cases"]))

    def test_the_headers_own_prose_does_not_become_a_red(self):
        """夹具头部注释里写着"`error: -[类 方法]`"这种形状 —— 它不许被当成红。

        这就是 `RED` 收紧到 ASCII 标识符的原因：Python 的 `\\w` 默认含中文，
        按 `\\w+` 写的话，**这份夹具的说明文字、门脚本自己的注释**都会变成假红，
        而假红被吞掉之后，这条闸门就又多了一种"红了没人看"。
        """
        self.assertGreaterEqual(len(HEADER_LINES), 3)
        self.assertTrue(any("error: -[" in line for line in HEADER_LINES),
                        "头部注释里必须真的有那个形状，否则这一臂没有判别力")
        self.assertEqual(len(analyse(RUNNER_FIXTURE)["reds"]), len(analyse(BODY)["reds"]))

    def test_the_numbers_behind_the_swift_floors_are_the_ones_in_the_log(self):
        """Swift 侧那两条新地板（0.85 / 0.5）是照这份日志写的 —— 数字要能在这份日志里查到。

        不这么写的话，注释里的"runner 最低 90.6%"就是**注释替事实背书**（这个仓库栽过好几次）。
        """
        rows = re.findall(r"\s(\S+\.png)\s+transparent=([\d.]+)%\s+blackBandPt=([\d.]+)"
                          r"\s+bottomInk=([\d.]+)%", RUNNER_FIXTURE)
        self.assertEqual(102, len(rows), "这一步应当逐帧报 102 张（51 帧 × 亮暗）")
        settings = [float(r[1]) for r in rows if r[0].startswith("settings-")]
        self.assertEqual(18, len(settings))
        self.assertEqual(90.6, min(settings), "写进 `captureFamilyBlankFraction` 的那个下界")
        self.assertEqual(95.9, max(settings))
        self.assertEqual(0.0, max(float(r[2]) for r in rows), "runner 上一处黑带都没有")
        inks = {r[0]: float(r[3]) for r in rows}
        self.assertEqual(100.0, max(inks.values()), "尺在 runner 上是活的：这条撑着 CONTENT_FIT 的绿")
        self.assertEqual(0.0, inks["sidebar-history-300x520-light.png"])
        self.assertEqual(100.0, inks["sidebar-history-300x520-dark.png"],
                         "同一帧的暗色版两台机器都是 100% ⇒ 差的是排版不是尺（U-59）")


class CaptureGateExitCodeTests(unittest.TestCase):
    def test_registered_not_run_is_not_a_red(self):
        result = analyse(CLEAN_LOG)
        self.assertEqual([], result["reds"])
        self.assertTrue(result["ran_cases"])
        self.assertEqual(2, len(result["not_run"]), result["not_run"])
        self.assertEqual(["CAPTURE_NOT_RUN", "MATERIAL_BLIND_NOT_RUN"],
                         result["not_run_markers"])

    def test_a_log_without_cases_is_a_failure_not_a_pass(self):
        result = analyse(NO_CASE_LOG)
        self.assertFalse(result["ran_cases"])

    def test_exit_codes_on_the_three_ways_this_step_can_be_wrong(self):
        handle, path = tempfile.mkstemp(suffix=".log")
        os.close(handle)
        try:
            with open(path, "w", encoding="utf-8") as writer:
                writer.write(RUNNER_FIXTURE)
            code, out = run_main(path)
            self.assertEqual(1, code)
            self.assertIn("CAPTURE_GATE_RESULT=fail", out)
            self.assertIn("testCaptureKeyViews", out)

            code, out = run_main(path, "--min-passed", "15")
            self.assertEqual(1, code, "红优先于门：两条都要报，但结论只有一个")
        finally:
            os.unlink(path)

        handle, path = tempfile.mkstemp(suffix=".log")
        os.close(handle)
        try:
            with open(path, "w", encoding="utf-8") as writer:
                writer.write(CLEAN_LOG)
            code, out = run_main(path)
            self.assertEqual(0, code, out)
            # ④ 全绿但只判出 2 条 ⇒ 低于门就红（"整批退回 skip"的那一种）。
            code, out = run_main(path, "--min-passed", "3")
            self.assertEqual(1, code)
            self.assertIn("skip 不是通过", out)
            code, out = run_main(path, "--min-passed", "2")
            self.assertEqual(0, code)
            self.assertIn("CAPTURE_GATE_RESULT=ok", out)
        finally:
            os.unlink(path)

        handle, path = tempfile.mkstemp(suffix=".log")
        os.close(handle)
        try:
            with open(path, "w", encoding="utf-8") as writer:
                writer.write(NO_CASE_LOG)
            code, out = run_main(path)
            self.assertEqual(1, code)
            self.assertIn("没跑不算通过", out)
        finally:
            os.unlink(path)

    def test_a_missing_log_is_a_failure_not_a_pass(self):
        code, out = run_main("/nonexistent/definitely-not-a-log.log")
        self.assertEqual(1, code)
        self.assertIn("CAPTURE_GATE_RESULT=fail", out)

    def test_help_runs(self):
        """`--help` 必须 0（`test_script_help_runs.py` 会替全仓库的脚本问这一句）。"""
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(0, raised.exception.code)

    def test_a_crash_without_assertion_lines_still_has_a_name(self):
        """只有结论行的那种红（崩溃 / 超时）不许被当成"一条红都没有"。"""
        log = ("Test Case '-[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews]' started.\n"
               "Test Case '-[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews]' failed (0.001 seconds).\n"
               "Test Case '-[ClipboardHistoryAppTests.UICaptureTests testInkDirectionRulerReadsBothEnds]' passed (1.000 seconds).\n")
        result = analyse(log)
        self.assertEqual([], result["reds"], "没有断言行")
        self.assertEqual(["ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews"],
                         result["red_cases"], "但用例名必须进来")
        self.assertEqual(result["red_cases"], result["crashed"])


if __name__ == "__main__":
    unittest.main()
