#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R231 变异刀：名册（`knownPending`）清空之后，这两处换算**退回去会不会红**。

为什么这一轮非得下刀：本轮把册子从 3 降到 0，而一张空册子最容易骗人的地方是
"它已经不判任何东西了" —— 空断言恒真。所以刀要证的正是：**退一处回去，两条守卫都得红**
（名册那条按 `strays` 红、跨文件那条按行数红）。

刀号接 R230 的 M771…M774 ⇒ 本轮 M775 / M776（全局唯一，先在台账查重）。
"""
import os
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
PKG = os.path.join(ROOT, 'ClipboardHistory')
DETAIL = os.path.join(PKG, 'Sources/ClipboardHistoryApp/Views/DetailView.swift')
SETTINGS = os.path.join(PKG, 'Sources/ClipboardHistoryApp/Views/SettingsView.swift')

FILTER = ('ControlHoverLadderTests/testEveryHoverTokenReaderGoesThroughTheSharedConversionOrIsOnTheRoster'
          '|UICaptureTests/testOverlayHoverPolicyIsATruthTableAndSharesItsTokenWithTheSidebar')

# (刀号, 文件, 锚点【必须恰好命中一次】, 替换成【把这一处退回旧形状】, 这一刀要证的病)
KNIVES = [
    ('M775', DETAIL,
     '.fill(.primary.opacity(isHovered\n'
     '                                ? HoverInk.opacity(level: VisualFill.hover, dark: colorScheme == .dark) : 0))',
     '.fill(.primary.opacity(isHovered ? VisualFill.hover : 0))',
     'chip 那一层退回直读令牌 ⇒ 名册应报 strays、跨文件那条应报行数 2≠1'),
    ('M776', SETTINGS,
     'guard isHovered else { return 0 }\n'
     '        return HoverInk.opacity(level: VisualFill.hover, dark: colorScheme == .dark)',
     'return isHovered ? VisualFill.hover : 0',
     '设置侧栏行那一层退回直读令牌 ⇒ 名册应报 strays'),
]


def read(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)


def run_roll(log):
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    with open(log, 'w', encoding='utf-8') as fh:
        proc = subprocess.run(['swift', 'test', '--filter', FILTER], cwd=PKG, env=env,
                              stdout=fh, stderr=subprocess.STDOUT)
    return proc.returncode


ORIG = {p: read(p) for _, p, _, _, _ in KNIVES}
ENV = 'R231_MUTATE_ENV'
env = dict(os.environ)
env.pop('SDKROOT', None)
# 先确认这两格在**未变异**的树上真的会跑（否则 CAUGHT 是恒真的假账）。
base_rc = run_roll('/tmp/r231_mutate_base.log')
base_red = base_rc != 0
if base_red:
    print('R231_MUTATE 基线就红 ⇒ 先修判据再下刀（不许在红树上记 CAUGHT）')
    sys.exit(1)

caught = escaped = not_run = 0
for kid, path, anchor, repl, why in KNIVES:
    original = read(path)
    hits = original.count(anchor)
    if hits != 1:
        print('%s NOT_RUN 锚点命中 %d 次（要恰好 1 次）｜%s' % (kid, hits, why))
        not_run += 1
        continue
    log = '/tmp/r231_mutate_%s.log' % kid
    write(path, original.replace(anchor, repl, 1))
    try:
        rc = run_roll(log)
    finally:
        write(path, original)
    restored = read(path) == original
    names = []
    with open(log, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if "' failed" in line and 'Test Case' in line:
                names.append(line.split('Test Case')[-1].split("'")[1] if "'" in line else line.strip())
    if rc != 0:
        caught += 1
        print('%s CAUGHT ｜ %s ｜ 红在：%s' % (kid, why, '、'.join(sorted(set(names)))))
    else:
        escaped += 1
        print('%s ESCAPED ⇒ 名册空了之后这条守卫是恒真的（本轮的修法等于没钉住）｜%s' % (kid, why))
    if not restored:
        print('%s RESTORE_FAILED ⇒ 树是脏的，后面的读数都不算' % kid)
        sys.exit(1)

dirty = [p for p, text in ORIG.items() if read(p) != text]
clean = not dirty
print('R231_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d' % (len(KNIVES), caught, escaped, not_run))
print('RESTORE_CLEAN=%s%s' % ('yes' if clean else 'no', '' if clean else ' ｜还脏着：' + '、'.join(dirty)))
sys.exit(0 if (escaped == 0 and not_run == 0 and caught == len(KNIVES) and clean) else 1)
