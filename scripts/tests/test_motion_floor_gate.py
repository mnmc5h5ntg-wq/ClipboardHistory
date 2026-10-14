"""`scripts/motion_floor_gate.py` 的自测（R46 / BACKLOG 66 / U-72）。

这条闸门管的是"**动效那一族今天判了几条、掉的是哪一条、掉的理由登记过没有**"。
它自己必须是可判红死的，否则就只是把旧的那句 `judged<2` 换了个地方写。
所以每一条规则都配一格"少了它就会漏"的用例：

  NO_RESOLVE      跑完了却没有结论行 ⇒ 红。旧版这一步在这里 `exit 0`，
                  那是一张免检牌：本仓库每条判据都会打这一行，缺了就是坏了。
  SKIPPED         suite 没跑完 ⇒ **不红**（"没跑完"不等于"验得不够"，D-055 那一族），
                  但必须打出来让人看见。
  REASONLESS      not-run 名单里有一条，而日志里没有任何一行说为什么 ⇒ 红。
  BAD_REASON      理由不在登记里 ⇒ 红（同一臂换了一种坏法 = 新缺陷，不是老毛病）。
  UNREGISTERED    清单外的臂 not-run ⇒ 红（新的盲区要先写理由再放行）。
  UNDERCOVERED    judged 低于"必须判到"的臂数 ⇒ 红。
  MISSING_KEY     MOTION_SUMMARY 少了一臂 ⇒ 红（下游会把"没测"读成"测了且为 0"）。
  UNLISTED_SCENARIO 多出一臂 ⇒ 红（判据加了场景而清单没跟上）。
  STALE           登记成"永远判不了"的臂判到了 ⇒ 红（清单不许变免检牌堆）。
                  而 `must_judge=false` 但**没有** stale 标记的臂判到了 ⇒ 不红：
                  这一格是把 R44 那条会随采样漂的臂从"反向恒红"里救出来 ——
                  判不到红、判到也红，最后被人删掉（R39 那一族的教训）。

`LOCAL_RUNNER_LOG` 是**逐字真日志**（`fixtures/r46_motion_local.log`，
本机 2026-10-14 06:09 跑 `CLIPBOARD_HISTORY_UI_MOTION=1 swift test --filter MotionFilmstripTests`）。
`RUNNER_SILENT_LOG` 是 run 38543090198 那一次"整族一条读数都没打"的**重建件**
（只抄那一步真打出来的行；原始 motion.log 没上传，所以它证明不了原因，见文件头）。

**R52 改的是这两份夹具各自"该红成什么样"**：登记表里 `notice-banner` 从 `must_judge=true`
改成放行 `clock-coarse-in-window` / `premise-not-visible` —— 不是为了让 CI 变绿，
而是那句话已被实测推翻两次（run 38538371464 与 38543812477，理由与毫秒数都在登记里）。
于是本机那份真日志从"红两处"变成"绿 + 一行 THIN"，正对照的角色交给 `RUNNER_SILENT_LOG`。
"""
import io
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.motion_floor_gate import main, parse, verdicts

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r46_motion_local.log"
HEADER_LINES = [line for line in FIXTURE.read_text(encoding="utf-8").splitlines()
                if line.startswith("# ")]
LOCAL_RUNNER_LOG = "\n".join(line for line in FIXTURE.read_text(encoding="utf-8").splitlines()
                             if not line.startswith("# "))

SILENT_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r51_motion_runner_silent.log"
RUNNER_SILENT_LOG = "\n".join(line for line in SILENT_FIXTURE.read_text(encoding="utf-8").splitlines()
                              if not line.startswith("# "))

EXPECTATIONS_PATH = Path(__file__).resolve().parents[2] / "scripts" / "motion_floor_expectations.json"
EXPECTATIONS = json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))

SUMMARY = "MOTION_SUMMARY notice-banner=3 notice-banner-dismiss=3 detail-kind-change=3 empty-state=4"
EXECUTED = "\t Executed 24 tests, with 5 tests skipped and 0 failures (0 unexpected) in 76.171 seconds"


def log(resolve: str, summary: str = SUMMARY, extra: str = "") -> str:
    return "\n".join([EXECUTED, summary, resolve, extra])


def markers(facts: dict, expectations: dict = None) -> list:
    return [(marker, red) for marker, _, red in verdicts(facts, expectations or EXPECTATIONS)]


class MotionFloorGateTests(unittest.TestCase):

    def setUp(self):
        # 夹具的头两行是注释，被剥掉之后必须还剩真读数行。
        self.assertTrue(HEADER_LINES, "夹具没有注释头 ⇒ 来源无法追溯")
        self.assertIn("MOTION_RESOLVE_SUMMARY", LOCAL_RUNNER_LOG)

    # ---- 解析 ----

    def testParserReadsTheRealLocalLog(self):
        facts = parse(LOCAL_RUNNER_LOG)
        self.assertEqual(facts["judged"], 2)
        self.assertEqual(facts["total"], 4)
        self.assertEqual(facts["not_run"], {"notice-banner", "notice-banner-dismiss"})
        self.assertEqual(facts["executed"], 24)
        self.assertEqual(facts["summary_arms"]["empty-state"], 4)
        # 没有臂名的那两种写法（`MOTION_NOT_RUN=app-not-active：…`）不许被当成某条臂的理由。
        self.assertNotIn("app-not-active", facts["reasons"].get("notice-banner", set()))
        self.assertEqual(facts["reasons"]["notice-banner"], {"premise-not-visible"})
        self.assertEqual(facts["reasons"]["notice-banner-dismiss"], {"clock-coarse-in-window"})

    def testParserTakesTheLastResolveLine(self):
        # CI 会把结论行再 echo 一遍。取第一条会让"重打的那一遍"盖掉真读数。
        text = ("MOTION_RESOLVE_SUMMARY judged=9/9 not-run=-\n" + EXECUTED + "\n"
                + SUMMARY + "\n" + "MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss\n")
        facts = parse(text)
        self.assertEqual(facts["judged"], 3)
        self.assertEqual(facts["not_run"], {"notice-banner-dismiss"})

    # ---- 每一条规则都要能红 ----

    def testAllJudgedIsGreen(self):
        facts = parse(log("MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-"))
        self.assertEqual([m for m, red in markers(facts) if red], [])

    def testRegisteredDriftIsGreenButVisible(self):
        """R44 那种形状在**合成清单**下仍然必须是"放行 + 打印"。

        R57 之前这一格直接吃今天的清单（dismiss 登记成 must_judge=false）。
        带捕获把成本降下来之后今天的清单收紧了（四臂全 true），
        于是这一格开始红 —— 而它要判的事根本不是"今天的清单严不严"，
        是"闸门支不支持'登记过的漂移就放行'这条规则"。
        ⇒ 规则用合成清单测，今天的清单另有一格专门盯（`testRegistryIsStrictAgain`）。
        """
        relaxed = json.loads(json.dumps(EXPECTATIONS))
        relaxed["arms"]["notice-banner-dismiss"]["must_judge"] = False
        relaxed["thin_warnings"] = []
        text = log("MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss",
                   extra="MOTION_NOT_RUN=clock-coarse-in-window notice-banner-dismiss：事件段最粗 101ms")
        facts = parse(text)
        self.assertEqual([m for m, red in markers(facts, relaxed) if red], [])
        self.assertEqual(facts["judged"], 3)
        # 同一条日志、今天的清单 ⇒ 必须红。这一句钉的是"红不红由清单决定，不由日志决定"。
        self.assertIn("MOTION_FLOOR_UNDERCOVERED", [m for m, red in markers(facts) if red])

    def testNotRunWithoutAReasonLineIsRed(self):
        facts = parse(log("MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss"))
        self.assertIn("MOTION_FLOOR_REASONLESS", [m for m, red in markers(facts) if red])

    def testNewReasonForAKnownArmIsRed(self):
        text = log("MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss",
                   extra="MOTION_NOT_RUN=something-never-seen notice-banner-dismiss：换了种坏法")
        facts = parse(text)
        self.assertIn("MOTION_FLOOR_BAD_REASON", [m for m, red in markers(facts) if red])

    def testUnregisteredArmIsRed(self):
        text = log("MOTION_RESOLVE_SUMMARY judged=3/4 not-run=brand-new-scenario",
                   extra="MOTION_NOT_RUN=clock-not-warm brand-new-scenario：新臂")
        facts = parse(text)
        self.assertIn("MOTION_FLOOR_UNREGISTERED", [m for m, red in markers(facts) if red])

    def testFloorIsTheMustJudgeCountNotTwo(self):
        # 旧版写死 `judged<2`。这一格钉的是"地板从清单算"，不是"这条闸门永远红"：
        # 同一份日志，清单里 must_judge 的臂数变了，UNDERCOVERED 就必须跟着消失。
        text = log("MOTION_RESOLVE_SUMMARY judged=1/4 "
                   "not-run=notice-banner,notice-banner-dismiss,detail-kind-change",
                   extra="MOTION_NOT_RUN=premise-not-visible notice-banner：x\n"
                         "MOTION_NOT_RUN=clock-coarse-in-window notice-banner-dismiss：x\n"
                         "MOTION_NOT_RUN=premise-not-visible detail-kind-change：x")
        facts = parse(text)
        reds = [m for m, red in markers(facts) if red]
        self.assertIn("MOTION_FLOOR_UNDERCOVERED", reds,
                      "真清单的地板是 2（detail-kind-change + empty-state），judged=1 必须红")
        self.assertIn("MOTION_FLOOR_BAD_REASON", reds,
                      "detail-kind-change 没登记任何允许理由 ⇒ 这条红必须另外红，不与地板混成一团")
        loose = json.loads(json.dumps(EXPECTATIONS))
        for spec in loose["arms"].values():
            spec["must_judge"] = False
            spec["allowed_not_run_reasons"] = sorted(
                set(spec["allowed_not_run_reasons"])
                | {"premise-not-visible", "clock-coarse-in-window"})
        self.assertNotIn("MOTION_FLOOR_UNDERCOVERED",
                         [m for m, red in markers(facts, loose) if red],
                         "地板算成 0 之后还红 ⇒ 那个 2 是写死的，不是从清单来的")


    def testMissingSummaryKeyIsRed(self):
        facts = parse(log("MOTION_RESOLVE_SUMMARY judged=3/4 not-run=-",
                          summary="MOTION_SUMMARY notice-banner=3 detail-kind-change=3 empty-state=4"))
        self.assertIn("MOTION_FLOOR_MISSING_KEY", [m for m, red in markers(facts) if red])

    def testExtraSummaryKeyIsRed(self):
        facts = parse(log("MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-",
                          summary=SUMMARY + " heat-first-record=2"))
        self.assertIn("MOTION_FLOOR_UNLISTED_SCENARIO", [m for m, red in markers(facts) if red])

    def testFinishedSuiteWithoutResolveLineIsRed(self):
        # 旧版在这里 exit 0（"旧版判据没有这一行"）—— 那是免检牌。
        facts = parse("\n".join([EXECUTED, SUMMARY]))
        self.assertIn("MOTION_FLOOR_NO_RESOLVE", [m for m, red in markers(facts) if red])

    def testUnfinishedSuiteIsSkippedNotRed(self):
        facts = parse("\n".join([SUMMARY, "MOTION_RESOLVE_SUMMARY judged=1/4 not-run=x"]))
        marks = markers(facts)
        self.assertEqual([m for m, red in marks if red], [])
        self.assertIn("MOTION_FLOOR_SKIPPED=suite-did-not-finish", [m for m, _ in marks])

    # ---- 两条"设计上的反面"：不许把漂的臂判成恒红，也不许让清单变成免检牌堆 ----

    def testFlakyArmBeingJudgedIsNotRed(self):
        # dismiss 登记成 must_judge=false（它会随采样漂）。它判到了 **不该** 红，
        # 否则就是"判不到红、判到也红"，而恒红的守卫最后会被人删掉。
        facts = parse(log("MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-"))
        self.assertEqual([m for m, red in markers(facts) if red], [])

    def testStaleFlagIsWhatMakesJudgedRed(self):
        strict = json.loads(json.dumps(EXPECTATIONS))
        strict["arms"]["notice-banner-dismiss"]["stale_if_judged"] = True
        facts = parse(log("MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-"))
        self.assertIn("MOTION_FLOOR_STALE", [m for m, red in markers(facts, strict) if red])
        # 同一份日志、没有 stale 标记 ⇒ 不红。这一格把"红"钉在登记上而不是钉在读数上。
        self.assertEqual([m for m, red in markers(facts) if red], [])

    # ---- 两份真日志：一份是"今天就是这样"，一份是"坏了要说为什么" ----

    def testRealLocalLogIsRedUnderTheTightenedRegistry(self):
        """本机那份真日志（R46 抓的，带捕获之前）今天**必须红，而且只红在地板上**。

        形状换了三轮，这里把三轮都留下：
          · R46–R51：`notice-banner` 的 `premise-not-visible` 不在允许列表里 ⇒ BAD_REASON + UNDERCOVERED；
          · R52：把两臂登记成"可以判不到" ⇒ 同一份日志变成**绿 + THIN**；
          · R57：`captureRect` 把抓一帧从 39.6ms 打到 4.5ms ⇒ 两臂今天判得到，清单改回必须判到，
            于是这份**旧**日志重新变成红，且只红在 UNDERCOVERED（judged=2 < 地板 4）。
        理由那两格不再红是因为理由都登记过 ⇒ 这一格同时钉住"红只该来自地板"，
        而不是"清单一改就到处冒红"。
        """
        facts = parse(LOCAL_RUNNER_LOG)
        reds = [m for m, red in markers(facts) if red]
        self.assertEqual(reds, ["MOTION_FLOOR_UNDERCOVERED"],
                         "本机真日志的红变了形状 ⇒ 要么清单又漂了，要么闸门判错了：%s" % reds)
        self.assertEqual([m for m, _ in markers(facts) if m.startswith("MOTION_FLOOR_THIN")], [],
                         "清单收紧之后 THIN 这一族已经没有入口了；它还在说明 thin_warnings 没清空")

    def testSilentRunnerLogRedsAndNamesTheSkips(self):
        """run 38543090198：整族一条读数都没打。红 + **必须把 skip 原因打出来**。

        那一次的 CI 步骤只 grep `MOTION_NOT_RUN=`，而 XCTest 层 `XCTSkipUnless` 的中文原因
        不带这个前缀 ⇒ 红是红了，没人知道为什么（R36 说的"红必须有名字"在这里没做到）。
        """
        facts = parse(RUNNER_SILENT_LOG)
        self.assertIsNone(facts["judged"])
        self.assertEqual(facts["executed"], 28)
        self.assertEqual(len(facts["skips"]), 4,
                         "夹具里 4 条 `Test skipped - …` 必须全被读到，一条都不许漏")
        marks = markers(facts)
        self.assertIn("MOTION_FLOOR_NO_RESOLVE", [m for m, red in marks if red])
        named = [m for m, _ in marks if m.startswith("MOTION_FLOOR_SKIPS")]
        self.assertEqual(len(named), 1, "NO_RESOLVE 必须紧跟一行 SKIPS，否则这条红没有名字")
        message = dict((m, msg) for m, msg, _ in verdicts(facts, EXPECTATIONS))[named[0]]
        self.assertIn("testNativeRowMoveIsVisibleToTheRuler", message)
        self.assertIn("app-not-active", message)

    def testSkipReasonWithoutTheMotionPrefixIsStillSurfaced(self):
        """合成一格：原因里**不带** `MOTION_NOT_RUN=` 的那种 skip 也必须被捞出来。

        这一格钉的是解析器不许只认自家前缀 —— CI 那一步的 grep 就是这么漏掉整族缺席的。
        """
        text = ("\t Executed 24 tests, with 1 test skipped and 0 failures (0 unexpected) in 70 seconds\n"
                + SUMMARY + "\n"
                + "MotionFilmstripTests.swift:2402: -[ClipboardHistoryAppTests"
                  ".MotionFilmstripTests testTransitionsAreActuallyRunning] : Test skipped - "
                  "动效胶片探针：设 CLIPBOARD_HISTORY_UI_MOTION=1 才跑（会抢前台并开窗）\n")
        facts = parse(text)
        self.assertIn("MOTION_FLOOR_SKIPS", [m for m, _ in markers(facts)])
        self.assertEqual(facts["skips"][0][0], "testTransitionsAreActuallyRunning")

    def testRelaxedArmsMustCiteARunId(self):
        """放宽必须留证据：任何 `must_judge=false` 的臂，note 里要有一个 run 号或测量出处。

        这一格防的是"为了让 CI 变绿而把登记改松" —— 那正是本仓库记过一整族的事
        （为过夹具改判据 / 把红藏起来）。改登记可以，但每一次都要留下**哪一次运行**逼着改。
        """
        for name, spec in EXPECTATIONS["arms"].items():
            if spec["must_judge"]:
                continue
            note = spec.get("note", "")
            self.assertTrue(re.search(r"run \d{8,}", note) or "fixtures/" in note,
                            "%s 被放行却没写是哪次运行/哪份夹具逼的 ⇒ 登记成了口头承诺" % name)

    def testThinWarningNeedsARegisteredReasonForEachAbsentArm(self):
        """THIN 只放行"理由在登记之内"的缺席；换一种坏法仍然要红（不许用 THIN 兜底）。

        R57 之后今天的清单里没有 thin_warnings 条目了（四臂都必须判到），
        所以这一格换成**合成清单**：规则要能被测，哪怕今天没人用它。
        """
        relaxed = json.loads(json.dumps(EXPECTATIONS))
        for arm in ("notice-banner", "notice-banner-dismiss"):
            relaxed["arms"][arm]["must_judge"] = False
        relaxed["thin_warnings"] = [{"arms": ["notice-banner", "notice-banner-dismiss"],
                                     "points_to": "BACKLOG 77", "note": "合成"}]
        text = log("MOTION_RESOLVE_SUMMARY judged=2/4 not-run=notice-banner,notice-banner-dismiss",
                   extra="MOTION_NOT_RUN=something-never-seen notice-banner：换了种坏法\n"
                         "MOTION_NOT_RUN=clock-coarse-in-window notice-banner-dismiss：x")
        marks = markers(parse(text), relaxed)
        self.assertIn("MOTION_FLOOR_BAD_REASON", [m for m, red in marks if red])
        self.assertIn("MOTION_FLOOR_THIN", [m for m, _ in marks])

    # ---- 清单自己也要被量 ----

    def testExpectationsCoverExactlyTheScenarioList(self):
        self.assertEqual(sorted(EXPECTATIONS["arms"]), sorted(EXPECTATIONS["scenarios"]),
                         "清单里有臂没登记，或登记了不在场景表里的臂")
        for name, spec in EXPECTATIONS["arms"].items():
            self.assertIn("must_judge", spec, "%s 没写 must_judge ⇒ 地板算不出来" % name)
            if not spec["must_judge"]:
                self.assertTrue(spec.get("allowed_not_run_reasons"),
                                "%s 允许判不到，却没登记任何允许的理由 ⇒ 闸门只会恒红或恒绿" % name)
        self.assertTrue(any(spec["must_judge"] for spec in EXPECTATIONS["arms"].values()),
                        "一条 must_judge 都没有 ⇒ 地板是 0，这条闸门就是装饰")

    def testRegistryIsStrictAgain(self):
        """R57 把两臂的 must_judge 改回 true，这一格不许它悄悄滑回去。

        为什么单独一格：R52 那次放宽是**有证据的**（两台机器都分辨不了），
        而放宽的代价是地板从 4 降到 2 —— 一条只判到 2/4 的闸门，
        与"今天到底验了几条"这句话一起变得没有分量。
        今天修的是原因（捕获面积 ⇒ 成本），不是症状，所以清单必须跟着收紧。
        哪天又要放宽，note 里得写新的 run 号/毫秒数（`testExpectationsCoverExactlyTheScenarioList`
        那条"must_judge=false 必须登记允许的理由"仍然在守着）。
        """
        for arm in ("notice-banner", "notice-banner-dismiss"):
            self.assertTrue(EXPECTATIONS["arms"][arm]["must_judge"],
                            "%s 又被放宽了 ⇒ 地板会悄悄降到 2，而带捕获之后今天没有放宽的理由" % arm)
        self.assertEqual(EXPECTATIONS["thin_warnings"], [],
                         "thin_warnings 还留着条目 ⇒ 有一族'两个都不判到只警告'的口子没关")
        self.assertEqual(len([a for a, s in EXPECTATIONS["arms"].items() if s["must_judge"]]), 4,
                         "四臂全该必须判到")

    def testGateExitCodeFollowsTheReds(self):
        with tempfile.TemporaryDirectory() as folder:
            green = os.path.join(folder, "green.log")
            with io.open(green, "w", encoding="utf-8") as handle:
                # R57 之后"绿"必须是四臂全判到 —— 本机那份旧日志今天该红（见上）。
                handle.write(log("MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-"))
            red = os.path.join(folder, "red.log")
            with io.open(red, "w", encoding="utf-8") as handle:
                handle.write(RUNNER_SILENT_LOG)     # 整族没读数 ⇒ 红
            for path, expected in ((green, 0), (red, 1)):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    code = main([path, "--expectations", str(EXPECTATIONS_PATH)])
                self.assertEqual(code, expected, buffer.getvalue())
                self.assertIn("MOTION_FLOOR_FACTS", buffer.getvalue())
                # 绿也要有 OK：以前 OK 只在"一条结果都没有"时打，
                # 于是"有 THIN 的绿"在日志里长得像"什么都没判"。
                self.assertIn("MOTION_FLOOR_OK" if expected == 0 else "MOTION_FLOOR_REDS=1",
                              buffer.getvalue())
            missing = os.path.join(folder, "nope.log")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                self.assertEqual(main([missing, "--expectations", str(EXPECTATIONS_PATH)]), 2,
                                 "日志读不到 ≠ 通过")

    def testUnreadableExpectationsIsExitTwo(self):
        with tempfile.TemporaryDirectory() as folder:
            good = os.path.join(folder, "ok.log")
            with io.open(good, "w", encoding="utf-8") as handle:
                handle.write(log("MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-"))
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main([good, "--expectations", os.path.join(folder, "nope.json")])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
