#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`motion_red_occurrence.py` 的真值表（R540 / 627 / 622 的出现率读数）。

三条规矩：skip 不是红、skip 不进 executed 分母、copy receipt 的通过不落日志。
刀 M1419 把「skip 不计执行」改坏时，这里必须红。
"""
import io
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "scripts", "motion_red_occurrence.py")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import motion_red_occurrence as occ  # noqa: E402


def line(step, body):
    return "build-and-test\t%s\t2026-11-01T00:00:00Z %s\n" % (step, body)


COPY_RED = line("Motion filmstrip (report-only)",
                "MotionFilmstripTests testCopyReceiptAppearsAndDismissesWithAVisibleProcess]' failed (10.9 seconds).")
COPY_SKIP = line("Swift tests (executed-count gate)",
                 "Test Case '-[AppTests.MotionFilmstripTests testCopyReceiptAppearsAndDismissesWithAVisibleProcess]' skipped (0.000 seconds).")
FOLD_PASS = line("Swift tests (executed-count gate)",
                 "Test Case '-[AppTests.MainWindowFoldMotionTests testCollapseWidthIsMeasuredFrameByFrame]' passed (0.7 seconds).")
FOLD_RED = line("Swift tests (executed-count gate)",
                "Test Case '-[AppTests.MainWindowFoldMotionTests testCollapseWidthIsMeasuredFrameByFrame]' failed (1.1 seconds).")
FOLD_SKIP = line("Swift tests (executed-count gate)",
                 "Test Case '-[AppTests.MainWindowFoldMotionTests testCollapseWidthIsMeasuredFrameByFrame]' skipped (0.001 seconds).")
FLOOR = line("Motion coverage floor",
             "MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=- summary=x 红的用例=- 汇总行报红=0 机器=github-runner")
FLOOR_RED = line("Motion coverage floor",
                 "MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=- summary=x 红的用例=testMarkdownModeLabelChangeIsAVisibleProcess 汇总行报红=1 机器=github-runner")
FPS = line("On-screen interaction probes (report-only)",
           "FORWARDED PROBE_FPS 机器=arm64/macOS 15.8/1x baseline_p95=16.67 off_p95=42.56 loaded_p95=46.73 比值=1.098 预算=3.00 n=175 worst=262.3ms 超锚点帧=2")


class MotionRedOccurrenceTests(unittest.TestCase):

    def test_copy_red_comes_from_filmstrip_and_skip_is_not_red(self):
        red = occ.scan(COPY_RED + COPY_SKIP)
        self.assertEqual("RED", red["copy"], u"filmstrip 的失败行必须算红")
        skip = occ.scan(COPY_SKIP)
        self.assertNotEqual("RED", skip["copy"], u"Swift tests 的 skip 不是红")
        self.assertEqual("NOT_PRINTED", skip["copy"], u"filmstrip 的通过/未跑都不落日志")
        self.assertTrue(skip["copy_swift_skip"], u"Swift 卷的 skip 要单独留痕")

    def test_fold_skip_is_not_executed_and_red_beats_pass(self):
        self.assertEqual("SKIP", occ.scan(FOLD_SKIP)["fold"])
        self.assertEqual("PASS", occ.scan(FOLD_PASS)["fold"])
        self.assertEqual("RED", occ.scan(FOLD_RED + FOLD_PASS)["fold"])
        z = occ.summarize([occ.scan(FOLD_PASS), occ.scan(FOLD_RED), occ.scan(FOLD_SKIP)])
        self.assertEqual(2, z["fold_exec"], u"skipped 不许进 executed 分母")
        self.assertEqual(1, z["fold_red"])

    def test_frame_multi_fields_are_read_from_one_line(self):
        f = occ.scan(FPS)["frame"]
        self.assertEqual(("16.67", "42.56", "46.73", "1.098", "175", "262.3", "2"), f)
        self.assertIsNone(occ.scan(FLOOR)["frame"], u"没有 PROBE_FPS 就是 None（不是 0）")
        self.assertEqual("testMarkdownModeLabelChangeIsAVisibleProcess",
                         occ.scan(FLOOR_RED)["judged"][4], u"红的用例名必须被读出来")

    def test_summary_counts_copy_and_fold_separately(self):
        z = occ.summarize([occ.scan(COPY_RED + FOLD_PASS), occ.scan(COPY_SKIP + FOLD_RED)])
        self.assertEqual(1, z["copy_red"])
        self.assertEqual(1, z["fold_red"])
        self.assertEqual(2, z["fold_exec"])
        self.assertEqual(2, z["logs"])
        self.assertEqual(0, z["markdown_red"], u"这份合成卷里没有 Motion floor 红名")

    def test_cli_reads_logs_and_unreadable_is_not_zero_red(self):
        fd, path = tempfile.mkstemp(suffix=".log")
        os.close(fd)
        with io.open(path, "w", encoding="utf-8") as h:
            h.write(COPY_RED + FOLD_PASS + FLOOR_RED + FPS)
        try:
            proc = subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True)
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertIn("copy_receipt reds=1", proc.stdout)
            self.assertIn("fold reds=0 executed=1", proc.stdout)
            self.assertIn("markdown reds=1", proc.stdout)
            self.assertIn("FRAME_MULTI logs=1 with=1", proc.stdout)
            self.assertIn("over_runs=1", proc.stdout)
            self.assertIn("loaded_p95_max=46.73", proc.stdout)
            self.assertIn("red=testMarkdownModeLabelChangeIsAVisibleProcess", proc.stdout)
            missing = subprocess.run([sys.executable, SCRIPT, path + ".missing"],
                                     capture_output=True, text=True)
            self.assertEqual(2, missing.returncode, u"一份日志都没读到必须退 2")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
