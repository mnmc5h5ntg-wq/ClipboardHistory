#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 把 STEP[19] 那一朵的归因接进 R566 的 ⓪ 格文本（同族 212 的第二次露面、换了形状）。
import io

P = '.scratch/motion-audit-2/ledgers_r566.py'
t = io.open(P, encoding='utf-8').read()
old = '最后一跑另加 **STEP[19]**\','
new = ('最后一跑另加 **STEP[19]**。那一朵是 **212 的第二次露面、换了一种形状**：'
       '`MOTION_FLOOR_SUITE_RED=1 … testBandCaptureIsCheaperAndStillSeesTheMotion：'
       'XCTAssertLessThan failed (11.394375 is not less than 11.1310105)` ⇒ 判的是「带捕获必须比整窗便宜」'
       '这条**方向**线（不是 212 当年的帧数地板），且同批七跑只有这一跑红 ⇒ 判间歇、不署名本轮、不放宽'
       '（R87/R146 的口径：单遍读数不配给产品定罪）\',')
assert t.count(old) == 1, t.count(old)
io.open(P, 'w', encoding='utf-8').write(t.replace(old, new, 1))
print('CIDLIST_EXTENDED_OK')
