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

from scripts.ci_capture_gate import analyse, main, union_lines

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


class ReadingsChannelUnionTests(unittest.TestCase):
    """第二条读数通道的并集（R64 / BACKLOG 96）。

    下面这几份日志**全是合成的**（真 runner 日志只有上面那批用的 `RUNNER_FIXTURE` 一份）。
    它们证明的是"并集这一步有没有牙"，不证明真 CI 已经长成那个形状 —— 那要等下一次
    runner 的日志（同一句话在 R36 也写过，见 BACKLOG 49 的验收）。

    形状是 R63 在两台机器上量到的那一种：**用例判了、结论行也在、而判据自己写的那条读数没了**。
    只读 stdout 的闸门在这种时候会绿。
    """

    STDOUT = """
Test Case '-[ClipboardHistoryAppTests.UICaptureTests testQuickPickOverlayFillsItsPanelAndCanBeCaptured]' started.
CAPTURE_SELFTEST_11aa22bb
CAPTURE_NOT_RUN settings-stats-720x1040-dark.png 93% 未绘制 ⇒ 记为未运行
Test Case '-[ClipboardHistoryAppTests.UICaptureTests testQuickPickOverlayFillsItsPanelAndCanBeCaptured]' passed (1.000 seconds).
Test Case '-[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews]' passed (1.000 seconds).
"""
    # 那一条断言行 stdout 没打出来（真机丢的就是这种），文件通道里留着。
    READINGS = """
CAPTURE_SELFTEST_11aa22bb
/Users/x/UICaptureHarness.swift:321: error: -[ClipboardHistoryAppTests.UICaptureTests testCaptureKeyViews] : XCTAssertGreaterThan failed: ("0.0") is not equal to ("2125.0")
QUICKPICK_FIXTURE_ROWS all=5 typed(访达)=2 empty(zzz 不存在)=0
CAPTURE_NOT_RUN settings-stats-720x1040-dark.png 93% 未绘制 ⇒ 记为未运行
"""

    def write(self, text, suffix=".log"):
        handle, path = tempfile.mkstemp(suffix=suffix)
        os.close(handle)
        with open(path, "w", encoding="utf-8") as writer:
            writer.write(text)
        self.addCleanup(os.unlink, path)
        return path

    def test_stdout_alone_would_call_this_green(self):
        """正对照：**不给** `--readings` 时这份 stdout 必须是 0。

        这一臂是整组的前提 —— 如果只读 stdout 已经能红，那"并集有牙"就什么都没证明。
        """
        code, out = run_main(self.write(self.STDOUT))
        self.assertEqual(0, code, out)

    def test_the_readings_channel_is_what_makes_a_lost_red_visible(self):
        code, out = run_main(self.write(self.STDOUT), "--readings", self.write(self.READINGS))
        self.assertEqual(1, code, out)
        self.assertIn("testCaptureKeyViews", out)
        # 补回 2 行：断言行 + `QUICKPICK_FIXTURE_ROWS`（第三行 `CAPTURE_SELFTEST_11aa22bb`
        # 和 `CAPTURE_NOT_RUN …` 那行两边都有，精确整行比对把它们去掉了）。
        self.assertIn("补回=2", out, out)
        self.assertIn("只在文件通道里", out, "红是从第二条通道补回来的，这句话必须说出来")

    def test_the_union_is_an_exact_line_match_not_a_marker_match(self):
        """同一句读数**数字变了**就是另一条结论，不许被"按 marker 去重"吃掉。

        第一版并集我差点写成"按 marker 名去重"，那样 stdout 里只要有过
        `QUICKPICK_FIXTURE_ROWS` 这几个字，文件里那条不同数字的就会被丢掉。
        """
        stdout = "QUICKPICK_FIXTURE_ROWS all=5 typed(访达)=2 empty(zzz 不存在)=0\n"
        readings = ("QUICKPICK_FIXTURE_ROWS all=5 typed(访达)=2 empty(zzz 不存在)=0\n"
                    "QUICKPICK_FIXTURE_ROWS all=5 typed(访达)=3 empty(zzz 不存在)=0\n")
        recovered = union_lines(stdout, readings)
        self.assertEqual(1, len(recovered), recovered)
        self.assertIn("typed(访达)=3", recovered[0])

    def test_repeated_lines_are_recovered_once(self):
        """文件内部重复、以及与 stdout 重复，都不许把 `NOT_RUN=` 的条数撑虚。"""
        readings = (
            "CAPTURE_NOT_RUN settings-stats-720x1040-dark.png 93% 未绘制 ⇒ 记为未运行\n"
            "CAPTURE_NOT_RUN settings-stats-720x1040-dark.png 93% 未绘制 ⇒ 记为未运行\n"
            "SPARSE_EXEMPTION_OK quickpick-empty drawn=5.1% < quickpick-list drawn=17.9% - 3pt\n")
        code, out = run_main(self.write(self.STDOUT), "--readings", self.write(readings))
        self.assertEqual(0, code, out)
        self.assertIn("补回=1", out, out)
        self.assertIn("NOT_RUN=1", out, out)

    def test_a_missing_readings_file_is_a_named_red(self):
        path = self.write(self.STDOUT)
        code, out = run_main(path, "--readings", "/nonexistent/capture-readings.log")
        self.assertEqual(1, code, out)
        self.assertIn("第二条读数通道", out)
        self.assertIn("缺文件", out)
        # 结论行必须打在**这条红之前**（R53 / BACKLOG 75 同一句话）：
        # 通道坏了的时候，"这次判了多少"仍然是现场最有用的数。
        self.assertLess(out.index("CAPTURE_GATE_CASES"), out.index("CAPTURE_GATE_RESULT"), out)

    def test_an_empty_readings_file_is_a_red_too(self):
        """文件在但一行读数都没有 ⇒ `emit` 从没被调用过，等于还是只有一条腿。"""
        code, out = run_main(self.write(self.STDOUT), "--readings", self.write("\n\n   \n"))
        self.assertEqual(1, code, out)
        self.assertIn("存在但一行读数都没有", out)

    def test_no_channel_line_when_the_flag_is_not_given(self):
        """不给 `--readings` 的旧调用不许多打一行（本地直接 `python3 … log` 的用法要保持原样）。"""
        code, out = run_main(self.write(CLEAN_LOG))
        self.assertEqual(0, code, out)
        self.assertNotIn("CAPTURE_GATE_CHANNELS", out)


class CauseLineHasToMatchItsEvidenceTests(unittest.TestCase):
    """R92 / BACKLOG 128：同样"没有结论行"的三种成因，必须给出三句不同的话。

    现场不是合成出来的（run 38838819089 与 38846896495，2/2）：这道门印的是
    `这一步没跑到用例（挂死、崩溃、或 filter 打错）`，而同一次 run 里捕获那一步自己打的是
    `Executed 47 tests, with 9 tests skipped and 0 failures` + `captured frames: 124`。
    真的跑完了 —— 是它要读的那份 `/tmp/frames.log` 被**自检夹具**覆盖了
    （`cp FAKE_LOG /tmp/frames.log` 写进了作业共享的 /tmp，而闸门被挪到了自检之后）。
    所以这一格钉的不是"要红"（三支全都红，标准一个字没动），而是
    **"红的时候那句话必须有证据"**：把"读不到结论"说成"没跑到用例"，
    下一次就会有人去查产品/查 filter，而该查的是通道 —— 这条路我走了两轮。

    同源证人为什么必须是指认**这一份文件**的：读数通道只要落在同一个 `/tmp` 里，
    就可能属于别的步骤（R89 那朵红恰恰就是共享目录）。`CAPTURE_READINGS_SELFTEST … @ <路径>`
    是捕获卷自己写的，路径一致才谈得上"这一步跑到过"。
    """

    NO_CASES = "Building for debugging...\nBuild complete! (0.09s)\n"

    def new_path(self):
        handle, path = tempfile.mkstemp(suffix=".log")
        os.close(handle)
        self.addCleanup(os.unlink, path)
        return path

    def write(self, text):
        return self.write_at(self.new_path(), text)

    def write_at(self, path, text):
        with open(path, "w", encoding="utf-8") as writer:
            writer.write(text)
        return path

    def test_readings_witness_from_this_suite_blames_the_channel_not_the_step(self):
        readings = self.new_path()
        self.write_at(readings, "CAPTURE_READINGS_SELFTEST 文件通道 404 行 @ %s\n"
                                "TEXT_SIDE light 侧栏列读到 0 个偏离像素\n" % readings)
        code, out = run_main(self.write(self.NO_CASES), "--readings", readings)
        self.assertEqual(1, code, out)
        self.assertIn("CAPTURE_LOG_CHANNEL_LOST_CONCLUSIONS=1", out)
        self.assertNotIn("这一步没跑到用例", out, out)

    def test_readings_without_a_same_source_witness_cannot_clear_the_step(self):
        """读数有 404 行，但那份证人指认的是**另一个路径** ⇒ 不许把它当"这一步跑到过"。"""
        readings = self.new_path()
        self.write_at(readings, "CAPTURE_READINGS_SELFTEST 文件通道 404 行 @ /tmp/别的步骤/readings.log\n"
                                "TEXT_SIDE light 侧栏列读到 0 个偏离像素\n")
        code, out = run_main(self.write(self.NO_CASES), "--readings", readings)
        self.assertEqual(1, code, out)
        self.assertIn("CAPTURE_READINGS_FOREIGN_SOURCE=1", out)
        self.assertNotIn("CAPTURE_LOG_CHANNEL_LOST_CONCLUSIONS", out)

    def test_both_channels_empty_is_the_original_cause(self):
        readings = self.new_path()
        self.write_at(readings, "")
        code, out = run_main(self.write(self.NO_CASES), "--readings", readings)
        self.assertEqual(1, code, out)
        self.assertIn("没跑不算通过", out)
        self.assertNotIn("CAPTURE_LOG_CHANNEL_LOST_CONCLUSIONS", out)
        self.assertNotIn("CAPTURE_READINGS_FOREIGN_SOURCE", out)

    def test_the_input_size_line_names_how_much_the_gate_actually_read(self):
        """R92：红的时候要说得出"我读到的日志有多大"。

        这两次假红之所以要看第二眼才穿帮，就是因为闸门只报了"没有结论行"而没报
        "我手上这份日志一共才几行"。这一格同时钉住旧契约：不给 `--readings` 就不许多打。
        """
        readings = self.new_path()
        self.write_at(readings, "CAPTURE_NOT_RUN settings-x 95% 未绘制\n")
        body = "Building for debugging...\n"
        code, out = run_main(self.write(body), "--readings", readings)
        self.assertEqual(1, code, out)
        input_line = [l for l in out.splitlines() if l.startswith("CAPTURE_GATE_INPUT")]
        self.assertEqual(1, len(input_line), out)
        # 数字**算出来**再比，不写死：这一格要钉的是"报的字节数等于真读到的那份"，
        # 手抄一个常量只会把"数错了"和"报错了"混成一朵红（U-200 那一族的第三种形状）。
        self.assertIn("日志通道=1 行/%d 字节" % len(body.encode("utf-8")), input_line[0])
        code2, out2 = run_main(self.write(self.NO_CASES))
        self.assertEqual(1, code2, out2)
        self.assertNotIn("CAPTURE_GATE_INPUT", out2,
                         "不给 --readings 的旧调用不许多打一行（和 CAPTURE_GATE_CHANNELS 同一契约）")

    def test_the_three_cause_lines_are_three_different_sentences(self):
        """正对照的对照：三支如果印出同一句话，上面三格的断言就会有一格红。

        这条把它写成**显式的两两不同**，是为了让"有人为了省事把分支合并成一句"
        这件事红在名字上，而不是红在某一句 `assertNotIn` 的偶然措辞上。
        """
        seen = {}
        for label, body in (
                ("同源", "CAPTURE_READINGS_SELFTEST 文件通道 404 行 @ {path}\n"),
                ("异源", "CAPTURE_READINGS_SELFTEST 文件通道 404 行 @ /other/place.log\n"),
                ("空", "")):
            readings = self.new_path()
            self.write_at(readings, body.replace("{path}", readings))
            code, out = run_main(self.write(self.NO_CASES), "--readings", readings)
            self.assertEqual(1, code, "%s 这一支必须仍然是红：%s" % (label, out))
            line = [l for l in out.splitlines() if l.startswith("CAPTURE_GATE_RESULT=fail")]
            self.assertEqual(1, len(line), "%s 这一支该只有一句结论：%s" % (label, out))
            seen[label] = line[0]
        self.assertEqual(3, len(set(seen.values())), seen)


if __name__ == "__main__":
    unittest.main()
class MotionScopeTests(unittest.TestCase):
    """R112 / BACKLOG 166：把「有名字的红」这份账推广到**别的卷**时的四格。

    已知答案全部来自一份合成日志（两类用例、各一朵红），所以每一格都能被逐字说出：
    ①切片要真能切到（前缀按类名最后一段比 —— 全限定名 `Target.Module.XxxTests` 用
      `startswith("Xxx")` 才切得到，第一版按全串比 ⇒ 一朵都切不到）；
    ②**切片为空必须红**（R99 那一族：一个用例都没匹配到还打「绿」，等于把"前缀写错"
      记成"这一卷全过"）；
    ③`--report-only` 只降级**产品那一格**（红/低于地板），通道坏了照旧红；
    ④`--label` 换的是结论行的名字，两卷的账不许混在同一行里（166 的病根就是
      「捕获那一卷说'唯一的红是 157'，而动效那一卷的红没人记账」）。
    """

    FIXTURE = (
        "Test Case '-[ClipboardHistoryAppTests.MotionFilmstripTests testFrameIntervalsUnderStateChanges]' failed (0.500 seconds).\n"
        "error: -[ClipboardHistoryAppTests.MotionFilmstripTests testFrameIntervalsUnderStateChanges] : XCTAssertLessThanOrEqual failed: (\"196.7\") is greater than (\"120.0\")\n"
        "Test Case '-[ClipboardHistoryAppTests.UICaptureTests testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox]' failed (0.400 seconds).\n"
        "error: -[ClipboardHistoryAppTests.UICaptureTests testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox] : XCTAssertGreaterThan failed: (\"0\") is greater than (\"0\")\n"
        "Test Case '-[ClipboardHistoryAppTests.UIInteractionProbeTests testFrameIntervalsUnderStateChanges]' failed (0.300 seconds).\n"
        "error: -[ClipboardHistoryAppTests.UIInteractionProbeTests testFrameIntervalsUnderStateChanges] : XCTAssertLessThanOrEqual failed: (\"42.4\") is greater than (\"20.0\")\n"
        "Test Case '-[ClipboardHistoryAppTests.MotionFilmstripTests testSomeGreenThing]' passed (0.100 seconds).\n"
        "Test Case '-[ClipboardHistoryAppTests.UICaptureTests testAnotherGreenThing]' passed (0.100 seconds).\n"
    )

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        with io.open(self.path, "w", encoding="utf-8") as handle:
            handle.write(self.FIXTURE)

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def _run(self, *extra):
        """跑一次闸门，只拿退出码；结论行进 `last_output`，**不进真实 stdout**。

        为什么必须吞掉：CI 的 Release script tests 那一步把整段 stdout 写进 /tmp/test.log，
        而闸门读的就是那份日志 ⇒ 样张在这里打的 `*_GATE_*` 与 runner 真步的读数
        是同一种形状（BACKLOG 168：R112 第一份 runner 读数里 `MOTION_GATE_CASES`
        既有 `passed=34 skipped=32` 也有夹具的 `passed=1 skipped=0 failed=1`）。
        嵌套 `redirect_stdout` 不算实现：里层会吃掉外层要读的那份，所以捕获只在这一层做。
        """
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([self.path, "--quiet"] + list(extra))
        self.last_output = buf.getvalue()
        self.last_code = code
        return code

    def test_prefix_slices_on_the_last_class_component(self):
        self.assertEqual(1, self._run("--label", "SAMPLE", "--class-prefix", "MotionFilmstrip"),
                         "切到了一朵动效红 ⇒ 必须红（默认不是 report-only）")
        out = self._capture("--label", "SAMPLE", "--class-prefix", "MotionFilmstrip")
        self.assertIn("SAMPLE_GATE_CASES passed=1 skipped=0 failed=1 有名字的红=1", out)
        # 反向牙：切片之后**不能**把另一卷的那朵红也算进来
        self.assertNotIn("testSettingsCardHorizontalInset", out.split("SAMPLE_GATE_CASES")[1][:400])

    def test_two_prefixes_cover_both_motion_classes(self):
        """U-370：动效那两朵红**住在两个不同的类里**（bandCapture 在 `MotionFilmstripTests`、
        frameIntervals 在 `UIInteractionProbeTests`）。只切一个类的那版尺会把有红的跑报成 0 红
        —— 这是"新尺第一次跑必须拿已知答案的真日志验一正一负"那一族（R102 的 U-302 同形），
        本轮第一次真跑 R109 的 CI 日志就撞上：它明明有 frameIntervals 的红，切片却给 0。
        """
        one = self._capture("--label", "SAMPLE", "--class-prefix", "MotionFilmstrip", "--report-only")
        self.assertIn("SAMPLE_GATE_CASES passed=1 skipped=0 failed=1 有名字的红=1", one)
        two = self._capture("--label", "SAMPLE", "--class-prefix", "MotionFilmstrip",
                            "--class-prefix", "UIInteraction", "--report-only")
        self.assertIn("failed=2 有名字的红=2", two)
        # 反向牙：只切 UIInteraction 时，MotionFilmstrip 那朵不许被算进来
        other = self._capture("--label", "SAMPLE", "--class-prefix", "UIInteraction", "--report-only")
        self.assertIn("failed=1 有名字的红=1", other)
        self.assertNotIn("testBandCaptureIsCheaper", other.split("SAMPLE_GATE_CASES")[1][:300])

    def test_empty_slice_is_red_not_green(self):
        self.assertEqual(1, self._run("--label", "SAMPLE", "--class-prefix", "NoSuchSuite"))
        out = self._capture("--label", "SAMPLE", "--class-prefix", "NoSuchSuite")
        self.assertIn("SAMPLE_SCOPE_EMPTY=1", out)
        self.assertIn("整份日志里 5 个用例、3 朵红", out)

    def test_report_only_downgrades_the_product_verdict_but_not_the_channel(self):
        self.assertEqual(0, self._run("--label", "SAMPLE", "--class-prefix", "MotionFilmstrip",
                                      "--report-only"))
        out = self._capture("--label", "SAMPLE", "--class-prefix", "MotionFilmstrip", "--report-only")
        self.assertIn("SAMPLE_GATE_RESULT=report_only", out)
        self.assertIn("有 1 个用例红了", out)          # 红仍然要**打出来**，只是不拦
        # 而通道那一格不吃 report-only：读不到的日志照旧红
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, main(["/tmp/这一份日志不存在-r112.log", "--quiet", "--report-only"]))

    def test_the_second_red_shape_is_not_silent(self):
        """U-370：`FAILED 方法名：XCTAssert…` 这一种形状**没有类名** ⇒ 闸门不许把它读成 0 红。

        正对照：日志里只有这一种形状的红、且切片切到的是别的类 ⇒ `有名字的红=0`，
        但 `类未知名单=1` 必须露面，且整份那一跑必须红。
        """
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        with io.open(path, "w", encoding="utf-8") as handle:
            handle.write("Test Case '-[T.SomeTests testA]' passed (0.100 seconds).\n")
            handle.write("FAILED testFrameIntervalsUnderStateChanges：XCTAssertLessThanOrEqual failed: "
                         "(\"42.4\") is greater than (\"20.0\")\n")
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                whole = main([path, "--quiet"])
            out = buf.getvalue()
            self.assertEqual(1, whole, out)
            self.assertIn("类未知名单=1(testFrameIntervalsUnderStateChanges)", out)
            # 切片那一卷自己 0 红，但同一行必须把类未知的那一笔带出来（不许冒充"这一卷干净"）
            buf2 = io.StringIO()
            with contextlib.redirect_stdout(buf2):
                main([path, "--quiet", "--label", "SAMPLE", "--class-prefix", "SomeTests",
                      "--report-only"])
            self.assertIn("有名字的红=0 类未知名单=1", buf2.getvalue())
        finally:
            os.unlink(path)

    def test_label_moves_the_whole_verdict_line(self):
        cap = self._capture("--label", "CAP2", "--class-prefix", "UICapture")
        self.assertIn("CAP2_GATE_CASES", cap)
        self.assertNotIn("SAMPLE_GATE_CASES", cap)

    def _capture(self, *extra):
        self._run(*extra)
        return self.last_output
