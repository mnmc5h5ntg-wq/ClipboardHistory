#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R292 的变异表（第 291 轮 / Round 289）：墨簇尺的**单位**与 1x 替身臂的**身份**，三轴各一把刀（D-244）。

这一张表是被 runner 那两跑红出来的（BACKLOG 340）：`columnClusters` 原来把合并阈值写成固定像素
（`mergeGapPx = 12`），而注释里那句"6pt"是在本机 @2x 上量的 —— runner 的截图是 @1x（账上早有读数：
`位图=720x540 scale=1.0`），12px 在 1x 下就是 12pt，比列与列之间 10pt 的缝还宽 ⇒ 相邻列并成一簇，
判据走「尺没有对象」出口而红。修法是阈值随密度换算 + 在本机造一条 1x 替身臂。

判据在测试进程里现渲染（`render` → PNG → 像素），所以三把刀**不必重捕帧**（D-240 那族的区分写在表头）。

· M855 单位轴 —— 把换算退化成固定 12px（正是 runner 上红的那个形状）：必须红，且红话里印出「数到 2 簇」。
  这一把**只在 1x 那一臂上有牙**：本机 2x 下 6pt 恰好就是 12px，两臂的 2x 那一半躲得过。
  所以"这把刀在 2x 上恒 CAUGHT"不成立，它靠的是判据里那条 1x 臂 —— 这正是 340 要的两臂证伪。
· M856 臂身份轴 —— 把抽帧倍率写死成 1（两臂其实是同一个对象）：必须红在「这一臂根本没在 @1x 上量」。
  没有这一把，M855 之外的第二种坏法（臂不灵）会安静通过。
· M857 臂对象轴 —— 1x 臂的 y 带不再按倍率换算（量到别处去）：必须红在「数到 0 簇」。

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
FILTER = ('UICaptureTests/testMultiFileRowSeparatorsStartAtTheTextAxis'
          '|UICaptureTests/testColumnClusterRulerIsDensityIndependent')

N_GAP = 'let mergeGapPx = max(1, Int((mergeGapPt * max(density, 1e-9)).rounded()))'
N_FACTOR = 'let factor = max(1, Int(density.rounded()))'
N_BAND = 'y0: Int(Double(span.minY) / Double(factor)),'

ARMS = [
    ('M855', u'阈值退化成固定 12px = 单位轴（runner 那两跑的形状）', HARNESS,
     N_GAP, u'let mergeGapPx = 12', FILTER, u'数到 2 簇'),
    ('M856', u'抽帧倍率写死成 1（两臂是同一个对象）= 臂身份轴', HARNESS,
     N_FACTOR, u'let factor = 1', FILTER, u'这一臂根本没在 @1x 上量'),
    ('M857', u'1x 臂的 y 带不按倍率换算 = 臂对象轴', HARNESS,
     N_BAND, u'y0: span.minY,', FILTER, u'数到 0 簇'),
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
    env.pop('SDKROOT', None)
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
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
             'cluster 两格', expect_text), flush=True)
    for line in text.splitlines():
        if 'error:' in line:
            print('   实际红话=%s' % line.strip()[:400], flush=True)
            break
    return 'ESCAPED' if not n_fail else 'WRONG_CELL'


def main():
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R292_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R292_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
