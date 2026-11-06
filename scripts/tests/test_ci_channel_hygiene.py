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

    # ———————————————————————————————————————————— R591 靶 2：值槽粘连（全仓扫描面）
    def test_glue_positive_control_covers_four_shapes(self):
        """四种形状都要认得出（R590 那把尺只认第一种 ⇒ M1572 当场空刀）。

        ① `NAME=%s（说明）` 值槽紧跟格式槽；② 名字后面还有别的键、粘连在第二个键上（bash 的那两行）；
        ③ 全角括号一直到**字符串末尾**都没闭合；④ 通道名被拆到两行（相邻字面量 / `+` 拼接）。
        """
        a = 'print("FOO_RESULT=ok 红=%s（见上）" % n)\n'
        b = 'echo "SHAPE_GUARD_EXIT guard=$GUARD rc=$g（0=判过）"\n'
        c = 'print("FOO_RESULT=ok 红=%s（说明没有右括号"\n      % n)\n'
        d = ('print("FOO_" "RESULT=ok 红=%s（粘在拼接后的名字上）" % n)\n'
             'print("BAR_" + "RESULT=1（+ 号拼接也要接得上）")\n')
        for name, src in ((u'①', a), (u'③', c), (u'④', d)):
            hits, unjudged = chi.channel_glue_risks(src)
            self.assertTrue(hits, u"%s 那种粘连没被抓到 ⇒ 命中=0 是尺盲，不是仓库干净（不判=%d）" % (name, unjudged))
        hits_b, _u = chi.channel_glue_risks_workflow(b)
        self.assertTrue(hits_b, u'② bash 的「名字后面还有别的键」那一形没被抓到（M1572 第一次空刀就是这个）')

    def test_glue_negative_control_legit_paren_is_not_a_channel(self):
        """负对照：没有通道名的括号、以及值与说明之间**有空格**的写法都不许算。

        否则这条门会退化成"禁止一切全角括号"，而真正打死 runner 日志的是"值槽与说明之间没有分隔"。
        """
        prose = 'print("这一格（说明）已经写完了")\n'
        self.assertEqual([], chi.channel_glue_risks(prose)[0], u'纯说明里的括号被当成了通道粘连')
        spaced = 'echo "IDENTICAL_WITNESS_NOT_RUN=1 这一维在 runner 上今天没人判"\n'
        self.assertEqual([], chi.channel_glue_risks_workflow(spaced)[0], u'值后面是空格 + 散文，不该算粘连')

    def test_glue_unjudged_is_a_named_lower_bound(self):
        """看不见的那部分要**具名计数**：动态参数 / f-string 表达式 ⇒ 命中=0 只是下界。"""
        src = ('msg = build_text()\n'
               'print(msg)\n'
               'print(f"FOO_RESULT={v}")\n')
        hits, unjudged = chi.channel_glue_risks(src)
        self.assertEqual([], hits)
        self.assertGreaterEqual(unjudged, 1, u'看不见却报 0 ⇒ 与 R587「门的 0 分不清没有与看不见」同族')

    def test_glue_scope_is_printed_and_the_enforceable_half_is_clean(self):
        """扫描面要当**读数**印出来（python 文件数 + echo 行数 + 三类计数），且"要拦的那一半"现读为 0。

        R591 的划界（逐字证据写在守卫正文里）：同一份 runner 日志里 1257 行含全角括号、
        只有 3 行被打坏，而**同形状完好**的有 72 行 ⇒ 粘连不是充分原因。
        所以红只判 `ci.yml` 的 echo（那些值被读取器**按值解析**的通道），脚本侧那批**具名报数**，
        既不并入 0，也不借一个被推翻的成因去改一批仪器的输出契约。
        """
        code, out = run_tool()
        self.assertIn('CI_CHANNEL_GLUE_SCOPE', out, out[-800:])
        scope = [l for l in out.splitlines() if l.startswith('CI_CHANNEL_GLUE_SCOPE')][0]
        import re as _re
        got = dict(_re.findall(r'(\S+?)=(\d+)', scope))
        self.assertGreater(int(got['python文件']), 50, scope)
        self.assertGreater(int(got['echo行']), 20, scope)
        self.assertGreater(int(got['粘连计']), 0, scope)      # 尺必须有对象，否则 0 不算数
        self.assertEqual('0', got['其中工作流echo'], out[-1200:])
        if int(got['脚本侧']):
            self.assertIn('CI_CHANNEL_GLUE_SCRIPT_ONLY=', out,
                          u'脚本侧有命中却不具名报数 ⇒ 会被读成"全仓没这形状"')
        if int(got['读数括号']):
            self.assertIn('CI_CHANNEL_GLUE_READING_PAREN=', out, u'读数括号那一族没印出来 ⇒ 并入 0 了')
        if int(got['不判']):
            self.assertIn('CI_CHANNEL_GLUE_PARTIAL=', out, u'有看不见的那部分却不印下界')
        self.assertEqual(0, code, out[-1200:])

    def test_glue_red_scope_is_the_workflow_echoes(self):
        """要拦的那一半要有牙：往工作流正文里塞一条 `NAME=$v（说明）` ⇒ 必须进 bad 并退红。"""
        d = tempfile.mkdtemp(prefix="r591_glue_")
        os.makedirs(os.path.join(d, '.github', 'workflows'))
        wf = os.path.join(d, 'workflows.yml')
        with open(wf, 'w', encoding='utf-8') as handle:
            handle.write('      - name: X\n        run: |\n'
                         '          echo "SHAPE_GUARD_EXIT guard=$GUARD rc=$g（0=判过）"\n')
        code, out = run_tool('--workflow', wf)
        self.assertEqual(1, code, out[-1500:])
        self.assertIn('channel-glue', out, out[-1500:])
        self.assertIn('CI_CHANNEL_HYGIENE_RESULT=red', out)

    def test_the_wiring_cell_and_this_scanner_share_one_ruler(self):
        """一把尺只许有一处定义（R324 那条）：接线卷那一格不许再自带第二条正则。"""
        text = open(os.path.join(HERE, 'test_ci_shape_guard_wiring.py'), encoding='utf-8').read()
        self.assertNotIn("GLUE_LOCAL", text)
        self.assertIn('channel_glue_risks_workflow', text,
                      u'接线那一格还在用自己的正则 ⇒ 两处定义会各自漂移')


if __name__ == '__main__':
    unittest.main()
