# -*- coding: utf-8 -*-
"""R565 补全：把 D-565 一节里撞号的补段三条按位置重编（⑥⑦→⑥⑦、⑤⑥⑦→⑧⑨⑩），
并加一行对照说明 + 一格新决定 ⑪。只动 AGENT_DECISIONS.md 的这一节。"""
import io

PATH = '/Users/wangziyi/Codex_Project0/AGENT_DECISIONS.md'
with io.open(PATH, encoding='utf-8') as handle:
    lines = handle.read().split('\n')

start = [i for i, l in enumerate(lines) if l.startswith(u'## D-565（')]
end = [i for i, l in enumerate(lines) if l.startswith(u'## D-566（')]
assert len(start) == 1 and len(end) == 1 and end[0] > start[0], (start, end)
lo, hi = start[0], end[0]

CIRCLED = set(u'①②③④⑤⑥⑦⑧⑨⑩')
labels = [l[:1] for l in lines[lo + 1:hi] if l[:1] in CIRCLED]
assert len(labels) == 10, labels
want = list(u'①②③④⑤⑥⑦⑧⑨⑩')
print('现读标签: %s' % ''.join(labels))
print('改成    : %s' % ''.join(want))

cursor = lo + 1
index = 0
for i in range(lo + 1, hi):
    if lines[i][:1] in CIRCLED:
        lines[i] = want[index] + lines[i][1:]
        index += 1
        cursor = i
assert index == 10, index

note = (u'⑪ **补账轮（R565 补全，2026-11-04）不落半条守卫，也不重编已被引用的号 —— 但撞号要当场拆开并留对照。** '
        u'这一节的三条补段决定原本与主批的 ⑤⑥⑦ 撞号（同一节里两个 ⑤、两个 ⑥、两个 ⑦），而**已推的三笔 commit 标题写着「D-565 ⑤⑥⑦」**、'
        u'台账与项目记忆也只引用到 ④ ⇒ 逐条引用今天没有断链，可以安全地按位置重编：主批仍是 ①…⑦，'
        u'**补段那三条现在是 ⑧（同族两种坏法收成一条守卫）⑨（判据不许把手伸进渲染）⑩（0 产品文件的段落里基线漂了就不 update）**；'
        u'读到旧引用「D-565 ⑤⑥⑦」（commit `bc5a2af`/`e391ddb`/`6a3542b` 那一族标题）时按这三条新号理解。'
        u'为什么这一格值一笔决定：撞号不是排版问题 —— 它让「D-565 ⑤」成为一个没有唯一指向的引用，'
        u'而本仓库的规矩是引用必须能复查（R206 那一族）。为什么补账轮不落新守卫：'
        u'D-565 ④ 那条跨节对账尺要的是「新守卫 + 各自的刀」，只写守卫的一半会造出一扇没有刀证人的门（R491/R560 的空刀教训反过来说就是：没刀就别开）。')
lines.insert(cursor + 1, u'')
lines.insert(cursor + 2, note)

with io.open(PATH, 'w', encoding='utf-8') as handle:
    handle.write('\n'.join(lines))
print('D-565 节重编完成，插入 ⑪ 于第 %d 行' % (cursor + 3))
