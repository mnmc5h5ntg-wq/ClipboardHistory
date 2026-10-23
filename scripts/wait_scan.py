#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""固定挂钟等待的**形状**清点（R268 / BACKLOG 318 / 接 D-253）。只读，不改任何东西。

问的是一句话：一处等待是**赌一段挂钟**，还是**等产物出现**？

命名就是判据 —— 读散文的守卫不算守卫（D-235 那一族），所以这两种形状在 Swift 里是两个不同的符号：

  pumpMain(seconds:)              赌注。R267 在 runner 现读里被证明会翻脸（同一版本代码
                                  run 39557244740 红、run 39559154078 绿），R268 把仓库里的
                                  调用点清零；再出现一处就是这一把尺要红的东西。
  pumpRunLoopStep(seconds:)       轮询体里的一步（调用点都在 `while 条件, Date() < 截止` 内）。
  pollUntil(cell:…)               等产物 + 把 waited_ms 打成读数 + `hit` 直接进断言。
  Thread.sleep(<字面量>)          观察窗口。**只有断言「没出现」的那种留得住**（缺席没法轮询），
                                  而且必须点名在册，并由同一条测试里的正面证人撑着。
  Thread.sleep(<具名常量>)        轮询步进（`ArchiveReloadWait.pollInterval`），不算赌注。
  pumpWindow(cell:…)              事件**之后**的固定观察窗口（起点是产物出现，不是动作发出）⇒ 不算赌注。

名册是双向的：新写一处没登记的固定等待 ⇒ 红；名册里那格已经没了 ⇒ 也红（R227 同族）。

范围 = `ClipboardHistory/Tests/`（产品源码里的等待形状不在这把尺的问题里 ⇒ BACKLOG 319）。
字符串里的 `//`（例如 URL）不会被当成注释：剥注释时认引号内外的区别，`\"` 也算转义。
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_ROOT = os.path.join(REPO, 'ClipboardHistory', 'Tests')

# 赌一段挂钟的两种写法
BET_PATTERNS = (
    ('wall_clock_bet', re.compile(r'(?<!func )\bpumpMain\(seconds:')),
    ('literal_sleep', re.compile(r'(?<!func )Thread\.sleep\(forTimeInterval:\s*[0-9]')),
)
POLL_STEP = re.compile(r'(?<!func )\bpumpRunLoopStep\(seconds:')
POLL_UNTIL = re.compile(r'(?<!func )\bpollUntil\(cell:')

# 只在这里出现的合法观察窗口：断言的是「文件没出现」，正面证人是同一条测试末尾的那次 flush。
OBSERVATION_WINDOWS = [
    ('DailyCopyHeatmapTests.swift', 'testBackfillDoesNotWriteDuringConstruction',
     '断言缺席 ⇒ 不可轮询；同格末尾 flushPendingSaves + 文件出现当正面控制'),
    # R319 / BACKLOG 374：这一格的"等待"是**主动把秒界跨过去** —— 条件是被观察的秒变化
    # （`while Date().timeIntervalSince(crossed) < 1.05`），里面的 `Thread.sleep(0.05)` 只是让出 CPU。
    # 它被扫出来是因为扫描认字面式（这条尺不该去猜"这个 sleep 是不是有意的"），
    # 登记的理由就是这一格与"撞运气的固定等待"的区别：**去掉这个等待，断言仍然成立；
    # 但它回来了 ⇒ 374 那朵"跟着挂钟走"的红会回来**，所以它是证据不是运气。
    ('HistoryPersistenceRecoveryTests.swift',
     'testCorruptHistoryWithoutBackupPreservesOriginalAndReferencedImages',
     '等条件是秒界（374：断言不许依赖挂钟粒度）；sleep 只让出 CPU，不决定结果'),
]

FUNC_DEF = re.compile(r'^\s*(?:@[\w.]+\s+)*(?:private |fileprivate |public |open |static |final )*func\s+(\w+)')


def strip_comment(line):
    """剥掉行尾 `//` 注释，但**字符串里**的 `//`（URL）不算注释。"""
    out = []
    in_string = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_string and c == '\\':
            out.append(c)
            if i + 1 < len(line):
                out.append(line[i + 1])
            i += 2
            continue
        if c == '"':
            in_string = not in_string
        elif not in_string and line[i:i + 2] == '//':
            break
        out.append(c)
        i += 1
    return ''.join(out)


def findings(text):
    """返回 (bets, poll_steps, poll_untils)。

    bets 是 [(函数名, 种类, 行号)]；声明行不算调用点 —— 把 helper 起成两个名字之后，
    数错声明就会多出一颗"赌注"，那把尺会红在它自己的定义上。
    """
    bets = []
    steps = 0
    untils = 0
    current = '<file>'
    for number, raw in enumerate(text.split('\n'), 1):
        code = strip_comment(raw)
        if not code.strip():
            continue
        matched = FUNC_DEF.match(code)
        if matched:
            current = matched.group(1)
        # 声明行不算调用点，但**不许整行跳过**：`func testX() { Thread.sleep(0.6) }` 这种
        # 一行体里既有声明又有调用 —— 上一版就是跳整行，被正对照当场抓出来（尺红在自己的规则上）。
        steps += len(POLL_STEP.findall(code))
        untils += len(POLL_UNTIL.findall(code))
        for kind, pattern in BET_PATTERNS:
            for _ in pattern.findall(code):
                bets.append((current, kind, number))
    return bets, steps, untils


def swift_files(root):
    paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.build', 'DerivedData')]
        for name in filenames:
            if name.endswith('.swift'):
                paths.append(os.path.join(dirpath, name))
    return sorted(paths)


def scan(root=DEFAULT_ROOT):
    bets = []
    steps = 0
    untils = 0
    for path in swift_files(root):
        with io.open(path, encoding='utf-8') as handle:
            file_bets, file_steps, file_untils = findings(handle.read())
        base = os.path.basename(path)
        bets.extend([(base, function, kind, line) for function, kind, line in file_bets])
        steps += file_steps
        untils += file_untils
    return bets, steps, untils


def judge(bets, windows=None, present=None):
    """名册双向对账：没登记的赌注 + 已经不存在的名册格。

    `present` 是**这次扫描真正走到的文件名集合**。少了这个参数，把尺指向 `Sources/` 会因为
    名册里那格住在 `Tests/` 而报"名册失配"—— 那是尺的作用域坏了，不是账坏了
    （R269 第一次把 `--root ClipboardHistory/Sources` 指上去就撞上，现读 名册失配=1）。
    """
    windows = OBSERVATION_WINDOWS if windows is None else windows
    keyed = set((b[0], b[1]) for b in bets)
    allowed = set((w[0], w[1]) for w in windows)
    unregistered = [b for b in bets if (b[0], b[1]) not in allowed]
    in_scope = [w for w in windows if present is None or w[0] in present]
    stale = [w for w in in_scope if (w[0], w[1]) not in keyed]
    return unregistered, stale


LINE_SHAPE = re.compile(r'^WAIT_SCAN bet=\d+ 未登记=\d+ 名册失配=\d+ poll_step=\d+ poll_until=\d+'
                        r' 判=PASS$|^WAIT_SCAN bet=\d+ 未登记=\d+ 名册失配=\d+ poll_step=\d+ poll_until=\d+'
                        r' 判=FAIL')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--root', default=DEFAULT_ROOT,
                        help='要扫的目录（默认 = 本仓库 ClipboardHistory/Tests，由 __file__ 推）')
    args = parser.parse_args(argv)

    if not os.path.isdir(args.root):
        print('WAIT_SCAN bet=0 未登记=0 名册失配=0 poll_step=0 poll_until=0 判=FAIL '
              '根目录不存在=' + args.root, flush=True)
        return 1

    bets, steps, untils = scan(args.root)
    unregistered, stale = judge(bets, present=set(os.path.basename(x) for x in swift_files(args.root)))
    verdict = 'PASS' if not unregistered and not stale else 'FAIL'
    print('WAIT_SCAN bet=%d 未登记=%d 名册失配=%d poll_step=%d poll_until=%d 判=%s'
          % (len(bets), len(unregistered), len(stale), steps, untils, verdict), flush=True)
    for base, function, kind, line in unregistered:
        print('WAIT_SCAN_UNREG %s#%s (%s) L%d ⇒ 等产物用 pollUntil，断言缺席才留观察窗口'
              % (base, function, kind, line), flush=True)
    for base, function, why in stale:
        print('WAIT_SCAN_STALE %s#%s ⇒ 名册里那格已经不在了（原因登记：%s）'
              % (base, function, why), flush=True)
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
