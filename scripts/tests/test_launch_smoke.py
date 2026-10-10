"""`scripts/launch_smoke.py` 的自测。

CI 里真启动那一步是报告型的（无头 runner 上窗口服务未必听话），但**判定逻辑**必须被硬门住：
"这个包到底算不算启动了"这句话如果判错，报告型步骤就变成一台只会点头的机器。
所以这里测的是纯函数 `evaluate` 与 `executable_in`，不需要真的启一个 GUI。
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.launch_smoke import (  # noqa: E402
    LOG_FILE_NAME,
    run,
    SECOND_INSTANCE_MARKER,
    SIGTERM_MARKER,
    SUCCESS_MARKER,
    evaluate,
    executable_in,
)


class LaunchSmokeTests(unittest.TestCase):
    def test_success_is_not_just_a_zero_exit_code(self):
        verdict = evaluate("%s\n" % SUCCESS_MARKER, True, -15)
        self.assertTrue(verdict["ok"], verdict["reasons"])
        # 被我们 terminate 的 GUI app 退出码必然是负的；判"退出码 == 0"会把所有成功都判成失败
        self.assertEqual(verdict["exit_code"], -15)

    def test_empty_log_is_a_failure_not_a_pass(self):
        verdict = evaluate("", True, None)
        self.assertFalse(verdict["ok"])
        self.assertIn("日志文件为空", " ".join(verdict["reasons"]))

    def test_missing_start_marker_is_reported(self):
        verdict = evaluate("some other noise\n", True, None)
        self.assertFalse(verdict["ok"])
        self.assertFalse(verdict["saw_start"])

    def test_second_instance_abort_is_its_own_reason(self):
        # 这条守卫命中时 app 会**静默退出**：没有它，冒烟测试会把它读成"启动成功但立刻退了"
        log = "%s\n[DEBUG] 检测到同 bundle 的另一实例 pid=4242：%s\n" % (SUCCESS_MARKER, SECOND_INSTANCE_MARKER)
        verdict = evaluate(log, False, 0)
        self.assertFalse(verdict["ok"])
        self.assertTrue(verdict["saw_second_instance_abort"])

    def test_early_death_without_an_orderly_terminate_is_a_failure(self):
        log = "%s\n" % SUCCESS_MARKER
        verdict = evaluate(log, False, -11)   # SIGSEGV：没活到检查点
        self.assertFalse(verdict["ok"])
        self.assertIn("进程提前退出", " ".join(verdict["reasons"]))

    def test_death_after_an_orderly_terminate_is_fine(self):
        log = "%s\n%s\n" % (SUCCESS_MARKER, SIGTERM_MARKER)
        verdict = evaluate(log, False, 0)
        self.assertTrue(verdict["ok"], verdict["reasons"])

    def test_executable_is_read_from_the_plist_not_guessed_from_the_product_name(self):
        with tempfile.TemporaryDirectory() as root:
            bundle = Path(root) / "任意名字.app"
            macos = bundle / "Contents" / "MacOS"
            macos.mkdir(parents=True)
            (macos / "TimeScissors").write_text("#!/bin/sh\n")
            (bundle / "Contents" / "Info.plist").write_text(
                '<?xml version="1.0"?><plist version="1.0"><dict>'
                '<key>CFBundleExecutable</key><string>TimeScissors</string>'
                '</dict></plist>')
            self.assertEqual(executable_in(str(bundle)), str(macos / "TimeScissors"))

    def test_missing_bundle_is_reported_as_a_failure_not_an_exception(self):
        self.assertIsNone(executable_in("/nonexistent/whatever.app"))
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(executable_in(root))

    def test_end_to_end_against_a_fake_bundle(self):
        """真的把 `run()` 跑一遍 —— 但用一个假包，不碰用户的 app。

        在开发机上真启产品是有代价的：用户那份 时间剪史 正在跑，我的冒烟会开出第二个实例
        和第二个窗口（本轮实测过，见账本 D-041）。所以这里用一个 shell 脚本冒充包内可执行文件，
        把 `run()` 的三段（找可执行文件 → 传隔离环境变量 → 读日志判定）都跑真的，
        只有"被启动的东西"是假的。
        """
        with tempfile.TemporaryDirectory() as root:
            bundle = Path(root) / "Fake.app"
            macos = bundle / "Contents" / "MacOS"
            macos.mkdir(parents=True)
            script = macos / "faked"
            script.write_text(
                "#!/bin/sh\n"
                'log="$CLIPBOARD_HISTORY_LOG_DIR/lifecycle_debug.log"\n'
                'printf "[DEBUG] applicationDidFinishLaunching called\\n" >> "$log"\n'
                'printf "%s\\n" "$CLIPBOARD_HISTORY_DATA_DIR" > "$CLIPBOARD_HISTORY_LOG_DIR/data_dir.txt"\n'
                "sleep 3\n"
            )
            script.chmod(0o755)
            (bundle / "Contents" / "Info.plist").write_text(
                '<?xml version="1.0"?><plist version="1.0"><dict>'
                '<key>CFBundleExecutable</key><string>faked</string></dict></plist>')

            workdir = Path(root) / "work"
            workdir.mkdir()
            ok, verdict, _text = run(str(bundle), settle_seconds=0.2, timeout=8, workdir=str(workdir))
            self.assertTrue(ok, verdict["reasons"])
            self.assertTrue(verdict["saw_start"])

            # 隔离开关必须真的传给了子进程：它报告的数据目录不许是用户那份
            recorded = workdir / "logs" / "data_dir.txt"
            self.assertTrue(recorded.exists(), "假包没看到 CLIPBOARD_HISTORY_DATA_DIR —— 隔离开关没传进去")
            seen = recorded.read_text().strip()
            self.assertNotIn("Application Support", seen)
            self.assertIn("data", seen)
            self.assertTrue(seen.startswith(str(workdir)),
                            "隔离数据目录不在本次临时区里：{}".format(seen))

    def test_second_instance_abort_is_detected_end_to_end(self):
        with tempfile.TemporaryDirectory() as root:
            bundle = Path(root) / "Fake2.app"
            macos = bundle / "Contents" / "MacOS"
            macos.mkdir(parents=True)
            script = macos / "faked"
            script.write_text(
                "#!/bin/sh\n"
                'log="$CLIPBOARD_HISTORY_LOG_DIR/lifecycle_debug.log"\n'
                'printf "[DEBUG] applicationDidFinishLaunching called\\n" >> "$log"\n'
                'printf "[DEBUG] 检测到同 bundle 的另一实例 pid=4242：本次启动取消\\n" >> "$log"\n'
                "sleep 2\n"
            )
            script.chmod(0o755)
            (bundle / "Contents" / "Info.plist").write_text(
                '<?xml version="1.0"?><plist version="1.0"><dict>'
                '<key>CFBundleExecutable</key><string>faked</string></dict></plist>')
            ok, verdict, _text = run(str(bundle), settle_seconds=0.2, timeout=8)
            self.assertFalse(ok)
            self.assertTrue(verdict["saw_second_instance_abort"],
                            "第二实例守卫命中时冒烟测试必须报出来，而不是当成启动成功：%s" % verdict)

    def test_log_file_name_matches_the_product(self):
        # 文件名漂了 = 冒烟测试读不到日志 = 报"启动失败"，而真相是探针自己坏了。
        source = Path(__file__).resolve().parents[2] / "ClipboardHistory" / "Sources" / \
            "ClipboardHistoryApp" / "Utilities" / "LifecycleDebugLogger.swift"
        self.assertIn(LOG_FILE_NAME, source.read_text(encoding="utf-8"))

    def test_markers_appear_in_the_products_log_source(self):
        # 判据里那两个字符串是**从产品日志里抄来的**。产品改了文案而这里没跟着改，
        # 冒烟测试就会永远"看不到"那个标记 —— 于是守卫命中时它反而报成功。
        source = Path(__file__).resolve().parents[2] / "ClipboardHistory" / "Sources" / \
            "ClipboardHistoryApp" / "Managers" / "AppDelegate.swift"
        text = source.read_text(encoding="utf-8")
        self.assertIn(SUCCESS_MARKER, text)
        self.assertIn(SECOND_INSTANCE_MARKER, text)


if __name__ == "__main__":
    unittest.main()
