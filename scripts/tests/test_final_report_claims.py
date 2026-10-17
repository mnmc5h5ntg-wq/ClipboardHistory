#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`AGENT_FINAL_REPORT.md` §9.3 那几句"仍未收口"的话，要能被机器复查（R143 / BACKLOG 181）。

为什么现在补这一格：R143 的台账复审查出这份报告**连着三轮**与台账相反，而它没有任何守卫 ——
§9.3 第 3 条写着「新加一个有作用的动效……最近的一次是 R126」（R141 之后为假）、
第 2 条写着「还有 102 格未判」（闸门打的是 101）、第 5 条写着「这两条都还没有各自的自动化守卫」
（两半 R137 / R139 就有了）。三句都是**能从仓库里算出来**的，却由我手抄，抄错了没人响。

判法：三句各绑一个读数，绑不上就点名。三格正对照（在内存里伪造，不碰仓库）证明每条都有牙 ——
只判"存在"不判"合不合"的守卫，等于没有守卫（R102 那一族）。
"""
import io
import json
import os
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REPORT = REPO / "AGENT_FINAL_REPORT.md"
LEDGER = REPO / "docs" / "motion_surface_ledger.json"
GUARDS = ["scripts/tests/test_ledger_generator_output.py", "scripts/tests/test_round_batch_consistency.py"]

UNCLEARED = re.compile(u"清账表还有\\s*(\\d+)\\s*格未判")
NO_NEW_MOTION = re.compile(u"这一件仍未发生")
NO_GUARD = re.compile(u"都还没有各自的自动化守卫")


def uncleared_cells(data):
    """未清账 = 表面 × 状态 − 已清账行数。与闸门同一颗尺（`MOTION_LEDGER 未清账=`）。"""
    cells = len(data.get("surfaces") or []) * len(data.get("states") or [])
    cleared = data.get("cleared_verdicts") or []
    done = len([r for r in (data.get("rows") or []) if (r.get("verdict") or "") in cleared])
    return cells - done


def stale_claims(report_text, data, guard_files_present):
    """返回 [(代码, 说明)]；空 = 这三句都跟得上仓库。"""
    problems = []
    section = report_text.split(u"### 9.3", 1)
    body = u""
    if len(section) > 1:
        # 只取 §9.3 自己那一节：后面紧跟的 `### 9.x` / `## ...` 不算它的话
        body = section[1].split(u"\n### ", 1)[0].split(u"\n## ", 1)[0]

    found = UNCLEARED.findall(body)
    if not found:
        problems.append(("UNCLEARED_CLAIM_ABSENT", u"§9.3 里找不到「清账表还有 NN 格未判」这句 ⇒ 形状变了，这一格没判"))
    else:
        claimed = int(found[0])
        actual = uncleared_cells(data)
        if claimed != actual:
            problems.append(("UNCLEARED_CLAIM_STALE",
                             u"§9.3 写 %d 格未判，而表算出来是 %d ⇒ 报告停在旧读数" % (claimed, actual)))

    added = len([r for r in (data.get("rows") or []) if (r.get("verdict") or "") == "added"])
    if added and NO_NEW_MOTION.search(body):
        problems.append(("NEW_MOTION_CLAIM_STALE",
                         u"清账表已有 %d 行 verdict=added，§9.3 却还写着「这一件仍未发生」" % added))

    present = [g for g in guard_files_present if g]
    if len(present) == len(GUARDS) and NO_GUARD.search(body):
        problems.append(("GUARD_CLAIM_STALE",
                         u"两份守卫文件都在仓库里，§9.3 第 5 条却还写「都还没有各自的自动化守卫」"))
    return problems


class FinalReportClaimsTests(unittest.TestCase):

    def read(self):
        with io.open(REPORT, encoding="utf-8") as handle:
            return handle.read()

    def ledger(self):
        with io.open(LEDGER, encoding="utf-8") as handle:
            return json.loads(handle.read())

    def test_the_three_claims_currently_agree_with_the_repository(self):
        present = [os.path.exists(REPO / g) for g in GUARDS]
        self.assertEqual([True, True], present, u"守卫文件本身不见了 ⇒ 这一族的判据无从谈起")
        problems = stale_claims(self.read(), self.ledger(), present)
        self.assertEqual([], [(c, m) for c, m in problems], u"§9.3 与仓库不一致：%s" % problems)

    def test_a_stale_uncleared_count_is_named(self):
        data = self.ledger()
        text = self.read()
        actual = uncleared_cells(data)
        forged = UNCLEARED.sub(u"清账表还有 %d 格未判" % (actual + 1), text, count=1)
        codes = [c for c, _ in stale_claims(forged, data, [True, True])]
        self.assertIn("UNCLEARED_CLAIM_STALE", codes, u"改一个数它不响 ⇒ 这一格是假的")
        self.assertEqual([], [c for c, _ in stale_claims(text, data, [True, True])],
                         u"正对照必须只由伪造触发：原文自己就该是干净的")

    def test_a_new_motion_makes_the_still_none_claim_red(self):
        data = self.ledger()
        text = self.read()
        self.assertGreater(len([r for r in data["rows"] if r.get("verdict") == "added"]), 0,
                           u"表里没有 added 行 ⇒ 这一格无从伪造（先造出证据再谈守卫）")
        forged = text.replace(u"已经在 R141 还上", u"仍未发生 —— 判据清单与清账表都在，但"
                                                  u"「新加一个有作用的动效」这一件仍未发生", 1)
        self.assertNotEqual(text, forged, u"锚点漂了：找不到那句关于 173 的话")
        codes = [c for c, _ in stale_claims(forged, data, [True, True])]
        self.assertIn("NEW_MOTION_CLAIM_STALE", codes)

    def test_existing_guards_make_the_no_guard_claim_red(self):
        data = self.ledger()
        text = self.read()
        forged = text.replace(u"**R143 更正这一条自己的过期**",
                              u"这两条都还没有各自的自动化守卫 —— 挂着，别当成已解决。\n**R143 更正这一条自己的过期**", 1)
        self.assertNotEqual(text, forged, u"锚点漂了：找不到第 5 条")
        codes = [c for c, _ in stale_claims(forged, data, [True, True])]
        self.assertIn("GUARD_CLAIM_STALE", codes)


if __name__ == "__main__":
    unittest.main()
