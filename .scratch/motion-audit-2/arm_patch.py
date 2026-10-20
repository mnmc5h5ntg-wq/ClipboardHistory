#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变异表的插刀/还原小工具（R245 / BACKLOG 283）：needle 从**文件**读，避免 shell 引号把 needle 改坏。

三个动作：
  patch   <目标文件> <needle 文件> <替换文件> <备份文件>   —— needle 必须命中恰好一次，否则 exit 3（不写）
  restore <目标文件> <备份文件>                            —— 逐字节写回
  verify  <目标文件> <备份文件>                            —— 只比对，exit 0=一致 / 4=不一致

为什么单独一份：R241 的 M796 就是被"needle 命中 3 次"救过一次（插错地方会造出一把假刀）。
"""
import io, sys


def read(p):
    return io.open(p, encoding='utf-8').read()


def main(argv):
    if len(argv) < 3:
        sys.stderr.write('用法：arm_patch.py patch|restore|verify …\n')
        return 2
    act = argv[1]
    if act == 'patch':
        path, oldf, newf, backup = argv[2:6]
        text = read(path)
        needle = read(oldf)
        repl = read(newf)
        hits = text.count(needle)
        if hits != 1:
            sys.stderr.write('needle 命中 %d 次（要恰好 1）：%s\n' % (hits, needle[:60]))
            return 3
        io.open(backup, 'w', encoding='utf-8').write(text)
        io.open(path, 'w', encoding='utf-8').write(text.replace(needle, repl, 1))
        return 0
    if act == 'restore':
        path, backup = argv[2:4]
        io.open(path, 'w', encoding='utf-8').write(read(backup))
        return 0
    if act == 'verify':
        path, backup = argv[2:4]
        return 0 if read(path) == read(backup) else 4
    sys.stderr.write('未知动作：%s\n' % act)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
