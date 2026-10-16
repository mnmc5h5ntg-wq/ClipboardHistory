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

from scripts.ui_probe_report import PULSE, main, report

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
