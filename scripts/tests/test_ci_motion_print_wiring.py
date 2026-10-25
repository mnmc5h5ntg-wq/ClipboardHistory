#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R359 / BACKLOG 431：动效那一步必须把**必印族**打出来，且不许被 `head -120` 截掉。

来历（run 40195884862，2026-10-25）：那跑是绿的、`MOTION_LINES=328`，而 R355 新加的
`MOTION_REDUCE_SOURCES` 一行都没有 —— 不是没打印，是它在排在后面的测试里，被
`grep -E "^MOTION_" | head -120` 截掉了。读数族必须接进**它被打印的那一步**；
这一支把"必印族"写成名单，并只认**专用 grep**（出现在一行含 `grep` 的文本里）。
"""
import io
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WORKFLOW = REPO / u".github" / u"workflows" / u"ci.yml"
STEP_NAME = u"- name: Motion filmstrip (report-only)"

# 判据：这四族是"结论/缺席/通道身份"级别的读数，不能在日志里被截断或消失。
# 加新族时把它写进来 —— 名单本身也要有一条会红的守（下一条测试的正对照证明它会响）。
MUST_PRINT = (
    u"MOTION_SUMMARY",
    u"MOTION_RESOLVE_SUMMARY",
    u"MOTION_NOT_RUN=",
    u"MOTION_REDUCE_SOURCES",
)


def step_body(workflow_text, name=STEP_NAME):
    start = workflow_text.find(name)
    if start < 0:
        return None
    after = workflow_text[start + len(name):]
    # 下一个同级步骤（同一缩进 6 空格 + "- name:"）；找不到就吃到文件尾。
    nxt = re.search(u"(?m)^      - name:", after)
    return after[:nxt.start()] if nxt else after


def missing_prints(step, patterns=MUST_PRINT):
    """pattern 必须出现在**含 grep 的那一行**里（裸 echo 不算 —— 那是把名字念一遍）。"""
    grep_lines = [line for line in (step or u"").splitlines() if u"grep" in line]
    out = []
    for pattern in patterns:
        if not any(pattern in line for line in grep_lines):
            out.append(pattern)
    return out


class MotionPrintWiringTests(unittest.TestCase):

    def test_every_required_family_has_its_own_grep_in_the_filmstrip_step(self):
        text = io.open(str(WORKFLOW), encoding=u"utf-8").read()
        step = step_body(text)
        self.assertIsNotNone(step, u"找不到 `%s` ⇒ 这一格没有对象（CI 形状漂了）" % STEP_NAME)
        self.assertEqual([], missing_prints(step),
                         u"这些必印族在动效那一步里没有专用 grep ⇒ runner 日志里会看不见：%s"
                         % (missing_prints(step),))
        # 正对照的另一半：`head -120` 必须仍在（它是"先全打再截"的那条路），
        # 而必印族不靠它 —— 两条同时存在才是"看得见 + 不爆日志"。
        self.assertIn(u"head -120", step, u"全量打印那一路不见了 ⇒ 先修那条，再谈必印族")

    def test_the_guard_names_a_missing_family_on_a_synthetic_step(self):
        synthetic = u"""
          summary=$(grep -m1 'MOTION_SUMMARY' /tmp/motion.log || true)
          grep -E "MOTION_NOT_RUN=" /tmp/motion.log || true
          grep -E "^MOTION_" /tmp/motion.log | head -120 || true
        """
        got = missing_prints(synthetic)
        self.assertEqual([u"MOTION_RESOLVE_SUMMARY", u"MOTION_REDUCE_SOURCES"], got,
                         u"正对照没点名缺的两族：%s" % (got,))

    def test_a_bare_echo_of_the_name_does_not_count_as_printing(self):
        synthetic = u'          echo "MOTION_REDUCE_SOURCES"\n'
        self.assertIn(u"MOTION_REDUCE_SOURCES", missing_prints(synthetic),
                      u"把族名 echo 一遍就当成打印过 ⇒ 这条守卫会被一行文案喂饱")

    def test_the_patterns_are_valid_regexes(self):
        for pattern in MUST_PRINT:
            re.compile(pattern)     # 编不过就抛，不必断言


if __name__ == u"__main__":
    unittest.main()
