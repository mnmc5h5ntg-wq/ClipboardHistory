#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R296 的变异表（第 295 轮 / Round 293）：0 告警那道门**本体**（BACKLOG 343 的下半场）。

门本体是 `scripts/warning_gate.sh`，`round_verify.sh` 的第 1 步现在调它并且会被它拦下。
这一张表判的不是 swift 用例，而是**一支 shell 门的退出码**，所以判定按退出码 + 正文里的键，
不看 Test Case 行（没有测试可红 = 没有结论行 ≠ 通过；这里"跑起来了没"由门自己打印的
`ROUND_WARNING_GATE` 那一行签）。

· M862 **注入一条真告警** —— 往测试靶的一个函数里塞 `let unusedR296Probe: Int = 1`
  （Swift 会打 initialization of immutable value was never used）。门必须 exit 1 且正文含
  `ROUND_WARNING_GATE_FAIL`。这一把钉的是"门到底拦不拦"：343 之前的形态是**只印不拦**，
  注入十条告警它也会打一行 `build_warnings=10` 然后继续往下跑。
· M863 **把冷编那一步换成必然失败的命令** —— 门必须 exit 2（`warnings=NOT-RUN`），
  不许 exit 0。这一把钉的是"0 的另一种成因"：尺没跑到编译器时，数出来的一条告警都没有，
  读成"干净"就是假绿（R100 那一族：仪器坏在哪个方向，结论就往哪个方向假）。

根由 `__file__` 推（D-260/D-262）；needle 必须恰好命中一次，还原必须逐字节一致。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GATE = 'scripts/warning_gate.sh'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'

SIG = u'    func testPressTravelSharesOneRulerWithTheSystemReference() throws {\n'
PROBE = SIG + u'        let unusedR296Probe: Int = 1\n'
COLD_NEEDLE = u'( cd "$ROOT/ClipboardHistory" && swift build --build-tests --scratch-path "$RUN/warninggate-build" ) > "$COLD" 2>&1'
COLD_BROKEN = u'false > "$COLD" 2>&1'

# (刀号, 说明, 目标文件, needle, 替换, 期望退出码, 期望正文里的键, 运行目录)
ARMS = [
    ('M862', u'注入一条未使用常量 = 门拦不拦', HARNESS, SIG, PROBE,
     1, 'ROUND_WARNING_GATE_FAIL', '/tmp/wg_r296_knife_a'),
    ('M863', u'冷编换成必然失败的命令 = 不许把尺坏读成干净', GATE, COLD_NEEDLE, COLD_BROKEN,
     2, 'warnings=NOT-RUN', '/tmp/wg_r296_knife_b'),
]


def read(path):
    with io.open(os.path.join(ROOT, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(os.path.join(ROOT, path), 'w', encoding='utf-8') as handle:
        handle.write(text)


def run_gate(run_dir):
    proc = subprocess.run(['bash', GATE, run_dir], cwd=ROOT,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode('utf-8', 'replace')


def run_arm(arm_id, why, target, needle, repl, want_code, want_text, run_dir):
    original = read(target)
    hits = original.count(needle)
    if hits != 1:
        print('%s NOT_RUN needle 命中 %d 次（要恰好 1）' % (arm_id, hits), flush=True)
        return 'NOT_RUN'
    try:
        write(target, original.replace(needle, repl, 1))
        code, text = run_gate(run_dir)
    finally:
        write(target, original)
        if read(target) != original:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 'RESTORE_FAILED'
    if not text.strip():
        print('%s NOT_RUN 门没有输出（跑起来了没要由它自己那一行签）' % arm_id, flush=True)
        return 'NOT_RUN'
    head = [l for l in text.splitlines() if l.startswith('ROUND_WARNING_GATE')]
    if not head:
        print('%s NOT_RUN 没打印 ROUND_WARNING_GATE 结论行 ⇒ 无从判定' % arm_id, flush=True)
        return 'NOT_RUN'
    ok_code = code == want_code
    ok_text = want_text in text
    if ok_code and ok_text:
        print('%s CAUGHT  %s ｜ exit=%d（期望 %d）｜ %s' % (arm_id, why, code, want_code, head[-1]), flush=True)
        return 'CAUGHT'
    print('%s %s ｜ exit=%d 期望 %d、正文含「%s」=%s ｜ %s'
          % (arm_id, 'WRONG_VERDICT' if head else 'ESCAPED', code, want_code, want_text,
             ok_text, head[-1] if head else u'（无结论行）'), flush=True)
    return 'ESCAPED'


def main():
    only = set(sys.argv[1:])
    arms = [a for a in ARMS if not only or a[0] in only]
    if only - set(a[0] for a in ARMS):
        print('R296_MUTATE NOT_RUN 未知刀号 %s' % sorted(only - set(a[0] for a in ARMS)), flush=True)
        return 1
    kinds = [run_arm(*a) for a in arms]
    caught = kinds.count('CAUGHT')
    escaped = kinds.count('ESCAPED')
    not_run = sum(1 for k in kinds if k in ('NOT_RUN', 'RESTORE_FAILED'))
    clean = 'yes' if 'RESTORE_FAILED' not in kinds else 'no'
    print('R296_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=%s'
          % (len(arms), caught, escaped, not_run, clean), flush=True)
    return 0 if (caught == len(arms) and clean == 'yes') else 1


if __name__ == '__main__':
    sys.exit(main())
