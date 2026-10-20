# -*- coding: utf-8 -*-
"""变异表"这一卷跑起来了没"的判据形状尺的判据卷（R262 / BACKLOG 286 收尾那一族）。

**不覆盖管线**：这一卷钉的是尺自己 —— 它不判产品，只判"变异表的结论行读法"有没有被写死。
它存在的理由是一条具体的假账：`mutate_r229.py` 旧版用 `'Executed 4 tests' in text` 判"跑了没"，
而它打的那一卷（`ControlHoverLadderTests`）在 R260 从 4 条长到 6 条 ⇒ 数字一变，
**真红了的那一遍会被读成"根本没跑起来"**（NOT_RUN）。反过来，把结论行放宽成"有 Test Suite 就算跑过"
又会把编译失败读成 CAUGHT（D-243）。两头都要有格子拦着。

名册是**有界的会红判据**，不是沉默的豁免：`ROSTER` 与现读必须双向相等 ——
多一支新写的写死表要红，修掉一支而名册没删也要红（"做完一行删一行"）。
"""
from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(REPO, "scripts", "mutation_verdict_scan.py")
DEFAULT_DIR = os.path.join(REPO, ".scratch", "motion-audit-2")

# R262 现读 6 支。每一支的成因写在 AGENT_UI_AUDIT.md 的 R262 那一节（两种味道：
# 把 skip 检测绑在颗数上 / 把 ran 检测绑在颗数上）。修掉一支就从这里删一行。
ROSTER = [
    "mutate_r108.py",
    "mutate_r109.py",
    "mutate_r10_ledger.py",
    "mutate_r110.py",
    "mutate_r225.py",
    "mutate_r9_heatmap.py",
]


def load():
    spec = importlib.util.spec_from_file_location("mutation_verdict_scan", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_table(dirpath, name, body):
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)
    return path


class MutationVerdictScanTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.mkdtemp(prefix="r262_verdict_")
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp, ignore_errors=True))

    # ── 名册：双向相等，且不许登记不存在的文件 ────────────────────────────
    def test_live_roster_equals_registered_roster(self):
        rows = [self.mod.scan_file(os.path.join(DEFAULT_DIR, n))
                for n in sorted(os.listdir(DEFAULT_DIR))
                if n.startswith("mutate_") and n.endswith(".py")]
        named = sorted(r["file"] for r in rows if r["literal"])
        self.assertEqual(sorted(ROSTER), named,
                         "写死颗数的变异表与名册不一致（多出来的要登记并说明成因，"
                         "修掉的要从名册删掉）")

    def test_roster_entries_point_at_files_that_exist(self):
        missing = [n for n in ROSTER if not os.path.exists(os.path.join(DEFAULT_DIR, n))]
        self.assertEqual([], missing, "名册里有不存在的表 —— 那是过期账，比没账更坏")

    def test_there_is_something_to_scan(self):
        n = len([1 for x in os.listdir(DEFAULT_DIR) if x.startswith("mutate_") and x.endswith(".py")])
        self.assertGreaterEqual(n, 50, "只扫到 %d 支变异表？这条尺失去意义前先确认没被删" % n)

    # ── 正对照：写死的数字必须被点名 ─────────────────────────────────────
    def test_planted_literal_count_is_named(self):
        path = write_table(self.tmp, "mutate_planted.py", (
            "x = 1\n"
            "if 'Executed 7 tests' in out:\n"
            "    pass\n"))
        row = self.mod.scan_file(path)
        self.assertEqual(["Executed 7 tests"], row["literal"],
                         "写死 7 颗没被点名 ⇒ 尺是摆设（正对照失败）：" + path)

    # ── 负对照：形状判据不许被误伤（否则名册会变成"把所有表都登记上"）──────
    def test_shape_detector_is_not_an_offender(self):
        path = write_table(self.tmp, "mutate_shaped.py", (
            "import re\n"
            "m = re.findall(r'Executed (\\d+) tests?, with (\\d+) failures?', text)\n"))
        row = self.mod.scan_file(path)
        self.assertEqual([], row["literal"], "按形状判的表被误报成写死 ⇒ 尺在读错对象")
        self.assertTrue(row["shape"], "形状判据没被认出来（另一格的名册会因此失真）")
        # 这一格自己也要被验一次：写进临时文件的必须是 `\d+` 而不是 `\\d+`，
        # 否则这格只是在测转义，不是在测尺。
        with open(path, encoding="utf-8") as handle:
            self.assertIn("Executed (\\d+) tests?", handle.read())

    def test_zero_is_a_state_not_a_round_reading(self):
        path = write_table(self.tmp, "mutate_zero.py", (
            "x = 1\n"
            "if 'Executed 0 tests' in out:\n"
            "    return 'DID-NOT-RUN=filter matched nothing'\n"))
        self.assertEqual([], self.mod.scan_file(path)["literal"],
                         "Executed 0 是「一条都没匹配上」这个状态，不是本轮量到的颗数 ⇒ 不该被点名")

    # ── 估计量卫生：守卫读字段，不读散文（R74 / D-247 那一族）───────────────
    def test_comment_and_docstring_quote_do_not_feed_the_ruler(self):
        path = write_table(self.tmp, "mutate_prose.py", (
            '"""这一支沿用旧写法 Executed 3 tests，见 R262 的说明。"""\n'
            "# 上一版写的是 'Executed 9 tests' in text，已废弃\n"
            "import re\n"
            "m = re.search(r'Executed (\\d+) tests', text)\n"))
        row = self.mod.scan_file(path)
        self.assertEqual([], row["literal"],
                         "注释与 docstring 里引用这句话就把表点名 ⇒ 守卫被散文喂饱")
        self.assertEqual("mutate_prose.py", row["file"], "文件本身没被扫到 ⇒ 空对账")

    def test_parse_failure_is_reported_not_silence(self):
        path = write_table(self.tmp, "mutate_broken.py", "def f(:\n")
        row = self.mod.scan_file(path)
        self.assertIsNotNone(row["parse_error"], "语法坏了却报成「没问题」⇒ 假绿")
        self.assertEqual([], row["literal"], "解析失败的表不许进 offender 名单（它不是「干净」，是没量到）")

    # ── 命令行契约：目录不存在必须响，不许在空名单上给绿（R99）───────────────
    def test_missing_dir_exits_one(self):
        proc = subprocess.run([sys.executable, SCRIPT, "--dir", os.path.join(self.tmp, "nope")],
                              capture_output=True, text=True)
        self.assertNotEqual(0, proc.returncode, "目录不存在却 exit 0 ⇒ 空对账静默通过")
        self.assertIn("MUT_VERDICT_DIR_MISSING=1", proc.stdout + proc.stderr)

    def test_cli_summary_line_names_the_offenders(self):
        write_table(self.tmp, "mutate_a.py", "x = 'Executed 5 tests'\n")
        proc = subprocess.run([sys.executable, SCRIPT, "--dir", self.tmp],
                              capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, proc.stderr[-400:])
        self.assertIn("MUT_VERDICT_SUMMARY tables=1 offenders=1 named=mutate_a.py", proc.stdout)

    def test_source_of_this_test_is_valid_python(self):
        with open(SCRIPT, encoding="utf-8") as handle:
            ast.parse(handle.read())


if __name__ == "__main__":
    unittest.main()
