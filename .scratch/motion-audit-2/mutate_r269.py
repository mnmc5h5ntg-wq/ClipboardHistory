#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R269 的变异表：一把刀，工具轴（D-244 一把只钉一件事）。

M829 把 `wait_scan.judge` 的名册作用域去掉（`in_scope = list(windows)`）⇒ 指向 `Sources/` 时，
住在 `Tests/` 的那格观察窗口会被报成"名册失配"。这一刀钉的就是 R269 当场修掉的那个作用域 bug：
去掉修法，两格守卫里必须至少一格红
（`test_a_window_living_outside_the_scanned_root_is_not_stale` 或 `test_the_product_sources_scan_clean`）。

本轮 0 产品文件、帧未重捕（基线现读 changed=0）⇒ 不需要重捕型刀（D-240 的分界）。
「跑起来了没」按结论行形状认；没有结论行一律 NOT_RUN（编译/加载失败不算 CAUGHT = D-243）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
SCANNER = 'scripts/wait_scan.py'

ARMS = [
    ('M829', u'名册作用域被去掉（跨根复用一张名册）= 工具轴', SCANNER,
     '    in_scope = [w for w in windows if present is None or w[0] in present]',
     '    in_scope = list(windows)'),
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
            proc = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'test_wait_scan'],
                                  cwd=os.path.join(ROOT, 'scripts', 'tests'),
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            text = proc.stdout.decode('utf-8', 'replace')
        finally:
            write(target, original)
            if read(target) != original:
                print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
                return 2
        ran = 'Ran ' in text
        # 红在哪些格：unittest -v 每跑完一格就打一行 `test_x (… ) ... ok`，
        # 按「行首是 test_ 」抓会把全卷都报成红的（R269 第一把就犯过，见本行历史）。
        # 只认结论形状 `FAIL: test_x` / `ERROR: test_x`。
        names = sorted(set(re.findall(r'^(?:FAIL|ERROR): (test_[\w.]+)', text, re.M)))
        failed = ('FAILED' in text) or (not ran)
        tail = ' 结论行=' + (text.strip().splitlines()[-1] if ran else '无')
        if not ran:
            not_run += 1
            print('%s NOT_RUN 没有结论行：%s' % (arm_id, why), flush=True)
            continue
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ 红在 %s%s' % (arm_id, why, ', '.join(names)[:140], tail), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s%s' % (arm_id, why, tail), flush=True)
    print('R269_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
