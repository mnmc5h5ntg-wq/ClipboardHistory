#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R370 / BACKLOG 432：空刀探测的四态词表。

现场：R368 的 M906 —— 落刀前后 `HIDDEN_ARMS` 三组数一字不差，判据也没红（ESCAPED）。
旧判法只会说"没咬住"；这一支把"读数没动"从沉默里拆出来，另给两个有名字的态：
  EMPTY_KNIFE（没红且读数全等）与 READOUT_BLIND（红了但读数全等，只印不判死）。
"""
import importlib.util
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / u".scratch" / u"motion-audit-2" / u"readout_probe.py"


def load():
    spec = importlib.util.spec_from_file_location(u"readout_probe_under_test", str(TOOL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FourStateTests(unittest.TestCase):
    def test_caught_with_changed_readout_stays_caught(self):
        tool = load()
        self.assertEqual("CAUGHT", tool.four_state("CAUGHT", u"HIDDEN_ARMS rot=33", u"HIDDEN_ARMS rot=0"))

    def test_caught_with_identical_readout_is_only_blind(self):
        tool = load()
        self.assertEqual("READOUT_BLIND", tool.four_state("CAUGHT", u"HIDDEN_ARMS rot=33", u"HIDDEN_ARMS rot=33"),
                         u"红了但读数一模一样 ⇒ 红不是这条读数引起的；只印，不判死")

    def test_escaped_with_identical_readout_is_an_empty_knife(self):
        tool = load()
        self.assertEqual("EMPTY_KNIFE", tool.four_state("ESCAPED", u"HIDDEN_ARMS rot=33", u"HIDDEN_ARMS rot=33"),
                         u"M906 的形状：没红、读数没动 ⇒ 刀是空的")

    def test_escaped_with_changed_readout_stays_escaped(self):
        tool = load()
        self.assertEqual("ESCAPED", tool.four_state("ESCAPED", u"HIDDEN_ARMS rot=33", u"HIDDEN_ARMS rot=6"))

    def test_unreadable_readout_never_counts_as_no_change(self):
        tool = load()
        self.assertEqual("ESCAPED", tool.four_state("ESCAPED", None, u"HIDDEN_ARMS rot=33"),
                         u"读数没拿到 → 不许冒充「没变化」")
        self.assertEqual("CAUGHT", tool.four_state("CAUGHT", u"HIDDEN_ARMS rot=33", None))

    def test_summary_counts_the_new_state(self):
        tool = load()
        counts = tool.summarize(["CAUGHT", "EMPTY_KNIFE", "READOUT_BLIND", "NOT_RUN", "RESTORE_FAILED"])
        self.assertEqual({"caught": 1, "empty": 1, "blind": 1, "escaped": 0, "not_run": 2}, counts)


if __name__ == "__main__":
    unittest.main()
