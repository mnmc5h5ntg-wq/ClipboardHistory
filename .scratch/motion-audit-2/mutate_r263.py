#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R263 的变异表：收藏星**字形墨**那一抬，两轴各一把刀（D-244）。

对象是产品源码（`HistoryRowViews.swift`），判据是本轮新增的
`UICaptureTests/testFavoriteGlyphInkClearsTheInteractiveFloor`（它自己 render → PNG → 像素，
所以这两把刀**不必重捕帧** —— 与 D-240 那族"重捕型"不同：那族量的产物在磁盘上，这一格量的产物
在测试进程里现渲染。这条区分要写在账上，否则下一轮会以为"改了产品没重捕"）。

M823 把悬停那一抬抹平（`isHoveredForDrawing ? 0.78 : 0.55` → 恒 0.55）⇒
     "悬停必须比静置更清楚"那条断言必须红。这一刀钉的是**令牌轴**：抬量本身算不算数。
M824 把画法改回读裸 `isHovered`（数值一字未动）⇒
     接线那三条断言与比值断言都必须红 —— 屏幕上什么都没变，但帧里那一抬又不存在了
     （R219/R225 同一族：令牌对、调用点没接 = 量不到，而量不到会被记成"没问题"）。
     这一刀钉的是**产品轴**：画法有没有接进取证通道。

两把刀都只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"跑起来了没"按结论行的**形状**认（R262 的教训：写死颗数的那一版在卷子长到 6 条之后
把真红读成 NOT_RUN），并且没有结论行一律 NOT_RUN —— 编译红不算 CAUGHT（D-243）。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
ROWS = 'ClipboardHistory/Sources/ClipboardHistoryApp/Views/HistoryRowViews.swift'
FILTER = 'UICaptureTests/testFavoriteGlyphInkClearsTheInteractiveFloor'
NEEDLE = 'Color.primary.opacity(isHoveredForDrawing ? 0.78 : 0.55)'

ARMS = [
    ('M823', u'抹平悬停那一抬（字形墨恒 0.55）⇒ 两态比值必须分不开 = 令牌轴', ROWS,
     NEEDLE, 'Color.primary.opacity(0.55)'),
    ('M824', u'画法读回裸 isHovered（数值一字未动）⇒ 接线与比值都必须红 = 产品轴', ROWS,
     NEEDLE, 'Color.primary.opacity(isHovered ? 0.78 : 0.55)'),
]


def read(p):
    with io.open(os.path.join(ROOT, p), encoding='utf-8') as h:
        return h.read()


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
        if not n_ran:
            not_run += 1
            print('%s NOT_RUN 没有结论行（编译红不算 CAUGHT = D-243）：%s' % (arm_id, why), flush=True)
            continue
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ 红在 %s（跑=%d exit=%d）'
                  % (arm_id, why, ', '.join(names) or '仅 exit 非 0', n_ran, code), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s ⇒ %s' % (arm_id, why, FILTER.split('/')[-1]), flush=True)
    print('R263_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
