#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R271 的变异表：一把刀，产品轴（D-244 一把只钉一件事）。

M831 把持久化的写从后台队列搬回调用线程（needle 从 R51 那张表里读，不手抄 —— 同一把坏法，
两个时代的两把尺）。这一把钉的是 R271 那次"拆掉时间判据"之后**硬门还在不在**：

  · 时间那条轴（绝对 ms 与倍率）从此只印不判 —— 它被自己的测量证伪了（干净倍率 1.13/1.05/0.96，
    坏法倍率 0.85，比干净还低）；
  · 拆掉它之后，这一把刀必须仍然红，而且必须红在**行为**那两条断言上（盘上出现了文件）。
    若它绿了，就说明"只印不判"其实是把判据拆了 —— 那才是 325 真正的坏结局。

「跑起来了没」按结论行形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
R51 = os.path.join(ROOT, '.scratch', 'motion-audit-2', 'mutate_r51_capture_path_blocked.py')
TEST1 = 'CapturePathWriteBudgetTests/testAddingACopyWritesNothingOnTheMainThread'


def load_arm():
    """从 R51 那张表里取 M249 的 (文件, 锚点, 替换) —— 同一把坏法，不手抄。"""
    src = io.open(R51, encoding='utf-8').read()
    head = src.split('# (编号, 说明, 文件, 锚点, 替换, 过滤器, 必须出现的失败消息, 预期)')[0]
    ns = {'os': os, 'sys': sys}
    exec(compile(head, R51, 'exec'), ns)          # noqa: S101 - 自家表的常量
    m = re.search(r'\("M249",\s*"([^"]*)",\s*(\w+),\s*(\w+),\s*\n?\s*"((?:[^"\\]|\\.)*)"', src)
    if not m:
        raise SystemExit('M831 NOT_RUN 读不到 R51 表里的 M249')
    return ns[m.group(2)], ns[m.group(3)], m.group(4)


def main():
    target, needle, repl = load_arm()
    rel = os.path.relpath(target, ROOT)
    original = io.open(target, encoding='utf-8').read()
    hits = original.count(needle)
    if hits != 1:
        print('M831 NOT_RUN needle 命中 %d 次（要 1）' % hits, flush=True)
        print('R271_MUTATE 刀=1 CAUGHT=0 ESCAPED=0 NOT_RUN=1 RESTORE_CLEAN=yes', flush=True)
        return 1
    try:
        io.open(target, 'w', encoding='utf-8').write(original.replace(needle, repl, 1))
        env = dict(os.environ)
        env.pop('SDKROOT', None)
        env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
        proc = subprocess.run(['swift', 'test', '--filter', TEST1],
                              cwd=os.path.join(ROOT, 'ClipboardHistory'), env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = proc.stdout.decode('utf-8', 'replace')
    finally:
        io.open(target, 'w', encoding='utf-8').write(original)
        if io.open(target, encoding='utf-8').read() != original:
            print('M831 RESTORE_FAILED ⇒ 立刻停表', flush=True)
            return 2
    executed = re.findall(r'Executed (\d+) tests?, with (\d+) failures?', text)
    n_ran, n_fail = (int(executed[-1][0]), int(executed[-1][1])) if executed else (0, 0)
    fails = sorted(set(re.findall(r"error: -\[[\w.]+ (\w+)\] : (XCTAssert\w+) failed", text)))
    got = re.search(r'CAPTURE_PATH_BLOCKED add 用时=([\d.]+)ms 空转基线=([\d.]+)ms 倍率=([\d.]+)', text)
    if not n_ran:
        print('M831 NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）', flush=True)
        print('\n'.join(text.strip().splitlines()[-3:]), flush=True)
        print('R271_MUTATE 刀=1 CAUGHT=0 ESCAPED=0 NOT_RUN=1 RESTORE_CLEAN=yes', flush=True)
        return 1
    behavior = [f for f in fails if f[1].startswith('XCTAssertFalse') or f[1].startswith('XCTAssertTrue')]
    if n_fail and behavior:
        print('M831 CAUGHT  写盘搬回调用线程 = 产品轴 ｜ 红在 '
              + ', '.join('%s(%s)' % (a, b) for a, b in behavior)
              + '（跑=%d 失败=%d）｜ 读数=%s'
              % (n_ran, n_fail, ('倍率=' + got.group(3)) if got else '无'), flush=True)
        print('R271_MUTATE 刀=1 CAUGHT=1 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes', flush=True)
        return 0
    print('M831 %s ｜ 红在 %s（跑=%d 失败=%d）⇒ 时间轴拆掉之后行为判据没接住 = 判据被拆了，不是被换了'
          % ('ESCAPED' if not n_fail else 'WRONG_ASSERTION', fails, n_ran, n_fail), flush=True)
    print('R271_MUTATE 刀=1 CAUGHT=0 ESCAPED=1 NOT_RUN=0 RESTORE_CLEAN=yes', flush=True)
    return 1


if __name__ == '__main__':
    sys.exit(main())
