# -*- coding: utf-8 -*-
"""R582 / 派单 ④：把「红名对账」从每轮手写五条"为什么不算"，做成**一个可数的口径 + 一扇会红的门**。

上一轮交的是「红名 11 条 vs 编号 6 处 ⇒ 对不上 5 条」，那五条靠**散文**逐条说明归属。
散文不能复算：下一轮只要换了措辞，"对不上"就重新变成一个人数字。这一支把它钉成三条机器规则：

1. 每一行 `· 红名「…」→ <归属>` 只有两种合法形状：
   · 归属里带 `⑨·`（进了本轮自伤编号）⇒ **计入**；
   · 归属里带 `不计入对账口径` 且写明三类名字之一（契约名 / 通道未跑 / 基名在漂）⇒ **不计入**（但可数）；
   · 两种都不是 ⇒ **未标** ⇒ 这一支退 1（"对不上"由门报出，不再由我手写理由）。
2. **名单为空 = 红**（R99 那一族：解析器坏掉时会安静地给 0 条然后全绿）。
3. **口径一旦启用就不许关**：只要有任何一节写过 `对账口径`，最新那一节没有它就退 1 ——
   否则"下一轮不写这行"就能把门悄悄降回散文。

只管未来：最新一节之前那些轮次没有这个 token 是**历史事实**，本支不回头判它们（R564 那一族的
"判范围只到还改得动的地方"）。`--measure` 那一档不参与闸门，只把旧节按新口径重数一遍给证人。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, 'AGENT_STATE.md')

# 三类"允许不计入"的名字 —— 派单 ④ 点名的就是这三类，多一类都要先改这里并配刀。
NAMED_CATEGORIES = (u'契约名', u'通道未跑', u'基名在漂')
ROUND_HEADING = re.compile(r'^## (R\d{3}) 状态', re.M)
RED_NAME_LINE = re.compile(u'·\\s*红名「')
REGIME_TOKEN = u'对账口径'
COUNTED_TOKEN = u'⑨·'
EXEMPT_TOKEN = u'不计入对账口径'
NUMBER_RE = re.compile(r'(\d+)')


def sections(text):
    """把 AGENT_STATE 切成 `## Rnnn 状态` 那一层的节（节 = 本标题到下一个同级标题）。"""
    marks = [(m.start(), m.group(1)) for m in ROUND_HEADING.finditer(text)]
    out = []
    for i, (start, name) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((name, text[start:stop]))
    return out


def newest(body_sections):
    def number(name):
        return int(name[1:])
    return max(body_sections, key=lambda pair: number(pair[0])) if body_sections else None


def classify(lines):
    """返回 (计入行, 去重后的编号个数, 不计入, 未标, 未标的逐字行)。

    ⚠ **两个口径必须分开报**：一行红名可以指向同一个编号（R580 那两行「预检 bad=1」与「M628 命中=3」
    都进 ⑨·2），所以「计入行数」与「去重编号数」本来就不同 —— 上一轮手写的那两个数（红名 16 / 编号 9）
    一个是行、一个是去重后的号。门若只报一个，下一轮就会拿错的那个对账（R540 那一族：口径要写死）。
    """
    counted = exempt = unmarked = 0
    numbers = set()
    unmarked_lines = []
    for line in lines:
        tail = line.split(u'→')[-1] if u'→' in line else u''
        if COUNTED_TOKEN in tail:
            counted += 1
            numbers.update(NUMBER_RE.findall(tail))
        elif EXEMPT_TOKEN in tail and any(name in tail for name in NAMED_CATEGORIES):
            exempt += 1
        else:
            unmarked += 1
            unmarked_lines.append(line.strip()[:120])
    return counted, len(numbers), exempt, unmarked, unmarked_lines


def red_name_lines(section_body):
    """只数「红名对账」那一格里的行，不数正文里其它提到红名的句子。

    为什么要切这一格：⑨ 正文里也满是"那一朵红"这种措辞，整节去扫会把解释自己判成违规
    （R55 的 M276 那一族），于是下一次有人为了变绿去删解释。
    """
    block = section_body.split(u'红名对账')
    if len(block) < 2:
        return []
    tail = block[-1]
    cut = len(tail)
    for stop_token in (u'\n⑨', u'\n##', u'\n###'):
        found = tail.find(stop_token)
        if found >= 0:
            cut = min(cut, found)
    return [ln for ln in tail[:cut].split('\n') if RED_NAME_LINE.search(ln)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--state', default=None, help='台账路径（默认仓库根那份）')
    parser.add_argument('--measure', action='store_true',
                        help='把**每一节**按新口径重数一遍（只报数、不判、不影响退出码）')
    args = parser.parse_args(argv)
    path = args.state or STATE
    with io.open(path, encoding='utf-8') as handle:
        text = handle.read()
    all_sections = sections(text)

    if args.measure:
        for name, body in all_sections[:6]:
            lines = red_name_lines(body)
            counted, numbers, exempt, unmarked, _ = classify(lines)
            print(u'RED_NAME_MEASURE 节=%s 红名=%d 计入行=%d 编号去重=%d 不计入=%d 未标=%d 口径=%s'
                  % (name, len(lines), counted, numbers, exempt, unmarked,
                     u'有' if REGIME_TOKEN in body else u'无'))
        return 0

    target = newest(all_sections)
    if target is None:
        print(u'RED_NAME_RECONCILIATION=EMPTY 一节 `## Rnnn 状态` 都没解析到 ⇒ 标题形状漂了，'
              u'这一支不许在空名单上给绿（R99）')
        return 1
    name, body = target
    enabled_before = any(REGIME_TOKEN in b for _, b in all_sections)
    has_regime = REGIME_TOKEN in body
    lines = red_name_lines(body)

    if not has_regime:
        if enabled_before:
            print(u'RED_NAME_RECONCILIATION=REGIME_CLOSED 节=%s ⇒ 更早的节启用过「%s」这一格口径，'
                  u'而最新一节没有它。门不许悄悄降回散文：要么补上口径行，要么把这轮的账写成编号。'
                  % (name, REGIME_TOKEN))
            return 1
        print(u'RED_NAME_RECONCILIATION 节=%s 红名=%d 口径=未启用（旧节） 处置=不判'
              u' —— 这一支只管未来：本轮之后第一笔写了口径行的账开始生效' % (name, len(lines)))
        return 0

    if not lines:
        print(u'RED_NAME_RECONCILIATION=EMPTY 节=%s ⇒ 口径行在、可「红名对账」那一格一行都没解析到，'
              u'要么格式漂了要么被人删空。不许读成「本轮没有红名」' % name)
        return 1

    counted, numbers, exempt, unmarked, samples = classify(lines)
    print(u'RED_NAME_RECONCILIATION 节=%s 红名=%d 计入行=%d 编号去重=%d 不计入=%d 未标=%d 对不上=%d 口径=已启用'
          % (name, len(lines), counted, numbers, exempt, unmarked, unmarked))
    for sample in samples[:8]:
        print(u'  未标：' + sample)
    return 0 if unmarked == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
