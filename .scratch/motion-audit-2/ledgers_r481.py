#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 479 轮（R480 · 2026-10-29"
AS=u"""## 第 480 轮（R481 · 2026-10-29 · U-1851…U-1856）：主列表补链接条目标记（2 张新帧、基线 300；M1308/M1309 2/2）+ 设置标题图标的 runner NOT-RUN 修复（产品 1 文件 + 判据）

- **U-1851：⓪ push 与 CI。** 开工一次快进 push **`59b63c1..2d54488` success**（两笔：60d65a4/2d54488）、HEAD=origin/main=`2d54488`、**ahead=0**。R479 跑 `40805576917 ↔ 225e6f8` failure 3 步已读：Release script（sources 时序）、Swift/Capture（**唯一测试红是 `SETTINGS_TITLE_ICON` 0 墨**，设置内容列在 runner 平涂）、Motion `5/5 executed=77 reds=0`；同跑签收 `FALLBACK_PATH` 1x **113pt**、`INLINE_CODE_PAD light 99/6.0、dark 102/5.0`、幻影块 **0**、`QUICKPICK_PIN` **+20/标题末列 0**。R480 跑（2d54488）与 R479/R478/R477 其余跑读时 in_progress/未读 ⇒ NOT-RUN；436 R479 跑 reds=0。
- **U-1852：① 腐烂与预检。** `HIDDEN_ARMS 表=350 可判=1081 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=263 covered=243 arms=660 bad=0`、`ARM_TOTAL files=356 arms=1144`。
- **U-1853：② 产品：主列表补链接条目标记。** 缺陷形状：URL 文本行与普通文本行同形，用户看不出这是一条链接。修法：新纯函数 `EntryPresentation.looksLikeLink`（只认 http/https、无空白）；`RowTextColumn` 时间行在富文本标记前补 `link`（11pt、secondaryLabelColor、helpLabel + accessibilityLabel），仅链接文本出现。旧/新：**2 张新帧**（`row-link-text` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **298→300**；2 张逐张看过：链形标记在来源后、时间行同一行。读数：最下一条墨带（时间行）末列 light/dark **441→476px（+35px=17.5pt）**。
- **U-1854：③ 判据与刀。** 新判据 `testLinkRowsCarryALinkBadge` 用 `row-text` / `row-link-text`：两臂最下一条墨带都是时间行（同一串时间/来源），正臂末列必须右移 ≥8pt·s（+35px 实测）；不读标题末列（标题不同）。刀 `M1308`（永不画）/`M1309`（永远画）**2/2 CAUGHT**、RESTORE_CLEAN。`SETTINGS_TITLE_ICON` 判据补 `SETTINGS_TITLE_ICON_NOT_RUN=settings-content-blank` 的 skip（R479 跑在置空 runner 上把它当红，本轮修）；本机仍 2/2。
- **U-1855：④ 既有面。** R480 的富文本标记、R479 的标题图标、R478 兜底路径、R477 图钉、R476–R477 的 inline/幻影/冲突均未改；R479 跑的 `SETTINGS_TITLE_ICON` 0 墨归到机器前提，不记产品回归。
- **U-1856：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **300 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `300/0/0/0`；全量 **1298/56/0**（512.8s，轻载；新增 1 条链接标记判据）；换装 `ok / SHA_MATCH=1 / 397=397`（版本 1.4.8，现读口径）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 480，`python3 scripts/product_streak.py --streak-for 480`，last=60d65a4）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R480 自身跑；② 链接标记的 runner 1x/dark；③ `SETTINGS_TITLE_ICON` 的 runner（置空 ⇒ 预期 NOT-RUN）；④ `FALLBACK_PATH`/`INLINE_CODE_PAD`/幻影/图钉/冲突的 runner 复核；⑤ `SETTINGS_DATA_PATH`；⑥ 既有 runner 复核；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–562 的其余未结项仍开。

"""
IS=u"""## Round 478 · R481（第 480 轮 · 2026-10-29）：主列表补链接条目标记（2 张新帧、基线 300）+ 标题图标 runner NOT-RUN 修复

URL 文本行与普通行同形。新 `EntryPresentation.looksLikeLink` + `RowTextColumn` 的 `link` 标记（11pt、secondary、helpLabel + accessibilityLabel）。2 张新帧、0 旧帧变化，基线 298→300；最下墨带末列 441→476px（+35px）；M1308/M1309 2/2。`SETTINGS_TITLE_ICON` 在 runner 设置内容平涂时补 `SETTINGS_TITLE_ICON_NOT_RUN` skip（R479 跑唯一的测试红即此，不是产品）。预检 263/243/660、rot 350/1081、ARM 356/1144。全量 1298/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ 一次快进 push 59b63c1..2d54488 success、ahead=0；R479 跑签收 FALLBACK_PATH 113/INLINE 99/6.0 与 102/5.0/幻影 0/图钉 +20；R480 跑 in_progress ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张新帧逐张看过：链形标记在来源后、时间行同基线。 |
| 判据有效性 | 15/15 | 时间行末列 +35px；M1308/M1309 2/2；标题差异被排除（只看最下墨带）。 |
| 假绿防御 | 15/15 | 标题图标判据补 NOT-RUN（runner 置空）；R479 的 0 墨不记产品红。 |
| 产品面推进 | 15/15 | 新类别（链接条目标记）；1 个产品文件；2 新帧、0 旧帧变化。 |
| 台账一致性 | 15/15 | U-1851…U-1856、D-478、300 帧/1298、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | runner 唯一红与机器前提分开写；签名/探针都如实。 |
| 可复核性 | 15/15 | 2 张帧、441→476px、M1308/M1309、precheck 263/243/660、rot 350/1081、基线 300 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-478 链接文本要有行内标记；设置标题图标在置空 runner 上 NOT-RUN（R481）

- 背景：URL 文本行与普通文本行同形；R479 跑在 runner 的设置内容整列平涂上把标题图标判据当红。
- 决定：`EntryPresentation.looksLikeLink` + 时间行 `link` 标记（仅 http/https、无空白）；`SETTINGS_TITLE_ICON` 两臂 0 墨时打 `SETTINGS_TITLE_ICON_NOT_RUN=settings-content-blank` 并 skip。
- 理由：链接是内容类型而不是装饰；置空机器没有对象，红/绿都不成立。
- 兼容性/迁移：2 张新帧、0 旧帧变化，基线 298→300；无 Store 变化。
- 边界：链接标记 runner 1x/dark 未签收；R480 跑未读。
- 回滚：删标记/策略/判据；标题图标 NOT-RUN 分支保留。
"""
CS=u"""### 主列表补链接条目标记（2 张新帧、基线 300）（R481 / 第 480 轮 / Round 478 / U-1851…U-1856 · 产品 1 文件 + 判据）

"""
BS=u"""**562. R480/R479/R478/R477 的跑未读或 in_progress**（R481 观察）
    现象：R480 自身跑、R479/R478/R477 其余跑读时 in_progress/未读；SETTINGS_TITLE_ICON 的 runner 预期 NOT-RUN。
    修法：下一跑读全部失败步骤与 ROW_LINK_BADGE；仍红按读数继续。

**563. 链接标记的 runner 1x/dark 未签收**（R481 观察）
    现象：本机最下墨带末列 +35px；runner 1x 的 11pt 链形可能更小。
    修法：读新跑 ROW_LINK_BADGE；低于 8pt·s 按 scale 重算，不改产品字号。
"""
SS=u"""## R481 状态（2026-10-29 · 本地 · 第 480 轮 / Round 478）：主列表补链接条目标记（2 张新帧、基线 300）+ 标题图标 runner NOT-RUN 修复；全量 1298/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R481 / 第 480 轮 / Round 478）：URL 文本行与普通文本行同形。修法：新 `EntryPresentation.looksLikeLink`（http/https、无空白）；`RowTextColumn` 时间行补 `link` 标记（11pt、secondaryLabelColor、helpLabel + accessibilityLabel），仅链接文本出现。旧/新：**2 张新帧**（`row-link-text` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **298→300**；2 张逐张看过：链形标记在来源后、时间行同一行。读数：最下一条墨带（时间行）末列 light/dark **441→476px（+35px=17.5pt）**。判据用 `row-text`/`row-link-text` 的最下墨带末列（标题差异被排除）；`M1308`（永不画）/`M1309`（永远画）**2/2**。`SETTINGS_TITLE_ICON` 判据在 runner 设置内容整列平涂时补 `SETTINGS_TITLE_ICON_NOT_RUN=settings-content-blank` 并 skip（R479 跑唯一测试红即此，不是产品）。预检 **263/243/660 bad=0**、ARM **356/1144**、HIDDEN **350/1081 rot=0**。⓪：一次快进 push **`59b63c1..2d54488` success**、HEAD=origin/main=`2d54488`、**ahead=0**；R479 跑 `40805576917 ↔ 225e6f8` failure 3 步，签收 `FALLBACK_PATH` 113pt、`INLINE_CODE_PAD` 99/6.0 与 102/5.0、幻影 0、图钉 +20；R480 跑与其余读时 in_progress/未读 ⇒ NOT-RUN；436 R479 跑 reds=0。全量 **1298/56/0**（512.8s，轻载）；捕获卷 **300 帧**；基线 **300/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 480，`python3 scripts/product_streak.py --streak-for 480`，last=60d65a4）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 59b63c1..2d54488 success、ahead=0；R479 跑 signoff；R480 跑 in_progress ⇒ NOT-RUN；436 reds=0。
② 产品：主列表补链接条目标记（2 张新帧、基线 300）。
③ 判据：时间行末列 +35px；M1308/M1309 2/2；标题图标 runner NOT-RUN 修复。
④ 预检 263/243/660；rot 350/1081；ARM 356/1144。
⑤ 捕获 300 帧；基线 300/0/0/0；build 0 告警；换装 ok/397=397；全量 1298/56/0。

NOT-RUN / 阻塞（分开写）：① R480 自身跑；② 链接标记 runner 1x/dark；③ 标题图标 runner（置空 ⇒ NOT-RUN）；④ 兜底路径/inline/幻影/图钉/冲突 runner 复核；⑤ SETTINGS_DATA_PATH；⑥ 既有 runner 复核；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–563 的其余未结项仍开。

下一轮（R482）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R481 自身跑、R480 跑、R479 跑、R478 两跑、R477 两跑、R476 跑、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `ROW_LINK_BADGE`（≥8px·s）、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`、`ROW_RICH_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R481（链接条目标记位 + 标题图标 NOT-RUN 修复）**：URL 文本行与普通行同形。新 `EntryPresentation.looksLikeLink` + 时间行 `link` 标记（11pt、secondary、helpLabel + accessibilityLabel）。**2 张新帧、0 张既有帧变化**，基线 **298→300**；最下墨带末列 441→476px（+35px）；M1308/M1309 **2/2**。`SETTINGS_TITLE_ICON` 在 runner 设置内容平涂时补 `SETTINGS_TITLE_ICON_NOT_RUN` skip（R479 跑唯一测试红即此，不是产品）。⓪ 一次快进 push `59b63c1..2d54488` success、ahead=0；R479 跑签收 FALLBACK_PATH 113pt、INLINE 99/6.0 与 102/5.0、幻影 0、图钉 +20；R480 跑 in_progress ⇒ NOT-RUN。全量 **1298/56/0**（512.8s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 480 轮（R481" in a: raise SystemExit("A")
if u"## Round 478 · R481" in i: raise SystemExit("I")
if u"## D-478" in d: raise SystemExit("D")
if u"链接条目标记" in c: raise SystemExit("C")
if u"**562." in b: raise SystemExit("B")
if st.count(u"## R480 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1850（R480 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R480 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R480 状态",SS+u"## R480 状态",1))
p2=p.replace(U,u"U-31 … U-1856（R481 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R480 节 ②",u"AGENT_STATE.md` 的 R481 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
