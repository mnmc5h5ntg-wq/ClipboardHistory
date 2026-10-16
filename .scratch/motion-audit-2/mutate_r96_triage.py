#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分诊那把尺的变异表（R95 开，R96 重做）。

跑法与 R94 那支一样：变异发生在**临时树**里（`scripts/` 的副本 + 软链的 `.github/workflows`
与 Swift 源文件），仓库里那颗尺子全程不被改写。

R96 重做的理由（不是"顺手扩表"）：R95 那五刀里 **M525 的锚点随代码一起没了**，
而 M527 那一格（"并列时取哪个孩子"）的修法也不是补夹具 —— 判定不再从"挑一条最深路径"读数，
改成从"有多少采样停在等待帧上"读数（`_waiting_leaves`）。所以：
  · M525 退役（锚点已不存在；留着只会以 `needle 命中 0 次` 的形式假装在册）；
  · M527 由 **M534** 替代：并列那一支如果退化成"取 fams[0]"，tie 夹具当场红；
  · 新增 M533（嵌套等待帧被重复计数）与 M535（占比分母被换掉）——
    这两刀抓的是新尺**独有**的两种坏法，旧尺上没有对应的代码可切；
  · M523 留着并且**仍然有牙**（它红在 `test_dominant_path_truth_table`）：
    主导路径那一格虽然不再决定 verdict，但它是要被打印、被人读的数，
    "不再承重"与"不再被验"是两件事。
退役与替代都写在这里，是因为"表里少了一格"和"表里那一格永远绿"是同一种失忆。

七刀（M523、M524、M526、M533..M536）：
  M523 每层取最后一个孩子而不是采样数最大的孩子 ⇒ 主导路径占比读错
  M524 等待占比阈值 0.9 → 0.0 ⇒ 任何一份栈都判"挂"（132 要分的就是这两种）
  M526 去掉"没有 `Call graph:`"那一格 ⇒ 坏文件会被继续解析（读起来像结论）
  M533 等待帧套等待帧时每层都计 ⇒ 611 被数成几千，占比失真
  M534 并列时只报第一个族 ⇒ 替栈做决定（BACKLOG 137 的正身）
  M535 占比分母从"主线程采样数"换成"树里所有节点之和" ⇒ 两格占比同时失真
  M536 去掉"主线程块里一个节点都没有"那一格 ⇒ 回到兜底 1.0，读不懂文件会被打印成 `blocked@unknown`（R95 的尺在 runner 上真的这样说过一句假话）
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = "/Users/wangziyi/Codex_Project0"
TARGET_REL = "scripts/ui_probe_report.py"
SWIFT_REL = "ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift"
MODULES = ["scripts.tests.test_ui_probe_report"]

PICK_LAST = "        best_i, best = level[-1]"
PICK_MAX = "        best_i, best = max(level, key=lambda kv: kv[1][1])"
THRESHOLD = "    if wait_share >= 0.9 and len(fams) == 1:"
THRESHOLD_OFF = "    if wait_share >= 0.0 and len(fams) == 1:"
NESTED = (
    '        if blocking_family(sym) != "unknown" and not inner:\n'
    '            return k, [(sym, count)]\n'
    '        return k, inner'
)
NESTED_OFF = (
    '        if blocking_family(sym) != "unknown":\n'
    '            inner.append((sym, count))\n'
    '        return k, inner'
)
TIE = '    elif wait_share >= 0.9:\n        verdict = "blocked@ambiguous"'
TIE_OFF = '    elif wait_share >= 0.9:\n        fams = fams[:1]\n        verdict = "blocked@ambiguous"'
DENOM = "    wait_share = (float(waited) / total) if total else 0.0"
DENOM_OFF = ("    wait_share = (float(waited) / sum(c for _, c, _ in nodes)) if nodes else 1.0")
UNPARSED = "    if not nodes:\n        # R96"
UNPARSED_OFF = "    if False:\n        # R96"
GUARD = '    if not text or "Call graph:" not in text:'
GUARD_OFF = '    if not text:'
GUARD_OFF = '    if not text:'

MUTATIONS = [
    ("M523", "每层取最后一个孩子而不是最多样本的孩子（主导路径那一格）", PICK_MAX, PICK_LAST, 'RED'),
    ("M524", "等待占比阈值失效（任何栈都判挂）", THRESHOLD, THRESHOLD_OFF, 'RED'),
    ("M526", "去掉缺 Call graph 那一格", GUARD, GUARD_OFF, 'RED'),
    ("M533", "嵌套等待帧每层都计（占比失真）", NESTED, NESTED_OFF, 'RED'),
    ("M534", "并列时只报第一个族（替栈做决定，137 的正身）", TIE, TIE_OFF, 'RED'),
    ("M535", "占比分母换成树里所有节点之和", DENOM, DENOM_OFF, 'RED'),
    ("M536", "去掉『主线程块里一个节点都没有』那一格（回到兜底 1.0）",
     UNPARSED, UNPARSED_OFF, 'RED'),
]


def sub_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit('%s 的锚点命中 %d 次（只许 1 次）⇒ 拒绝造变异' % (tag, n))
    return text.replace(old, new)


def build_tree():
    root = tempfile.mkdtemp(prefix='r96_mutate-')
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
        print('%s %-52s %s（期望 %s）' % (tag, desc, got, want))
        if got == 'RED':
            names = [l[6:].split(' (')[0] for l in out.splitlines() if l.startswith('FAIL:')]
            print('    红在：%s' % '; '.join(names[:4]))
    reset(root)
    after, out = run(root)
    print('恢复后基线复跑：%s' % after)
    wrong = [r for r in rows if r[2] != r[3]]
    print('MUTATE_TABLE n=%d caught=%d intended_escaped=%d mismatch=%d not_run=%d' % (
        len(rows), sum(1 for r in rows if r[2] == 'RED'),
        sum(1 for r in rows if r[2] == 'GREEN' and r[3] == 'GREEN'), len(wrong),
        sum(1 for r in rows if r[2] == 'ERROR')))
    for tag, desc, got, want in wrong:
        print('  MISMATCH %s %s got=%s want=%s' % (tag, desc, got, want))
    shutil.rmtree(root, ignore_errors=True)
    return 1 if (wrong or after != 'GREEN') else 0


if __name__ == '__main__':
    sys.exit(main())
