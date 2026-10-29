#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 487 轮（R488 · 2026-10-29"
AS=u"""## 第 488 轮（R489 · 2026-10-29 · U-1893…U-1898）：默认排除项补「默认」身份标记（6 张旧帧变化 + 2 张新帧、基线 310；M1323/M1324 2/2）（产品 1 文件 + 判据）

- **U-1893：⓪ push 与 CI。** `git push` no-op（Everything up-to-date）、HEAD=origin/main=`2cafe1b`、**ahead=0**。R488 主跑 `40851078685 ↔ 9487c0f` **failure 2 步**：Release script 3 条非产品 + Motion 已知 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess 1<2`（judged=4/5）；Swift/Capture 全绿，`TABLE_COLUMNS` 1x **制表位=2、第二列 [122,123,123] 极差 1px、第三列 [161,161,161] 极差 0px**（dark 160/160/160）、`TABLE_PIPES` 1x 竖线 0、墨 1130/1073、`WIDE_TABLE` 689.9pt/行片段 1、`TABLE_HEADER` 1.08/1.19。R488 补记跑 `40851311888 ↔ 2cafe1b` **success**。R487 跑 success（TABLE_PIPES 1x 0/1158/1074、WIDE_TABLE 719.8、表头 1.11/1.18）；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。
- **U-1894：① 腐烂与预检。** `HIDDEN_ARMS 表=357 可判=1095 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=270 covered=247 arms=668 bad=0`（新表登记；M1323/M1324 两针静态可判）、`ARM_TOTAL files=363 arms=1156`。**重锚 R432 两把旧刀**（默认名单 ForEach 的针被本轮 HStack 断掉）：M1187/M1188 改指新块后 **2/2 CAUGHT**、RESTORE_CLEAN=yes；种子守卫从“右缘所有墨段”改为只数**红段**（默认标记是灰色，不再混入），现读 `SEED_GUARD 期望=2 右边缘墨带=11 红段=2`。
- **U-1895：② 产品：默认排除项补「默认」身份标记。** 缺陷形状（`settings-privacy-excluded` 直看）：默认排除项不能移除，自定义项有红色「移除」；两类行原来只靠按钮有无区分，用户看不出“为什么这一行不能删”。修法：默认名单的每行尾部补 `Text("默认")`（meta、secondary、fixedSize、accessibilityLabel「默认排除项，不可移除」），自定义行的「移除」不动；加捕获缝 `settingsDefaultExcludedBadgeForCapture`（产品默认 nil 画）。旧/新：**6 张旧帧变化**（settings-privacy、settings-privacy-excluded、settings-privacy-tall 各亮暗）+ **2 张新帧**（settings-privacy-no-default-badge 亮暗）、0 缺失；基线 **308→310**；逐张看过：默认行尾部灰字与自定义行红「移除」分列、行高不变。
- **U-1896：③ 判据与刀。** 新判据 `testDefaultExcludedRowsCarryADefaultBadge` 读右列墨量差（两臂都有自定义行「移除」；差出来的就是默认标记）：`DEFAULT_BADGE` light **2704→5548（差 2844）**、dark **3132→6723（差 3591）**（2x）。刀 `M1323`（标记永不画）/`M1324`（标记移到行下左侧）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1897：④ 既有面。** 自定义行的「移除」、默认行的图标/名称/bundle ID、输入框与「添加」、底部「数据与保留」卡片均未动；种子守卫重锚后仍能数出 2 条自定义行。**表格共享路径本轮未动**，宽表/表头沿用 R488 读数。
- **U-1898：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **310 帧**、`CHANGED=6 ADDED=2 MISSING=0`，更新后 `310/0/0/0`；全量 **1305/56/0**（513.6s，轻载；种子守卫重锚后重跑）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 488，`python3 scripts/product_streak.py --streak-for 488`，last=9487c0f）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R489 自身跑（提交后取）；② `DEFAULT_BADGE` 的 runner 1x/dark（设置内容平涂时预期 NOT_RUN）；③ `TABLE_COLUMNS` 1x 已由 R488 跑签收；④ `TABLE_PIPES` 1x 已签收；⑤ `DATA_ACTION_ICONS`/`HEATMAP_TODAY` 1x 出口已签收；⑥ `QUICKPICK_FAVORITE` 1x 已签收；⑦ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑧ `SETTINGS_DATA_PATH`；⑨ 既有 runner 复核；⑩ Capture MATERIAL_BLIND_NOT_RUN；⑪ 已知 Motion 采样红；⑫ 437–578 的其余未结项仍开。

"""
IS=u"""## Round 486 · R489（第 488 轮 · 2026-10-29）：默认排除项补「默认」身份标记（6 旧帧 + 2 新帧、基线 310）

默认排除项不能移除、自定义项有红色「移除」，两类行原来只靠按钮有无区分。默认行尾部补 `Text("默认")`（meta/secondary/fixedSize + accessibilityLabel），自定义行不动；加捕获缝。6 张旧帧变化 + 2 张新帧，基线 308→310；`DEFAULT_BADGE` light 2704→5548（差 2844）、dark 3132→6723（差 3591）；M1323/M1324 2/2。重锚 R432 M1187/M1188 后 2/2；种子守卫改数红段（11→红段=2）。预检 270/247/668、rot 357/1095、ARM 363/1156。全量 1305/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push no-op、ahead=0；R488 主跑唯一红是 Release 3 条 + 已知 Motion 1<2、补记跑 success；TABLE_COLUMNS 1x 制表位=2、第二列极差 1px、第三列 0px。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 8 张隐私帧逐张看过：默认灰字与自定义红「移除」分列、行高不变。 |
| 判据有效性 | 15/15 | 右列墨差 2844/3591；M1323/M1324 2/2；R432 旧刀重锚 2/2。 |
| 假绿防御 | 14/15 | 种子守卫从墨段改红段，避免把灰色默认标记算成自定义行；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（默认排除项身份标记）；1 个产品文件；6 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1893…U-1898、D-485、310 帧/1305、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 表格共享路径未动；宽表/表头沿用 R488 runner 读数；runner 结论原样登记。 |
| 可复核性 | 15/15 | 2704→5548/3132→6723、M1323/M1324、重锚 M1187/M1188、precheck 270/247/668、基线 310 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-485 默认排除项补「默认」身份标记；种子守卫改数红色「移除」（R489）

- 背景：默认排除项不能移除、自定义项有红色「移除」；两类行只靠按钮有无区分，默认行的“为什么不能删”在界面上没有答案。
- 决定：默认名单每行尾部补 `Text("默认")`（meta、secondary、fixedSize、accessibilityLabel「默认排除项，不可移除」）；自定义行的「移除」不动；加捕获缝 `settingsDefaultExcludedBadgeForCapture`。
- 理由：默认行需要身份/状态标记，而不是再造一条删除动作；标记在右列与「移除」同轴，扫读时一眼分开两类。
- 兼容性/迁移：6 张旧帧变化 + 2 张新帧，基线 308→310；种子守卫从右缘所有墨段改为红段，避免把灰色标记算成自定义行。
- 边界：runner 1x/dark 未读；默认标记为灰色文字，不承担颜色对比判据。
- 回滚：删标记/捕获缝/新帧与判据，种子守卫恢复右缘墨段。
"""
CS=u"""### 默认排除项补「默认」身份标记（6 张旧帧变化 + 2 张新帧、基线 310）（R489 / 第 488 轮 / Round 486 / U-1893…U-1898 · 产品 1 文件 + 判据）

"""
BS=u"""**577. DEFAULT_BADGE 的 runner 1x/dark 未签收**（R489 观察）
    现象：本机 2x 右列墨差 light 2844 / dark 3591；runner 1x 设置内容平涂时预期 NOT_RUN，未读。
    修法：下一跑读 `DEFAULT_BADGE` 两档；若 1x 有内容但差低于 80·s²，先查捕获通道，不降地板。

**578. 默认标记与自定义「移除」同处右列，靠文字/颜色区分**（R489 观察）
    现象：默认行尾部灰字「默认」与自定义行红字「移除」都在右列；色盲用户只靠文字区分。
    修法：下一轮若要更强的身份语义，可给默认行加一个中性图标；先不加判据、不声称已解决。
"""
SS=u"""## R489 状态（2026-10-29 · 本地 · 第 488 轮 / Round 486）：默认排除项补「默认」身份标记（6 张旧帧变化 + 2 张新帧、基线 310）；全量 1305/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R489 / 第 488 轮 / Round 486）：默认排除项不能移除，自定义项有红色「移除」；两类行原来只靠按钮有无区分，用户看不出“为什么这一行不能删”。修法：默认名单每行尾部补 `Text("默认")`（meta、secondary、fixedSize、accessibilityLabel「默认排除项，不可移除」），自定义行的「移除」不动；加捕获缝 `settingsDefaultExcludedBadgeForCapture`（产品默认 nil 画）。旧/新：**6 张旧帧变化**（settings-privacy、settings-privacy-excluded、settings-privacy-tall 各亮暗）+ **2 张新帧**（settings-privacy-no-default-badge 亮暗）、0 缺失；基线 **308→310**；逐张看过：默认行尾部灰字与自定义行红「移除」分列、行高不变。读数（`DEFAULT_BADGE`，2x）：light 右列墨 **2704→5548（差 2844）**、dark **3132→6723（差 3591）**。新判据读右列墨量差；`M1323`（永不画）/`M1324`（移到行下左侧）**2/2**。**重锚 R432 两把旧刀**（默认名单 ForEach 的针被本轮 HStack 断掉）：M1187/M1188 改指新块后 **2/2**；种子守卫从“右缘所有墨段”改为只数**红段**，现读 `期望=2 右缘墨带=11 红段=2`。预检 **270/247/668 bad=0**、ARM **363/1156**、HIDDEN **357/1095 rot=0**。⓪：push no-op、HEAD=origin/main=`2cafe1b`、**ahead=0**；R488 主跑 `40851078685 ↔ 9487c0f` failure 2 步（Release 3 条非产品 + Motion 已知 1<2），Swift/Capture 全绿，`TABLE_COLUMNS` 1x **制表位=2、第二列 [122,123,123] 极差 1px、第三列 [161,161,161] 极差 0px**、`TABLE_PIPES` 1x 0、`WIDE_TABLE` 689.9pt/行片段 1、`TABLE_HEADER` 1.08/1.19；R488 补记跑 `40851311888 ↔ 2cafe1b` success；R487 跑 success；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1305/56/0**（513.6s，轻载；种子守卫重锚后重跑）；捕获卷 **310 帧**；基线 **310/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 488，`python3 scripts/product_streak.py --streak-for 488`，last=9487c0f）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R488 主跑唯一红是 Release 3 条 + 已知 Motion 1<2、补记跑 success；TABLE_COLUMNS 1x 签收。
② 产品：默认排除项补「默认」身份标记（6 旧帧 + 2 新帧、基线 310）。
③ 判据：右列墨差 2844/3591；M1323/M1324 2/2；重锚 R432 M1187/M1188；种子守卫改红段。
④ 预检 270/247/668；rot 357/1095；ARM 363/1156。
⑤ 捕获 310 帧；基线 310/0/0/0；build 0 告警；换装 ok/397=397；全量 1305/56/0。

NOT-RUN / 阻塞（分开写）：① R489 自身跑（提交后取）；② DEFAULT_BADGE runner 1x/dark；③ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；④ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑤ QUICKPICK_FAVORITE 1x 已签收；⑥ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑦ SETTINGS_DATA_PATH；⑧ 既有 runner 复核；⑨ Capture MATERIAL_BLIND_NOT_RUN；⑩ 已知 Motion 采样红；⑪ 437–578 的其余未结项仍开。

下一轮（R490）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R489 自身跑、R488 两跑 `40851078685`/`40851311888`、R487 跑 `40845483735`、R486 两跑 `40836764232`/`40837020563`、R485 跑 `40832860076`、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2）；**重点读 `DEFAULT_BADGE`（右列墨差 ≥80·s²、1x/dark）、`TABLE_COLUMNS`（1x 已签收）、`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R489（默认排除项身份标记位）**：默认排除项不能移除、自定义项有红色「移除」，两类行原来只靠按钮有无区分。默认行尾部补 `Text("默认")`（meta/secondary/fixedSize + accessibilityLabel），自定义行不动；加捕获缝。**6 张旧帧 + 2 张新帧**，基线 **308→310**；`DEFAULT_BADGE` light 2704→5548（差 2844）、dark 3132→6723（差 3591）；M1323/M1324 2/2；重锚 R432 M1187/M1188 2/2；种子守卫改数红段（右缘墨带 11→红段 2）。⓪ push no-op、ahead=0；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2、补记跑 success；TABLE_COLUMNS 1x 制表位=2、第二列极差 1px、第三列 0px。全量 **1305/56/0**（513.6s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 488 轮（R489" in a: raise SystemExit("A")
if u"## Round 486 · R489" in i: raise SystemExit("I")
if u"## D-485" in d: raise SystemExit("D")
if u"默认排除项补「默认」身份标记" in c: raise SystemExit("C")
if u"**577." in b: raise SystemExit("B")
if st.count(u"## R488 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1892（R488 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R488 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R488 状态",SS+u"## R488 状态",1))
p2=p.replace(U,u"U-31 … U-1898（R489 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R488 节 ②",u"AGENT_STATE.md` 的 R489 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
