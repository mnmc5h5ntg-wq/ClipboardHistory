#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R270 的变异表：一把刀，尺轴（D-244 一把只钉一件事）。

M830 把判据里那段"读产品常量"的窗口表达式换回裸数字 600 —— 这正是 R270 之前**已经存在过**的形状
（R268 的台账里那句"值抄在这里 ⇒ BACKLOG 320"）。去掉修法之后，`ledger_timing_scan.py` 必须点名。

这一把钉的不是产品，是"抄值不再发生"这件事本身：如果哪天有人图省事把窗口写回字面量，
红的是尺，不是判据的运气。本轮另两把被主动放弃并写明理由（不许把 NOT_RUN 说成通过）：
  · 把产品 `visibilityGrace` 改成 0.9 ⇒ 判据**照绿**是**对的**（窗口跟着日程长到 2850 ms），
    它不配当一把刀 —— 刀的定义是"坏法必须红"，这里没有坏。
  · 把镜像排程里的 `+ Self.visibilityGrace` 删掉 ⇒ 现读不会红（那次镜像只是提早，
    成功路径上仍然没有多余发布）⇒ 那是另一条轴（提早可见性），本轮不假装它被钉住。
「跑起来了没」按结论行形状认；没有结论行一律 NOT_RUN（加载失败不算 CAUGHT = D-243）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
TEST = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/DailyCopyHeatmapTests.swift'

ARMS = [
    ('M830', u'窗口表达式换回裸字面量（抄值复活）= 尺轴', TEST,
     'milliseconds: Int(3 * (0.05 + DailyCopyLedger.visibilityGrace) * 1000))',
     'milliseconds: 600)'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        try:
            write(target, original.replace(needle, repl, 1))
            proc = subprocess.run([sys.executable, 'scripts/ledger_timing_scan.py'],
                                  cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            text = proc.stdout.decode('utf-8', 'replace')
        finally:
            write(target, original)
            if read(target) != original:
                print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
                return 2
        line = [l for l in text.splitlines() if l.startswith('TIMING_SCAN ')]
        ran = bool(line)
        failed = (proc.returncode != 0) or (not ran)
        if not ran:
            not_run += 1
            print('%s NOT_RUN 没有结论行：%s' % (arm_id, why), flush=True)
            continue
        named = [l for l in text.splitlines() if l.startswith('TIMING_SCAN_BAD')]
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ %s ｜ 点名=%s'
                  % (arm_id, why, line[0], ' / '.join(named)[:150]), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s ｜ %s' % (arm_id, why, line[0]), flush=True)
    print('R270_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
