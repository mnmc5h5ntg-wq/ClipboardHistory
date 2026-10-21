#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R280 的变异表（第 279 轮 / Round 277）：名册的第二条轴（两态声明 vs 帧名单）各钉一把刀。

· M836 对象轴 —— 把声明的前缀换成名单里不存在的东西：那一格必须红在"声明不成立"上。
  没有这把刀，`TWO_STATE_CLAIMS` 就只是一张抄了帧名的表，指不到东西也无所谓。
· M837 尺轴 —— 把守卫的否定词扫描弄瞎（`negated = []`）：正对照那一格必须红。
  本轮真实撞过的坏法就是这一族的镜像：更正后的理由里我引用了旧那句假话，守卫**字面**读它，
  于是真产物那一格反而红了（Ran 9 / failures=1）。那条规矩写进理由文本本身：否定词被字面读，
  旧原话只进台账不进表。

「跑起来了没」按 unittest 的结论行认；没有结论行一律 NOT_RUN（编译/语法错不算 CAUGHT = D-243）。
根由 `__file__` 推（D-260）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODULE = 'scripts.tests.test_hover_capture_channel'
T = 'scripts/tests/test_hover_capture_channel.py'

N_CLAIM = "    'DailyCopyHeatmapView.swift': 'heatmap-cell-strip',"
R_CLAIM = "    'DailyCopyHeatmapView.swift': 'heatmap-cell-strip_NOT_ON_DISK',"
N_RULER = '        negated = [w for w in NEGATIONS if w in reason]'
R_RULER = '        negated = []  # M837 刀：把否定词扫描弄瞎'

ARMS = [
    ('M836', u'两态声明指向不存在的帧 = 对象轴', T, N_CLAIM, R_CLAIM,
     'test_every_undeclared_hover_file_declares_its_two_state_evidence'),
    ('M837', u'守卫不读理由里的否定 = 尺轴', T, N_RULER, R_RULER,
     'test_prose_denying_frames_that_exist_is_caught'),
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
        proc = subprocess.run([sys.executable, '-m', 'unittest', MODULE],
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
    print('R280_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(ARMS), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(ARMS) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
