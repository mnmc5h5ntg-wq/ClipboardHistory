# -*- coding: utf-8 -*-
"""清账表里"靠缺席立论"的那些格，必须能被机器复查（R165 / 承 R131 的文法）。

为什么要有这一支（不是"再 grep 一遍"）：动效与视觉账里有一大类结论长这样 ——
「这一屏没有加载态」「这层没有禁用分支」「这颗按钮永远有标题」。它们的证据是**某个关键字在某个文件里出现 0 次**。
写在散文里的"实测 0 处"不会自己保鲜：哪天有人真给那层加了 `disabled` 分支，
表里那格的理由就成了谎话，而**没有一格会红** —— 这正是 R131 记过的"靠缺席立论要写成可复查文法"，
也是 R206 那一族（台账里"已完成"的断言必须能被机器复查）的反面。

文法（只认这一种，别的写法一律不算声明）：

    缺席:<仓库相对路径>=<标识符>[,<标识符>…]

扫描对象是**已提交的表** `docs/motion_surface_ledger.json` 的 `evidence` 字段。
判定：路径必须解析得到；每个标识符在该文件里必须出现 0 次（出现即"理由过期"）。
名单为空 = 红（R99：按名单遍历的工具必须"名单为空=红"，否则解析器坏掉时会安静地给 0 条然后全绿）。
"""
import argparse
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, 'docs', 'motion_surface_ledger.json')
CLAIM = re.compile(u'缺席:([^\\s=；;，,"]+)=([A-Za-z_][A-Za-z0-9_]*(?:,[A-Za-z_][A-Za-z0-9_]*)*)')


def load_rows(path=TABLE):
    """读表。形状坏了要抛出去，不许在调用方手里变成"0 条声明"。"""
    with io.open(path, encoding='utf-8') as handle:
        table = json.load(handle)
    rows = table['rows'] if isinstance(table, dict) and 'rows' in table else table
    if not isinstance(rows, list):
        raise ValueError('表的形状不是列表：%s' % type(rows).__name__)
    return rows


def parse_claims(rows):
    """[(surface, state, path, keyword)] —— 一条声明一行，按 (格, 词) 展开。"""
    claims = []
    for row in rows:
        evidence = (row.get('evidence') or '') if isinstance(row, dict) else ''
        for match in CLAIM.finditer(evidence):
            path = match.group(1)
            for keyword in match.group(2).split(','):
                claims.append((row.get('surface'), row.get('state'), path, keyword))
    return claims


def resolve(path, root=REPO):
    """表里的证据指针写的是**包内相对路径**（`Sources/ClipboardHistoryApp/…`，
    与 `motion_surface_gate.py` 同一口径），而仓库根下面还有一层包目录。
    两个候选根都要试 —— 少试一个就会把"路径解析得到"报成"解析不到"，
    那是仪器坏，不是台账坏（R131：证据指针「形状合法」不等于「指得到东西」）。"""
    for candidate in (os.path.join(root, path), os.path.join(root, 'ClipboardHistory', path)):
        if os.path.exists(candidate):
            return candidate
    return None


def check(claims, root=REPO):
    """返回问题清单。空表由调用方判红（这一支只负责"每条声明成不成立"）。"""
    problems = []
    cache = {}
    for surface, state, path, keyword in claims:
        full = resolve(path, root) or os.path.join(root, path)
        if full not in cache:
            if not os.path.exists(full):
                cache[full] = None
            else:
                with io.open(full, encoding='utf-8') as handle:
                    cache[full] = handle.read()
        text = cache[full]
        if text is None:
            problems.append(u'%s × %s：证据路径解析不到 ⇒ %s' % (surface, state, path))
        elif keyword in text:
            problems.append(u'%s × %s：理由过期 ⇒ %s 里现在有 `%s`（这一格要重新判）'
                            % (surface, state, path, keyword))
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--table', default=None, help='表的路径（默认 docs 下那份）')
    parser.add_argument('--root', default=None, help='仓库根（默认由脚本位置推出来）')
    args = parser.parse_args(argv)
    global TABLE, REPO
    if args.root:
        REPO = args.root
    table = args.table or TABLE
    rows = load_rows(table)   # 显式取模块级路径：自检要能在内存里换掉它
    claims = parse_claims(rows)
    print('LEDGER_ABSENCE_CLAIMS 格=%d 声明=%d' % (len(rows), len(claims)))
    if not claims:
        print(u'LEDGER_ABSENCE_EMPTY=1 一条"靠缺席立论"的声明都没解析到 ⇒ 要么文法漂了、'
              u'要么表被清空。这一支不许在空名单上给绿（R99）')
        return 1
    problems = check(claims)
    for problem in problems[:12]:
        print('  ' + problem)
    print('LEDGER_ABSENCE_RESULT=%s 不成立=%d/%d'
          % ('ok' if not problems else 'red', len(problems), len(claims)))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
