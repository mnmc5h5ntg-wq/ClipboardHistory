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
    "AGENT_UI_AUDIT.md": [u"^## 第 \\d+ 轮（R%d"],
    # ITERATION 那一本原来只认 `^## Round <R号> · `，这等于**假设 Round 号 == R 号**。
    # R235 实测这个假设已经断了：活账的标题是 `## Round 232 · …（2026-10-20 / R235 / 第 234 轮 / …）`
    # —— 那本账自己的编号比脚本臂慢 3（历史节 229/230/231 的标题里根本没有 R 标签，不能反向推）。
    # 所以这里收两种形状：① 旧的同名形状（历史节仍可查）；② 标题行里带本轮 R 标签（新写法）。
    # 两种都只准命中在**标题行**上，散文里提一句仍喂不饱它。
    "AGENT_VISUAL_ITERATION.md": [u"^## Round %d · ", u"^## Round \\d+ · .*\\bR%d\\b"],
    "CHANGELOG.md": [u"^### .*（R%d / "],
}
LOOKBACK = 3

# ITERATION 那一本自己的编号（Round 号）与脚本臂的 R 号**不同源**：本轮实测
# `第 234 轮（R235 / Round 232` ⇒ Round 号 = R 号 - 3，而更早的节差 2（R230 那节对应 Round 230）。
# 与其再钉一个常数（那正是 `第 N 轮 = R + 2` 那根钉子本轮断掉的原因），这里只登记**已经逐字核对过标题**的对应：
# 每条都要能在文件里查到那一枚 `^## Round <别名> · ` 标题行才算数（指不到东西 ⇒ 判缺、红）。
ITERATION_ROUND_ALIAS = {
    234: 231,  # `## Round 231 · 看图量出"渲染档里表格穿的是代码那件灰底"…（… mutate_r234）`
    235: 232,  # `## Round 232 · …（2026-10-20 / R235 / 第 234 轮 / U-748 U-749 U-750）`
}


def patterns_for(name, round_no):
    """某本账对"第 <round_no> 轮有没有标题行"的全部可接受形状（已代入编号的具体正则）。"""
    out = [f % round_no for f in LEDGERS[name]]
    if name == "AGENT_VISUAL_ITERATION.md" and round_no in ITERATION_ROUND_ALIAS:
        out.append(u"^## Round %d · " % ITERATION_ROUND_ALIAS[round_no])
    return out

# R188 / 新开 211：**显式申报**过的「只动 BACKLOG」笔次。为什么不顺手给 186/187 补两行桩标题：
# 桩标题会让「半批已写」这一格永远查不出来（守卫被散文喂饱）；而申报是**可查的** ——
# `test_round_batch_declaration.py` 钉住三件事：申报必须带理由、申报的那轮必须确实缺一本账、当前轮永远不许被豁免。
# 删掉这张表 ⇒ 186/187 又会让 STATE 轮换红三格（红回来，不是绿过去）。
SINGLE_LEDGER_ROUNDS = {
    186: "a90e380 只追加 BACKLOG 210 追记 2（绑定链查到底），三本账没写",
    187: "2720e72 + 81105b0 只追加 BACKLOG 210 追记 3/4（病根改判与钉死），三本账没写；"
         "该读数已在 R188（8b90efe）撤回 ⇒ 连内容也作废了",
    197: "f3b3933 只追加 BACKLOG 221（热图梯子『空→最低档』那条质询的开单，带 1.05 与 28/255 两个读数），"
         "UI_AUDIT 与 CHANGELOG 到今天仍没有它的标题行；ITERATION 那一节由 R198 补落"
         "（`patch_r197_backfill.py`，动机是 `test_curve_gaps` 当场打出 GAPS=[197] —— 曲线不认申报通道，少一轮就把均值算错）",
    233: "纯文本收账笔（把『没接新通道时旧的红照旧红』那一格改成按机器登记的行推导）。"
         "本轮实测的形状：CHANGELOG 有它的标题行（`### 判据：纯文本那一格也不再拿本机的能力当另一台机器的地板（R233 / …）`），"
         "而 AGENT_UI_AUDIT 与 AGENT_VISUAL_ITERATION **没有**以 R233 为标签的标题行 —— "
         "那一批的内容并进了相邻节（第 233 轮那节的标签是 R234）。"
         "这里只登记『三本账不齐』这个事实；它怎么归的正文我没逐字核对，不替它辩护。",
}


def current_round():
    text = open(STATE, encoding="utf-8").read()
    m = re.search(u"最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮", text)
    assert m, "读不到 AGENT_STATE 的『最后更新』轮次行 ⇒ 这条判据会空跑"
    return int(m.group(1)), int(m.group(2))


class RoundBatchTests(unittest.TestCase):

    def audit_round_for(self, r):
        """从**审计台账自己的标题行**读 R<r> 是第几轮（读不到 ⇒ None）。"""
        text = open(os.path.join(REPO, "AGENT_UI_AUDIT.md"), encoding="utf-8").read()
        m = re.search(u"^## 第 (\\d+) 轮（R%d\\b" % r, text, re.M)
        return int(m.group(1)) if m else None

    def test_the_state_round_number_and_the_audit_round_agree(self):
        """STATE 自报的 (R, 第 N 轮) 必须与审计台账那一节的标题**逐字相符**。

        为什么改掉原来的硬映射（R188 起写死 `第 N 轮 = R + 2`）：那条断言把一次**漂移**钉成了常数。
        本轮实测活账的形状是 `第 232 轮（R230` / `第 233 轮（R234` / `第 234 轮（R235` ——
        中间那三个补记臂（R231 补记 / R232 / R233）没各自开新节，所以 2 的间距在 R234 就断了；
        于是 STATE 写**真值**（R235 = 第 234 轮）反而被这根常数判成红。
        新判法读的是审计台账这个**字段**，不再猜漂移量：漂移多少都照实对账，
        而 STATE 与台账任一边漂了仍会红。正对照**本轮是手工一次性做的、没有入库脚本**
        （别再假装 `mutate_r235_state_pair` 存在）：把 AGENT_STATE『最后更新』行的
        `第 234 轮` 改成 `第 231 轮` 后单跑这一格 ⇒ 实测红
        `AssertionError: 234 != 231 : STATE 说 R235 是第 231 轮，而 AGENT_UI_AUDIT 的标题写第 234 轮`，
        随后 `git checkout -- AGENT_STATE.md` 还原（改动文件数 0）。
        """
        r, n = current_round()
        declared = self.audit_round_for(r)
        self.assertIsNotNone(
            declared,
            "审计台账里没有『## 第 N 轮（R%d』这一节标题 ⇒ STATE 自报的 (R%d, 第%d) 无据可对" % (r, r, n))
        self.assertEqual(declared, n,
                         "STATE 说 R%d 是第 %d 轮，而 AGENT_UI_AUDIT 的标题写第 %d 轮 ⇒ 两边有一边漂了" % (r, n, declared))

    def test_the_last_three_rounds_are_written_in_all_three_ledgers(self):
        r, _ = current_round()
        missing = []
        for back in range(LOOKBACK):
            this = r - back
            # 当前轮（back == 0）永远不许被豁免：豁免只给「已经落盘、且明说只动了一本账」的历史笔次
            if back > 0 and this in SINGLE_LEDGER_ROUNDS:
                continue
            for name, fmts in LEDGERS.items():
                path = os.path.join(REPO, name)
                if not os.path.exists(path):
                    missing.append("%s（文件缺失）" % name)
                    continue
                text = open(path, encoding="utf-8").read()
                hit = any(re.search(p, text, re.M) for p in patterns_for(name, this))
                if back == 0:
                    self.assertTrue(hit,
                                    "本轮（R%d）在 %s 里没有**标题行** ⇒ 半批已写" % (this, name))
                if not hit:
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
