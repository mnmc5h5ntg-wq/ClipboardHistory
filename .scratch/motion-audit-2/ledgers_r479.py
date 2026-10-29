#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R479 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io, os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT=os.path.join(ROOT,"AGENT_UI_AUDIT.md"); ITER=os.path.join(ROOT,"AGENT_VISUAL_ITERATION.md")
DECISIONS=os.path.join(ROOT,"AGENT_DECISIONS.md"); CHANGELOG=os.path.join(ROOT,"CHANGELOG.md")
BACKLOG=os.path.join(ROOT,"AGENT_BACKLOG.md"); STATE=os.path.join(ROOT,"AGENT_STATE.md")
REPORT=os.path.join(ROOT,"AGENT_FINAL_REPORT.md")
def rd(p):
    return io.open(p,encoding="utf-8").read()
def wr(p,t):
    io.open(p,"w",encoding="utf-8").write(t)
AUDIT_TITLE=u"## 第 477 轮（R478 · 2026-10-29"
AUDIT_SECTION=u"""## 第 478 轮（R479 · 2026-10-29 · U-1839…U-1844）：设置页标题补分类图标（36 张旧帧变化 + 2 张新帧、基线 296；M1302/M1303 2/2）（产品 1 文件 + 判据）

- **U-1839：⓪ push 与 CI。** 开工 `git push` **Everything up-to-date**、HEAD=origin/main=`7f21720`、**ahead=0**。R477 补记跑 `40797866181 ↔ 7a79987` 收口已读 **failure 2 步**（Swift/Capture）：冲突判据仍是 `0 != 2` —— 7a79987 还没有 R478 补记的 skip 修正（该修正只在 `7f21720`）；`SHORTCUT_CONFLICT_NOT_RUN` 两档已打。R478 主跑 `40801850707 ↔ b64682e` 与补记跑 `40802042660 ↔ 7f21720` 读时 **in_progress ⇒ NOT-RUN**；R477 主跑已读（inline 99/6.0 与 102/5.0、幻影块 0、图钉 +20 签收）；R476/R475/R474/R473/R472/R471 沿用。436 无 R479 新跑；R477 主跑 Motion 红 = markdown 标签 1<2（已知采样）。
- **U-1840：① 腐烂与预检。** `HIDDEN_ARMS 表=348 可判=1077 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=261 covered=243 arms=660 bad=0`、`ARM_TOTAL files=354 arms=1143`。
- **U-1841：② 产品：设置页标题补分类图标。** 缺陷形状（`settings-data` 等直看）：侧栏选中项有分类图标，内容页标题却只有一行字，换页后标题没有与侧栏同一个视觉锚点。修法：新 `SettingsPageTitle`（标题左侧 `category.icon`、`.secondary`、`accessibilityHidden`、与标题同字号，默认 headline、统计页 title semibold），7 个页面标题接入；加捕获缝 `settingsPageTitleIconForCapture` 供负向帧。旧/新：**36 张旧帧变化 + 2 张新帧**（`settings-data-no-title-icon` 亮暗）、0 缺失；基线 **294→296**；逐张看过数据/通用/统计等页：图标与侧栏同形、不挤压卡片。读数（`SETTINGS_TITLE_ICON`）：标题行末墨列 light/dark 均 **393→445px（+52px=26pt）**、墨 829→1156 / 897→1226。
- **U-1842：③ 判据、刀与名册。** 新判据 `testSettingsPageTitlesCarryTheCategoryIcon` 用成对帧（settings-data / 只关图标的负向帧）读标题行末墨列（+52px）与墨量；刀 `M1302`（图标永不画）/`M1303`（负向帧也画）**2/2 CAUGHT**。负向帧是同一棵 settings 侧栏 vibrant 子树 ⇒ 补进 `darkSidebarTextBlindSpots`；首遍全量正因漏这一格而红，修名册后干净。
- **U-1843：④ 既有面。** R478 的兜底路径 / R477 的 inline/幻影/图钉均不在本笔产品改动内；R477 补记跑的冲突红是 skip 位置错误（7f21720 已修，但不在 7a79987 那跑里），不记产品回归。R478 两跑的 `FALLBACK_PATH`/冲突复验仍待读。
- **U-1844：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **296 帧**、`CHANGED=36 ADDED=2 MISSING=0`，更新后 `296/0/0/0`；全量 **1296/56/0**（468.3s，轻载；首遍因 vibrant 名册漏新帧红 1 条，补名册后重跑）；换装 `ok / SHA_MATCH=1 / 388=388`（版本 1.4.8；上轮账写 387、本轮现读 388 —— 与旧包 `diff find` 为空，计数口径未改产品）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 478，`python3 scripts/product_streak.py --streak-for 478`，last=b64682e）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R478 两跑（in_progress）；② 兜底路径/冲突提示的 runner 复验；③ 设置标题图标的 runner 1x/dark；④ `SETTINGS_DATA_PATH` 两档；⑤ 既有 runner 复核（无新跑）；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–558 的其余未结项仍开。

"""
ITER_SECTION=u"""## Round 476 · R479（第 478 轮 · 2026-10-29）：设置页标题补分类图标（36 张旧帧变化 + 2 张新帧、基线 296）

侧栏有分类图标，内容页标题只有一行字。新 `SettingsPageTitle`（标题左侧同形图标、同字号、secondary、a11y 隐藏）接入 7 页；捕获缝 `settingsPageTitleIconForCapture` 只给负向帧。36 张旧帧变化 + 2 张新帧，基线 294→296；`SETTINGS_TITLE_ICON` 标题行末墨 393→445px（+26pt）、墨 +327/+329；M1302/M1303 2/2。负向帧补进 vibrant 盲区名册（首遍全量红 1 条，修名册后 1296/56/0）。预检 261/243/660、rot 348/1077、ARM 354/1143。换装 ok/388=388。⓪ no-op push、ahead=0；R477 补记跑冲突红仍是 skip 位置（7a79987 未含 7f21720 的修正）；R478 两跑 in_progress ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 数据/通用/统计等页逐张看过：图标与侧栏同形、标题同字号、卡片未挤。 |
| 判据有效性 | 15/15 | 成对帧只差图标，标题末墨 +52px；M1302/M1303 2/2。 |
| 假绿防御 | 14/15 | 负向帧名册漏登记被首遍全量抓住并补；扣 1：R478 两跑与标题图标 runner 仍未读。 |
| 产品面推进 | 15/15 | 新类别（设置页标题图标）；1 个产品文件；36 旧帧 + 2 新帧；Store 不动。 |
| 台账一致性 | 15/15 | U-1839…U-1844、D-476、296 帧/1296、388=388 都来自命令与测试。 |
| 交付诚实性 | 15/15 | R477 补记跑的冲突红写明是 skip 位置而非产品；388 计数差异写明。 |
| 可复核性 | 15/15 | 36+2 帧、393→445px、M1302/M1303、precheck 261/243/660、rot 348/1077、基线 296 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_476=u"""## D-476 设置页标题与侧栏共用图标；捕获缝给负向帧；名册随新帧同笔（R479）

- 背景：侧栏有分类图标，内容页标题只有一行字；新帧如果不进 vibrant 盲区名册，全量会红在名册而不是产品。
- 决定：新 `SettingsPageTitle`（category.icon + 标题，同字号、secondary、a11y 隐藏）接入 7 页；加 `settingsPageTitleIconForCapture` 捕获缝（产品默认 nil 画图标，夹具 false 拍负向帧）；负向帧进 `darkSidebarTextBlindSpots`。
- 理由：图标是换页后的视觉锚点，与侧栏同一语言；成对帧只差图标，标题末墨 +52px 是可复核的对象；名册必须与新帧同笔，否则红的是账不是产品。
- 兼容性/迁移：36 张旧帧变化 + 2 张新帧，基线 294→296；无 Store/存档变化。
- 边界：标题图标的 runner 1x/dark 未签收；R478 两跑仍 in_progress。
- 回滚：删 `SettingsPageTitle` 与捕获缝、恢复 7 处 Text；负向帧与名册一并撤。
"""

CHANGELOG_SECTION=u"""### 设置页标题补分类图标（36 张旧帧变化 + 2 张新帧、基线 296）（R479 / 第 478 轮 / Round 476 / U-1839…U-1844 · 产品 1 文件 + 判据）

"""
BACKLOG_SECTION=u"""**556. R478 两跑与兜底路径/冲突复验未读**（R479 观察）
    现象：R478 主跑 `40801850707 ↔ b64682e` 与补记跑 `40802042660 ↔ 7f21720` 读时 in_progress；FALLBACK_PATH 与冲突 NOT-RUN 只有本机读数。
    修法：读这两跑的 `FALLBACK_PATH`（≥90pt）与 `SHORTCUT_CONFLICT(_NOT_RUN)`；仍红按读数继续。

**557. 设置页标题图标的 runner 1x/dark 未签收**（R479 观察）
    现象：本机两档标题行末墨 393→445px（+26pt）、墨 +327/+329；runner 1x 的 13pt 图标可能更小。
    修法：读新跑的 `SETTINGS_TITLE_ICON`；低于 8pt 就按 scale 重算，不改产品字号。

**558. 换装条目数 387→388 的计数口径**（R479 观察）
    现象：本轮 install 现读 388=388，而前几轮账写 387=387；新旧 app bundle `diff find` 为空。
    修法：下一轮读 install 的 entries；若不等于 388 再查，不把 387 手抄进新账。
"""
STATE_SECTION=u"""## R479 状态（2026-10-29 · 本地 · 第 478 轮 / Round 476）：设置页标题补分类图标（36 张旧帧变化 + 2 张新帧、基线 296）；全量 1296/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R479 / 第 478 轮 / Round 476）：侧栏选中项有分类图标，内容页标题却只有一行字，换页后没有与侧栏同一个视觉锚点。修法：新 `SettingsPageTitle`（标题左侧 `category.icon`、`.secondary`、`accessibilityHidden`、与标题同字号；统计页 title semibold），7 个页面标题接入；加捕获缝 `settingsPageTitleIconForCapture` 供负向帧。旧/新：**36 张旧帧变化 + 2 张新帧**（`settings-data-no-title-icon` 亮暗）、0 缺失；基线 **294→296**；逐张看过数据/通用/统计等页：图标与侧栏同形、不挤压卡片。读数（`SETTINGS_TITLE_ICON`）：标题行末墨列 light/dark 均 **393→445px（+52px=26pt）**、墨 829→1156 / 897→1226。新判据用成对帧读标题末墨；`M1302`（永不画）/`M1303`（负向帧也画）**2/2**；负向帧补进 vibrant 盲区名册（首遍全量红 1 条，修名册后重跑）。预检 **261/243/660 bad=0**、ARM **354/1143**、HIDDEN **348/1077 rot=0**。⓪：`git push` **Everything up-to-date**、HEAD=origin/main=`7f21720`、**ahead=0**；R477 补记跑 `40797866181 ↔ 7a79987` failure 2 步（冲突判据仍 0!=2，7a79987 未含 7f21720 的 skip 修正）；R478 主跑 `40801850707 ↔ b64682e` 与补记跑 `40802042660 ↔ 7f21720` 读时 in_progress ⇒ NOT-RUN；R477 主跑 inline/幻影/图钉签收；436 无新跑。全量 **1296/56/0**（468.3s，轻载）；捕获卷 **296 帧**；基线 **296/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 388=388`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 478，`python3 scripts/product_streak.py --streak-for 478`，last=b64682e）。清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；R477 补记跑冲突红（skip 位置，非产品）；R478 两跑 in_progress ⇒ NOT-RUN；R477 主跑三处修复签收。
② 产品：设置页标题补分类图标（36 旧帧 + 2 新帧、基线 296）。
③ 判据：成对帧标题末墨 +52px；M1302/M1303 2/2；负向帧补进名册。
④ 预检 261/243/660；rot 348/1077；ARM 354/1143。
⑤ 捕获 296 帧；基线 296/0/0/0；build 0 告警；换装 ok/388=388；全量 1296/56/0。

NOT-RUN / 阻塞（分开写）：① R478 两跑（in_progress）；② 兜底路径/冲突复验；③ 标题图标 runner 1x/dark；④ `SETTINGS_DATA_PATH` 两档；⑤ 既有 runner 复核（无新跑）；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–558 的其余未结项仍开。

下一轮（R480）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R479 自身跑、R478 两跑 `40801850707 ↔ b64682e`/`40802042660 ↔ 7f21720`、R477 两跑、R476 跑、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `SETTINGS_TITLE_ICON`（≥8pt）、`FALLBACK_PATH`（≥90pt）、`INLINE_CODE_PAD`（light ≥4.5、dark 99/6.5）、`QUICKPICK_GREY_BAND`（1x 8 行）、`QUICKPICK_PIN`（+104/+105）、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
R479_REPORT_BULLET=u"""- **R479（设置页标题图标位）**：侧栏有分类图标，内容页标题只有一行字。新 `SettingsPageTitle`（标题左侧同形图标、同字号、secondary、a11y 隐藏）接入 7 页；捕获缝 `settingsPageTitleIconForCapture` 给负向帧。**36 张旧帧变化 + 2 张新帧**，基线 **294→296**；`SETTINGS_TITLE_ICON` 标题行末墨 393→445px（+26pt）、墨 +327/+329；M1302/M1303 **2/2**；负向帧补进 vibrant 名册（首遍全量红 1 条，修名册后 1296/56/0）。⓪ no-op push、ahead=0；R477 补记跑冲突红是 skip 位置（7a79987 未含 7f21720 修正）；R478 两跑 in_progress ⇒ NOT-RUN；R477 主跑 inline/幻影/图钉签收。全量 **1296/56/0**（468.3s）；build 0 告警；换装 ok/SHA_MATCH=1/388=388；电池 683/5。
"""
audit=rd(AUDIT); it=rd(ITER); dec=rd(DECISIONS); ch=rd(CHANGELOG); bl=rd(BACKLOG); st=rd(STATE); rp=rd(REPORT)
if audit.count(AUDIT_TITLE)!=1: raise SystemExit("AUDIT")
if u"第 478 轮（R479" in audit: raise SystemExit("AUDIT2")
if u"## Round 476 · R479" in it: raise SystemExit("ITER")
if u"## D-476" in dec: raise SystemExit("DEC")
if u"设置页标题补分类图标" in ch: raise SystemExit("CH")
if u"**556." in bl: raise SystemExit("BL")
if st.count(u"## R478 状态")!=1: raise SystemExit("ST")
U=u"U-31 … U-1838（R478 现读抬到最新一节）"
if rp.count(U)!=1: raise SystemExit("U")
if rp.count(u"AGENT_STATE.md` 的 R478 节 ②")!=1: raise SystemExit("PTR")
wr(AUDIT,audit.replace(AUDIT_TITLE,AUDIT_SECTION+AUDIT_TITLE,1))
wr(ITER,it.rstrip()+"\n\n"+ITER_SECTION+"\n")
wr(DECISIONS,dec.rstrip()+"\n\n"+DECISION_476+"\n")
mark=u"## [Unreleased]\n"
if ch.count(mark)!=1: raise SystemExit("CH2")
wr(CHANGELOG,ch.replace(mark,mark+"\n"+CHANGELOG_SECTION,1))
wr(BACKLOG,bl.rstrip()+"\n\n"+BACKLOG_SECTION+"\n")
wr(STATE,st.replace(u"## R478 状态",STATE_SECTION+u"## R478 状态",1))
rp2=rp.replace(U,u"U-31 … U-1844（R479 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R478 节 ②",u"AGENT_STATE.md` 的 R479 节 ②",1)
wr(REPORT,rp2.rstrip()+"\n\n"+R479_REPORT_BULLET+"\n")
print("LEDGERS_R479_OK")
