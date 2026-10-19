#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R231 第二批变异刀：设置侧栏那一行的**像素证人**是不是真的承重（BACKLOG 258）。

为什么这一轮非得下刀：新判据 `testSettingsRowHoverFillIsVisibleOnItsOwnSurface` 的绿
现在由两件事撑着 —— 产品侧那条 `hoveredForCapture` 的出口、夹具侧那一次
`.environment(…, true)`。两处任一处被摘掉，帧就变成"两帧同值"，而一条只比值的尺
很容易把"量不到"读成"比值 1.000 ⇒ 淡"甚至读成 skip。刀要证的正是**它必须红，不许 skip**。

刀号接本轮第一批 M775 / M776 ⇒ M777 / M778（全局唯一，先在台账查重）。
"""
import os
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
PKG = os.path.join(ROOT, 'ClipboardHistory')
SETTINGS = os.path.join(PKG, 'Sources/ClipboardHistoryApp/Views/SettingsView.swift')
HARNESS = os.path.join(PKG, 'Tests/ClipboardHistoryAppTests/UICaptureHarness.swift')

FILTER = 'UICaptureTests/testSettingsRowHoverFillIsVisibleOnItsOwnSurface'

# (刀号, 文件, 锚点【必须恰好命中一次】, 替换成【退回的形状】, 这一刀要证的病)
KNIVES = [
    ('M777', SETTINGS,
     'guard isHovered || (hoveredForCapture ?? false) else { return 0 }',
     'guard isHovered else { return 0 }',
     '产品侧摘掉取证通道出口 ⇒ 两帧同值，判据该按比值与"同灰阶"那两格红（不是 skip）'),
    ('M778', HARNESS,
     'SettingsSidebarRow(category: .privacy, isSelected: false, action: {})\n'
     '                .environment(\\.hoveredForCapture, true)',
     'SettingsSidebarRow(category: .privacy, isSelected: false, action: {})\n'
     '                .environment(\\.hoveredForCapture, false)',
     '夹具侧把点亮写成 false ⇒ 证人自己失效时判据必须红，不许把"两帧同值"读成通过'),
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
base_rc = run_roll('/tmp/r231b_mutate_base.log')
if base_rc != 0:
    print('R231B_MUTATE 基线就红 ⇒ 先修判据再下刀（不许在红树上记 CAUGHT）')
    sys.exit(1)

caught = escaped = not_run = 0
skips = 0
for kid, path, anchor, repl, why in KNIVES:
    original = read(path)
    hits = original.count(anchor)
    if hits != 1:
        print('%s NOT_RUN 锚点命中 %d 次（要恰好 1 次）｜%s' % (kid, hits, why))
        not_run += 1
        continue
    log = '/tmp/r231b_mutate_%s.log' % kid
    write(path, original.replace(anchor, repl, 1))
    try:
        rc = run_roll(log)
    finally:
        write(path, original)
    restored = read(path) == original
    names, skipped = [], 0
    with open(log, 'r', encoding='utf-8', errors='replace') as fh:
        for line in fh:
            if "' failed" in line and 'Test Case' in line:
                names.append(line.split('Test Case')[-1].split("'")[1] if "'" in line else line.strip())
            if "' skipped" in line and 'Test Case' in line:
                skipped += 1
    # 红与 skip 是两个方向：这一族判据把"环境判不了"写成 skip 也算逃（尺没坏，产品没判）。
    if rc != 0 and skipped == 0:
        caught += 1
        print('%s CAUGHT ｜ %s ｜ 红在：%s' % (kid, why, '、'.join(sorted(set(names)))))
    else:
        escaped += 1
        print('%s ESCAPED ⇒ rc=%d skipped=%d（绿或 skip 都算逃）｜%s' % (kid, rc, skipped, why))
    if not restored:
        print('%s RESTORE_FAILED ⇒ 树是脏的，后面的读数都不算' % kid)
        sys.exit(1)

dirty = [p for p, text in ORIG.items() if read(p) != text]
clean = not dirty
print('R231B_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d'
      % (len(KNIVES), caught, escaped, not_run))
print('RESTORE_CLEAN=%s%s' % ('yes' if clean else 'no', '' if clean else ' ｜还脏着：' + '、'.join(dirty)))
sys.exit(0 if (escaped == 0 and not_run == 0 and caught == len(KNIVES) and clean) else 1)
