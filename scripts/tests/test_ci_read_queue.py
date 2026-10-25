#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R357 / BACKLOG 428：`ci_read.py queue` 的三种状态与「排在前面几跑」。

为什么要有这一格：R354 追记二那次「五跑同时在队里、零跑结案」，
`latest` 只打 status/conclusion，台账里只剩「未读」一个词 ——
读的人分不清「还没轮到」与「跑了一半挂了」，而「没跑」被当成「没红」是本仓库栽过的形状。
这一支把三态写死，并把 `queued / in_progress / concluded / unknown` 与
「同 workflow 里 created 更早且仍未结案的跑数」做成读数。
"""
import datetime
import importlib.util
import io
import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / u"scripts" / u"ci_read.py"


def load_tool():
    spec = importlib.util.spec_from_file_location(u"ci_read_under_test", str(TOOL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)      # 文件底部有 __main__ 守卫，import 不会跑 gh
    return module


NOW = datetime.datetime(2026, 10, 25, 12, 0, 0, tzinfo=datetime.timezone.utc)


def run(rid, status, created, workflow=u"CI", conclusion=None):
    return {
        u"databaseId": rid,
        u"headSha": u"abcdef" + str(rid),
        u"status": status,
        u"conclusion": conclusion,
        u"createdAt": created,
        u"workflowName": workflow,
        u"displayTitle": u"t" + str(rid),
    }


class QueueStateTests(unittest.TestCase):

    def test_the_three_states_are_written_down_and_unknown_is_named(self):
        tool = load_tool()
        self.assertEqual(u"queued", tool.queue_state(u"queued"))
        self.assertEqual(u"in_progress", tool.queue_state(u"in_progress"))
        self.assertEqual(u"concluded", tool.queue_state(u"completed"))
        self.assertEqual(u"unknown:waiting", tool.queue_state(u"waiting"),
                         u"认不出的状态必须点名，不许静默归到任何一边")
        self.assertEqual(u"unknown:None", tool.queue_state(None),
                         u"缺 status 也只是一种未知，不许当成 concluded")

    def test_ahead_counts_only_earlier_unconcluded_runs_of_the_same_workflow(self):
        tool = load_tool()
        runs = [
            run(5, u"queued", u"2026-10-25T11:59:00Z"),
            run(4, u"in_progress", u"2026-10-25T11:58:00Z"),
            run(3, u"queued", u"2026-10-25T11:55:00Z"),
            run(2, u"completed", u"2026-10-25T11:50:00Z", conclusion=u"failure"),
            run(1, u"queued", u"2026-10-25T11:40:00Z", workflow=u"UI"),
        ]
        rows = {r[u"databaseId"]: (state, waited, ahead) for r, state, waited, ahead in tool.queue_rows(runs, NOW)}
        self.assertEqual((u"queued", 60, 2), rows[5],
                         u"最新那一跑前面有两个未结案的 CI 跑（4、3）；已结案的 2 不与另一个 workflow 的 1 都不算")
        self.assertEqual((u"in_progress", 120, 1), rows[4], u"4 前面只剩 3")
        self.assertEqual((u"queued", 300, 0), rows[3], u"3 前面没有未结案的")
        self.assertEqual((u"concluded", 600, 0), rows[2], u"已结案的不排队")
        self.assertEqual((u"queued", 1200, 0), rows[1], u"UI 那条队里它前面没人")
        # 汇总按**全体**数（不按 workflow 过滤）：三跑 queued（5/3/1，其中 1 属于 UI 那条队），
        # 这与「同 workflow 前面」是两个问题 —— 汇总回答"这一段里有几跑在排队"，不是"CI 队里有几跑"。
        self.assertEqual({u"queued": 3, u"in_progress": 1, u"concluded": 1,
                          u"unknown": 0, u"unread_time": 0},
                         tool.queue_summary(tool.queue_rows(runs, NOW)))

    def test_an_unreadable_created_at_is_not_counted_as_order(self):
        tool = load_tool()
        runs = [
            run(9, u"queued", u"2026-10-25T11:59:00Z"),
            run(8, u"queued", u"not-a-time"),
        ]
        rows = {r[u"databaseId"]: (state, waited, ahead) for r, state, waited, ahead in tool.queue_rows(runs, NOW)}
        self.assertEqual((u"queued", -1, 0), rows[8],
                         u"时间读不出 ⇒ 已等=-1（不是 0）、也不许拿它当'排在前面'的证据")
        self.assertEqual(0, rows[9][2],
                         u"8 的时间读不出 ⇒ 不能证明它比 9 早 ⇒ 前面=0（做减法，不许猜）")
        summary = tool.queue_summary(tool.queue_rows(runs, NOW))
        self.assertEqual(1, summary[u"unread_time"], u"时间读不出要单独数得出来")

    def test_an_unknown_status_is_counted_separately(self):
        tool = load_tool()
        runs = [
            run(7, u"waiting", u"2026-10-25T11:59:00Z"),
            run(6, u"completed", u"2026-10-25T11:58:00Z", conclusion=u"success"),
        ]
        summary = tool.queue_summary(tool.queue_rows(runs, NOW))
        self.assertEqual(1, summary[u"unknown"])
        self.assertEqual(1, summary[u"concluded"])
        self.assertEqual((u"unknown:waiting", 60, 0), tool.queue_rows(runs, NOW)[0][1:],
                         u"未知状态那一跑也要给出已等，但它不许被算成排队前面的一员")

    def test_empty_input_is_all_zero_not_a_crash(self):
        tool = load_tool()
        self.assertEqual({u"queued": 0, u"in_progress": 0, u"concluded": 0,
                          u"unknown": 0, u"unread_time": 0},
                         tool.queue_summary(tool.queue_rows([], NOW)))

    def test_bad_limit_is_a_usage_error_without_touching_gh(self):
        """`--limit` 不是整数 ⇒ exit 2；这一格不许走到 gh（否则这条测试会依赖网络）。"""
        tool = load_tool()
        saved = sys.argv
        try:
            sys.argv = [u"ci_read.py", u"queue", u"--limit", u"ten"]
            self.assertEqual(2, tool.main())
        finally:
            sys.argv = saved


if __name__ == u"__main__":
    unittest.main()
