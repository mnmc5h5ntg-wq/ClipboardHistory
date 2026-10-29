#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 486 轮（R487 · 2026-10-29"
AS=u"""## 第 487 轮（R488 · 2026-10-29 · U-1887…U-1892）：表格列宽随内容对齐（8 张旧帧变化 + 2 张新帧、基线 308；M1319–M1322 4/4）（产品 3 文件 + 判据）

- **U-1887：⓪ push 与 CI。** 开工一次快进 push **`04cc517..519b22b` success**、HEAD=origin/main=`519b22b`、**ahead=0**。R487 跑 `40845483735 ↔ 519b22b` **success**；`TABLE_PIPES` 1x **竖线=0、表格区墨 1158/1074**，`TABLE_HEADER` **1.11/1.18**（>1.08）、左右沿 21.0/21.0pt，`WIDE_TABLE` 容器 **719.8pt**、行片段 [1,1,1]、滚动条开、短表仍跟踪视图。R486 主跑 `40836764232 ↔ dfbf6f6` failure 仅 Release script 3 条非产品（Swift/Capture/Motion 全绿；`DATA_ACTION_ICONS_NOT_RUN` 与 `HEATMAP_TODAY_NOT_RUN` 两档按预期出现；QUICKPICK_FAVORITE 1x 54→71/50→63 签收），补记跑 `40837020563 ↔ 04cc517` success。R485/R484 failure 4/3 步沿用；R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。
- **U-1888：① 腐烂与预检。** `HIDDEN_ARMS 表=356 可判=1093 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=269 covered=246 arms=666 bad=0`（新表登记；M1321/M1322 两针静态可判）、`ARM_TOTAL files=362 arms=1154`。
- **U-1889：② 产品：表格列宽随内容对齐。** 缺陷形状（修前 `detail-table-uneven` 直看）：R487 去竖线后，列位置仍跟作者源码里的空格走；长单元格把第二列推歪，三行第二列起点 **269/254/260px**、第三列 **353/350/356px**（2x）。修法：`MarkdownTablePresentation.renderedContent` 只保留 `\\t` 分列，`columnStops(in:)` 按每列**最大实宽**（表头 semibold、表体 regular 各用自己的字体）算 12pt 间距的绝对制表位；`MarkdownPresentation.paragraphStyle` 给表格块设置这些 `tabStops`；`WideMarkdownDocument` 的表格宽度改按最后一列右沿量。旧/新：**8 张旧帧变化**（detail-markdown-rendered、detail-table、detail-table-rows、detail-table-wide 各亮暗）+ **2 张新帧**（detail-table-uneven 亮暗）、0 缺失；基线 **306→308**；逐张看过：三列对齐、行分隔线与表头字重仍在。
- **U-1890：③ 判据与刀。** 新判据 `testTableColumnsAlignAcrossRows`：先读表格块段落 `tabStops` **必须=2**（三列），再在帧上按每个文字行的列 run 起点读第二/第三列，极差 ≤2·s。读数：第二列 **[245,246,246] 极差 1px**、第三列 **[321,321,321] 极差 0px**（2x）。刀 `M1321`（不设制表位）/`M1322`（只按表头定列宽）**2/2 CAUGHT**；R487 旧刀 `M1319/M1320` 按新函数重锚后仍 **2/2**、RESTORE_CLEAN=yes。**重锚后宽表 690.1pt（仍 >611）、行片段 [1,1,1]；表头墨比 1.16/1.19（仍 >1.08）**。
- **U-1891：④ 既有面。** 源码态仍保留作者表格源码；表格体行分隔线、表头 semibold、宽表横向滚动、短表可读列均未动；R488 的首版按空格补宽（表头/表体字体差导致残差 5–15px）与首版 tab（把已渲染行又按竖线切）均在本轮内撤回，最终用 tabStops。
- **U-1892：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **308 帧**、`CHANGED=8 ADDED=2 MISSING=0`，更新后 `308/0/0/0`；全量 **1304/56/0**（506.7s，轻载；宽表宽度修正后重跑）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 487，`python3 scripts/product_streak.py --streak-for 487`，last=d44e16d）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R488 自身跑（提交后取）；② `TABLE_COLUMNS` 的 runner 1x/dark；③ `TABLE_PIPES` 1x 已由 R487 跑签收；④ `DATA_ACTION_ICONS`/`HEATMAP_TODAY` 1x 出口已签收；⑤ `QUICKPICK_FAVORITE` 1x 已签收；⑥ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑦ `SETTINGS_DATA_PATH`；⑧ 既有 runner 复核；⑨ Capture MATERIAL_BLIND_NOT_RUN；⑩ 已知 Motion 采样红；⑪ 437–576 的其余未结项仍开。

"""
IS=u"""## Round 485 · R488（第 487 轮 · 2026-10-29）：表格列宽随内容对齐（8 旧帧 + 2 新帧、基线 308）

R487 去竖线后列仍跟作者源码空格走，长单元格把第二列推歪（修前 269/254/260px、第三列 353/350/356px）。修法：`renderedContent` 只保留 `\\t` 分列，`columnStops` 按每列最大实宽（表头/表体各自字体）算绝对制表位，`paragraphStyle` 给表格块设 tabStops，`WideMarkdownDocument` 按最后一列右沿量宽。8 张旧帧变化 + 2 张新帧，基线 306→308；`TABLE_COLUMNS` 制表位=2、第二列 [245,246,246] 极差 1px、第三列 [321,321,321] 极差 0px；M1321/M1322 2/2，R487 M1319/M1320 重锚后 2/2。宽表 690.1pt（>611）、行片段 [1,1,1]；表头墨比 1.16/1.19（>1.08）。预检 269/246/666、rot 356/1093、ARM 362/1154。全量 1304/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push 04cc517..519b22b success、ahead=0；R487 跑 success（TABLE_PIPES 1x 0/1158/1074、WIDE_TABLE 719.8、表头 1.11/1.18）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 修前/修后 2 张 uneven 帧逐张看过：第二列 269/254/260→245/246/246、第三列 353/350/356→321/321/321。 |
| 判据有效性 | 15/15 | 结构（tabStops=2）+ 像素（列起点极差 1/0px）；M1321/M1322 与重锚后的 M1319/M1320 共 4/4。 |
| 假绿防御 | 14/15 | 首版空格补宽残留 5–15px、首版 tab 零停靠均在本轮内被读数打回；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（列宽随内容对齐）；3 个产品文件；8 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1887…U-1892、D-484、308 帧/1304、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 源码态保留；宽表/表头旧地板未降；R487 runner 读数原样登记。 |
| 可复核性 | 15/15 | 269/254/260→245/246/246、353/350/356→321/321/321、tabStops=2、precheck 269/246/666、基线 308 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-484 表格列用绝对制表位对齐，列宽按每列最大实宽；源码态不变（R488）

- 背景：R487 去竖线后列仍跟作者源码空格走，长单元格把第二列推歪。
- 决定：`MarkdownTablePresentation.renderedContent` 只保留 `\\t` 分列；`columnStops(in:)` 按每列最大实宽（表头 semibold、表体 regular 各用自己的字体）计算 12pt 间距的绝对制表位；`MarkdownPresentation.paragraphStyle` 给表格块设置 `tabStops`；`WideMarkdownDocument` 的表格宽度按最后一列右沿量。
- 理由：空格式补宽离不开字体实宽与取整，表头/表体字重差会残留 5–15px；tabStops 是绝对位置，不吃这个差。
- 兼容性/迁移：8 张旧帧变化 + 2 张新帧，基线 306→308；宽表 690.1pt（仍 >611）、行片段 [1,1,1]；表头墨比 1.16/1.19（>1.08）。
- 边界：runner 1x/dark 未读；源码态保留作者源码中的原样空格。
- 回滚：删 columnStops/tabStops/measuredWidth，renderedContent 改回空格拼接。
"""
CS=u"""### 表格列宽随内容对齐（制表位；8 张旧帧变化 + 2 张新帧、基线 308）（R488 / 第 487 轮 / Round 485 / U-1887…U-1892 · 产品 3 文件 + 判据）

"""
BS=u"""**575. TABLE_COLUMNS 的 runner 1x/dark 未签收**（R488 观察）
    现象：本机 2x 第二列 [245,246,246] 极差 1px、第三列 [321,321,321] 极差 0px；runner 1x 未读。
    修法：下一跑读 `TABLE_COLUMNS` 两档；若 1x 有内容但列段不足，按缺陷红，不许改写成 NOT_RUN。

**576. 表格列对齐仍依赖等宽字体与制表位，不是 NSTextTable**（R488 观察）
    现象：列宽按实宽算，但单元格多行/自动换行时仍无行内折行策略；源码态的整行宽度由作者决定。
    修法：若要真表格换行，另立一页用 NSTextTable；先不加判据、不声称已解决。
"""
SS=u"""## R488 状态（2026-10-29 · 本地 · 第 487 轮 / Round 485）：表格列宽随内容对齐（8 张旧帧变化 + 2 张新帧、基线 308）；全量 1304/56/0（产品 3 文件 + 判据）

最后更新：2026-10-29（本地 · R488 / 第 487 轮 / Round 485）：R487 去竖线后列仍跟作者源码里的空格走，长单元格把第二列推歪（修前 `detail-table-uneven` 第二列 **269/254/260px**、第三列 **353/350/356px**，2x）。修法：`MarkdownTablePresentation.renderedContent` 只保留 `\\t` 分列，`columnStops(in:)` 按每列**最大实宽**（表头 semibold、表体 regular 各用自己的字体）算 12pt 间距的绝对制表位；`MarkdownPresentation.paragraphStyle` 给表格块设置 `tabStops`；`WideMarkdownDocument` 的表格宽度按最后一列右沿量。旧/新：**8 张旧帧变化**（detail-markdown-rendered、detail-table、detail-table-rows、detail-table-wide 各亮暗）+ **2 张新帧**（detail-table-uneven 亮暗）、0 缺失；基线 **306→308**；逐张看过：三列对齐、行分隔线与表头字重仍在。读数（`TABLE_COLUMNS`，2x）：制表位 **2**、第二列 **[245,246,246] 极差 1px**、第三列 **[321,321,321] 极差 0px**。新判据先读 tabStops=2 再读列起点极差 ≤2·s；`M1321`（不设制表位）/`M1322`（只按表头定列宽）**2/2**；R487 旧刀 `M1319/M1320` 重锚后仍 **2/2**。**重锚后宽表 690.1pt（仍 >611）、行片段 [1,1,1]；表头墨比 1.16/1.19（仍 >1.08）**。预检 **269/246/666 bad=0**、ARM **362/1154**、HIDDEN **356/1093 rot=0**。⓪：一次快进 push **`04cc517..519b22b` success**、HEAD=origin/main=`519b22b`、**ahead=0**；R487 跑 `40845483735 ↔ 519b22b` **success**（TABLE_PIPES 1x 竖线 0、墨 1158/1074；TABLE_HEADER 1.11/1.18；WIDE_TABLE 719.8pt/行片段 1）；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1304/56/0**（506.7s，轻载；宽表宽度修正后重跑）；捕获卷 **308 帧**；基线 **308/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 487，`python3 scripts/product_streak.py --streak-for 487`，last=d44e16d）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 04cc517..519b22b success、ahead=0；R487 跑 success（TABLE_PIPES 1x 0/1158/1074、WIDE_TABLE 719.8、表头 1.11/1.18）；R486 主跑唯一红是 Release 3 条非产品。
② 产品：表格列宽随内容对齐（8 旧帧 + 2 新帧、基线 308）。
③ 判据：tabStops=2 + 列起点极差 1/0px；M1321/M1322 2/2、M1319/M1320 重锚 2/2。
④ 预检 269/246/666；rot 356/1093；ARM 362/1154。
⑤ 捕获 308 帧；基线 308/0/0/0；build 0 告警；换装 ok/397=397；全量 1304/56/0。

NOT-RUN / 阻塞（分开写）：① R488 自身跑（提交后取）；② TABLE_COLUMNS runner 1x/dark；③ TABLE_PIPES 1x 已签收；④ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑤ QUICKPICK_FAVORITE 1x 已签收；⑥ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑦ SETTINGS_DATA_PATH；⑧ 既有 runner 复核；⑨ Capture MATERIAL_BLIND_NOT_RUN；⑩ 已知 Motion 采样红；⑪ 437–576 的其余未结项仍开。

下一轮（R489）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R488 自身跑、R487 跑 `40845483735`、R486 两跑 `40836764232`/`40837020563`、R485 跑 `40832860076`、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑 `40805576917` 的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收）；**重点读 `TABLE_COLUMNS`（制表位=2、第二/第三列极差 ≤2·s、1x/dark）、`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R488（表格列宽随内容对齐位）**：R487 去竖线后列仍跟作者源码空格走，长单元格把第二列推歪（修前 269/254/260px、第三列 353/350/356px）。`renderedContent` 只保留 `\\t` 分列；`columnStops` 按每列最大实宽（表头/表体各自字体）算绝对制表位；`paragraphStyle` 给表格块设 tabStops；`WideMarkdownDocument` 按最后一列右沿量宽。**8 张旧帧 + 2 张新帧**，基线 **306→308**；`TABLE_COLUMNS` 制表位=2、第二列 [245,246,246] 极差 1px、第三列 [321,321,321] 极差 0px；M1321/M1322 2/2，R487 M1319/M1320 重锚后 2/2。宽表 690.1pt（>611）、行片段 [1,1,1]；表头墨比 1.16/1.19（>1.08）。⓪ push 04cc517..519b22b success、ahead=0；R487 跑 success（TABLE_PIPES 1x 0/1158/1074、WIDE_TABLE 719.8、表头 1.11/1.18）；R486 主跑唯一红是 Release 3 条非产品。全量 **1304/56/0**（506.7s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 487 轮（R488" in a: raise SystemExit("A")
if u"## Round 485 · R488" in i: raise SystemExit("I")
if u"## D-484" in d: raise SystemExit("D")
if u"表格列宽随内容对齐" in c: raise SystemExit("C")
if u"**575." in b: raise SystemExit("B")
if st.count(u"## R487 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1886（R487 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R487 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R487 状态",SS+u"## R487 状态",1))
p2=p.replace(U,u"U-31 … U-1892（R488 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R487 节 ②",u"AGENT_STATE.md` 的 R488 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
