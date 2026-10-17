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
import sys
import os
import tempfile
import unittest
from pathlib import Path

from scripts.ui_probe_report import PULSE, _dominant_path, analyse_sample, main, report

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
        """两支闸门不许互相替代（R86 定下；R94 把它从"词汇"改成"能力"，理由写在下面）。

        那一支判**集合级**：源码里有几条在屏判据、这次哪几条没下结论、缺席登记过没有。
        这一支判**因果级**：这一卷是怎么停的、挂住的那条**叫什么名字**。
        只有前者会漏成：11 条全登记着、全都没结论、闸门照样绿 —— 那正是 R62 到 R85 的形状。

        R94 为什么要改这条守卫的形状：BACKLOG 134 让登记必须回答
        「没结论的这几条是**排队没到**还是**跑到一半被收掉**」，而这一支的日志里本来就有
        `Test Case … started.` 这一层信息 —— 那一支于是也要读 `started`。
        老守卫判的是"文本里不许出现 started 这个词"，它会把这种**共用原始通道**误判成分工崩溃。
        真正会崩的是**共用判定**：两边各自报一个"挂住的是谁"，就成了一把没有样本数优势的第二尺子
        （R87：结论相反时定罪权按样本数分配 —— 那一支只有一份 stdout，这一支有两份互相签字）。
        所以现在的守卫读能力，不读散文：
          ① 那一支不许打出 `HUNG` 这个判定名，也不许把"没闭口"的任何一条**用例名**当成结论输出；
          ② 它的新读数只许是计数与 `queued`（一次都没轮到的那些），不许新增红；
          ③ 这一支仍然独占 `UI_PROBE_HUNG=<名字>`。
        """
        gate = Path(__file__).resolve().parents[1] / "probe_coverage_gate.py"
        text = gate.read_text(encoding="utf-8")
        self.assertIn("started", text,
                      "R94 之后那一支本来就要读 started 来分「排队没到 / 跑到被收」；"
                      "这个词没了说明它退回了老写法")
        # 只看它**打出去**的东西：`print(...)` 里的字面串。
        # 为什么不能整份文件扫 —— 守卫会命中自己那族的老毛病（R53：region() 先命中守卫写的名字）：
        # 那一支的文档串里正写着"这个名字归另一支"，扫全文就会因为**解释了分工**而红。
        printed = " ".join(ln for ln in text.splitlines() if "print(" in ln)
        for token in ("HUNG", "STALLED"):
            self.assertNotIn(token, printed,
                             f"那一支打出了 {token} ⇒ 因果级的名字被复制成了第二颗尺子")
        red_lines = [ln for ln in text.splitlines() if "reds.append" in ln]
        for ln in red_lines:
            for word in ("stall", "open_not_closed", "ORDER"):
                self.assertNotIn(word, ln,
                                 f"那一支把一条**诊断**变成了门禁（{ln.strip()[:80]}）")
        self.assertIn('reds.append(f"NOT_RUN {name}', text,
                      "集合级那两条红（NOT_RUN / NOW_RUNS）必须还在：放宽成只报数就等于撤了闸门")

    def test_this_script_owns_the_hung_case_name(self):
        """反方向也要有牙：名字只能这一支出。缺了它，R94 那条"共用 started"就变成"没人负责"。"""
        here = Path(__file__).resolve().parents[1] / "ui_probe_report.py"
        text = here.read_text(encoding="utf-8")
        self.assertIn("UI_PROBE_HUNG", text, "这一支不再点名『挂住的是谁』⇒ 那一句今天没人说了")


if __name__ == "__main__":
    unittest.main()

class PulseChannelTests(unittest.TestCase):
    """R90 / BACKLOG 122 · 第二条通道：每条用例在 setUpWithError 里写到自己文件上的一行心跳。

    这一族存在的理由是一条被实测推翻的假设：R89 我以为 stderr（`FileHandle.write` = write(2)）
    天然活得过 SIGKILL。R90 把它真的接上之后量到的是 —— 进程活着、已经跑进第二条用例的方法体，
    `ui.log` 仍是 119 字节、`heartbeat=0`（`swift test … > ui.log 2>&1` 里 fd2 指向的是 SwiftPM
    驱动的**管道**，驱动被杀时它那块缓冲一起丢）。⇒ 只能自己开文件写。
    """

    REAL_PULSE = (Path(__file__).resolve().parent / "fixtures" / "r90_pulse_real.log").read_text(
        encoding="utf-8")

    def testRealProductPulseLineIsParsed(self):
        """正对照：正则读的是**产品今天真写出来的那两行**，不是我照着格式编的串。

        夹具 `r90_pulse_real.log` 是 `spike_r90_pulse.sh` 在本机跑出来的原文件（逐字节拷进来）。
        没有这一格，其余各格都只是在验"我看得懂我自己写的字"。
        """
        names = [m.group(1) for m in PULSE.finditer(self.REAL_PULSE)]
        self.assertEqual(["testAccessibilityTreeCoverage",
                          "testDragSelectExpandsSelectionInsideTheRealList"], names,
                         "解析不出产品自己写的那两行 ⇒ 通道接上了也没人读它")

    def testPulseNamesEveryCaseThatOpenedWithoutConclusion(self):
        """R88 的形状（日志只有 build 那 119 字节、started=0）+ 心跳有内容 ⇒ 第一次能点名。

        两条都报，不是只报最后那条：这一份日志里**两条都没有结论**，
        而 `UI_PROBE_HUNG` 的语义就是"开了口没结论"。只报最后一条会把
        "第一条的结论也丢了"这件事说成"第一条正常结束"。（我第一版期望写的是只报一条，
        那是我心里把这条标记当成了"挂死的那条" —— 语义由代码定，不由我的直觉定。）
        """
        lines, named = report("[0/1] Planning build\nBuild complete! (0.16s)\n", 1, self.REAL_PULSE)
        text = "\n".join(lines)
        self.assertTrue(named, "心跳点出来了还不许说『没有名字』：" + text)
        self.assertEqual(1, text.count("UI_PROBE_HUNG=testAccessibilityTreeCoverage"))
        self.assertEqual(1, text.count("UI_PROBE_HUNG=testDragSelectExpandsSelectionInsideTheRealList"))
        self.assertIn("UI_PROBE_HUNG_CHANNEL=pulse", text)
        self.assertIn("UI_PROBE_CHANNELS pulse=2 started=0 concluded=0", text)
        self.assertNotIn("UI_PROBE_LOG_EMPTY", text, "日志里有 build 行，它不是空文件")

    def testPulseWinsWhenBothChannelsAgree(self):
        log = started("testAlpha") + started("testBeta") + concluded("testAlpha") + "\n"
        pulse = "PROBE_PULSE testAlpha\nPROBE_PULSE testBeta\n"
        lines, named = report(log, 1, pulse)
        text = "\n".join(lines)
        self.assertTrue(named)
        self.assertIn("UI_PROBE_HUNG=testBeta", text)
        self.assertIn("UI_PROBE_HUNG_CHANNEL=pulse", text)
        self.assertIn("UI_PROBE_CHANNELS_AGREE=1", text)
        self.assertEqual(1, text.count("UI_PROBE_HUNG=testBeta"))

    def testContradictingChannelsAreRedNotCherryPicked(self):
        """两条通道各点一条不同的 ⇒ 至少一条不可信。这一格不许挑一个信，也不许静默优先。"""
        log = started("testAlpha") + "\n"
        pulse = "PROBE_PULSE testBeta\n"
        lines, named = report(log, 1, pulse)
        text = "\n".join(lines)
        self.assertFalse(named, "通道互相矛盾时给名字=替一条说谎的通道签字：" + text)
        self.assertIn("UI_PROBE_CHANNELS_CONTRADICT", text)
        self.assertIn("UI_PROBE_HUNG_LOG=testAlpha", text, "日志那条仍要打出来，但要换个标记")

    def testEmptyPulseWhileRunnerAliveIsABrokenChannel(self):
        """接了心跳通道、进程还活着、却一条心跳都没有 ⇒ 是**通道坏了**，不是"用例没开始"。"""
        lines, named = report("[0/1] Planning build\n", 1, "")
        text = "\n".join(lines)
        self.assertFalse(named, "心跳空着就退回旧通道，等于让装饰替结论签字：" + text)
        self.assertIn("UI_PROBE_PULSE_EMPTY=1", text)

    def testUnwiredPulseKeepsTheOldVerdict(self):
        """`--pulse` 没传（本地手跑、老日志）⇒ 维持 R88 那一格，不许假装心跳通道在。"""
        lines, named = report("[0/1] Planning build\n", 1, None)
        text = "\n".join(lines)
        self.assertTrue(named)
        self.assertIn("UI_PROBE_START_LINES_LOST=1", text)
        self.assertIn("BACKLOG 122", text, "没接线时那句『还缺心跳』要留在原地，别被新代码抹掉")
        self.assertNotIn("UI_PROBE_PULSE_EMPTY", text)

    def testCliPassesThePulseFileThrough(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "ui.log"
            log.write_text("[0/1] Planning build\n", encoding="utf-8")
            pulse = Path(tmp) / "probe-pulse.log"
            pulse.write_text(self.REAL_PULSE, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([str(log), "--runner-alive", "1", "--pulse", str(pulse)])
            text = out.getvalue()
        self.assertEqual(0, code)
        self.assertIn("UI_PROBE_HUNG=testDragSelectExpandsSelectionInsideTheRealList", text)

    def testCliMissingPulseFileIsAnnouncedNotSwallowed(self):
        """路径没对上与 setUp 没跑到长得一样 ⇒ "我读不到"必须自己说出口。"""
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "ui.log"
            log.write_text("[0/1] Planning build\n", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([str(log), "--runner-alive", "1",
                             "--pulse", str(Path(tmp) / "definitely-absent.log")])
            text = out.getvalue()
        self.assertEqual(1, code, "读不到心跳文件而进程又活着 ⇒ 通道坏了，这一卷没有名字")
        self.assertIn("UI_PROBE_PULSE_UNREADABLE", text)
        self.assertIn("UI_PROBE_PULSE_EMPTY=1", text)


class PulseWiringTests(unittest.TestCase):
    """心跳这条通道**接没接上**要能被跑出来，不能只被我记得。

    R84 那一格（BACKLOG 124）刚教过：凡是"每一轮都要做"的事，没有可 grep 的证据行 +
    会红的对账，它就会静默地不做。心跳同理 —— 删掉 `setUpWithError` 里那一行，
    其余 25 格真值表照样全绿（它们读的是我自己造的字符串夹具）。
    """

    REPO = Path(__file__).resolve().parents[2]
    PROBE = REPO / "ClipboardHistory" / "Tests" / "ClipboardHistoryAppTests" / "UIInteractionProbeTests.swift"
    CI = REPO / ".github" / "workflows" / "ci.yml"

    EMIT_LINE = "        CaptureReadings.emit(\"PROBE_PULSE \\(pulseStamp)\", to: Self.pulseURL)\n"
    SETUP_HEAD = "    override func setUpWithError() throws {\n"

    def testEmitLineIsTheFirstStatementOfSetUp(self):
        text = self.PROBE.read_text(encoding="utf-8")
        self.assertEqual(1, text.count(self.SETUP_HEAD),
                         "setUpWithError 的定义行不是恰好一处 ⇒ 位置判据没有对象")
        at = text.index(self.SETUP_HEAD)
        body = text[at:at + 400]
        self.assertIn(self.EMIT_LINE, body,
                      "心跳不在 setUpWithError 里 ⇒ 它不会每例必到（BACKLOG 122 的整条理由）")
        self.assertLess(body.index(self.EMIT_LINE), body.index("try super.setUpWithError()"),
                        "心跳排在 super 之后 ⇒ 一旦 super 里出问题这一行就不写了，通道会静默变窄")

    def testPulseUsesTheFileChannelNotStdoutOrStderr(self):
        """`emit` 那一条腿换成 stdout/stderr 都会让通道在 SIGKILL 下消失（R90 实测的那件事）。"""
        text = self.PROBE.read_text(encoding="utf-8")
        at = text.index(self.SETUP_HEAD)
        body = text[at:at + 400]
        self.assertIn("CaptureReadings.emit(", body)
        for banned in ("print(", "FileHandle.standardError", "standardOutput"):
            self.assertNotIn(banned, body,
                             "心跳走了 %s ⇒ 那是驱动那层的缓冲，被 kill -9 时整块丢（本轮的起因）" % banned)

    def testPulseFileIsNotTheCaptureSuitesFile(self):
        """两条卷共用一份读数文件会互相整份重写 —— 这一格钉的是"心跳有自己的文件名"。"""
        text = self.PROBE.read_text(encoding="utf-8")
        self.assertIn('"probe-pulse.log"', text,
                      "心跳文件名不是自己的 ⇒ 会和捕获卷的 capture-readings.log 撞，"
                      "第一次写就把别人那卷整份抹掉")
        self.assertNotIn('appendingPathComponent("capture-readings.log")', text)

    def testCiWiresThePulseIntoBothReportCalls(self):
        ci = self.CI.read_text(encoding="utf-8")
        self.assertEqual(2, ci.count("--pulse /tmp/probe-pulse.log"),
                         "报告器两处调用里有一处没接 --pulse ⇒ 那一处的名字仍然只来自会被丢的通道")
        self.assertIn("CLIPBOARD_HISTORY_PROBE_PULSE=/tmp", ci,
                      "CI 没给心跳目录 ⇒ 探针会退回默认路径，而闸门读的是 /tmp 那个文件")

    SHOTS_RE = __import__("re").compile(r"CLIPBOARD_HISTORY_UI_SHOTS=(/\S+)")
    READINGS_RE = __import__("re").compile(r"--readings (\S+)")

    def testCaptureAndProbeSuitesDoNotShareTheReadingsFile(self):
        """R90 的那朵新红：两步共用一个 shots 目录 ⇒ 后一步第一次写把前一步的读数整份换掉。

        `CaptureReadings` 的"每个进程第一次写要整份重写"是对的（上一遍的读数冒充这一遍比没读数更坏），
        错的是把两份**同一次运行里不同卷**的读数放进同一个文件。R89 之前捕获闸门紧跟捕获步骤，
        这个共用从来没人看见；把闸门挪到证据之后（U-193 的修法）它就红了。
        """
        ci = self.CI.read_text(encoding="utf-8")
        # 只看在屏那一卷与捕获那一卷各自的 env 行（按步骤切块，避免跨步骤 grep 造出假矛盾）
        def step_body(name):
            at = ci.index("- name: " + name)
            nxt = ci.find("\n      - name: ", at)
            return ci[at:nxt if nxt > 0 else len(ci)]

        capture = step_body("Offscreen frame capture (report-only, gated below)")
        onscreen = step_body("On-screen interaction probes (report-only)")
        cap_dirs = set(self.SHOTS_RE.findall(capture))
        probe_dirs = set(self.SHOTS_RE.findall(onscreen))
        self.assertEqual(1, len(cap_dirs), "捕获卷的 shots 目录不止一个 ⇒ 这条判据没有对象")
        self.assertEqual(1, len(probe_dirs), "在屏卷的 shots 目录不止一个 ⇒ 同上")
        cap, probe = cap_dirs.pop(), probe_dirs.pop()
        self.assertNotEqual(cap, probe,
                            "两卷共用 %s ⇒ 在屏卷第一次写会把捕获卷的 capture-readings.log 整份换掉，"
                            "而捕获闸门现在跑在它们之后" % cap)
        gate = step_body("Capture gate (unregistered reds must be zero)")
        readings = self.READINGS_RE.findall(gate)
        self.assertEqual([cap + "/capture-readings.log"], readings,
                         "闸门读的读数文件必须落在**捕获卷自己**那个目录下：%s" % readings)


def sample(name):
    """读一份 `sample` 夹具。`sample_real_sleep.txt` 是**本机真产物**（拿 sleep 当靶子），
    其余四份是合成的 —— 因为 CoreDrag 那条挂死在进程内造不出来（R91 已证），
    而"慢"那一格要的是散开的树。两种来源在断言里不混用：真产物那格只判"读得动且读到什么"。
    """
    return (Path(__file__).resolve().parent / "fixtures" / (name + ".txt")).read_text(encoding="utf-8")


class SampleTriageTests(unittest.TestCase):
    """R95 / BACKLOG 132：那份栈到底说"挂"还是说"慢"。"""

    def test_real_sample_from_this_machine_is_parsed(self):
        """正对照（真产物）：新尺第一遍必须在本机真的 `sample` 输出上读到东西。"""
        lines, verdict = analyse_sample(sample("sample_real_sleep"))
        self.assertEqual("blocked@sleep-wait", verdict, lines)
        self.assertIn("主线程采样=534", lines[0])
        # R96 起最深帧不在第一行了（第一行只有两个占比与终端计数）。
        # 断言因此改成"整段读数里必须有它"—— 换行不是丢检查，但**必须仍然点着那一格**：
        # 这条是这份尺唯一一处"真产物"正对照，它一旦只判 verdict，就再没人管我读的是不是那棵树。
        self.assertIn("__semwait_signal", "\n".join(lines), "最深帧读错了 ⇒ 下降逻辑没走到底")
        self.assertIn("等待终端=1 个", lines[0])

    def test_empty_main_thread_block_is_not_read_as_an_unknown_hang(self):
        """R96 在 runner 上真的撞到的那一格：`sample` 退出码 0、有 `Call graph:`、
        主线程行也读到了 306 个采样，**但那一段里一个节点都没有**。

        旧写法把占比兜底成 1.0 ⇒ 打出 `blocked@unknown`，读起来像"它挂在某个我们不认识的帧上"。
        那是把"我读不懂这份文件"说成了一条产品级结论 —— 现在它必须报**未量到**，
        并且把形状（缩进宽度 / 是否以数字开头）打出来，好让下一次能定位是谁的锅。
        形状里不许出现帧名：台账有一条硬规矩，日志不许带用户的剪贴板内容。
        """
        lines, verdict = analyse_sample(sample("sample_empty_call_graph"))
        self.assertEqual("未量到", verdict, lines)
        text = "\n".join(lines)
        self.assertIn("UI_PROBE_SAMPLE_UNPARSED=1", text)
        self.assertIn("主线程采样=306", text)
        self.assertIn("UI_PROBE_SAMPLE_SHAPE", text, "不判还不够，得留下能定位形状的东西")
        self.assertNotIn("blocked", text, "读不懂文件的时候不许出现任何『挂』的字样")
        self.assertNotIn("xctest", text, "形状读数里不该出现帧名或进程名（只打缩进与是否数字开头）")

    def test_tied_branches_say_ambiguous_and_name_both_families(self):
        """BACKLOG 137：并列的时候**不许替栈挑一个答案**。

        这份夹具是 600 个采样里 300 停在 `TrackMouse`、300 停在 `mach_msg2_trap`，
        两者都在 `_CFRunLoopRunSpecific` 下面。旧尺子在这里会：主导路径占比=50% ⇒ 判成
        "progressing"（把挂在两件事上读成在往前走），而打印出来的那一帧由"取第一个还是最后一个
        孩子"决定 —— 变异 M527 就是这么逃掉的。现在两格分开：等待占比 100% ⇒ 挂；
        族有两个 ⇒ `blocked@ambiguous` 且两个族与各自采样数都要出现在读数里。
        """
        lines, verdict = analyse_sample(sample("sample_tied_branches"))
        self.assertEqual("blocked@ambiguous", verdict, lines)
        text = "\n".join(lines)
        self.assertIn("等待帧占比=100%", text)
        self.assertIn("主导路径占比=50%", text, "两格必须同时打出来：它们分岔的那一刻才是信息")
        self.assertIn("menu-tracking=300", text)
        self.assertIn("runloop-wait=300", text)
        for line in lines:
            self.assertNotIn("UI_PROBE_HUNG_KIND=blocked@menu-tracking", line,
                             "并列时把任何一族单独写成结论，就是替栈做了决定")

    def test_nested_blocking_frames_are_counted_once(self):
        """等待帧套等待帧（`_BlockUntilNextEvent…` → `ReceiveEvents` → `_tryCatchDrag…`）
        只算最外层那一次：四帧链上的 611 个采样必须还是 611，不是 2444。
        占比一旦能超过 100%，"挂 vs 慢"这条线就没有意义了。
        """
        lines, verdict = analyse_sample(sample("sample_core_drag_hang"))
        self.assertEqual("blocked@coredrag", verdict, lines)
        self.assertIn("等待终端=1 个", lines[0], lines)
        self.assertIn("等待帧占比=100%", lines[0], "重复计数会把占比推到 100% 以上")

    def test_progressing_line_carries_its_own_number(self):
        """判成"慢"的时候，那行必须带着**是多少**（33%），不许只写"它在往前走"。
        处置是"把看门狗调大并去量慢在哪一段"，而 33% 与 89% 是两种完全不同的下一步。
        """
        lines, verdict = analyse_sample(sample("sample_spread_slow"))
        self.assertEqual("progressing", verdict, lines)
        text = "\n".join(lines)
        self.assertIn("只有 33% 的采样停在等待帧上", text)
        self.assertIn("等待终端=1 个", lines[0])

    def test_two_different_hangs_get_two_different_families(self):
        """CoreDrag 与 NSMenu 必须分开 —— 这条是修 bug 的回归格。

        第一版一次循环里"叶子与路径"两个都查，于是 `_BlockUntilNextEventMatchingListInMode`
        （两族名单里都有它）把一条 `-[NSMenu popUp…]` 判成了 `coredrag`：
        名字听起来对，因为那条链上确实经过 CoreDrag 的那个符号。**挂在哪件事上由最深那一帧说。**
        """
        self.assertEqual("blocked@coredrag", analyse_sample(sample("sample_core_drag_hang"))[1])
        self.assertEqual("blocked@menu-tracking", analyse_sample(sample("sample_menu_tracking_hang"))[1])

    def test_a_spread_stack_is_slow_not_hung(self):
        """散开的树必须判 progressing：132 要分的正是这两种，处置完全不同。"""
        lines, verdict = analyse_sample(sample("sample_spread_slow"))
        self.assertEqual("progressing", verdict, lines)
        self.assertIn("主导路径占比=17%", lines[0], lines)

    def test_truncated_sample_is_not_read_as_slow(self):
        """`sample` 自己没跑成 ⇒ 只能报"未量到"，不许把 132 读成任何一种。"""
        lines, verdict = analyse_sample(sample("sample_truncated"))
        self.assertEqual("未量到", verdict)
        self.assertTrue(any("UI_PROBE_SAMPLE_UNAVAILABLE" in l for l in lines), lines)

    def test_sample_without_main_thread_is_not_judged(self):
        # 靶子的文字里**不许**出现 "main-thread" 这个子串：`THREADED` 找的是
        # `Thread_\d+.*main-thread`，第一版写成 "(no main-thread here)" 反而被匹配上了，
        # 于是这一格测的是"有没有主线程"，读到的却是"有主线程但树是空的"。
        lines, verdict = analyse_sample("Call graph:\n    10 Thread_1   另一个线程，不是主线程\n")
        self.assertEqual("未量到", verdict)
        self.assertTrue(any("NO_MAIN_THREAD" in l for l in lines), lines)

    def test_dominant_path_truth_table(self):
        """`_dominant_path` 自己的真值表：它决定占比，而占比决定"挂还是慢"。"""
        chain = [(4, 100, "a"), (6, 100, "b"), (8, 100, "c")]
        self.assertEqual(("c", 100), _dominant_path(chain))
        split = [(4, 60, "a"), (6, 60, "a1"), (4, 40, "b")]
        self.assertEqual(("a1", 60), _dominant_path(split), "同层要取采样数最大的那个孩子")
        self.assertEqual(("", 0), _dominant_path([]))
        self.assertEqual(("only", 7), _dominant_path([(4, 7, "only")]))

    def test_main_prints_the_kind_only_when_the_channel_is_wired(self):
        """没接线时不许出现读数行 —— 否则"这一格没跑"与"这一格跑了没问题"长得一样。"""
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, "ui.log")
            with open(log, "w", encoding="utf-8") as handle:
                handle.write("Test Case '-[M.T testA]' started.\n"
                             "Test Case '-[M.T testA]' passed (1.000 seconds).\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                main([log])
            self.assertNotIn("UI_PROBE_SAMPLE", out.getvalue())
            sfile = os.path.join(tmp, "s.txt")
            with open(sfile, "w", encoding="utf-8") as handle:
                handle.write(sample("sample_core_drag_hang"))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                main([log, "--sample", sfile])
            text = out.getvalue()
        self.assertIn("UI_PROBE_HUNG_KIND=blocked@coredrag", text)

    def test_missing_sample_file_says_unreadable_not_empty(self):
        """路径写错与"没有栈"要分开：前者是仪器坏了（同 R90 的 pulse 那一格）。"""
        with tempfile.TemporaryDirectory() as tmp:
            log = os.path.join(tmp, "ui.log")
            with open(log, "w", encoding="utf-8") as handle:
                handle.write("Test Case '-[M.T testA]' started.\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                main([log, "--sample", os.path.join(tmp, "nope.txt")])
        text = out.getvalue()
        self.assertIn("UI_PROBE_SAMPLE_UNREADABLE", text)
        self.assertIn("UI_PROBE_SAMPLE_UNAVAILABLE", text,
                      "读不到文件之后还要明说这一格没有依据，不许只留一行错误就过去")


class SampleWiringTests(unittest.TestCase):
    """R95 / BACKLOG 132：那份栈**接没接上**要能被跑出来（同 PulseWiringTests 的理由）。

    真值表全在 `SampleTriageTests` 里，它们读的是我自己造的字符串夹具 ——
    所以"CI 里根本没拍这份栈"这件事，只有读 `ci.yml` 正文才看得见。
    """

    REPO = Path(__file__).resolve().parents[2]
    CI = REPO / ".github" / "workflows" / "ci.yml"
    STEP = "On-screen interaction probes (report-only)"
    FLOOR = "On-screen probe coverage floor"

    def step_body(self, name):
        ci = self.CI.read_text(encoding="utf-8")
        at = ci.index("- name: " + name)
        nxt = ci.find("\n      - name: ", at)
        return ci[at:nxt if nxt > 0 else len(ci)]

    def test_both_report_calls_carry_the_sample_channel(self):
        """两条 report 调用都要带 `--sample`。

        只带在报告型那一步是不够的：硬门那一步（floor）才是"红有名字"的地方，
        而 R88 之后闸门排在最后 —— 通道只接一半，读数就永远出现在不判红的那一步。
        """
        for step in (self.STEP, self.FLOOR):
            body = self.step_body(step)
            self.assertIn("--sample /tmp/ui-sample.txt", body,
                          "%s 这一步的 report 调用没接 --sample ⇒ 132 那份栈今天没人读" % step)

    def test_sample_is_taken_before_the_kill(self):
        body = self.step_body(self.STEP)
        self.assertIn('sample "$victim"', body, "没拍栈 ⇒ 132 仍然只能靠外推")
        self.assertLess(body.index('sample "$victim"'), body.index('kill -9 -"$pid"'),
                        "拍栈排在 kill 之后 ⇒ 进程已经没了，这份栈永远是空的（而且空得像没挂）")

    def test_sample_exit_code_survives_bash_e(self):
        """`rc=0; … || rc=$?` 而不是 `… || true`：后者会把退出码那一格吞掉。"""
        body = self.step_body(self.STEP)
        self.assertIn('|| rc=$?', body, "sample 的退出码没被留住 ⇒ 它坏了与它没跑长得一样")
        at = body.index('sample "$victim"')
        self.assertNotIn('|| true', body[at:at + 160],
                         "sample 后面直接 `|| true` ⇒ `bash -e` 下失败会静默，退出码那一格写不出来")

    def test_no_backticks_inside_double_quoted_echo(self):
        """读数行里不许有反引号：`echo "…\`sample\`…"` 会**执行**它（本轮差点踩了这格）。

        这一步的正文会被 `scripts/tests/test_ci_report_selftest.py` 真的跑起来，
        所以这类错不是"难看"，是"多跑一条命令 + 一行被污染的读数"。
        """
        body = self.step_body(self.STEP)
        bad = [ln for ln in body.splitlines()
               if ln.strip().startswith('echo "') and '`' in ln]
        self.assertEqual([], bad, "echo 的双引号串里有反引号 ⇒ 它会被当命令执行：%s" % bad[:2])

    def test_step_bodies_still_parse_as_bash(self):
        """改完 CI 正文要还能过 `bash -n`（这一格是 R88 那支"真跑步骤正文"的自检的轻量版）。"""
        import subprocess
        import tempfile
        for step in (self.STEP, self.FLOOR):
            body = self.step_body(step)
            script = body.split("run: |", 1)[1]
            lines = [ln[10:] if ln.startswith(" " * 10) else ln for ln in script.splitlines()]
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, encoding="utf-8") as handle:
                handle.write("#!/bin/bash\n" + "\n".join(lines) + "\n")
                path = handle.name
            proc = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
            os.unlink(path)
            self.assertEqual(0, proc.returncode, "%s 的正文语法坏了：%s" % (step, proc.stderr[:200]))


class FpsForwardingTests(unittest.TestCase):
    """R143 / BACKLOG 176：帧间隔的三臂读数必须被转发进 CI 日志，而**缺席必须自己报一行**。

    为什么单独测：探针那三行原来走 `print`（块缓冲），CI 里从来没有它们；
    改成 `emit` 之后它们进了 `/tmp/ui.log`，但那份日志不上传 —— 所以"转发"这一步才是
    让 runner 读数真正存在的那一环。少了它，176 的收紧永远没有依据，
    而 CI 看起来一切正常（这正是"只印不拦的读数=没读数"的反面：只写在本地=没写）。
    """

    def _run(self, body):
        import os
        import subprocess
        import tempfile
        repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(tempfile.mkdtemp(), "ui.log")
        with io.open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        proc = subprocess.run([sys.executable,
                               os.path.join(repo, "scripts", "ui_probe_report.py"), path],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.stdout.decode("utf-8", "replace")

    def test_a_present_reading_is_forwarded(self):
        out = self._run(u"Test Case '-[X testA]' passed (1.0 seconds).\n"
                        u"PROBE_FPS 机器=runner baseline_p95=16.70 off_p95=16.80 "
                        u"loaded_p95=26.94 比值=1.604 预算=3.00 n=210 worst=88.0\n")
        self.assertIn("FORWARDED PROBE_FPS", out)
        self.assertNotIn("UI_PROBE_FPS_ABSENT", out)

    def test_absence_is_named_rather_than_silent(self):
        out = self._run(u"Test Case '-[X testA]' passed (1.0 seconds).\n")
        self.assertIn("UI_PROBE_FPS_ABSENT=1", out,
                      "没有读数时必须报这一行 ⇒ 否则 CI 绿会替我说「帧间隔没问题」，"
                      "而实际是这条用例没跑完或者读数没走 emit")
