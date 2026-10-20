#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数一数变异表里"这一卷跑起来了没"是用什么判的 —— 写死颗数的报出来，按形状判的不报。

起因（R262 现读）：`mutate_r229.py` 旧版用 `'Executed 4 tests' in text` 判"跑了没"，而
`ControlHoverLadderTests` 在 R260 长到 6 条 —— 数字一变，**真红了的那一遍会被读成"根本没跑起来"**。
同一颗写法在另外几支表里也有（本尺就是去数它们）。这一族的成因和 D-243 是一侧的：
编译红不是 CAUGHT，而"结论行读不到"也不是 ESCAPED —— 两种都把判据的机会算成别的东西。

规矩：**判"跑起来了没"要看结论行的形状（`Executed (\\d+) tests?, with (\\d+) failures?`），
不许把某一轮量到的颗数写进代码。** 唯一的例外是 `Executed 0 tests` —— 那个 0 不是本轮读数，
而是"filter 一条都没匹配上"这个状态本身，写死它是对的。

只用 `ast` 里的字符串常量，所以注释和 docstring 里引用这句话（比如本文件开头那段）
**不会**被算成命中 —— 守卫读字段不读散文（R74 那一族）。

只测不判：退出码恒 0，命名与"不许再加新的"由 `scripts/tests/test_mutation_verdict_scan.py`
里的名册负责。
"""
import argparse
import ast
import io
import os
import re
import sys

LITERAL = re.compile(r'Executed (\d+) tests?\b')
# 形状判据长这样：`re.search(r'Executed (\d+) tests?…', text)` —— 源码里出现的是 `\d+`，不是数字。
SHAPE = re.compile(r'Executed \(\\d\+\)')


def string_constants(tree):
    """返回文件里所有**代码中**的字符串常量（跳过模块/类/函数 docstring）。"""
    doc_nodes = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, 'body', None)
            if body and isinstance(body[0], ast.Expr):
                val = body[0].value
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    doc_nodes.add(id(val))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in doc_nodes:
            out.append(node.value)
    return out


def scan_file(path):
    with io.open(path, encoding='utf-8', errors='replace') as handle:
        src = handle.read()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {'file': os.path.basename(path), 'parse_error': str(exc),
                'literal': [], 'shape': False}
    literal, shape = [], False
    for const in string_constants(tree):
        for m in LITERAL.finditer(const):
            if m.group(1) != '0':
                literal.append(m.group(0))
        if SHAPE.search(const):
            shape = True
    return {'file': os.path.basename(path), 'parse_error': None,
            'literal': sorted(set(literal)), 'shape': shape}


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)          # scripts/ 的上一级就是仓库根 —— 由自己所在位置推，不写死


def main():
    ap = argparse.ArgumentParser(description='变异表"跑了没"的判据形状扫描（只测不判）')
    ap.add_argument('--dir', default=None,
                    help='变异表所在目录（默认 <仓库>/.scratch/motion-audit-2）')
    ap.add_argument('--root', default=REPO, help='仓库根目录（默认由脚本自身位置推出）')
    args = ap.parse_args()

    directory = args.dir or os.path.join(args.root, '.scratch', 'motion-audit-2')
    if not os.path.isdir(directory):
        print('MUT_VERDICT_DIR_MISSING=1 %s 不存在 ⇒ 不许在空目录上给绿' % directory)
        return 1
    paths = [os.path.join(directory, n) for n in os.listdir(directory)
             if n.startswith('mutate_') and n.endswith('.py')]
    rows = [scan_file(p) for p in sorted(paths)]
    broken = [r['file'] for r in rows if r['parse_error']]
    offenders = [r for r in rows if r['literal']]
    for r in rows:
        if r['parse_error']:
            print('MUT_VERDICT file=%s 解析失败=%s ⇒ 这一支没被量到，不算通过' % (r['file'], r['parse_error']))
            continue
        print('MUT_VERDICT file=%s 写死=%s 形状判据=%d'
              % (r['file'], '、'.join(r['literal']) if r['literal'] else '无', 1 if r['shape'] else 0))
    print('MUT_VERDICT_SUMMARY tables=%d offenders=%d named=%s parse_bad=%d'
          % (len(rows), len(offenders),
             ','.join(r['file'] for r in offenders) or '无', len(broken)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
