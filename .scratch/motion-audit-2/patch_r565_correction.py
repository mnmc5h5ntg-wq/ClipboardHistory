# -*- coding: utf-8 -*-
"""R565 补正：把「未推状态才数到 5」那两处错解释改齐，并对齐 §产品面 那句「本轮产品文件 N 个」。"""
import io
import re

# ---- 1) STATE 里剩下的两处错解释 ----
p = 'AGENT_STATE.md'
t = io.open(p, encoding='utf-8').read()
pat = re.compile(
    u'（⚠ 这是\\*\\*未推状态\\*\\*下门自己派生的数：门只认已推的产品笔，本轮产品笔 `f6c2a1d` 还在本地 ⇒ 5；'
    u'push 之后同一命令会派生成 0[^）]*）')
right = (u'（⚠ **as-of 口径**：第 N 轮的格 = N −（标签 < N 的最后一笔产品提交的轮次标签）= 564 − 559 = 5，'
         u'读成「本轮**之前**的连读轮数」⇒ 本轮产品笔 `f6c2a1d` 不清零它，清零发生在下一轮。'
         u'开场那一版把这里解释成「未推状态才数到 5、push 后变 0」——**解释错了、数没错**，由补正笔改齐）')
hits = pat.findall(t)
t = pat.sub(right, t)
io.open(p, 'w', encoding='utf-8').write(t)
print('STATE 解释改齐 %d 处' % len(hits))

# ---- 2) FINAL_REPORT 的 §产品面 那一句：本轮产品文件 N 个 ----
p2 = 'AGENT_FINAL_REPORT.md'
r = io.open(p2, encoding='utf-8').read()
old = u'- **产品面（这一节最该被读的部分）**：本轮产品文件 **0** 个（'
new = (u'- **产品面（这一节最该被读的部分）**：本轮产品文件 **1** 个（R565 = `QuickPickKeyboardHint.swift` 的颜色；'
       u'这一句每一轮自己改写，本轮改写为 1，与 §18 那一笔、STATE `## R565 状态` ③、产品笔 `f6c2a1d` 四处对齐'
       u'（八十一：同一轮里同一件事的几处说法要交叉核对）（')
n2 = r.count(old)
if n2 == 1:
    r = r.replace(old, new, 1)
    io.open(p2, 'w', encoding='utf-8').write(r)
print('REPORT 产品句改写 hits=%d' % n2)

# ---- 3) 复核 ----
t = io.open('AGENT_STATE.md', encoding='utf-8').read()
r = io.open('AGENT_FINAL_REPORT.md', encoding='utf-8').read()
print('残留「未推状态」 STATE=%d REPORT=%d' % (t.count(u'未推状态'), r.count(u'未推状态')))
