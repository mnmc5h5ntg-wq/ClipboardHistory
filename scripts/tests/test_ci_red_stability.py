# -*- coding: utf-8 -*-
"""`ci_red_stability.py` 的真值表（BACKLOG 166 的仪器自己要有牙）。

规矩（D-034 / R105 的 U-320 那一族）：一把新尺落盘当天必须带
①正对照（两跑一样 ⇒ 必须报"没有换班"），②反向牙（把红挪到另一个用例 ⇒ 必须报换班），
③形状覆盖（带宏名的 `XCTAssert… failed` 与裸 `XCTFail` 的 `error: … : failed - …` 两种都要数），
④读不到不等于没有（缺文件必须退 2，不许退 0 冒充"两台都干净"）。
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "ci_red_stability.py")


def log_line(body):
    # `gh run view --log` 每行是 `<job>\t<step>\t<时间戳 正文>`（ci_read 的实测形状）
    return "build-and-test\tSwift tests\t2026-10-17T00:00:00Z %s\n" % body


def write_log(lines):
    fd, path = tempfile.mkstemp(suffix=".log")
    os.close(fd)
    with io.open(path, "w", encoding="utf-8") as handle:
        for line in lines:
            handle.write(line)
    return path


def run(a, b):
    proc = subprocess.run([sys.executable, SCRIPT, "--from-file", a, b],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


class RedStabilityTests(unittest.TestCase):
    MACRO_A = log_line("Test Case '-[AppTests.UICaptureTests testFrameIntervalsUnderStateChanges]' failed")
    MACRO_A2 = log_line("FAILED testFrameIntervalsUnderStateChanges：XCTAssertLessThanOrEqual failed: (\"196.7\") is greater than (\"120.0\")")
    MACRO_B = log_line("FAILED testBandCaptureIsCheaperAndStillSeesTheMotion：XCTAssertLessThanOrEqual failed: (\"26.8\") is greater than (\"23.8\")")
    BARE_C = log_line("error: -[AppTests.UICaptureTests testOverlayTypedFrameCarriesNoPhantomSelectionFill] : failed - light：那一条带里没有墨")

    def tearDown(self):
        for attr in ("paths",):
            for p in getattr(self, attr, []):
                if os.path.exists(p):
                    os.unlink(p)

    def test_same_reds_report_no_drift(self):
        """①正对照：两跑红的是同一批用例 ⇒ 换班=0、退出码 0。

        （第一版这里把 `Test Case '-[…]' failed` 那一行也当红喂进去 ⇒ 它**不是**红行
        （`assertion_reds` 认的是"带 XCTAssert 的失败行"与"裸 `: failed - `"两种形状），
        于是 B 侧红=0、这一格假失败。改法是把同一朵真红放进两边，不是放宽判据。）
        """
        self.paths = [write_log([self.MACRO_A, self.MACRO_A2]), write_log([self.MACRO_A2])]
        code, out = run(self.paths[0], self.paths[1])
        self.assertEqual(0, code, out)
        self.assertIn("两跑都红=1", out)
        self.assertIn("换班=0", out)
        self.assertIn("testFrameIntervalsUnderStateChanges", out)

    def test_swapped_red_is_caught(self):
        """②反向牙：R108 红 bandCapture、R109 红 frameIntervals ⇒ 必须报换班并退 1。"""
        self.paths = [write_log([self.MACRO_B]), write_log([self.MACRO_A2])]
        code, out = run(self.paths[0], self.paths[1])
        self.assertEqual(1, code, out)
        self.assertIn("ONLY_A     testBandCaptureIsCheaperAndStillSeesTheMotion", out)
        self.assertIn("ONLY_B     testFrameIntervalsUnderStateChanges", out)
        self.assertIn("两跑都红=0", out)
        self.assertIn("换班=1", out)

    def test_bare_xctfail_shape_counts(self):
        """③形状覆盖：裸 `XCTFail`（没有 `XCTAssert` 这个词）也必须被数进来。"""
        self.paths = [write_log([self.BARE_C]), write_log([self.BARE_C])]
        code, out = run(self.paths[0], self.paths[1])
        self.assertEqual(0, code, out)
        self.assertIn("testOverlayTypedFrameCarriesNoPhantomSelectionFill", out)
        self.assertIn("形状=bare", out)

    def test_shape_change_alone_counts_as_drift(self):
        """同一个用例、两跑红的**形状**不同（宏名 vs 裸 fail）⇒ 也算换班。"""
        self.paths = [write_log([self.MACRO_A2]), write_log([self.BARE_C.replace(
            "testOverlayTypedFrameCarriesNoPhantomSelectionFill", "testFrameIntervalsUnderStateChanges")])]
        code, out = run(self.paths[0], self.paths[1])
        self.assertEqual(1, code, out)
        self.assertIn("形状换=1", out)

    def test_unreadable_log_is_not_clean(self):
        """④读不到 ≠ 没有红：缺一份日志必须退 2，并且不许打出"换班=0"。"""
        self.paths = [write_log([self.MACRO_A])]
        code, out = run(self.paths[0], "/tmp/这一份日志不存在-r110.log")
        self.assertEqual(2, code, out)
        self.assertIn("RED_STABILITY_UNREADABLE=1", out)
        self.assertNotIn("换班=0", out)

    def test_help_exits_zero(self):
        """`--help` 必须退 0（`test_script_help_runs` 对 scripts/ 下每一支都这么要求）。"""
        proc = subprocess.run([sys.executable, SCRIPT, "--help"], capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("两次 CI 跑", proc.stdout)


    def test_unnamed_reds_are_not_one_bucket(self):
        """U-364 的牙：两跑各有**一朵不同**的"名字在另一行"的红 ⇒ 不许塞进同一个桶报成"两跑都红"。"""
        a = log_line("Test Case '-[X y]' failed")
        a2 = log_line('XCTAssertGreaterThan failed: ("0") is greater than ("0") - 参照臂 cardprobe-split-groupbox dark 在带子里读到 0 行墨')
        b2 = log_line('XCTAssertGreaterThan failed: ("0") is greater than ("0") - 参照臂 cardprobe-split-groupbox light 在带子里读到 0 行墨')
        self.paths = [write_log([a, a2]), write_log([a, b2])]
        code, out = run(self.paths[0], self.paths[1])
        self.assertEqual(1, code, out)
        self.assertIn("ONLY_A", out)
        self.assertIn("ONLY_B", out)


if __name__ == "__main__":
    unittest.main()
