#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R275 的变异表（第 274 轮 / Round 272）：两把刀各钉一条轴（D-244）。

· M832 产品轴 —— 把 `SettingsView` 那条 hover 动画的 value 退回裸 `isHovered`（画法仍接键）。
  这正是本轮修掉的缺陷本身 ⇒ 守卫必须红，而且必须红在**对齐那一格**，不是红在真值表。
· M833 尺轴 —— 把守卫自己的谓词弄瞎（`isBare` 比较一个不存在的名字）。
  真值表那一格必须红。没有这一把，"守卫红"与"守卫坏了但恰好没东西可红"就分不开。

「跑起来了没」按结论行形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
失败行的形状是从 /tmp/r275_raw.log 实测的：`error: -[Module.Class testFoo] : XCTAssertEqual failed: ...`
与 `Test Case '-[Module.Class testFoo]' failed` —— 第一版只认 `name : XCTAssert…` 这种形状，
于是两把刀都被误报成 WRONG_CELL（刀读不到 ≠ 产品没红）。根由 `__file__` 推（D-260）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILTER = 'HoverAnimationChannelTests'

T_PRODUCT = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/SettingsView.swift'
N_PRODUCT = 'value: isHoveredForDrawing)'
R_PRODUCT = 'value: isHovered)'

T_RULER = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/HoverAnimationChannelTests.swift'
N_RULER = 'private func isBare(_ value: String) -> Bool { value == "isHovered" }'
R_RULER = 'private func isBare(_ value: String) -> Bool { value == "isHovered_NO_RULER" }'

ARMS = [
    ('M832', u'hover 动画的触发条件退回裸 isHovered = 产品轴', T_PRODUCT, N_PRODUCT, R_PRODUCT,
     'testEveryHoverAnimationInAKnownFilesReadsTheSameConditionAsTheInk'),
    ('M833', u'把守卫的裸读谓词弄瞎 = 尺轴', T_RULER, N_RULER, R_RULER,
     'testTheRulerFlagsTheBareFormAndAcceptsTheConjunction'),
]

ASSERT_SHAPE = re.compile(r"-\[[\w.]+ (test\w+)\] :\s*(XCTAssert\w+) failed")
CASE_SHAPE = re.compile(r"Test Case '-\[[\w.]+ (test\w+)\]' failed")


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
        env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
        proc = subprocess.run(['swift', 'test', '--filter', FILTER],
                              cwd=os.path.join(ROOT, 'ClipboardHistory'), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = proc.stdout.decode('utf-8', 'replace')
    finally:
        io.open(target, 'w', encoding='utf-8').write(original)
        if io.open(target, encoding='utf-8').read() != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED', []
    executed = re.findall(r'Executed (\d+) tests?, with (\d+) failures?', text)
    n_ran, n_fail = (int(executed[-1][0]), int(executed[-1][1])) if executed else (0, 0)
    if not n_ran:
        print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）' % arm_id, flush=True)
        print('\n'.join(text.strip().splitlines()[-3:]), flush=True)
        return 'NOT_RUN', []
    fails = sorted(set(ASSERT_SHAPE.findall(text)))
    if not fails:
        fails = sorted({(c, 'no-assert-type') for c in CASE_SHAPE.findall(text)})
    named = [f for f in fails if expected_cell in f[0]]
    reading = re.search(r'HOVER_ANIM_ALIGNMENT files=(\d+) sites=(\d+) 免检\(不读取证键\)=(\d+) 裸读=(\d+)', text)
    if n_fail and named:
        print('%s CAUGHT  %s ｜ 红在 %s（跑=%d 失败=%d）｜ 读数=%s'
              % (arm_id, why, ', '.join('%s(%s)' % x for x in named), n_ran, n_fail,
                 reading.group(0).split(' ', 1)[1] if reading else '无'), flush=True)
        return 'CAUGHT', named
    print('%s %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 期望的格子是 %s'
          % (arm_id, 'ESCAPED' if not n_fail else 'WRONG_CELL', fails, n_ran, n_fail, expected_cell), flush=True)
    return ('ESCAPED' if not n_fail else 'WRONG_CELL'), named


def main():
    verdicts = [run_arm(*a) for a in ARMS]
    kinds = [v[0] for v in verdicts]
    caught = kinds.count('CAUGHT')
    escaped = sum(1 for k in kinds if k in ('ESCAPED', 'WRONG_CELL'))
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if all(k != 'RESTORE_FAILED' for k in kinds) else 'no'
    print('R275_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(ARMS), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(ARMS) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
