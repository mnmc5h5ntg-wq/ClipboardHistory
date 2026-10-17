#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""台账生成器与已提交表之间的对账（R137 / U-450、U-452 的自动守卫）。

为什么单独一支（§9.3 里挂着的那条"还没有自动守卫"）：
R134 与 R136 各撞过一次同形状的坑 —— 生成器抛了异常（SyntaxError / NameError），
JSON 停在上一版，而闸门读的是那份**旧** JSON 并打印 `RESULT=ok`。
两句合起来读就是"表没问题"，真相是"新数据一行都没进去"。
当时唯一的证人是人眼看行数（52 → 60）。这一支把它变成会红的断言。

两条判据各自的方向：
  ① 生成器必须**跑得完**（exit 0），且它写出来的东西与仓库里那份**逐字相同**
     （不同 ⇒ 有人改了生成器没重跑，或改了 JSON 没回写生成器 —— 两边都会漂）
  ② 表里引用的每个 `BACKLOG <n>` 必须在 `AGENT_BACKLOG.md` 里真有一个 `<n>.` 条目
     （悬空引用 = 半批已写的典型形状，U-452）
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
GENERATOR = os.path.join(REPO, ".scratch", "motion-audit-2", "make_surface_ledger.py")
COMMITTED = os.path.join(REPO, "docs", "motion_surface_ledger.json")
BACKLOG = os.path.join(REPO, "AGENT_BACKLOG.md")


def run_generator_in_sandbox():
    """在临时目录里跑生成器：它写的是相对路径 `docs/...`，所以沙箱里必须有同名目录。

    绝不在仓库里跑 —— 那会让一支"检查"顺手改掉被检查的东西（R91/R92 那一族的共享路径教训）。
    """
    box = tempfile.mkdtemp(prefix="ledger-guard-")
    try:
        os.makedirs(os.path.join(box, "docs"))
        shutil.copy2(GENERATOR, os.path.join(box, "gen.py"))
        proc = subprocess.run([sys.executable, "gen.py"], cwd=box,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              env=dict(os.environ, PYTHONUTF8="1"))
        out = os.path.join(box, "docs", "motion_surface_ledger.json")
        produced = None
        if os.path.exists(out):
            produced = io.open(out, encoding="utf-8").read()
        return proc.returncode, proc.stdout.decode("utf-8", "replace"), produced
    finally:
        shutil.rmtree(box, ignore_errors=True)


class GeneratorAgreementTests(unittest.TestCase):

    def test_the_generator_runs_clean_in_a_sandbox(self):
        code, text, produced = run_generator_in_sandbox()
        self.assertEqual(0, code,
                         "生成器没跑完（exit %d）：台账停在上一版，闸门会拿旧数据报 ok（U-450）\n%s"
                         % (code, text[-600:]))
        self.assertIsNotNone(produced, "生成器 exit 0 却没写出文件 ⇒ 路径假设漂了")

    def test_the_committed_table_is_the_generators_own_output(self):
        """逐字比对：改了生成器就要重跑，改了 JSON 就要回写生成器。"""
        code, text, produced = run_generator_in_sandbox()
        self.assertEqual(0, code, "生成器跑不完，无从比对：%s" % text[-400:])
        committed = io.open(COMMITTED, encoding="utf-8").read()
        self.assertEqual(produced, committed,
                         "已提交的表与生成器的输出不一致 ⇒ 有一边是手改的（半批已写的形状）")

    def test_the_printed_row_count_is_the_committed_one(self):
        """结论行要打在能力闸门之前，也要与产物自己报的数一致（不许手抄）。"""
        code, text, produced = run_generator_in_sandbox()
        self.assertEqual(0, code, text[-400:])
        printed = re.search(r"MOTION_LEDGER_ROWS=(\d+)", text or "")
        self.assertIsNotNone(printed, "生成器没打印行数 ⇒ 这一格无从对账，算红")
        data = json.loads(io.open(COMMITTED, encoding="utf-8").read())
        self.assertEqual(int(printed.group(1)), len(data["rows"]),
                         "打印的行数与已提交表的行数不一致")


class DanglingReferenceTests(unittest.TestCase):

    def test_prose_references_to_backlog_items_resolve_too(self):
        """散文里的 `BACKLOG <n>` 也要能落到条目上 —— 只查表里的引用是半个盲区（U-454）。

        本轮实测到的形状：`AGENT_BACKLOG.md` 里 172 那条的**条目号前缀被某次插入吃掉了**，
        于是文件里所有"172"的引用都指向一个扫描器看不见的条目。
        这条判据把同一把尺伸到正文台账上；它查的是"号存不存在"，不是"结论对不对"。
        """
        item_numbers = set()
        for line in io.open(BACKLOG, encoding="utf-8"):
            m = re.match(r"^(?:\*\*)?(\d{2,3})\.", line)
            if m:
                item_numbers.add(int(m.group(1)))
        self.assertGreater(len(item_numbers), 100, "条目名册读不出来，这条判据会恒真")
        dangling = []
        for name in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "CHANGELOG.md",
                     "AGENT_STATE.md", "AGENT_FINAL_REPORT.md", "AGENT_DECISIONS.md"):
            path = os.path.join(REPO, name)
            if not os.path.exists(path):
                continue
            text = io.open(path, encoding="utf-8").read()
            for n in set(int(x) for x in re.findall(r"BACKLOG\s*(\d{2,3})", text)):
                if n not in item_numbers:
                    dangling.append("%s → BACKLOG %d" % (name, n))
        self.assertEqual([], sorted(dangling),
                         "正文引用了扫描器认不出的条目号（要么号被吃掉，要么从没开过）")

    def test_every_backlog_reference_in_the_ledger_names_a_real_item(self):
        """表里写 `BACKLOG 58` 就必须真有条目 58；悬空引用多半是"半批已写"留下的。"""
        # 条目行有**两种形状**（R156 之后我改成用粗体起头）：
        #   `155. **运动地板那把尺…`  与  `**166.（R119 结案…）…`
        # 只认前一种会让 20 多个条目"不存在"，于是这条守卫会把真引用报成悬空 ——
        # 与 R94 那一课同形（"定义行正则要按台账实际形状写，只认 ### 会漏 115 条"，U-453）。
        item_numbers = set()
        for line in io.open(BACKLOG, encoding="utf-8"):
            m = re.match(r"^(?:\*\*)?(\d{2,3})\.", line)
            if m:
                item_numbers.add(m.group(1))
        self.assertGreater(len(item_numbers), 100,
                           "只认出 %d 个条目 ⇒ 条目行的形状变了，这条判据会恒真" % len(item_numbers))
        data = json.loads(io.open(COMMITTED, encoding="utf-8").read())
        dangling = []
        for row in data["rows"]:
            text = (row.get("reason", "") or "") + " " + (row.get("evidence", "") or "")
            for n in re.findall(r"BACKLOG\s*(\d{2,3})", text):
                if n not in item_numbers:
                    dangling.append("%s×%s → BACKLOG %s" % (row["surface"], row["state"], n))
        self.assertEqual([], dangling, "表里引用了不存在的条目（U-452：半批已写）")


if __name__ == "__main__":
    unittest.main()
