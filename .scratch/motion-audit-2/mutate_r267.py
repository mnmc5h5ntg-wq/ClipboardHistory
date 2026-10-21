#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R267 的变异表：写盘失败的「有人发布」这一半，一把刀（产品轴）。

对象是产品源码（`DailyCopyLedger.syncWriteFailure`），判据是本轮改过形状的
`DailyCopyHeatmapTests.testWriteFailureBecomesVisibleWithoutAnotherCopy`
（它现在**等条件而不是等挂钟**，见该格注释）。

M825 把镜像那一行换成 `_ = message` —— 盒子仍有值、`@Published` 永不发布 ⇒
     设置页不会重绘，用户看不到那一行。这一刀钉的是"发布"这半条，
     与 R9 当年钉住的"值不丢"那半条是两回事（那条当时就是被"计算属性读盒子"糊过去的）。

本轮**不需要重捕帧**：这一格量的是对象发布次数与盒子值，产物不在磁盘上（D-240 的分界）。
"跑起来了没"按结论行形状认；没有结论行一律 NOT_RUN（编译红不算 CAUGHT = D-243）。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
LEDGER = 'ClipboardHistory/Sources/ClipboardHistoryApp/Managers/DailyCopyLedger.swift'
FILTER = 'DailyCopyHeatmapTests/testWriteFailureBecomesVisibleWithoutAnotherCopy'

ARMS = [
    ('M825', u'镜像那一行不再发布（盒子有值、@Published 不动）= 产品轴', LEDGER,
     '            lastWriteError = message', '            _ = message'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run():
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    proc = subprocess.run(['swift', 'test', '--filter', FILTER], cwd=os.path.join(ROOT, 'ClipboardHistory'),
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    names = sorted(set(re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", text)))
    executed = re.findall(r'Executed (\d+) tests?, with (\d+) failures?', text)
    n_ran = int(executed[-1][0]) if executed else 0
    return proc.returncode, n_ran, bool(names), text, names


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
            code, n_ran, failed, text, names = run()
        finally:
            write(target, original)
            if read(target) != original:
                print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
                return 2
        waited = re.findall(r'LEDGER_WRITE_ERROR_VISIBLE waited_ms=(\d+)', text)
        tail = ' 等待读数=' + ('/'.join(waited) + 'ms' if waited else '无')
        if not n_ran:
            not_run += 1
            print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）：%s' % (arm_id, why), flush=True)
            continue
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ 红在 %s（跑=%d）%s'
                  % (arm_id, why, ', '.join(names) or '仅 exit 非 0', n_ran, tail), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s%s' % (arm_id, why, tail), flush=True)
    print('R267_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
