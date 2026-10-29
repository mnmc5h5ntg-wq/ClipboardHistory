#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 488 轮（R489 · 2026-10-29"
AS=u"""## 第 489 轮（R490 · 2026-10-29 · U-1899…U-1904）：主列表来源行补来源 App 图标（70 张旧帧变化、基线 310；M1325/M1326 2/2）（产品 1 文件 + 判据）

- **U-1899：⓪ push 与 CI。** 开工一次快进 push **`d8b0712..3d4a03a` success**、HEAD=origin/main=`3d4a03a`、**ahead=0**。R489 主跑 `40858253532 ↔ d8b0712` 读时 **in_progress**、补记跑 `40861168233 ↔ 3d4a03a` **queued ⇒ NOT-RUN**。R488 主跑 `40851078685 ↔ 9487c0f` failure 2 步（Release 3 条非产品 + Motion 已知 1<2）已读，Swift/Capture 全绿，`TABLE_COLUMNS` 1x 制表位=2、第二列 [122,123,123] 极差 1px、第三列 [161,161,161] 极差 0；R488 补记跑 `40851311888 ↔ 2cafe1b` success。R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。
- **U-1900：① 腐烂与预检。** `HIDDEN_ARMS 表=358 可判=1097 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=271 covered=248 arms=670 bad=0`（新表登记）、`ARM_TOTAL files=364 arms=1158`。**重锚 R444 M1220**：来源行拆视图后旧针失效，改成把 `name` 置空（行退回纯时间），与 M1221 一起重跑 **2/2**、RESTORE_CLEAN=yes。
- **U-1901：② 产品：主列表来源行补来源 App 图标。** 缺陷形状（`sidebar-history` 直看）：详情头部与浮层都有来源 App 图标，主列表只有「来自 X」文字 —— 同一信息在三种表面有三种形态。修法：`RowTextColumn` 把时间与来源拆开排，在「 · 来自 」后补 `SourceAppIconProvider` 的 11pt 图标，来源名仍走搜索高亮；macOS 13+ 用 `ViewThatFits`：放得下才带图标，250pt 最小窗退回无图标分支，来源名不能被挤没；macOS 12 走无图标分支。旧/新：**70 张旧帧变化**（sidebar-history、sidebar-search-source、row-*、content-* 等）、0 新增/缺失；基线 **310/0/0/0**；逐张看过：300pt 源名带图标、250pt 无图标但源名保留、标题/时间轴未动。
- **U-1902：③ 判据与刀。** 新判据 `testMainListSourceRowsCarryTheSourceAppIcon` 读文字列**彩色像素**（缩略图列作彩色通道对照；无来源负臂必须彩色=0）：`HISTORY_SOURCE_ICON` light 负臂 0→正臂 **807**、dark **789**，缩略图对照 680（2x）。刀 `M1325`（图标永不画）/`M1326`（无来源也画一个蓝图标）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。第一版两刀都逃了：判据把“两臂都 0”当通道缺席静默 skip、且负臂没断言 0；补彩色对照与负臂 0 后两刀才红。
- **U-1903：④ 既有面。** 标题/时间轴、来源搜索高亮、OCR/富文本/链接徽标、行高与缩略图列均未动；250pt 最小窗改由 `ViewThatFits` 走无图标分支（来源名优先）。源码态/表格共享路径本轮未动，宽表/表头沿用 R488 读数。
- **U-1904：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **310 帧**、`CHANGED=70 ADDED=0 MISSING=0`，复验 `310/0/0/0`；全量 **1306/56/0**（489.3s，轻载；重锚 R444 后重跑）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 489，`python3 scripts/product_streak.py --streak-for 489`，last=d8b0712）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R490 自身跑（提交后取）；② `HISTORY_SOURCE_ICON` 的 runner 1x/dark；③ R489 两跑（in_progress/queued）；④ `DEFAULT_BADGE`/`TABLE_COLUMNS`/`TABLE_PIPES` 的 1x 已签收；⑤ `DATA_ACTION_ICONS`/`HEATMAP_TODAY` 1x 出口已签收；⑥ `QUICKPICK_FAVORITE` 1x 已签收；⑦ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑧ `SETTINGS_DATA_PATH`；⑨ 既有 runner 复核；⑩ Capture MATERIAL_BLIND_NOT_RUN；⑪ 已知 Motion 采样红；⑫ 437–580 的其余未结项仍开。

"""
IS=u"""## Round 487 · R490（第 489 轮 · 2026-10-29）：主列表来源行补来源 App 图标（70 旧帧、基线 310）

详情/浮层都有来源图标，主列表只有「来自 X」文字。`RowTextColumn` 拆时间与来源，在「 · 来自 」后补 11pt App 图标，来源名仍走搜索高亮；macOS 13+ 用 `ViewThatFits`，250pt 最小窗退回无图标分支、来源名不被挤没；macOS 12 走无图标。70 张旧帧变化、基线 310 不变；`HISTORY_SOURCE_ICON` light 负臂 0→807、dark 789，缩略图彩色对照 680；M1325/M1326 2/2；R444 M1220 重锚后 2/2（name 置空）。第一版两刀被静默 skip 逃过，补彩色对照与负臂 0 才红。预检 271/248/670、rot 358/1097、ARM 364/1158。全量 1306/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push d8b0712..3d4a03a success、ahead=0；R489 两跑 in_progress/queued ⇒ NOT-RUN；R488 主跑 Release+Motion 已知、补记跑 success。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 300pt 与 250pt 两档逐张看过：源名带图标 / 最小窗无图标但源名保留，标题/时间轴未动。 |
| 判据有效性 | 15/15 | 彩色像素 807/789、缩略图对照 680、负臂必须 0；M1325/M1326 2/2。 |
| 假绿防御 | 14/15 | 第一版两刀都因“两臂 0 静默 skip”逃过，补对照/负臂 0 后重跑才红；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（主列表来源图标）；1 个产品文件；70 旧帧变化。 |
| 台账一致性 | 15/15 | U-1899…U-1904、D-486、310 帧/1306、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 250pt 回归（图标挤没源名）在本轮内被 ViewThatFits 修掉；runner 结论原样登记。 |
| 可复核性 | 15/15 | 807/789、对照 680、负臂 0、M1325/M1326、重锚 M1220、precheck 271/248/670、基线 310 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-486 主列表来源行补 App 图标；窄窗用 ViewThatFits 让源名优先（R490）

- 背景：详情头部与浮层都有来源 App 图标，主列表只有「来自 X」文字 —— 同一信息在三种表面有三种形态。
- 决定：`RowTextColumn` 拆时间与来源，在「 · 来自 」后补 `SourceAppIconProvider` 的 11pt 图标，来源名仍走搜索高亮；macOS 13+ 用 `ViewThatFits`（带图标 / 无图标两档），250pt 最小窗退回无图标分支，源名不被挤没；macOS 12 走无图标分支。
- 理由：来源图标是「来自 X」的视觉锚点；窄窗里源名比图标重要，不能用图标换掉文字。首版固定加图标，250pt 实测源名被挤到 0，本轮内改掉。
- 兼容性/迁移：70 张旧帧变化，基线 310 不变；标题/时间轴/行高/缩略图列未动。
- 边界：runner 1x/dark 未读；彩色通道用缩略图列作对照，负臂无来源必须彩色=0。
- 回滚：删来源图标与 ViewThatFits，恢复单段 `HistoryRowMatchHighlight.sourceLine` 文本。
"""
CS=u"""### 主列表来源行补来源 App 图标（70 张旧帧变化、基线 310）（R490 / 第 489 轮 / Round 487 / U-1899…U-1904 · 产品 1 文件 + 判据）

"""
BS=u"""**579. HISTORY_SOURCE_ICON 的 runner 1x/dark 未签收**（R490 观察）
    现象：本机 2x 正臂彩色 807/789、缩略图对照 680、负臂 0；runner 1x 未读。
    修法：下一跑读 `HISTORY_SOURCE_ICON` 两档；若 1x 彩色差低于 40·s²，先查捕获通道，不降地板。

**580. 来源图标只在 macOS 13+ 的 ViewThatFits 里出现，macOS 12 永远无图标**（R490 观察）
    现象：macOS 12 走无图标分支（源名优先），没有图标可看；本机与 runner 都不是 12。
    修法：若要在 12 上也有图标，需要按行宽阈值而不是 ViewThatFits；先不加判据、不声称已解决。
"""
SS=u"""## R490 状态（2026-10-29 · 本地 · 第 489 轮 / Round 487）：主列表来源行补来源 App 图标（70 张旧帧变化、基线 310）；全量 1306/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R490 / 第 489 轮 / Round 487）：详情头部与浮层都有来源 App 图标，主列表只有「来自 X」文字 —— 同一信息在三种表面有三种形态。修法：`RowTextColumn` 拆时间与来源，在「 · 来自 」后补 `SourceAppIconProvider` 的 11pt 图标，来源名仍走搜索高亮；macOS 13+ 用 `ViewThatFits`（带图标 / 无图标两档），250pt 最小窗退回无图标分支、来源名不被挤没；macOS 12 走无图标分支。旧/新：**70 张旧帧变化**、0 新增/缺失；基线 **310/0/0/0**；逐张看过：300pt 源名带图标、250pt 无图标但源名保留、标题/时间轴未动。读数（`HISTORY_SOURCE_ICON`，2x）：light 负臂 0→正臂 **807**、dark **789**，缩略图彩色对照 **680**、负臂必须 0。新判据读文字列彩色像素；`M1325`（图标永不画）/`M1326`（无来源也画蓝图标）**2/2**。第一版两刀都因“两臂都 0 静默 skip”逃过，补彩色对照与负臂 0 后才红。**重锚 R444 M1220**：来源行拆视图后旧针失效，改成把 `name` 置空，与 M1221 重跑 **2/2**。预检 **271/248/670 bad=0**、ARM **364/1158**、HIDDEN **358/1097 rot=0**。⓪：一次快进 push **`d8b0712..3d4a03a` success**、HEAD=origin/main=`3d4a03a`、**ahead=0**；R489 主跑 `40858253532 ↔ d8b0712` in_progress、补记跑 `40861168233 ↔ 3d4a03a` queued ⇒ NOT-RUN；R488 主跑 failure 2 步（Release 3 条非产品 + Motion 已知 1<2）、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1306/56/0**（489.3s，轻载；重锚 R444 后重跑）；捕获卷 **310 帧**；基线 **310/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 489，`python3 scripts/product_streak.py --streak-for 489`，last=d8b0712）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push d8b0712..3d4a03a success、ahead=0；R489 两跑 NOT-RUN；R488 主跑 Release+Motion 已知、补记跑 success。
② 产品：主列表来源行补来源图标（70 旧帧、基线 310）；250pt 用 ViewThatFits 保源名。
③ 判据：彩色 807/789、对照 680、负臂 0；M1325/M1326 2/2；重锚 R444 M1220。
④ 预检 271/248/670；rot 358/1097；ARM 364/1158。
⑤ 捕获 310 帧；基线 310/0/0/0；build 0 告警；换装 ok/397=397；全量 1306/56/0。

NOT-RUN / 阻塞（分开写）：① R490 自身跑（提交后取）；② HISTORY_SOURCE_ICON runner 1x/dark；③ R489 两跑（in_progress/queued）；④ DEFAULT_BADGE/TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑤ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑥ QUICKPICK_FAVORITE 1x 已签收；⑦ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑧ SETTINGS_DATA_PATH；⑨ 既有 runner 复核；⑩ Capture MATERIAL_BLIND_NOT_RUN；⑪ 已知 Motion 采样红；⑫ 437–580 的其余未结项仍开。

下一轮（R491）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R490 自身跑、R489 两跑 `40858253532`/`40861168233`、R488 两跑 `40851078685`/`40851311888`、R487 跑 `40845483735`、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2）；**重点读 `HISTORY_SOURCE_ICON`（彩色 ≥40·s²、负臂=0、1x/dark）、`DEFAULT_BADGE`（1x 未读）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R490（主列表来源图标位）**：详情/浮层都有来源图标，主列表只有「来自 X」文字。`RowTextColumn` 拆时间与来源，在「 · 来自 」后补 11pt App 图标，来源名仍走搜索高亮；macOS 13+ 用 `ViewThatFits`，250pt 最小窗退回无图标分支、源名不被挤没。**70 张旧帧变化、基线 310 不变**；`HISTORY_SOURCE_ICON` light 负臂 0→807、dark 789，缩略图对照 680、负臂必须 0；M1325/M1326 2/2；R444 M1220 重锚后 2/2。第一版两刀被静默 skip 逃过，补对照/负臂 0 才红。⓪ push d8b0712..3d4a03a success、ahead=0；R489 两跑 NOT-RUN；R488 主跑 Release+Motion 已知、补记跑 success。全量 **1306/56/0**（489.3s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 489 轮（R490" in a: raise SystemExit("A")
if u"## Round 487 · R490" in i: raise SystemExit("I")
if u"## D-486" in d: raise SystemExit("D")
if u"主列表来源行补来源 App 图标" in c: raise SystemExit("C")
if u"**579." in b: raise SystemExit("B")
if st.count(u"## R489 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1898（R489 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R489 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R489 状态",SS+u"## R489 状态",1))
p2=p.replace(U,u"U-31 … U-1904（R490 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R489 节 ②",u"AGENT_STATE.md` 的 R490 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
