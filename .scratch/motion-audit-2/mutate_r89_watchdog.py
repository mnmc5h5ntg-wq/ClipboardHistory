#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R89 的变异电池：看门狗那一刀的**位置**、两份读数的**落盘**、硬门的**顺序**，各有一刀。

规矩沿用 R62/R88：先跑基线（不绿就拒跑）、按内容还原、纯插入型看"文件变了没有"、
`没跑成` 与 `逃掉` 分开计数，删除型变异的替换串**不许留着原 token 的前缀**（R88 的 U-189）。

用法：
    python3 .scratch/motion-audit-2/mutate_r89_watchdog.py --measure
    python3 .scratch/motion-audit-2/mutate_r89_watchdog.py
"""
import os
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
CI = os.path.join(REPO, '.github/workflows/ci.yml')
HARNESS = os.path.join(REPO, '.scratch/motion-audit-2/r89_watchdog_shape.py')

LOOP = '''          for child in $(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests" 2>/dev/null || true); do
            cpgid=$(ps -o pgid= -p "$child" 2>/dev/null | tr -d ' ' || true)
            if [ -n "$cpgid" ]; then kill -9 -"$cpgid" 2>/dev/null || true; fi
          done
'''


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def run_harness():
    proc = subprocess.run([sys.executable, HARNESS], cwd=REPO,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode('utf-8', 'replace')


def ui_step_span(text):
    start = text.index(u'- name: On-screen interaction probes')
    end = text.index(u'- name: On-screen probe coverage floor')
    return start, end


def in_ui_step(text, old, new):
    """只在**那一步的正文里**替换：`wait "$pid" && status=0 || status=$?` 这种行在动效那一步也有，
    整文件替换会命中多处 —— 刀就会改到别人身上（R85 那族"锚点不唯一"的老账）。"""
    a, b = ui_step_span(text)
    seg = text[a:b]
    assert seg.count(old) >= 1, u'刀在这一步里找不到锚点：%s' % old[:60]
    return text[:a] + seg.replace(old, new, 1) + text[b:]


def move_loop_before_wait(text):
    """整块搬到 `wait "$pid"` 之前 —— 这就是 R89 本机对照抓到的那种竞态放置。"""
    assert text.count(LOOP) == 1
    text = text.replace(LOOP, '', 1)
    return in_ui_step(text,
                      u'          wait "$pid" && status=0 || status=$?\n',
                      LOOP + u'          wait "$pid" && status=0 || status=$?\n')


def measure_before_cleanup(text):
    """把孤儿计数挪到残留收杀**之前**（那一格会永远读到 ≥1，红得没有意义）。"""
    old = (u'          orphans=$(pgrep -f "xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests"'
           u" 2>/dev/null | wc -l | tr -d ' ' || true)\n")
    assert text.count(old) == 1 and text.count(LOOP) == 1
    text = text.replace(old, '', 1)
    return text.replace(LOOP, old + LOOP, 1)


def gate_first(text):
    """把 `Motion coverage floor` 挪回证据步骤之前（R88 交出去的那个形状）。"""
    lines = text.split('\n')
    start = next(i for i, l in enumerate(lines) if l.startswith('      - name: Motion coverage floor'))
    nxt = [i for i in range(start + 1, len(lines)) if lines[i].startswith('      - name: ')]
    end = nxt[0] if nxt else len(lines)     # 它现在是最后一步，没有下一个 - name
    block = lines[start:end]
    del lines[start:end]
    at = next(i for i, l in enumerate(lines) if l.startswith('      - name: Motion filmstrip'))
    return '\n'.join(lines[:at] + block + lines[at:])


def drop_always(text):
    return text.replace(u'        if: always()\n', u'', 1)


def drop_orphan_file(text):
    return in_ui_step(text, u'          echo "${orphans:-0}" > /tmp/ui-orphans\n', u'')


def drop_alive_file(text):
    return in_ui_step(text, u'            echo "${alive:-0}" > /tmp/ui-runner-alive\n', u'')


def single_pid_kill(text):
    return in_ui_step(text, u'kill -9 -"$pid" 2>/dev/null || true', u'kill -9 "$pid" 2>/dev/null || true')


# (编号, 说明, 变换函数, 期望)
KNIVES = [
    ('M489', u'删掉"再杀残留孩子的组"那一整块（R88 的形状原样留在树上）',
     lambda t: t.replace(LOOP, '', 1)),
    ('M490', u'把那一块搬到 `wait` 之前（同一段代码，位置错了就是竞态）',
     move_loop_before_wait),
    ('M491', u'把孤儿计数挪到残留收杀之前（那一格永远读到 ≥1）',
     measure_before_cleanup),
    ('M492', u'删掉一道硬门的 `if: always()`（一朵红又会 skip 掉后面的证据）',
     drop_always),
    ('M493', u'把 `Motion coverage floor` 挪回动效卷之前（顺序修复被撤销）',
     gate_first),
    ('M494', u'不写 /tmp/ui-orphans（下一步是另一个 shell，拿不到依据）',
     drop_orphan_file),
    ('M495', u'不写 /tmp/ui-runner-alive（93 的分诊读数没有来源）',
     drop_alive_file),
    ('M496', u'组杀退回单 PID 杀（R86–R87 的形状）',
     single_pid_kill),
]


def main():
    original = read(CI)
    code, out = run_harness()
    print('基线：harness=%d' % code)
    if '--measure' in sys.argv:
        print('EXPECTED: harness=0（当前 %d）' % code)
        return 0
    if code != 0:
        print('基线不绿 ⇒ 拒跑\n' + out[-800:])
        return 2
    caught = escaped = notrun = 0
    for tag, note, fn in KNIVES:
        print('%s %s' % (tag, note))
        try:
            mutated = fn(original)
        except Exception as error:
            print('   NOT-RUN 刀自己坏了：%r' % error)
            notrun += 1
            continue
        if mutated == original:
            print('   NOT-RUN 这一刀什么都没改（刀坏了，不是判据没牙）')
            notrun += 1
            continue
        write(CI, mutated)
        code, out = run_harness()
        write(CI, original)
        if read(CI) != original:
            print('   !! 还原失败')
            return 3
        if code != 0:
            missing = [l for l in out.splitlines() if u'缺：' in l or 'ESCAPED' in l]
            print('   CAUGHT（harness 退出 %d）%s' % (code, missing[:1]))
            caught += 1
        else:
            print('   ESCAPED（harness 仍然 0）')
            escaped += 1
    print('汇总：%d 刀 CAUGHT / %d 逃掉 / %d 没跑成（共 %d）'
          % (caught, escaped, notrun, len(KNIVES)))
    return 1 if (escaped or notrun) else 0


if __name__ == '__main__':
    sys.exit(main())
