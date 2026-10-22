#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R301 的变异表（第 300 轮 / Round 298）：读数通道那条规矩必须两侧都有牙。

本轮把 `HeatmapHoverEvidenceTests` 的 9 行读数从裸 stdout 改成走 `CaptureReadings`（文件 + stdout 两条腿），
并把「零裸 stdout 调用」那条绝对规矩从"只扫守卫自己那个文件"扩成**按名册扫**。两把刀：

· M870 **规矩的牙**：把 `emit` 的实现换回裸 stdout 调用 ⇒ `testCaptureReadingsUseTheFileChannel`
  必须红在「只走 stdout」。这一把钉的是"扫描真的在看这个文件"，而不是名册上写了一行字。
· M871 **名册不许空转**：把名册里的一个文件名改成一个不存在的名字 ⇒ 同一格必须红在「不存在」。
  这一把专治"名单里的文件改名/删掉之后，守卫扫了个空还报绿"（R99：按名单遍历的工具，
  名单为空或指不到东西时必须红，不许把"没扫到"读成"扫过了"）。

被搜的串（`pr` + `int(`）在 M870 的替换文本里是**拼出来的**：这张表自己住在 `.scratch/`，
不在名册里，但拼一下能让"读代码的人"一眼看出那是被注入的违规，而不是刀表自己的笔误。

「跑起来了没」按结论行的形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
判定按**失败正文**而不只按格子名（D-244）。根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HEAT = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/HeatmapHoverEvidenceTests.swift'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'

N_EMIT = u'    static func emit(_ line: String) { CaptureReadings.emit(line) }'
R_EMIT_STDOUT = u'    static func emit(_ line: String) { pri' + u'nt(line) }'
# R302 把名册从 3 个名字扩成 10 个（派生集上门），这一根的 needle 跟着换到当前形状，
# 否则 M871 会变成「needle 命中 0 次」的哑刀（DID-NOT-RUN 不是通过，D-234 同一族）。
N_ROSTER = (u'        let roster = ["CaptureReadings.swift", "DailyCopyHeatmapTests.swift",\n'
            u'                      "FrameIntervalBudgetTests.swift", "HeatmapHoverEvidenceTests.swift",\n')
R_ROSTER_GONE = (u'        let roster = ["CaptureReadings.swift", "DailyCopyHeatmapTests.swift",\n'
                 u'                      "FrameIntervalBudgetTestsRenamed.swift", "HeatmapHoverEvidenceTests.swift",\n')

GUARD = 'UICaptureTests/testCaptureReadingsUseTheFileChannel'

ARMS = [
    ('M870', u'把 emit 的实现换回裸 stdout = 证明扫描真的在看这个文件', HEAT,
     N_EMIT, R_EMIT_STDOUT, GUARD, u'只走 stdout'),
    ('M871', u'名册里放一个不存在的文件 = 名单不许空转', HARNESS,
     N_ROSTER, R_ROSTER_GONE, GUARD, u'不存在'),
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
        print('R301_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R301_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
