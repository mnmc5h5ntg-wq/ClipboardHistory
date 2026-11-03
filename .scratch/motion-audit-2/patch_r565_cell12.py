#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 补段 ⑫：台账落盘之后的现读五格 + 占位符回读口径 + 帧基线不更新的声明。"""
import io

P = 'AGENT_STATE.md'
CELL = '''⑫ **台账落盘之后现读**（派生格只抄门，一格不手改）：`PRODUCT_STREAK ledger_round=564 streak=5 … as_of=last=631f910 last_round=559 newest=f6c2a1d newest_round=564` ⇒ `PRODUCT_STREAK_LEDGER_OK streak=5`（**as-of 口径**：本段产品 0 文件，不动分界 ⇒ 数不变，与前一笔的 5 逐字相同）；`SOURCES_CELL 账上=R565/`f6c2a1d` git=R565/`f6c2a1d` 一致=是`（本段没有新的产品笔 ⇒ **不需要 `--write`**）；清账 `格=162 声明=63 不成立=0/63`；`CI_CHANNEL_HYGIENE … 绝对根=0 真人路径=0 通道空格=0 RESULT=ok`；`COMMIT_ROUND_IDENTITY 范围=origin/main..HEAD 退化=无 笔=6 无R前缀=0 身份缺失=0 不一致=0`（写这一格时现读；**本笔自己那一笔会再 +1** ⇒ 以 `git rev-list --count origin/main..HEAD` 现读为准，不回头改这里的数）；电池台账后复跑 **`Ran 719 / OK (skipped=5)`、退出码 0**（与台账前那一跑逐字相同 ⇒ 七本的改动没有改变任何判据结果，日志 `/tmp/r565-补-battery1.log`、`/tmp/r565-补-battery2.log`）；**未渲染占位符（percent 后接字母）逐节现读 = 1 处**，且那一处是 `AGENT_UI_AUDIT.md` U-2447 里反引号内的判法引用「键=%s」—— 是被描述的形状本身，不是没替换的模板（其余六节全 0）。⚠ 帧基线**没有更新**：`FRAME_BASELINE_DRIFT=138/356 not-updated`（见 ⑪ⓓ 与 BACKLOG 640）⇒ `docs/frame_baseline.json` 本段一字未动。

'''

t = io.open(P, encoding='utf-8').read()
anchor = '## R565 ⓪ 开工（2026-11-03'
if t.count(anchor) != 1:
    raise SystemExit('ANCHOR_BAD %d' % t.count(anchor))
if '⑫ **台账落盘之后现读**' in t:
    raise SystemExit('ALREADY_PATCHED')
io.open(P, 'w', encoding='utf-8').write(t.replace(anchor, CELL + anchor, 1))
print('CELL12_ADDED')
