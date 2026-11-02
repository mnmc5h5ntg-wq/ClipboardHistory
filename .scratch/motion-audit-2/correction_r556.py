# -*- coding: utf-8 -*-
"""R556 更正：把"电池在推送之后才抓到 sources 格时序红"这件事写进本轮 ⑤ 末尾。"""
import io

p = 'AGENT_STATE.md'
s = io.open(p, encoding='utf-8').read()

anchor = u'629 那两条修法相反的出口（(A) 加密录制 / (B) 换判据对象）就按那三个数选，不靠猜。'
assert s.count(anchor) == 1, s.count(anchor)

add = (u'**R556 更正（电池抓到的一格，顺序错在我）**：台账笔 `680aea3` 推出去之后我才跑电池，'
       u'它当场报两格红 —— `test_final_report_headline` 与 `test_sources_cell_second_source` 都说 '
       u'`FINAL_REPORT_SOURCES_CELL_STALE`：那一格写 commit `6b70474`，而 git 说最近动源码的是 `1a7e31c`。成因是我把 `report_sources_cell.py --write` 放在**产品笔提交之前**，'
       u'于是它派生到的还是上一轮那笔 —— 与 R474 那格「sources 格补记才派生」同族，只是这次是**顺序**而不是补记。'
       u'正确顺序：写台账 → 提交产品/判据笔 → **再**跑 `--write` → 电池 → 推送。本笔按正确顺序重跑：'
       u'`SOURCES_CELL 账上=R555/6b70474 git=R556/1a7e31c 一致=否` → `SOURCES_CELL_WRITTEN 复核=一致`，'
       u'整只电池 695/5 OK。另 `test_skip_roster` 那一朵在整卷里红、单跑 3/3 OK ⇒ 具名 flake（R553/R554 同形两次），'
       u'不改判据也不改阈值。**已推的 `680aea3` 不改写**，本笔只做更正与说明。')

s = s.replace(anchor, anchor + add, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('correction written')
