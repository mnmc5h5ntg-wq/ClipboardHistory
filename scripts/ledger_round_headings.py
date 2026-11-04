# -*- coding: utf-8 -*-
"""七本台账里**逐字重复的轮次标题行**必须会红（R574 · dispatch ④ 的修复证人）。

为什么要有这一支（不是"再 grep 一遍"）：R573 那一轮写手给 `AGENT_UI_AUDIT.md` 补一行 U 号时，
替换串写成「`\n` + 那一行 + 从 anchor 起的全部内容」⇒ anchor 之后的**整段**被接了两遍，
文件从 15812 行涨到 31281 行。抓到它的是既有的"U 号重复"那一格（2256 个号各定义两次），
而**没有任何一格**盯着"同一轮的标题出现两遍"这件事 —— 也就是说这一族第四次得手时，
证人仍然是碰巧在场的那一把别的尺。

判法刻意只用**整行逐字相同**，不用"轮次号相同"：
- `## 第 498 轮（R499 …）` 与 `## 第 498 轮续一（R499 续 …）` 是**两条不同的合法标题**
  （同一轮里追加的续节），按号判会把它读成重复；
- `## Round 29 · …` 与 `## Round 29d · …` 同一形状；
- 而整段复制必然留下**逐字相同**的两行 ⇒ 这条判法恰好只判那件真要判的事。
（R574 本轮第一次试写这把尺时用的正是"按号判"，当场把上面两种合法形状读成 4 处重复 ⇒
  形状没定对的新尺比没有尺更坏，这条教训写在这里而不是只写在账里。）

用法：`python3 scripts/ledger_round_headings.py [--root 仓库根] [--books a.md,b.md]`
退出码：0=没有重复；1=有重复（逐条打印）或一本书都没读到（R99：空名单不许给绿）。
"""
import argparse
import io
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = [
    'AGENT_UI_AUDIT.md',
    'AGENT_VISUAL_ITERATION.md',
    'AGENT_STATE.md',
    'AGENT_BACKLOG.md',
    'AGENT_DECISIONS.md',
    'AGENT_FINAL_REPORT.md',
    'CHANGELOG.md',
]
HEADING_PREFIX = '## '


def headings(path):
    """返回 (该书的 `## ` 标题行 [(行号, 文本)…]，逐字重复的 [(文本, [行号…])…])。

    读不到文件要抛出去，不许在调用方手里变成"0 条"（R99 那一族）。
    """
    with io.open(path, encoding='utf-8') as handle:
        lines = handle.read().split('\n')
    got = [(index, ln) for index, ln in enumerate(lines, 1) if ln.startswith(HEADING_PREFIX)]
    where = {}
    for index, ln in got:
        where.setdefault(ln, []).append(index)
    return got, [(text, idxs) for text, idxs in sorted(where.items()) if len(idxs) > 1]


def check(root, books):
    problems = []
    total = 0
    for book in books:
        path = os.path.join(root, book)
        if not os.path.isfile(path):
            problems.append(u'%s 读不到这个文件 ⇒ 名单里的书必须真在仓里' % book)
            continue
        got, dups = headings(path)
        total += len(got)
        for text, idxs in dups:
            problems.append(u'%s:%s（与 :%s 逐字相同）%s' % (book, idxs[-1], idxs[0], text[:48]))
    return total, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', default=REPO, help='台账所在目录（默认仓库根）')
    parser.add_argument('--books', default=None, help='逗号分隔的书名（默认那七本）')
    args = parser.parse_args(argv)
    books = args.books.split(',') if args.books else BOOKS
    total, problems = check(args.root, books)
    print('ROUND_HEADINGS 本=%d 标题=%d 逐字重复=%d' % (len(books), total, len(problems)))
    if total == 0:
        print(u'ROUND_HEADINGS_EMPTY=1 一本里都没解析到 `## ` 标题 ⇒ 要么前缀漂了、'
              u'要么表被清空，这一支不许在空名单上给绿（R99）')
        return 1
    for problem in problems[:12]:
        print('  ' + problem)
    print('ROUND_HEADINGS_RESULT=%s 重复=%d' % ('ok' if not problems else 'red', len(problems)))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
