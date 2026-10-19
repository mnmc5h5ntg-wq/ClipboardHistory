#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R217 的变异表：两臂行为证人（BACKLOG 240）的两条断言各配一把刀。

背景：R214 的注释里写着"补第三把刀之前要先补行为证人（同一视图两臂的像素判据）"。
R217 真补了这个证人，**实验结果是否定的**：本机亮/暗两臂都是 `冻结臂条带行=50 不冻臂条带行=50`
⇒ `freezeLoadingForCapture` 在离屏捕帧通道里没有像素后果（`.task` 那一跳不会在渲染期内落地）。
所以"传死值"那一刀在这个通道里**永远抓不到**，它不进本表（不进表 ≠ 跑过），
240 因此留开、并把"要能被像素抓，先得让通道分得出两臂"记成它的先决条件。

本表两把：

M750 把尺的**第一个子句**翻成恒假（`strong < 8` ⇒ `strong < 0`）⇒ 一行条带都数不出来
     ⇒ `frozenRows > 20` 必须红。这一刀证明证人不是空转：骨架真的是它量的对象。
M751 把**不冻臂**的外框高度从 520 改成 300（夹具侧的正对照）⇒ 两臂读数分叉
     ⇒ 那条 `XCTAssertEqual(liveRows, frozenRows)` 必须红。这一刀证明等号那条不是恒真式
     —— R100 的规矩：只印不拦的读数等于没有读数，新闸门要能在同一样本上被抓红。

两把刀都必须只改一处（needle 整行字面、命中恰好一次），跑完逐字节还原并复核。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
HARNESS = 'ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift'
FILT = 'UICaptureTests'
TEST = 'testFrozenAndLiveArmsReadTheSameSkeletonRows'

ARMS = [
    ('M750', u'尺的第一个子句恒假 ⇒ 数不出条带（证人失去对象）', HARNESS,
     '            if strong < 8 && weak > width / 8 { barRows.append(y) }',
     '            if strong < 0 && weak > width / 8 { barRows.append(y) }',
     TEST),
    ('M751', u'不冻臂外框高度改成 300 ⇒ 两臂读数分叉（等号那条正对照）', HARNESS,
     '                    DetailView(historyStore: liveStore, freezeLoadingForCapture: false)\n'
     '                        .frame(width: 720, height: 520)',
     '                    DetailView(historyStore: liveStore, freezeLoadingForCapture: false)\n'
     '                        .frame(width: 720, height: 300)',
     TEST),
]


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def run(test_name):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    proc = subprocess.run(['env', '-u', 'SDKROOT', 'swift', 'test', '--filter',
                           '%s/%s' % (FILT, test_name)],
                          cwd=os.path.join(ROOT, 'ClipboardHistory'), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    m = re.search(r'Executed (\d+) tests?', text)
    fm = re.search(r'with (\d+) failure', text)
    failed = bool(fm) and int(fm.group(1)) > 0
    return proc.returncode, (int(m.group(1)) if m else 0), failed, text


def main():
    caught = escaped = not_run = 0
    for arm_id, why, target, needle, repl, filt in ARMS:
        original = read(target)
        hits = original.count(needle)
        if hits != 1:
            not_run += 1
            print('%s NOT_RUN needle 命中 %d 次（要 1）' % (arm_id, hits), flush=True)
            continue
        restored = False
        try:
            write(target, original.replace(needle, repl, 1))
            code, n_ran, failed, text = run(filt)
        finally:
            write(target, original)
            restored = read(target) == original
        if not restored:
            print('%s RESTORE_FAILED ⇒ 立刻停表' % arm_id, flush=True)
            return 2
        if n_ran == 0:
            not_run += 1
            print('%s NOT_RUN 那一格根本没跑（Executed 0）⇒ 不算 CAUGHT：%s' % (arm_id, why), flush=True)
            continue
        proof = re.search(r'SKELETON_BEHAVIOR_PROOF[^\n]*', text)
        reading = (proof.group(0) if proof else u'没有读数行')
        if code != 0 and failed:
            caught += 1
            print('%s CAUGHT  %s.%s ｜ %s ｜ %s' % (arm_id, FILT, filt, why, reading), flush=True)
        else:
            escaped += 1
            print('%s ESCAPED %s.%s ｜ %s ｜ %s' % (arm_id, FILT, filt, why, reading), flush=True)
    print('R217_MUTATE 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d RESTORE_CLEAN=yes'
          % (len(ARMS), caught, escaped, not_run), flush=True)
    return 0 if (escaped == 0 and not_run == 0 and caught == len(ARMS)) else 1


if __name__ == '__main__':
    sys.exit(main())
