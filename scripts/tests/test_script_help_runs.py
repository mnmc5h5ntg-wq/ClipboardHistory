"""每个脚本的 `--help` 都必须能用**当前这台机器的 python** 跑出来。

起因：CI 的 runner 上是 Homebrew python 3.14，本机 `/usr/bin/python3` 是 3.9。
`frame_baseline.py` 里一个 argparse 的 help 文案写了 "95% 空白"，
argparse 会把 help 串当 `%` 格式串处理，3.14 直接
`ValueError: badly formed help string` 并在**构造 parser 的那一刻**抛出 ——
本机 3.9 却一声不响。于是"CI 少帧硬门"这一步红了，红的还是脚本自己根本没能启动，
判据一条都没执行（run 38074023728）。

这类"CI 的解释器比本机严"的事在 Swift 那边早就写过（CI 是 6.1.2 比本机 6.2.1 严），
但我只给 Swift 留了 0-warning 闸，没给 Python 留任何等价的检查。
`--help` 是最便宜的探针：它不测业务，只测"这个脚本在你的解释器上能不能被构造出来"。
"""
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = sorted((Path(__file__).resolve().parents[2] / "scripts").glob("*.py"))


class ScriptHelpRunsTests(unittest.TestCase):
    def test_there_is_something_to_check(self):
        self.assertGreaterEqual(len(SCRIPTS), 4,
                                "scripts/ 下只剩 %d 个脚本？这条守卫失去意义前先确认没被删" % len(SCRIPTS))

    def test_every_script_builds_its_parser_under_this_interpreter(self):
        bad = []
        for script in SCRIPTS:
            proc = subprocess.run([sys.executable, str(script), "--help"],
                                  capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                bad.append("%s (exit=%s)\n%s" % (script.name, proc.returncode,
                                                 (proc.stderr or "")[-400:]))
        self.assertEqual(bad, [],
                         "这些脚本在当前解释器上连 --help 都跑不出来（argparse 的 help 串里"
                         "别写裸的 %）：\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
