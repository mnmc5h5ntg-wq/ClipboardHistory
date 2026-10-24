#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""把 STATE 正文里那根危险的 `\\b` 修成**源码里写两根、求值后留一根**。

为什么要单独一支脚本：Edit 把 `(?:\\A|\\s)` 与 `\\balt` 原样写进了 python 源文件，
而台账正文用的是三引号普通串（不是 raw 串）：
- `\\b` 会被求值成退格符 0x08 —— 那是"看起来对、盘上是控制字符"的那一类；
- `\\A` / `\\s` 不是合法转义，python 原样保留，所以**不用**动（动反而多一根反斜杠）。
脚本按"求值后的字面量里不许有退格"来判，而不是按行数或肉眼。
"""
import ast
import io
import sys

P = u"/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/ledgers_r336.py"

src = io.open(P, encoding=u"utf-8").read()
# 只补那两处真正会变成控制字符的（先长后短，避免子串自吃）
fixes = [(u"`\\b`", u"`\\\\b`"), (u"\\balt", u"\\\\balt")]
out = src
for old, new in fixes:
    if old in out:
        out = out.replace(old, new)

tree = ast.parse(out)
bad = []
for node in ast.walk(tree):
    if isinstance(node, ast.Str):
        if u"\x08" in node.s or u"\x00" in node.s:
            bad.append(node.lineno)
print(u"ALT_ESCAPE changed=%d fixes=%d" % (out != src, len(fixes)))
print(u"CONTROL_CHARS_IN_LITERALS=%d %s" % (len(bad), bad))
if bad:
    sys.exit(1)
io.open(P, u"w", encoding=u"utf-8").write(out)
for i, l in enumerate(out.splitlines(), 1):
    if u"altAttr" in l or u"HTML_ALT_SOURCE" in l:
        print(u"%d %s" % (i, l))
