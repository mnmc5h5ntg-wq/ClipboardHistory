#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R95 变异对照：那份栈的三格新逻辑（`_dominant_path`、族的选择、占比阈值、缺 `Call graph:` 那一格）。

跑法与 R94 那支一样：变异发生在**临时树**里（`scripts/` 的副本 + 软链的 `.github/workflows`
与 Swift 源文件），仓库里那颗尺子全程不被改写。

五刀（M523..M527，编号先查重：R94 用到 M522）：
  M523 每层取"第一个孩子"而不是"采样数最大的孩子" ⇒ 散开的栈会被读成挂
  M524 占比阈值 0.9 → 0.0 ⇒ 任何一份栈都判"挂"（132 要分的就是这两种，阈值失效等于没分）
  M525 族的选择退回"路径与叶子一起查" ⇒ `-[NSMenu popUp…]` 被读成 cordrag（R95 真错过的地方）
  M526 去掉"没有 `Call graph:`"那一格 ⇒ 坏文件会被继续解析（读起来像结论）
  M527 **预期 ESCAPED**：并列时（两个孩子同为最大）取最后一个而不是第一个 ——
      现有任何夹具都没有并列，所以这一刀会绿。真实缺口开成 BACKLOG 137：
      占比那一格不受影响，但**被点名的那个最深帧**在并列时是任意的 ⇒
      `blocked@X` 里的 X 可能只是并列者之一。
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = '/Users/wangziyi/Codex_Project0'
TARGET_REL = 'scripts/ui_probe_report.py'
SWIFT_REL = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift'
MODULES = ['scripts.tests.test_ui_probe_report']

PICK_FIRST = "        best_i, best = max(level, key=lambda kv: kv[1][1])"
PICK_LAST = "        best_i, best = level[-1]"
THRESHOLD = 'share >= 0.9'
THRESHOLD_OFF = 'share >= 0.0'
FAM_TAIL = """    family = fam(leaf)
    if family == "unknown":
        family = fam(frames)"""
FAM_HEAD = """    family = fam(frames)
    if family == "unknown":
        family = fam(leaf)"""
GUARD = '    if not text or "Call graph:" not in text:'
GUARD_OFF = '    if not text:'


def sub_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit('%s 的锚点命中 %d 次（只许 1 次）⇒ 拒绝造变异' % (tag, n))
    return text.replace(old, new)


def build_tree():
    root = tempfile.mkdtemp(prefix='r95_mutate-')
    shutil.copytree(os.path.join(REPO, 'scripts'), os.path.join(root, 'scripts'))
    os.makedirs(os.path.join(root, 'ClipboardHistory/Tests/ClipboardHistoryAppTests'))
    os.symlink(os.path.join(REPO, SWIFT_REL), os.path.join(root, SWIFT_REL))
    os.makedirs(os.path.join(root, '.github'), exist_ok=True)
    os.symlink(os.path.join(REPO, '.github/workflows'), os.path.join(root, '.github/workflows'))
    return root


def target(root):
    return os.path.join(root, TARGET_REL)


def reset(root):
    shutil.copy(os.path.join(REPO, TARGET_REL), target(root))


def run(root):
    proc = subprocess.run([sys.executable, '-m', 'unittest'] + MODULES, cwd=root,
                          env=dict(os.environ, PYTHONUTF8='1'),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode('utf-8', 'replace')
    if proc.returncode == 0:
        return 'GREEN', out
    if 'FAILED (' in out:
        return 'RED', out
    return 'ERROR', out


MUTATIONS = [
    ("M523", "每层取第一个孩子而不是最多样本的孩子", PICK_FIRST, PICK_LAST, 'RED'),
    ("M524", "占比阈值失效（任何栈都判挂）", THRESHOLD, THRESHOLD_OFF, 'RED'),
    ("M525", "族先看路径再看叶子（R95 真错过的方向）", FAM_TAIL, FAM_HEAD, 'RED'),
    ("M526", "去掉缺 Call graph 那一格", GUARD, GUARD_OFF, 'RED'),
    ("M527", "并列时取最后一个孩子（没有夹具覆盖，预期绿）",
     "        best_i, best = max(level, key=lambda kv: kv[1][1])",
     "        best_i, best = max(level, key=lambda kv: (kv[1][1], kv[0]))", 'GREEN'),
]


def main():
    root = build_tree()
    reset(root)
    baseline, out = run(root)
    print('基线（临时树，%s）：%s' % ('、'.join(MODULES), baseline))
    if baseline != 'GREEN':
        print(out[-1500:])
        raise SystemExit('临时树本身跑不绿 ⇒ 这一轮的变异表不作数')
    rows = []
    for tag, desc, old, new, want in MUTATIONS:
        reset(root)
        with open(target(root), encoding='utf-8') as handle:
            text = handle.read()
        with open(target(root), 'w', encoding='utf-8') as handle:
            handle.write(sub_once(text, old, new, tag))
        got, out = run(root)
        rows.append((tag, desc, got, want))
        print('%s %-46s %s（期望 %s）' % (tag, desc, got, want))
        if got == 'RED':
            names = [l[6:].split(' (')[0] for l in out.splitlines() if l.startswith('FAIL:')]
            print('    红在：%s' % '; '.join(names[:4]))
    reset(root)
    after, out = run(root)
    print('恢复后基线复跑：%s' % after)
    wrong = [r for r in rows if r[2] != r[3]]
    print('MUTATE_TABLE n=%d caught=%d intended_escaped=%d mismatch=%d not_run=%d' % (
        len(rows), sum(1 for r in rows if r[2] == 'RED'),
        sum(1 for r in rows if r[2] == 'GREEN'), len(wrong),
        sum(1 for r in rows if r[2] == 'ERROR')))
    for tag, desc, got, want in wrong:
        print('  MISMATCH %s %s got=%s want=%s' % (tag, desc, got, want))
    shutil.rmtree(root, ignore_errors=True)
    return 1 if (wrong or after != 'GREEN') else 0


if __name__ == '__main__':
    sys.exit(main())
