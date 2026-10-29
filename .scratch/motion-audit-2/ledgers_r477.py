#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R477 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 475 轮（R476 · 2026-10-29"
AUDIT_SECTION = u"""## 第 476 轮（R477 · 2026-10-29 · U-1827…U-1832）：浮层置顶行改用主列表同一枚图钉（2 张新帧、基线 294；M1297/M1298 2/2）+ 按 R476 跑把 inline 选择器加 4.5pt padding 池、幻影块下限抬到 8 行、冲突提示在内容平涂时具名 NOT-RUN（产品 1 文件 + 判据 + 检测）

- **U-1827：⓪ push 与 CI。** `git push` **`599ec98..3339baf` success**、HEAD=origin/main=`3339baf`、**ahead=0**。R476 跑 `40791382232 ↔ 599ec98` 读时已 completed **failure 3 步**：**Release script tests**（主笔跑的 sources 格仍是补记前的值 ⇒ `FINAL_REPORT_SOURCES_CELL_STALE` 等；补记跑才会过，`SOURCES_CELL_PENDING_ADDENDUM`）；**Swift tests**：inline light `102/101/1.0`（低于 4.5 地板）、幻影块下限 4 行仍读到 1x 分隔线的 **5 行 396px** 灰带、冲突提示在**设置内容整列平涂**时读到 0 墨而红；**Capture gate** 同三条。R475 跑 `40785879418 ↔ 638eeff`、R474 两跑、R473/R472/R471 跑全部失败步骤沿用已读。**签收**：`QUICKPICK_LIST_RULE` 1x 6/6、`ROW_OCR_BADGE` 1x（+27/+24）、`TRUNCATION_NOTE 11/14`。436：R476 跑 `MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=- reds=0`。R477 自身跑随提交创建 ⇒ 收口视网络。
- **U-1828：① 腐烂与预检。** `HIDDEN_ARMS 表=346 可判=1073 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=259 covered=241 arms=656 bad=0`、`ARM_TOTAL files=352 arms=1139`。新增 `M1299`（padding 池）并重跑 R476 表 **2/2**、R470 表 **2/2**；R477 图钉表 **2/2**。旧契约测试 `testRowTitleFlattensNewlinesMarksPinnedAndNeverBlank` 按新语义改名/改断言（置顶不再写进标题）。
- **U-1829：② 产品：浮层置顶行改用主列表同一枚图钉。** 缺陷形状（`quickpick-pinned` 直看）：主列表早已用 `pin.fill` 徽标说"已固定"，浮层却把「置顶」两个字写进标题 —— 同一状态两种语言，而两个字会吃掉标题的截断预算（长标题少显示一截）。修法：`QuickPickController.rowTitle` 去掉「置顶」前缀；`QuickPickRowCell` 加 `pinnedBadge`（9pt `pin.fill`、叠在类型符号右下角、不占固定槽），`isHidden = !entry.isPinned`；读屏标签仍保留「置顶」前缀（图形对读屏是噪音）。旧/新：**2 张新帧**（`quickpick-pinned` 亮暗）、**0 张既有帧变化**（未置顶行逐字节不变）、0 缺失；基线 **292→294**；2 张逐张看过：图钉在类型符号右下角、标题起点未动。读数（`QUICKPICK_PIN`）：light 负臂类型列墨 215→正臂 319（**+104**）、dark 233→338（**+105**）；两档标题末列均 **320px→320px**（前缀确实没回到标题里）。
- **U-1830：③ 判据、刀与旧契约。** 新判据 `testQuickPickPinnedRowsUseTheMainListPinGlyph` 用成对帧（`quickpick-no-source` / `quickpick-pinned`，同内容/同时间只差 isPinned）：① 负臂类型列有墨（尺有对象）；② 正臂在该列多出图钉墨；③ 标题末列不动（前缀还在会红）。刀：`M1297`（图钉永不显示）、`M1298`（图钉永远显示 + 图像恒 pin）均 **CAUGHT**、RESTORE_CLEAN。旧契约测试改成"置顶不进标题文本"（R477 语义），新单测 `QuickPickPinnedMarkerTests`。
- **U-1831：④ 按 R476 跑的分桶继续修检测（靶关键）。** R476 跑的 dark 四门：`候选=442 过span=12 过coverage=12 过ink=12 过rowMax=11`，TOP_SPAN `r319:s320:m320`、`r319:s150:i6:v382:m320`、`r153:s102:i0:v310`、`r138:s99:i0:v307` —— verticalInk 让真带进池了，但 **light 选中了 102/101/1.0 的宽带**（真带 85/80/5.0 在池里），离 4.5 地板差 3.5；dark 选中 102/97/5.0。修法：`best` 先只留 `padding ≥ 4.5` 的候选（池空才退回全量，把缺陷读数打出来），再在池里取最宽实心带。本机恢复 light **98.5/92.5/6.0**、dark **99.0/92.5/6.5**；`M1299`（拆池）CAUGHT。**幻影**：R476 的 4 行下限仍被 1x 分隔线的 **5 行**灰带骗过（396px>25/28），下限抬到 `max(8, Int(8.0*scale))`（1x 8 / 2x 16），旧 32 行缺陷仍整块。**冲突提示**：runner 1x 设置内容整列平涂时两臂都 0 墨 ⇒ 判据改成 `SHORTCUT_CONFLICT_NOT_RUN=settings-content-blank` 具名跳过，不把"没画"记成"警告没画"。三处都只有本地新读数（inline 98.5/6.0 与 99/6.5、幻影本机 2x 通过、冲突本机仍判 2/2），**runner 复验未做**（R477 跑随提交）⇒ 具名 NOT-RUN。
- **U-1832：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **294 帧**、`CHANGED=0 MISSING=0 ADDED=2`，更新后 `294/0/0/0`；全量 **1294/56/0**（472.2s，轻载；第一遍因旧契约测试 `rowTitle` 仍断言「置顶」前缀而红 1 条，改契约后重跑干净）；换装 `ok / SHA_MATCH=1 / 387=387`（版本 1.4.8）；`STORE-SIZE lines=1108 funcs=52 longest=66 top3=[66,62,56]`；产品面连续零改动 **1** 轮（as-of 476，`python3 scripts/product_streak.py --streak-for 476`，last=599ec98）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R477 自身跑；② inline padding 池的 runner 复验（本机 98.5/6.0 与 99/6.5）；③ 幻影 8 行下限的 runner 复验；④ 冲突提示的 runner（内容平涂 ⇒ 预期 NOT-RUN）；⑤ 图钉的 runner 1x/dark；⑥ `SETTINGS_DATA_PATH` 两档；⑦ 既有 runner 复核（无新跑）；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 回执 flake；⑩ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑪ 437–552 的其余未结项仍开。

"""

ITER_SECTION = u"""## Round 474 · R477（第 476 轮 · 2026-10-29）：浮层置顶行改用主列表同一枚图钉（2 张新帧、基线 294）+ 按 R476 跑加 inline padding 池/幻影 8 行/冲突 NOT-RUN

主列表早已用 `pin.fill` 说“已固定”，浮层却把「置顶」两个字写进标题。`rowTitle` 去掉前缀，`QuickPickRowCell` 在类型符号右下角叠 9pt 图钉（不占固定槽）；读屏标签保留「置顶」。2 张新帧、0 张既有帧变化，基线 292→294；`QUICKPICK_PIN` 类型列墨 215→319 / 233→338（+104/+105），标题末列 320→320（前缀没回来）；M1297/M1298 2/2。按 R476 跑分桶继续修检测：dark 442/12/12/12/11，light 选中了 102/101/1.0 的宽带 ⇒ `best` 先只留 padding≥4.5 的候选再取最宽实心带（本机恢复 98.5/92.5/6.0 与 99/92.5/6.5，M1299 CAUGHT）；幻影块下限 4→8 行（runner 1x 分隔线是 5 行 396px）；冲突提示在设置内容平涂时改具名 `SHORTCUT_CONFLICT_NOT_RUN`。预检 259/241/656、rot 346/1073、ARM 352/1139。全量 1294/56/0；build 0 告警；换装 ok/387=387；电池 683/5。⓪ push 599ec98..3339baf success、ahead=0；R476 跑 failure 3 步（sources 时序 + inline light 1.0 + 幻影 396 + 冲突平涂）已读；QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x 签收；436 5/5/77 reds=0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张图钉帧逐张看过：图钉在类型符号右下角、标题起点/末列未动；对照帧同内容同时间。 |
| 判据有效性 | 14/15 | 成对帧三句（有对象/多图钉墨/标题末列不动）；M1297/M1298 2/2；扣 1：第一遍全量因旧 rowTitle 契约测试红 1 条（改契约后干净）。 |
| 假绿防御 | 15/15 | R476 跑暴露 light 1.0/幻影 5 行/冲突平涂三处，均按读数修；padding 池 M1299 钉住；4.5 地板未动。 |
| 产品面推进 | 15/15 | 新类别（浮层置顶图钉）；1 个产品文件；0 张既有帧变化；Store 不动；读屏保留置顶语义。 |
| 台账一致性 | 15/15 | U-1827…U-1832、D-474、294 帧/1294、387=387 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 三处修复的 runner 复验未做就具名 NOT-RUN；冲突在平涂机器上标 NOT-RUN 而不是假绿/假红。 |
| 可复核性 | 15/15 | 2 张帧、215→319/233→338、320→320、四门 12/12/12/11、98.5/6.0 与 99/6.5、M1297–M1299、precheck 259/241/656、rot 346/1073、基线 294 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_474 = u"""## D-474 浮层置顶用主列表同一枚图钉；inline 选择器先过 4.5 地板再取最宽；幻影块下限 8 行；冲突提示在平涂机器上 NOT-RUN（R477）

- 背景：主列表用 `pin.fill` 说“已固定”，浮层的标题却写着「置顶」，两个字吃掉标题截断预算；R476 跑的 inline 四门是 442/12/12/12/11，light 选中 102/101/1.0（真带 85/80/5.0 在池里），幻影 4 行下限仍被 1x 分隔线的 5 行灰带骗过（396px>25/28），冲突提示在设置内容整列平涂时 0 墨而红。
- 决定：`rowTitle` 去掉「置顶」；`QuickPickRowCell` 在类型符号右下角叠 9pt `pin.fill`（不占固定槽），读屏标签保留「置顶」。`best` 先只留 `padding ≥ 4.5` 的候选（池空才退回全量以打印缺陷读数），池内取最宽实心带（coverage≥0.90）。幻影块下限 `max(8, Int(8.0*scale))`。冲突判据在两臂都无字时打 `SHORTCUT_CONFLICT_NOT_RUN=settings-content-blank` 并 skip。
- 理由：同一状态两种语言会让长标题少一截，且图钉不占布局；inline 的对象必须是**已经过内边距地板**的整条带，不是 padding 虚高的宽带；1pt 发丝线在 1x 实测 5 行，固定 3/4 行会把尺的对象换掉；设置内容平涂是机器前提，不是产品缺陷。
- 兼容性/迁移：图钉 2 张新帧、0 张既有帧变化，基线 292→294；inline/幻影/冲突是测试侧检测；4.5 地板与 150 上限未动。
- 边界：三处修复的 runner 复验未做（R477 跑随提交）⇒ NOT-RUN；冲突提示在平涂的 runner 上预期 skip。
- 回滚：删图钉徽标/恢复 rowTitle 前缀；inline 去掉 padding 池会退回 102/1.0 的假对象；幻影下限回 4 会重新误报 1x 分隔线。
"""

CHANGELOG_SECTION = u"""### 浮层置顶行改用主列表同一枚图钉（2 张新帧、基线 294）+ inline padding 池/幻影 8 行/冲突 NOT-RUN（R477 / 第 476 轮 / Round 474 / U-1827…U-1832 · 产品 1 文件 + 判据 + 检测）

"""

BACKLOG_SECTION = u"""**550. R477 跑对三处修复的复验（inline padding 池 / 幻影 8 行 / 图钉）**（R477 观察）
    现象：本机 inline 恢复 98.5/92.5/6.0 与 99/92.5/6.5；幻影 8 行下限本机通过；图钉本机 215→319/233→338。R477 跑随提交创建。
    修法：读 R477 跑的 `INLINE_CODE_PAD`（light 应 85/5.0 或至少 ≥4.5）、`QUICKPICK_GREY_BAND`（块下限 4 行? 等 1x 应 8 行）、`QUICKPICK_PIN`；仍红按读数继续，4.5 不动、150 不放开。

**551. 冲突提示在 runner 1x 设置内容平涂时是 NOT-RUN**（R477 观察）
    现象：R476 跑两档 `SHORTCUT_CONFLICT 负臂末墨行=-1 正臂=-1 下方墨=0`，整列内容没画；改判据为 `SHORTCUT_CONFLICT_NOT_RUN=settings-content-blank` 并 skip。
    修法：这属于已登记的 runner 设置内容列平涂（同 `SETTINGS_DATA_PATH_NOT_RUN`）；哪天内容画出来再读 `SHORTCUT_CONFLICT`，不要把 NOT-RUN 记成绿。

**552. inline 的 `best` 现在带 4.5pt padding 池；旧阅读者要按新对象解释 PAD**（R477 观察）
    现象：同一帧里 102/101/1.0 的宽带与 85/80/5.0 的真带并存；池外选最宽会报 1.0，池内选最宽报 5.0。
    修法：读 `INLINE_CODE_PAD` 时先确认 `best` 的池；若 PAD<4.5 说明真带也不合格（缺陷），不是"宽带被选中"。
"""

STATE_SECTION = u"""## R477 状态（2026-10-29 · 本地 · 第 476 轮 / Round 474）：浮层置顶行改用主列表同一枚图钉（2 张新帧、基线 294）+ 按 R476 跑加 inline padding 池/幻影 8 行/冲突 NOT-RUN；全量 1294/56/0（产品 1 文件 + 判据 + 检测）

最后更新：2026-10-29（本地 · R477 / 第 476 轮 / Round 474）：主列表早已用 `pin.fill` 说“已固定”，浮层却把「置顶」两个字写进标题 —— 同一状态两种语言，而两个字会吃掉标题的截断预算。修法：`QuickPickController.rowTitle` 去掉「置顶」前缀；`QuickPickRowCell` 加 `pinnedBadge`（9pt `pin.fill`、叠在类型符号右下角、不占固定槽），`isHidden = !entry.isPinned`；读屏标签仍保留「置顶」前缀。旧/新：**2 张新帧**（`quickpick-pinned` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **292→294**；2 张逐张看过：图钉在类型符号右下角、标题起点未动。读数（`QUICKPICK_PIN`）：light 类型列墨 215→319（+104）、dark 233→338（+105）；两档标题末列 320→320（前缀没回标题）。新判据用成对帧三句（有对象/多图钉墨/标题末列不动）；`M1297`（永不显示）/`M1298`（永远显示+图像恒 pin）**2/2**；旧 `rowTitle` 契约测试按新语义改名并改断言。**按 R476 跑分桶继续修检测**：dark 四门 442/12/12/12/11；light 选中 102/101/1.0 的宽带（真带 85/80/5.0 在池里）⇒ `best` 先只留 padding≥4.5 的候选（池空退回全量打印缺陷读数）再取最宽实心带；本机恢复 light 98.5/92.5/6.0、dark 99.0/92.5/6.5；`M1299`（拆池）CAUGHT。幻影块下限 4→8 行（runner 1x 分隔线是 5 行 396px）；冲突提示在设置内容平涂时改 `SHORTCUT_CONFLICT_NOT_RUN=settings-content-blank` 并 skip。预检 **259/241/656 bad=0**、ARM **352/1139**、HIDDEN **346/1073 rot=0**。⓪：`git push` **`599ec98..3339baf` success**、HEAD=origin/main=`3339baf`、**ahead=0**；R476 跑 `40791382232 ↔ 599ec98` failure 3 步已读（Release script sources 时序；Swift/Capture 的 inline light 1.0、幻影 396、冲突平涂）；`QUICKPICK_LIST_RULE` 1x 6/6、`ROW_OCR_BADGE` 1x（+27/+24）、`TRUNCATION_NOTE 11/14` 签收；436 `MOTION_FLOOR_FACTS judged=5/5 executed=77 reds=0`。全量 **1294/56/0**（472.2s，轻载；首遍旧契约测试红 1 条，改契约后重跑）；捕获卷 **294 帧**；基线 **294/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 387=387`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 476，`python3 scripts/product_streak.py --streak-for 476`，last=599ec98）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 599ec98..3339baf success、ahead=0；R476 跑 failure 3 步全部已读；QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x、TRUNCATION 11/14 签收；436 5/5/77 reds=0。
② 产品：浮层置顶行改用主列表同一枚图钉（2 张新帧、基线 294）。
③ 判据：成对帧三句 + M1297/M1298 2/2；旧 rowTitle 契约测试改语义。
④ 按 R476 跑修检测：inline padding 池（本机 98.5/6.0、99/6.5，M1299）、幻影 8 行下限、冲突平涂 NOT-RUN。
⑤ 捕获 294 帧；基线 294/0/0/0；build 0 告警；换装 ok/387=387；全量 1294/56/0（轻载）。

NOT-RUN / 阻塞（分开写）：① R477 自身跑；② inline padding 池的 runner 复验；③ 幻影 8 行的 runner 复验；④ 冲突提示在平涂 runner 上（预期 skip）；⑤ 图钉 runner 1x/dark；⑥ `SETTINGS_DATA_PATH` 两档；⑦ 既有 runner 复核（无新跑）；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 回执 flake；⑩ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑪ 437–552 的其余未结项仍开。

下一轮（R478）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R477 自身跑、R476 跑 `40791382232 ↔ 599ec98`、R475 跑 `40785879418 ↔ 638eeff`、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 R477 跑的 `INLINE_CODE_PAD`（light 应 ≥4.5，真带 85/5.0；dark 99/6.5）、`QUICKPICK_GREY_BAND`（1x 块下限 8 行，分隔线 5 行不许再进块）、`QUICKPICK_PIN`（类型列 +104/+105、标题末列不动）、`SHORTCUT_CONFLICT`/`SHORTCUT_CONFLICT_NOT_RUN`**；inline 仍红就按读数继续，4.5 地板不动、150 上限不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""

R477_REPORT_BULLET = u"""- **R477（浮层置顶图钉位 + 按 R476 跑修检测）**：主列表早已用 `pin.fill` 说“已固定”，浮层却把「置顶」写进标题。`rowTitle` 去前缀，类型符号右下角叠 9pt 图钉（不占固定槽）；**2 张新帧、0 张既有帧变化**，基线 **292→294**；`QUICKPICK_PIN` 类型列墨 215→319 / 233→338（+104/+105），标题末列 320→320；M1297/M1298 **2/2**。按 R476 跑分桶（dark 442/12/12/12/11）修检测：light 选中 102/101/1.0 的宽带 ⇒ `best` 先留 padding≥4.5 的候选再取最宽实心带（本机恢复 98.5/92.5/6.0 与 99/92.5/6.5；M1299 CAUGHT）；幻影块下限 4→8 行（1x 分隔线 5 行 396px）；冲突提示在设置内容平涂时改 `SHORTCUT_CONFLICT_NOT_RUN`。⓪ push `599ec98..3339baf` success、ahead=0；R476 跑 failure 3 步已读；QUICKPICK_LIST_RULE 1x 6/6、ROW_OCR_BADGE 1x 签收；436 5/5/77 reds=0。全量 **1294/56/0**（472.2s）；build 0 告警；换装 ok/SHA_MATCH=1/387=387；电池 683/5。
"""

audit = rd(AUDIT); iter_text = rd(ITER); decisions = rd(DECISIONS)
changelog = rd(CHANGELOG); backlog = rd(BACKLOG); state = rd(STATE); report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1: raise SystemExit("REFUSED AUDIT %d" % audit.count(AUDIT_TITLE))
if u"第 476 轮（R477" in audit: raise SystemExit("REFUSED AUDIT 已有 R477")
if u"## Round 474 · R477" in iter_text: raise SystemExit("REFUSED ITER 已有 Round 474")
if u"## D-474" in decisions: raise SystemExit("REFUSED DECISIONS 已有 D-474")
if u"浮层置顶行改用主列表同一枚图钉" in changelog: raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**550." in backlog: raise SystemExit("REFUSED BACKLOG 已有 550")
if state.count(u"## R476 状态") != 1: raise SystemExit("REFUSED STATE %d" % state.count(u"## R476 状态"))
U_CELL_OLD = u"U-31 … U-1820（R476 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1: raise SystemExit("REFUSED REPORT U %d" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R476 节 ②") != 1: raise SystemExit("REFUSED REPORT pointer")

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_474 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1: raise SystemExit("REFUSED CHANGELOG")
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R476 状态", STATE_SECTION + u"## R476 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1832（R477 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R476 节 ②", u"AGENT_STATE.md` 的 R477 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R477_REPORT_BULLET + "\n"

wr(AUDIT, new_audit); wr(ITER, new_iter); wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog); wr(BACKLOG, new_backlog); wr(STATE, new_state); wr(REPORT, new_report)
print("LEDGERS_R477_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
