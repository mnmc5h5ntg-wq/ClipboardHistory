#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R224 的变异表：左轴尺的**坐标约定**（BACKLOG 246 的修法本体）两把刀。

对象是 `scripts/surface_left_axes.py` 自己 ⇒ 跑的是它的 `--self-test`，判据是退出码与 SELFTEST 行。

来历（本轮 ⓪ 的读数）：runner 那一跑（run 39273827335 = `69bccbd`）7 颗探针全部
`cause=no-bg-window frame=420x300 / 720x540 / 720x520` —— 帧**拍到了、尺寸也对**，
掉到画外的是取底窗口：旧表把窗口写在**本机 @2x 帧的像素**上（统计页的 bg 写在 y=900..960，
而 @1x 的帧只有 540 高）。所以那 7 个 NOT_RUN 量的是这把尺的坐标约定，不是产品。
修法是"窗口按 pt 写 + 像素每 pt 由帧自己算"，配一格缩放不变量对照（同一份内容 @2x/@1x 读数逐字相等）。

M761 把"像素每 pt"写死成 2（= 只认本机这一档）⇒ 缩放不变量那格必须红。
     这一刀钉的是**别把今天这台机器的密度当成契约**（R38 那一族：两台机器的读数不能互当对方）。
M762 把 pt→px 的换算整个去掉（窗口原样当像素用）⇒ 同一格必须红，而且红回的是旧形状。
     这一刀是"改之前那把尺在 @1x 上根本没有对象"的可复查版本。

两把刀都只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
RULER = 'scripts/surface_left_axes.py'
LABEL = u'正对照·两档缩放同读数'

ARMS = [
    ('M761', u'把「像素每 pt」写死成 2（只认本机 @2x 那一档）', RULER,
     "    ppp = W / float(pt_w)",
     "    ppp = 2.0",
     LABEL),
    ('M762', u'去掉 pt→px 的换算（窗口原样当像素 = R224 之前的形状）', RULER,
     "    return tuple(int(round(v * ppp)) for v in rect)",
     "    return tuple(rect)",
     LABEL),
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
    print('R224_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
