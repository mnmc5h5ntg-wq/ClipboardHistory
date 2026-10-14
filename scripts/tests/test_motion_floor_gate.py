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
它当正对照：这份日志必须红，而且红在该红的两处（本机 notice-banner 是 premise-not-visible、
judged=2 低于地板 3）—— 一张只会绿的夹具证明不了任何事。
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
        # R44 的真实形状：dismiss 掉了一臂，理由登记过 ⇒ 放行，但 FACTS 行要把它打出来。
        text = log("MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss",
                   extra="MOTION_NOT_RUN=clock-coarse-in-window notice-banner-dismiss：事件段最粗 101ms")
        facts = parse(text)
        self.assertEqual([m for m, red in markers(facts) if red], [])
        self.assertEqual(facts["judged"], 3)

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
        # 旧版写死 `judged<2`。这里 judged=2 却掉了两条 must_judge ⇒ 必须红。
        text = log("MOTION_RESOLVE_SUMMARY judged=2/4 not-run=notice-banner,detail-kind-change",
                   extra="MOTION_NOT_RUN=premise-not-visible notice-banner：x\n"
                         "MOTION_NOT_RUN=premise-not-visible detail-kind-change：x")
        facts = parse(text)
        self.assertIn("MOTION_FLOOR_UNDERCOVERED", [m for m, red in markers(facts) if red])

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

    # ---- 真日志正对照 ----

    def testRealLocalLogIsRedOnExactlyTwoThings(self):
        facts = parse(LOCAL_RUNNER_LOG)
        reds = [m for m, red in markers(facts) if red]
        # 本机 notice-banner 是 premise-not-visible（登记里它是 must_judge、允许理由为空）；
        # judged=2 低于地板 3。两件事都必须被这条闸门抓住。
        self.assertEqual(reds, ["MOTION_FLOOR_BAD_REASON", "MOTION_FLOOR_UNDERCOVERED"],
                         "真日志的红变了形状 ⇒ 要么登记错了，要么闸门判错了：%s" % reds)

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

    def testGateExitCodeFollowsTheReds(self):
        with tempfile.TemporaryDirectory() as folder:
            green = os.path.join(folder, "green.log")
            with io.open(green, "w", encoding="utf-8") as handle:
                handle.write(log("MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-"))
            red = os.path.join(folder, "red.log")
            with io.open(red, "w", encoding="utf-8") as handle:
                handle.write(LOCAL_RUNNER_LOG)
            for path, expected in ((green, 0), (red, 1)):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    code = main([path, "--expectations", str(EXPECTATIONS_PATH)])
                self.assertEqual(code, expected, buffer.getvalue())
                self.assertIn("MOTION_FLOOR_FACTS", buffer.getvalue())
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
