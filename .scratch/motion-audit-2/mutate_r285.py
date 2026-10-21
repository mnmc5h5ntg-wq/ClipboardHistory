#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R285 的变异表（第 284 轮 / Round 282）：给 336 那道零地板守卫补两把刀（D-244 各钉一条轴）。

· M838 尺轴 —— 把"绝对下限"的识别弄瞎（换成一个永远匹配不上的式子）：
  仓库里那三处**合法**写法（绝对下限写在上一行 guard 里）就会被点名 ⇒
  `test_no_relative_floor_without_an_absolute_clamp_in_the_repo` 必须红。
  没有这把刀，"我认得 max(...)" 这句话与"我什么都不认"同形。
· M839 对象轴 —— 把"相对地板"的识别弄瞎（一个都不匹配）：
  正对照那一格必须红（`test_the_scanner_finds_the_real_offender_shape`）——
  它证明这把尺至少看得见本轮真踩过的那个形状。

「跑起来了没」按 unittest 的结论行认；没有结论行一律 NOT_RUN（语法错不算 CAUGHT = D-243）。
根由 `__file__` 推（D-260）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODULE = 'scripts.tests.test_zero_floor_guard'
T = 'scripts/tests/test_zero_floor_guard.py'

N_CLAMP = "ABSOLUTE_CLAMP = re.compile(r'minimumVisibleChange|min_floor|max\\s*\\(|MIN_VISIBLE|ABSOLUTE_FLOOR')"
R_CLAMP = "ABSOLUTE_CLAMP = re.compile(r'NEVER_MATCHES_M838')"
N_REL = "RELATIVE_FLOOR = re.compile(r'>=\\s*(?:[A-Za-z_][\\w.]*\\s*\\([^)]*\\)\\s*\\*|peak\\b[^*\\n]*\\*)')"
R_REL = "RELATIVE_FLOOR = re.compile(r'NEVER_MATCHES_M839')"

ARMS = [
    ('M838', u'把绝对下限的识别弄瞎 = 尺轴', T, N_CLAMP, R_CLAMP,
     'test_no_relative_floor_without_an_absolute_clamp_in_the_repo'),
    ('M839', u'把相对地板的识别弄瞎 = 对象轴', T, N_REL, R_REL,
     'test_the_scanner_finds_the_real_offender_shape'),
]

FAIL_SHAPE = re.compile(r'^FAIL: (test\w+) \(', re.M)
RAN_SHAPE = re.compile(r'^Ran (\d+) tests?', re.M)
FAILED_SHAPE = re.compile(r'^FAILED \((?:failures=(\d+))?', re.M)


def run_arm(arm_id, why, rel_target, needle, repl, expected_cell):
    target = os.path.join(ROOT, rel_target)
    original = io.open(target, encoding='utf-8').read()
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        io.open(target, 'w', encoding='utf-8').write(original.replace(needle, repl, 1))
        env = dict(os.environ)
        env.pop('SDKROOT', None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTHONUTF8'] = '1'
        proc = subprocess.run([sys.executable, '-W', 'ignore', '-m', 'unittest', MODULE],
                              cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = proc.stdout.decode('utf-8', 'replace')
    finally:
        io.open(target, 'w', encoding='utf-8').write(original)
        if io.open(target, encoding='utf-8').read() != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    ran = RAN_SHAPE.findall(text)
    n_ran = int(ran[-1]) if ran else 0
    if not n_ran:
        print('%s NOT_RUN 没有结论行（跑不起来不算 CAUGHT = D-243）' % arm_id, flush=True)
        print('\n'.join(text.strip().splitlines()[-3:]), flush=True)
        return 'NOT_RUN'
    m = FAILED_SHAPE.search(text)
    n_fail = int(m.group(1)) if (m and m.group(1)) else 0
    fails = sorted(set(FAIL_SHAPE.findall(text)))
    named = [f for f in fails if expected_cell == f]
    if n_fail and named:
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d）' % (arm_id, why, ', '.join(named), n_ran, n_fail), flush=True)
        return 'CAUGHT'
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望的格子是 %s'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', fails, n_ran, n_fail, expected_cell), flush=True)
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    kinds = [run_arm(*a) for a in ARMS]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R285_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(ARMS), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(ARMS) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
