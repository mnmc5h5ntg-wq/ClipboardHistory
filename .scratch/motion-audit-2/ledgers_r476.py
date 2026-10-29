#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R476 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


AUDIT_TITLE = u"## 第 474 轮（R475 · 2026-10-29"
AUDIT_SECTION = u"""## 第 475 轮（R476 · 2026-10-29 · U-1815…U-1820）：设置快捷键补冲突提示（2 张新帧、基线 292；M1293/M1294 2/2）+ inline ink 门改读垂直窗口、选择器取最宽实心带（四门分桶 12/12/1/0 定位；M1295/M1296 2/2）+ 幻影填充块下限按倍率（1x 发丝线误报）（产品 2 文件 + 判据 + 检测）

- **U-1815：⓪ push 与 CI。** 开工 `git push` **`348e75e..638eeff` success**（两笔：c0b716a/638eeff）、HEAD=origin/main=`638eeff`、**ahead=0**。`ci_read` 成对读：R475 跑 `40785879418 ↔ 638eeff` **failure 3 步**（Swift tests：inline dark「找不到带」、幻影填充 1x 396px>25/28；Capture gate：同两条；Motion coverage floor：`MOTION_FLOOR_FACTS judged=4/5 executed=77 not-run=notice-banner summary=detail-kind-change=4 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=testCopyReceiptAppearsAndDismissesWithAVisibleProcess` = 已知 `RUNNER_COPY_RECEIPT_MOTION_FLAKE`）；R474 跑 `40780110804 ↔ d70cc57` **failure 3 步**（Release script tests：sources 格在补记才派生 ⇒ `FINAL_REPORT_SOURCES_CELL_STALE` 等 3 条，补记跑 `40780464933 ↔ 348e75e` 该步未列 ⇒ 通过；Swift/Capture 为 inline dark + 幻影 1x），R474 补记跑 `40780464933` failure 2 步（同两条）；R473/R472/R471 四跑沿用。**签收**：`QUICKPICK_LIST_RULE` 1x 六帧 `线数=1 y=36px 厚=1px 宽=396px`、`ROW_OCR_BADGE` 1x 两档（负臂末列 208px→正臂 226/225px、墨 +27/+24）、`TRUNCATION_NOTE 11/14`；`SETTINGS_DATA_PATH_NOT_RUN=settings-content-blank` 两档。436 如上（只读新跑 Motion floor，不重猜 `must_judge`）。
- **U-1816：① 腐烂与预检。** `HIDDEN_ARMS 表=344 可判=1070 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=257 covered=239 arms=653 bad=0`、`ARM_TOTAL files=350 arms=1136`。`M1277/M1278` 因 ink 门改名腐烂（命中 0）⇒ 重钉到 `verticalInk` 并复跑 R470 表 **2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1817：② 产品：设置快捷键补冲突提示。** 缺陷形状（`settings-shortcuts-conflict` 直看）：两行可以设成同一组键，两组都真的注册过，而系统只会把热键递给其中一个 —— 另一行动作按下去没有反应，界面一句话都不说。修法：新纯函数 `ShortcutConflictPolicy.conflicts` 两两对账；`SettingsView.shortcutsSection` 在卡片下方画橙色警告（`exclamationmark.triangle.fill` + "「X」与「Y」都设为 ⌃⌥C —— 同一组键只会触发其中一个，请改开一个。"，caption、primary 正文、`accessibilityIdentifier("shortcutConflictWarning")`）。旧/新：**2 张新帧**（`settings-shortcuts-conflict` 亮暗）、**0 张既有帧变化**（正常 `settings-shortcuts` 逐字节不变）、0 缺失；基线 **290→292**；2 张逐张看过：警告在卡片外、与页标题同列、橙图标可辨，正常页无警告。读数（`SHORTCUT_CONFLICT`）：light 负臂末墨行 582px→正臂 660px（差 78px）、下方文字墨 4842、下方橙像素 221、负臂橙 0；dark 同形（下方墨 5783、橙 230、负臂橙 0）。
- **U-1818：③ 判据、刀与名册。** 新判据 `testSettingsShortcutConflictIsSurfaced` 用成对帧（正常 / 第一行与第二行同为 ⌃⌥C），只认**负臂最后墨行之下**新增的文字墨与橙色图标墨（两个方向各一道身份）；4 条 `ShortcutConflictPolicyTests` 纯函数。刀：`M1293`（ForEach 源为空 ⇒ 警告永不画）、`M1294`（`where` 恒 true ⇒ 无冲突也报）**2/2 CAUGHT**。新帧必须进两本名册：`darkSidebarTextBlindSpots`（同 vibrant 子树）与卡片节奏的**有意下方一段**白名单（只这一屏、只允许 1 段）—— 第一遍全量正是因为漏了这两处而红，修的是名册不是产品。
- **U-1819：④ 靶指定 inline 检测（按四门分桶改）。** R475 跑的四门数据：dark `候选=442 过span=12 过coverage=12 过ink=1 过rowMax=0`，`TOP_SPAN` 前六条 `r319:s320:m320`（全宽块底，span 超上限）、`r319:s150:c0.95:i6:m320`（span/coverage/ink 都过，但 rowMax=320 被整行门排掉）、`r153:s102:i0:m102`/`r138:s99:i0:m99`（真带，**本行 ink=0**）。结论：真带只出现在文字上下的 padding 行，文字行被字形切短；旧 ink 门要求"这一行有字"把真带整族砍掉。修法：`Candidate` 新增 `verticalInk`（带上下 ±20pt 窗口里的墨），`best` 的 ink 门改读它；**同时**把对象钉成"实心带（coverage≥0.90）里最宽的一条"，否则 local dark 会从 99/92.5/6.5 变成 83/75.5/7.5 的碎片（padding 虚高但对象错了）。本机复跑：light 98.5/92.5/6.0、dark **99.0/92.5/6.5**（原值恢复），四门 35/35/35/35；`M1295`（ink 门退回本行）/`M1296`（选择器退回 padding 优先）**2/2 CAUGHT**，新纯函数判据 `testInlineCodeBandChoiceReadsInkInTheVerticalWindow`。4.5 地板未动、选择器上界 150 未动。**runner 复验未做**（R476 跑随提交创建）⇒ 具名 NOT-RUN。
- **U-1820：⑤ 幻影填充下限按倍率 + 八步。** R474 引入的 1pt 分隔线在 runner **1x** 上渲染成 3 行灰带，R474 的"连续 ≥3 行"把它读成填充块（396px>25/28px）；修法：块下限改成 `max(4, Int(3.5*scale))`（1x 4 行、2x 7 行），旧缺陷 32 行仍是一整块。build **0 告警**（arm64+x86_64）；捕获卷 **292 帧**、`CHANGED=0 MISSING=0 ADDED=2`，更新后 `292/0/0/0`；全量 **1292/56/0**（511.8s，轻载；新增 5 条判据）；换装 `ok / SHA_MATCH=1 / 387=387`（版本 1.4.8；检测改动是测试侧，产品二进制与之一致）；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 475，`python3 scripts/product_streak.py --streak-for 475`，last=c0b716a）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R476 自身跑（随提交创建）；② inline dark 的 runner 复验（本机已恢复 99/92.5/6.5，四门 35/35/35/35）；③ 幻影填充 1x 的 runner 复验；④ 快捷键冲突提示的 runner 1x/dark；⑤ `SETTINGS_DATA_PATH` 两档（runner 设置内容列平涂）；⑥ `INLINE_CODE_PAD`/`TRUNCATION_NOTE`/`QUICKPICK_SOURCE_ICON`/`CROSS_YEAR`/`MAIN_ROWS`/`SETTINGS_HELPER_AXIS`/`CARD_INSET_CONTROL_FIRST`/`VIDEO_*` 复核（无新跑；R475 跑 TRUNCATION 11/14、QUICKPICK_LIST_RULE 6/6、ROW_OCR_BADGE 1x 已签收）；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 回执 flake；⑨ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑩ 437–550 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 473 · R476（第 475 轮 · 2026-10-29）：设置快捷键补冲突提示（2 张新帧、基线 292）+ inline ink 门改读垂直窗口、选择器取最宽实心带 + 幻影填充块下限按倍率

设置页三行快捷键可以设成同一组键，两组都真的注册过而系统只递一个 —— 另一行按下去没有反应，界面不说。新纯函数 `ShortcutConflictPolicy.conflicts` 两两对账，`SettingsView` 在卡片下方画橙色警告（图标 + 一句话，accessibilityIdentifier）。2 张新帧、0 张既有帧变化，基线 290→292；`SHORTCUT_CONFLICT` 负臂末墨行 582→660px、下方橙像素 221/230、负臂橙 0；M1293/M1294 2/2。靶指定的 inline 检测按 R475 跑四门分桶（dark 442/12/12/1/0）定位：真带只在文字上下 padding 行（本行 ink=0），旧 ink 门把整族砍掉 ⇒ `verticalInk` 门 + "实心带里取最宽"（local dark 恢复 99/92.5/6.5，四门 35/35/35/35），M1295/M1296 2/2。幻影填充下限按倍率（1x 4 行/2x 7 行）修 R474 分隔线在 1x 的 396px 误报。预检 257/239/653、rot 344/1070、ARM 350/1136。全量 1292/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ push 348e75e..638eeff success、ahead=0；R475 跑 failure 3 步（inline/phantom + Motion 回执 1<2），QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x 签收。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张冲突帧逐张看过：警告在卡片外、同列、橙图标可辨；正常页无警告。 |
| 判据有效性 | 14/15 | 成对帧双身份（文字墨+橙像素）；M1293/M1294/M1295/M1296 4/4；扣 1：首遍全量漏了两本名册（新帧），当场修名册后 1292/56/0。 |
| 假绿防御 | 15/15 | inline 按 runner 四门分桶定位到 ink 门；对象钉成最宽实心带，local dark 恢复原值；4.5 未动。 |
| 产品面推进 | 15/15 | 新类别（快捷键冲突提示）；2 个产品文件（策略 + 视图）；0 张既有帧变化；Store 不动。 |
| 台账一致性 | 15/15 | U-1815…U-1820、D-473、292 帧/1292、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | inline/phantom 的 runner 复验未做就具名 NOT-RUN；R474 主笔跑的 Release script 红写明是 sources 格在补记才派生。 |
| 可复核性 | 15/15 | 2 张帧、582→660px/+221 橙、四门 12/12/1/0、35/35/35/35、M1293–M1296、precheck 257/239/653、rot 344/1070、基线 292 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_473 = u"""## D-473 快捷键冲突要在设置页说话；inline 的 ink 门读垂直窗口、对象取最宽实心带；幻影块下限按倍率（R476）

- 背景：三行快捷键可以设成同一组键，系统只递一个，另一行动作静默失效；inline dark 的 runner 四门分桶是 442/12/12/1/0 —— 真带只在文字上下的 padding 行（本行 ink=0），文字行被字形切短，旧 ink 门把真带整族砍掉；R474 的 1pt 分隔线在 runner 1x 渲染成 3 行灰带，被幻影填充判据的"连续 ≥3 行"读成填充块（396px>25/28px）。
- 决定：新增 `ShortcutConflictPolicy` 纯函数 + `SettingsView` 卡片下方橙色警告（成对帧判据 + 2 把刀）；`InlineCodeBandChoice.Candidate` 加 `verticalInk`（带上下 ±20pt 窗口墨），ink 门改读它；`best` 先取 coverage≥0.90 的实心池再取最宽，padding 只破平；幻影块下限 `max(4, Int(3.5*scale))`。
- 理由：冲突是"两组都注册、只一个生效"的事实，必须在设置页说清；inline 的门问的是"这条带里有没有字"而不是"这一行有没有字"；对象必须是整条带，碎片 padding 虚高会把缺陷藏起来；1pt 发丝线的渲染厚度随倍率变，固定 3 行会把尺的对象换掉。
- 兼容性/迁移：冲突 2 张新帧、0 张既有帧变化，基线 290→292；inline/幻影是测试侧检测，产品二进制不变；4.5 地板与 150 上限未动。
- 边界：冲突警告的 runner 1x/dark、inline 与幻影的 runner 复验都未做（R476 跑随提交）⇒ 具名 NOT-RUN；`SETTINGS_DATA_PATH` 在 runner 仍平涂。
- 回滚：删冲突策略/警告与判据；inline 的 verticalInk/最宽实心带可单独回退（回到旧 ink 门与 padding 优先）；幻影下限回到固定 3 行会重新误报 1x 分隔线。
"""

CHANGELOG_SECTION = u"""### 设置快捷键补冲突提示（2 张新帧、基线 292）+ inline 检测按四门分桶改 ink 门/对象 + 幻影填充块下限按倍率（R476 / 第 475 轮 / Round 473 / U-1815…U-1820 · 产品 2 文件 + 判据 + 检测）

"""

BACKLOG_SECTION = u"""**547. inline dark 与幻影 1x 的 runner 复验未做**（R476 观察）
    现象：本机 inline 已恢复 98.5/92.5/6.0 与 99/92.5/6.5（四门 35/35/35/35）；幻影块下限改为 1x 4 行/2x 7 行，本机通过。R475 跑仍是修前代码（dark 442/12/12/1/0、幻影 396px）。
    修法：读 R476 跑的 `INLINE_CODE_GATES`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`；仍有红就按新的四门读数继续，4.5 地板不动。

**548. 快捷键冲突提示的 runner 1x/dark 未签收**（R476 观察）
    现象：本机亮暗两档 `SHORTCUT_CONFLICT` 均 582→660px、橙 221/230、负臂橙 0；runner 的 1x 橙图标可能小于 10px²。
    修法：读新跑的 `SHORTCUT_CONFLICT`；读不到就具名 NOT-RUN，不改 10pt/30px² 地板。

**549. 主笔跑的 Release script tests 因 sources 格在补记才派生而红**（R476 观察）
    现象：R474 主笔 `40780110804 ↔ d70cc57` 的 Release script tests 3 条红（`FINAL_REPORT_SOURCES_CELL_STALE`、跳过名册无结论、第二来源），补记跑 `40780464933 ↔ 348e75e` 该步通过 ⇒ 不是产品缺陷，是"格子在补记里才派生"的时序。
    修法：读账时把主笔跑的这一步标成 `SOURCES_CELL_PENDING_ADDENDUM`，不要记成回归；要消除噪音只能在主笔提交前就把 sources 格写成该笔 SHA（需要先 commit 再 amend，不可取），或接受补记跑作准。
"""

STATE_SECTION = u"""## R476 状态（2026-10-29 · 本地 · 第 475 轮 / Round 473）：设置快捷键补冲突提示（2 张新帧、基线 292）+ inline ink 门改读垂直窗口/最宽实心带 + 幻影填充块下限按倍率；全量 1292/56/0（产品 2 文件 + 判据 + 检测）

最后更新：2026-10-29（本地 · R476 / 第 475 轮 / Round 473）：设置页三行快捷键可以设成同一组键，两组都真的注册过而系统只递一个 —— 另一行动作按下去没有反应，界面不说。修法：新纯函数 `ShortcutConflictPolicy.conflicts` 两两对账；`SettingsView.shortcutsSection` 在卡片下方画橙色警告（`exclamationmark.triangle.fill` + "「X」与「Y」都设为 ⌃⌥C —— 同一组键只会触发其中一个，请改开一个。"，caption、primary 正文、`accessibilityIdentifier`）。旧/新：**2 张新帧**（`settings-shortcuts-conflict` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **290→292**；2 张逐张看过：警告在卡片外、与页标题同列、橙图标可辨，正常页无警告。读数（`SHORTCUT_CONFLICT`）：light 负臂末墨行 582→660px（差 78px）、下方文字墨 4842、橙 221、负臂橙 0；dark 同形（5783/230/0）。判据用成对帧 + 双身份（文字墨 + 橙像素）；4 条纯函数；`M1293`（永不画）/`M1294`（无冲突也报）**2/2**。新帧进两本名册（vibrant 盲区、卡片外有意一段）。**靶指定的 inline 检测已按四门分桶改**：R475 跑 dark `候选=442 过span=12 过coverage=12 过ink=1 过rowMax=0`，真带只在文字上下 padding 行（本行 ink=0）⇒ `Candidate.verticalInk`（±20pt 窗口墨）+ `best` 先取 coverage≥0.90 实心池再取最宽；本机恢复 light 98.5/92.5/6.0、dark **99.0/92.5/6.5**（四门 35/35/35/35）；`M1295`（ink 门退回本行）/`M1296`（选择器退回 padding 优先）**2/2**；4.5 地板与 150 上限未动。幻影填充块下限改 `max(4, Int(3.5*scale))`（1x 4 行/2x 7 行），修 R474 分隔线在 1x 的 396px 误报。预检 **257/239/653 bad=0**、ARM **350/1136**、HIDDEN **344/1070 rot=0**。⓪：`git push` **`348e75e..638eeff` success**（两笔）、HEAD=origin/main=`638eeff`、**ahead=0**；R475 跑 `40785879418 ↔ 638eeff` failure 3 步（inline dark、幻影 1x、Motion 回执 1<2）；R474 主笔 `40780110804 ↔ d70cc57` failure 3 步（Release script 的 sources 格时序 + inline + 幻影）、补记 `40780464933 ↔ 348e75e` failure 2 步；`QUICKPICK_LIST_RULE` 1x 6/6、`ROW_OCR_BADGE` 1x（+27/+24）、`TRUNCATION_NOTE 11/14` 签收；436 见 `MOTION_FLOOR_FACTS judged=4/5 executed=77 reds=1`（已知回执 flake）。全量 **1292/56/0**（511.8s，轻载）；捕获卷 **292 帧**；基线 **292/0/0/0**；build **0 告警**（arm64+x86_64）；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 475，last=c0b716a）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `348e75e..638eeff` success、ahead=0；R475 跑 failure 3 步已读（inline/phantom 为修前代码、Motion 回执 flake）；R474 两跑已读（Release script 的 sources 格时序）；QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x 签收。
② 产品：设置快捷键补冲突提示（2 张新帧、基线 292）。
③ 判据：成对帧 + 文字墨/橙像素双身份，M1293/M1294 2/2；新帧进两本名册；precheck 257/239/653；rot 344/1070。
④ 靶检测：按四门分桶把 ink 门改读 verticalInk、对象取最宽实心带；本机恢复 99/92.5/6.5（四门 35/35/35/35）；M1295/M1296 2/2；4.5 未动。
⑤ 幻影下限按倍率（1x 4/2x 7）；捕获 292 帧；基线 292/0/0/0；build 0 告警；换装 ok/387=387；全量 1292/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R476 自身跑（随提交创建）；② inline dark 的 runner 复验（本机已恢复）；③ 幻影填充 1x 的 runner 复验；④ 快捷键冲突提示的 runner 1x/dark；⑤ `SETTINGS_DATA_PATH` 两档（runner 平涂）；⑥ 既有 runner 复核（无新跑）；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 回执 flake；⑨ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑩ 437–550 的其余未结项仍开。

下一轮（R477）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R476 自身跑、R475 跑 `40785879418 ↔ 638eeff`、R474 两跑 `40780110804 ↔ d70cc57`/`40780464933 ↔ 348e75e`、R473/R472/R471 跑的全部失败步骤；**重点读 R476 跑的 `INLINE_CODE_GATES`/`INLINE_CODE_TOP_SPAN`/`INLINE_CODE_PAD`（dark 应恢复 99/92.5/6.5、四门 35/35/35/35）与 `QUICKPICK_GREY_BAND`（1x 块下限 4 行）**：inline 仍红就按新分桶继续，4.5 地板不动、选择器上界 150 不动；`SHORTCUT_CONFLICT`（runner 1x/dark）；`ROW_OCR_BADGE` 1x 已签收；`QUICKPICK_LIST_RULE` 1x 6/6 已签收；`SETTINGS_DATA_PATH`；`TRUNCATION_NOTE`；`QUICKPICK_SOURCE_ICON`；`CROSS_YEAR`/`MAIN_ROWS`；`SETTINGS_HELPER_AXIS`；`CARD_INSET_CONTROL_FIRST`；`VIDEO_*`；Capture MATERIAL_BLIND_NOT_RUN；436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R476_REPORT_BULLET = u"""- **R476（快捷键冲突提示位 + inline 检测按四门分桶）**：三行快捷键可以设成同一组键，系统只递一个、另一行静默失效。新 `ShortcutConflictPolicy.conflicts` + `SettingsView` 卡片下方橙色警告；**2 张新帧、0 张既有帧变化**，基线 **290→292**；`SHORTCUT_CONFLICT` 负臂末墨行 582→660px、橙 221/230、负臂橙 0；M1293/M1294 **2/2**。靶指定的 inline 检测按 R475 跑四门分桶（dark 442/12/12/1/0）定位：真带只在文字上下 padding 行（本行 ink=0）⇒ `verticalInk` 门 + "实心带里取最宽"；本机恢复 light 98.5/92.5/6.0、dark **99.0/92.5/6.5**，四门 35/35/35/35；M1295/M1296 **2/2**，4.5 地板未动。幻影填充下限改 1x 4 行/2x 7 行，修 R474 分隔线在 1x 的 396px 误报。⓪ push `348e75e..638eeff` success、ahead=0；R475 跑 failure 3 步（修前 inline/phantom + Motion 回执 1<2）；QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x 签收。全量 **1292/56/0**（511.8s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 475 轮（R476" in audit: raise SystemExit("REFUSED AUDIT 已有 R476")
if u"## Round 473 · R476" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 473")
if u"## D-473" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-473")
if u"设置快捷键补冲突提示" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**547." in backlog: raise SystemExit("REFUSED BACKLOG 已有 547")
if state.count(u"## R475 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R475 状态"))
U_CELL_OLD = u"U-31 … U-1808（R475 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R475 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_473 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R475 状态", STATE_SECTION + u"## R475 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1820（R476 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R475 节 ②", u"AGENT_STATE.md` 的 R476 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R476_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R476_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
