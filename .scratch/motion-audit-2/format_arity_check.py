#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""台账生成器的**格式串 arity 预检**：占位符个数与参数个数不等，就在跑电池之前当场报。

为什么要有它（R334 现读，两次各浪费一整步）：`ledgers_r334.py` 里七个 `%`-格式串共 100 多个占位符，
而参数**按位置**配对。两种坏法都真发生过：
① `TypeError: not enough arguments for format string`（漏一个参数）；
② `%d format: a number is required, not str`（形状对但类型错 —— 我把 `s(ROUND - 1)` 传给了 `%d`）。
两种都在**执行到那一行**时才炸，而生成器是"边算边写"的：算到第 500 行才炸 = 前面白跑三遍电池
（R334 撞的就是这个：电池 50 秒 × 2 遍 + 帧日志解析，两次）。
`ast.parse` 拦不住这两类（语法完全合法）。

用法：`python3 .scratch/motion-audit-2/format_arity_check.py <生成器.py> [...]`
退出码：0=每个格式串的占位符都对得上；1=有至少一处不等（打印文件:行号 + 串的前 60 字）。
只判 `字面量 % (...)` 这一种形状；`%(name)s` 那种带键的走 dict，条数对不上是常态，**不判**。
"""
import ast
import io
import re
import sys

PLACEHOLDER = re.compile(r"%\((?P<key>\w+)\)?[sdrif]|%(?P<plain>[sdrif])")


def check(path):
    """返回 [(行号, 说明)]；空表 = 这个文件里每个字面量格式串的 arity 都对得上。"""
    src = io.open(path, encoding=u"utf-8").read()
    bad = []
    for node in ast.walk(ast.parse(src)):
        if not (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)
                and isinstance(node.left, ast.Str)):
            continue
        text = node.left.s
        ph = PLACEHOLDER.findall(text)
        if any(k for k, _ in ph):        # %(name)s 形状：参数是一个 dict，条数不对是常态
            continue
        kinds = [c for _, c in ph]
        right = node.right
        if isinstance(right, ast.Tuple):
            args = right.elts
        else:
            args = [right]
        if len(kinds) != len(args):
            bad.append((node.lineno, u"占位符 %d 个（%s）vs 参数 %d 个：%s"
                        % (len(kinds), u"".join(kinds), len(args), text[:60])))
            continue
        # 类型对不上也在这一格判：%d 收到字符串字面量 = R334 那一朵 `a number is required, not str`
        for kind, arg in zip(kinds, args):
            if kind == u"d" and isinstance(arg, ast.Str):
                bad.append((node.lineno, u"%%d 收到字符串字面量 %r" % (arg.s[:30],)))
    return bad


def self_check():
    u"""正对照：三颗人造的坏格式串必须全部被抓到，一颗好的不许被抓。

    没有这一格的尺就是"只测正则、不测流水线"（memory: 三种假绿的尺病）——
    它会对着真文件报 0 处，而那个 0 什么也不说明。
    """
    import tempfile
    src = (u"a = u'%s %s' % (1, 2)\n"                      # 好
           u"b = u'%s %s %d' % (1, 2)\n"                    # 少一个参数
           u"c = u'--for %d' % ('333',)\n"                  # %d 收到字符串
           u"d = u'%(x)s' % {'x': 1}\n"                     # 带键，不判
           u"e = u'100%% 是真的 %s' % (u'ok',)\n")          # 转义的 %% 不许算成占位符
    h = tempfile.NamedTemporaryFile(u"w", suffix=u".py", delete=False, encoding=u"utf-8")
    h.write(src)
    h.close()
    try:
        got = check(h.name)
    finally:
        import os
        os.unlink(h.name)
    lines = sorted(n for n, _ in got)
    assert lines == [2, 3], u"正对照没抓到该抓的两处（实得 %s）⇒ 这把尺量不出 arity" % (lines,)
    print(u"ARITY_SELFCHECK 正对照=2/2 抓到 假警报=0")


if __name__ == u"__main__":
    self_check()
    files = sys.argv[1:]
    if not files:
        sys.stdout.write(u"用法：format_arity_check.py <生成器.py> [...]\n")
        sys.exit(2)
    total = 0
    for f in files:
        for lineno, msg in check(f):
            sys.stdout.buffer.write((u"ARITY_BAD %s:%d %s\n" % (f, lineno, msg)).encode(u"utf-8"))
            total += 1
    sys.stdout.write(u"ARITY_CHECK files=%d bad=%d\n" % (len(files), total))
    sys.exit(1 if total else 0)
