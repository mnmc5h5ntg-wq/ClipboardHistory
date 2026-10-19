#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R221 的变异表：NOT_RUN 的成因分档（BACKLOG 246 的仪器）两把刀。

对象是 `scripts/surface_left_axes.py` 自己 —— 这一轮没有 Swift 侧的改动，
所以跑的是**尺的自检**（`--self-test`），判据就是它自己的退出码与那几行 SELFTEST。

M757 把"底不纯"那一档的成因**混进** no-ink（`absence('bg-not-flat', …)` ⇒ `absence('no-ink', …)`）⇒
     自测里新加的"反对照·底不纯的成因"必须红。
     这一刀就是 246 开单的理由本身：三种成因的处置相反（帧没画 / 窗口无墨 / 底不纯要修尺），
     混成一档等于下一轮还要重问，而且会把"尺自己的前提没成立"读成"这台机器画不出这块表面"。
M758 把缺席判定改成恒不缺席（`if r is None or not r.get('ok'):` ⇒ `if False:`）⇒
     自测里"反对照·全空帧"与两格成因对照必须一起红（缺席被当成通过 = 假绿通道）。

两把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
RULER = 'scripts/surface_left_axes.py'

ARMS = [
    ('M757', u'把「底不纯」的成因混进 no-ink（246 要拦的就是这一档）', RULER,
     "        return absence('bg-not-flat', bg=bg)",
     "        return absence('no-ink', bg=bg)",
     u'反对照·底不纯的成因'),
    ('M758', u'缺席判定改成恒不缺席（把没有对象当成通过）', RULER,
     "        if r is None or not r.get('ok'):",
     "        if False:",
     u'反对照·全空帧'),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(_unused):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    proc = subprocess.run([sys.executable, RULER, '--self-test'], cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    bad = bool(re.search(r'LEFT_AXIS_SELFTEST bad', text))
    return proc.returncode, (0 if bad else 1), bad, text


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, label in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, failed, text = run(label)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 2
        if n_ran == 0 and not failed:
            not_run += 1
            print('%s NOT_RUN 自检既没绿也没红 ⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        line = [l for l in text.splitlines() if label in l]
        note = line[0][:96] if line else u'找不到那一格对照（标签漂了）'
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ %s ｜ %s' % (arm_id, label, why, note), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s ｜ %s ｜ %s' % (arm_id, label, why, note), flush=True)
    print('R221_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
