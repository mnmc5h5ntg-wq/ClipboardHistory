#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产品日程常量 vs 判据里抄的值（R270 / BACKLOG 320）。只读，不改。

问一句：**这条判据的窗口长度，是读产品那个常量，还是把常量的值抄在自己身上？**
抄值会腐烂（R94 那条规矩：注释里的"实测"要么升成判据要么删掉，同一个道理）。

判的形状：
  产品  `static let visibilityGrace: TimeInterval = <值>`        ← 唯一真相
  判据  `pumpWindow(..., milliseconds: Int(k * (debounce + DailyCopyLedger.visibilityGrace) * 1000))`
        ⇒ 表达式里必须**出现**那个常量名；
        ⇒ 判据文件里（剥掉行注释之后）不许再出现等于该值的裸字面量。

两条都会红，且方向相反：把窗口换回裸数字 ⇒ 红；产品里那个常量被删掉/改名 ⇒ 红（读不到真相）。
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PRODUCT = os.path.join(REPO, 'ClipboardHistory', 'Sources', 'ClipboardHistoryApp',
                       'Managers', 'DailyCopyLedger.swift')
TEST = os.path.join(REPO, 'ClipboardHistory', 'Tests', 'ClipboardHistoryAppTests',
                    'DailyCopyHeatmapTests.swift')
CONSTANT = 'visibilityGrace'

sys.path.insert(0, HERE)
from wait_scan import strip_comment  # noqa: E402  同一把剥注释的尺（D-247）

DECL = re.compile(r'(?:static\s+let|let)\s+' + CONSTANT + r'\s*:\s*TimeInterval\s*=\s*([0-9.]+)')
WINDOW = re.compile(r'pumpWindow\(\s*cell:\s*"([\w-]+)"\s*,?\s*milliseconds:\s*(.{0,120})')


def code_lines(text):
    return '\n'.join(strip_comment(l) for l in text.splitlines())


def scan(product_text, test_text):
    """返回 (grace 值或 None, [(窗口表达式, 是否读常量)], 抄值处数)。"""
    m = DECL.search(code_lines(product_text))
    grace = m.group(1) if m else None
    body = code_lines(test_text)
    windows = []
    for w in WINDOW.finditer(body):
        expr = w.group(2)
        reads = (CONSTANT in expr)
        windows.append((w.group(1), expr.strip(), reads))
    copied = 0
    if grace is not None:
        for line in body.splitlines():
            if WINDOW.search(line) or CONSTANT in line:
                continue
            if re.search(r'(?<![\w.])' + re.escape(grace) + r'(?![\d])', line):
                copied += 1
    return grace, windows, copied


def judge(grace, windows, copied):
    bad = []
    if grace is None:
        bad.append('产品里读不到 ' + CONSTANT + ' 的声明 ⇒ 窗口长度没有真相可读')
    for cell, expr, reads in windows:
        if not reads:
            bad.append('窗口 ' + cell + ' 没读常量，表达式=' + expr[:60])
    if copied:
        bad.append('判据里有 ' + str(copied) + ' 处裸字面量等于产品常量值 ⇒ 抄值')
    return bad


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--product', default=PRODUCT)
    parser.add_argument('--test', default=TEST)
    args = parser.parse_args(argv)

    for path in (args.product, args.test):
        if not os.path.isfile(path):
            print('TIMING_SCAN product_grace=无 windows=0 读常量=0 抄值=0 判=FAIL 文件不存在=' + path,
                  flush=True)
            return 1

    with io.open(args.product, encoding='utf-8') as h:
        product_text = h.read()
    with io.open(args.test, encoding='utf-8') as h:
        test_text = h.read()

    grace, windows, copied = scan(product_text, test_text)
    bad = judge(grace, windows, copied)
    reads = sum(1 for _, _, r in windows if r)
    verdict = 'PASS' if not bad else 'FAIL'
    print('TIMING_SCAN product_grace=' + str(grace if grace else '无')
          + ' windows=' + str(len(windows)) + ' 读常量=' + str(reads)
          + ' 抄值=' + str(copied) + ' 判=' + verdict, flush=True)
    for b in bad:
        print('TIMING_SCAN_BAD ' + b, flush=True)
    return 0 if verdict == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
