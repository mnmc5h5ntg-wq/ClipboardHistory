# -*- coding: utf-8 -*-
"""闸门结论行的**归属**守卫（R115 / BACKLOG 168）。

R112 的动效闸门在 CI 上第一次落读数时，`ci_read` 的 `MOTION_GATE` 通道里混进了
`Release script tests` 那一步的**样张**：`MOTION_GATE_CASES passed=1 skipped=0 failed=1`
（夹具）与 `passed=34 skipped=32 failed=0`（runner 的判词）形状完全一样。
按 marker grep 的人拿到哪一条，取决于谁先出现。与 R53「region() 命中守卫自己」同一族，
但这次的后果更直接：166 的升硬门判据就是"两跑名单一致"，那份名单可以被夹具冒充。

这里判的是**产物**而不是源码文本：真跑一遍样张那一卷，看它的 stdout 里有没有生产标记。
"""
import glob
import io
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def production_labels():
    """生产那一侧用过的标签 = workflow 里显式的 `--label` ∪ 闸门自己的默认值。"""
    labels = set()
    for path in glob.glob(os.path.join(ROOT, ".github", "workflows", "*.yml")):
        with io.open(path, encoding="utf-8") as handle:
            text = handle.read()
        for match in re.finditer(r'ci_capture_gate\.py.*--label\s+([A-Za-z_][A-Za-z0-9_]*)', text):
            labels.add(match.group(1))
    with io.open(os.path.join(ROOT, "scripts", "ci_capture_gate.py"), encoding="utf-8") as handle:
        gate = handle.read()
    for match in re.finditer(r'add_argument\("--label",\s*default="([A-Z]+)"', gate):
        labels.add(match.group(1))
    return labels


def markers_present(text, labels):
    return sorted({label for label in labels for marker in ("%s_GATE_" % label,) if marker in text})


class GateMarkerHygieneTests(unittest.TestCase):
    def test_production_labels_are_discovered(self):
        labels = production_labels()
        self.assertTrue(labels, "workflow 与闸门源码里一个 `--label` 都没找到 ⇒ 这条守卫是空的")
        self.assertIn("MOTION", labels, "动效那一卷的标签没被发现 ⇒ workflow 的形状变了，先修这条")

    def test_the_sample_suite_prints_no_production_marker(self):
        labels = production_labels()
        proc = subprocess.Popen(
            [sys.executable, "-m", "pytest",
             os.path.join("scripts", "tests", "test_ci_capture_gate.py"), "-q", "--no-header"],
            cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out = proc.communicate()[0].decode("utf-8", "replace")
        self.assertEqual(0, proc.returncode, "样张那一卷自己没通过（先把上面那卷修绿再看这一格）：\n%s" % out[-800:])
        self.assertEqual([], markers_present(out, labels),
                         "脚本电池的样张把**生产标记**打进了 stdout ⇒ 同一份 CI 日志里真步与夹具分不开：%s"
                         % markers_present(out, labels))

    def test_the_hygiene_check_itself_has_a_tooth(self):
        labels = production_labels()
        victim = sorted(labels)[0]
        forged = "%s_GATE_CASES passed=1 skipped=0 failed=1" % victim
        self.assertEqual([victim], markers_present(forged, labels),
                         "伪造一条生产标记都没抓到 ⇒ 它不是在判归属")
        self.assertEqual([], markers_present("SAMPLE_GATE_CASES passed=1",
                                             {label for label in labels if label != "SAMPLE"}),
                         "样张自己的标签也被当成生产标记 ⇒ 两卷并没有真的分开")


if __name__ == "__main__":
    unittest.main()
