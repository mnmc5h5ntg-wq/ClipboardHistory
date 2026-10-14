#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHANGELOG 自己的形状（R60）。

为什么要有这一条：R59 往 `## [Unreleased]` 下面插正文时，把整段（含那行标题）插了一遍，
于是文件顶上出现**两个** `## [Unreleased]` —— 没有任何检查发现，脚本测试 107 格全绿。
台账是要给人逐字读的（发布说明也从这里来），标题重复不是排版问题，是"同一节被分成两半"。

这一条只判**一件**事，而它就是本轮真的踩过的那个坑：
`## [Unreleased]` 必须有且只有一个。R59 往这一节里插正文时，把整段（含那行标题）插了一遍，
于是文件顶上出现两个同名标题，而脚本测试 107 格全绿 —— 台账是要给人逐字读的，
标题重复意味着"同一版本被分成两半"，读的人会以为后面那截是另一个版本。

**写过又被删掉的两条**（都记在这里，因为它们是"守卫拿标准去判约定"的样子）：
① "小节类型必须是 Keep a Changelog 那六种" —— 这个文件在 Unreleased 里已经在用
   `### Tests`、`### Release`、`### 判断（R…）`、`### 量出来但没修（R22）`，两次跑这条守卫
   就红了两次，红的是守卫自己；
② "同一类型不许出现两次" —— 每轮各写一节（两个 `### Fixed`）就是这个文件的约定。
要管住小节命名是另一件事，得先改约定再立规矩，不许反过来拿规矩去追认。
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
# Keep a Changelog 的六种，加上这个文件历史上已经在用的两种：`Tests`（测试侧改动，出现 3 次）
# 与 `Release`（发版条目，5 次）。守卫记的是**这个仓库实际在用的约定**，
# 不是拿标准去把约定判成坏 —— 那正是本轮第一次跑这条守卫时自己撞到的。
KINDS = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security", "Tests", "Release")


def unreleased_body(text):
    """取 `## [Unreleased]` 到下一个 `## ` 之间的正文。"""
    start = text.index("## [Unreleased]")
    rest = text[start + len("## [Unreleased]"):]
    nxt = rest.find("\n## ")
    return rest if nxt < 0 else rest[:nxt]


class ChangelogShapeTest(unittest.TestCase):
    def setUp(self):
        with open(CHANGELOG, encoding="utf-8") as handle:
            self.text = handle.read()

    def test_exactly_one_unreleased_heading(self):
        n = len(re.findall(r"^## \[Unreleased\]$", self.text, re.MULTILINE))
        self.assertEqual(n, 1,
                         "`## [Unreleased]` 出现 %d 次 ⇒ 有一轮的正文被插成了两节（R59 就这么坏过一次）" % n)

if __name__ == "__main__":
    unittest.main()
