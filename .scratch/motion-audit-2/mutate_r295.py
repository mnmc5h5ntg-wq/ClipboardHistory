#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R295 的变异表（第 294 轮 / Round 292）：新落地的逐像素差尺 `pairDelta` 与它那道存在性闸门。

判据在测试进程里现渲染（`render` → PNG → 像素），**不必重捕帧**（D-240 那一族的区分写在表头）。

· M860 **参照臂那一侧的两态轴** —— 把系统参照按钮的按下态夹具改回 `highlighted: false`
  （与 idle 同一态）：`pairDelta` 在参照臂上必须读到 0 颗变化，判据必须红在「参照臂没画」。
  这一把钉的是"分母是不是真的另一态"——参照臂若两态同值，任何拿它当尺的地板都是拿噪声当尺。
· M861 **自家这一侧的计数轴** —— 把 `pairDelta` 的 `minDelta` 门限抬到 1000000：
  两臂的 `changed` 都必须归 0，判据必须红在「逐像素相减为 0 颗」。
  这一把钉的是"这颗尺会不会把'没量到'读成'量到了'"——它恒 0 时上面所有读数都该作废而不是安静通过。

「跑起来了没」按结论行的形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
判定按**失败正文**而不只按格子名（D-244）。根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
SECTION = 'UICaptureTests/testPressTravelSharesOneRulerWithTheSystemReference'

N_REF = 'AnyView(self.controlFrame(SystemPressProbe(highlighted: true)))'
R_REF = 'AnyView(self.controlFrame(SystemPressProbe(highlighted: false)))'
N_BAND = 'if abs(d) > minDelta { changed += 1; sumAbsChanged += abs(d) }'
R_BAND = 'if abs(d) > 1000000 { changed += 1; sumAbsChanged += abs(d) }'

ARMS = [
    ('M860', u'参照臂按下态改成与 idle 同态 = 分母的两态轴', HARNESS,
     N_REF, R_REF, SECTION, u'参照臂没画'),
    ('M861', u'逐像素差的门限抬到无穷 = 计数轴', HARNESS,
     N_BAND, R_BAND, SECTION, u'逐像素相减为 0 颗'),
]


EXECUTED = re.compile(r'Executed (\d+) tests?, with (\d+) failures?')
FAILED_CASE = re.compile(r"Test Case '-\[[\w.]+ (\w+)\]' failed")


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(os.path.join(ROOT, path), 'w', encoding='utf-8') as handle:
        handle.write(text)


def run(filter_name):
    env = dict(os.environ)
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    try:
        env['SDKROOT'] = subprocess.check_output(
            ['xcrun', '--sdk', 'macosx', '--show-sdk-path'], env=env).decode().strip()
    except Exception:
        env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', filter_name],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    executed = EXECUTED.findall(text)
    n_ran = int(executed[-1][0]) if executed else 0
    n_fail = int(executed[-1][1]) if executed else 0
    names = sorted(set(FAILED_CASE.findall(text)))
    return proc.returncode, n_ran, n_fail, names, text


def run_arm(arm_id, why, target, needle, repl, filter_name, expect_text):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        code, n_ran, n_fail, names, text = run(filter_name)
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not n_ran:
        tail = '\n'.join(text.strip().splitlines()[-3:])
        print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）：%s' % (arm_id, tail), flush=True)
        return 'NOT_RUN'
    named = [expect_text in ln for ln in text.splitlines() if 'error:' in ln]
    if n_fail and names and any(named):
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d exit=%d）'
              % (arm_id, why, ', '.join(names), n_ran, n_fail, code), flush=True)
        for line in text.splitlines():
            if expect_text in line and 'error:' in line:
                print('   正文=%s' % line.strip(), flush=True)
                break
        return 'CAUGHT'
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望格子 %s 且正文含「%s」'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', names, n_ran, n_fail,
             filter_name.split('/')[-1], expect_text), flush=True)
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R295_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R295_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
