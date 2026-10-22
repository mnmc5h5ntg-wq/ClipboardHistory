#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R307 的变异表（第 306 轮 / Round 304）：`suite_reds` 的缺席打点，四条轴各钉一把。

本轮改的是 `scripts/motion_floor_gate.py` 里 `suite_verdicts` 的**干净那一支**：
R306 现读到 runner 连两跑打 `MOTION_FLOOR_SUITE_CLEAN=0`，而表里为它登记着两条红 ——
那一支旧代码直接 `return`，对缺席一行都不提 ⇒ 登记可以无限期赖着（354 第四步）。
新代码分三档 + 一条"不许恒响"，四把刀各钉一条：

· M885 `recurrence=always` 而这一跑没露面 ⇒ 必须**红**（缺席=过期，逼退场）。
· M886 登记没写 `recurrence` ⇒ 必须**红**（不许用默认值替作者选一个永远不会响的方向）。
· M887 `recurrence=sampled` 缺席 ⇒ 必须**点名**（不许静默 return）。
· M888 反过来：登记为空时这段**不许响** —— 钉的是"恒红的守卫最后会被人删掉"（R39）那一族，
  所以这一把的期望是"让它恒响 ⇒ 该红的那格真的会红"。

判定按**失败的格子名 + 正文里的串**（D-244）；没有结论行一律 NOT_RUN（D-243）；
needle 恰好命中一次、落刀后回读、还原逐字节一致（RESTORE_CLEAN）。根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = 'scripts/motion_floor_gate.py'
PY_GATE = 'scripts.tests.test_motion_floor_gate'

ARMS = [
    ('M885', u'always 那一档的缺席被降级成提示 = 过期登记不再逼退场', GATE,
     u'% (machine, ", ".join(always)), True))',
     u'% (machine, ", ".join(always)), False))',
     'test_always_absence_is_red_and_asks_for_retirement', u'不是提示'),
    ('M886', u'没写 recurrence 被默认成 sampled = 门替作者选了不响的那头', GATE,
     u'    if no_rec:',
     u'    if no_rec and False:',
     'test_missing_recurrence_is_red_not_a_silent_default', u'默认成某一档'),
    ('M887', u'sampled 的点名整块拿掉 = 回到 R306 那种静默 return', GATE,
     u'    if sampled:',
     u'    if False and sampled:',
     'test_sampled_absence_is_named_but_not_red', u'不许静默'),
    ('M888', u'让缺席提示在没有登记时也响 = 造出一把恒红的守卫（R39 那一族）', GATE,
     u'    if sampled:',
     u'    if True:',
     'test_empty_registry_does_not_make_noise', u'没有对象时也在响'),
]

RAN = re.compile(r'^Ran (\d+) tests', re.M)
PY_FAIL = re.compile(r'^FAIL: (\w+) ', re.M)


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def run_py(module):
    env = dict(os.environ)
    env['PYTHONUTF8'] = '1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    proc = subprocess.run([sys.executable, '-B', '-W', 'ignore', '-m', 'unittest', '-v', module],
                          cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    ran = RAN.findall(text)
    return (int(ran[-1]) if ran else 0), sorted(set(PY_FAIL.findall(text))), text


def run_arm(arm_id, why, target, needle, repl, want_fail, want_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        if read(target).count(repl) != 1:
            print('%s NOT_RUN 落刀后回读不是那一刀' % arm_id, flush=True)
            return 'NOT_RUN'
        ran, fails, text = run_py(PY_GATE)
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not ran:
        tail = '\n'.join(text.strip().splitlines()[-3:])
        print('%s NOT_RUN 没有结论行（编译/收集失败不算 CAUGHT = D-243）：%s' % (arm_id, tail), flush=True)
        return 'NOT_RUN'
    body = [line for line in text.splitlines() if want_text in line]
    if want_fail in fails and body:
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d）' % (arm_id, why, ', '.join(fails), ran), flush=True)
        print('   正文=%s' % body[0].strip()[:220], flush=True)
        return 'CAUGHT'
    print('%s %s ｜ 跑=%d 红=%s 正文含串=%s ⇒ 期望格子 %s 且正文含「%s」'
          % (arm_id, 'ESCAPED' if not fails else 'WRONG_CELL', ran, fails, bool(body),
             want_fail, want_text), flush=True)
    return 'ESCAPED' if not fails else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    unknown = only - set(a[0] for a in ARMS)
    if unknown:
        print('R307_MUTATE NOT_RUN 未知刀号 %s' % sorted(unknown), flush=True)
        return 2
    ran, fails, _ = run_py(PY_GATE)
    if not ran or fails:
        print('R307_BASELINE NOT_RUN 门那一卷基线不绿（跑=%d 红=%s）⇒ 拒绝出表'
              % (ran, fails), flush=True)
        return 1
    print('R307_BASELINE OK（%d 格全绿）' % ran, flush=True)
    arms = [a for a in ARMS if not only or a[0] in only]
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'no' if 'RESTORE_FAILED' in kinds else 'yes'
    print('R307_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
