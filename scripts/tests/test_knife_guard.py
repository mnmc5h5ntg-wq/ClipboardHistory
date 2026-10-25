#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R375 / BACKLOG 433：崩溃安全还原 + 硬超时的纯函数测试。"""
import importlib.util
import os
import tempfile
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


if __name__ == u"__main__":
    unittest.main()
