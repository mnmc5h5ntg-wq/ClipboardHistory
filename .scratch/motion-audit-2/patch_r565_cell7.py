#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R565 补正笔的 ⑦ 格：把这一笔做了什么、现读到什么，写成可复查的账。'''
import io
import sys

P = 'AGENT_STATE.md'
CELL = '''⑦ **补正笔（本笔，`HEAD` 之后那一笔）落了三格改账 + 一格真修**：ⓐ streak 那一格的**解释**从前写「未推状态才数到 5、push 之后会变 0」——**数没错、解释错了**，门的规矩是 as-of（第 N 轮的格 = N −（标签 < N 的最后一笔产品提交的轮次标签）= 564 − 559 = 5 ⇒ 「本轮**之前**的连读轮数」，本轮产品笔不清零它，清零在下一轮），STATE ⑥/⑤ 两格与 FINAL_REPORT §18 那句「产品文件 0 个」一起改齐（现读 §产品面 = **1 个**，与 ②③/CHANGELOG/ITERATION 四处交叉核对）。ⓑ 刀号的第三处互斥：空刀草稿临时借过 M1468 这个名字，而 B 笔 `020cef3` 早已把 M1468/M1469 登记成真刀 ⇒ U-2443 / D-565 ③ / CHANGELOG / ITERATION（正文 + 七维表）/ 补记 ④ / 自伤 ⑥④ 六处一次改齐，现读名册最高 **M1469**、R566 从 **M1470** 起。ⓒ **一格真修（不是改账）**：`commit_round_identity.py` 把退化说明写进了 `范围=` 的**值**里，而那一行是「键=值 键=值」按空格切的结构 ⇒ 一个 ASCII 空格把判它的那条测试打死（`ValueError: dictionary update sequence element #1 has length 1`）——**R564 的绝对根打死 runner、R565 的空格打死本机电池，同一族的第二种坏法：通道值里不许有分隔符**。改成 `退化=未推的为空` 另开一格，并补一条活的门 `test_channel_values_contain_no_spaces`（**没给它登记刀**：这条门自己就是判据，把标签写回带空格立刻红 ⇒ 具名「无刀、靠活门」，不许说成"钉死了")。ⓓ 现读（本笔收口时）：`COMMIT_ROUND_IDENTITY 范围=HEAD~1..HEAD 退化=未推的为空 笔=1 无R前缀=0 身份缺失=0 不一致=0`、`PRODUCT_STREAK_LEDGER_OK streak=5`（**数没动**）、`SOURCES_CELL 账上=R565/`f6c2a1d` git=R565/`f6c2a1d` 一致=是`、清账 `格=162 声明=63 不成立=0/63`、电池 **`Ran 710 / OK (skipped=5)`、退出码 0**（709→710 = 上面那条新门；台账那一格写的 709/5 是它自己那一批的真读数，**不改数、只在此补记本笔的现读**）。ⓔ 本笔是**第二批 push** ⇒ 回答 R566 读单 (g)：派生格（streak / sources / 清账）本笔之前就现读齐了、本笔只动解释与判据文本，不新增产品文件也不动名册 ⇒ 逻辑上造不出"注定红的派生格"；但**这一笔的跑要自己作证**，红了就按自伤记，不许拿这句话预先豁免。

'''

check = '--check' in sys.argv
t = io.open(P, encoding='utf-8').read()
if t.count(CELL.strip('\n')) == 1:
    sys.stderr.write('ALREADY_PATCHED\n')
    sys.exit(1)
anchor = '## R565 ⓪ 开工（2026-11-03'
if t.count(anchor) != 1:
    sys.stderr.write('ANCHOR_BAD count=%d\n' % t.count(anchor))
    sys.exit(1)
if '⑦ **补正笔' in t:
    sys.stderr.write('ALREADY_PATCHED cell\n')
    sys.exit(1)
if not check:
    io.open(P, 'w', encoding='utf-8').write(t.replace(anchor, CELL + anchor, 1))
print('STATE_CELL_7 books=%d check=%d' % (1, 1 if check else 0))
