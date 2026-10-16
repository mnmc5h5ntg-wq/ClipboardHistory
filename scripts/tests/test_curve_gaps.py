# -*- coding: utf-8 -*-
"""曲线仪器的"中间断档必须挡"这一格（R100 / U-278）。

**不覆盖管线**：它判的是一把 .scratch 里的读数工具，不是产品；
产品级判据在 `ClipboardHistory/Tests/`（本文件所属的这套脚本自检守的是发布链路与台账工具）。

三条用例各挡一种"看着对、其实不报错"：
① 正对照（合成）：轮次连续 ⇒ 退出码必须是 0。少了这一条，"断档红"可以靠"永远红"蒙过去。
② 断档（合成）：中间缺一轮 ⇒ 退出码非 0 且必须打 `CURVE_GAP`。
   这一格就是本轮真实踩到的坑：编辑台账时把 `## Round 99 · …` 整行吃掉，
   仪器把 `GAPS=[99]` **印了出来**却 `exit 0` —— 报出来了但不负责，等于没报。
③ 真产物：仓库里那份台账现在必须无断档（防"新闸门是恒真的"）。
"""
import io
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(REPO, ".scratch", "motion-audit-2", "curve_from_ledger.py")
LEDGER = "AGENT_VISUAL_ITERATION.md"


def make_ledger(rounds):
    """合成一份台账：升序（与真台账同方向），每轮带一行结论 `**均分 91.5**`。

    轮次号必须 ≥9：仪器只把 Round 9 起算进阶段二曲线，而那段代码会读 `phase2[0]`，
    拿 1..3 造例会让它 IndexError —— 那是用例写错，不是仪器坏（先按仪器的实际口径造样本）。
    """
    parts = [u"# 视觉迭代台账（合成）\n"]
    for r in rounds:
        parts.append(u"## Round %s · 第 %s 轮标题\n\n**均分 91.5**\n\n" % (r, r))
    return u"".join(parts)


def run_curve(cwd):
    return subprocess.run(["python3", SCRIPT], cwd=cwd,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          universal_newlines=True)


class CurveGapGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="r100-curve-")
        shutil.copy(SCRIPT, os.path.join(self.tmp, os.path.basename(SCRIPT)))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_ledger(self, rounds):
        with io.open(os.path.join(self.tmp, LEDGER), "w", encoding="utf-8") as handle:
            handle.write(make_ledger(rounds))

    def script_in_tmp(self):
        return os.path.join(self.tmp, os.path.basename(SCRIPT))

    def test_contiguous_rounds_pass(self):
        """① 正对照：不断档时闸门必须放它过去。"""
        self.write_ledger([9, 10, 11])
        proc = subprocess.run(["python3", self.script_in_tmp()], cwd=self.tmp,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True)
        self.assertEqual(0, proc.returncode,
                         "连续轮次却被闸门拦下 ⇒ 这一格是恒真的：\n" + proc.stdout)
        self.assertIn("GAPS=none", proc.stdout)

    def test_missing_middle_round_is_fatal(self):
        """② 中间缺一轮：既要打出来，也要让退出码负责。"""
        self.write_ledger([9, 10, 12])
        proc = subprocess.run(["python3", self.script_in_tmp()], cwd=self.tmp,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True)
        self.assertIn("GAPS=[11]", proc.stdout,
                      "断档没被报出来 ⇒ 断档检查本身坏了：\n" + proc.stdout)
        self.assertIn("CURVE_GAP", proc.stdout,
                      "报了断档却没打闸门行 ⇒ 又是「印出来但 exit 0」那一族：\n" + proc.stdout)
        self.assertNotEqual(0, proc.returncode,
                            "中间断一档而退出码仍是 0 ⇒ 少一轮只会让均值跟着错，"
                            "而这正是本文件顶部那段话讲的错（R100 实测：台账编辑吃掉整节标题）")

    def test_real_ledger_has_no_gap_today(self):
        """③ 真产物：仓库那份台账今天必须无断档（防新闸门只在合成样本上成立）。"""
        self.assertTrue(os.path.exists(SCRIPT), "找不到 " + SCRIPT)
        proc = run_curve(REPO)
        self.assertIn("GAPS=none", proc.stdout,
                      "真台账有断档 ⇒ 先修台账再谈闸门：\n" + proc.stdout[-400:])
        self.assertEqual(0, proc.returncode,
                         "真台账 GAPS=none 却退出非 0 ⇒ 闸门咬错了别的东西：\n"
                         + proc.stdout[-400:])


if __name__ == "__main__":
    unittest.main()
