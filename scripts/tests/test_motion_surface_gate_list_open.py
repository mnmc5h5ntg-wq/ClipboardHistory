#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`motion_surface_gate --list-open` 要有牙（R173 / 阶段二的清账工具）。

起因是本轮自己撞上的：`MOTION_LEDGER 未清账=59` 只给一个数，而下一轮要挑格子判必须先知道
**是哪 59 格**。当时的做法是反推 JSON（读 `rows` 手工求差），而手工求差用的是
`surfaces × states − rows`，**漏了"行存在但 verdict 不在 cleared_verdicts 里"那一类**
（占位行 `not-measured`）⇒ 反推出的名单会比闸门的计数少，挑出来的格子看着"已判"其实没判。

所以这条判据钉的不是"有没有输出"，而是：
1. 列名单与数名单必须是**同一颗函数**（不一致会打 `OPEN_MISMATCH`，且测试断言两者相等）；
2. 名单不许为空（空名单要么是没活、要么是词表漂了，两种都不许被读成"做完了"）；
3. 每一格都必须落在 `surfaces × states` 的词表里（防止把已判的格子重复列出来）。

判据来源是 `scripts/motion_surface_gate.py` 的真身（`open_cells` / `main`），不在这里另抄一份实现。
"""
import importlib.util
import io
import json
import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / "scripts" / "motion_surface_gate.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("motion_surface_gate_under_test", str(TOOL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def table(rows, surfaces=None, states=None):
    return {
        "verdicts": ["added", "kept", "not-added", "not-applicable", "not-measured"],
        "cleared_verdicts": ["added", "kept", "not-added", "not-applicable"],
        "surfaces": surfaces or [u"主窗口/行", u"设置窗口/热图"],
        "states": states or [u"空", u"悬停", u"聚焦"],
        "rows": rows,
        "floor_cleared": len(rows),
    }


def row(surface, state, verdict):
    return {"surface": surface, "state": state, "verdict": verdict,
            "reason": u"占位理由，长度要够闸门的最小字数要求啊啊啊啊",
            "evidence": u"Sources/ClipboardHistoryApp/Views/SettingsView.swift"}


class MotionSurfaceGateListOpenTests(unittest.TestCase):

    def test_open_cells_skips_only_cleared_verdicts(self):
        mod = load_tool()
        data = table([row(u"主窗口/行", u"悬停", "kept"),
                      row(u"主窗口/行", u"聚焦", "not-measured")])
        todo = mod.open_cells(data)
        self.assertEqual(
            [(u"主窗口/行", u"空"), (u"主窗口/行", u"聚焦"),
             (u"设置窗口/热图", u"空"), (u"设置窗口/热图", u"悬停"), (u"设置窗口/热图", u"聚焦")],
            todo,
            u"占位行（not-measured）不算清账 ⇒ 它必须还在名单里；已判的那格不许出现")
        self.assertNotIn((u"主窗口/行", u"悬停"), todo, u"kept 是已清账的 verdict，重复列出会误导下一轮")

    def test_empty_roster_lists_every_cell_rather_than_nothing(self):
        mod = load_tool()
        self.assertEqual(6, len(mod.open_cells(table([]))),
                         u"rows 为空时名单必须是满的 6 格 —— 空名单会被读成做完了")

    def test_repo_table_open_list_matches_the_census_and_the_vocabulary(self):
        mod = load_tool()
        data = json.load(io.open(REPO / "docs/motion_surface_ledger.json", encoding="utf-8"))
        todo = mod.open_cells(data)
        cells = len(data["surfaces"]) * len(data["states"])
        cleared = set(data["cleared_verdicts"])
        cleared_n = len([r for r in data["rows"] if (r.get("verdict") or "") in cleared])
        self.assertEqual(cells - cleared_n, len(todo),
                         u"列名单与数名单分叉：%d vs %d" % (len(todo), cells - cleared_n))
        # R207 改：原来这两行钉的是「仓库现状必须还剩一些没判」，而"还剩一些"不是不变量 ——
        # 它会在真的判完那天变成恒红的门。要防的是**假判完**，所以换成两条方向相反的账：
        # 上界：一格都没判（rows 被清空）⇒ todo 等于满乘积，这一格仍然红；
        # 下界：todo 为空 ⇒ 必须能证明"每一格都有一行且都在已清账词表里"，否则红。
        self.assertLess(len(todo), cells, u"一格都没判 ⇒ 名单等于满乘积，通常意味着 rows 被清空")
        if not todo:
            self.assertEqual(cells, len(data["rows"]),
                              u"未清账为 0 但行数 %d != 名册乘积 %d ⇒ 有格子整行不见了" % (len(data["rows"]), cells))
            self.assertEqual([], [r for r in data["rows"] if (r.get("verdict") or "") not in cleared],
                              u"未清账为 0 却还有不在已清账词表里的行 ⇒ 词表被动过")
        for surface, state in todo:
            self.assertIn(surface, data["surfaces"], u"名单里冒出词表外的表面：%s" % surface)
            self.assertIn(state, data["states"], u"名单里冒出词表外的状态：%s" % state)

    def test_list_open_flag_prints_one_line_per_open_cell(self):
        import tempfile
        mod = load_tool()
        data = table([row(u"主窗口/行", u"悬停", "kept")])
        # 夹具**不写进 docs/**：那是闸门与 CI 都要读的真目录（R91 那一族：夹具覆盖了
        # 闸门要读的文件、或留下一张没人清的表）。用一次性临时目录，退出即删。
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "list_open_fixture.json")
            io.open(path, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
            old_argv, sys.argv = sys.argv, ["prog", "--path", path, "--list-open"]
            buffer = io.StringIO()
            old_stdout, sys.stdout = sys.stdout, buffer
            try:
                mod.main()
            finally:
                sys.stdout, sys.argv = old_stdout, old_argv
        out = buffer.getvalue()
        self.assertIn("MOTION_LEDGER_OPEN 5", out,
                      u"2×3 的表判掉一格 ⇒ 必须报 5 格未清账，实际输出：%s" % out)
        self.assertEqual(5, len([l for l in out.splitlines() if l.startswith("OPEN ")]),
                         u"OPEN 行数必须等于名单长度（只报数不报名字 = 这条出口没解决本轮的痛点）")
        self.assertNotIn("MOTION_LEDGER_OPEN_MISMATCH", out)
        self.assertFalse(os.path.exists(os.path.join(
            str(REPO), "docs", "motion_surface_ledger_list_open_fixture.json")),
            u"夹具不许落在 docs/ 里：闸门默认读的就是那个目录")


if __name__ == "__main__":
    unittest.main()
