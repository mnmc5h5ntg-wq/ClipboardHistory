#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变异臂号的查重器要有牙（R143 / U-483）。

起因是实测到的撞号：`mutate_r141.py` 在 R143 补的三把用了 M666/M667/M668，而 `mutate_r142.py`
的 M666-M669 早就占了这三个号 ⇒ 台账里一句「M668 CAUGHT」同时指两把不同的刀。
每张表只数自己的 `n=`，所以撞号在写的时候没人看见。

查重器不能只靠"恰好有重复"来证明它有效 ⇒ 这里给它配人造的撞号表（正对照），
再加一条"仓库现状必须 0 重复"（守卫）。两条管的是相反的方向。

判据来源：`arm_ids` / `cross_table_ids` 都在 `.scratch/motion-audit-2/mutate_needle_precheck.py` 里，
那是**工具真身**，不是这里另抄一份（抄一份就等于两条实现互相掩盖，R134 那一族）。
"""
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL = REPO / u".scratch" / u"motion-audit-2" / u"mutate_needle_precheck.py"


def load_tool():
    spec = importlib.util.spec_from_file_location(u"needle_precheck_under_test", str(TOOL))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)      # 文件底部有 __main__ 守卫，import 不会真跑预检
    return module


class MutateArmRegistryTests(unittest.TestCase):

    def write_table(self, directory, name, lines):
        path = os.path.join(directory, name + u".py")
        with open(path, u"w", encoding=u"utf-8") as handle:
            handle.write(u"\n".join(lines) + u"\n")
        return path

    def test_bash_recapture_arms_are_in_the_same_cross_table_dedup(self):
        """R261 / BACKLOG 306：重捕型刀住在 bash + `arms_r*/manifest.tsv`，旧查重只看 `mutate_r*.py`
        ⇒ M814…M818 五把刀连续四轮"名册看不见"，撞号不会有人发现。
        这一格种一对**人造的**撞号 manifest（正对照）：尺必须把它们点名。
        """
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            for table, mid in ((u"arms_r900", u"M890"), (u"arms_r901", u"M890")):
                d = os.path.join(directory, table)
                os.makedirs(d)
                with open(os.path.join(d, u"manifest.tsv"), u"w", encoding=u"utf-8") as handle:
                    handle.write(u"\t".join([mid, u"recapture", u"ClipboardHistory/x.swift",
                                             u".scratch/a.old", u".scratch/a.new",
                                             u"someTest", u"人造撞号对照"]) + u"\n")
            _files, dupes, _repeats, total = tool.cross_table_ids(directory)
        self.assertEqual(2, total, u"两张 manifest 各一把 ⇒ 该数到 2，现读 %d" % total)
        self.assertEqual([u"arms_r900", u"arms_r901"], dupes.get(u"M890"),
                         u"bash 刀撞号没被抓到 ⇒ 名册还是看不见它们：%s" % dupes)

    def test_the_repo_manifests_are_registered_unique_and_anchored(self):
        """仓库现状：五把重捕型刀要在名册里、号不撞、锚点各自恰好命中一次。

        锚点命中=0 有两种成因（R103：要么针死了，要么此刻正有表把它注入了）⇒ 这一格必须在
        **电池之外**跑预检时读，别在变异表跑到一半时读。
        """
        tool = load_tool()
        rows = tool.manifest_rows()
        ids = [r[1] for r in rows]
        self.assertGreaterEqual(len(ids), 5,
                                u"重捕型刀少于 5 把 ⇒ 名册又看不见 bash 刀了（M814…M818）：%s" % ids)
        self.assertEqual(sorted(ids), sorted(set(ids)), u"manifest 内部撞号：%s" % ids)
        self.assertEqual(set(), set(ids) & set(self.python_arm_ids(tool)),
                         u"bash 刀号与 python 表撞号")
        n, problems = tool.check_manifests()
        self.assertEqual(len(ids), n)
        self.assertEqual([], problems, u"锚点腐烂或空刀：\n  " + u"\n  ".join(problems))

    def python_arm_ids(self, tool):
        out = set()
        for name in tool.TABLES:
            path = os.path.join(str(REPO / u".scratch" / u"motion-audit-2"), name + u".py")
            if os.path.exists(path):
                out.update(tool.arm_ids(path))
        return out

    def test_four_digit_arm_ids_are_not_invisible_to_the_needle_precheck(self):
        """R355 / BACKLOG 430：`MID` 以前只认三位（`M\\d{3}`）⇒ 从 R345 起的 M1001… 整张表
        被预检读成「静态抽不出 needle」，**针从来没查过**（R355 自己的 M1005 就是这么发现隐形的）。

        正对照的形状必须是人造表：用仓库里现存的五位来测，一旦哪天全删掉它就会空跑。
        """
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_table(directory, u"mutate_r912", [
                u"ARMS = [",
                u'    ("M1006", u"四位数", "/tmp/a.swift", "needle-text", "repl-text"),',
                u"]",
            ])
            spec = importlib.util.spec_from_file_location(u"four_digit_under_test", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sites = tool.needles(module)
        self.assertEqual([(u"M1006", u"/tmp/a.swift", [u"needle-text"])], sites,
                         u"四位数刀号在 needle 预检里隐形 ⇒ 那一批刀既没查过针，也不在 covered 里")

    def test_four_digit_arm_ids_are_not_invisible_to_the_cross_table_dedup(self):
        """R381：`MID` 放宽到四位只治了 needle 那一侧；`ARM_LINE` 还是 `M\\d{3}`。

        ⇒ r56 的 M1010 与 R381 的 M1011/M1012 在**跨表查重**里隐形：撞号不会有人发现。
        正对照是人造的两张表（各一把 M1007），尺必须点名它们；只测仓库现状会随刀号漂走。
        """
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            for table in (u"mutate_r913", u"mutate_r914"):
                self.write_table(directory, table, [
                    u"ARMS = [",
                    u'    ("M1007", u"四位数", "/tmp/a.swift", "needle-text", "repl-text", "CAUGHT"),',
                    u"]",
                ])
            _files, dupes, repeats, total = tool.cross_table_ids(directory)
        self.assertEqual(2, total, u"四位数刀号没被扫描器看见 ⇒ 跨表查重对 M1001… 整批失效")
        self.assertEqual([u"mutate_r913", u"mutate_r914"], dupes.get(u"M1007"),
                         u"四位数撞号必须被点名（与三位数同一个判据）")
        self.assertEqual({}, repeats)

    def test_duplicate_arm_id_across_two_tables_is_found(self):
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            self.write_table(directory, u"mutate_r900", [
                u"ARMS = [",
                u'    ("M700", "/tmp/a", "needle", "replaced", "CAUGHT"),',
                u"]",
            ])
            self.write_table(directory, u"mutate_r901", [
                u"ARMS = [",
                u'    ("M700", "/tmp/b", "needle2", "replaced2", "CAUGHT"),',
                u"]",
            ])
            files, dupes, repeats, total = tool.cross_table_ids(directory)
        self.assertEqual(2, len(files), u"两张人造表都没被扫到 ⇒ 这把尺量的不是它声称的对象")
        self.assertEqual(2, total)
        self.assertEqual([u"mutate_r900", u"mutate_r901"], dupes.get(u"M700"),
                         u"跨表撞号必须被点名（这就是 R141/R142 那一次的形状）")
        self.assertEqual({}, repeats, u"同表内没重复，不该报同表重复")

    def test_same_arm_id_twice_in_one_table_is_found(self):
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            self.write_table(directory, u"mutate_r902", [
                u"ARMS = [",
                u'    ("M701", "/tmp/a", "needle", "replaced", "CAUGHT"),',
                u'    ("M701", "/tmp/a", "other", "replaced", "CAUGHT"),',
                u"]",
            ])
            files, dupes, repeats, total = tool.cross_table_ids(directory)
        self.assertEqual([u"mutate_r902", u"mutate_r902"], repeats.get(u"M701"),
                         u"同一个号在一张表里出现两次 ⇒ 要么刀写重了，要么号忘了往后排")
        self.assertEqual({}, dupes)

    def test_runtime_append_lines_are_not_counted_as_arms(self):
        """正对照的反面：把运行期回填结果的那两行误当成臂声明，就会报出一个假重复。

        这不是设想 —— 第一版实扫 `mutate_r99.py` 时它报了 `M554 出现在两处`，
        而那两行都是 `results.append(("M554", …))`（同一把刀的两条出口）。
        假阳性会让下一个人去「修号」，而刀号是对的、要修的是扫描器。
        """
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            self.write_table(directory, u"mutate_r903", [
                u"ARMS = [",
                u'    ("M702", "/tmp/a", "needle", "replaced", "CAUGHT"),',
                u"]",
                u'    results.append(("M702", verdict, u"还原成改之前", reason))',
                u'    results.append(("M702", "DID-NOT-RUN", u"还原失败", str(err)))',
            ])
            files, dupes, repeats, total = tool.cross_table_ids(directory)
        self.assertEqual(1, total, u"只有 ARMS 里那一行该算臂")
        self.assertEqual({}, dupes)
        self.assertEqual({}, repeats)

    def test_single_quoted_arm_lines_are_extracted_too(self):
        """R262：`('M6NN', …` 这种单引号写法以前一颗都抽不出来（现读 34 张表 / 123 把刀隐形）。

        这一格还钉住**组号**：放宽引号之后编号住在第二组，若代码退回 `group(1)`，
        抽出来的是引号字符本身 ⇒ 所有臂号塌成两个"号"。所以这里断言里没有引号。
        """
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_table(directory, u"mutate_r906", [
                u"ARMS = [",
                u"    ('M703', u'单引号写法', '/tmp/a', 'needle', 'repl'),",
                u'    ("M704", "双引号写法", "/tmp/b", "needle", "repl"),',
                u"]",
            ])
            got = tool.arm_ids(path)
        self.assertEqual([u"M703", u"M704"], got,
                         u"两种引号都得抽得出来（少一种就是那 123 把刀继续隐形）")
        self.assertFalse([x for x in got if not x.startswith(u"M")],
                         u"抽出来的是引号而不是刀号 ⇒ ARM_LINE 的组号取错了：%s" % got)

    def test_quoting_style_does_not_hide_a_cross_table_collision(self):
        """正对照：一张双引号表 + 一张单引号表撞同一个号 ⇒ 必须被点名。

        放宽之前这两张表在查重器里**各是一个宇宙**：单引号那张一颗号都抽不出来，
        于是撞号静默通过。形状照 R141/R142 那一次，只把引号换成历史上看不见的那一种。
        """
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            self.write_table(directory, u"mutate_r907", [
                u"ARMS = [",
                u'    ("M705", "双引号那张", "/tmp/a", "n", "r"),',
                u"]",
            ])
            self.write_table(directory, u"mutate_r908", [
                u"ARMS = [",
                u"    ('M705', u'单引号那张', '/tmp/b', 'n', 'r'),",
                u"]",
            ])
            files, dupes, repeats, total = tool.cross_table_ids(directory)
        self.assertEqual(2, total, u"两张表各一颗号：%s" % total)
        self.assertEqual([u"mutate_r907", u"mutate_r908"], dupes.get(u"M705"),
                         u"引号不同就不算撞号 ⇒ 这正是 306 结掉的那个洞的另一半")

    def test_the_tools_derive_their_repo_root_instead_of_hardcoding_it(self):
        """R262：runner 上这一格只能报 FileNotFoundError —— 预检把仓库根写死成了我本机的路径。

        run 39512069087 / STEP[9] 现读：`check_manifests` 去开 `/Users/wangziyi/Codex_Project0/...`，
        而作业树在 `/Users/runner/work/ClipboardHistory/ClipboardHistory` ⇒ 一格"本机绿、
        另一台机器只能报错"的判据不是判据（R100 的夹具绝对路径、R154 的环境差异是同一族）。

        扫的是**代码里的字符串常量**：用 `ast`，所以注释里引用那句路径不会被误伤
        （本文件上面那段 docstring 就写着 `/Users/...`，它不该喂饱这条守卫）。
        估计量与 `scripts/mutation_verdict_scan.py` 共用同一颗 = D-247，不另抄一份。
        """
        import ast

        spec = importlib.util.spec_from_file_location(
            u"verdict_scan_under_test", str(REPO / u"scripts" / u"mutation_verdict_scan.py"))
        ruler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ruler)

        def abs_home(path):
            with open(path, encoding=u"utf-8") as handle:
                tree = ast.parse(handle.read())
            return [s for s in ruler.string_constants(tree) if u"/Users/" in s]

        tools = [str(TOOL), str(REPO / u"scripts" / u"mutation_verdict_scan.py"),
                 str(REPO / u".scratch" / u"motion-audit-2" / u"curve_from_ledger.py"),
                 str(REPO / u".scratch" / u"motion-audit-2" / u"make_surface_ledger.py")]
        for tool_path in tools:
            self.assertEqual([], abs_home(tool_path),
                              u"%s 里不许出现写死的家目录路径：换一台机器它只会报错，不会给出读数"
                              % os.path.basename(tool_path))
        with tempfile.TemporaryDirectory() as directory:
            planted = self.write_table(directory, u"mutate_r909", [
                u"ROOT = '/Users/someone/else'",
            ])
            self.assertEqual(1, len(abs_home(planted)),
                             u"写死绝对路径的正对照没被点名 ⇒ 上面那条守卫是恒真的")

    def test_the_roster_gap_is_pinned_to_the_measured_number(self):
        """BACKLOG 310 的地板（R377 现读）：**74 张表声明了臂却没登记进 `TABLES`，共 414 把刀**。
        （R264 是 75 / 423；R377 把 `mutate_r56_readings_channel` 真的登记进去、并让抽取器认得它的
        五元组形状与 `.yml` 目标 —— 它那 10 把刀此前**从来没被针预检覆盖过**，其中 6 把连着两次
        CAUGHT 的正是 R376 修的那把 M278。）

        撞号查重按 glob 扫全部表，而 needle 预检只走手写名册 ⇒ 未登记的表**静默不覆盖**：
        锚点腐烂（286 那一族）可以在它们身上重新长出来而报表一片绿。
        这一格用 `assertEqual` 而不是 `assertLessEqual`：多一张表没登记 ⇒ 红；
        少一张（真去登记了）⇒ 也红，但红话是"把地板降到实测值"，逼着那一笔同时进台账。
        数的是"抽得出臂"的那些（抽不出的是 285 那族的"薄"，两种成因不许混成一个数）。
        """
        tool = load_tool()
        gaps = tool.roster_gap()
        tables = len(gaps)
        arms = sum(n for _, n in gaps)
        detail = u"未登记表=%d 隐藏臂=%d；前几名 %s" % (
            tables, arms, u"、".join(u"%s(%d)" % (n, k) for n, k in sorted(gaps)[:6]))
        self.assertEqual(74, tables,
                         u"登记表与实存表的缺口变了（R377 现读 74）⇒ 要么有新表静默不覆盖，"
                         u"要么真登记掉了 —— 两种都要改账。" + detail)
        self.assertEqual(414, arms,
                         u"缺口里的臂数变了（R377 现读 414）⇒ 同上，改账之前先看清是哪张表。" + detail)

    def test_an_unregistered_table_that_declares_arms_is_named(self):
        """正对照：人造一张"声明了臂但没登记"的表 ⇒ 必须被点名（否则上面那个地板是在数空气）。"""
        tool = load_tool()
        with tempfile.TemporaryDirectory() as directory:
            self.write_table(directory, u"mutate_r910", [
                u"ARMS = [",
                u'    ("M706", "已登记那张", "/tmp/a", "n", "r"),',
                u"]",
            ])
            self.write_table(directory, u"mutate_r911", [
                u"ARMS = [",
                u"    ('M707', u'没登记那张', '/tmp/b', 'n', 'r'),",
                u"]",
            ])
            gaps = tool.roster_gap(directory, tables=[u"mutate_r910"])
        self.assertEqual([(u"mutate_r911", 1)], gaps,
                         u"未登记却声明了臂的表没被点名 ⇒ 310 那个缺口仍然只能靠记忆守")

    def test_the_repository_currently_has_no_arm_id_collisions(self):
        tool = load_tool()
        files, dupes, repeats, total = tool.cross_table_ids()
        self.assertGreaterEqual(len(files), 100,
                                u"扫到的表少于 100 张 ⇒ 目录参数或通配漂了，这条守卫会空跑")
        # 地板是量出来的，不是猜的：R262 现读 695（双引号 572 颗 + 单引号 123 颗 + manifest 16 把）。
        # 谁把 ARM_LINE 收窄回"只认双引号"，这一格会先红在数上，而不是让 123 把刀重新隐形。
        self.assertGreaterEqual(total, 600,
                                u"臂号总数掉到 600 以下（R262 实测 695）⇒ 扫描形状收窄了，先修尺再谈结论")
        self.assertEqual({}, dupes, u"跨表撞号：%s" % dupes)
        self.assertEqual({}, repeats, u"同表重号：%s" % repeats)


if __name__ == u"__main__":
    unittest.main()
