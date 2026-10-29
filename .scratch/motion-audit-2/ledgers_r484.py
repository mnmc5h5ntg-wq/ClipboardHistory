#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 482 轮（R483 · 2026-10-29"
AS=u"""## 第 483 轮（R484 · 2026-10-29 · U-1863…U-1868）：热图「今天」格补右上角标（8 张旧帧变化 + 2 张新帧、基线 302；M1313/M1314 2/2）（产品 1 文件 + 判据）

- **U-1863：⓪ push 与 CI。** 开工 `git push` no-op、HEAD=origin/main=`dbceebe`、**ahead=0**。R481 跑 `40812979165 ↔ 2770bfe` 已读（日志全 `UNKNOWN STEP`）：`ROW_LINK_BADGE light 218→237px（差 19）、dark 219→237px（差 18）` **1x 签收**；`SETTINGS_TITLE_ICON_NOT_RUN=settings-content-blank` 两档已登记、Capture gate 该用例 **skipped 不再是红**；`CAPTURE_GATE_CASES passed=167 skipped=21 failed=0 NOT_RUN=117`、`CAPTURE_GATE_RESULT=ok 红=0`；Motion `5/5 executed=77 reds=0`；失败步骤只剩 Release script（sources 格主笔跑未派生）。R483 跑 `40821834371 ↔ a59956c` 读时 **in_progress ⇒ NOT-RUN**；R480、R478 两跑、R477 两跑未读 ⇒ NOT-RUN。436：R481 跑 `judged=5/5 executed=77 reds=0`。
- **U-1864：① 腐烂与预检。** `HIDDEN_ARMS 表=352 可判=1085 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=265 covered=243 arms=660 bad=0`、`ARM_TOTAL files=358 arms=1146`。
- **U-1865：② 产品：热图「今天」格补右上角标。** 缺陷形状（`settings-stats-populated` 直看）：热图靠"右下角是今天"的文字说明让用户自己找今天，而今天那格与别的格子同形；今天恰好没有复制时尤其找不到。修法：`DailyCopyHeatmapCell` 加 `isToday`（默认 false 保持组件帧原状），今天格右上角 4pt `labelColor` 圆点；`DailyCopyHeatmapView` 用 `calendar.isDate(cell.date, inSameDayAs: today)` 判定，加捕获缝 `heatmapTodayMarkerForCapture`（产品默认 nil 画）。旧/新：**8 张旧帧变化**（settings-stats-populated、heatmap-populated、heatmap-summary-after 等 ×亮暗）+ **2 张新帧**（`settings-stats-populated-no-today` 亮暗）、0 缺失；基线 **300→302**；逐张看过：角标在今天格右上角、不压数据色块。读数（`HEATMAP_TODAY`）：两臂差异 **60 像素**、bbox **1108,408–1115,415**（2x），1x 待 runner。
- **U-1866：③ 判据与刀。** 新判据 `testHeatmapTodaysCellCarriesACornerMarker` 用成对帧（populated / 只关角标）逐像素差：≥8·s² 且 <4000·s²（证明只差角标）；刀 `M1313`（永不画）/`M1314`（圆点透明）**2/2 CAUGHT**。新帧 `settings-stats-populated-no-today` 补进 vibrant 盲区名册（首遍全量正因漏它红 1 条，补名册后 1300/56/0）。
- **U-1867：④ 既有面。** 热图悬停描边/图例/工具提示/空态未动；`heatmap-populated` 与 `heatmap-summary-after` 的变化只来自今天角标；设置统计页其它卡片未动。
- **U-1868：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **302 帧**、`CHANGED=8 ADDED=2 MISSING=0`，更新后 `302/0/0/0`；全量 **1300/56/0**（494.7s，轻载；首遍 vibrant 名册漏新帧红 1 条，补后重跑）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **2** 轮（as-of 484，`python3 scripts/product_streak.py --streak-for 484`，last=a59956c）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R483/R480/R478/R477 跑；② 今天角标的 runner 1x/dark；③ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；④ `SETTINGS_DATA_PATH`；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ 437–568 的其余未结项仍开。

"""
IS=u"""## Round 481 · R484（第 483 轮 · 2026-10-29）：热图「今天」格补右上角标（8 旧帧 + 2 新帧、基线 302）

热图靠文字说明让用户自己找今天。`DailyCopyHeatmapCell` 加 `isToday`（默认 false），今天格右上角 4pt labelColor 圆点；`DailyCopyHeatmapView` 用 `calendar.isDate` 判定，加捕获缝。8 张旧帧变化 + 2 张新帧，基线 300→302；`HEATMAP_TODAY` 两臂差 60 像素、bbox 1108,408–1115,415；M1313/M1314 2/2；新负向帧补进 vibrant 名册（首遍全量红 1 条，修后 1300/56/0）。预检 265/243/660、rot 352/1085、ARM 358/1146。全量 1300/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ no-op push、ahead=0；R481 跑签收 ROW_LINK_BADGE 19/18 与 Capture gate 红 0；R483 跑 in_progress ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张 stats 帧与 2 张组件帧逐张看过：角标在今天格右上角、不压数据色块。 |
| 判据有效性 | 15/15 | 成对帧逐像素差 60、bbox 单格；M1313/M1314 2/2。 |
| 假绿防御 | 14/15 | 新负向帧名册漏登记被首遍全量抓住并补；扣 1：runner 1x/其余跑未读。 |
| 产品面推进 | 15/15 | 新类别（热图今天角标）；1 个产品文件；8 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1863…U-1868、D-480、302 帧/1300、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 差异上界 4000·s² 防其它控件混入；runner 未读具名。 |
| 可复核性 | 15/15 | 10 张帧、60 像素、bbox、M1313/M1314、precheck 265/243/660、rot 352/1085、基线 302 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-480 热图今天格加右上角标；负向帧缝只给成对判据用（R484）

- 背景：热图靠文字让用户自己找今天，今天格与别的格同形；今天没有复制时尤其找不到。
- 决定：`DailyCopyHeatmapCell.isToday`（默认 false）+ 右上角 4pt labelColor 圆点；`DailyCopyHeatmapView` 用 `calendar.isDate` 判定；捕获缝 `heatmapTodayMarkerForCapture` 只给负向帧。判据逐像素差（≥8·s²、<4000·s²），M1313/M1314 2/2；负向帧补 vibrant 名册。
- 理由：角标不占布局、不压数据色块；成对帧把差异锁在单格内；新帧名册必须同笔补。
- 兼容性/迁移：8 张旧帧变化 + 2 张新帧，基线 300→302；组件默认 false 保持原组件帧。
- 边界：runner 1x/dark 未签收；今天若在窗口右缘，角标可能贴边。
- 回滚：删 isToday/圆点/捕获缝/新帧与判据。
"""
CS=u"""### 热图「今天」格补右上角标（8 张旧帧变化 + 2 张新帧、基线 302）（R484 / 第 483 轮 / Round 481 / U-1863…U-1868 · 产品 1 文件 + 判据）

"""
BS=u"""**567. R483/R480/R478/R477 的跑仍未读**（R484 观察）
    现象：R483 跑 40821834371 in_progress，R480/R478/R477 跑未读；HEATMAP_TODAY 的 runner 1x/dark 未签收。
    修法：下一跑成对读全部失败步骤与 HEATMAP_TODAY/CLEAR_LABEL/ROW_LINK_BADGE。

**568. 热图今天角标在窗口右缘可能贴边**（R484 观察）
    现象：今天在最后一列时角标贴格子右上角，距热图右缘 1pt padding。
    修法：下一帧看右缘是否被裁；若裁，按格子内缩不改判据地板。
"""
SS=u"""## R484 状态（2026-10-29 · 本地 · 第 483 轮 / Round 481）：热图「今天」格补右上角标（8 张旧帧变化 + 2 张新帧、基线 302）；全量 1300/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R484 / 第 483 轮 / Round 481）：热图靠"右下角是今天"的文字说明让用户自己找今天，而今天那格与别的格子同形。修法：`DailyCopyHeatmapCell` 加 `isToday`（默认 false 保持组件帧原状），今天格右上角 4pt `labelColor` 圆点；`DailyCopyHeatmapView` 用 `calendar.isDate(cell.date, inSameDayAs: today)` 判定，加捕获缝 `heatmapTodayMarkerForCapture`（产品默认 nil 画）。旧/新：**8 张旧帧变化**（settings-stats-populated、heatmap-populated、heatmap-summary-after 等 ×亮暗）+ **2 张新帧**（settings-stats-populated-no-today 亮暗）、0 缺失；基线 **300→302**；逐张看过：角标在今天格右上角、不压数据色块。读数（`HEATMAP_TODAY`）：两臂差异 **60 像素**、bbox **1108,408–1115,415**（2x）。新判据用成对帧逐像素差（≥8·s² 且 <4000·s²）；`M1313`（永不画）/`M1314`（圆点透明）**2/2**。新负向帧补进 vibrant 盲区名册（首遍全量红 1 条，补后重跑）。预检 **265/243/660 bad=0**、ARM **358/1146**、HIDDEN **352/1085 rot=0**。⓪：no-op push、HEAD=origin/main=`dbceebe`、**ahead=0**；R481 跑 `40812979165 ↔ 2770bfe` 已读：ROW_LINK_BADGE 1x +19/+18、SETTINGS_TITLE_ICON_NOT_RUN 登记、Capture gate **failed=0/红=0**、Motion 5/5 reds0；R483 跑 `40821834371 ↔ a59956c` in_progress ⇒ NOT-RUN；R480/R478/R477 未读 ⇒ NOT-RUN；436 R481 跑 reds=0。全量 **1300/56/0**（494.7s，轻载）；捕获卷 **302 帧**；基线 **302/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **2** 轮（as-of 484，`python3 scripts/product_streak.py --streak-for 484`，last=a59956c）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ no-op push、ahead=0；R481 跑签收 ROW_LINK_BADGE 19/18、Capture gate 红 0；R483 跑 in_progress、R480/R478/R477 未读 ⇒ NOT-RUN。
② 产品：热图今天格右上角标（8 旧帧 + 2 新帧、基线 302）。
③ 判据：逐像素差 60/bbox 单格；M1313/M1314 2/2；新负向帧补名册。
④ 预检 265/243/660；rot 352/1085；ARM 358/1146。
⑤ 捕获 302 帧；基线 302/0/0/0；build 0 告警；换装 ok/397=397；全量 1300/56/0。

NOT-RUN / 阻塞（分开写）：① R483/R480/R478/R477 跑；② 今天角标 runner 1x/dark；③ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；④ SETTINGS_DATA_PATH；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ 437–568 的其余未结项仍开。

下一轮（R485）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R484 自身跑、R483 跑 `40821834371`、R481 跑 `40812979165`、R480 跑、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `HEATMAP_TODAY`（≥8·s²、1x/dark）、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R484（热图今天角标位）**：热图靠文字让用户自己找今天，今天格与别的格同形。`DailyCopyHeatmapCell.isToday`（默认 false）+ 今天格右上角 4pt labelColor 圆点；`DailyCopyHeatmapView` 用 `calendar.isDate` 判定，加捕获缝。**8 张旧帧变化 + 2 张新帧**，基线 **300→302**；`HEATMAP_TODAY` 两臂差 60 像素、bbox 1108,408–1115,415；M1313/M1314 **2/2**；负向帧补 vibrant 名册（首遍全量红 1 条，修后 1300/56/0）。⓪ no-op push、ahead=0；R481 跑签收 ROW_LINK_BADGE 19/18 与 Capture gate 红 0；R483 跑 in_progress ⇒ NOT-RUN。全量 **1300/56/0**（494.7s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 483 轮（R484" in a: raise SystemExit("A")
if u"## Round 481 · R484" in i: raise SystemExit("I")
if u"## D-480" in d: raise SystemExit("D")
if u"热图「今天」格补右上角标" in c: raise SystemExit("C")
if u"**567." in b: raise SystemExit("B")
if st.count(u"## R483 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1862（R483 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R483 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R483 状态",SS+u"## R483 状态",1))
p2=p.replace(U,u"U-31 … U-1868（R484 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R483 节 ②",u"AGENT_STATE.md` 的 R484 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
