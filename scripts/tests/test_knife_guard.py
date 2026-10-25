#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R375 / BACKLOG 433：崩溃安全还原 + 硬超时的纯函数测试。"""
import importlib.util
import os
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / u".scratch" / u"motion-audit-2" / u"knife_guard.py"


def load():
    spec = importlib.util.spec_from_file_location(u"knife_guard_under_test", str(TOOL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackupRestoreTests(unittest.TestCase):
    def test_backup_then_restore_when_the_target_was_left_mutated(self):
        tool = load()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, u"target.swift")
            with open(path, u"w", encoding=u"utf-8") as handle:
                handle.write(u"let a = 1\n")
            tool.backup(path, u"T")
            with open(path, u"w", encoding=u"utf-8") as handle:
                handle.write(u"let a = 1\nreturn   // MUTANT\n")
            self.assertTrue(tool.restore_if_stale(path, u"T"))
            with open(path, encoding=u"utf-8") as handle:
                self.assertEqual(u"let a = 1\n", handle.read())

    def test_clean_target_is_not_touched(self):
        tool = load()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, u"target.swift")
            with open(path, u"w", encoding=u"utf-8") as handle:
                handle.write(u"let a = 1\n")
            tool.backup(path, u"T")
            self.assertFalse(tool.restore_if_stale(path, u"T"))

    def test_no_backup_means_nothing_to_restore(self):
        tool = load()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, u"target.swift")
            with open(path, u"w", encoding=u"utf-8") as handle:
                handle.write(u"let a = 1\n")
            self.assertFalse(tool.restore_if_stale(path, u"T"))

    def test_clear_backup_removes_the_shadow_copy(self):
        tool = load()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, u"target.swift")
            with open(path, u"w", encoding=u"utf-8") as handle:
                handle.write(u"let a = 1\n")
            tool.backup(path, u"T")
            self.assertTrue(os.path.exists(tool.backup_path(path, u"T")))
            tool.clear_backup(path, u"T")
            self.assertFalse(os.path.exists(tool.backup_path(path, u"T")))


class HardTimeoutTests(unittest.TestCase):
    def test_a_hung_child_is_killed_and_named(self):
        tool = load()
        code, out, timed_out = tool.run([u"sleep", u"5"], timeout_seconds=1)
        self.assertTrue(timed_out, u"1 秒超时没有触发 ⇒ 硬超时形同虚设")
        self.assertIsNone(code)

    def test_a_fast_child_is_not_flagged(self):
        tool = load()
        code, out, timed_out = tool.run([u"true"], timeout_seconds=5)
        self.assertFalse(timed_out)
        self.assertEqual(0, code)

    def test_a_grandchild_in_its_own_session_is_killed_too(self):
        # R376：R375 那一刀超时后，xctest 被 launchd 收养又活了 9 分钟 —— 它不在 swift-test
        # 的进程组里，只 killpg 杀不到。这里让孙子**自开会话**（模拟它），超时后必须一起消失。
        tool = load()
        sentinel = u"R376_SENTINEL_%d" % os.getpid()
        script = (u"import subprocess, sys, time; "
                  u"subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)', sys.argv[1]], "
                  u"start_new_session=True); time.sleep(30)")
        code, out, timed_out = tool.run([u"python3", u"-c", script, sentinel], timeout_seconds=1)
        self.assertTrue(timed_out)
        survivors = subprocess.run([u"pgrep", u"-f", sentinel],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(b"", survivors.stdout.strip(),
                         u"孙进程活下来了（pid=%r）⇒ 超时只杀了进程组，孤儿照样在盘上跑"
                         % survivors.stdout.decode().strip())


class SwallowedReturnTests(unittest.TestCase):
    """R376 / BACKLOG 433：`return` 独占一行、下一行是调用 ⇒ Swift 解析成 `return expr`。"""

    def test_the_exact_m278_shape_is_caught(self):
        tool = load()
        text = (u"    static func emit(_ line: String, to url: URL) {\n"
                u"        writeStdoutLine(line)\n"
                u"        return   // MUTANT: 只 stdout，不落盘\n"
                u"        lock.lock()\n"
                u"        defer { lock.unlock() }\n"
                u"    }\n")
        self.assertEqual(1, len(tool.swallowed_return_lines(text)),
                         u"这一格就是 R374/R375 挂死的那一刀；漏掉它 = 下一次再挂 6 分钟")

    def test_return_before_a_brace_is_fine(self):
        tool = load()
        self.assertEqual([], tool.swallowed_return_lines(u"func f() {\n    return\n}\n"))

    def test_return_before_a_case_label_is_fine(self):
        tool = load()
        text = u"switch x {\ncase .a:\n    return  // MUTANT\ncase .b:\n    break\n}\n"
        self.assertEqual([], tool.swallowed_return_lines(text),
                         u"`case` 不是表达式 —— 把它算成陷阱会让查重开始报假红")

    def test_return_unit_is_fine(self):
        tool = load()
        self.assertEqual([], tool.swallowed_return_lines(u"func f() {\n    return ()\n    foo()\n}\n"))


class DescendantSnapshotTests(unittest.TestCase):
    def test_snapshot_finds_a_live_grandchild(self):
        tool = load()
        proc = subprocess.Popen([u"python3", u"-c",
                                 u"import subprocess, sys, time; "
                                 u"subprocess.Popen(['sleep', '20'], start_new_session=True); time.sleep(20)"])
        try:
            # 让孙子先起来再快照（最多等 2 秒）。
            kids = []
            for _ in range(20):
                kids = tool.descendants(proc.pid)
                if len(kids) >= 1:
                    break
                time.sleep(0.1)
            self.assertGreaterEqual(len(kids), 1, u"快照没看到任何子孙 ⇒ 下面的逐杀是空转")
        finally:
            for pid in [proc.pid] + tool.descendants(proc.pid):
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError:
                    pass
            proc.wait()


if __name__ == u"__main__":
    unittest.main()
