# -*- coding: utf-8 -*-
"""`scripts/ui_probe_report.py` 的自测（R86 / BACKLOG 92 路 a）。

这支脚本只回答一句话：**在屏那一卷停了，它是怎么停的**。
它不判产品，所以它的真值表全是"能不能给出名字"这一件事。
每一格都对应一种"缺席被藏起来"或"仪器故障冒充结论"的形状：

  ① 挂在哪一条 ⇒ 点名（有名字，绿）
  ② 每条都有结论 ⇒ 跑完了（绿）
  ③ 一条用例都没开始 ⇒ 进程级死法（绿，但说的是启动阶段）
  ④ 有结论却没有它的 started 行 ⇒ 日志不完整，差集不再可信（**红**）
  ⑤ 喂进来的是 CI 那一步的汇报片段 ⇒ 拿错了文件（**红**）
  ⑥ 空日志 ⇒ 我没有它的输出（**红**）
  ⑦ 文件读不到 ⇒ 仪器坏了（**红**）

⑤ 那一格用的是仓库里已有的**真**夹具 `fixtures/r62_runner_ui.log`
（run 38603034761 那一步的逐字汇报）。它不是编出来的：本轮第一次试脚本时就是拿它喂的，
而脚本当时**自信地**报了"进程在第一条用例开口之前就死了"—— 那是一句关于产品的假话，
真相是我拿错了文件。这一格钉的就是那次错误。
"""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from scripts.ui_probe_report import main, report

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r62_runner_ui.log"
RUNNER_ECHO = FIXTURE.read_text(encoding="utf-8")


def lines_of(text):
    out, _named = report(text)
    return "\n".join(out)


def started(name):
    return "Test Case '-[ClipboardHistoryAppTests.UIInteractionProbeTests %s]' started.\n" % name


def concluded(name, state="passed"):
    return ("Test Case '-[ClipboardHistoryAppTests.UIInteractionProbeTests %s]' %s (1.234 seconds).\n"
            % (name, state))


class TruthTableTests(unittest.TestCase):
    def testHungCaseIsNamed(self):
        """① 开了口没结论 ⇒ 点名那一条，且只点那一条。"""
        text = started("testAlpha") + concluded("testAlpha") + started("testBeta") + "line 6927 Killed: 9\n"
        out = lines_of(text)
        self.assertIn("UI_PROBE_HUNG=testBeta", out)
        self.assertNotIn("UI_PROBE_HUNG=testAlpha", out,
                        "testAlpha 已经有结论了还被报成挂死 ⇒ 差集算反了，"
                        "下一次 CI 会指着一条其实跑完的用例说它挂住")
        self.assertIn("UI_PROBE_PROGRESS started=2 concluded=1", out)
        self.assertIn("UI_PROBE_CRASH_MARKERS", out)

    def testAllConcluded(self):
        """② 每条都有结论 ⇒ 说"跑完了"，并且**不许**同时报挂死。"""
        text = started("testAlpha") + concluded("testAlpha") + started("testBeta") + concluded("testBeta", "skipped")
        out = lines_of(text)
        self.assertIn("UI_PROBE_ALL_CONCLUDED=1", out)
        self.assertNotIn("UI_PROBE_HUNG", out)
        self.assertIn("UI_PROBE_PROGRESS started=2 concluded=2", out)

    def testNoStartLineWithoutProcessProbeIsObservationOnly(self):
        """③a 原始日志里一条 `Test Case` 都没有，而**今天没量进程表** ⇒ 只许报观察。

        R86–R87 在这一格写的是"进程在第一条用例开口之前就死了"。R88 本机按 CI 原样重跑
        发现那是假话：`kill -9` 收掉 `swift-test` 之后 `xctest` 还活着在跑用例，
        而它的 stdout 在块缓冲里一行都没落盘（见 r88_spike_partial_channel.md）。
        ⇒ 日志的沉默不再是任何成因的名字。
        """
        text = "Building for debugging...\nBuild complete! (3.12s)\n"
        out, named = report(text)
        joined = "\n".join(out)
        self.assertIn("UI_PROBE_NO_START_LINE=1", joined)
        self.assertNotIn("UI_PROBE_NO_CASE_STARTED", joined,
                         "没量到进程表就报『死在启动阶段』= 把 R88 刚证伪的那句话又写回去")
        self.assertNotIn("UI_PROBE_START_LINES_LOST", joined)
        self.assertTrue(named, "『日志里没有 started 行』本身就是这一步要说清的形状，不许红也不许装没事")

    def testRunnerAliveTurnsSilenceIntoChannelLoss(self):
        """③b 收掉那一刻 xctest 还活着 ⇒ 名字是"started 行整块丢了"，不是"没开始"。"""
        text = "Building for debugging...\nBuild complete! (3.12s)\n"
        joined = "\n".join(report(text, 1)[0])
        self.assertIn("UI_PROBE_START_LINES_LOST=1", joined)
        self.assertNotIn("UI_PROBE_NO_CASE_STARTED", joined,
                         "用例在跑与用例没开始是两种相反的成因，同一份输出里不许同时出现")
        self.assertNotIn("UI_PROBE_NO_START_LINE", joined)

    def testRunnerDeadIsTheOnlyCaseThatMaySayNeverStarted(self):
        """③c 收掉那一刻连 xctest 都没起来 ⇒ 这时"死在启动阶段"才有资格说。"""
        text = "Building for debugging...\nBuild complete! (3.12s)\n"
        joined = "\n".join(report(text, 0)[0])
        self.assertIn("UI_PROBE_NO_CASE_STARTED=1", joined)
        self.assertNotIn("UI_PROBE_START_LINES_LOST", joined)
        self.assertTrue(report(text, 0)[1])

    def testTheThreeCausesAreMutuallyExclusive(self):
        """③d 三格互斥：同一份日志在 alive=1/0/没量 下各自只说一句话。

        这一格防的是"以后有人为了让 CI 绿，把两句话并成一句"（R86 的 ② 就是这么混进 ① 的）。
        """
        text = "Building for debugging...\nBuild complete! (3.12s)\n"
        marks = ("UI_PROBE_NO_START_LINE", "UI_PROBE_START_LINES_LOST", "UI_PROBE_NO_CASE_STARTED")
        for alive in (None, 1, 0):
            joined = "\n".join(report(text, alive)[0])
            hit = [m for m in marks if m in joined]
            self.assertEqual(len(hit), 1, "alive=%r 命中了 %s ⇒ 三格互相取消了" % (alive, hit))

    def testConcludedWithoutStartIsRed(self):
        """④ stdout 成块丢会把 started 丢掉而留下结论行 ⇒ 差集不可信，必须红。"""
        text = concluded("testAlpha") + concluded("testBeta", "failed")
        out, named = report(text)
        self.assertFalse(named, "有结论却没 started 行 = 这份日志不完整。"
                               "把它读成『挂死的那条已经点出来了』就是假绿")
        joined = "\n".join(out)
        self.assertIn("UI_PROBE_CONCLUDED_WITHOUT_START=testAlpha", joined)
        self.assertIn("UI_PROBE_CONCLUDED_WITHOUT_START=testBeta", joined)

    def testStepEchoIsNotTheRawLog(self):
        """⑤ 真夹具：CI 那一步的汇报片段，没有一条 `Test Case`。"""
        self.assertIn("ui suite exit: 137", RUNNER_ECHO)
        self.assertNotIn("Test Case", RUNNER_ECHO)
        out, named = report(RUNNER_ECHO)
        self.assertFalse(named, "拿错文件时不许给结论 —— 本轮真的错过一次")
        self.assertIn("UI_PROBE_NOT_THE_RAW_LOG=1", "\n".join(out))
        self.assertNotIn("UI_PROBE_NO_CASE_STARTED", "\n".join(out),
                        "摘要里没有 Test Case 行 ≠ 探针没开始跑。"
                        "这两句要是能互相冒充，③ 那格就成了万能免责牌")

    def testEmptyLogIsInstrumentFailure(self):
        """⑥ 空文件 ≠ "一条用例都没开始"：那是我没拿到输出。"""
        out, named = report("   \n")
        self.assertFalse(named)
        self.assertIn("UI_PROBE_LOG_EMPTY=1", "\n".join(out))

    def testDuplicateStartedLinesCountOnce(self):
        """重跑或两条通道并进来时同一条会出现两次 ⇒ 不许报成两条挂死。"""
        text = started("testAlpha") + started("testAlpha")
        out = lines_of(text)
        self.assertEqual(out.count("UI_PROBE_HUNG=testAlpha"), 1)
        self.assertIn("UI_PROBE_PROGRESS started=1 concluded=0", out)


class MainExitCodeTests(unittest.TestCase):
    def run_main(self, text, extra=()):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ui.log")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = main([path] + list(extra))
            return code, buffer.getvalue()

    def testRunnerAliveFlagReachesTheVerdict(self):
        """CI 把"收掉那一刻进程表"传进来 ⇒ 命令行这一层也要走到那一格（不能只在纯函数里对）。"""
        silence = "Building for debugging...\nBuild complete! (3.12s)\n"
        code_alive, out_alive = self.run_main(silence, ["--runner-alive", "1"])
        self.assertEqual(0, code_alive)
        self.assertIn("UI_PROBE_START_LINES_LOST=1", out_alive)
        code_dead, out_dead = self.run_main(silence, ["--runner-alive", "0"])
        self.assertEqual(0, code_dead)
        self.assertIn("UI_PROBE_NO_CASE_STARTED=1", out_dead)
        self.assertNotIn("UI_PROBE_START_LINES_LOST", out_dead)

    def testUnparsableRunnerAliveFallsBackToObservation(self):
        """CI 那一格自己坏了（不是数字）⇒ 不许猜，退回"只报观察"，并且把坏法打出来。"""
        silence = "Building for debugging...\nBuild complete! (3.12s)\n"
        code, out = self.run_main(silence, ["--runner-alive", "n/a"])
        self.assertEqual(0, code, "观察格仍然有名字 ⇒ 不红，但也不许升成因")
        self.assertIn("UI_PROBE_RUNNER_ALIVE_UNPARSED", out)
        self.assertIn("UI_PROBE_NO_START_LINE", out)
        self.assertNotIn("UI_PROBE_START_LINES_LOST", out)
        self.assertNotIn("UI_PROBE_NO_CASE_STARTED", out)

    def testNamedExitsZeroAndPrintsMarker(self):
        code, out = self.run_main(started("testAlpha"))
        self.assertEqual(0, code)
        self.assertIn("UI_PROBE_NAMED=1", out)
        self.assertIn("UI_PROBE_HUNG=testAlpha", out)

    def testUnnamedExitsOne(self):
        code, out = self.run_main(RUNNER_ECHO)
        self.assertEqual(1, code, "红必须落在退出码上：CI 那一步靠它决定要不要挡发布")
        self.assertIn("UI_PROBE_NAMED=0", out)

    def testUnreadableLogIsRedNotSilent(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main([os.path.join(tempfile.gettempdir(), "r86-definitely-absent.log")])
        self.assertEqual(1, code)
        self.assertIn("UI_PROBE_LOG_UNREADABLE", buffer.getvalue(),
                      "日志读不到时如果安静 exit 0，CI 会把它当成『这一卷没问题』")

    def testQuietStillPrintsTheVerdict(self):
        """`--quiet` 只许省进度行，不许省结论行（否则报告型那一步会看起来"什么都没发生"）。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ui.log")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(started("testAlpha"))
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                main([path, "--quiet"])
            out = buffer.getvalue()
        self.assertNotIn("UI_PROBE_PROGRESS", out)
        self.assertIn("UI_PROBE_HUNG=testAlpha", out)
        self.assertIn("UI_PROBE_NAMED=1", out)


class NonRedundancyTests(unittest.TestCase):
    def testGateAndReportAnswerDifferentQuestions(self):
        """两支闸门不许互相替代（R86 开脚本之前先确认过 `probe_coverage_gate.py` 没有这一格）。

        那一支判**集合级**：源码里有几条在屏判据、这次哪几条没下结论、缺席登记过没有。
        这一支判**因果级**：这一卷是怎么停的。
        只有前者会漏成：11 条全登记着、全都没结论、闸门照样绿 —— 那正是 R62 到 R85 的形状。
        """
        gate = Path(__file__).resolve().parents[1] / "probe_coverage_gate.py"
        text = gate.read_text(encoding="utf-8")
        self.assertNotIn("started", text,
                        "`probe_coverage_gate.py` 里出现了 started ⇒ 两支开始重叠，"
                        "要么合并、要么在这里写清为什么仍然要两支（不许留成『看着都像在判同一件事』）")


if __name__ == "__main__":
    unittest.main()
