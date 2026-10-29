#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 490 轮（R491 · 2026-10-29"
AS=u"""## 第 491 轮（R492 · 2026-10-29 · U-1911…U-1916）：开机启动失败回执补错误图标（2 张旧帧变化 + 2 张新帧、基线 316；M1329/M1330 2/2）（产品 1 文件 + 判据）

- **U-1911：⓪ push 与 CI。** `git push` no-op（Everything up-to-date）、HEAD=origin/main=`ebc64aa`、**ahead=0**。R490 主跑 `40865789755 ↔ c0c08c7` **failure 仅 Release script 3 条非产品**；Swift/Capture/Motion 全绿，`HISTORY_SOURCE_ICON` 1x **light 负臂 0/正臂 187/缩略图 170、dark 0/165/170** 签收；`DEFAULT_BADGE_NOT_RUN=settings-content-blank` 两档、种子守卫 NOT_RUN。R490 补记跑 `40866154839 ↔ 9f987c7` **success**。R491 主跑 `40868743008 ↔ 83e2087` 与补记跑（ebc64aa）读时仍 **in_progress ⇒ NOT-RUN**；R489 主跑唯一红是 Release 3 条非产品、补记跑 success；R488 主跑 Release 3 条 + Motion 已知 1<2、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。
- **U-1912：① 腐烂与预检。** `HIDDEN_ARMS 表=360 可判=1101 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=273 covered=250 arms=674 bad=0`（新表登记）、`ARM_TOTAL files=366 arms=1162`。**重锚两处旧尺**：R384 M1015 改指 `loginFailureStyle`（恒 secondary ⇒ 失败帧红=0），CAUGHT；R39 M177 改指新 HStack 回执块、**M178 改指“禁用标签也恒 primary”**（旧 `.disabled` 针已被 R396 分色取代，删了不影响被判的标签）⇒ R39 表 **8/8 CAUGHT**、RESTORE_CLEAN=yes。
- **U-1913：② 产品：开机启动失败回执补错误图标。** 缺陷形状（`settings-general-login-failed` 直看）：失败回执只有红字，而横幅/回执都带图标。修法：`if let message` 分支改成 HStack，`lastActionFailed` 时在文字左侧加 `exclamationmark.triangle.fill`（11pt，与文字同错误色）；不支持说明不加；加捕获缝 `loginFailureIconForCapture`（产品默认 nil 画）。旧/新：**2 张旧帧变化**（settings-general-login-failed 亮暗）+ **2 张新帧**（settings-general-login-failed-no-icon 亮暗）、0 缺失；基线 **314→316**；逐张看过：三角在红字左、不支持态与正常态未动。
- **U-1914：③ 判据与刀。** 新判据 `testLoginFailureReceiptCarriesAnErrorIcon` 读内容列红像素：`LOGIN_FAILURE_ICON` light 负臂 **2374→正臂 2631（+257）**、dark **2119→2366（+247）**（2x）。刀 `M1329`（图标永不画）/`M1330`（图标不是红色）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。第一版还断言“最左红像素左移”，实测 0/-1px（图标占掉的正是旧文字左沿）⇒ 删掉该断言、只数红像素。**新负向帧补进复选框首墨名册**（否则 card inset 等式误红）。
- **U-1915：④ 既有面。** 失败回执的红字、说明文字轴、不支持态/正常态、开关禁用态、卡片内缩均未动；`CARD_INSET_CONTROL_FIRST` 名册加新负向帧后恢复 +2.5/+3.0；表格/来源图标/浮层内容徽标字段未动。
- **U-1916：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **316 帧**、`CHANGED=2 ADDED=2 MISSING=0`，更新后 `316/0/0/0`；全量 **1308/56/0**（568.7s，轻载；R39/R384 重锚与名册后重跑）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 491，`python3 scripts/product_streak.py --streak-for 491`，last=83e2087）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R492 自身跑（提交后取）；② `LOGIN_FAILURE_ICON` 的 runner 1x/dark；③ R491 两跑（in_progress）；④ `QUICKPICK_CONTENT_BADGE` runner 1x/dark；⑤ `HISTORY_SOURCE_ICON` 1x 已签收；⑥ `DEFAULT_BADGE` runner 仍 NOT_RUN=settings-content-blank；⑦ `TABLE_COLUMNS`/`TABLE_PIPES` 1x 已签收；⑧ `DATA_ACTION_ICONS`/`HEATMAP_TODAY` 1x 出口已签收；⑨ `QUICKPICK_FAVORITE` 1x 已签收；⑩ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑪ `SETTINGS_DATA_PATH`；⑫ 既有 runner 复核；⑬ Capture MATERIAL_BLIND_NOT_RUN；⑭ 已知 Motion 采样红；⑮ 437–584 的其余未结项仍开。

"""
IS=u"""## Round 489 · R492（第 491 轮 · 2026-10-29）：开机启动失败回执补错误图标（2 旧帧 + 2 新帧、基线 316）

失败回执只有红字，横幅/回执都有图标。`if let message` 改 HStack：`lastActionFailed` 时在文字左侧加 11pt `exclamationmark.triangle.fill`（同错误色），不支持说明不加；加捕获缝。2 张旧帧变化 + 2 张新帧，基线 314→316；`LOGIN_FAILURE_ICON` light 2374→2631（+257）、dark 2119→2366（+247）；M1329/M1330 2/2；R384 M1015 重锚 CAUGHT；R39 表 M177/M178 重锚后 8/8。第一版“最左红像素左移”断言实测 0/-1（图标占旧文字左沿）⇒ 删掉、只数红像素。新负向帧补进复选框首墨名册。预检 273/250/674、rot 360/1101、ARM 366/1162。全量 1308/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push no-op、ahead=0；R490 主跑仅 Release 3 条 + HISTORY_SOURCE_ICON 1x 签收、补记跑 success；R491 两跑 in_progress ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张登录帧逐张看过：三角在红字左、不支持/正常态未动。 |
| 判据有效性 | 15/15 | 红像素 2374→2631/2119→2366；M1329/M1330 2/2。 |
| 假绿防御 | 14/15 | 左移断言被实测打回后删掉；R39 M178 旧刀失效已重锚并重跑；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（失败回执图标）；1 个产品文件；2 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1911…U-1916、D-488、316 帧/1308、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 旧刀失效如实重锚；新负向帧补名册；runner 结论原样登记。 |
| 可复核性 | 15/15 | 2374→2631、2119→2366、M1329/M1330、重锚 M1015/M177/M178、precheck 273/250/674、基线 316 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-488 失败回执补错误图标；红像素计数不以“最左红”作证（R492）

- 背景：开机启动失败回执只有红字，横幅/回执都带图标；同一套错误语言缺一枚图标。
- 决定：`if let message` 改 HStack，`lastActionFailed` 时在文字左侧加 11pt `exclamationmark.triangle.fill`，与文字同错误色；不支持说明不加；加捕获缝 `loginFailureIconForCapture`。
- 理由：错误状态需要图标 + 颜色双通道；图标放在文字左，不改变说明文字轴以外的布局。判据只数红像素：图标占掉的正是旧文字左沿，最左红像素不会左移。
- 兼容性/迁移：2 张旧帧变化 + 2 张新帧，基线 314→316；正常/不支持态未动；新负向帧补进复选框首墨名册。
- 边界：runner 1x/dark 未读；图标与文字同色，颜色不作独立通道。
- 回滚：删图标/捕获缝/新帧与判据，回执恢复纯 Text。
"""
CS=u"""### 开机启动失败回执补错误图标（2 张旧帧变化 + 2 张新帧、基线 316）（R492 / 第 491 轮 / Round 489 / U-1911…U-1916 · 产品 1 文件 + 判据）

"""
BS=u"""**583. LOGIN_FAILURE_ICON 的 runner 1x/dark 未签收**（R492 观察）
    现象：本机 2x 红像素 light 2374→2631（+257）、dark 2119→2366（+247）；runner 1x 未读。
    修法：下一跑读 `LOGIN_FAILURE_ICON` 两档；若 1x 红差低于 30·s²，先查红色通道，不降地板。

**584. 失败图标与文字同错误色，判据只把红像素当计数**（R492 观察）
    现象：图标占掉旧文字左沿，最左红像素不左移；颜色不作独立证人。
    修法：若要更强的图标身份，可给图标不同形状/尺寸或单独色相；先不加判据、不声称已解决。
"""
SS=u"""## R492 状态（2026-10-29 · 本地 · 第 491 轮 / Round 489）：开机启动失败回执补错误图标（2 张旧帧变化 + 2 张新帧、基线 316）；全量 1308/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R492 / 第 491 轮 / Round 489）：失败回执只有红字，而横幅/回执都带图标。修法：`if let message` 分支改成 HStack，`lastActionFailed` 时在文字左侧加 `exclamationmark.triangle.fill`（11pt，与文字同错误色）；不支持说明不加；加捕获缝 `loginFailureIconForCapture`（产品默认 nil 画）。旧/新：**2 张旧帧变化**（settings-general-login-failed 亮暗）+ **2 张新帧**（settings-general-login-failed-no-icon 亮暗）、0 缺失；基线 **314→316**；逐张看过：三角在红字左、不支持态与正常态未动。读数（`LOGIN_FAILURE_ICON`，2x）：light 红像素 **2374→2631（+257）**、dark **2119→2366（+247）**。新判据只数红像素（第一版“最左红左移”实测 0/-1px，已删）；`M1329`（图标永不画）/`M1330`（图标不是红色）**2/2**。**重锚两处旧尺**：R384 M1015 改指 `loginFailureStyle`（恒 secondary）CAUGHT；R39 M177 改指新 HStack、**M178 改指“禁用标签恒 primary”**（旧 `.disabled` 针被 R396 分色取代）⇒ R39 表 **8/8 CAUGHT**、RESTORE_CLEAN=yes。新负向帧补进复选框首墨名册，`CARD_INSET_CONTROL_FIRST` 恢复 +2.5/+3.0。预检 **273/250/674 bad=0**、ARM **366/1162**、HIDDEN **360/1101 rot=0**。⓪：push no-op、HEAD=origin/main=`ebc64aa`、**ahead=0**；R490 主跑 `40865789755 ↔ c0c08c7` failure 仅 Release 3 条非产品（HISTORY_SOURCE_ICON 1x light 0/187/170、dark 0/165/170 签收；DEFAULT_BADGE/种子守卫 NOT_RUN），补记跑 `40866154839 ↔ 9f987c7` success；R491 主跑 `40868743008 ↔ 83e2087` 与补记跑读时 in_progress ⇒ NOT-RUN；R489 主跑唯一红是 Release 3 条、补记跑 success；R488 主跑 Release 3 条 + Motion 已知 1<2、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1308/56/0**（568.7s，轻载；R39/R384 重锚后重跑）；捕获卷 **316 帧**；基线 **316/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 491，`python3 scripts/product_streak.py --streak-for 491`，last=83e2087）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R490 主跑唯一红是 Release 3 条 + HISTORY_SOURCE_ICON 1x 签收、补记跑 success；R491 两跑 in_progress ⇒ NOT-RUN。
② 产品：开机启动失败回执补错误图标（2 旧帧 + 2 新帧、基线 316）。
③ 判据：红像素 2374→2631/2119→2366；M1329/M1330 2/2；R384 M1015、R39 M177/M178 重锚。
④ 预检 273/250/674；rot 360/1101；ARM 366/1162。
⑤ 捕获 316 帧；基线 316/0/0/0；build 0 告警；换装 ok/397=397；全量 1308/56/0。

NOT-RUN / 阻塞（分开写）：① R492 自身跑（提交后取）；② LOGIN_FAILURE_ICON runner 1x/dark；③ R491 两跑（in_progress）；④ QUICKPICK_CONTENT_BADGE runner 1x/dark；⑤ HISTORY_SOURCE_ICON 1x 已签收；⑥ DEFAULT_BADGE runner 仍 NOT_RUN=settings-content-blank；⑦ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑧ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑨ QUICKPICK_FAVORITE 1x 已签收；⑩ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑪ SETTINGS_DATA_PATH；⑫ 既有 runner 复核；⑬ Capture MATERIAL_BLIND_NOT_RUN；⑭ 已知 Motion 采样红；⑮ 437–584 的其余未结项仍开。

下一轮（R493）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R492 自身跑、R491 两跑、R490 两跑 `40865789755`/`40866154839`、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2；R490 主跑唯一红是 Release 3 条）；**重点读 `LOGIN_FAILURE_ICON`（红像素差 ≥30·s²、1x/dark）、`QUICKPICK_CONTENT_BADGE`（1x/dark）、`HISTORY_SOURCE_ICON`（1x 已签收）、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R492（开机启动失败回执图标位）**：失败回执只有红字，横幅/回执都有图标。`if let message` 改 HStack，`lastActionFailed` 时在文字左侧加 11pt `exclamationmark.triangle.fill`（同错误色），不支持说明不加；加捕获缝。**2 张旧帧 + 2 张新帧**，基线 **314→316**；`LOGIN_FAILURE_ICON` light 2374→2631（+257）、dark 2119→2366（+247）；M1329/M1330 2/2；R384 M1015 重锚 CAUGHT；R39 表 M177/M178 重锚后 8/8。第一版“最左红左移”断言实测 0/-1px ⇒ 删掉、只数红像素；新负向帧补进复选框首墨名册。⓪ push no-op、ahead=0；R490 主跑仅 Release 3 条 + HISTORY_SOURCE_ICON 1x 签收、补记跑 success；R491 两跑 NOT-RUN。全量 **1308/56/0**（568.7s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 491 轮（R492" in a: raise SystemExit("A")
if u"## Round 489 · R492" in i: raise SystemExit("I")
if u"## D-488" in d: raise SystemExit("D")
if u"开机启动失败回执补错误图标" in c: raise SystemExit("C")
if u"**583." in b: raise SystemExit("B")
if st.count(u"## R491 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1910（R491 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R491 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R491 状态",SS+u"## R491 状态",1))
p2=p.replace(U,u"U-31 … U-1916（R492 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R491 节 ②",u"AGENT_STATE.md` 的 R492 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
