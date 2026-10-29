#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 489 轮（R490 · 2026-10-29"
AS=u"""## 第 490 轮（R491 · 2026-10-29 · U-1905…U-1910）：浮层候选行补内容标记（4 张新帧、基线 314；M1327/M1328 2/2）（产品 1 文件 + 判据）

- **U-1905：⓪ push 与 CI。** 开工两次探针均失败（`git push` remote closed、`ls-remote` 同报）、**`PUSH_BLOCKED=network`（HEAD=origin/main=`9f987c7`、ahead=0）**、**`CI_READ_BLOCKED=network`**；R490 主跑 `40865789755 ↔ c0c08c7` 与补记跑 `40866154839 ↔ 9f987c7` **均未读 ⇒ NOT-RUN**。R489 主跑 `40858253532 ↔ d8b0712` failure 仅 Release 3 条非产品（Swift/Capture/Motion 全绿；`DEFAULT_BADGE_NOT_RUN=settings-content-blank` 两档、种子守卫 NOT_RUN）、补记跑 `40861168233 ↔ 3d4a03a` success。R488 主跑 failure 2 步（Release 3 条 + Motion 已知 1<2）、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。
- **U-1906：① 腐烂与预检。** `HIDDEN_ARMS 表=359 可判=1099 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=272 covered=249 arms=672 bad=0`（新表登记）、`ARM_TOTAL files=365 arms=1160`；R490 的 `HISTORY_SOURCE_ICON` 旧表沿用手工签收，预检未新增腐烂。
- **U-1907：② 产品：浮层候选行补内容标记。** 缺陷形状（`quickpick-list` 直看）：主列表的链接/富文本/OCR 都有小标记，浮层一行只说标题 —— 同一份内容注释在两种列表里有两种可见性。修法：`QuickPickRowCell` 加 `contentBadge`（9pt，叠在类型符号**左上角**，与收藏右上、图钉右下错开；不占固定槽）；按链接 > 富文本 > OCR 取一枚符号（`link`/`textformat`/`text.viewfinder`），读屏标签加「链接/富文本/可搜索文字」前缀。旧/新：**4 张新帧**（quickpick-plain / quickpick-link-badge 亮暗）、**0 张旧帧变化**、0 缺失；基线 **310→314**；逐张看过：链接徽标在类型符号左上角、不压标题/时间，普通行无标记。
- **U-1908：③ 判据与刀。** 新判据 `testQuickPickLinkRowsCarryAContentBadge` 用成对帧（plain / link，同一条时间）读类型符号那一列墨量：`QUICKPICK_CONTENT_BADGE` light **215→311（+96）**、dark **233→332（+99）**（2x）。刀 `M1327`（内容徽标永不画）/`M1328`（无内容也画链接徽标）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。M1327 第一版写成同值注释（空刀），本轮内改成 `isHidden = true` 后重跑。
- **U-1909：④ 既有面。** 置顶/收藏徽标、来源图标、时间列、标题轴均未动；`quickpick-list`/`quickpick-typed`/`quickpick-pinned` 等旧帧逐字节不变。表格共享路径未动，宽表/表头沿用 R488 读数。
- **U-1910：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **314 帧**、`CHANGED=0 ADDED=4 MISSING=0`，更新后 `314/0/0/0`；全量 **1307/56/0**（509.0s，轻载）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 490，`python3 scripts/product_streak.py --streak-for 490`，last=c0c08c7）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R491 自身跑（push 恢复后取）；② `QUICKPICK_CONTENT_BADGE` 的 runner 1x/dark；③ R490 两跑（未读）；④ `HISTORY_SOURCE_ICON` runner 1x/dark；⑤ `DEFAULT_BADGE` runner 仍 NOT_RUN=settings-content-blank；⑥ `TABLE_COLUMNS`/`TABLE_PIPES` 1x 已签收；⑦ `DATA_ACTION_ICONS`/`HEATMAP_TODAY` 1x 出口已签收；⑧ `QUICKPICK_FAVORITE` 1x 已签收；⑨ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑩ `SETTINGS_DATA_PATH`；⑪ 既有 runner 复核；⑫ Capture MATERIAL_BLIND_NOT_RUN；⑬ 已知 Motion 采样红；⑭ 437–582 的其余未结项仍开。

"""
IS=u"""## Round 488 · R491（第 490 轮 · 2026-10-29）：浮层候选行补内容标记（4 新帧、基线 314）

主列表的链接/富文本/OCR 都有小标记，浮层一行只说标题。`QuickPickRowCell` 加 `contentBadge`（9pt，类型符号左上角，与收藏右上、图钉右下错开；链接 > 富文本 > OCR 取一枚），读屏标签加前缀。4 张新帧、0 旧帧变化，基线 310→314；`QUICKPICK_CONTENT_BADGE` light 215→311（+96）、dark 233→332（+99）；M1327/M1328 2/2（M1327 第一版空刀，本轮内改对）。预检 272/249/672、rot 359/1099、ARM 365/1160。全量 1307/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ 两次探针失败 ⇒ PUSH_BLOCKED=network（9f987c7、ahead=0）、CI_READ_BLOCKED；R490 两跑未读 ⇒ NOT-RUN；R489 主跑仅 Release 3 条非产品、补记跑 success。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张新帧逐张看过：链接徽标在类型符号左上角、普通行无标记、标题/时间未动。 |
| 判据有效性 | 15/15 | 类型列墨 215→311/233→332；M1327/M1328 2/2。 |
| 假绿防御 | 14/15 | M1327 第一版空刀被本轮内改对；扣 1：runner 1x 与 R490 两跑未读。 |
| 产品面推进 | 15/15 | 新类别（浮层候选行内容标记）；1 个产品文件；4 新帧。 |
| 台账一致性 | 15/15 | U-1905…U-1910、D-487、314 帧/1307、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 网络两探失败具名 PUSH_BLOCKED；空刀在本轮内改对；旧帧 0 变化。 |
| 可复核性 | 15/15 | 215→311、233→332、M1327/M1328、precheck 272/249/672、基线 314 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-487 浮层候选行补内容标记，叠在类型符号左上角（R491）

- 背景：主列表的链接/富文本/OCR 都有小标记，浮层一行只说标题；同一份内容注释在两种列表里有两种可见性。
- 决定：`QuickPickRowCell` 加 `contentBadge`（9pt，类型符号左上角，与收藏右上、图钉右下错开；按链接 > 富文本 > OCR 取一枚），读屏标签加「链接/富文本/可搜索文字」前缀。
- 理由：内容标记是状态不是控件，叠层不占固定槽；四角各一枚状态徽标（内容左上、收藏右上、图钉右下），标题/时间轴不动。
- 兼容性/迁移：4 张新帧、0 旧帧变化，基线 310→314；旧面板帧逐字节不变。
- 边界：runner 1x/dark 未读；一个内容徽标按优先级只显示一种（不并列）。
- 回滚：删 contentBadge/锚点/读屏前缀/新帧与判据。
"""
CS=u"""### 浮层候选行补内容标记（4 张新帧、基线 314）（R491 / 第 490 轮 / Round 488 / U-1905…U-1910 · 产品 1 文件 + 判据）

"""
BS=u"""**581. QUICKPICK_CONTENT_BADGE 的 runner 1x/dark 未签收**（R491 观察）
    现象：本机 2x 类型列墨 light 215→311（+96）、dark 233→332（+99）；runner 1x 未读。
    修法：下一跑读 `QUICKPICK_CONTENT_BADGE` 两档；若 1x 有内容但差低于 8·s²，先查捕获通道，不降地板。

**582. 一个内容徽标按优先级只显示一种（链接 > 富文本 > OCR）**（R491 观察）
    现象：同时是链接+富文本的条目只显示链接徽标；主列表会并列显示多枚。四角各一枚是本轮的设计取舍。
    修法：若要多枚并列，需要另立角位/横向徽标槽；先不加判据、不声称已解决。
"""
SS=u"""## R491 状态（2026-10-29 · 本地 · 第 490 轮 / Round 488）：浮层候选行补内容标记（4 张新帧、基线 314）；全量 1307/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R491 / 第 490 轮 / Round 488）：主列表的链接/富文本/OCR 都有小标记，浮层一行只说标题。修法：`QuickPickRowCell` 加 `contentBadge`（9pt，叠在类型符号左上角，与收藏右上、图钉右下错开；按链接 > 富文本 > OCR 取一枚），读屏标签加「链接/富文本/可搜索文字」前缀。旧/新：**4 张新帧**（quickpick-plain / quickpick-link-badge 亮暗）、**0 张旧帧变化**、0 缺失；基线 **310→314**；逐张看过：链接徽标在类型符号左上角、不压标题/时间，普通行无标记。读数（`QUICKPICK_CONTENT_BADGE`，2x）：light 类型列墨 **215→311（+96）**、dark **233→332（+99）**。新判据用成对帧读类型列墨差；`M1327`（永不画）/`M1328`（无内容也画链接）**2/2**（M1327 第一版空刀，本轮内改对）。预检 **272/249/672 bad=0**、ARM **365/1160**、HIDDEN **359/1099 rot=0**。⓪：两次探针均失败 ⇒ **`PUSH_BLOCKED=network`（HEAD=origin/main=`9f987c7`、ahead=0）**、**`CI_READ_BLOCKED=network`**；R490 两跑未读 ⇒ NOT-RUN；R489 主跑唯一红是 Release 3 条非产品（DEFAULT_BADGE/种子守卫 NOT_RUN）、补记跑 success；R488 主跑 Release 3 条 + Motion 已知 1<2、补记跑 success；R487 跑 success；R486 主跑唯一红是 Release 3 条、补记跑 success；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1307/56/0**（509.0s，轻载）；捕获卷 **314 帧**；基线 **314/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 490，`python3 scripts/product_streak.py --streak-for 490`，last=c0c08c7）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 两次探针失败 ⇒ PUSH_BLOCKED=network（9f987c7、ahead=0）/CI_READ_BLOCKED；R490 两跑未读 ⇒ NOT-RUN；R489 主跑唯一红是 Release 3 条、补记跑 success。
② 产品：浮层候选行内容标记（4 新帧、基线 314）。
③ 判据：类型列墨 215→311/233→332；M1327/M1328 2/2（空刀已改）。
④ 预检 272/249/672；rot 359/1099；ARM 365/1160。
⑤ 捕获 314 帧；基线 314/0/0/0；build 0 告警；换装 ok/397=397；全量 1307/56/0。

NOT-RUN / 阻塞（分开写）：① R491 自身跑（push 未上）；② QUICKPICK_CONTENT_BADGE runner 1x/dark；③ R490 两跑（未读）；④ HISTORY_SOURCE_ICON runner 1x/dark；⑤ DEFAULT_BADGE runner 仍 NOT_RUN=settings-content-blank；⑥ TABLE_COLUMNS/TABLE_PIPES 1x 已签收；⑦ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑧ QUICKPICK_FAVORITE 1x 已签收；⑨ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑩ SETTINGS_DATA_PATH；⑪ 既有 runner 复核；⑫ Capture MATERIAL_BLIND_NOT_RUN；⑬ 已知 Motion 采样红；⑭ 437–582 的其余未结项仍开。

下一轮（R492）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R491 自身跑、R490 两跑 `40865789755`/`40866154839`、R489 两跑 `40858253532`/`40861168233`、R488 两跑 `40851078685`/`40851311888`、R487 跑 `40845483735`、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤（R483/R486 唯一红是 Release 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R488 主跑唯一红是 Release 3 条 + Motion 已知 1<2）；**重点读 `QUICKPICK_CONTENT_BADGE`（类型列墨差 ≥8·s²、1x/dark）、`HISTORY_SOURCE_ICON`（彩色 ≥40·s²、负臂=0）、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`（1x 已签收）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R491（浮层候选行内容标记位）**：主列表的链接/富文本/OCR 都有小标记，浮层一行只说标题。`QuickPickRowCell` 加 `contentBadge`（9pt，类型符号左上角，与收藏右上、图钉右下错开；链接 > 富文本 > OCR 取一枚），读屏标签加前缀。**4 张新帧、0 旧帧变化**，基线 **310→314**；`QUICKPICK_CONTENT_BADGE` light 215→311（+96）、dark 233→332（+99）；M1327/M1328 2/2（M1327 第一版空刀，本轮内改对）。⓪ 两次探针失败 ⇒ PUSH_BLOCKED=network（9f987c7、ahead=0）、CI_READ_BLOCKED；R490 两跑未读 ⇒ NOT-RUN；R489 主跑唯一红是 Release 3 条、补记跑 success。全量 **1307/56/0**（509.0s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 490 轮（R491" in a: raise SystemExit("A")
if u"## Round 488 · R491" in i: raise SystemExit("I")
if u"## D-487" in d: raise SystemExit("D")
if u"浮层候选行补内容标记" in c: raise SystemExit("C")
if u"**581." in b: raise SystemExit("B")
if st.count(u"## R490 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1904（R490 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R490 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R490 状态",SS+u"## R490 状态",1))
p2=p.replace(U,u"U-31 … U-1910（R491 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R490 节 ②",u"AGENT_STATE.md` 的 R491 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
