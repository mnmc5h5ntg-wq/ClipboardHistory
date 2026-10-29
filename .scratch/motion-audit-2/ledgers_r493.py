#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 491 轮（R492 · 2026-10-29"
AS=u"""## 第 492 轮（R493 · 2026-10-29 · U-1917…U-1922）：设置「恢复默认」按钮补图标（18 张旧帧变化 + 2 张新帧、基线 318；M1331/M1332 2/2）（产品 2 文件 + 判据）

- **U-1917：⓪ push 与 CI。** `git push` no-op（Everything up-to-date）、HEAD=origin/main=`e754cf7`、**ahead=0**。R492 主跑 `40880105650 ↔ a90b074` **failure 2 步**：Release script 3 条非产品 + Motion 已知 2 条（`testEmptyStateStillFadesWhenMotionIsReduced`、`testMarkdownModeLabelChangeIsAVisibleProcess`）；`LOGIN_FAILURE_ICON_NOT_RUN=no-red-channel` 两档。R492 补记跑 `40880472552 ↔ e754cf7` **failure 仅 Motion 2 条**（`testCopyReceiptAppearsAndDismissesWithAVisibleProcess`、`testMarkdownModeLabelChangeIsAVisibleProcess`；Release 已绿）。R491 主跑唯一红是 Release 3 条 + Motion 已知 1<1、补记跑 success；R490 主跑唯一红是 Release 3 条、补记跑 success；R489/R488/R487/R486 沿用；436 无新跑。
- **U-1918：① 腐烂与预检。** `HIDDEN_ARMS 表=361 可判=1103 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=274 covered=251 arms=676 bad=0`（新表登记）、`ARM_TOTAL files=367 arms=1164`。**重跑 MotionDriverTests 并重锚权重复位尺**：按钮从 `Button("恢复默认")` 改为 closure-label 后，`weightsResetIsAnimated` 的 `call` 与正对照改成新形状；两格通过。
- **U-1919：② 产品：「恢复默认」按钮补图标。** 缺陷形状（`settings-shortcuts` 直看）：数据页导出/导入已带图标，快捷键/推荐两处「恢复默认」仍纯文字 —— 同一设置窗口的动作图标语言分裂。修法：`HotKeySettingsRow` 与 `RecommendationWeightsView` 的按钮改用 `Label("恢复默认", systemImage: "arrow.counterclockwise")`，标签不改；加捕获缝 `settingsResetButtonIconsForCapture`（产品默认 nil 画）。旧/新：**18 张旧帧变化**（settings-shortcuts、settings-min、conflict、recording、recommendations-tall 等）、**2 张新帧**（settings-shortcuts-no-reset-icon 亮暗）、0 缺失；基线 **316→318**；逐张看过：图标在标签左、按钮未压卡片、禁用态仍可读。
- **U-1920：③ 判据与刀。** 新判据 `testShortcutResetButtonsCarryAResetIcon` 读右列墨量差：`RESET_ICON` light **3057→3507（+450）**、dark **3636→4101（+465）**（2x）。刀 `M1331`（图标永不画）/`M1332`（负臂也画）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1921：④ 既有面。** 快捷键录制/冲突/重置禁用态、推荐权重滑杆与复位动画、设置卡片几何均未动；MotionDriver 两格重锚后仍通过；表格/登录/浮层/来源图标字段未动。
- **U-1922：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **318 帧**、`CHANGED=18 ADDED=2 MISSING=0`，更新后 `318/0/0/0`；全量 **1309/56/0**（525.8s，轻载）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 492，`python3 scripts/product_streak.py --streak-for 492`，last=a90b074）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R493 自身跑（提交后取）；② `RESET_ICON` 的 runner 1x/dark；③ `LOGIN_FAILURE_ICON` 1x（no-red-channel）；④ `QUICKPICK_CONTENT_BADGE` 1x 已签收；⑤ `HISTORY_SOURCE_ICON` 1x 已签收；⑥ `DEFAULT_BADGE` runner 仍 NOT_RUN=settings-content-blank；⑦ `TABLE_COLUMNS`/`TABLE_PIPES` 1x 已签收；⑧ `DATA_ACTION_ICONS`/`HEATMAP_TODAY` 1x 出口已签收；⑨ `QUICKPICK_FAVORITE` 1x 已签收；⑩ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑪ `SETTINGS_DATA_PATH`；⑫ 既有 runner 复核；⑬ Capture MATERIAL_BLIND_NOT_RUN；⑭ 已知 Motion 采样红（本跑 2 条）；⑮ 437–586 的其余未结项仍开。

"""
IS=u"""## Round 490 · R493（第 492 轮 · 2026-10-29）：设置「恢复默认」补图标（18 旧帧 + 2 新帧、基线 318）

数据页按钮已有图标，快捷键/推荐「恢复默认」仍纯文字。两处改用 `Label("恢复默认", systemImage: "arrow.counterclockwise")`，标签不改，加捕获缝。18 张旧帧变化 + 2 张新帧，基线 316→318；`RESET_ICON` light 3057→3507（+450）、dark 3636→4101（+465）；M1331/M1332 2/2；MotionDriver 权重复位尺按 closure-label 重锚后通过。预检 274/251/676、rot 361/1103、ARM 367/1164。全量 1309/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push no-op、ahead=0；R492 两跑均 failure（主跑 Release 3 条 + Motion 2 条；补记跑仅 Motion 2 条）；LOGIN_FAILURE_ICON NOT_RUN=no-red-channel。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 18 张旧帧 + 2 张新帧逐张看过：图标在标签左、按钮未压卡片、禁用态可读。 |
| 判据有效性 | 15/15 | 右列墨差 450/465；M1331/M1332 2/2。 |
| 假绿防御 | 14/15 | 权重复位尺按新按钮形状重锚后复跑；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（恢复默认按钮图标）；2 个产品文件；18 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1917…U-1922、D-489、318 帧/1309、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | R492 两跑 2 条 Motion 已知红原样登记；LOGIN_FAILURE_ICON 具名 NOT_RUN。 |
| 可复核性 | 15/15 | 3057→3507、3636→4101、M1331/M1332、MotionDriver 重锚、precheck 274/251/676、基线 318 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-489 「恢复默认」按钮补 counterclockwise 图标；权重复位尺按 closure-label 重锚（R493）

- 背景：数据页导出/导入已带图标，快捷键/推荐两处「恢复默认」仍纯文字；同一设置窗口的动作图标语言分裂。
- 决定：两处改用 `Label("恢复默认", systemImage: "arrow.counterclockwise")`，标签不改；加捕获缝 `settingsResetButtonIconsForCapture`。
- 理由：同一动作组的图标语言要一致；图标放标签左，按钮宽度增长由布局吸收，禁用态文字仍可读。
- 兼容性/迁移：18 张旧帧变化 + 2 张新帧，基线 316→318；MotionDriver 的 `weightsResetIsAnimated` 从 `Button("恢复默认")` 改成 closure-label 的正对照，产品调用仍唯一。
- 边界：runner 1x/dark 未读。
- 回滚：两处 Label 改回 Text，删捕获缝/新帧与判据，MotionDriver 正对照改回旧字面量。
"""
CS=u"""### 设置「恢复默认」按钮补图标（18 张旧帧变化 + 2 张新帧、基线 318）（R493 / 第 492 轮 / Round 490 / U-1917…U-1922 · 产品 2 文件 + 判据）

"""
BS=u"""**585. RESET_ICON 的 runner 1x/dark 未签收**（R493 观察）
    现象：本机 2x 右列墨 light 3057→3507（+450）、dark 3636→4101（+465）；runner 1x 未读。
    修法：下一跑读 `RESET_ICON` 两档；若 1x 有内容但差低于 40·s²，先查捕获通道，不降地板。

**586. 权重复位尺钉的是按钮源码形状，不是产品调用路径**（R493 观察）
    现象：按钮改成 closure-label 后 `weightsResetIsAnimated` 失配；本轮已重锚，但它仍对按钮写法敏感。
    修法：若要更稳，改读 `Self.resetDefaults` 的唯一调用次数与 helper 的 withAnimation；先不加判据。
"""
SS=u"""## R493 状态（2026-10-29 · 本地 · 第 492 轮 / Round 490）：设置「恢复默认」按钮补图标（18 张旧帧变化 + 2 张新帧、基线 318）；全量 1309/56/0（产品 2 文件 + 判据）

最后更新：2026-10-29（本地 · R493 / 第 492 轮 / Round 490）：数据页导出/导入已带图标，快捷键/推荐两处「恢复默认」仍纯文字 —— 同一设置窗口的动作图标语言分裂。修法：`HotKeySettingsRow` 与 `RecommendationWeightsView` 的按钮改用 `Label("恢复默认", systemImage: "arrow.counterclockwise")`，标签不改；加捕获缝 `settingsResetButtonIconsForCapture`（产品默认 nil 画）。旧/新：**18 张旧帧变化**（settings-shortcuts、settings-min、conflict、recording、recommendations-tall 等）、**2 张新帧**（settings-shortcuts-no-reset-icon 亮暗）、0 缺失；基线 **316→318**；逐张看过：图标在标签左、按钮未压卡片、禁用态仍可读。读数（`RESET_ICON`，2x）：light 右列墨 **3057→3507（+450）**、dark **3636→4101（+465）**。新判据读右列墨差；`M1331`（永不画）/`M1332`（负臂也画）**2/2**。**重跑 MotionDriverTests 并重锚权重复位尺**：按钮 closure-label 形状变化后 `weightsResetIsAnimated` 的正对照已改，两格通过。预检 **274/251/676 bad=0**、ARM **367/1164**、HIDDEN **361/1103 rot=0**。⓪：push no-op、HEAD=origin/main=`e754cf7`、**ahead=0**；R492 主跑 `40880105650 ↔ a90b074` failure 2 步（Release 3 条 + Motion 已知 2 条；LOGIN_FAILURE_ICON NOT_RUN=no-red-channel 两档），补记跑 `40880472552 ↔ e754cf7` failure 仅 Motion 2 条；R491 主跑 Release 3 条 + Motion 1<1、补记跑 success；R490 主跑 Release 3 条、补记跑 success；R489/R488/R487/R486 沿用；436 无新跑。全量 **1309/56/0**（525.8s，轻载）；捕获卷 **318 帧**；基线 **318/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 492，`python3 scripts/product_streak.py --streak-for 492`，last=a90b074）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R492 两跑均 failure（主跑 Release 3 条 + Motion 2 条；补记跑仅 Motion 2 条）；LOGIN_FAILURE_ICON NOT_RUN=no-red-channel。
② 产品：恢复默认按钮补图标（18 旧帧 + 2 新帧、基线 318）。
③ 判据：右列墨差 450/465；M1331/M1332 2/2；MotionDriver 重锚。
④ 预检 274/251/676；rot 361/1103；ARM 367/1164。
⑤ 捕获 318 帧；基线 318/0/0/0；build 0 告警；换装 ok/397=397；全量 1309/56/0。

NOT-RUN / 阻塞（分开写）：① R493 自身跑（提交后取）；② RESET_ICON runner 1x/dark；③ LOGIN_FAILURE_ICON 1x（no-red-channel）；④ QUICKPICK_CONTENT_BADGE 1x 已签收；⑤ HISTORY_SOURCE_ICON 1x 已签收；⑥ DEFAULT_BADGE runner 仍 NOT_RUN=settings-content-blank；⑦ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑧ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑨ QUICKPICK_FAVORITE 1x 已签收；⑩ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑪ SETTINGS_DATA_PATH；⑫ 既有 runner 复核；⑬ Capture MATERIAL_BLIND_NOT_RUN；⑭ 已知 Motion 采样红（本跑 2 条）；⑮ 437–586 的其余未结项仍开。

下一轮（R494）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R493 自身跑、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2；R490 主跑唯一红是 Release 3 条；R492 主跑/补记跑均 Motion 2 条已知红）；**重点读 `RESET_ICON`（右列墨差 ≥40·s²、1x/dark）、`LOGIN_FAILURE_ICON`（no-red-channel）、`QUICKPICK_CONTENT_BADGE`（1x 已签收）、`HISTORY_SOURCE_ICON`（1x 已签收）、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R493（恢复默认按钮图标位）**：数据页按钮已有图标，快捷键/推荐「恢复默认」仍纯文字。两处改用 `Label("恢复默认", systemImage: "arrow.counterclockwise")`，标签不改，加捕获缝。**18 张旧帧 + 2 张新帧**，基线 **316→318**；`RESET_ICON` light 3057→3507（+450）、dark 3636→4101（+465）；M1331/M1332 2/2；MotionDriver 权重复位尺按 closure-label 重锚后通过。⓪ push no-op、ahead=0；R492 两跑均 failure（主跑 Release 3 条 + Motion 2 条；补记跑仅 Motion 2 条）；LOGIN_FAILURE_ICON NOT_RUN=no-red-channel。全量 **1309/56/0**（525.8s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 492 轮（R493" in a: raise SystemExit("A")
if u"## Round 490 · R493" in i: raise SystemExit("I")
if u"## D-489" in d: raise SystemExit("D")
if u"设置「恢复默认」按钮补图标" in c: raise SystemExit("C")
if u"**585." in b: raise SystemExit("B")
if st.count(u"## R492 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1916（R492 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R492 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R492 状态",SS+u"## R492 状态",1))
p2=p.replace(U,u"U-31 … U-1922（R493 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R492 节 ②",u"AGENT_STATE.md` 的 R493 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
