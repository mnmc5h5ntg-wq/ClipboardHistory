#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R234 变异刀：表格不再吃"代码的那块灰底"这一判，是不是真的有牙。

形状沿用 mutate_r233，但这一轮被审的是 **Swift 产品文件** ⇒ 卷是 `swift test --filter Round4MarkdownTests`。
刀号接 M783 ⇒ M784 / M785（全局唯一；`cross_table_ids` 会扫全部 mutate_r*.py 查重）。
"""
import os
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
PKG = os.path.join(ROOT, 'ClipboardHistory')
PRES = os.path.join(PKG, 'Sources/ClipboardHistoryApp/Utilities/MarkdownPresentation.swift')

FILTER = 'Round4MarkdownTests'

KNIVES = [
    ('M784', PRES,
     '        if case .table = block.kind { return false }\n',
     '',
     '把表格重新塞回代码那块灰底 ⇒ 新格必须红在"表格那一行仍被涂了底色"'),
    ('M785', PRES,
     '        case .codeBlock, .table: return true\n        default: return false',
     '        case .codeBlock: return true\n        default: return false',
     '撤底色的代价如果是连等宽一起丢 ⇒ 说"表格靠等宽保住列对齐"那一句必须红'),
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
base_rc = run_roll('/tmp/r234_mutate_base.log')
if base_rc != 0:
    print('R234_MUTATE 基线就红 ⇒ 先修判据再下刀（不许在红树上记 CAUGHT）')
    sys.exit(1)

caught = escaped = not_run = 0
for kid, path, anchor, repl, why in KNIVES:
    original = read(path)
    hits = original.count(anchor)
    if hits != 1:
        print('%s NOT_RUN 锚点命中 %d 次（要恰好 1 次）｜%s' % (kid, hits, why))
        not_run += 1
        continue
    log = '/tmp/r234_mutate_%s.log' % kid
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
    if rc != 0 and names:
        caught += 1
        print('%s CAUGHT ｜ %s ｜ 红在：%s' % (kid, why, '、'.join(sorted(set(names)))))
    elif rc != 0:
        not_run += 1
        print('%s NOT_RUN ⇒ rc=%d 但红没有名字（崩栈/编译错不是证人，修刀）｜%s' % (kid, rc, why))
    else:
        escaped += 1
        print('%s ESCAPED ⇒ rc=0（绿就是证人没在判）｜%s' % (kid, why))
    if not restored:
        print('%s RESTORE_FAILED ⇒ 树是脏的，后面的读数都不算' % kid)
        sys.exit(1)

dirty = [p for p, text in ORIG.items() if read(p) != text]
clean = not dirty
print('R234_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d'
      % (len(KNIVES), caught, escaped, not_run))
print('RESTORE_CLEAN=%s%s' % ('yes' if clean else 'no', '' if clean else ' ｜还脏着：' + '、'.join(dirty)))
sys.exit(0 if (escaped == 0 and not_run == 0 and caught == len(KNIVES) and clean) else 1)
