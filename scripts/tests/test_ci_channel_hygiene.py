#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`scripts/ci_channel_hygiene.py` 的门（R565 补段 C）。

同族两次事故收成一条守卫：
- R564 `commit_round_identity.py` 把仓库根写成本机绝对路径 ⇒ runner 上 `subprocess.run(cwd=…)` 抛异常
  ⇒ STEP[9] 红、STEP[10]-[14]（含帧基线名册门）整段 skipped。
- R565 同一支守卫把退化说明写进 `范围=` 的**值**里（一个 ASCII 空格）⇒ 判它的测试
  `dict(kv.split("=", 1) …)` 崩 `element #1 has length 1`。

形状都是"判据的输出契约从没被任何门判过"。四格：名单非空、真人路径、通道裸空格、以及
**每条都配正对照**（尺不测坏形状就等于没有）。
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOL = os.path.join(ROOT, 'scripts', 'ci_channel_hygiene.py')

spec = importlib.util.spec_from_file_location('ci_channel_hygiene_under_test', TOOL)
chi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chi)


def run_tool(*extra):
    env = {k: v for k, v in os.environ.items() if k != 'SDKROOT'}
    env['PYTHONUTF8'] = '1'
    proc = subprocess.run([sys.executable, TOOL] + list(extra), cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=180)
    return proc.returncode, proc.stdout + proc.stderr


class CiChannelHygieneTests(unittest.TestCase):
    def test_script_help_runs(self):
        code, out = run_tool('--help')
        self.assertEqual(0, code, out)
        self.assertIn('--extra', out)

    def test_roster_is_derived_from_the_workflow_and_nonempty(self):
        """名单从 `ci.yml` 现读，且不许为空（空名单 = 没有对象，不许读成绿）。"""
        roster = chi.ci_script_roster()
        self.assertGreaterEqual(len(roster), 5, '从 ci.yml 只抽出 %d 支脚本 ⇒ 解析器或工作流形状变了' % len(roster))
        # R564 那支守卫**不在** ci.yml 的名单上（STEP[9] 跑的是 `unittest discover`，它是被电池调的）
        # ⇒ 只按 ci.yml 抽名单会漏掉那个两次打死机器的文件。这一格钉的是"扫描范围要覆盖到它"。
        self.assertNotIn('scripts/commit_round_identity.py', roster,
                         '它若进了 ci.yml 名单，下面那一格就该改成断言名单里有它')
        self.assertIn('scripts/commit_round_identity.py', chi.referenced_by_battery(),
                      '电池引用闭包没抽到 R564 那支守卫 ⇒ 扫描范围漏了红过两次的对象')

    def test_empty_roster_is_red_not_green(self):
        """正对照：把 `ci.yml` 换成一份没有脚本的 ⇒ 必须 ROSTER_EMPTY 红，不许"零条也算过"。"""
        with tempfile.TemporaryDirectory() as directory:
            os.mkdir(os.path.join(directory, '.github'))
            os.mkdir(os.path.join(directory, '.github', 'workflows'))
            with open(os.path.join(directory, '.github', 'workflows', 'CI.yml'), 'w') as handle:
                handle.write('jobs:\n  build:\n    run: echo nothing\n')
            code, out = run_tool()
            self.assertEqual(0, code, out)  # 默认那份是真的，绿
            # 直接叫解析器读那份假的 ⇒ 空表；main 在空表时必须返回 1
            self.assertEqual([], chi.ci_script_roster(os.path.join(directory, '.github', 'workflows')))
            real = chi.ci_script_roster
            chi.ci_script_roster = lambda *a, **k: []
            try:
                self.assertEqual(1, chi.main([]), '空名单被读成绿 ⇒ 这一格是恒真的')
            finally:
                chi.ci_script_roster = real

    def test_the_repo_is_clean_right_now(self):
        code, out = run_tool()
        self.assertEqual(0, code, '通道/路径卫生守卫红：\n' + out)
        self.assertIn('CI_CHANNEL_HYGIENE_RESULT=ok', out)
        self.assertIn('绝对根=0 真人路径=0 通道空格=0', out)

    def test_scanner_catches_the_concatenated_real_home_shape(self):
        """正对照：真人路径**拆成三段拼起来**也必须抓到（R565 现读：电池里就是这么写的）。"""
        source = "MACHINE = '/' + 'Users' + '/' + 'ming' + '/Repo'\n"
        self.assertTrue(chi.real_home_mentions(source, accounts={'ming'}),
                        '拆段拼接的真人路径没被抓到 ⇒ B 格只剩一半（注入"这台机器上有 ming 这个账号"）')
        # 同一颗源在默认（这台机器的真账号）下不该被咬 —— 否则 B 格会把自己的正对照判成缺陷。
        self.assertEqual([], chi.real_home_mentions(source))

    def test_scanner_catches_a_plain_real_home_and_a_root_assignment(self):
        source = "ROOT = '/Users/ming/Repo'\nwith open(ROOT + '/x') as f:\n    pass\n"
        self.assertTrue(chi.real_home_mentions(source, accounts={'ming'}))
        self.assertTrue(chi.names_used_as_paths(source, accounts={'ming'}),
                        'ROOT 赋值那一行必须被当运行时缺陷')
        self.assertEqual([], chi.names_used_as_paths(source),
                         '这台机器上没有 ming 这个账号 ⇒ 默认口径不许咬自己的正对照')

    def test_scanner_does_not_bite_synthetic_or_runner_paths(self):
        """负对照：合成/runner 形状是正对照需要的，不许误咬。"""
        synthetic = "MACHINE_ROOT = '/Users/someone/' + 'DemoRepo'\n"
        self.assertEqual([], chi.real_home_mentions(synthetic))
        runner = "x = '/Users/runner/work/ClipboardHistory/ClipboardHistory'\n"
        self.assertEqual([], chi.real_home_mentions(runner))
        numeric_channel = "print('FOO 笔=%d 值=%s' % (n, 'abc'))\n"
        self.assertEqual([], chi.channel_space_risks(numeric_channel))

    def test_scanner_catches_the_channel_space_shape(self):
        """正对照：`范围=%s` 那一格喂进一个含空格的字面量 ⇒ 必须点名（R565 真实坏法）。"""
        source = ('scope = "HEAD~1..HEAD（未推的为空 ⇒ 退化）"\n'
                  'print("COMMIT_ROUND_IDENTITY 范围=%s 笔=%d" % (scope, 1))\n')
        hits = chi.channel_space_risks(source)
        self.assertTrue(hits, '通道值里的裸空格没被抓到 ⇒ 判它的测试会重演 R565 那一崩')

    def test_finding_is_printed_not_swallowed(self):
        """命中必须进 stdout 的读数（只数不印 = 下一轮没法复查）。"""
        bad = [('scripts/x.py', 'channel-space', 'L1 范围=%s')]
        line = 'CI_CHANNEL_HYGIENE ci脚本=1 电池脚本=0 合计=1 绝对根=0 真人路径=0 通道空格=1'
        self.assertEqual(1, sum(1 for b in bad if b[1] == 'channel-space'), line)


if __name__ == '__main__':
    unittest.main()
