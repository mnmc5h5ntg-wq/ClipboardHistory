#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一轮的台账必须**同时**出现在三本账里（R139 / U-452 的那半道守卫）。

为什么需要它：本轮之前我两次撞上同一个形状 —— 一批台账补丁里有一处锚点命中 0 次，
其余四处落了盘，于是台账停在"半批已写"。R138 那次是 CHANGELOG 整条没落上，
而我是在写完 U-452 的下一秒又犯了一遍，当时只靠人眼发现。

判法：从 `AGENT_STATE.md` 的"最后更新"行读出本轮的 R 号，然后要求**最近三轮**
每一轮都在三本账里各自有标题：
  AGENT_UI_AUDIT.md        `^## 第 N 轮（R<r>`
  AGENT_VISUAL_ITERATION.md `^## Round <r> · `
  CHANGELOG.md              `^### …R<r>`
查的是**标题行**（R143 起）：原来只查文件里有没有 `R<r>` 这串字，于是正文里提一句旧轮次就能喂饱它，而 M655（删掉 CHANGELOG 本轮标题）实测 PASSED。
只查标题存在，不查内容 —— 内容对不对仍由别的判据管。
名册下限（最近三轮）是防它退化成恒真：只查一轮时，那一轮恰好没写也不会红。
"""
import io
import os
import re
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
STATE = os.path.join(REPO, "AGENT_STATE.md")
# R143 收紧：这三条原来只是"文件里任何地方出现 R<r>"，而本文件要查的是**标题**。
# 散文里提一句旧轮次就能喂饱它 —— 实测 M655（删掉 CHANGELOG 本轮那一行标题）在收紧前是 PASSED，
# 因为正文里还留着 `R142`。判据要读结构，不读散文（与"守卫要读字段不能读散文"同族）。
# 三本账的标题形状是本轮实测的（`grep -n '^#'` 各账），不是设想：
#   AGENT_UI_AUDIT.md         `^## 第 N 轮（R<r> · 日期）：…`
#   AGENT_VISUAL_ITERATION.md `^## Round <r> · …`
#   CHANGELOG.md              `^### …（R<r> / U-… · 产品 …）`
LEDGERS = {
    "AGENT_UI_AUDIT.md": u"^## 第 \\d+ 轮（R%d",
    "AGENT_VISUAL_ITERATION.md": u"^## Round %d · ",
    "CHANGELOG.md": u"^### .*（R%d / ",
}
LOOKBACK = 3


def current_round():
    text = open(STATE, encoding="utf-8").read()
    m = re.search(u"最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮", text)
    assert m, "读不到 AGENT_STATE 的『最后更新』轮次行 ⇒ 这条判据会空跑"
    return int(m.group(1)), int(m.group(2))


class RoundBatchTests(unittest.TestCase):

    def test_the_state_round_number_and_the_audit_round_agree(self):
        r, n = current_round()
        self.assertEqual(r + 2, n,
                         "STATE 自报 R%d / 第 %d 轮，而这套映射（第 N 轮 = R + 2）本轮变了 ⇒ 先确认是谁漂了" % (r, n))

    def test_the_last_three_rounds_are_written_in_all_three_ledgers(self):
        r, _ = current_round()
        missing = []
        for back in range(LOOKBACK):
            this = r - back
            for name, fmt in LEDGERS.items():
                path = os.path.join(REPO, name)
                if not os.path.exists(path):
                    missing.append("%s（文件缺失）" % name)
                    continue
                text = open(path, encoding="utf-8").read()
                if back == 0:
                    self.assertTrue(re.search(fmt % this, text, re.M),
                                    "本轮（R%d）在 %s 里没有**标题行** ⇒ 半批已写" % (this, name))
                if not re.search(fmt % this, text, re.M):
                    missing.append("R%d 缺于 %s" % (this, name))
        self.assertEqual([], missing,
                         "有轮次在三本账里缺一本（这就是『锚点命中 0 次而其余落了盘』的可检查形式）")

    def source_lookback(self):
        """从**源码文本**里读窗口值，而不是用模块全局。

        为什么（U-462）：本轮实测到磁盘上 `LOOKBACK = 3`、清过 `__pycache__`、
        而 `unittest` 里读到的模块全局是 1 —— 成因没定位。
        R154 追因（U-516 / U-517，结掉这里那句「成因没定位」）：同一个成因是**字节码缓存在仓库外** ——
        macOS 把 .pyc 写到 `~/Library/Caches/com.apple.python/<绝对路径>/<模块>.cpython-<ver>.pcy`（用 `module.__cached__` 能打印出来），
        失效判据是「源码 mtime（整秒）+ 字节数」。所以「清过 `__pycache__` 而全局还是旧值」不是玄学，是**清错了地方**；
        而当一次改动**长度不变**、又落在同一秒内（我这轮的变异刀是 `return 1`→`return 0`），缓存自认新鲜 ⇒ 执行的是上一版。
        规矩：改过 `.py` 的对照跑一律带 `PYTHONDONTWRITEBYTECODE=1`；判据红而源码看着对，先问「这台机器执行的是哪一份字节码」。
        与其继续用一个会被不知名写者改掉的进程内全局当判据，不如把这条自检改成
        读"文件里声明的窗口"：它测的正是我想测的那件事（这张表声明的窗口够不够大），
        而且不受导入期状态影响。
        """
        text = io.open(os.path.abspath(__file__), encoding="utf-8").read()
        m = re.search(r"^LOOKBACK = (\d+)", text, re.M)
        self.assertIsNotNone(m, "读不到 LOOKBACK 的声明 ⇒ 这条自检会空跑")
        return int(m.group(1))

    def test_the_lookback_window_is_not_empty(self):
        """正对照的反面：如果最近三轮恰好都只写在一本账里，上面那条也会绿。
        所以这里要求 STATE 自报的轮次确实落在被检查的窗口内，且窗口 >= 2。"""
        declared = self.source_lookback()
        self.assertGreaterEqual(declared, 2, "窗口小于 2 ⇒ 这条判据只看一轮，半批已写会漏（读到 %d）" % declared)
        r, _ = current_round()
        text = open(os.path.join(REPO, "AGENT_UI_AUDIT.md"), encoding="utf-8").read()
        found = [int(x) for x in re.findall(u"^## 第 \\d+ 轮（R(\\d+)", text, re.M)]
        self.assertTrue(found, "审计台账里一个轮次标题都没认出 ⇒ 正则漂了")
        self.assertIn(r, found[:LOOKBACK + 1],
                      "STATE 说现在是 R%d，但审计台账最近的标题里没有它：%s" % (r, found[:LOOKBACK + 1]))


if __name__ == "__main__":
    unittest.main()
