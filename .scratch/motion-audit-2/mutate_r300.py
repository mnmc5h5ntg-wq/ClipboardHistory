#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R300 的变异表（第 299 轮 / Round 297）：热图悬停那一圈的两条界必须各自能被打红。

本轮把 `VisualHeat.hoverRingOpacity` 从 0.55 降到 0.30、把梯子顶档 0.85 抬到 0.92，
理由是现读的像素：环在最响的一臂上改 75.50/255，而最重的一次数据变化只改 37.33 ⇒ 交互比数据响。
三把刀各自钉一条轴（判据在测试进程里现渲染，**不必重捕帧** —— D-240 那一族的区分写在表头）：

· M866 **克制度的牙**：把环的透明度装回 0.55 ⇒ `testHoverIsNotLouderThanOneDataStep` 必须红。
  这一把钉的是"新界真的依赖这次改动"，而不是恒绿的一句漂亮话（R100：对照判据对整把尺一起偏免疫，
  所以要拿改动本身当被告）。
· M867 **可见性的牙（反方向）**：把环降到 0.12 ⇒ `testHoverRingIsVisibleOnEveryHeatLevelAndBothScales`
  必须红。两条界夹出来的窗口是本轮全部含义所在 —— 只装一边，另一边就是装饰。
· M869 **界本身是承重的**：把 `heaviestDataStepAllowed` 写成 0.0 ⇒ 同一条判据必须红，
  而它的正文就是出货版的环/档步读数（本地 print 会被 swift test 吞掉，见下）。
· M868 **顶档那一格是承重的**：把梯子顶档从 0.92 改回 0.85（环留在 0.30）⇒ 克制度那条必须红。
  这一把专治"改了调色板其实只是审美微调"的指控：如果窗口不需要抬顶档就能打开，这一把会 ESCAPED。

「跑起来了没」按结论行的形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
判定按**失败正文**而不只按格子名（D-244）。根由 `__file__` 推（D-260/D-262）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKENS = 'ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift'

N_RING = u'        isHovered ? 0.30 : 0'
R_RING_OLD = u'        isHovered ? 0.55 : 0'
R_RING_FAINT = u'        isHovered ? 0.12 : 0'
N_LADDER = u'    static let ladder: [Double] = [0.18, 0.34, 0.56, 0.92]'
R_LADDER_OLD = u'    static let ladder: [Double] = [0.18, 0.34, 0.56, 0.85]'
# M869 的靶是**判据自己的界**：把它写成 0.0（等于"交互一点都不许比数据响"）⇒ 那条判据必须红。
# 这一把有两个用处：① 证明这条界是承重的而不是装饰（把它调松到 1.0 之外它就恒绿了）；
# ② 它红下来的正文里带着**出货版**的环读数与档步读数 —— 本地 `swift test` 会吞掉 print，
#    所以本轮要进账的那两个数只能从这条红里拿（R90：结论要走能活下来的那条通道）。
TESTFILE = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/HeatmapHoverEvidenceTests.swift'
N_BOUND = u'static let heaviestDataStepAllowed: Double = 1.0'
R_BOUND_ZERO = u'static let heaviestDataStepAllowed: Double = 0.0'

LOUD = 'HeatmapHoverEvidenceTests/testHoverIsNotLouderThanOneDataStep'
VISIBLE = 'HeatmapHoverEvidenceTests/testHoverRingIsVisibleOnEveryHeatLevelAndBothScales'

ARMS = [
    ('M866', u'把环的透明度装回 0.55 = 克制度那条判据的牙', TOKENS,
     N_RING, R_RING_OLD, LOUD, u'交互比一次真实的数据变化还响'),
    ('M867', u'把环降到 0.12 = 可见性地板的反方向牙', TOKENS,
     N_RING, R_RING_FAINT, VISIBLE, u'那一圈在屏幕上根本不存在'),
    ('M868', u'把顶档改回 0.85（环留在 0.30）= 顶档那一格是承重的', TOKENS,
     N_LADDER, R_LADDER_OLD, LOUD, u'交互比一次真实的数据变化还响'),
    ('M869', u'把克制度的界写成 0.0 = 这条界本身是承重的（正文给出货版读数）', TESTFILE,
     N_BOUND, R_BOUND_ZERO, LOUD, u'交互比一次真实的数据变化还响'),
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
        print('R300_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R300_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
