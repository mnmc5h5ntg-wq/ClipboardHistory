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
        self.assertTrue(ran and skipped,
                        '内层没有结论行（Ran / OK (skipped=N)）⇒ 无从对账，不许把"没解析到"读成"没缺席"')
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
        print('SKIP_ROSTER 键=%s 类=%s 内层Ran=%s 汇总skipped=%s 解析=%d 名单外=%s 名册未跳=%s'
              % (key, klass, ran[-1], skipped.group(1), len(actual), extra or u'无', gone or u'无'), flush=True)
        self.assertEqual([], extra,
                         '名单外出现 skip（%s）⇒ 有人新增了一格会跳的判据却没登记它替谁承重（331）' % extra)
        self.assertEqual([], gone,
                         '名册说这一台会跳而实际没跳（%s）⇒ 名册过期，过期比没名册更坏（R88 那条）' % gone)


if __name__ == '__main__':
    unittest.main(verbosity=2)
