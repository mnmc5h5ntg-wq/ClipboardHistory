#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`scripts/surface_left_axes.py` 的电池（R209 看图那一轮）。

规矩：一把新尺进仓库，必须带"已知答案的对照"，而且**这一支不许自己造对照** ——
它跑的就是尺自带的 `--self-test`（真值表在尺里面，改坏判据会当场红）。
另两格钉的是"不许空对账"：帧不在 ⇒ 必须 NOT_RUN 而不是绿。
"""
import io
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'scripts'))
import surface_left_axes as sla  # noqa E402

try:
    import PIL  # noqa F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
NEEDS_PIL = unittest.skipUnless(HAS_PIL, u'PIL 不可用 ⇒ 这一格造不出帧，记 NOT-RUN（不是通过）')

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, 'scripts', 'surface_left_axes.py')
# 帧目录**不许写死**（R227 / BACKLOG 253）。上一版这里是一个临时捕获目录
# （`/tmp/` + `shots_r` + 某一轮的轮次号），后果分两半：runner 上那个目录从来不存在 ⇒
# 这两格真帧对照在 CI 上永远 skip；本机只是"那个目录还没被 /tmp 清理带走"时才跑。
# 两种"没跑"都穿着 skip 的衣服，报表里看不出区别 —— 而 skip 的两种成因处置相反
# （环境缺席要能被点名；证据路径腐烂要修路径）。
# 现在由**捕获卷同一个环境变量**给；取不到就 skip，但 skip 文本必须说清找的是哪个通道。
# 这条规矩由 `test_frames_path_hygiene.py` 钉住（写死的轮次帧目录 = 红）。
SHOTS = (os.environ.get('CLIPBOARD_HISTORY_UI_SHOTS') or '').strip()
SHOTS_NOTE = SHOTS if SHOTS else u'未给 CLIPBOARD_HISTORY_UI_SHOTS'



def run(*args, **kw):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    env.update(kw.pop('env', {}))
    p = subprocess.run([sys.executable, SCRIPT] + list(args), cwd=ROOT, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


@NEEDS_PIL
class SelfTruthTableTests(unittest.TestCase):
    def test_self_test_passes_and_names_every_control(self):
        code, out = run('--self-test')
        self.assertEqual(0, code, u'尺的自带真值表红了：\n%s' % out)
        for label in (u'正对照·今天的样子', u'反对照·药丸只往右缩', u'反对照·月份行换了一条轴',
                      u'反对照·网格越过文字右缘', u'反对照·全空帧'):
            self.assertIn(label, out, u'真值表里少了这一格：%s' % label)
        self.assertIn('LEFT_AXIS_SELFTEST ok', out)

    def test_the_negative_controls_actually_go_red(self):
        """正对照不许是唯一被跑过的那一侧：逐格读 SELFTEST 行的"实得"。"""
        _, out = run('--self-test')
        rows = [l for l in out.splitlines() if l.startswith(u'SELFTEST')]
        self.assertGreaterEqual(len(rows), 7,
                              u'SELFTEST 行=%d，至少要有正/反各一组' % len(rows))
        reds = [l for l in rows if u'实得=红' in l]
        self.assertGreaterEqual(len(reds), 5,
                              u'反对照必须各自红，实红 %d：\n%s' % (len(reds), out))
        for code in (u'ASYMMETRIC', u'OFF_AXIS', u'GRID_PAST_TEXT', u'NOT_RUN'):
            self.assertIn(code, out, u'少了一类坏法：%s' % code)


class RealFrameTests(unittest.TestCase):
    """在**真帧**上跑尺（不带 --ci），期望由这台机器自己登记的那一行推导（R233）。

    与 `CiExitTests` 的分工：那一格判 `--ci` 的出口处置，这一格判尺在真产物上有没有
    把四条关系各自报数 —— 纯文本正文是这四条关系**唯一**逐条打数的地方，删掉它就等于
    把"尺读没读到对象"从账上抹了。
    """

    @unittest.skipUnless(os.path.isdir(SHOTS), u'帧目录不在（%s）⇒ 这一格本机 NOT-RUN' % SHOTS_NOTE)
    @NEEDS_PIL
    def test_working_frames_still_satisfy_the_three_relations(self):
        key = machine_key()
        if key not in CI_EXPECTATIONS:
            self.fail(u'未登记的机器：解析出 %s=%s ⇒ 这一格必须红（不许静默通过、也不许改成 skip）。'
                      u'名册里已有：[%s]。补行的依据是**这台机器自己打的** LEFT_AXIS_VERDICT 结论行'
                      u'与逐颗 NOT_RUN / 规则行，不是别人的输出。'
                      % (MACHINE_KEY_ENV, key, u' | '.join(sorted(CI_EXPECTATIONS))))
        code, out = run('--shots', SHOTS)
        want = plain_expectation_from_row(CI_EXPECTATIONS[key])
        got = parse_plain_profile(out)
        self.assertEqual(want[u'exit_code'], code,
                         u'exit 与推导对不上（期望 %d 实得 %d）；这一格的处置由 hard/not_run 两轴决定：\n%s'
                         % (want[u'exit_code'], code, out))
        self.assertEqual([], diff_plain_profile(want, got),
                         u'机器=%s（%s）纯文本画像不匹配：\n%s\n原输出：\n%s'
                         % (key, CI_EXPECTATIONS[key][u'provenance'],
                            u'\n'.join(diff_plain_profile(want, got)), out))
        print(u'PLAIN_PROFILE_OK 机器=%s verdict=%s 问题=%d 真红=%d 盲区=[%s] 规则行=[%s] 帧目录=%s'
              % (key, got[u'verdict'], got[u'problems'], len(got[u'hard']),
                 u', '.join(got[u'blind']), u', '.join(got[u'tags']), SHOTS))

    @NEEDS_PIL
    def test_missing_frames_are_not_run_not_green(self):
        empty = os.path.join(ROOT, '.scratch', 'motion-audit-2', '__no_such_frames__')
        os.makedirs(empty, exist_ok=True)
        self.addCleanup(lambda: os.path.isdir(empty) and os.rmdir(empty))
        code, out = run('--shots', empty)
        self.assertEqual(1, code, u'空目录必须红，不能给绿：\n%s' % out)
        self.assertIn('LEFT_AXIS_VERDICT bad', out)
        self.assertIn(u'NOT_RUN', out)


# ---------------------------------------------------------------------------
# R231 / BACKLOG 259：`--ci` 那一格的期望改成**按机器 × 按探针**切片的表
# ---------------------------------------------------------------------------
# 来历：253 把帧目录接进电池那一步以后，本格的 `verdict=ok` 断言在 runner 上连红两跑
# （847ab2b → run 39315666980，写账时 conclusion=failure）。红的是**我的断言**，不是产品：
# runner 自己打的是 `verdict=skipped hard=0 not_run=4 missing_frames=0 probes=7`，四条 NOT_RUN
# 由尺逐颗点名（浮层/选中行药丸 cause=bg-not-flat；统计/统计行、统计/月份行、统计/热图网格
# cause=no-ink，全带 bg=(50, 50, 50)），而 missing_frames=0 ⇒ 帧到了、尺也真跑了。
# 拿本机的能力当 runner 的地板 = 一把尺去判另一台机器（R154 / R87 那一族）。
# 但反过来把 "skipped 也算过" 写进判据也不许 —— 这一步就变成永远绿的装饰（R210 立这两格的原意）。
# 所以处置是一张表：每台机器登记**它自己该看到的完整画像**（verdict + 三个计数 + 逐颗名单）。
# 画像不匹配就红；未登记的机器也红，并把解析出来的键打进输出，让人知道该补哪一行。
import platform
import re

MACHINE_KEY_ENV = u'LEFT_AXIS_MACHINE_KEY'
GITHUB_RUNNER_KEY = u'github-runner'
LOCAL_KEY = u'local:MacBook-Air.local'   # R231 实测 `platform.node()`=MacBook-Air.local


def machine_key():
    """机器身份从**可观察事实**推：runner 上 GitHub 自己会设 `GITHUB_ACTIONS=true`，
    本机按主机名。`LEFT_AXIS_MACHINE_KEY` 只是显式逃生口，也只准填名册里已有的键。
    """
    explicit = (os.environ.get(MACHINE_KEY_ENV) or u'').strip()
    if explicit:
        return explicit
    if (os.environ.get('GITHUB_ACTIONS') or u'').strip().lower() == u'true':
        return GITHUB_RUNNER_KEY
    return u'local:' + platform.node()


# 一行 = 一台机器的画像。`not_run_names` 必须逐颗点名：只数数量不点名是一条覆盖率通道
# （R121 的名单分键同义）。`missing_names` 是**另一件事**（帧路径腐烂 / 帧没拍到），
# 与 NOT_RUN（帧到了但那块没墨）不许并成一支 —— 刀二钉的就是这条。
CI_EXPECTATIONS = {
    LOCAL_KEY: dict(
        provenance=u'R231 本机实测、R233 复测：帧目录由 CLIPBOARD_HISTORY_UI_SHOTS 给出（162 帧 @2x，纯文本四条关系行都打）',
        verdict=u'ok', hard=0, not_run=0, missing_frames=0, probes=7,
        not_run_names=(), missing_names=()),
    GITHUB_RUNNER_KEY: dict(
        provenance=u'run 39315666980 / commit 847ab2b 的失败正文逐字抄录',
        verdict=u'skipped', hard=0, not_run=4, missing_frames=0, probes=7,
        not_run_names=(u'浮层/选中行药丸', u'统计/统计行', u'统计/月份行', u'统计/热图网格'),
        missing_names=()),
}

CI_LINE_RE = re.compile(
    r'LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)')
NOT_RUN_RE = re.compile(r'LEFT_AXIS_NOT_RUN ([^：\n]+)')
MISSING_RE = re.compile(r'LEFT_AXIS_MISSING_FRAME (\S+)')


def parse_ci_profile(text):
    """把尺自己打的结论行 + 名单行读成一份画像。

    两道闸门：结论行打不出来 = 坏（不许当空画像通过）；结论行的 `missing_frames` 计数与它自己
    点名的缺席名单不签字 = 坏（R99 的"数次数 ≠ 出口数"这一族 —— 计数会被另一条出口喂饱）。
    """
    m = CI_LINE_RE.search(text)
    if m is None:
        raise AssertionError(u'LEFT_AXIS_CI 结论行没打出来 ⇒ 尺没跑完，不许判通过：\n%s'
                             % text[-400:])
    names = tuple(sorted(set(NOT_RUN_RE.findall(text))))
    absent = tuple(sorted(set(MISSING_RE.findall(text))))
    if int(m.group(4)) != len(absent):
        raise AssertionError(u'尺自陈 missing_frames=%d 却点名了 %d 颗缺席帧（%s）⇒ 计数与名单有一个在说谎，'
                             u'这一格的任何一个数都不配当期望' % (int(m.group(4)), len(absent), u', '.join(absent)))
    return dict(verdict=m.group(1), hard=int(m.group(2)), not_run=int(m.group(3)),
                missing_frames=int(m.group(4)), probes=int(m.group(5)),
                not_run_names=names, missing_names=absent)


CI_FIELDS = (u'verdict', u'hard', u'not_run', u'missing_frames', u'probes')


def diff_ci_profile(want, got):
    """期望 vs 实得，逐字段返回不匹配的话；全匹配 ⇒ 空表。"""
    bad = [u'%s 期望=%s 实得=%s' % (f, want[f], got[f]) for f in CI_FIELDS
           if want[f] != got[f]]
    for label, field in ((u'NOT_RUN 名单', u'not_run_names'), (u'缺席帧名单', u'missing_names')):
        w, g = tuple(sorted(want[field])), tuple(sorted(got[field]))
        if w != g:
            bad.append(u'%s 期望=[%s] 实得=[%s]' % (label, u', '.join(w), u', '.join(g)))
    return bad


# 四张**逐字抄录**的正文（不依赖任何环境，正对照与刀都拿它们重放）。
#
# 来历（R233）：上一版这里只有两张 ci 样本，而 `RUNNER_SAMPLE` 的第一行是我手写拼上去的 ——
# 它给的是 `LEFT_AXIS A 对称 ｜ 浮层/选中行药丸`，而同一份正文里 浮层/选中行药丸 在 NOT_RUN 名单里。
# `judge()` 的规矩是「NOT_RUN 只免掉**引用了那颗探针的那条关系**」，所以那一行在 runner 上**根本不可能**
# 被打印。它当时没让任何一格红（解析器只读结论行与名单行），于是"逐字抄录"这句注释一直在替
# 一份拼出来的证据作证。现在四处都在：本机 39321660036 同一时刻的纯文本正文（R233 实测：
# 四条关系行一条不缺、`问题=0`）、runner 那一跑的失败正文逐字取出（只剩 D 一行 + 4 颗 NOT_RUN），
# 以及同一 `judge()` 在 `--ci` 下的结论行。行部分与名单互为证人：下面 `PlainContractTests` 里
# "给没有对象的探针打规则行 = 红"那一格，正是让这种拼出来的样本从此不能过账的牙。

LOCAL_PLAIN_SAMPLE = (
    u'LEFT_AXIS A 对称 ｜ 浮层/选中行药丸 ｜ 左内缩=22.0pt 右内缩=22.0pt 差=0.0pt（容差 1.0）\n'
    u'LEFT_AXIS B 同轴 ｜ 统计/统计行、统计/月份行、统计/说明正文 ｜ 最左墨=[148.0, 148.0, 148.0]pt 跨度=0.0pt（容差 1.0）\n'
    u'LEFT_AXIS C 不越过 ｜ 统计/热图网格 ⊆ 统计/说明正文 ｜ 网格左缘=148.0pt 右内缩=161.0pt ｜参照左缘=148.0pt 右内缩=32.0pt\n'
    u'LEFT_AXIS D 同轴·组合帧 ｜ 详情/组合帧头部、详情/组合帧骨架 ｜ 最左墨=[20.5, 20.0]pt 跨度=0.5pt（容差 2.0，跨种类 ⇒ 含字形侧边距）\n'
    u'LEFT_AXIS_VERDICT ok 探针=7 问题=0 NOT_RUN帧=0\n'
)

RUNNER_PLAIN_SAMPLE = (
    u'LEFT_AXIS D 同轴·组合帧 ｜ 详情/组合帧头部、详情/组合帧骨架 ｜ 最左墨=[20.0, 20.0]pt 跨度=0.0pt（容差 2.0，跨种类 ⇒ 含字形侧边距）\n'
    u'LEFT_AXIS_NOT_RUN 浮层/选中行药丸：cause=bg-not-flat bg=(50, 50, 50) ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_NOT_RUN 统计/统计行：cause=no-ink bg=(50, 50, 50) thr=12 window=580x14 ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_NOT_RUN 统计/月份行：cause=no-ink bg=(50, 50, 50) thr=12 window=580x14 ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_NOT_RUN 统计/热图网格：cause=no-ink bg=(50, 50, 50) thr=12 window=580x13 ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_VERDICT bad 探针=7 问题=4 NOT_RUN帧=0\n'
)

LOCAL_SAMPLE = (
    u'LEFT_AXIS A 对称 ｜ 浮层/选中行药丸 ｜ 左内缩=22.0pt 右内缩=22.0pt 差=0.0pt（容差 1.0）\n'
    u'LEFT_AXIS B 同轴 ｜ 统计/统计行、统计/月份行、统计/说明正文 ｜ 最左墨=[148.0, 148.0, 148.0]pt 跨度=0.0pt（容差 1.0）\n'
    u'LEFT_AXIS C 不越过 ｜ 统计/热图网格 ⊆ 统计/说明正文 ｜ 网格左缘=148.0pt 右内缩=161.0pt ｜参照左缘=148.0pt 右内缩=32.0pt\n'
    u'LEFT_AXIS D 同轴·组合帧 ｜ 详情/组合帧头部、详情/组合帧骨架 ｜ 最左墨=[20.5, 20.0]pt 跨度=0.5pt（容差 2.0，跨种类 ⇒ 含字形侧边距）\n'
    u'LEFT_AXIS_CI verdict=ok hard=0 not_run=0 missing_frames=0 probes=7\n'
)

RUNNER_SAMPLE = (
    u'LEFT_AXIS D 同轴·组合帧 ｜ 详情/组合帧头部、详情/组合帧骨架 ｜ 最左墨=[20.0, 20.0]pt 跨度=0.0pt（容差 2.0，跨种类 ⇒ 含字形侧边距）\n'
    u'LEFT_AXIS_NOT_RUN 浮层/选中行药丸：cause=bg-not-flat bg=(50, 50, 50) ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_NOT_RUN 统计/统计行：cause=no-ink bg=(50, 50, 50) thr=12 window=580x14 ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_NOT_RUN 统计/月份行：cause=no-ink bg=(50, 50, 50) thr=12 window=580x14 ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_NOT_RUN 统计/热图网格：cause=no-ink bg=(50, 50, 50) thr=12 window=580x13 ⇒ 尺没有对象，不许给绿\n'
    u'LEFT_AXIS_CI verdict=skipped hard=0 not_run=4 missing_frames=0 probes=7\n'
)


# ---------------------------------------------------------------------------
# 纯文本模式（不带 --ci）的期望：由**同一行机器画像**推导，不再抄第二遍数字
# ---------------------------------------------------------------------------
# 来历：253 把帧目录接进电池之后，`RealFrameTests` 那一格在 runner 上红了（run 39321660036 /
# STEP[9]「Release script tests」，那一跑**唯一**一朵红，正文逐字抄进上面的 RUNNER_PLAIN_SAMPLE）。
# 它原来写死两件事：① `assertEqual(0, code)` 加 `assertIn(u'LEFT_AXIS_VERDICT ok')`；
# ② `assertEqual(4, len(rule_rows))`。两件都是"拿本机的能力当另一台机器的地板"
# （R154 / R231 同一族），只是 259 那轮只把 `--ci` 那一格改成按机器切片，纯文本这一格漏了 ——
# **同一件事两份判定，修了一处忘另一处**（R151 那一族：一条规则两份实现互相掩盖）。
#
# 尺在两种模式里跑的是同一个 `judge()`，差别只在结论行：纯文本把「硬违反」与「尺没有对象」
# 缝进同一个 `问题=` 计数 ⇒ 环境盲区也 exit 1；`--ci` 把它们拆成 `hard` / `not_run` ⇒ 只有真红才 exit 1。
# 两个方向都不许走：这一格不许改成"skip 也算过"（那会让它变成永远绿的装饰，R210 立它的原意），
# 也不许把 runner 的四条 NOT_RUN 说成产品没问题。处置：期望由**这一台机器已登记的那一行**推导，
# 并把尺自陈的那条规矩钉成会红的判据 —— 缺席名单与规则行必须互相解释：
# 引用了盲区探针的那条关系不许打行，其余每条都必须各自报数；尺自陈的 `问题=` 必须等于
# 它自己点名的（没对象的颗 + 真红的条数）。
PLAIN_VERDICT_RE = re.compile(u'LEFT_AXIS_VERDICT (\\w+) 探针=(\\d+) 问题=(\\d+) NOT_RUN帧=(\\d+)')
NOT_RUN_PREFIX = u'LEFT_AXIS_NOT_RUN '
ROW_PREFIX = u'LEFT_AXIS '
ABSENT_MARK = u'探针取不到帧'
# 尺能报的"真红"编码，从被告自己的 `judge()` 抄。新增一类坏法而这里没跟上 ⇒
# 下面的"计数与名单互相签字"会红，不会让新的一类悄悄免检。
HARD_CODES = (u'ASYMMETRIC', u'OFF_AXIS', u'GRID_PAST_TEXT', u'GRID_LEFT_OF_TEXT',
              u'COMPOSED_OFF_AXIS')


def relation_probes():
    """四条关系各自引用哪几颗探针 —— 从尺的常量读，不在测试里另抄一份名单。"""
    return (
        (u'A 对称', (sla.SYMMETRY_PROBE,)),
        (u'B 同轴', tuple(n.strip() for n in sla.AXIS_GROUP.split(u','))),
        (u'C 不越过', tuple(sla.NO_OVERFLOW)),
        (u'D 同轴·组合帧', tuple(n.strip() for n in sla.AXIS_GROUP_COMPOSED.split(u','))))


def parse_plain_profile(text):
    """纯文本正文 → 画像。结论行缺失、或尺自陈的计数与它自己点名的名单不签字 ⇒ 响。"""
    m = PLAIN_VERDICT_RE.search(text)
    if m is None:
        raise AssertionError(u'LEFT_AXIS_VERDICT 结论行没打出来 ⇒ 尺没跑完，不许判通过：\n%s' % text[-400:])
    blind, absent = [], []
    for line in text.splitlines():
        if not line.startswith(NOT_RUN_PREFIX):
            continue
        rest = line[len(NOT_RUN_PREFIX):]
        if rest.startswith(ABSENT_MARK):
            absent.append(rest.split(u'：', 1)[-1])
        else:
            blind.append(rest.split(u'：')[0])
    hard = [c for c in HARD_CODES if (u'LEFT_AXIS_' + c) in text]
    tags = [l[len(ROW_PREFIX):].split(u' ｜')[0]
            for l in text.splitlines() if l.startswith(ROW_PREFIX) and u' ｜' in l]
    problems = int(m.group(3))
    if problems != len(blind) + len(hard):
        raise AssertionError(
            u'尺自陈 问题=%d，却点名了 %d 颗没有对象 + %d 条真红（没对象=[%s] 真红=[%s]）'
            u'⇒ 计数与名单有一个在说谎，这一格的任何一个数都不配当期望：\n%s'
            % (problems, len(blind), len(hard), u', '.join(sorted(set(blind))),
               u', '.join(hard), text[-400:]))
    return dict(verdict=m.group(1), probes=int(m.group(2)), problems=problems,
                missing=int(m.group(4)), blind=tuple(sorted(set(blind))),
                absent=tuple(sorted(set(absent))), hard=tuple(sorted(set(hard))),
                tags=tuple(sorted(set(tags))))


def plain_expectation_from_row(row):
    """由**同一行**机器画像推出纯文本模式该打什么：`问题 = hard + not_run`，其余全是推导。"""
    want_problems = row[u'hard'] + row[u'not_run']
    blind = tuple(sorted(row[u'not_run_names']))
    return dict(verdict=u'ok' if want_problems == 0 else u'bad',
                exit_code=0 if want_problems == 0 else 1,
                problems=want_problems,
                probes=row[u'probes'],
                missing=row[u'missing_frames'],
                hard=() if row[u'hard'] == 0 else None,
                hard_count=row[u'hard'],
                blind=blind,
                tags=tuple(sorted(tag for tag, probes in relation_probes()
                                  if not (set(probes) & set(blind)))))


PLAIN_FIELDS = (u'verdict', u'problems', u'probes', u'missing')


def diff_plain_profile(want, got):
    """期望 vs 实得，逐字段返回不匹配的话；全匹配 ⇒ 空表。"""
    bad = [u'%s 期望=%s 实得=%s' % (f, want[f], got[f])
           for f in PLAIN_FIELDS if want[f] != got[f]]
    if want[u'hard'] is not None and tuple(sorted(got[u'hard'])) != want[u'hard']:
        bad.append(u'真红名单 期望=[%s] 实得=[%s]'
                   % (u', '.join(want[u'hard']), u', '.join(got[u'hard'])))
    if len(got[u'hard']) != want[u'hard_count']:
        bad.append(u'真红条数 期望=%d 实得=%d（[%s]）⇒ 产品那一条轴不许按机器放宽'
                   % (want[u'hard_count'], len(got[u'hard']), u', '.join(got[u'hard'])))
    for label, field in ((u'NOT_RUN 名单', u'blind'), (u'规则行', u'tags')):
        w, g = tuple(sorted(want[field])), tuple(sorted(got[field]))
        if w != g:
            bad.append(u'%s 期望=[%s] 实得=[%s]' % (label, u', '.join(w), u', '.join(g)))
    return bad


class PlainContractTests(unittest.TestCase):
    """纯文本那一格的**契约**：不碰环境、不跑子进程，只验"表 + 推导 + 解析器"这套东西本身。

    为什么单独钉：`RealFrameTests` 那一格要等下一跑 CI 用别人的机器替我试；这一族现在就红。
    """

    def test_the_two_rows_derive_different_plain_expectations(self):
        loc = plain_expectation_from_row(CI_EXPECTATIONS[LOCAL_KEY])
        run_ = plain_expectation_from_row(CI_EXPECTATIONS[GITHUB_RUNNER_KEY])
        self.assertEqual((u'ok', 0, 0, ()),
                         (loc[u'verdict'], loc[u'problems'], loc[u'hard_count'], loc[u'blind']),
                         u'本机那一行推出来的期望必须仍然苛刻： verdict=ok、问题=0、没有盲区名单')
        self.assertEqual(4, len(loc[u'tags']), u'本机四条关系都要各自报数：%s' % u','.join(loc[u'tags']))
        self.assertEqual(0, loc[u'exit_code'])
        self.assertEqual(u'bad', run_[u'verdict'])
        self.assertEqual(4, run_[u'problems'], u'runner 那一行：四条盲区缝在 问题= 里')
        self.assertEqual(1, run_[u'exit_code'], u'纯文本的 exit 1 由推导给，不许写死也不许放宽成 0')
        self.assertEqual(0, run_[u'hard_count'], u'产品那一条轴在 runner 上也是 0，这一格才不是"环境说"')
        self.assertEqual((u'D 同轴·组合帧',), run_[u'tags'],
                         u'runner 上只该活下来 D：A/B/C 引用的探针都在它的盲区名单里')
        self.assertNotEqual(loc[u'tags'], run_[u'tags'], u'两行推不出差别 ⇒ 按机器切片失效')

    def test_each_verbatim_body_satisfies_its_own_rows(self):
        for key, plain, ci in ((LOCAL_KEY, LOCAL_PLAIN_SAMPLE, LOCAL_SAMPLE),
                               (GITHUB_RUNNER_KEY, RUNNER_PLAIN_SAMPLE, RUNNER_SAMPLE)):
            got = parse_plain_profile(plain)
            self.assertEqual([], diff_plain_profile(plain_expectation_from_row(CI_EXPECTATIONS[key]), got),
                             u'%s 的纯文本正文满足不了自己那一行：\n%s\n%s'
                             % (key, u'\n'.join(
                                 diff_plain_profile(plain_expectation_from_row(CI_EXPECTATIONS[key]), got)), plain))
            self.assertEqual([], diff_ci_profile(CI_EXPECTATIONS[key], parse_ci_profile(ci)),
                             u'%s 的 --ci 正文满足不了自己那一行：\n%s' % (key, ci))

    def test_a_body_must_not_satisfy_the_other_machines_expectation(self):
        """切片要双向：runner 的正文不许满足本机那一行，反之亦然。"""
        for mine, other in ((RUNNER_PLAIN_SAMPLE, LOCAL_KEY), (LOCAL_PLAIN_SAMPLE, GITHUB_RUNNER_KEY)):
            got = parse_plain_profile(mine)
            self.assertTrue(diff_plain_profile(plain_expectation_from_row(CI_EXPECTATIONS[other]), got),
                            u'一份正文同时满足两台机器的期望 ⇒ 这一格退回成"一把尺判另一台机器"')

    def test_pinning_the_plain_verdict_to_ok_for_every_machine_is_red(self):
        """刀一复演：把推导写成"人人都该 ok"（= 拿本机能力当另一台的地板）必须判不匹配。

        上一版的判据就是这个形状，而且它在 runner 上**真的**红了 —— 这一格钉的是
        "改回那个形状会被现在这套契约抓住"，不是"我记得它坏过"。
        """
        pinned = dict(plain_expectation_from_row(CI_EXPECTATIONS[LOCAL_KEY]))
        bad = diff_plain_profile(pinned, parse_plain_profile(RUNNER_PLAIN_SAMPLE))
        joined = u' '.join(bad)
        self.assertTrue(bad, u'把期望钉死成本机那一行仍然匹配 ⇒ 这一格没有牙')
        for word in (u'verdict', u'problems', u'NOT_RUN 名单', u'规则行'):
            self.assertIn(word, joined, u'放宽的那一格要能点名：%s\n%s' % (word, joined))

    def test_a_rule_row_for_a_blind_probe_is_red(self):
        """刀二复演：给没有对象的探针打规则行（= 缺席那一侧冒充结论）必须判不匹配。

        预登记的期望在这里被推翻过一次，记下来免得下轮再猜：我原本以为"计数与名单互相签字"
        那道闸门会抓住伪造的行 —— **它不会**。规则行进不了 `问题=` 计数（那个数只由
        「没有对象的颗 + 真红的条数」构成），抓住它的是画像里单独一根 `规则行` 轴。
        两侧各一格，谁也不许替谁签字：伪造行撞盲区那一侧，删行撞"活着的不许沉默"那一侧。
        """
        forged = (u'LEFT_AXIS B 同轴 ｜ 统计/统计行、统计/月份行、统计/说明正文 ｜ '
                  u'最左墨=[148.0, 148.0, 148.0]pt 跨度=0.0pt（容差 1.0）\n' + RUNNER_PLAIN_SAMPLE)
        got = parse_plain_profile(forged)
        bad = diff_plain_profile(plain_expectation_from_row(CI_EXPECTATIONS[GITHUB_RUNNER_KEY]), got)
        self.assertTrue(any(u'规则行' in b for b in bad),
                        u'没有对象的探针竟能打报告行而不被判红：\n%s' % u'\n'.join(bad))
        # 反面对照：伪造行不许把尺自己弄矛盾（问题= 计数照旧，只有规则行那一根轴动）
        self.assertEqual(4, got[u'problems'], u'规则行不该进 问题= 计数：进两根轴就分不开是谁动的')
        # 另一侧：尺**没**自相矛盾、只是少打了一条该活着的行（本机正文里删掉 C 行）
        dropped = u'\n'.join(l for l in LOCAL_PLAIN_SAMPLE.splitlines() if not l.startswith(u'LEFT_AXIS C'))
        bad = diff_plain_profile(plain_expectation_from_row(CI_EXPECTATIONS[LOCAL_KEY]),
                                 parse_plain_profile(dropped))
        self.assertTrue(any(u'规则行' in b for b in bad),
                        u'活着的探针少了报告行必须点名：\n%s' % u'\n'.join(bad))

    def test_a_hard_violation_is_never_a_per_machine_exit(self):
        """产品那一条轴不许跟着机器放宽：真红在**两台**机器的期望里都是 0 条。"""
        for key in (LOCAL_KEY, GITHUB_RUNNER_KEY):
            self.assertEqual(0, CI_EXPECTATIONS[key][u'hard'],
                             u'%s 那一行登记了硬违反 ⇒ 环境出口与产品结论被并成一支' % key)
            self.assertEqual(0, plain_expectation_from_row(CI_EXPECTATIONS[key])[u'hard_count'])
        forged = RUNNER_PLAIN_SAMPLE + u'LEFT_AXIS_ASYMMETRIC 浮层/选中行药丸：左右内缩差 3.0pt > 1.0pt\n'
        with self.assertRaises(AssertionError):
            parse_plain_profile(forged)
        # 尺自陈把它算进 问题 之后，画像就要能读出来并判成与期望不符（= CI 该红）
        counted = forged.replace(u'问题=4', u'问题=5')
        got = parse_plain_profile(counted)
        self.assertEqual((u'ASYMMETRIC',), got[u'hard'])
        bad = diff_plain_profile(plain_expectation_from_row(CI_EXPECTATIONS[GITHUB_RUNNER_KEY]), got)
        self.assertTrue(any(u'真红条数' in b for b in bad), u'真红必须单独成一条轴：\n%s' % u'\n'.join(bad))


class CiExitTests(unittest.TestCase):
    """R210 / BACKLOG 234：接进 CI 之后，"该红"与"该跳"必须分得开 —— 两侧都要有证人。

    为什么单独钉这一族：无头 runner 的高窗只画一条下沿带（BACKLOG 201），
    把环境缺席报成产品结论就是 R154 那朵假红的形状；而反过来把真红也吞成 skipped，
    这一步就变成一条永远绿的装饰。两个方向各一格，谁也不许替谁签字。
    """

    def _tmp_frames(self, images):
        import tempfile, shutil
        from PIL import Image
        d = tempfile.mkdtemp(prefix='left-axes-')
        self.addCleanup(shutil.rmtree, d)
        for name, im in images.items():
            im.save(os.path.join(d, name))
        return d

    @NEEDS_PIL
    def test_ci_exit_matches_this_machines_registered_profile(self):
        """这台机器自己打的画像，必须与名册里它那一行逐字段吻合（R231 / BACKLOG 259）。

        前一版这里写死 `verdict=ok` —— 那是把本机的能力当成 runner 的地板。现在期望按机器取，
        未登记的机器不给静默通过：它红，并且红话里带着解析出来的键，让人补该补的那一行。
        """
        key = machine_key()
        if key not in CI_EXPECTATIONS:
            self.fail(u'未登记的机器：解析出 %s=%s ⇒ 这一格必须红（不许静默通过、也不许改成 skip）。'
                      u'名册里已有：[%s]。补行的依据是**这台机器自己打的** LEFT_AXIS_CI 结论行 '
                      u'与逐颗 NOT_RUN / MISSING_FRAME 名单，不是别人的输出。'
                      % (MACHINE_KEY_ENV, key, u' | '.join(sorted(CI_EXPECTATIONS))))
        if not os.path.isdir(SHOTS):
            print(u'SKIPPED(本机)：帧目录不在 ⇒ 这一格 NOT-RUN')
            self.skipTest(u'帧目录不在盘上：%s' % SHOTS_NOTE)
        want = CI_EXPECTATIONS[key]
        code, out = run('--shots', SHOTS, '--ci')
        self.assertEqual(0, code, u'--ci 这步 exit 非 0（hard>0 才会）：\n%s' % out)
        got = parse_ci_profile(out)
        self.assertEqual([], diff_ci_profile(want, got),
                         u'机器=%s（%s）画像不匹配：\n%s\n原输出：\n%s'
                         % (key, want[u'provenance'], u'\n'.join(diff_ci_profile(want, got)), out))
        print(u'CI_PROFILE_OK 机器=%s verdict=%s not_run=%d 名单=[%s] 缺帧=%d 帧目录=%s'
              % (key, got[u'verdict'], got[u'not_run'], u', '.join(got[u'not_run_names']),
                 got[u'missing_frames'], SHOTS))

    def test_registered_rows_match_the_transcribed_samples(self):
        """正对照：两张逐字抄录的样本要各自满足自己那一行，且**不**满足对面那一行。

        这一格不碰环境、不跑子进程，只验"表 + 解析器"这套契约本身：解析器坏了、表抄错了、
        或者两行被误并成一行，都会在这里先红 —— 而不是等下一跑 CI 用环境去替我试。
        """
        for key, sample in ((GITHUB_RUNNER_KEY, RUNNER_SAMPLE), (LOCAL_KEY, LOCAL_SAMPLE)):
            got = parse_ci_profile(sample)
            self.assertEqual([], diff_ci_profile(CI_EXPECTATIONS[key], got),
                             u'%s 的样本满足不了自己那一行：\n%s\n%s'
                             % (key, u'\n'.join(diff_ci_profile(CI_EXPECTATIONS[key], got)), sample))
        for key, other in ((GITHUB_RUNNER_KEY, LOCAL_KEY), (LOCAL_KEY, GITHUB_RUNNER_KEY)):
            sample = RUNNER_SAMPLE if key == GITHUB_RUNNER_KEY else LOCAL_SAMPLE
            self.assertTrue(diff_ci_profile(CI_EXPECTATIONS[other], parse_ci_profile(sample)),
                            u'%s 的样本竟能满足 %s 那一行 ⇒ 两行被并成一行，切片失效'
                            % (key, other))

    def test_stripping_the_runner_roster_would_go_red(self):
        """刀一：把 runner 那一行的名册清空、verdict 写成 ok（= 把四条 NOT_RUN 说成没问题）
        ⇒ 同一份 runner 原文必须判成不匹配，而且要三样都报出来。

        这张表的每一格都要能被证伪；"放宽一格"和"修好一格"在测试里不许同形。
        """
        row = dict(CI_EXPECTATIONS[GITHUB_RUNNER_KEY])
        row.update(verdict=u'ok', not_run=0, not_run_names=())
        bad = diff_ci_profile(row, parse_ci_profile(RUNNER_SAMPLE))
        joined = u' '.join(bad)
        self.assertTrue(bad, u'清空名册后仍然判成匹配 ⇒ 这一格没有牙（名单是死读数）')
        self.assertIn(u'verdict', joined)
        self.assertIn(u'not_run', joined)
        self.assertIn(u'NOT_RUN 名单', joined)

    def test_merging_the_absent_frames_exit_would_go_red(self):
        """刀二：把"帧没到"这一支并进本格（= 缺帧也放行）⇒ 必须判成不匹配。

        两支的处置相反：NOT_RUN 是"帧到了、那块窗口没墨"（环境盲区），MISSING_FRAME 是
        "帧路径腐烂 / 捕获步骤没跑"（要修路径）。造一份只缺帧的样本去撞本机那一行，
        既验解析器分得开，也验尺自陈的计数与名单互相签字。
        """
        sample = (u'LEFT_AXIS A 对称 ｜ 浮层/选中行药丸 ｜ 左内缩=22.0pt 右内缩=22.0pt 差=0.0pt\n'
                  u'LEFT_AXIS_MISSING_FRAME quickpick-list-420x300-dark.png\n'
                  u'LEFT_AXIS_MISSING_FRAME settings-stats-populated-720x540-dark.png\n'
                  u'LEFT_AXIS_CI verdict=skipped hard=0 not_run=0 missing_frames=2 probes=5\n')
        got = parse_ci_profile(sample)
        self.assertEqual(2, len(got[u'missing_names']), u'缺席名单没被点名 ⇒ 只有数量没有主语')
        self.assertEqual((), got[u'not_run_names'])
        bad = diff_ci_profile(CI_EXPECTATIONS[LOCAL_KEY], got)
        joined = u' '.join(bad)
        self.assertTrue(bad, u'缺帧这一支被并进了本机那一行 ⇒ 路径腐烂会被读成通过')
        self.assertIn(u'missing_frames', joined)
        self.assertIn(u'缺席帧名单', joined)
        # 尺自己把计数与名单弄矛盾时，解析器要当场响，而不是安静取一个数：
        with self.assertRaises(AssertionError):
            parse_ci_profile(u'LEFT_AXIS_MISSING_FRAME a.png\n'
                             u'LEFT_AXIS_CI verdict=skipped hard=0 not_run=0 missing_frames=9 probes=5\n')

    def test_unregistered_machine_is_red_not_quietly_skipped(self):
        """负对照：键不在名册里时，那一格必须走 fail 分支（红），不许被 skip 或 ok 吃掉。"""
        saved = dict((k, os.environ.get(k)) for k in (MACHINE_KEY_ENV, 'GITHUB_ACTIONS'))
        os.environ[MACHINE_KEY_ENV] = u'someone-elses-mac'
        try:
            self.assertEqual(u'someone-elses-mac', machine_key())
            self.assertNotIn(machine_key(), CI_EXPECTATIONS)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertEqual(LOCAL_KEY if not os.environ.get('GITHUB_ACTIONS') else GITHUB_RUNNER_KEY,
                         machine_key(), u'逃生口用完没擦干净：解析出的键被夹具污染了')

    @NEEDS_PIL
    def test_absent_frames_are_skipped_not_red(self):
        d = self._tmp_frames({})
        code, out = run('--shots', d, '--ci')
        self.assertEqual(0, code, u'缺席不该让 CI 红：\n%s' % out)
        self.assertIn(u'LEFT_AXIS_CI verdict=skipped', out)
        self.assertIn(u'not_run=%d' % len(sla.PROBES), out,
                      u'缺席要写成读数，不许只说"跳过了"：\n%s' % out)

    def test_missing_pillow_is_unavailable_not_red(self):
        # 这一格只测「没有像素库时走哪个出口」，不该依赖某个帧目录存在：
        # R212 那版指 /tmp/shots_r211，在 runner 上先撞上 FRAME_DIR_MISSING（exit 2）而红了
        # —— 环境依赖被写进了判据的入口，run 39258514435 的 STEP[8] 就是这么红的。
        code, out = run('--shots', ROOT, '--ci', env={'SURFACE_LEFT_AXES_FORCE_NO_PIL': '1'})
        self.assertEqual(0, code, out)
        self.assertIn(u'LEFT_AXIS_CI verdict=unavailable', out)

    @NEEDS_PIL
    def test_a_real_violation_still_goes_red(self):
        """正对照的反面：造一张药丸只往右缩的帧 ⇒ 这一步必须真的能让 CI 红。"""
        from PIL import Image
        im = Image.new('RGB', (840, 600), (30, 30, 30))
        px = im.load()
        for y in range(104, 148):
            for x in range(74, 796):        # 左缘被推走 30px ⇒ 不对称
                px[x, y] = (60, 60, 60)
        st = Image.new('RGB', (1440, 1080), (30, 30, 30))
        sp = st.load()
        for y0 in (246, 296, 666):
            for y in range(y0, y0 + 28):
                for x in range(296, 1357):
                    sp[x, y] = (230, 230, 230)
        for y in range(326, 352):
            for x in range(296, 1117):
                sp[x, y] = (60, 120, 220)
        d = self._tmp_frames({u'quickpick-list-420x300-dark.png': im,
                              u'settings-stats-populated-720x540-dark.png': st})
        code, out = run('--shots', d, '--ci')
        self.assertEqual(1, code, u'真红被判成绿了（这一步会变成装饰）：\n%s' % out)
        self.assertIn(u'LEFT_AXIS_CI verdict=red', out)
        self.assertIn(u'ASYMMETRIC', out)


    def test_plain_mode_without_pillow_reports_unavailable_not_traceback(self):
        # R209 在 runner 上红的真因：非 --ci 路径让 ImportError 抛成崩溃，电池读不到结论行，
        # 于是「环境没有像素库」被报成「代码结论不成立」（R154 那一族）。现在它必须是一条具名出口。
        code, out = run('--shots', ROOT, env={'SURFACE_LEFT_AXES_FORCE_NO_PIL': '1'})
        self.assertEqual(2, code, out)
        self.assertIn(u'LEFT_AXIS_VERDICT unavailable', out)
        self.assertNotIn(u'Traceback', out, u'崩栈不是结论：读栈的人无法判断产品对不对')


class WorkflowWiringTests(unittest.TestCase):
    """接线本身也要有证人：这一步存在、且**不是** continue-on-error（否则接了等于没接）。"""

    YAML = os.path.join(ROOT, '.github', 'workflows', 'ci.yml')

    def test_ruler_step_exists_and_has_teeth(self):
        with io.open(self.YAML, encoding='utf-8') as h:
            t = h.read()
        self.assertIn(u'Surface left-axis ruler', t)
        i = t.index(u'Surface left-axis ruler')
        block = t[i:i + 600]
        self.assertNotIn(u'continue-on-error', block.split(u'- name:')[0] + block.split(u'\n')[0],
                         u'尺那一步不许 continue-on-error：红了也不算数')
        self.assertIn(u'--ci', block)

    def test_pillow_install_is_allowed_to_fail(self):
        with io.open(self.YAML, encoding='utf-8') as h:
            t = h.read()
        i = t.index(u'Pillow for the frame rulers')
        self.assertIn(u'continue-on-error: true', t[i:i + 300],
                      u'装库这一步失败不该红整条流水线 —— 缺席由尺自己报成 unavailable')


if __name__ == '__main__':
    unittest.main()
