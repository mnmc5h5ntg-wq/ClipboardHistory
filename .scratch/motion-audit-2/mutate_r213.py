#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R213 的变异表：给 R209…R212 那把尺补上欠的三把刀（BACKLOG 238 结案）。

对象是 `scripts/surface_left_axes.py`（判据自己），不是产品。三把刀各打一种"尺坏了还照绿"的形态：

M745 同帧判据恒真（`if spread2 > COMPOSED_TOL_PT:` ⇒ `if False:`）⇒
     自检的「反对照·组合帧头部换列」不再红 ⇒ `LEFT_AXIS_SELFTEST bad` ⇒ SelfTruthTableTests 红。
     这一格是 233 判据半的牙：没有它，把 D 整条注释掉也不会有任何反应。
M746 把"没有像素库"的具名出口改回裸 `raise` ⇒
     `test_plain_mode_without_pillow_reports_unavailable_not_traceback` 必须红。
     这一刀钉的是 R209 在 runner 上那朵红的**原样复发**（环境缺席被报成代码结论）。
M747 把 NOT_RUN 的"只免引用它的那条规则"改回"永远活着"（`live()` ⇒ True）⇒
     缺席的探针会被当成有对象去解引用 ⇒ 崩栈，CI 那一格必须红。
     这一刀证明证人读的是**结论行**，不只是退出码。

三把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
RULER = 'scripts/surface_left_axes.py'
T = 'scripts.tests.test_surface_left_axes'

D_NEEDLE = '    if spread2 > COMPOSED_TOL_PT:'
EXIT_NEEDLE = ("    except ImportError:\n"
               "        print(u'LEFT_AXIS_VERDICT unavailable reason=pillow-missing 探针=0 问题=0 NOT_RUN帧=0')")
LIVE_NEEDLE = "        return all(readings.get(n) and readings[n].get('ok') for n in names)"  # R223 跟着 R221 的成因分档改过锚点

ARMS = [
    ('M745', u'同帧判据恒真（D 被注释掉也不会有反应）', RULER,
     D_NEEDLE, '    if False:', T + '.SelfTruthTableTests.test_self_test_passes_and_names_every_control'),
    ('M746', u'把 unavailable 具名出口改回裸 raise（R209 runner 那朵红的复发）', RULER,
     EXIT_NEEDLE, "    except ImportError:\n        raise",
     T + '.CiExitTests.test_plain_mode_without_pillow_reports_unavailable_not_traceback'),
    ('M747', u'NOT_RUN 不再免掉引用它的规则（缺席被当成有对象）', RULER,
     LIVE_NEEDLE, '        return True',
     T + '.CiExitTests.test_a_real_violation_still_goes_red'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_id):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
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
            print('%s NOT_RUN 变异文与原文逐字相同 ⇒ 没有对象' % arm_id, flush=True)
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
    print('R213_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
