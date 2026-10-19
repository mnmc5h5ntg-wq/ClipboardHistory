#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R220 的表面账同步：把「主窗口/详情区 × 加载」那一格的 reason/evidence 补上 R219 与本轮的判据。

先按**生成器**改（`make_surface_ledger.py` 是这本账的源，JSON 是产物）：
生成器里找得到那句 reason ⇒ 改生成器再重跑产物；找不到 ⇒ 说明这本账已经不由它生成了，
那就直接改 JSON 并在结论行里写明白（不许悄悄改产物还宣称"生成器同步过"）。
两道自检：行数必须仍是 162、那一格的 verdict 必须仍是 added（本轮是**补理由**，不是翻判法）。
"""
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
GEN = '.scratch/motion-audit-2/make_surface_ledger.py'
LEDGER = 'docs/motion_surface_ledger.json'
ANCHOR = u'spinner 说「我在等」'
ADD_REASON = (u'；亮档的墨按档给（R219 / BACKLOG 242：暗档 0.06/0.18 未动、亮档 0.14/0.26，'
              u'两档 lift 同 0.12 —— 同一个 opacity 在两个底上给的绝对差值差一个量级）')
ADD_EVIDENCE = (u'｜Tests/ClipboardHistoryAppTests/UICaptureHarness.swift 的 '
                u'`testSkeletonBarsAreVisibleAgainstTheirOwnBackground`'
                u'（两档各一条对比度下界 + 合成图已知答案对照，R220 / BACKLOG 245）')


def die(why):
    print('SURFACE_R220 refused: ' + why)
    sys.exit(1)


def load(path):
    return json.load(io.open(os.path.join(ROOT, path), encoding='utf-8'))


rows = load(LEDGER).get('rows')
if not isinstance(rows, list):
    die('rows 不是列表 ⇒ 这本账的形状与我读到的不同，停手')
hits = [r for r in rows if r.get('surface') == u'主窗口/详情区' and r.get('state') == u'加载']
if len(hits) != 1:
    die('「主窗口/详情区 × 加载」那一格命中 %d 颗（要 1）⇒ 对象不明' % len(hits))
cell = hits[0]
if cell.get('verdict') != 'added':
    die('那一格的 verdict 是 ' + str(cell.get('verdict')) + u'，本轮的前提（补理由而不是翻判法）不成立')
if ADD_REASON in cell.get('reason', ''):
    print('SURFACE_R220 already-synced ⇒ 不动盘')
    sys.exit(0)

gen_path = os.path.join(ROOT, GEN)
used_generator = False
if os.path.exists(gen_path):
    gen = io.open(gen_path, encoding='utf-8').read()
    if ANCHOR in gen and gen.count(ANCHOR) == 1:
        # reason 文本在生成器里以一行 `reason=...` 出现，结尾就是那句「8s 上界」之后
        line = [l for l in gen.splitlines() if ANCHOR in l][0]
        tail = u'8s 上界'
        if tail not in line:
            die('生成器那一行里找不到结尾锚 ' + tail)
        patched_line = line.replace(tail, tail + ADD_REASON, 1)
        if patched_line == line:
            die('生成器补丁没生效')
        io.open(gen_path, 'w', encoding='utf-8').write(gen.replace(line, patched_line, 1))
        proc = subprocess.run([sys.executable, GEN], cwd=ROOT,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1'))
        out = proc.stdout.decode('utf-8', 'replace')
        if proc.returncode != 0:
            die('重跑生成器失败（exit=%d）：\n%s' % (proc.returncode, out[-800:]))
        used_generator = True
        print('SURFACE_R220 generator-patched-and-ran')
    else:
        print('SURFACE_R220 generator-missing-anchor hits=%d ⇒ 直接改 JSON（并在结论里写明没走生成器）'
              % gen.count(ANCHOR))

if not used_generator:
    data = json.load(io.open(os.path.join(ROOT, LEDGER), encoding='utf-8'))
    target = [r for r in data['rows']
              if r.get('surface') == u'主窗口/详情区' and r.get('state') == u'加载'][0]
    if ADD_REASON not in target['reason']:
        target['reason'] = target['reason'] + ADD_REASON
    if ADD_EVIDENCE.strip(u'｜') not in target.get('evidence', ''):
        target['evidence'] = target.get('evidence', '') + ADD_EVIDENCE
    io.open(os.path.join(ROOT, LEDGER), 'w', encoding='utf-8').write(
        json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('SURFACE_R220 json-patched-directly')

after = load(LEDGER)
rows_after = after.get('rows')
if len(rows_after) != len(rows):
    die('行数变了：%d → %d ⇒ 这本账被写坏' % (len(rows), len(rows_after)))
cell_after = [r for r in rows_after
              if r.get('surface') == u'主窗口/详情区' and r.get('state') == u'加载']
if len(cell_after) != 1:
    die('改完找不到那一格了')
if cell_after[0].get('verdict') != 'added':
    die('verdict 被改动')
if ADD_REASON not in cell_after[0]['reason']:
    die('reason 没补上')
print('SURFACE_R220 rows=%d verdict=%s generator=%s'
      % (len(rows_after), cell_after[0]['verdict'], 'yes' if used_generator else 'no'))
sys.exit(0)
