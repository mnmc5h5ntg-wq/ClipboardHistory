#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`commit_round_identity.py` 的真值表 + 端到端闸门（R564 / 637 的判据位那一半）。

为什么要有这条守卫（账里的原委）：R563 的 A 笔 `64d3192` 把 subject 前缀写成「R562 A：」，
而它自己的轮次身份行是 `第 562 轮 / Round 560`（= R563）。那一笔已经推出去 ⇒ 按 R534 的口径
不许 amend ⇒ 只能 forward：判**未推的那一批**，已推的历史不重判（所以不需要给它开豁免）。

三件事分开钉：
- 真值表：`judge()` 这个纯函数认得"一致 / 轮次不一致 / Round 不一致 / 身份缺失 / 无 R 前缀"五种形状。
  ⚠ 正对照用的是**仓库里真实存在过**的那一笔（`64d3192` 的形状），不是随手编的串。
- 端到端：拿真的 git 跑一遍，本轮这一批必须 0 条命中（这才是门）。
- 范围不许为空：`origin/main..HEAD` 为空时必须退化到 HEAD，**不许"零条也算通过"**
  （刀 M1464 钉的就是这一条 —— 把退化改成空列表，这里必须红）。
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import commit_round_identity as cri  # noqa: E402


class CommitRoundIdentityTests(unittest.TestCase):
    # ---- 真值表 ----
    def test_consistent_triple_passes(self):
        """正对照：R564 = 第 563 轮 / Round 561（本轮 ⓪ 笔的真实形状）。"""
        self.assertEqual(cri.judge("R564 ⓪ 开工节：基线全现读（第 563 轮 / Round 561）", ""), [])

    def test_identity_comes_from_subject_not_from_body(self):
        """正文里出现别的轮次号是**合法叙述**，不是这一笔的身份。

        这条是守卫自己抓到的自伤：第一版扫全文，于是本轮 A 笔正文里引用的
        `64d3192`（「它自己的身份行是 第 562 轮 / Round 560」）被判成"这一笔不一致"。
        仓库惯例是身份写在标题末尾的括号里 ⇒ 只认 subject。
        """
        self.assertEqual(cri.judge("R564 台账", "本轮引用：64d3192 的身份行是 第 562 轮 / Round 560"),
                         ["身份缺失"])
        self.assertEqual(cri.judge("R564 台账（第 563 轮 / Round 561）",
                                   "正文里另提 第 562 轮 / Round 560 那一笔"), [])

    def test_prefix_disagrees_with_round_number(self):
        """`64d3192` 那一族的形状：前缀写上一轮的号，身份行是本轮的。"""
        findings = cri.judge("R562 A：侧栏选中行那块黑补上另一通道的读数（第 562 轮 / Round 560）", "")
        self.assertIn("不一致:R562≠第562轮", findings)

    def test_prefix_disagrees_with_round_label(self):
        findings = cri.judge("R564 补记（第 563 轮 / Round 560）", "")
        self.assertIn("不一致:R564≠Round560", findings)

    def test_prefix_without_identity_is_red_not_silent(self):
        """前缀在、身份行不在 ⇒ 守卫无从判起，必须红（R488：有内容不足必须红）。"""
        self.assertEqual(cri.judge("R564 随手改个注释", ""), ["身份缺失"])

    def test_missing_prefix_is_red(self):
        self.assertEqual(cri.judge("台账：本轮七本落盘", "（第 563 轮 / Round 561）"), ["无R前缀"])

    def test_subject_identity_wins_over_body_quotation(self):
        """正对照的第二半：标题带身份 + 正文引用历史 ⇒ 必须 0 条命中。"""
        self.assertEqual(cri.judge("R564 A：守卫落地（第 563 轮 / Round 561）",
                                   "R563 的 A 笔 64d3192 前缀写成 R562，正文身份是 第 562 轮"), [])

    def test_prefix_boundary_is_not_greedy(self):
        """`R5640` 这种四位数不许被 `R564` 抢走前缀（负数形状的先验）。"""
        self.assertEqual(cri.judge("R5640 补记（第 5639 轮 / Round 5637）", ""), [])

    # ---- 范围不许为空（M1464 的靶）----
    def test_empty_unpushed_range_falls_back_to_head(self):
        """未推的为空时判 HEAD，绝不允许"一条都没判"被读成通过。"""
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        head = [ln for ln in out.splitlines() if ln.startswith("COMMIT_ROUND_IDENTITY ")]
        self.assertEqual(len(head), 1, out)
        read = dict(kv.split("=", 1) for kv in head[0].split()[1:])
        self.assertGreaterEqual(int(read["笔"]), 1,
                                "一条都没判到却被读成通过 ⇒ 范围退化那一半坏了：" + out)
        self.assertIn("COMMIT_ROUND_IDENTITY_RESULT=ok", out)

    def test_channel_values_contain_no_spaces(self):
        """通道行必须是「键=值」按空格切就能解析的形状。

        这一条是活的门，不是文档：R565 实测把退化说明写进 `范围=` 的值里（一个 ASCII 空格），
        上面那条 `dict(kv.split("=", 1) …)` 就报 `element #1 has length 1` ⇒ 守卫自己是绿的、
        判它的那一条却崩了。值里不许有空格 ⇒ 退化另开一格 `退化=`。
        """
        code, out = self.run_script()
        self.assertEqual(code, 0, out)
        head = [ln for ln in out.splitlines() if ln.startswith("COMMIT_ROUND_IDENTITY ")]
        self.assertEqual(len(head), 1, out)
        tokens = head[0].split()[1:]
        loose = [tk for tk in tokens if "=" not in tk]
        self.assertEqual(loose, [], "通道值里出现了空格 ⇒ 按空格切的解析会断：" + head[0])
        read = dict(tk.split("=", 1) for tk in tokens)
        self.assertIn(read["退化"], ("无", "未推的为空"), head[0])

    def run_script(self):
        env = {k: v for k, v in os.environ.items() if k != "SDKROOT"}
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "commit_round_identity.py")],
                              cwd=ROOT, capture_output=True, text=True, env=env, timeout=180)
        return proc.returncode, proc.stdout + proc.stderr

    # ---- 端到端：这一批必须一致（这才是门）----
    def test_current_batch_is_consistent(self):
        code, out = self.run_script()
        self.assertEqual(code, 0, "commit 轮次身份守卫红：\n" + out)
        self.assertIn("无R前缀=0 身份缺失=0 不一致=0", out)


if __name__ == "__main__":
    unittest.main()
