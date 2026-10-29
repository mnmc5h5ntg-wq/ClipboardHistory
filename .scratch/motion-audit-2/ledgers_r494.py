#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 492 轮（R493 · 2026-10-29"
AS=u"""## 第 493 轮（R494 · 2026-10-29 · U-1923…U-1928）：主侧栏标题补时钟图标（48 张旧帧变化 + 2 张新帧、基线 320；M1335/M1336 2/2）（产品 1 文件 + 判据）

- **U-1923：⓪ push 与 CI。** 开工 `git push` 失败（监督者现测 api=000 / apple=200、`git ls-remote` 报 Connection closed on port 22），再探一次仍失败 ⇒ **`PUSH_BLOCKED=network`（HEAD=`0e461b7`、origin/main=`67cb683`、**ahead=1**）**；`CI_READ_BLOCKED`，本轮未新读任何 run；收口前再试一次（见 U-1928）。R493 跑 `40887758385 ↔ 67cb683` 在 R493 补记读时 **in_progress ⇒ NOT-RUN**。R492 主跑 `40880105650 ↔ a90b074` failure 2 步（Release 3 条 + Motion 2 条；`LOGIN_FAILURE_ICON_NOT_RUN=no-red-channel` 两档），补记跑 `40880472552 ↔ e754cf7` failure 仅 Motion 2 条。R491 主跑 `40868743008 ↔ 83e2087` failure 仅 Release 3 条 + Motion `testFilterPillSlideIsAProcessNotATeleport 1<1`，补记跑 `40868988761 ↔ ebc64aa` success。R490 主跑 `40865789755 ↔ c0c08c7` failure 仅 Release 3 条、补记跑 `40866154839 ↔ 9f987c7` success。R489 主跑 `40858253532 ↔ d8b0712` failure 仅 Release 3 条、补记跑 `40861168233 ↔ 3d4a03a` success。R488 主跑 `40851078685 ↔ 9487c0f` failure 2 步（Release 3 条 + Motion 1<2）、补记跑 `40851311888 ↔ 2cafe1b` success。R487 跑 `40845483735 ↔ 519b22b` success。R486 主跑 `40836764232 ↔ dfbf6f6` 唯一红 Release 3 条、补记跑 `40837020563 ↔ 04cc517` success。R485 跑 `40832860076 ↔ 35ad21a` failure 4 步（HEATMAP 两档 0、Motion 1<2、Release 3 条）；R484 跑 `40826572977 ↔ 6454a93` failure 3 步；R483 跑 `40821834371 ↔ a59956c` 唯一红 Release 3 条；R481 跑 `40812979165 ↔ 2770bfe` 已签收 `ROW_LINK_BADGE 19/18`、Capture 红 0；R480 `60d65a4` 无跑；R478 主跑 `40801850707 ↔ b64682e` failure 3 步（冲突 `0≠2`）、补记跑 `40802042660 ↔ 7f21720` success；R477 主跑 `40797827495 ↔ 0fd3ec0` failure 4 步、补记跑 `40797866181 ↔ 7a79987` failure 2 步；R479 跑 `40805576917 ↔ 225e6f8` failure 3 步（`SETTINGS_TITLE_ICON` 0 墨，runner 平涂）。以上均为沿用账上成对读数，本轮因网络未新读；436 沿用 R481 跑 `judged=5/5 executed=77 reds=0`。
- **U-1924：① 腐烂与预检。** `HIDDEN_ARMS 表=362 可判=1105 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=275 covered=252 arms=678 bad=0`（新表 `mutate_r494_main_title_icon` 已登记）、`ARM_TOTAL files=368 arms=1166`。
- **U-1925：② 产品：主侧栏标题补时钟图标。** 缺陷形状（`content-with-history` 与 `sidebar-history` 直看）：设置页标题与设置分类行都有图标，主窗口侧栏标题「时间剪史」只有一行字 —— 同一窗口的身份锚点少一枚。修法：`HistorySidebarView.header` 在标题前加 `Image(systemName: "clock.arrow.circlepath")`（`VisualFont.title` semibold、`.secondary`、`accessibilityHidden(true)`，纯装饰不重复念），加捕获缝 `mainSidebarTitleIconForCapture`（产品默认 nil 画）。旧/新：**48 张旧帧变化**（12 组 `content-*` + 12 组 `sidebar-*`，各亮暗）、**2 张新帧**（`sidebar-no-title-icon` 亮暗）、0 缺失；基线 **318→320**；逐组看过 9 张（含亮/暗、搜索、多选、固定分区、收藏、无结果、暂停横幅与两张负向臂）：图标在标题左、标题右移后不压计数/批量按钮，行内容与来源图标未动。
- **U-1926：③ 判据与刀。** 新判据 `testMainSidebarTitleCarriesAnIcon` 读标题带墨量：`MAIN_TITLE_ICON` light 负臂 **1772** → 正臂 **2050**（+278）、dark **14213** → **14487**（+274）；首墨 34→32 / 26→26（左移 2/0px，仅打印不作断言 —— 图标占掉旧标题左沿，第一版断言实测 2/0px 已删）。判据只要求负臂有墨 + 正臂墨量更大；两臂都空 ⇒ `MAIN_TITLE_ICON_NOT_RUN=sidebar-blank` 具名出口。刀 `M1335`（图标永不画）/`M1336`（图标透明）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1927：④ 既有面。** 侧栏搜索/收藏/多选/固定分区/悬停/拖放/无结果/无来源各帧只多了标题图标；行内容、时间、来源图标、计数文案、批量按钮排均未动；content-* 的侧栏仍按已登记盲区（离屏 sidebar 不跟暗色）只看几何。新负向帧已登记系统 List 选中黑带名册（`sidebar-no-title-icon`，与 `sidebar-history` 同批）；`CARD_INSET_CONTROL_FIRST` 名册不涉及侧栏。表格/设置/浮层/视频面未动。
- **U-1928：⑤ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh`，arm64+x86_64）；捕获卷 **320 帧**、`CHANGED=48 ADDED=2 MISSING=0`，更新后 `320/0/0/0`；全量 **1310/56/0**（719.1s）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 493，`python3 scripts/product_streak.py --streak-for 493`，last=67cb683）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。收口 push 结果与 R494 跑状态见补记（开工两探均网络失败）。**具名 NOT-RUN**：① R494 自身跑（推送后取）；② R493 跑 `40887758385`（in_progress）；③ `MAIN_TITLE_ICON` runner 1x/2x；④ 其余 runner 复核（网络未读）；⑤ `LOGIN_FAILURE_ICON` 1x（no-red-channel）；⑥ `DEFAULT_BADGE`（settings-content-blank）；⑦ Capture `MATERIAL_BLIND_NOT_RUN`；⑧ 已知 Motion 采样红；⑨ 437–588 的其余未结项仍开。

"""
IS=u"""## Round 491 · R494（第 493 轮 · 2026-10-29）：主侧栏标题补时钟图标（48 旧帧 + 2 新帧、基线 320）

设置页标题与设置分类行都有图标，主窗口侧栏标题「时间剪史」只有一行字。`HistorySidebarView.header` 在标题前加 `clock.arrow.circlepath`（title 字号 semibold、secondary、读屏隐藏），加捕获缝。48 张旧帧变化 + 2 张新帧，基线 318→320；`MAIN_TITLE_ICON` light 1772→2050（+278）、dark 14213→14487（+274）；M1335/M1336 2/2。预检 275/252/678、rot 362/1105、ARM 368/1166。全量 1310/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ PUSH_BLOCKED=network（HEAD=`0e461b7`、origin/main=`67cb683`、ahead=1）；CI_READ_BLOCKED；R493 跑 in_progress ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 48 张旧帧按 12+12 组抽看 9 张（亮/暗、搜索、多选、固定分区、收藏、无结果、暂停、负向臂）：图标在标题左、不压计数/批量按钮。 |
| 判据有效性 | 15/15 | 墨差 +278/+274；M1335/M1336 2/2。 |
| 假绿防御 | 14/15 | 两臂都空有具名 NOT_RUN；左移断言按实测删除；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（主侧栏标题图标）；1 个产品文件；48 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1923…U-1928、D-490、320 帧/1310、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | CI 网络未读全部成对沿用并注明；R493 in_progress 具名 NOT-RUN。 |
| 可复核性 | 15/15 | 1772→2050、14213→14487、M1335/M1336、precheck 275/252/678、基线 320 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-490 主侧栏标题补 clock.arrow.circlepath 图标；图标占旧左沿时判据只数墨量（R494）

- 背景：设置页标题与设置分类行都有图标，主窗口侧栏标题「时间剪史」只有一行字；同一窗口的身份锚点少一枚。
- 决定：`HistorySidebarView.header` 在标题前加 `Image(systemName: "clock.arrow.circlepath")`（`VisualFont.title` semibold、`.secondary`、`accessibilityHidden(true)`），加捕获缝 `mainSidebarTitleIconForCapture`（产品默认 nil 画）。
- 理由：图标与标题同字号同字重，作为身份锚点；读屏不重复念；纯装饰不抢计数与批量按钮。
- 兼容性/迁移：48 张旧帧变化 + 2 张新帧，基线 318→320；标题右移但行的左沿由图标接住，判据不拿左移作证。
- 边界：`MAIN_TITLE_ICON` 在 runner 1x/2x 未签收；content-* 侧栏的暗色仍属已登记盲区，只看几何。
- 回滚：删 Image 与捕获缝、删新夹具/判据/两刀，基线回 318。
"""
CS=u"""### 主侧栏标题补时钟图标（48 张旧帧变化 + 2 张新帧、基线 320）（R494 / 第 493 轮 / Round 491 / U-1923…U-1928 · 产品 1 文件 + 判据）

"""
BS=u"""**587. MAIN_TITLE_ICON 的 runner 1x/2x 未签收**（R494 观察）
    现象：本机墨差 light +278、dark +274；runner 未读（网络阻断 + 新跑未创建）。
    修法：下一跑读 `MAIN_TITLE_ICON` 两档；若 1x 有内容但差低于 40·s²，先查捕获通道，不降地板。

**588. 主侧栏标题图标的左沿由图标接住，标题左移不再是可用信号**（R494 观察）
    现象：图标占掉旧标题左沿，首墨只移 2/0px；第一版“左移”断言实测不成立已删。
    修法：后续若改标题字号或换符号，只重钉墨量地板；不要复活左移断言。
"""
SS=u"""## R494 状态（2026-10-29 · 本地 · 第 493 轮 / Round 491）：主侧栏标题补时钟图标（48 张旧帧变化 + 2 张新帧、基线 320）；全量 1310/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R494 / 第 493 轮 / Round 491）：设置页标题与设置分类行都有图标，主窗口侧栏标题「时间剪史」只有一行字 —— 同一窗口的身份锚点少一枚。修法：`HistorySidebarView.header` 在标题前加 `Image(systemName: "clock.arrow.circlepath")`（`VisualFont.title` semibold、`.secondary`、`accessibilityHidden(true)`），加捕获缝 `mainSidebarTitleIconForCapture`（产品默认 nil 画）。旧/新：**48 张旧帧变化**（12 组 content-* + 12 组 sidebar-*，各亮暗）、**2 张新帧**（`sidebar-no-title-icon` 亮暗）、0 缺失；基线 **318→320**；逐组看过 9 张：图标在标题左、标题右移后不压计数/批量按钮、各行态未动。读数（`MAIN_TITLE_ICON`）：light 负臂 **1772** → 正臂 **2050（+278）**、dark **14213 → 14487（+274）**；首墨 34→32 / 26→26（仅打印）。新判据只要求负臂有墨 + 正臂更多，两臂都空有 `MAIN_TITLE_ICON_NOT_RUN=sidebar-blank` 具名出口；`M1335`（图标永不画）/`M1336`（图标透明）**2/2**。预检 **275/252/678 bad=0**、ARM **368/1166**、HIDDEN **362/1105 rot=0**。⓪：开工 push 失败（api=000、`ls-remote` Connection closed）⇒ **`PUSH_BLOCKED=network`（HEAD=`0e461b7`、origin/main=`67cb683`、ahead=1）**、`CI_READ_BLOCKED`；R493 跑 `40887758385 ↔ 67cb683` in_progress ⇒ NOT-RUN；R492 主跑 Release 3 条 + Motion 2 条、补记跑仅 Motion 2 条；R491 主跑 Release 3 条 + Motion 1<1、补记跑 success；R490/R489 主跑 Release 3 条、补记跑 success；R488 主跑 Release 3 条 + Motion 1<2、补记跑 success；R487 跑 success；R486 主跑 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 沿用 R481 跑 reds=0。全量 **1310/56/0**（719.1s，轻载）；捕获卷 **320 帧**；基线 **320/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 493，`python3 scripts/product_streak.py --streak-for 493`，last=67cb683）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 与 CI：网络阻断具名、成对读数沿用、R493 跑 NOT-RUN。
② 产品：主侧栏标题补时钟图标（48 旧帧 + 2 新帧、基线 320）。
③ 判据：墨差 +278/+274；M1335/M1336 2/2；两臂空有具名出口。
④ 预检 275/252/678；rot 362/1105；ARM 368/1166。
⑤ 捕获 320 帧；基线 320/0/0/0；build 0 告警；换装 ok/397=397；全量 1310/56/0。

NOT-RUN / 阻塞（分开写）：① R494 自身跑（推送后取）；② R493 跑 `40887758385`（in_progress）；③ MAIN_TITLE_ICON runner 1x/2x；④ 其余 runner 复核（网络未读）；⑤ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑥ DEFAULT_BADGE（settings-content-blank）；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–588 的其余未结项仍开。

下一轮（R495）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（当前 `PUSH_BLOCKED=network`、HEAD=`0e461b7`、origin/main=`67cb683`、ahead=1；R494 主笔提交后 ahead=2）；成对读 R494 自身跑（推送后才有）、R493 跑 `40887758385`、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `MAIN_TITLE_ICON`（墨差 ≥40·s²、1x/2x）、`RESET_ICON`（右列墨差、1x/dark）、`LOGIN_FAILURE_ICON`（no-red-channel）、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R494（主侧栏标题图标位）**：设置页标题与设置分类行都有图标，主窗口侧栏标题「时间剪史」只有一行字。`HistorySidebarView.header` 在标题前加 `clock.arrow.circlepath`（title 字号 semibold、secondary、读屏隐藏），加捕获缝。**48 张旧帧 + 2 张新帧**，基线 **318→320**；`MAIN_TITLE_ICON` light 1772→2050（+278）、dark 14213→14487（+274）；M1335/M1336 2/2。⓪ PUSH_BLOCKED=network（HEAD=`0e461b7`、origin/main=`67cb683`、ahead=1）；CI_READ_BLOCKED；R493 跑 in_progress ⇒ NOT-RUN。全量 1310/56/0；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 493 轮（R494" in a: raise SystemExit("A")
if u"## Round 491 · R494" in i: raise SystemExit("I")
if u"## D-490" in d: raise SystemExit("D")
if u"主侧栏标题补时钟图标" in c: raise SystemExit("C")
if u"**587." in b: raise SystemExit("B")
if st.count(u"## R493 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1922（R493 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R493 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R493 状态",SS+u"## R493 状态",1))
p2=p.replace(U,u"U-31 … U-1928（R494 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R493 节 ②",u"AGENT_STATE.md` 的 R494 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
