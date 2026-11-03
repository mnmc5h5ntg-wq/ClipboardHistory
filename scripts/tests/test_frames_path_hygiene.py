# -*- coding: utf-8 -*-
"""R227 / BACKLOG 253 的守卫：判据与脚本里**不许出现写死的轮次帧目录**。

来历（一句话）：`test_surface_left_axes.py` 有两格真帧对照把证据押在
`/tmp/` + `shots_r` + 某一轮的轮次号 上 —— runner 上那个目录从来不存在，本机也随时会被清掉，
于是"这一格从没跑过"穿着 skip 的衣服混过每一轮报表。skip 有两种成因，处置相反：
环境缺席（要能被点名）与证据路径腐烂（要修路径）。这一支钉的是第二种。

三条各自承重，缺一格就是假绿：
  ① 真扫：`scripts/**/*.py` 的非注释行里出现该字面串 ⇒ 红，并点名文件与行号；
  ② 正对照：把一条含该字面串的假行喂给扫描器，**必须**被报出来
     （没这一格，①可以因为正则写坏而永远零命中还打绿 —— 本仓库为此记过不止一次）；
  ③ 负对照：`/tmp/shots-ci`（CI 里那个由步骤自己 mkdir 的固定目录，合法的）不许被报，
     以及**纯注释行**不许被报（守卫引用自己修过的历史时不该自咬 —— R88 那一族）。
"""
from __future__ import annotations

import io
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 仓库里的 scripts/
# 字面串由片段拼出来：这一支自己扫描自己，把完整串写进源码就会被自己抓到（②的形状）。
BAD_PREFIX = u'/' + u'tmp/' + u'shots_' + u'r'
BAD_RE = re.compile(re.escape(BAD_PREFIX) + u'[0-9]')


# R565 补的第二支：脚本**自己的仓库根常量**不许写死机器路径。
# 来历：R564 新加的 `scripts/commit_round_identity.py` 把 ROOT 写成
#   '/' + 'Users/' + 'wangziyi/' + 'Codex_Project0'（本机绝对路径）⇒ runner 上那个目录不存在，
#   `subprocess.run(cwd=ROOT)` 直接抛异常 ⇒ STEP[9] 电池红、STEP[10]-[14]（含帧基线名册门）整段
#   skipped，两跑的 CI 信号全被带走。上面那支只盯 `/tmp/shots_rNN`，看不见这一族。
# 只盯**根常量**这一种形状：`test_mutate_r271_needle.py` 里那些合成路径是测试输入（合法的靶），
#   docstring 里引用历史也是合法的 —— 抓到它们就等于把守卫变成噪音。
# R565 补：这一支按**形状**判，不按"某个真用户名"判。
# 从前它把模式抄成一个真用户名（`'/' + 'Users' + '/' + 'wangziyi'`）—— 于是换一个人的机器、
# 或者写死的其实是别人的目录，它就抓不到：判据的靶比它要防的缺陷窄。现在 `= "/Users/<任何名字>/…"`
# 一律算，由 `__file__` 推的那一种不匹配（它不是字面量开头）。
# 隐私那一半交给 `scripts/ci_channel_hygiene.py` 的 B 格（它按"这台机器上真存在的账号"判），
# 两支各判一件事：这一支判"换一台机器只能报错"，那一支判"把别人的家目录写进仓库"。
MACHINE_ROOT_FRAGMENT = '/Users/someone'          # 只给正/负对照当样本用，不参与模式
ROOT_CONST_RE = re.compile(r'^\s*(?:ROOT|REPO_ROOT|repo_root|REPO|[A-Z_]*ROOT)\s*=\s*[\'"]'
                           r'/(?:Users|home)/')


def scan_root_lines(lines):
    hits = []
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith(u'#'):
            continue
        if ROOT_CONST_RE.search(line):
            hits.append((i, line.rstrip()))
    return hits


def scan_tree_root(scripts_dir):
    offenders = []
    for base, _dirs, files in os.walk(scripts_dir):
        for name in sorted(files):
            if not name.endswith(u'.py'):
                continue
            path = os.path.join(base, name)
            text = io.open(path, encoding='utf-8', errors='replace').read()
            hits = scan_root_lines(text.splitlines())
            if hits:
                rel = os.path.relpath(path, os.path.dirname(scripts_dir))
                offenders.append((rel, hits))
    return offenders


def scan_lines(lines):
    """返回 [(行号, 行)] —— 只看非注释行；注释行是"引用历史"，不是"依赖路径"。"""
    hits = []
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith(u'#'):
            continue
        if BAD_RE.search(line):
            hits.append((i, line.rstrip()))
    return hits


def scan_tree(scripts_dir):
    offenders = []
    for base, _dirs, files in os.walk(scripts_dir):
        for name in sorted(files):
            if not name.endswith(u'.py'):
                continue
            path = os.path.join(base, name)
            text = io.open(path, encoding='utf-8', errors='replace').read()
            hits = scan_lines(text.splitlines())
            if hits:
                rel = os.path.relpath(path, os.path.dirname(scripts_dir))
                offenders.append((rel, hits))
    return offenders


class FramesPathHygieneTests(unittest.TestCase):
    def test_no_hardcoded_round_frame_directory(self):
        offenders = scan_tree(ROOT)
        self.assertEqual(
            [], offenders,
            u'判据/脚本里写死了轮次帧目录（这一格会在 runner 上永远 skip、本机随时失效）：'
            + u'；'.join(u'%s:%s' % (rel, [n for n, _ in hits]) for rel, hits in offenders)
            + u' ⇒ 改由 CLIPBOARD_HISTORY_UI_SHOTS 派生，或读仓库内的基线帧')

    def test_scanner_catches_the_shape_it_is_supposed_to_catch(self):
        """正对照：坏写法必须被点名，否则①的零命中毫无意义。"""
        bad = u"SHOTS = '" + BAD_PREFIX + u"211'"
        hits = scan_lines([u'# 上一版指 ' + bad, bad])
        self.assertEqual(1, len(hits), u'扫描器抓不到写死的轮次帧目录 ⇒ 这把尺是空的')
        self.assertEqual(2, hits[0][0], u'抓到了但行号不对（注释行不该算，代码行要算）')

    def test_scanner_does_not_bite_legitimate_or_commented_lines(self):
        """负对照：CI 那个固定目录、以及注释里的历史引用，都不许被报。"""
        legit = u"run('mkdir -p /tmp/shots-ci && python3 x.py')"
        comment = u'# R212 那版指 ' + BAD_PREFIX + u'211，在 runner 上先撞上 FRAME_DIR_MISSING'
        self.assertEqual([], scan_lines([legit, comment, u'']))


class MachineRootHygieneTests(unittest.TestCase):
    def test_no_script_uses_a_hardcoded_machine_root(self):
        offenders = scan_tree_root(ROOT)
        self.assertEqual(
            [], offenders,
            u'这些脚本把自己的仓库根常量写成机器绝对路径（runner 上目录不存在 ⇒ 脚本抛异常、'
            u'CI 那一步整段红/跳过）：'
            + u'；'.join(u'%s:%s' % (rel, [n for n, _ in hits]) for rel, hits in offenders)
            + u' ⇒ 用 os.path.dirname(os.path.abspath(__file__)) 推出来')

    def test_scanner_catches_the_root_shape_it_is_supposed_to_catch(self):
        """正对照：这一族必须被点名，否则上面那格的零命中毫无意义。"""
        bad = u'ROOT = "' + MACHINE_ROOT_FRAGMENT + u'/Codex_Project0"'
        hits = scan_root_lines([u'# 上一版 ' + bad, bad])
        self.assertEqual(1, len(hits), u'扫描器抓不到写死的仓库根 ⇒ 这把尺是空的')
        self.assertEqual(2, hits[0][0], u'抓到了但行号不对（注释行不该算，代码行要算）')
        # 形状判的第二半：**别人的**用户名（不是这台机器的账号）也必须被抓 —— 从前按真用户名抄，
        # 这一条是整个洞（换一台机器、或写死的是别人的目录，尺就哑）。
        other = u'REPO_ROOT = "/home/anyone/Repo"'
        self.assertEqual(1, len(scan_root_lines([other])),
                         u'按形状判没做到 ⇒ 模式还是绑在某个具体用户名上')

    def test_scanner_does_not_bite_synthetic_paths_or_comments(self):
        """负对照：测试里的合成路径靶、由 __file__ 推出来的根、注释里的历史引用，都不许被报。"""
        legit_derived = u"ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))"
        synthetic = u"MINE = '" + MACHINE_ROOT_FRAGMENT + u"/Codex_Project0/Sources/X.swift'"
        comment = u'# R564 那版写 ' + MACHINE_ROOT_FRAGMENT + u'/Codex_Project0 ⇒ runner 上炸'
        self.assertEqual([], scan_root_lines([legit_derived, synthetic, comment, u'']))


if __name__ == u'__main__':
    unittest.main()
