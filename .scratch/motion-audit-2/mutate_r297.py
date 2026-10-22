#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R297 的变异表（第 296 轮 / Round 294）：346 结案 —— 带窗上界去掉之后，两件事都要能被证伪。

判据在测试进程里现渲染，**不必重捕帧**（D-240 那一族的区分写在表头）。

· M864 **相对漏电地板的牙** —— 给 `row-favorite-idle` 那颗夹具真的接上悬停取证键
  （模拟"取证通道漏电"这一件地板本来要抓的事）：新的相对判据（`idle.pillPixels × 4 < press.pillPixels`）
  必须红在「空闲帧也量到一整片第二层」。这一把钉的是"换成相对判据之后地板还剩不剩牙"——
  旧的绝对阈值 40 被删掉时，如果没人证明新地板会红，那这就是一次放宽而不是改进（R74 那一课）。
· M865 **反对照：把带窗上界装回去** —— `if d > 2` 改回 `if d > 2 && d < 60`：
  参照臂那格新加的无条件断言（"去掉带窗上界之后仍数不到按下那一块 ⇒ 346 的修法没生效"）必须红。
  这一把钉的是"那条断言真的依赖这次改动"，而不是恒绿的一句漂亮话（R100：对照判据对整把尺一起偏免疫，
  所以要拿改动本身当被告）。

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

N_IDLE = u'            AnyView(self.controlFrame(RowFavoriteButton(isFavorite: false, action: {})))\n        })'
R_IDLE = u'            AnyView(self.controlFrame(RowFavoriteButton(isFavorite: false, action: {})\n                .environment(\\.hoveredForCapture, true)))\n        })'
N_BAND = u'                if d > 2 { band[luma(x, y), default: 0] += 1 }'
R_BAND = u'                if d > 2 && d < 60 { band[luma(x, y), default: 0] += 1 }'

LADDER = 'UICaptureTests/testPressRungIsOrderedAboveTheHoverRung'
REF = 'UICaptureTests/testSystemPressReferenceExistsOnTheFixtureChannel'

ARMS = [
    ('M864', u'给 idle 夹具真的接上悬停键 = 相对漏电地板的牙', HARNESS,
     N_IDLE, R_IDLE, LADDER, u'空闲帧也量到一整片第二层'),
    ('M865', u'把带窗上界装回去 = 反对照（修法没生效时必须红）', HARNESS,
     N_BAND, R_BAND, REF, u'346 的修法没生效'),
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
        print('R297_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R297_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
