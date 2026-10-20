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

    def test_the_repository_currently_has_no_arm_id_collisions(self):
        tool = load_tool()
        files, dupes, repeats, total = tool.cross_table_ids()
        self.assertGreaterEqual(len(files), 100,
                                u"扫到的表少于 100 张 ⇒ 目录参数或通配漂了，这条守卫会空跑")
        self.assertGreaterEqual(total, 400, u"臂号总数掉到 400 以下 ⇒ 扫描形状变了，先修尺再谈结论")
        self.assertEqual({}, dupes, u"跨表撞号：%s" % dupes)
        self.assertEqual({}, repeats, u"同表重号：%s" % repeats)


if __name__ == u"__main__":
    unittest.main()
