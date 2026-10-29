#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 494 轮（R495 · 2026-10-30"
AS=u"""## 第 495 轮（R496 · 2026-10-30 · U-1935…U-1940）：浮层候选行补搜索命中高亮（2 张旧帧变化 + 2 张新帧、基线 324；M1339/M1340 2/2）（产品 1 文件 + 判据）

- **U-1935：⓪ push 与 CI。** 开工一次快进 push **`bbfe31c..2e7828f` success**、HEAD=origin/main=`2e7828f`、**ahead=0**。R495 跑 `40920092629 ↔ bbfe31c` **success**（`Executed 1311/80 skip/0`）：`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` light/dark（runner 设置帧 **1.0x**，10/11pt 差 1px，判据不降 1.5 倍率门槛）、`MAIN_TITLE_ICON` light **478→550（+72）** / dark **3733→3820（+87）**、`RESET_ICON_NOT_RUN=settings-content-blank` 两档 —— 由此 **BACKLOG 587（MAIN_TITLE_ICON runner 未签收）结案**。R494 主跑 `40895877246 ↔ 590ead8` **failure 仅 `STEP[9] Release script tests`**（日志全 `UNKNOWN STEP`，原文读：sources 格主笔跑未派生 ×2 + skip roster 嵌套无汇总行，`Ran 683 / FAILED 3`）；R494 补记跑 `40896245079 ↔ e05b13c` **failure 仅 `STEP[19] Motion coverage floor`**（`MOTION_FLOOR_FACTS judged=5/5 executed=77 reds=1`，红 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`；Swift 1310/79/0 绿、`MAIN_TITLE_ICON` 1x 已在上表签收）。R493 跑 `40887758385 ↔ 67cb683` **failure 2 步**：`STEP[9] Release script tests` = 3 条非产品红（sources 格 ×2 + skip roster），`STEP[15] Swift tests` = `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 1 条（1309/79/1；`RESET_ICON_NOT_RUN=settings-content-blank` 两档）。旧跑按 `ci_read.py steps` 成对复核失败步名：R492 主跑 = STEP[9]+STEP[19]、补记跑 = STEP[19]；R491 主跑 = STEP[9]+STEP[19]、补记跑 success；R490/R489 主跑 = STEP[9]、补记跑 success；R488 主跑 = STEP[9]+STEP[19]、补记跑 success；R487 success；R486 主跑 = STEP[9]、补记跑 success；R485 4 步、R484 3 步、R483 1 步、R481 1 步、R480 无跑、R478 主跑 3 步/补记跑 success、R477 主跑 4 步/补记跑 2 步、R479 3 步。最新跑 `40922562716 ↔ 2e7828f` 读时 **in_progress ⇒ NOT-RUN**。436 沿用 R481 跑 `judged=5/5 executed=77 reds=0`。收口 push 与 R496 自身跑见补记。
- **U-1936：① 腐烂与预检。** `HIDDEN_ARMS 表=364 可判=1108 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=277 covered=254 arms=682 bad=0`（新表 `mutate_r496_quickpick_highlight` 登记）、`ARM_TOTAL files=370 arms=1169`。本轮只动 `QuickPickController` 的标题赋值（新表针就在新代码里），旧表针无一腐烂、无需重锚；QuickPick 既有六条判据（来源理由 ×2、typed 行数、overlay、内容徽标、收藏星标）单跑 **6/6 通过**。
- **U-1937：② 产品：浮层候选行补搜索命中高亮。** 缺陷形状（`quickpick-typed` 直看）：主列表与侧栏命中时都给匹配片段加底色（R456 的 `HistoryRowMatchHighlight`），浮层同一查询只过滤不高亮 —— 来源命中时这行的全部理由就是「来自 访达」，而这两个字没有任何标记。修法：新增 `QuickPickTitlePresentation`（复用 `MatchHighlighting.spans` 与 `DetailTypography.highlightColor`），**只在命中段非空时**把标题写成 `attributedStringValue`（空查询帧逐字节不变）；捕获缝 `titleHighlightEnabled`（产品默认 true，负向帧置 false）。旧/新：**2 张旧帧变化**（`quickpick-typed` 亮暗）、**2 张新帧**（`quickpick-typed-no-highlight` 亮暗）、0 缺失；基线 **322→324**；逐张看过：两行「访达」都上黄底、标题/时间/图标几何未动、负向帧无黄底。
- **U-1938：③ 判据与刀。** 新判据 `testQuickPickTypedRowsHighlightTheMatchedReason` 读标题带黄度像素：`QUICKPICK_MATCH_HIGHLIGHT` light 正臂 **头 0 / 尾 2115**、负臂 **0/0**（标题墨 6348/6345）；dark 正臂 **头 0 / 尾 2148**、负臂 **0/0**（8103/7078）（2x）。判据要求：正臂头段（x<200pt）≤40·s²、尾段 ≥200·s²、负臂黄底必须 0；任一臂标题墨为 0 ⇒ `QUICKPICK_MATCH_HIGHLIGHT_NOT_RUN=quickpick-blank`。刀 `M1339`（高亮开关反了：正臂不画/负臂画）/`M1340`（整行标题都高亮、不按命中段）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。**教训**：M1339 第一版改产品默认 `titleHighlightEnabled=false` 时**逃刀** —— 夹具显式把开关设回 true，读数量根本没变；改成正向臂不设缝（`highlight: Bool? = nil`，只有负向臂写 false）后才咬。
- **U-1939：④ 既有面。** QuickPick 来源理由/内容徽标/收藏/overlay/行数六条单跑全绿；**空查询帧零变化**（attributed 只在命中段非空时走），`quickpick-hover/list/search-focus/search-hover` 逐字节不变；标题的时间列、来源图标、图钉/星标/内容徽标叠层几何未动。**BACKLOG 587 结案**（R495 跑 1x 签收 +72/+87）；`RESET_ICON` runner 仍 `settings-content-blank`；`SETTINGS_HELPER_FONT` runner 1x 具名 NOT_RUN（新开 591）。
- **U-1940：⑤ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh` arm64 冷编 + x86_64）；捕获卷 **324 帧**、`CHANGED=2 ADDED=2 MISSING=0`，更新后 `324/0/0/0`；全量 **1312/56/1** —— 唯一红 `PerfBudgetTests.testImageComparisonCostStaysBounded` 306.4ms>250（`LOCAL_PERF_BUDGET_FLAKE=load`），**单跑原样重跑通过**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 495，`python3 scripts/product_streak.py --streak-for 495`，last=9e72947）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。收口 push 与 R496 自身跑状态见补记。**具名 NOT-RUN**：① R496 自身跑（推送后取）；② `QUICKPICK_MATCH_HIGHLIGHT` runner 1x；③ `SETTINGS_HELPER_FONT` runner 1x/2x（scale-too-low）；④ `RESET_ICON` runner（settings-content-blank）；⑤ `LOGIN_FAILURE_ICON` 1x（no-red-channel）；⑥ `DEFAULT_BADGE`（settings-content-blank）；⑦ 其余 runner 复核（R495 跑外的旧面）；⑧ 已知性能/采样 flake（本跑 PerfBudget 306.4ms）；⑨ 437–592 的其余未结项仍开。

"""
IS=u"""## Round 493 · R496（第 495 轮 · 2026-10-30）：浮层候选行补搜索命中高亮（2 旧帧 + 2 新帧、基线 324）

主列表/侧栏命中会给匹配片段加黄底，浮层同一查询只过滤不高亮——来源命中时「来自 访达」是这行唯一的理由，却无任何标记。新增 `QuickPickTitlePresentation`（复用 `MatchHighlighting.spans` + `DetailTypography.highlightColor`），只在命中段非空时走 attributed；捕获缝 `titleHighlightEnabled`（默认 true，负向帧 false）。2 张旧帧变化 + 2 张新帧，基线 322→324；`QUICKPICK_MATCH_HIGHLIGHT` 正臂头 0/尾 2115（light）、0/2148（dark），负臂 0/0；M1339/M1340 2/2。预检 277/254/682、rot 364/1108、ARM 370/1169。全量 1312/56/1（PerfBudget 306.4ms 本机 flake，单跑过）；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push `bbfe31c..2e7828f` success、ahead=0；R495 跑 success（1311/80/0；MAIN_TITLE_ICON 1x 签收 +72/+87 ⇒ 587 结案）；R494 主跑 Release 3 条、补记跑 Motion 1 条；R493 跑 2 步红。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张旧帧 + 2 张新帧逐张看过：两行「访达」黄底、几何未动、负向无黄底。 |
| 判据有效性 | 15/15 | 正臂尾黄 2115/2148、头 0；负臂 0；M1339/M1340 2/2。 |
| 假绿防御 | 14/15 | 负臂必须 0、头段必须干净、空帧有具名 NOT_RUN；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（浮层命中高亮）；1 个产品文件；2 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1935…U-1940、D-492、324 帧/1312、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 全量唯一红按性能 flake 具名并单跑复验；SETTINGS_HELPER_FONT 1x 具名 NOT_RUN；587 结案。 |
| 可复核性 | 15/15 | 2115/2148、0/0、M1339/M1340、precheck 277/254/682、基线 324 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-492 浮层候选行补搜索命中高亮；只在命中段非空时改 attributed（R496）

- 背景：主列表与侧栏命中时给匹配片段加底色，浮层同一查询只过滤不高亮；来源命中时「来自 访达」是这行唯一理由，却无标记。
- 决定：新增 `QuickPickTitlePresentation`（复用 `MatchHighlighting.spans` 与 `DetailTypography.highlightColor`）；只在命中段非空时写 `attributedStringValue`，空查询保持 `stringValue`（帧逐字节不变）；捕获缝 `titleHighlightEnabled`（产品默认 true）。
- 理由：同一查询在三种列表里应当给同一个答案；只改有命中的行，避免全局改色（第一版无条件 attributed 让 10 张空查询帧全变）。
- 兼容性/迁移：2 张旧帧变化 + 2 张新帧，基线 322→324；既有 stringValue 读取者（来源理由判据）不受影响。
- 边界：runner 1x 的黄底像素地板未读（本地 2x）；SETTINGS_HELPER_FONT 在 runner 1x 仍不可判。
- 回滚：删 `QuickPickTitlePresentation`、恢复 `stringValue`、删缝/新帧/判据/两刀，基线回 322。
"""
CS=u"""### 浮层候选行补搜索命中高亮（2 张旧帧变化 + 2 张新帧、基线 324）（R496 / 第 495 轮 / Round 493 / U-1935…U-1940 · 产品 1 文件 + 判据）

"""
BS=u"""**591. SETTINGS_HELPER_FONT 在 runner 1x 不可判**（R496 现读）
    现象：R495 跑 `40920092629` success，但该判据 `SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` 两档（runner 设置帧 1.0x，10/11pt 差 1px）。
    修法：若要在 runner 判，需换结构量（如 helper 行数/折行位置）或要求 ≥2x 捕获；**不许**把 1.5 倍率门槛降下来。

**592. QUICKPICK_MATCH_HIGHLIGHT 的 runner 1x 黄底像素地板未读**（R496 观察）
    现象：本机 2x 正臂尾黄 2115/2148、负臂 0；runner 1x 跑尚未创建（R496 自身跑 in_progress）。
    修法：下一跑读该通道；1x 尾黄若低于 200·s²，先查 1x 下黄底是否落墨，不降地板。

**587 结案**（R496）：R495 跑 `40920092629 ↔ bbfe31c` success 里 `MAIN_TITLE_ICON` light 478→550（+72）、dark 3733→3820（+87），1x 签收。
"""
SS=u"""## R496 状态（2026-10-30 · 本地 · 第 495 轮 / Round 493）：浮层候选行补搜索命中高亮（2 张旧帧变化 + 2 张新帧、基线 324）；全量 1312/56/1（唯一红 PerfBudget 本机 flake，单跑过）（产品 1 文件 + 判据）

最后更新：2026-10-30（本地 · R496 / 第 495 轮 / Round 493）：主列表与侧栏命中时给匹配片段加底色，浮层同一查询只过滤不高亮 —— 来源命中时「来自 访达」是这行唯一的理由，却没有任何标记。修法：新增 `QuickPickTitlePresentation`（复用 `MatchHighlighting.spans` 与 `DetailTypography.highlightColor`）；**只在命中段非空时**写 `attributedStringValue`（空查询帧逐字节不变）；捕获缝 `titleHighlightEnabled`（产品默认 true，负向帧 false）。旧/新：**2 张旧帧变化**（`quickpick-typed` 亮暗）、**2 张新帧**（`quickpick-typed-no-highlight` 亮暗）、0 缺失；基线 **322→324**；逐张看过：两行「访达」都上黄底、标题/时间/图标几何未动、负向帧无黄底。读数（`QUICKPICK_MATCH_HIGHLIGHT`，2x）：light 正臂 **头 0 / 尾 2115**、负臂 **0/0**（墨 6348/6345）；dark 正臂 **头 0 / 尾 2148**、负臂 **0/0**（8103/7078）。判据：头 ≤40·s²、尾 ≥200·s²、负臂黄底 0；标题墨 0 ⇒ 具名 NOT_RUN。`M1339`（开关反了）/`M1340`（整行都高亮）**2/2**；M1339 第一版被夹具显式 true 抵消而逃刀，改成正向臂不设缝后才咬。预检 **277/254/682 bad=0**、ARM **370/1169**、HIDDEN **364/1108 rot=0**；QuickPick 既有六条单跑 6/6。⓪：开工一次快进 push **`bbfe31c..2e7828f` success**、HEAD=origin/main=`2e7828f`、**ahead=0**；**R495 跑 `40920092629 ↔ bbfe31c` success**（`1311/80 skip/0`；`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` 两档、`MAIN_TITLE_ICON` light 478→550 / dark 3733→3820 **1x 签收 ⇒ BACKLOG 587 结案**、`RESET_ICON_NOT_RUN=settings-content-blank` 两档）；R494 主跑 `40895877246 ↔ 590ead8` failure 仅 Release（3 条非产品红）、补记跑 `40896245079 ↔ e05b13c` failure 仅 Motion（`testCopyReceiptAppearsAndDismissesWithAVisibleProcess`，Swift 1310/79/0 绿）；R493 跑 `40887758385 ↔ 67cb683` failure 2 步（Release 3 条 + Swift `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 1 条）；旧跑成对复核；最新跑 `40922562716 ↔ 2e7828f` **in_progress ⇒ NOT-RUN**；收口 push 见补记。全量 **1312/56/1**（860.6s；唯一红 `PerfBudgetTests.testImageComparisonCostStaysBounded` 306.4ms>250 = `LOCAL_PERF_BUDGET_FLAKE=load`，**单跑原样重跑通过**）；捕获卷 **324 帧**；基线 **324/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 495，`python3 scripts/product_streak.py --streak-for 495`，last=9e72947）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `bbfe31c..2e7828f` success、ahead=0；R495 跑 success 并签收 MAIN_TITLE_ICON 1x（587 结案）；R494/R493/旧跑失败步名复核。
② 产品：浮层候选行补搜索命中高亮（2 旧帧 + 2 新帧、基线 324）。
③ 判据：正臂尾黄 2115/2148、负臂 0；M1339/M1340 2/2。
④ 预检 277/254/682；rot 364/1108；ARM 370/1169。
⑤ 捕获 324 帧；基线 324/0/0/0；build 0 告警；换装 ok/397=397；全量 1312/56/1（PerfBudget 本机 flake，单跑过）。

NOT-RUN / 阻塞（分开写）：① R496 自身跑（推送后取）；② QUICKPICK_MATCH_HIGHLIGHT runner 1x；③ SETTINGS_HELPER_FONT runner 1x/2x（scale-too-low）；④ RESET_ICON runner（settings-content-blank）；⑤ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑥ DEFAULT_BADGE（settings-content-blank）；⑦ 其余 runner 复核；⑧ 已知性能/采样 flake（本跑 PerfBudget 306.4ms）；⑨ 437–592 的其余未结项仍开。

下一轮（R497）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（R496 主笔提交后 ahead=1 起）；成对读 R496 自身跑（推送后才有）、R495 跑 `40920092629`、R494 两跑（`40895877246`/`40896245079`）、R493 跑 `40887758385`、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `QUICKPICK_MATCH_HIGHLIGHT`（头 ≤40·s²、尾 ≥200·s²、负臂 0、1x/2x）、`SETTINGS_HELPER_FONT`（正臂极差 ≤0.6、负臂 ≥0.8、1x/2x）、`MAIN_TITLE_ICON`（1x 已签收）、`RESET_ICON`、`LOGIN_FAILURE_ICON`（no-red-channel）、`DEFAULT_BADGE`（settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层候选行搜索命中高亮/设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R496（浮层命中高亮位）**：主列表/侧栏命中加黄底，浮层同一查询只过滤不高亮——来源命中时「来自 访达」是唯一理由却无标记。新增 `QuickPickTitlePresentation`（复用 spans + highlightColor），只在命中段非空时走 attributed；缝 `titleHighlightEnabled`（默认 true）。**2 张旧帧 + 2 张新帧**，基线 **322→324**；`QUICKPICK_MATCH_HIGHLIGHT` 正臂尾黄 2115/2148、头 0，负臂 0/0；M1339/M1340 2/2。⓪ push `bbfe31c..2e7828f` success、ahead=0；R495 跑 success（1311/80/0；MAIN_TITLE_ICON 1x 签收 +72/+87 ⇒ 587 结案）；R494 主跑 Release 3 条、补记跑 Motion 1 条；R493 跑 2 步红。全量 1312/56/1（PerfBudget 306.4ms 本机 flake，单跑过）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 495 轮（R496" in a: raise SystemExit("A")
if u"## Round 493 · R496" in i: raise SystemExit("I")
if u"## D-492" in d: raise SystemExit("D")
if u"浮层候选行补搜索命中高亮" in c: raise SystemExit("C")
if u"**591." in b: raise SystemExit("B")
if st.count(u"## R495 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1934（R495 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R495 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R495 状态",SS+u"## R495 状态",1))
p2=p.replace(U,u"U-31 … U-1940（R496 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R495 节 ②",u"AGENT_STATE.md` 的 R496 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
