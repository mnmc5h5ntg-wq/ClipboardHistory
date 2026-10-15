#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R88 的变异电池：看门狗那一族每一处"牙齿"都要被一刀证明它会红。

跑法（先 --measure 看基线，再不带参数跑真刀）：
    python3 .scratch/motion-audit-2/mutate_r88_watchdog.py --measure
    python3 .scratch/motion-audit-2/mutate_r88_watchdog.py

规矩（R62 之后一直沿用）：
  * 动手之前先跑一遍基线，基线不绿就拒跑（否则"红"是谁造成的说不清）；
  * 还原**按内容**而不是 `git checkout --`（新文件没入库时 pathspec 不匹配，刀会留在树上）；
  * 落地没有要看内容变了没有，不能看"原串消失"（纯插入型的刀必然包含原串）；
  * **删东西的刀，变异串里不许留着原 token 的前缀**：M484 / M485 第一版把
    `PROBE_FLOOR_WATCHDOG_MISSED` 改成 `PROBE_FLOOR_WATCHDOG_MISSED_REMOVED_BY_MUTATION`，
    而接线检查用的是子串查 ⇒ 两刀"逃掉"，逃的是我的刀（它什么都没删）。
    与 R86 的 M472 同族反方向：那次是刀里**没带**那个词，这次是**带太多**。
  * `没跑成(NOT-RUN)` 与 `逃掉(ESCAPED)` 分开计数：前者是我的刀坏了，后者才是判据没牙。
"""
import io
import os
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
CI = os.path.join(REPO, '.github/workflows/ci.yml')
REPORT = os.path.join(REPO, 'scripts/ui_probe_report.py')
HARNESS = os.path.join(REPO, '.scratch/motion-audit-2/r88_watchdog_shape.py')
TESTS = os.path.join(REPO, 'scripts/tests/test_ui_probe_report.py')

# 两个验证器：一个测 shell 形状与接线，一个测报告脚本的三格互斥。
VERIFIERS = {
    'harness': ['python3', HARNESS],
    'unittest': ['python3', '-m', 'unittest', 'discover',
                 '-s', 'scripts/tests', '-p', 'test_ui_probe_report.py'],
}


def read(path):
    with io.open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def run(which):
    argv = VERIFIERS[which]
    cwd = REPO if which == 'unittest' else os.path.dirname(HARNESS)
    proc = subprocess.run(argv, cwd=REPO if which == 'unittest' else None,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode('utf-8', 'replace')


def baseline():
    """unittest 走 `python3 -m unittest discover -s scripts/tests`（仓库里 CI 用的就是这条）。"""
    unittest_code = subprocess.run(
        VERIFIERS['unittest'], cwd=REPO,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode
    harness_code = run('harness')[0]
    return unittest_code, harness_code


KNIVES = [
    # (编号, 说明, 文件, 原串, 变异串, 由哪个验证器负责)
    ('M481', '删掉 `set -m` ⇒ 进程组没建起来，kill -- -$pid 退化成杀父',
     CI, '          set -m\n', '', 'harness'),
    ('M482', '组杀改回单 PID 杀（R86–R87 的形状）',
     CI, 'kill -9 -"$pid" 2>/dev/null || true', 'kill -9 "$pid" 2>/dev/null || true', 'harness'),
    ('M483', '报告型那一步不再传 --runner-alive（只剩硬门那一步传 ⇒ 一半出口读不到分诊）',
     CI, 'python3 ../scripts/ui_probe_report.py /tmp/ui.log \\\n            --runner-alive',
     'python3 ../scripts/ui_probe_report.py /tmp/ui.log \\\n            --no-such-flag', 'harness'),
    ('M484', '硬门里删掉孤儿那一格（看门狗失手时 CI 照样绿）',
     CI, 'PROBE_FLOOR_WATCHDOG_MISSED', 'GATE_REMOVED_BY_MUTATION', 'harness'),
    ('M485', '硬门里删掉"没量到就红"那一格（读不到文件时 ${orphans} 会读成 ?，那一格若被删就静默过）',
     CI, 'PROBE_FLOOR_ORPHAN_UNMEASURED', 'GATE_UNMEASURED_REMOVED', 'harness'),
    ('M486', '报告脚本：runner 活着时不再点名"日志丢了"，退回"只报观察"',
     REPORT, '    if runner_alive == 1:', '    if runner_alive == 99:', 'unittest'),
    ('M487', '报告脚本：把 1/0 的语义对调（runner 死了才说"日志丢了"）',
     REPORT, '    if runner_alive == 0:', '    if runner_alive == 1:', 'unittest'),
    ('M488', '报告脚本：--runner-alive 传进坏值时当成"活着"（不许猜）',
     REPORT, '            print("UI_PROBE_RUNNER_ALIVE_UNPARSED=%s ⇒ 这一格不许被读成『已分出成因』" % args.runner_alive)\n            alive = None',
     '            alive = 1', 'unittest'),
]


def main():
    measure = '--measure' in sys.argv
    code_u, code_h = baseline()
    print('基线：unittest=%d harness=%d' % (code_u, code_h))
    if measure:
        print('EXPECTED: 两把验证器都要 0（当前 harness=%d unittest=%d）' % (code_h, code_u))
        return 0
    if code_u != 0 or code_h != 0:
        print('基线不绿 ⇒ 拒跑（否则分不清红是刀造成的还是本来就红的）')
        return 2
    caught = escaped = notrun = 0
    for tag, note, path, old, new, which in KNIVES:
        original = read(path)
        hits = original.count(old)
        print('%s %s' % (tag, note))
        if hits != 1:
            print('   NOT-APPLIED 锚点命中 %d 次（要求恰好 1 次）⇒ 这一刀没动过文件' % hits)
            notrun += 1
            continue
        write(path, original.replace(old, new, 1))
        if read(path) == original:
            print('   NOT-RUN 写盘之后文件没变')
            notrun += 1
            continue
        try:
            code, out = run(which)
        except Exception as error:            # 验证器自己起不来 ⇒ 是我的刀坏了，不是判据没牙
            print('   NOT-RUN 验证器异常：%s' % error)
            notrun += 1
            write(path, original)
            continue
        finally:
            pass
        write(path, original)
        if read(path) != original:
            print('   !! 还原失败：%s' % path)
            return 3
        if code != 0:
            print('   CAUGHT（%s 退出 %d）' % (which, code))
            caught += 1
        else:
            print('   ESCAPED（%s 仍然 0）' % which)
            tail = [l for l in out.splitlines() if 'ESCAPED' in l or 'FAIL' in l][:3]
            for line in tail:
                print('     | %s' % line)
            escaped += 1
    print('汇总：%d 刀 CAUGHT / %d 逃掉 / %d 没跑成（共 %d）'
          % (caught, escaped, notrun, len(KNIVES)))
    return 1 if (escaped or notrun) else 0


if __name__ == '__main__':
    sys.exit(main())
