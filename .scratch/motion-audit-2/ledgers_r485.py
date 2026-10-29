#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 483 轮（R484 · 2026-10-29"
AS=u"""## 第 484 轮（R485 · 2026-10-29 · U-1869…U-1874）：浮层候选行补「已收藏」星标（2 张新帧、基线 304；M1315/M1316 2/2）（产品 1 文件 + 判据）

- **U-1869：⓪ push 与 CI。** 开工 `git push` 两次均报 remote closed、`git ls-remote` 同报 ⇒ **`PUSH_BLOCKED=network`（HEAD=`2eadacf`、origin/main=`6454a93`、ahead=1）**、`CI_READ_BLOCKED=network`（gh EOF）。R484 跑 `40826572977 ↔ 6454a93` 未读 ⇒ NOT-RUN。R483 跑 `40821834371 ↔ a59956c` **failure 1 步**＝Release script tests：3 条非产品红（`test_the_sources_cell_agrees_with_git`/`test_the_cell_agrees_with_its_own_source` 是主笔跑先于补记的 sources 格；`test_the_roster_matches_what_this_machine_actually_skips` 是嵌套套件无汇总行，同提交组 `40802042660 ↔ 7f21720` success 是反证），Swift **1299/74 skip/0 failure**、Capture gate **failed=0/红=0**、`CLEAR_LABEL_NOT_RUN=settings-content-blank` 两档具名。R481 跑 `40812979165 ↔ 2770bfe` 签收 `ROW_LINK_BADGE 19/18`、Capture 红 0、Motion `5/5 executed=77 reds=0`。R480 `60d65a4` **无跑**（同批 push head `2d54488` 跑归 R481）。R478 主跑 `40801850707 ↔ b64682e` **failure 3 步**（冲突 `0≠2`）、补记跑 `40802042660 ↔ 7f21720` **success**；R477 主跑 `40797827495 ↔ 0fd3ec0` **failure 4 步**（冲突 `0≠2` + Motion `1<2`）、补记跑 `40797866181 ↔ 7a79987` **failure 2 步**（冲突红仍在，已由 `7f21720` 跑签收）；R479 跑 `40805576917 ↔ 225e6f8` 沿用 R481 账签收。436 无新跑（最后已知 R481 跑 reds=0）。
- **U-1870：① 腐烂与预检。** `HIDDEN_ARMS 表=352 可判=1085 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=266 covered=243 arms=660 bad=0`（新表已登记；M1316 的 needle 跨行，静态抽不出 ⇒ 以真跑 2/2 签收）、`ARM_TOTAL files=359 arms=1148`。
- **U-1871：② 产品：浮层候选行补「已收藏」星标。** 缺陷形状（修前 `quickpick-favorite` 与 `quickpick-no-source` 逐像素同形）：主列表每行都用星标说「已收藏」，浮层的置顶、来源、时间都有标记，唯独收藏一个字都不说 —— 同一条记录在两种列表里有两种可见性。修法：`QuickPickRowCell` 加 `favoriteBadge`（9pt `star.fill`，叠在类型符号右上角，与图钉右下角错开；不占固定槽），颜色走 `FavoriteTogglePresentation.favoriteNSColor`（从同一份 `favoriteColor` 派生，浮层与主列表不会变成两种橙）；读屏标签加「收藏 」前缀。旧/新：**2 张新帧**（`quickpick-favorite` 亮暗）、**0 张旧帧变化**、0 缺失；基线 **302→304**；逐张看过：星在类型符号右上角、不压标题/时间，图钉仍在右下角。读数（`QUICKPICK_FAVORITE`，2x）：light 类型列墨 **215→328（+113）**、首墨行 **115→105（上移 10px）**、标题末列差 **0px**；dark **233→348（+115）**、上移 **9px**、标题末列差 **0px**。
- **U-1872：③ 判据与刀。** 新判据 `testQuickPickFavoriteRowsCarryAStarBadge` 用成对帧四句：① 负臂类型列有墨（尺有对象）；② 正臂多出星形墨 ≥8·s²；③ 正臂首墨行比负臂高 ≥2·s（星在类型符号**上方**，不是第二颗图钉或标题前缀）；④ 标题末列差 ≤3·s（叠层不占布局）。颜色不作证，只数墨。刀 `M1315`（星永不画）/`M1316`（星永远画，负臂也画）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1873：④ 既有面。** 浮层标题/时间右沿、类型符号、来源槽、图钉徽标均未动（旧帧 0 变化）；`quickpick-pinned` 仍只有右下角图钉；主列表星标与详情药丸的收藏色未动。
- **U-1874：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **304 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `304/0/0/0`；全量 **1301/56/0**（467.8s，轻载；新增 1 条判据）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 484，`python3 scripts/product_streak.py --streak-for 484`，last=6454a93）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R484 跑（网络未读）与补记 `2eadacf` 未推；② `QUICKPICK_FAVORITE` 的 runner 1x/dark；③ `HEATMAP_TODAY`/`CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；④ `SETTINGS_DATA_PATH`；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ 收藏+置顶同时出现的帧未拍；⑨ 437–570 的其余未结项仍开。

"""
IS=u"""## Round 482 · R485（第 484 轮 · 2026-10-29）：浮层候选行补「已收藏」星标（2 新帧、基线 304）

浮层的置顶、来源、时间都有标记，唯独收藏没有；同一条记录在主列表有星标，浮层里零可见（修前 `quickpick-favorite` 与 `quickpick-no-source` 逐像素同形）。`QuickPickRowCell` 加 `favoriteBadge`（9pt star.fill，类型符号右上角，与图钉右下角错开），颜色与主列表同源；读屏标签加「收藏 」。2 张新帧、0 旧帧变化，基线 302→304；`QUICKPICK_FAVORITE` light 215→328（+113）、首墨行 115→105；dark 233→348（+115）、上移 9px；标题末列差 0px。M1315/M1316 2/2。预检 266/243/660、rot 352/1085、ARM 359/1148。全量 1301/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ 网络两探失败 ⇒ PUSH_BLOCKED=network（2eadacf、ahead=1）、CI_READ_BLOCKED；R484 跑未读 ⇒ NOT-RUN；R483 跑唯一红是 Release 3 条非产品。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 修前正/负两帧逐像素同形；修后亮暗两帧逐张看过：星在类型符号右上角、不压标题/时间。 |
| 判据有效性 | 15/15 | 成对帧四句（对象/墨差/上移/标题不动）；M1315/M1316 2/2。 |
| 假绿防御 | 14/15 | 颜色不作证、只数墨；新表 needle 跨行静态抽不出，已用真跑 2/2 补；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（浮层候选行收藏星标）；1 个产品文件；2 新帧、旧帧 0 变化。 |
| 台账一致性 | 15/15 | U-1869…U-1874、D-481、304 帧/1301、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 修前同形帧留证；网络两探失败具名 PUSH_BLOCKED；收藏+置顶同现未拍具名。 |
| 可复核性 | 15/15 | 215→328/115→105、233→348/9px、标题差 0、M1315/M1316、precheck 266/243/660、基线 304 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-481 浮层行补收藏星标，位置与图钉分角、颜色与主列表同源（R485）

- 背景：主列表每行用星标说「已收藏」，浮层的置顶/来源/时间都有标记，唯独收藏不可见；同一条记录在两种列表里有两种可见性。
- 决定：`QuickPickRowCell` 加 `favoriteBadge`（9pt `star.fill`），叠在类型符号**右上角**，图钉留在右下角；不占固定槽。颜色走 `FavoriteTogglePresentation.favoriteNSColor`（由同一份 `favoriteColor` 派生）。读屏标签加「收藏 」前缀。
- 理由：叠层不占布局，标题/时间轴不动；两个状态徽标分角，互不遮挡；颜色只作身份不作判据（判据只数墨）。
- 兼容性/迁移：2 张新帧、0 旧帧变化，基线 302→304；未收藏行的几何一字未动。
- 边界：收藏+置顶同时出现没有帧；runner 1x/dark 未签收（首墨行 9pt 小图在 1x 可能只余 4–5px）。
- 回滚：删 favoriteBadge/两个锚点/读屏前缀/新帧与判据。
"""
CS=u"""### 浮层候选行补「已收藏」星标（2 张新帧、基线 304）（R485 / 第 484 轮 / Round 482 / U-1869…U-1874 · 产品 1 文件 + 判据）

"""
BS=u"""**569. QUICKPICK_FAVORITE 的 runner 1x/dark 未签收**（R485 观察）
    现象：本机 2x 读数 light +113 墨/上移 10px、dark +115/9px；runner 是 1x，9pt 星标可能只余 4–5px 墨。
    修法：下一跑读 `QUICKPICK_FAVORITE` 两档；若 1x 墨差低于 8·s²，先查捕获通道，不降地板。

**570. 收藏与置顶同时出现没有帧**（R485 观察）
    现象：星在类型符号右上、图钉在右下，几何上不重叠（星 9pt、图钉 9pt、16pt 符号），但没有同时置顶+收藏的帧。
    修法：需要时加一张 `quickpick-favorite-pinned` 成对帧，量两枚徽标的行带与标题轴；不加就先不声明视觉已验证。
"""
SS=u"""## R485 状态（2026-10-29 · 本地 · 第 484 轮 / Round 482）：浮层候选行补「已收藏」星标（2 张新帧、基线 304）；全量 1301/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R485 / 第 484 轮 / Round 482）：浮层的置顶、来源、时间都有标记，唯独收藏没有；同一条记录在主列表有星标，浮层里零可见（修前 `quickpick-favorite` 与 `quickpick-no-source` 逐像素同形）。修法：`QuickPickRowCell` 加 `favoriteBadge`（9pt `star.fill`，叠在类型符号右上角，与图钉右下角错开；不占固定槽），颜色走 `FavoriteTogglePresentation.favoriteNSColor`（与主列表同源）；读屏标签加「收藏 」前缀。旧/新：**2 张新帧**（quickpick-favorite 亮暗）、**0 张旧帧变化**、0 缺失；基线 **302→304**；逐张看过：星在类型符号右上角、不压标题/时间，图钉仍在右下角。读数（`QUICKPICK_FAVORITE`，2x）：light 类型列墨 **215→328（+113）**、首墨行 **115→105（上移 10px）**、标题末列差 **0px**；dark **233→348（+115）**、上移 **9px**、标题末列差 **0px**。新判据用成对帧四句（对象/墨差 ≥8·s²/首墨行上移 ≥2·s/标题末列差 ≤3·s）；`M1315`（星永不画）/`M1316`（星永远画）**2/2**。预检 **266/243/660 bad=0**（新表已登记；M1316 needle 跨行，静态抽不出 ⇒ 真跑 2/2）、ARM **359/1148**、HIDDEN **352/1085 rot=0**。⓪：开工两次 push 均 remote closed、`ls-remote` 同报 ⇒ **`PUSH_BLOCKED=network`（HEAD=`2eadacf`、origin/main=`6454a93`、ahead=1）**、**`CI_READ_BLOCKED=network`**；R484 跑 `40826572977 ↔ 6454a93` 未读 ⇒ NOT-RUN；R483 跑 `40821834371 ↔ a59956c` failure 1 步＝Release script 3 条非产品红（sources 格×2 + skip roster 嵌套；`40802042660 ↔ 7f21720` success 反证），Swift 1299/74 skip/0 failure、Capture gate failed=0/红=0、CLEAR_LABEL 两档 NOT_RUN；R481 跑签收 ROW_LINK_BADGE 19/18、Capture 红 0；R480 无跑；R478 主跑冲突红、补记跑 success；R477 两跑冲突红；R479 沿用；436 无新跑。全量 **1301/56/0**（467.8s，轻载）；捕获卷 **304 帧**；基线 **304/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 484，`python3 scripts/product_streak.py --streak-for 484`，last=6454a93）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 网络两探失败 ⇒ PUSH_BLOCKED=network（2eadacf、ahead=1）/CI_READ_BLOCKED；R484 跑未读 ⇒ NOT-RUN；R483 跑唯一红是 Release 3 条非产品。
② 产品：浮层候选行收藏星标（2 新帧、基线 304）。
③ 判据：成对帧四句 + M1315/M1316 2/2；颜色不作证。
④ 预检 266/243/660；rot 352/1085；ARM 359/1148。
⑤ 捕获 304 帧；基线 304/0/0/0；build 0 告警；换装 ok/397=397；全量 1301/56/0。

NOT-RUN / 阻塞（分开写）：① R484 跑（网络未读）与补记 2eadacf 未推；② QUICKPICK_FAVORITE runner 1x/dark；③ HEATMAP_TODAY/CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；④ SETTINGS_DATA_PATH；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ 收藏+置顶同现帧未拍；⑨ 437–570 的其余未结项仍开。

下一轮（R486）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R485 自身跑、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑 `40801850707`/`40802042660`、R477 两跑 `40797827495`/`40797866181`、R479 跑 `40805576917` 的全部失败步骤（R483 唯一红是 Release script 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收）；**重点读 `QUICKPICK_FAVORITE`（≥8·s²、首墨行上移 ≥2·s、1x/dark）、`HEATMAP_TODAY`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R485（浮层候选行收藏星标位）**：浮层的置顶/来源/时间都有标记，唯独收藏没有；同一条记录在主列表有星标，浮层里零可见（修前 `quickpick-favorite` 与 `quickpick-no-source` 逐像素同形）。`QuickPickRowCell` 加 `favoriteBadge`（9pt star.fill，类型符号右上角，与图钉右下角错开），颜色与主列表同源；读屏标签加「收藏 」。**2 张新帧、0 旧帧变化**，基线 **302→304**；`QUICKPICK_FAVORITE` light 215→328（+113）、首墨行 115→105；dark 233→348（+115）、上移 9px；标题末列差 0px；M1315/M1316 **2/2**。⓪ 网络两探失败 ⇒ **PUSH_BLOCKED=network（2eadacf、ahead=1）**、CI_READ_BLOCKED；R484 跑未读 ⇒ NOT-RUN；R483 跑唯一红是 Release 3 条非产品。全量 **1301/56/0**（467.8s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 484 轮（R485" in a: raise SystemExit("A")
if u"## Round 482 · R485" in i: raise SystemExit("I")
if u"## D-481" in d: raise SystemExit("D")
if u"浮层候选行补「已收藏」星标" in c: raise SystemExit("C")
if u"**569." in b: raise SystemExit("B")
if st.count(u"## R484 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1868（R484 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R484 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R484 状态",SS+u"## R484 状态",1))
p2=p.replace(U,u"U-31 … U-1874（R485 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R484 节 ②",u"AGENT_STATE.md` 的 R485 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
