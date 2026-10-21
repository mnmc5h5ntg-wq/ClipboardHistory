#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R279 的变异表（第 278 轮 / Round 276）：新闸门的两条轴各一把刀（D-244）。

被测对象不是 Swift 而是**脚本 + 它的证人卷** ⇒ 执行器换成 `python3 -m unittest`（根由 `__file__` 推，D-260）。

· M834 产品轴 —— 把 `scripts/round_verify.sh` 那道门的 `exit 1` 换成 `true`：
  门仍然打印 FRAME_GATE_RED 然后**继续往下走**。这正是 333 的原始缺陷形状（只说不拦）
  ⇒ 必须红在"changed=3 要红"那一格，不是红在接线格。
· M835 尺轴 —— 把守卫自己的 `code_lines` 弄瞎（不剥注释，整块喂给判据）。
  本轮真实撞过的坏法：门里注释写着「故意不留 `|| true`」，整块子串搜于是把散文读成代码，
  一道设计正确的守卫恒红。没有这把刀，"守卫有牙"与"守卫只是在读散文"分不开。

「跑起来了没」按 unittest 的结论行认（`Ran N tests` + `OK`/`FAILED (failures=k)`）；
没有结论行一律 NOT_RUN —— 语法错打不红不算 CAUGHT（D-243 同一族，换语言不换规矩）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODULE = 'scripts.tests.test_round_verify_frame_gate'

T_GATE = 'scripts/round_verify.sh'
N_GATE = u'之后重跑 scripts/round_verify.sh"\n  exit 1\n'
R_GATE = u'之后重跑 scripts/round_verify.sh"\n  true\n'

T_RULER = 'scripts/tests/test_round_verify_frame_gate.py'
N_RULER = '    kept = []'
R_RULER = "    return block  # M835 刀：尺弄瞎（不剥注释，整块当代码）\n    kept = []"

ARMS = [
    ('M834', u'闸门只打印不拦（门被拆）= 产品轴', T_GATE, N_GATE, R_GATE,
     'test_a_changed_frame_set_is_red'),
    ('M835', u'守卫不剥注释（把散文读成代码）= 尺轴', T_RULER, N_RULER, R_RULER,
     'test_the_gate_exists_and_uses_the_changed_reading'),
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
        return 'NOT_RUN', []
    try:
        io.open(target, 'w', encoding='utf-8').write(original.replace(needle, repl, 1))
        env = dict(os.environ)
        env.pop('SDKROOT', None)
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTHONUTF8'] = '1'
        proc = subprocess.run([sys.executable, '-m', 'unittest', MODULE, '-v'],
                              cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = proc.stdout.decode('utf-8', 'replace')
    finally:
        io.open(target, 'w', encoding='utf-8').write(original)
        if io.open(target, encoding='utf-8').read() != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED', []
    ran = RAN_SHAPE.findall(text)
    n_ran = int(ran[-1]) if ran else 0
    if not n_ran:
        print('%s NOT_RUN 没有结论行（跑不起来不算 CAUGHT = D-243）' % arm_id, flush=True)
        print('\n'.join(text.strip().splitlines()[-3:]), flush=True)
        return 'NOT_RUN', []
    m = FAILED_SHAPE.search(text)
    n_fail = int(m.group(1)) if (m and m.group(1)) else 0
    fails = sorted(set(FAIL_SHAPE.findall(text)))
    named = [f for f in fails if expected_cell == f]
    if n_fail and named:
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d）'
              % (arm_id, why, ', '.join(named), n_ran, n_fail), flush=True)
        return 'CAUGHT', named
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望的格子是 %s'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', fails, n_ran, n_fail, expected_cell), flush=True)
    return ('ESCAPED' if not n_fail else 'WRONG_CELL'), named


def main():
    if '--measure' in sys.argv:
        print('M834 target=%s needle=%s' % (os.path.join(ROOT, T_GATE), repr(N_GATE)), flush=True)
        print('M835 target=%s needle=%s' % (os.path.join(ROOT, T_RULER), repr(N_RULER)), flush=True)
        return 0
    verdicts = [run_arm(*a) for a in ARMS]
    kinds = [v[0] for v in verdicts]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if all(k != 'RESTORE_FAILED' for k in kinds) else 'no'
    print('R279_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(ARMS), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(ARMS) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
