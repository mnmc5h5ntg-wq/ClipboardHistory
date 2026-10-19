#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R220 的变异表：新入库的骨架条带对比度尺（BACKLOG 245）两把刀，一把打产品值、一把打尺的参照点。

M755 把亮档底色墨改回 **0.06**（也就是把 R219 的修法撤掉）⇒
     `testSkeletonBarsAreVisibleAgainstTheirOwnBackground` 的亮档那一格必须红（实测比值退回 1.12 < 1.20）。
     这一刀就是 242 那个缺陷本身：注意它**不会**让真值表红（0.26-0.06=0.20 仍 ≥ 0.08）
     ⇒ 这正是这条像素判据存在的意义：抬升够、条带却照样看不见，那种坏法只有量像素的那把尺拦得住。
M756 把尺的"底"从众数改成**最小值**（`histogram.max` ⇒ `histogram.min`）⇒
     合成对照与两档真帧必须一起红。这一刀证明参照点本身有牙（R37 那一族：参照点取错，整把尺就在量别的东西）。

两把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
SHIMMER = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
FILT = 'UICaptureTests'

ARMS = [
    ('M755', u'亮档底色墨退回 0.06（撤掉 R219 的修法；真值表照样绿）', SHIMMER,
     '    static let lightBaseOpacity: Double = 0.14',
     '    static let lightBaseOpacity: Double = 0.06',
     'testSkeletonBarsAreVisibleAgainstTheirOwnBackground'),
    ('M756', u'尺的底从众数改成最小值（参照点取错 ⇒ 整把尺在量别的东西）', HARNESS,
     '        let background = (histogram.max { $0.value < $1.value }?.key ?? 0) * 4 + 2\n'
     '        var barRows: [Int] = []\n',
     '        let background = (histogram.min { $0.value < $1.value }?.key ?? 0) * 4 + 2\n'
     '        var barRows: [Int] = []\n',
     'testSkeletonBarContrastRulerKnowsItsOwnAnswers'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_name):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run(['env', '-u', 'SDKROOT', 'swift', 'test', '--filter',
                           '%s/%s' % (FILT, test_name)],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    m = re.search(r'Executed (\d+) tests?', text)
    fm = re.search(r'with (\d+) failure', text)
    return proc.returncode, (int(m.group(1)) if m else 0), bool(fm) and int(fm.group(1)) > 0, text


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, failed, text = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 2
        if n_ran == 0:
            not_run += 1
            print('%s NOT_RUN 那一格根本没跑（Executed 0，多半是没编译过）⇒ 不算 CAUGHT：%s'
                  % (arm_id, why), flush=True)
            continue
        readings = re.findall(r'SKELETON_CONTRAST[^\n]*', text)
        note = readings[0] if readings else u'没有读数行'
        if code != 0 and failed:
            caught += 1
            print('%s CAUGHT  %s.%s ｜ %s ｜ %s' % (arm_id, FILT, filt, why, note), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s.%s ｜ %s ｜ %s' % (arm_id, FILT, filt, why, note), flush=True)
    print('R220_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
