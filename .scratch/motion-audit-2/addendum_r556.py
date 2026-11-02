# -*- coding: utf-8 -*-
"""R556 补记：把本轮各笔的 run↔commit 成对号与 R557 读单写进 STATE 的 R556 节 ⑤ 末尾。"""
import io

p = 'AGENT_STATE.md'
s = io.open(p, encoding='utf-8').read()

anchor = (u'4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板与 1x 的 6.0pt 整行地板均不动。\n')
assert s.count(anchor) == 1, s.count(anchor)

add = (u' **R556 补记（收口后）**：⓪ 笔 `eb883ad` 的跑 `41442000018` 现已 concluded='
       u'**success** ⇒ STEP[9] 之外再多一格独立证据（那一跑连 622/SelectionReveal 都没红）。'
       u'本轮产品笔 `1a7e31c` 与刀表笔 `5ba5b2f` **同次 push ⇒ 只有头笔建跑** `41450045802 ↔ 5ba5b2f`'
       u'（取号时 in_progress ⇒ **未读**；`1a7e31c` 无独立跑，由该笔覆盖）；台账笔 `680aea3` ⇒ 跑 '
       u'`41450081248`（取号时 queued ⇒ **未读**）。**R557 必读这两跑的全部失败步骤**，而且本轮新加的'
       u'`MOTION_MARKDOWN_MODE_FADE … 窗口= 每格= 相邻帧差=[…]` 会在 runner 上第一次打出真数 —— '
       u'629 那两条修法相反的出口（(A) 加密录制 / (B) 换判据对象）就按那三个数选，不靠猜。')

s = s.replace(anchor, anchor + add, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('addendum written')
