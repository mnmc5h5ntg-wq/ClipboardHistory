#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R287 / BACKLOG 331：同一版本的脚本电池在两台机器上 skip 的**名单**，按机器键双向对账。

为什么这一卷存在：R276 现读到本机 `Ran 521 / OK (skipped=4)` 而 runner `Ran 519 / FAILED (failures=1, skipped=1)`，
两台的缺席集合几乎**不相交** —— 本机跳的是四格帧通道缺席，runner 跳的是端到端启动冒烟（仓库根没有已构建的 .app）。
这不是"环境不同所以正常"就翻篇的事（D-255 同族）：没有任何名册登记过"谁在替谁承重"，
于是新增一格会 skip 的判据时，没人能回答"它在 runner 上会不会变成一朵没登记的红"。

前两版为什么回退（都记在 331 的追记里，这里不再重复走）：
· 静态扫源码预测谁会 skip —— 跨行匹配会把后面格子的 skip 记到前面格子头上，且 skip 的形状至少三种
  （装饰器 / 语句级 / 藏在 helper 里），对"谁会 skip"没有分辨力。
· 观测式第一版按 marker 切 —— `unittest -v` 把格子 docstring 打在第一行、把 `... skipped '理由'` 落在另一行，
  行首不是 `test_x (模块.类)`，于是拿不到 id（我自己写的正对照格把这条 bug 抓了出来）。

这一版的形状因此是：**按「表头行 + 结果行」配对归属**，再加一条**恒等式闸门** ——
解析出的 id 数必须等于内层汇总行 `OK (skipped=N)` 的 N 减去观察者自己那一格；不相等就红
（"少认一格"正是上一版的红法）。观察者用 `SKIP_ROSTER_NESTED=1` 防递归，
而"排除观察者恰好 1 格"本身要能被红，不许是沉默的减法。
"""
import io
import os
import re
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SUITE_DIR = os.path.join('scripts', 'tests')
NESTED_ENV = 'SKIP_ROSTER_NESTED'
OBSERVER_ID = 'test_the_roster_matches_what_this_machine_actually_skips'

HEADER = re.compile(r'^(test\w+) \(([\w.]+)\)')
RESULT = re.compile(r'\.\.\. (ok|skipped|fail|expected failure|unexpected success|error)')
SUMMARY = re.compile(r'^Ran (\d+) tests?', re.M)
SKIPPED_SUMMARY = re.compile(r'OK \(skipped=(\d+)\)')
# R558 / 634：结论行有**两种**形状。从前只认 `OK (…)` 那一种，于是内层红的时候
# 这一格把「有红」读成「没有结论行」—— 现在两种都认，各自说各自的话。
FAILED_SUMMARY = re.compile(r'^FAILED \(([^\n]*)\)', re.M)
RED_NAMES = re.compile(r'^(?:FAIL|ERROR): (\S+)', re.M)


def inner_summary_verdict(text):
    u"""把内层那一卷的输出分成**三种**读数（R558 / BACKLOG 634 的形状）。

    从前只有两种（「有 `OK (skipped=N)`」与「没有结论行」），于是「内层自己红了」这一种被并进第二类，
    而它的正文还说"没跑完" —— 一个成因在红名册里记成两朵，还替那朵红做伪证。
    返回值：`('no-summary', '')` / `('inner-red', 红名串)` / `('ok', 内层 skipped 数)`。
    """
    ran = SUMMARY.findall(text)
    ok = SKIPPED_SUMMARY.search(text)
    failed = FAILED_SUMMARY.search(text)
    if not (ran and (ok or failed)):
        return 'no-summary', u''
    if failed:
        return 'inner-red', u'、'.join(RED_NAMES.findall(text)) or u'未解析到'
    return 'ok', ok.group(1)

# discover 会把 scripts/tests 放进 sys.path，但 `python3 -m unittest scripts.tests.X` 这种点号形式不会 ——
# 显式加一次，免得同一卷换一种调用方式就换一种身份（那正是 331 要避免的两种成因混成一个数）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from test_surface_left_axes import GITHUB_RUNNER_KEY, machine_key      # discover 会把 scripts/tests 放进 sys.path
except Exception:                                                          # 导入不到 ⇒ 这一卷必须红，不许静默换一套身份
    GITHUB_RUNNER_KEY = None
    machine_key = None


# 名册：**按机器类**给（R276 现读）。每一项都要能说出为什么缺席；名单外出现 skip 也要红。
ROSTER = {
    'local': {
        'test_the_real_shots_pair_at_least_as_well_as_the_registered_floor': '帧通道未给 CLIPBOARD_HISTORY_UI_SHOTS',
        'test_every_real_pair_clears_the_floor_or_is_named_nonflat': '帧通道未给 CLIPBOARD_HISTORY_UI_SHOTS',
        'test_ci_exit_matches_this_machines_registered_profile': '帧目录不在盘上（本机没重捕帧时不承重）',
        'test_working_frames_still_satisfy_the_three_relations': '帧目录不在（本机 NOT-RUN）',
        # R435：本机 /tmp 被清掉时，验证链日志不在盘上 ⇒ 这一格合法跳过（runner 那一侧
        # 早就登记过；本机这边以前一直有文件所以没露面）。文件在就真跑，不承重时署名。
        'test_the_round_chain_log_reads_as_the_ledger_claims':
            '本机 /tmp 的验证链日志被清掉时不承重（文件在就真跑）',
    },
    'github-runner': {
        # 这一行原来是 R276 的**外推**（那一次只读到 `skipped=1` 这个数，没读到是谁），
        # 外推填的是 `test_app_launches_and_terminates_cleanly`。它被 runner 自己两跑驳回：
        # run 39608106160（41e1e66）与 39607521077（3403a78）都打
        # `SKIP_ROSTER 键=github-runner … 名单外=['test_built_bundle_carries_no_app_delegate_stub']
        #  名册未跳=['test_app_launches_and_terminates_cleanly']` —— 跳的是端到端读包那一格
        # （`时间剪史.app` 不在 runner 的仓库根），而启动冒烟那一格在 runner 上是**跑过的**。
        # 现在填的是读来的名字，不是猜的；两跑同读才签（R83：单次 runner 读数不配签字）。
        'test_built_bundle_carries_no_app_delegate_stub':
            'runner 的仓库根没有已构建的 时间剪史.app（run 39608106160 与 39607521077 两跑同读）',
        # R309 新加的那格「拿真产物日志对账」在 runner 上必然缺席：/tmp/r308_chain.log 是本机
        # 验证链留下的，runner 的 /tmp 里没有它。名字是 **runner 自己点出来的**，不是我猜的：
        # run 39965996188（340452f）STEP[9] 打
        #   名单外=['test_the_round_chain_log_reads_as_the_ledger_claims']
        # ⇒ 这一格在 runner 上不承重（本机仍承重：文件在就真跑）。
        'test_the_round_chain_log_reads_as_the_ledger_claims':
            'runner 的 /tmp 没有本机验证链日志（run 39965996188 点名；本机有文件时不跳）',
        # R566 加的那格「现读真钥匙串必须走身份支」在 runner 上必然缺席：固定签名身份
        # `ClipboardHistory Local Signing` 装在这台 Mac 的登录钥匙串里，runner 上没有它，
        # 所以那一格自己打了具名出口 `SIGN_LIVE_NOT_RUN=no-identity`。
        # 名字是 **runner 自己点出来的**（run 41704430816 / f538d2c 的 STEP[9] 打
        #   名单外=['test_this_machine_actually_takes_the_identity_branch']），不是我猜的；
        # 那一跑同时把 ROSTER 闸门红成 STEP[9] failure —— 门是对的，缺的是登记。
        # 本机仍承重：有身份时真签一次并判 `SIGNATURE_KIND=local` + `Authority=`。
        'test_this_machine_actually_takes_the_identity_branch':
            'runner 的钥匙串没有那个固定身份 ⇒ 具名 SIGN_LIVE_NOT_RUN=no-identity（run 41704430816 点名；本机真跑并判 local）',
    },
}


def machine_class(key):
    if GITHUB_RUNNER_KEY is None:
        raise AssertionError('导不到 GITHUB_RUNNER_KEY ⇒ 这台机器的身份无从判定，不许猜一个类')
    return 'github-runner' if key == GITHUB_RUNNER_KEY else 'local'


def parse_verbose(text):
    """按「表头行 + 结果行」配对：表头开一条记录，直到遇到结果行为止（中间可能是 docstring）。"""
    records = {}
    current = None
    for line in text.split('\n'):
        h = HEADER.match(line)
        if h:
            current = h.group(1)
            # 单行形状：`test_x (模块.类) ... skipped '理由'` —— 没有 docstring 的格子全走这条。
            # 第一版在这里直接 continue，于是这些格子的结果被丢掉：恒等式闸门当场抓到
            # 「内层说 5 格、只解析到 2 格」（正是 R277 预告的那种少认一格的红法）。
            r0 = RESULT.search(line)
            if r0:
                records[current] = r0.group(1)
                current = None
            else:
                records.setdefault(current, 'unknown')
            continue
        if current is None:
            continue
        r = RESULT.search(line)
        if r:
            records[current] = r.group(1)
            current = None
    return records



class TestReadingKeyHygiene(unittest.TestCase):
    """R292 / BACKLOG 341：一台工具不许把自己的读数印成**别人的结论行的键名**。

    为什么这一格值得红：台账生成器普遍用未锚定的 `re.search(r"skipped=(\\d+)")` 去取
    unittest 的结论行 `OK (skipped=4)`。而名册闸门自己那一行印在它**前面**，键名里也带着
    `skipped=` ⇒ 生成器借到的是内层那一卷的数（合法地多一颗观察者自己的防递归 skip），
    于是「外层电池 skipped=4」被写成 5，一路进了五本台账。修法是两边都做：
    闸门那行改叫 `内层skip汇总=`（源头消歧），这一格钉住"以后不许再有 print 用 `skipped=` 当键"。
    """

    KEY = u"skipped="

    def _print_string_constants(self, path):
        import ast
        tree = ast.parse(io.open(path, encoding="utf-8").read())
        out = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "print":
                for sub in ast.walk(node):
                    # 只看字面量本身；注释与 docstring 不算（R76：扫前剥掉不参与判定的文本）
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, str) \
                            and not isinstance(getattr(sub, "_doc", None), str):
                        out.append((sub.lineno, sub.value))
        return out

    def test_no_print_uses_the_unittest_summary_key(self):
        import glob
        offenders = []
        for path in sorted(glob.glob(os.path.join(SUITE_DIR, "*.py"))):
            for line, text in self._print_string_constants(path):
                if self.KEY in text:
                    offenders.append("%s:%d" % (os.path.basename(path), line))
        self.assertEqual([], offenders,
                         u"这些 print 用了 unittest 结论行的键名 `%s` ⇒ 任何未锚定的取数都会借错主语（341）：%s"
                         % (self.KEY, offenders))

    def test_the_guard_itself_has_teeth(self):
        # 正对照：把同一颗尺喂给一段**已知违规**的源码，必须报出来（否则上面那格是恒真式）。
        import tempfile
        src = u"print('X 汇总skipped=%s' % 1)\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as h:
            h.write(src)
            path = h.name
        try:
            hits = [ln for ln, t in self._print_string_constants(path) if self.KEY in t]
        finally:
            os.unlink(path)
        self.assertEqual([1], hits, u"正对照没抓到已知违规 ⇒ 这一格判不了任何东西（341）")

    def test_inner_summary_has_three_readings_not_two(self):
        u"""R558 / BACKLOG 634：内层那一卷的读数必须有**三种**，而且「内层有红」不许落在「没结论行」里。

        旧形状只有 `ran and skipped` 一格布尔：`SKIPPED_SUMMARY` 只认 `OK (skipped=N)`，
        所以内层红了（汇总是 `FAILED (…)`）与内层压根没跑完（连 `Ran` 行都没有）
        得到的是**同一句**「内层没有结论行」。这一格把三种形状并排放进去，
        并把「旧形状确实分不清前两种」一起钉住 —— 否则下一轮有人把它合回去，读数还是绿的。
        """
        ok_text = u'Ran 5 tests\nOK (skipped=2)\n'
        red_text = (u'Ran 5 tests\nFAILED (failures=1, skipped=2)\n\n'
                    u'=====================================================================\n'
                    u'FAIL: test_the_cell (tests.test_demo.DemoTests.test_the_cell)\n'
                    u'---------------------------------------------------------------------\n')
        missing_text = u'... 跑到这里就断了\n'

        self.assertEqual(('ok', u'2'), inner_summary_verdict(ok_text),
                         u'可对账那一格必须取到内层的跳过数')
        state, detail = inner_summary_verdict(red_text)
        self.assertEqual('inner-red', state,
                         u'内层红却被读成「没有结论行」就是 634 本体：这一格必须单独认出来')
        self.assertIn(u'test_the_cell', detail,
                      u'内层红名要原样带出来（%r）⇒ 不带名字就还是替那朵红做伪证' % detail)
        self.assertEqual('no-summary', inner_summary_verdict(missing_text)[0],
                         u'真缺席仍然叫缺席，不许与「内层有红」共用一句话')

        # 旧形状为什么错：同一份「内层有红」的文本，在它眼里与「没结论行」不可分辨。
        self.assertIsNone(SKIPPED_SUMMARY.search(red_text),
                          u'旧的那颗尺在这份文本上取到 None —— 这正是借红的机制')
        self.assertIsNotNone(SKIPPED_SUMMARY.search(ok_text),
                             u'正对照：可对账那份必须取得到数，否则上面三条在比两个 None')


class SkipRosterTests(unittest.TestCase):

    def test_the_roster_matches_what_this_machine_actually_skips(self):
        if os.environ.get(NESTED_ENV) == '1':
            self.skipTest('嵌套防递归：这一格是被观察的那一卷的一部分，不再往下跑一层')
        self.assertIsNotNone(machine_key, '导不到 machine_key ⇒ 331 的机器身份没有来源（不许退回 hostname 自造一套）')
        key = machine_key()
        klass = machine_class(key)
        env = dict(os.environ)
        env[NESTED_ENV] = '1'
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTHONUTF8'] = '1'
        env.pop('SDKROOT', None)
        pr = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', 'discover', '-s', SUITE_DIR, '-v'],
                            cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = pr.stdout.decode('utf-8', 'replace')
        records = parse_verbose(text)
        ran = SUMMARY.findall(text)
        skipped = SKIPPED_SUMMARY.search(text)
        # R558 / BACKLOG 634：原来这一格只写 `assertTrue(ran and skipped, '内层没有结论行…')`。
        # `SKIPPED_SUMMARY` 只认 `OK (…)` 那一种形状，所以内层只要有**任何**一条红，汇总行就是
        # `FAILED (…)` ⇒ `skipped` 取到 None ⇒ 这一格以「内层没有结论行」红。那句话是假的：
        # 结论行在，只是不是 OK。后果有两层 —— ①同一个成因在红名册里记成两朵（runner 三跑实测：
        # sources-cell 那一族 + 这一格，本机 R553/R554/R556 那三次「flake」标签也是同一件事）；
        # ②它替真正的那朵红做伪证，读起来像"探针没跑完"。现在拆成三种读数（`inner_summary_verdict`），
        # 真缺席 ⇒ 具名出口；汇总是 FAILED ⇒ 仍然红，但内层的红名必须原样带出来。
        state, detail = inner_summary_verdict(text)
        if state == 'no-summary':
            self.skipTest('SKIP_ROSTER_INNER_NO_SUMMARY=1 内层连汇总行都没有（键=%s 类=%s）'
                          '⇒ 无从对账。这是**缺席**，要具名，不许读成"没缺席"，更不许读成"通过"。'
                          % (key, klass))
            return
        if state == 'inner-red':
            # 不许把 `skipped=` 原样印进消息（R292 / 341：台账生成器拿未锚定的 `skipped=(\d+)`
            # 取电池的结论行，而这一行印在它前面 ⇒ 借到的是内层那一卷的数）。
            excerpt = FAILED_SUMMARY.search(text).group(0).replace('skipped=', u'跳过了=')
            self.fail('内层那一卷自己是红的 ⇒ 这一格没有可对账的对象，红在内层不在这里。'
                      '汇总行「%s」；内层红名=%s（键=%s 类=%s）。'
                      '这一句从前写成「内层没有结论行」，那是把被观察者的红借成观察者的缺席（634）。'
                      % (excerpt, detail, key, klass))
        actual = sorted(n for n, v in records.items() if v == 'skipped')
        # 恒等式闸门：解析到的 id 数必须等于内层汇总的 skipped 数（观察者那一格在嵌套里也 skip，算在里面）
        self.assertEqual(int(skipped.group(1)), len(actual),
                         '解析到 %d 格 skip，内层汇总说 %s 格 ⇒ 归属漏了（R277 那一版的红法正是少认一格）'
                         % (len(actual), skipped.group(1)))
        # 观察者自己在嵌套那一跑里必然 skip（防递归）—— 它不许混进"名单外"，也不许被沉默减掉：
        # 排除动作本身写成会红的判据（R277 那条：排除观察者恰好 1 格，多一格少一格都红）。
        self.assertEqual(1, actual.count(OBSERVER_ID),
                         '嵌套那一跑里观察者那一格应当恰好 skip 一次，实得 %d 次 ⇒ 防递归失效或归属重了'
                         % actual.count(OBSERVER_ID))
        actual = [n for n in actual if n != OBSERVER_ID]
        expected = set(ROSTER[klass])
        extra = [n for n in actual if n not in expected]
        gone = sorted(expected - set(actual))
        # 字段名不许叫 `skipped=`（R292 / 341）：台账生成器普遍用未锚定的 re.search(r"skipped=(\d+)")
        # 取电池自己的结论行，而这一行印在它前面 ⇒ 借到的是**内层那一卷**的数（合法地多一颗观察者自己的
        # 防递归 skip）。歧义要在源头消掉：读数行的键名与 unittest 的结论行键名不许重名。
        print('SKIP_ROSTER 键=%s 类=%s 内层Ran=%s 内层skip汇总=%s 解析=%d 名单外=%s 名册未跳=%s'
              % (key, klass, ran[-1], skipped.group(1), len(actual), extra or u'无', gone or u'无'), flush=True)
        self.assertEqual([], extra,
                         '名单外出现 skip（%s）⇒ 有人新增了一格会跳的判据却没登记它替谁承重（331）' % extra)
        self.assertEqual([], gone,
                         '名册说这一台会跳而实际没跳（%s）⇒ 名册过期，过期比没名册更坏（R88 那条）' % gone)


if __name__ == '__main__':
    unittest.main(verbosity=2)
