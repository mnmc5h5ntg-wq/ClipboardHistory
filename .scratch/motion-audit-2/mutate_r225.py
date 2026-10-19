#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R225 的变异表：浮层悬停那一档的**按色档抬墨**（产品改动）两把刀。

对象是产品源码 `ClipboardHistory/Sources/.../Managers/QuickPickController.swift`，
判据是新增的 `QuickPickHoverInkTests`（跑 `swift test --filter`，按 `FAIL:` 行认红）。

M763 把亮档那一抬去掉（`hoverFillAlpha + lightHoverLift` ⇒ `hoverFillAlpha`）⇒
     两档回到"一个数管两档"，亮档 1.14:1 掉在仓库自己的 1.20 地板下 ⇒ 必须红。
M764 把画法搬回不分色档的老令牌 ⇒ 数值仍然是对的，但**产品不再读它**（R219 那一族：
     令牌写对了、调用点没接 = 屏幕上什么都没变）⇒ 源码守卫必须红。

两把刀都只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
TARGET = 'ClipboardHistory/Sources/ClipboardHistoryApp/Managers/QuickPickController.swift'
FILTER = 'QuickPickHoverInkTests'

ARMS = [
    ('M763', u'去掉亮档那一抬（两档又共用一个数）',
     "        dark ? hoverFillAlpha : hoverFillAlpha + lightHoverLift",
     "        dark ? hoverFillAlpha : hoverFillAlpha"),
    ('M764', u'画法搬回不分色档的老令牌（数值对、产品没接）',
     "        NSColor.labelColor.withAlphaComponent(QuickPickController.hoverFillAlpha(dark: dark)).setFill()",
     "        NSColor.labelColor.withAlphaComponent(QuickPickController.hoverFillAlpha).setFill()"),
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
    fails = set(re.findall(r"'s test case '([^']+)' failed|Test Case '.*?\.(test\w+)' failed", text))
    names = sorted({a or b for a, b in fails})
    ran = ('Executed 2 tests' in text) or ('Test Suite ' in text)
    return proc.returncode, (1 if ran else 0), bool(names) or proc.returncode != 0, text, names


def main():
    caught = escaped = not_run = 0
    for arm_id, why, needle, repl in ARMS:
        original = read(TARGET)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        try:
            write(TARGET, original.replace(needle, repl, 1))
            code, n_ran, failed, text, names = run()
        finally:
            write(TARGET, original)
            if read(TARGET) != original:
                print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
                return 2
        if not n_ran:
            not_run += 1
            print('%s NOT_RUN 那一卷根本没跑起来（编译失败？）⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        if failed:
            caught += 1
            print('%s CAUGHT  %s ｜ 红在 %s' % (arm_id, why, ', '.join(names) or 'exit=%d' % code), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s' % (arm_id, why), flush=True)
    print('R225_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
