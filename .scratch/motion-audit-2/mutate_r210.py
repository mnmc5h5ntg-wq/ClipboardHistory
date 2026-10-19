#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R210 的变异表：把看图尺接进 CI 之后，"该红"与"该跳"这两个出口各一把刀（BACKLOG 234 的收尾）。

被改的对象是**尺自己**（`scripts/surface_left_axes.py`），不是产品。
这一族的牙在于"接线不能把判据变成装饰"，所以三把刀打的都是出口的三种坏法：

M742 把 `return 1 if hard else 0` 改成恒 0（CI 永远不会红）⇒
     `test_a_real_violation_still_goes_red` 必须红：接了线却不承重，比不接更坏 ——
     日志里有一行 `LEFT_AXIS_CI verdict=red` 而流水线照绿。
M743 把 NOT_RUN 也算进 hard（环境缺席被报成产品结论）⇒
     `test_absent_frames_are_skipped_not_red` 必须红：这正是 R154 那朵假红的形状，
     无头 runner 的高窗只画一条下沿带（BACKLOG 201），缺席不是不合格。
M744 把容差从 1.0pt 放大到 999pt（判据恒真）⇒
     `test_self_test_passes_and_names_every_control` 必须红：尺自带的四格反对照会全部不红，
     `LEFT_AXIS_SELFTEST` 从 ok 变 bad ⇒ 这一刀证明"真值表"不是只在正对照上跑过。

三把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
RULER = 'scripts/surface_left_axes.py'
CLS = 'scripts.tests.test_surface_left_axes.CiExitTests'
TRUTH = 'scripts.tests.test_surface_left_axes.SelfTruthTableTests'

EXIT_LINE = '    return 1 if hard else 0'
HARD_LINE = "    hard = [c for c in codes if c != 'NOT_RUN']"
TOL_LINE = 'TOL_PT = 1.0'

ARMS = [
    ('M742', u'CI 出口改成恒 0（接了线不承重：verdict=red 而流水线照绿）', RULER,
     EXIT_LINE, '    return 0', CLS + '.test_a_real_violation_still_goes_red'),
    ('M743', u'把 NOT_RUN 算成真红（环境缺席被报成产品结论，R154 那一族）', RULER,
     HARD_LINE, '    hard = list(codes)', CLS + '.test_absent_frames_are_skipped_not_red'),
    ('M744', u'容差放大到 999pt（判据恒真，四格反对照全部不红）', RULER,
     TOL_LINE, 'TOL_PT = 999.0', TRUTH + '.test_self_test_passes_and_names_every_control'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_id):
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONUTF8'] = '1'
    proc = subprocess.run([sys.executable, '-m', 'unittest', test_id], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    m = re.search(r'Ran (\d+) tests?', text)
    return proc.returncode, (int(m.group(1)) if m else 0), text


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        if needle == repl:
            not_run += 1
            print('%s NOT_RUN 变异文与原文逐字相同 ⇒ 这一刀没有对象' % arm_id, flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, _ = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 2
        if n_ran == 0:
            not_run += 1
            print('%s NOT_RUN 那一格根本没跑（Ran 0）⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        if code != 0:
            caught += 1
            print('%s CAUGHT  %s ⇒ %s' % (arm_id, filt.split('.')[-1], why), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s ⇒ %s' % (arm_id, filt.split('.')[-1], why), flush=True)
    print('R210_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
