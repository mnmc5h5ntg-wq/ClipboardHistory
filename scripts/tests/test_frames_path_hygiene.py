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


if __name__ == u'__main__':
    unittest.main()
