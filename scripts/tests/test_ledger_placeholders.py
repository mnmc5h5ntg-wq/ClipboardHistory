#!/usr/bin/env python3
"""台账里不许有未渲染的占位符（R258 现读发现的历史缺陷）。

为什么这一卷存在：R258 写台账时给生成器加了一条"渲染后仍有 @@ 就拒绝写盘"的自检，
它第一次跑就把我打红（我把星形符号的灰阶当成了底）。顺手拿同一条尺扫全库，
结果在**已经提交的历史台账**里读到 6 处未渲染占位符 —— `@@ROWS@@` / `@@CELLS@@` /
`@@OPEN@@` / `@@BATT@@`，分布在 AGENT_UI_AUDIT / AGENT_STATE / CHANGELOG 三本里。
那些行长得和真读数一模一样（"清账表 @@ROWS@@ 行 / @@CELLS@@ 格"），也就是说：
**台账里曾经把"没落数"当成"落过数"推上线，而且没有任何守卫会红。**

规矩：六本台账里不许出现 `@@大写@@` 形式的占位符。缺席的数要写成中文的"未落数 + 成因"，
不许留一个看起来像字段的空壳（R89/R90 那一族：读不到要写成有名字、能红的形态）。

不覆盖管线：这一卷只扫台账文本，不判产品；正对照在下面第一格（尺自己也要能被打红）。
"""
import io
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOOKS = ["AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
         "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md"]

PAT = re.compile(r"@@[A-Za-z0-9_]+@@")


def find_placeholders(text):
    """返回 (行号, 整行) 列表 —— 尺只有一处定义，正对照与真产物走同一条。"""
    return [(i + 1, line) for i, line in enumerate(text.splitlines()) if PAT.search(line)]


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


class LedgerPlaceholderTests(unittest.TestCase):
    def test_the_ruler_itself_catches_a_planted_placeholder(self):
        # 正对照：不许造"永远绿"的守卫。同一把尺，坏样本必须被它自己抓出来，
        # 而且**按行报**（第一版我把它写成"按颗报"，期望 2 实际 1 ⇒ 自己红在自己身上）。
        hits = find_placeholders("清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 电池 Ran @@BATT@@\n正常一行\n未清账 @@OPEN@@ 格\n")
        self.assertEqual(2, len(hits), "尺抓不到种下去的两行占位符 ⇒ 下面那格恒真")
        self.assertEqual([1, 3], [ln for ln, _ in hits], "行号不对 ⇒ 报出来的位置不可复查")
        self.assertIn("@@ROWS@@", hits[0][1])
        self.assertIn("@@BATT@@", hits[0][1])
        # 反向：正常文本不许误报（否则守卫会被"太吵"绕开）
        self.assertEqual([], find_placeholders("Ran 459 tests / OK (skipped=4) / U-834…U-840"))

    def test_all_six_books_exist_and_are_non_empty(self):
        for name in BOOKS:
            path = os.path.join(ROOT, name)
            self.assertTrue(os.path.exists(path), "台账不在盘上：" + name)
            self.assertGreater(len(read(path).strip()), 200, name + " 空得可疑")

    def test_no_unrendered_placeholder_survives_in_the_ledgers(self):
        bad = []
        for name in BOOKS:
            for ln, line in find_placeholders(read(os.path.join(ROOT, name))):
                bad.append("%s:%d %s" % (name, ln, line.strip()[:120]))
        self.assertEqual([], bad,
                         "台账里有未渲染的占位符（看起来像字段、其实是没落数）：\n  " + "\n  ".join(bad))


if __name__ == "__main__":
    unittest.main()
