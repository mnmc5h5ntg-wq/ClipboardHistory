#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 R192/R193 学到的失效形状追加进两份既有记忆文件（不新增文件、不动索引行长度）。

规矩：索引 MEMORY.md 的条目已经超长（系统警告 33129 > 25000），所以这一轮**只往主题文件里追加**，
不碰索引 —— 索引变长比没索引更坏。
"""
import io

USER = '/Users/wangziyi/.qoder-cn/memory/feedback-probe-and-assertion-hygiene.md'
PROJ = '/Users/wangziyi/.qoder-cn/projects/-Users-wangziyi-Documents-Codex-Project0/memory/target-mode-status-2026-10-19-r159-r175.md'

USER_BLOCK = u'''

## R192–R193 一批（2026-10-19，同一晚两轮）

- **共用一条绝对线会"把小臂判成不存在"**（R192 / D-196）：`sharedMovingFloor` = 较大峰值 × 比例 ⇒ 幅度不对称时
  较小那一臂的**峰值本身就低于这条线**，它整臂读 0 帧，"两臂相同"被读成"两臂都落定"。本机实测 0.027/0.234 ⇒ 线 0.0351，
  那一臂从 11 帧掉到 0 帧。判据不引入新阈值：拿线自己当判据（"小臂峰值 ≥ 线"）。⇒ 跨臂**相同性**比较用同一条线；
  跨臂**谁演得久**在幅度不等时既不配各自归一化（212）也不配共用线，欠的是时间轴。
- **开单前读被告代码，行号 + grep 符号名不算读通**（R192 / U-628）：我上一轮按 `:2916`/`:2332` 点名的两处靶
  都不成立 —— 一处 R59 就用共享线了，一处明写"帧数不参与判定"；真站点在别处。同一条老规矩第四次复发。
- **`contains("X")` 会被同一方法体里的兄弟行喂饱**（R193 / 刀 M723 先 ESCAPED）：要求"两臂都打印时间轴"的守卫
  用 `section.contains("过程=")`，摘掉开臂那行后关臂那行还在 ⇒ 绿。改成**按站点数次数=2**（R85 那一课的兄弟形状：
  只数"出现过"的守卫必须数次数，次数=出口数）。
- **生成器"数了锚点却没替换"会自报成功**（R193 / U-634）：批量替换脚本先做 `count(needle)==want` 的检查，
  然后**忘了执行 replace**，照样打印 `PATCHED_OK calls=6`。修法：检查通过后替换，末尾按**改完之后的文本**
  再数一遍 post-state（5 条计数），不吻合就拒绝写盘。自报成功要按结果作证，不是按"我数过锚点"。
- **帧数地板会被散点撑绿**（R193 / D-197）：`transitionFrameCount ≥ 3` 允许"第 1、8、20 帧各抖一下"，
  而"演了一段"要的是**连续**。真卷五跑：`row-insert 开` 帧数 7~10、含峰值那段只有 1~2 帧对 ⇒ 那两处 AppKit 行 A/B
  的"看得见动画"结论一直是散点给的。⇒ 判"有过程"必须问连续段（时长 ÷ 本次实测中位间隔）。
- **新尺自己也要先量分布再当判据**（R193）：同一条"连续段跨几个间隔"五跑给 1.1/1.4/1.6/2.6/2.9 ⇒ 压 `≥2` 会有 2/5 跑红。
  所以本轮只装仪器、不换判据，并把"要一个更稳的统计量"开成 BACKLOG 218。单次读数不配签字这条，这次是用在新尺自己身上。
'''

PROJ_BLOCK = u'''

## R192–R193（2026-10-19 晚，接续上一节）

- R192 `9a8c9c9`→`9d5fc1a` 之前一笔：212 结案（④ 换同一条线 + `bandShared ≥ 1`）；216 结案并**更正 R191 点名的两处位置**
  （`:2916`/`:2332` 都不是 212 的形状；真站点 = `testSystemSymbolEffectsAreOutOfThisRulersReach`、
  `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`，改成"两把尺都说相同"才不红）。
  新开 217、D-196（共用线的适用域）。CI：run 39204808115（`2a7c829`）与 39206313202（`9a8c9c9`）**都是 success**
  ⇒ R190 修的能力谓词在 runner 上验收过，STEP[13]/[15]/[17] 那三朵红已消失。
- R193 `28b7d0f`：217 的"装仪器"结案 —— `armProcessInIntervals`（含峰值段时长 ÷ 本次实测中位间隔）+
  `processReadingVerdict`（散点撑绿 / 有一段过程 / 帧数本来就不够）接进三处 AppKit 行 A/B；
  五跑读数证明那 9~11 帧多数是散点（`row-insert 开` 连续段 1.1~2.9 个间隔、帧对 1~2），
  但这条轴自己在 2.0 界上翻面 ⇒ **判据故意没换**，新开 218 + D-197。刀 M712–M720（R192）、M721–M725（R193）；
  下一支刀号 **M726**。
- 计数（R193 落盘时）：swift 判据 **879 例 / 42 skip / 0 失败**、脚本电池 **Ran 368 / OK**、变异表 51 张 / 145 臂、
  U 到 **U-634**、BACKLOG 到 **218**、D 到 **D-197**、清账表 115 已清账 / **47 未判**、帧 138 张（R189 起未变）。
- 七维自评曲线：189=92、190=89、191=86、**192=90、193=86** ⇒ 连续两轮里有一轮不达标（<90），
  欠的两格固定是"真实视觉审查"（产品 0 文件、没有新界面）与"产品面推进"。
  R194 的靶已写进 `AGENT_STATE.md`：⓪ 读 `28b7d0f` 那一跑并从 runner 抓 `MOTION_NATIVE row-insert 开 过程=`；
  ① 218 选一个更稳的统计量；② 215 真机亮档一格；③ 201/202/205/207 + 47 格；
  ④ **产品已连续三轮 0 文件 —— 要么按 173 的清单动一个真位点，要么把三臂逐帧条带真看一遍**。
'''

for path, block in ((USER, USER_BLOCK), (PROJ, PROJ_BLOCK)):
    text = io.open(path, encoding='utf-8').read()
    marker = block.strip().split(u'\n')[0]
    if marker in text:
        print('ALREADY_APPENDED %s' % path.split('/')[-1])
        continue
    with io.open(path, 'a', encoding='utf-8') as h:
        h.write(block)
    print('APPENDED %s +%d chars' % (path.split('/')[-1], len(block)))
