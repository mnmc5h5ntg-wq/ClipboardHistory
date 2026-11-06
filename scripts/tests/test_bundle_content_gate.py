# -*- coding: utf-8 -*-
"""R593 / 靶 2：`bundle_content_gate.py` 的接线判据卷。

判的是三件事：① 三种结论各自不同（有桩 / 尺瞎了 / 产物不在）；② 正对照用**真产物**（这台机器
`make bundle` 落下的那一份），不是手摆文件；③ 落点是从 Makefile 现读的，不在这里抄第二份常量。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import bundle_content_gate as gate  # noqa: E402
import repo_root_bundle  # noqa: E402

# 从 D-029 那两条实测形状里搭的 `otool -tvV` 片段（真产物那一半由下面那格现读，不靠这两段）。
# 形状必须与解析器认的那一条一致：字面量行在前、`bl …unimplementedInitializer` 行在后
# —— 第一版我只写了 `-[Class init:]` + `unimplemented initializer`，解析器读成 0 个桩 ⇒
# 判据红在"尺瞎了"那一支上，而这恰好证明那一支有牙。
def _stub(cls, addr):
    return (u"%s\tadrp\tx5, 510 ; 0x10021a000\n"
            u"%s\tadd\tx5, x5, #0x3b0 ; literal pool for: \"%s\"\n"
            u"%s\tbl\t_$ss25_unimplementedInitializer22file_name22function_line14function_columnys5NeverO...\n"
            % (addr, _next(addr), cls, _next(_next(addr))))


def _next(addr):
    n = int(addr, 16) + 4
    return u"%016x" % n


CLEAN = (_stub(u"ClipboardHistoryApp.ChineseSelectableNSTextView", u"000000010001ce18")
         + _stub(u"ClipboardHistoryApp.Coordinator", u"000000010001cf00")
         + _stub(u"ClipboardHistoryApp.QuickPickController", u"000000010001d000"))
STUBBED = CLEAN + _stub(u"ClipboardHistoryApp.AppDelegate", u"000000010001d100")
BLIND = u"no symbols\ntext\n"


class VerdictTableTest(unittest.TestCase):
    def test_three_shapes_are_three_different_verdicts(self):
        self.assertEqual(0, gate.judge(CLEAN)[0], u"良性桩那一档不该拦：%s" % gate.judge(CLEAN)[1])
        rc, why = gate.judge(STUBBED)
        self.assertEqual(1, rc, u"AppDelegate 桩回来了必须红")
        self.assertIn(u"D-029", why)
        rc, why = gate.judge(BLIND)
        self.assertEqual(1, rc, u"一个桩都没解析出来 = 尺瞎了，必须红（不许读成『没有桩所以干净』）")
        self.assertIn(u"STUB_SCAN_BLIND", why)

    def test_the_missing_artifact_is_not_run_and_says_so(self):
        tmp = tempfile.mkdtemp(prefix=u"bundle-content-gate-")
        proc = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "bundle_content_gate.py"),
                               os.path.join(tmp, u"没有这个.app")],
                              capture_output=True, text=True)
        self.assertEqual(2, proc.returncode,
                         u"产物不在盘上 ⇒ exit 2（not-run），不许 exit 0：%s%s" % (proc.stdout, proc.stderr))
        self.assertIn(u"BUNDLE_CONTENT=absent", proc.stdout)
        self.assertIn(u"not-run", proc.stdout, u"红话/绿话之外还要写清『没判到不等于干净』")


class DriverPathTest(unittest.TestCase):
    def test_the_gate_reads_the_bundle_the_makefile_produces(self):
        """落点从 Makefile 现读，并且**这台机器真的构建过** ⇒ 判的是产品自己的驱动路径产出的东西。"""
        bundle = repo_root_bundle.makefile_stage(ROOT)
        self.assertIn(u"_bundle", bundle.replace(u"\\", u"/"),
                      u"暂存路径读出来不像暂存目录 ⇒ 620 那条漂了")
        self.assertNotIn(ROOT, bundle, u"落点又指回仓库根 ⇒ 620 复发，这一格必须先红")
        exe = os.path.join(bundle, u"Contents", u"MacOS", gate.EXECUTABLE)
        if not os.path.exists(exe):
            self.skipTest(u"BUNDLE_CONTENT_DRIVER_PATH_NOT_RUN=no-artifact —— 这台机器现在没有 "
                          u"%s（跑过 make bundle 再验）。这一格是**没跑**，不是『内容干净』。" % bundle)
        proc = subprocess.run([sys.executable,
                               os.path.join(ROOT, "scripts", "bundle_content_gate.py")],
                              capture_output=True, text=True)
        self.assertEqual(0, proc.returncode, u"真产物上这一格必须绿：%s%s" % (proc.stdout, proc.stderr))
        self.assertIn(u"BUNDLE_CONTENT_GATE_RESULT=ok", proc.stdout)
        self.assertIn(u"APP_DELEGATE_STUB=absent", proc.stdout)


if __name__ == u"__main__":
    unittest.main(verbosity=2)
