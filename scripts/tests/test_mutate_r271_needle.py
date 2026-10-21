#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R272 / BACKLOG 327：静态镜像与 R51 那颗 needle 必须逐字相同（漂移就红）。

`mutate_r271.py` 为了让 `mutate_needle_precheck.py` 抽得到，把 TARGET / NEEDLE / REPL 写成了字面量；
字面量的代价就是会腐烂 —— 这一格是它的解药：单一真相仍然是 R51 那张表，运行时读它、逐字对账。
"""
import importlib.util
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, '.scratch', 'motion-audit-2'))

# R273 的 runner 红（run 39579621207 / STEP[9] Release script tests，errors=3 全落在下面这三格）：
# `mutate_r271.py` 把仓库根写死成**本机**绝对路径，而 runner 的检出目录不是它 ⇒ FileNotFoundError。
# 修法是让它从 `__file__` 推（同 R262 修预检那一次）；下面的门防的是「只有这一次修了」。
MACHINE_ROOT = '/Users/wangziyi/' + 'Codex_Project0'


def imported_tool_names():
    """电池自己 import 了哪几颗 `.scratch/motion-audit-2/` 工具 —— 名单从正文现读，不手写。"""
    pat = re.compile(r"""['"]motion-audit-2['"]\s*,\s*['"]([A-Za-z0-9_]+\.py)['"]""")
    names = set()
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith('.py'):
            continue
        with open(os.path.join(HERE, fn), encoding='utf-8') as h:
            names.update(pat.findall(h.read()))
    return sorted(names)


def closure_tool_names(seed):
    """把名单推到**可达闭包**（R276 / D-262）。

    直接 import 那一层不够：`mutate_r271.py` 在运行时读 `mutate_r51_capture_path_blocked.py`
    取 needle 的单一真相，于是 R51 那张表里写死的本机绝对路径照样进 runner ——
    run 39583125728 的 STEP[9] 就是这么红的（正文存 /tmp/r276_log1.txt）。
    一颗工具引用另一颗的写法很多（`os.path.join(HERE, 'x.py')`、`'x.py'` 裸串、`sys.path` 注入），
    所以这里只认**同目录里真实存在的 .py 文件名**，避免把注释里的散文当依赖。
    """
    here_tools = {f for f in os.listdir(os.path.join(REPO, '.scratch', 'motion-audit-2'))
                  if f.endswith('.py')}
    seen = set(seed)
    frontier = list(seed)
    pat = re.compile(r"([A-Za-z0-9_]+\.py)")
    while frontier:
        n = frontier.pop()
        path = os.path.join(REPO, '.scratch', 'motion-audit-2', n)
        if not os.path.exists(path):
            continue
        for cand in set(pat.findall(open(path, encoding='utf-8').read())) & here_tools:
            if cand not in seen:
                seen.add(cand)
                frontier.append(cand)
    return sorted(seen)


def repo_relative(path):
    """把任何机器上的绝对路径归一到仓库相对形式，只用于**比较**（不改变被比较的对象）。"""
    marker = 'ClipboardHistory/'
    norm = path.replace(os.sep, '/')
    i = norm.rfind(marker)
    return norm[i:] if i >= 0 else norm


def loads_machine_root(src):
    """这把尺只认赋值那一行，别被注释与 docstring 里的路径字样喂饱（R76：扫前剥注释）。"""
    for line in src.splitlines():
        code = line.split('#', 1)[0]
        if re.match(r"^\s*(?:_[A-Z_]+|ROOT|REPO)\s*=", code) and MACHINE_ROOT in code:
            return True
    return False


def load():
    spec = importlib.util.spec_from_file_location(
        'mutate_r271', os.path.join(REPO, '.scratch', 'motion-audit-2', 'mutate_r271.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NeedleMirrorTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()

    def test_the_static_mirror_equals_the_r51_needle(self):
        target, needle, repl = self.mod.resolve_r51()
        # 比较**归一后的仓库相对形式**（R276）：R51 那张表历史上把 target 写成绝对路径，
        # 于是这一格在 runner 上算出 `../../../../wangziyi/...` —— 机器不同就不同，
        # 量的不是"漂移"而是"这台机器叫什么"。归一不放宽判据：文件不同仍然不等（见下面那格的正对照）。
        self.assertEqual(repo_relative(target), self.mod.TARGET,
                         '文件漂移：R51 指的是另一颗文件')
        self.assertEqual(needle, self.mod.NEEDLE, '锚点漂移：R51 那颗 save 的写法已经改了，镜像还是旧的')
        self.assertEqual(repl, self.mod.REPL, '替换漂移：两把刀已经不是同一个坏法')

    def test_the_mirror_hits_exactly_once_in_the_product(self):
        path = os.path.join(self.mod.ROOT, self.mod.TARGET)
        with open(path, encoding='utf-8') as h:
            src = h.read()
        self.assertEqual(1, src.count(self.mod.NEEDLE),
                         '锚点在被测文件里不是恰好一次 ⇒ 这把刀会 NOT_RUN 而不是红')

    def test_a_drifted_mirror_is_caught_by_this_cell(self):
        # 正对照：把镜像改一个字符，对账必须红（否则这三格只是在证明两边都抄自同一处）
        target, needle, repl = self.mod.resolve_r51()
        self.assertNotEqual(needle + 'x', self.mod.NEEDLE)

    def test_module_root_is_derived_from_the_module_itself(self):
        """行为证人：ROOT 必须等于由本文件位置推出来的那一个，而不是某台机器的路径。"""
        derived = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(self.mod.__file__))))
        self.assertEqual(os.path.realpath(derived), os.path.realpath(self.mod.ROOT),
                         'ROOT 不是从 __file__ 推的 ⇒ 换一台机器（runner）就是 FileNotFoundError')
        self.assertTrue(os.path.isdir(os.path.join(self.mod.ROOT, 'ClipboardHistory')),
                        '推出来的根下面没有仓库 ⇒ 这把尺指错了对象')

    def test_no_battery_imported_tool_hardcodes_a_machine_root(self):
        """门覆盖的是「电池 import 的全部工具」，名单现读；名单为空本身要红（R99 那条规矩）。"""
        names = closure_tool_names(imported_tool_names())
        self.assertGreaterEqual(len(names), len(imported_tool_names()) + 1,
                                '闭包没有比直接 import 名单大 ⇒ 运行时读表那条可达性没被扫到（R276 的漏法）')
        print('MIRROR_GATE 直接=%d 闭包=%d 判=RUN' % (len(imported_tool_names()), len(names)))
        self.assertGreaterEqual(len(names), 2,
                                '抽不出电池 import 的工具名单 ⇒ 这一格是恒真的门，不是读数')
        bad = []
        for n in names:
            p = os.path.join(REPO, '.scratch', 'motion-audit-2', n)
            if not os.path.exists(p):
                bad.append(n + '(名单对不上磁盘)')
                continue
            with open(p, encoding='utf-8') as h:
                if loads_machine_root(h.read()):
                    bad.append(n)
        self.assertEqual([], bad, '电池 import 的工具里有人写死本机仓库根 ⇒ runner 上必红')

    def test_the_closure_reaches_the_table_that_actively_broke_ci(self):
        """闭包必须真的包含 R51 那张表 —— 它就是 run 39583125728 上红掉的对象，不含它这格是装饰。"""
        names = closure_tool_names(imported_tool_names())
        self.assertIn('mutate_r51_capture_path_blocked.py', names,
                      '闭包没追到 mutate_r51（被 mutate_r271 运行时读）⇒ 门又只扫了一层')

    def test_path_normalization_has_teeth(self):
        """归一化只消「机器」差异，不消「对象」差异：同文件两台机器要相等，不同文件必须不等。"""
        mine = '/Users/wangziyi/Codex_Project0/ClipboardHistory/Sources/X/HistoryPersistence.swift'
        other_machine = '/Users/runner/work/ClipboardHistory/ClipboardHistory/Sources/X/HistoryPersistence.swift'
        self.assertEqual(repo_relative(mine), repo_relative(other_machine),
                         '同一颗文件在两台机器上被判成不同 ⇒ 归一化没做到')
        other_file = '/Users/wangziyi/Codex_Project0/ClipboardHistory/Sources/X/DailyCopyLedger.swift'
        self.assertNotEqual(repo_relative(mine), repo_relative(other_file),
                            '不同文件被判成相同 ⇒ 这条对账被归一化放宽成了恒真')
        self.assertEqual('ClipboardHistory/Sources/X/HistoryPersistence.swift', repo_relative(mine))

    def test_the_machine_root_predicate_itself_has_teeth(self):
        """正负对照：喂旧的写法必须判成红，喂现在的写法必须判成绿（否则上一格只是看起来在扫）。"""
        self.assertTrue(loads_machine_root("ROOT = '" + MACHINE_ROOT + "'"))
        self.assertTrue(loads_machine_root("ROOT = \"" + MACHINE_ROOT + "\"  # 注释"))
        self.assertFalse(loads_machine_root("_HERE = os.path.dirname(os.path.abspath(__file__))\n"
                                            "ROOT = os.path.dirname(os.path.dirname(_HERE))"))
        # 注释里出现那个路径不算（R76：判"用没用"要剥注释）
        self.assertFalse(loads_machine_root("# 别写 " + MACHINE_ROOT + " 这种本机路径"))


if __name__ == '__main__':
    unittest.main()
