#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 495 轮（R496 · 2026-10-30"
AS=u"""## 第 496 轮（R497 · 2026-10-30 · U-1941…U-1946）：主侧栏搜索占位符省略号与全 App 统一（44 张旧帧变化 + 2 张新帧、基线 326；M1341/M1342 2/2）（产品 1 文件 + 判据）

- **U-1941：⓪ push 与 CI。** 开工一次快进 push **`2e7828f..1d3179a` success**（两笔：`3c64394`/`1d3179a`）、HEAD=origin/main=`1d3179a`、**ahead=0**。最新跑 `40932022750 ↔ 1d3179a` 读时 **queued ⇒ NOT-RUN**（`3c64394` 无独立跑）。R495 跑 `40920092629 ↔ bbfe31c` **success**（`Executed 1311/80 skip/0`）：`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` light/dark（runner 设置帧 1.0x）、`MAIN_TITLE_ICON` light 478→550（+72）/ dark 3733→3820（+87）、`RESET_ICON_NOT_RUN=settings-content-blank` 两档。R494 主跑 `40895877246 ↔ 590ead8` **failure 仅 `STEP[9] Release script tests`**（日志全 `UNKNOWN STEP`：sources 格 ×2 + skip roster，`Ran 683 / FAILED 3`）；R494 补记跑 `40896245079 ↔ e05b13c` **failure 仅 `STEP[19] Motion coverage floor`**（`MOTION_FLOOR_FACTS judged=5/5 executed=77 reds=1` = `testCopyReceiptAppearsAndDismissesWithAVisibleProcess`；Swift 1310/79/0 绿）。R493 跑 `40887758385 ↔ 67cb683` **failure 2 步**：Release 3 条非产品 + Swift `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 1 条（1309/79/1；`RESET_ICON_NOT_RUN=settings-content-blank` 两档）。旧跑按 `ci_read.py steps` 成对复核失败步名：R492 主跑 = STEP[9]+STEP[19]、补记跑 = STEP[19]；R491 主跑 = STEP[9]+STEP[19]、补记跑 success；R490/R489 主跑 = STEP[9]、补记跑 success；R488 主跑 = STEP[9]+STEP[19]、补记跑 success；R487 success；R486 主跑 = STEP[9]、补记跑 success；R485 4 步、R484 3 步、R483 1 步、R481 1 步、R480 无跑、R478 主跑 3 步/补记跑 success、R477 主跑 4 步/补记跑 2 步、R479 3 步。436 沿用 R481 跑 `judged=5/5 executed=77 reds=0`。收口 push 与 R497 自身跑见补记。
- **U-1942：① 腐烂与预检。** `HIDDEN_ARMS 表=365 可判=1110 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=278 covered=255 arms=684 bad=0`（新表 `mutate_r497_search_placeholder` 登记）、`ARM_TOTAL files=371 arms=1171`。只动 `SearchField` 的占位文案与一个环境缝，旧表针无一腐烂、无需重锚；QuickPick/详情/表格面未动。
- **U-1943：② 产品：主侧栏搜索占位符省略号与全 App 统一。** 缺陷形状（`sidebar-history` 直看）：全仓动作文案十余处都用单「…」（导出历史…、查找…、正在加载预览…、浮层「搜索历史记录…」），只有主侧栏搜索占位符写「搜索历史……」**两个省略号** —— 同一 App 两种省略号形态。修法：占位符改成「搜索历史…」，加捕获缝 `searchPlaceholderForCapture`（产品默认 nil 用新形态，负向帧给旧文案）。旧/新：**44 张旧帧变化**（22 张 `content-*`、20 张 `sidebar-*`、2 张 `search-field-*`，各亮暗）、**2 张新帧**（`sidebar-search-placeholder-legacy` 亮暗）、0 缺失；基线 **324→326**；逐张看过：新占位符 3 点、旧帧 6 点，搜索框高度/清除按钮/侧栏其余几何未动。
- **U-1944：③ 判据与刀。** 新判据 `testSearchPlaceholderUsesTheSingleEllipsis` 量占位文字总墨宽（pt）：`SEARCH_PLACEHOLDER` light 正臂 **60.5pt**、负臂 **71.0pt**、差 **10.5pt**；dark 同值（2x）。判据要求两臂差落在 **[6,16]pt**（差的必须恰是一个省略号字形）；任一臂宽为 0 ⇒ `SEARCH_PLACEHOLDER_NOT_RUN=search-field-blank`。刀 `M1341`（占位符回到两个省略号）/`M1342`（去掉省略号）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1945：④ 既有面。** 新负向帧已登记系统纯黑填充带名册（与 `sidebar-history` 同一选中材质）；搜索框两态高度、清除 ×、侧栏搜索/多选/固定分区各行未动；QuickPick 占位符本就是单「…」。全量 **1313/56/1**：唯一红仍是 `PerfBudgetTests.testImageComparisonCostStaysBounded`（`LOCAL_PERF_BUDGET_FLAKE=load`，**单跑原样重跑通过**）；其余全绿。
- **U-1946：⑤ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh` arm64 冷编 + x86_64）；捕获卷 **326 帧**、`CHANGED=44 ADDED=2 MISSING=0`，更新后 `326/0/0/0`；全量 **1313/56/1**（857.8s；PerfBudget 本机负载 flake，单跑过）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 496，`python3 scripts/product_streak.py --streak-for 496`，last=3c64394）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。收口 push 与 R497 自身跑状态见补记。**具名 NOT-RUN**：① R497 自身跑（推送后取）；② `SEARCH_PLACEHOLDER` runner 1x/2x；③ `QUICKPICK_MATCH_HIGHLIGHT` runner 1x；④ `SETTINGS_HELPER_FONT` runner 1x/2x（scale-too-low）；⑤ `RESET_ICON`（settings-content-blank）；⑥ `LOGIN_FAILURE_ICON` 1x（no-red-channel）；⑦ `DEFAULT_BADGE`（settings-content-blank）；⑧ 其余 runner 复核；⑨ 已知性能/采样 flake（本跑 PerfBudget）；⑩ 437–594 的其余未结项仍开。

"""
IS=u"""## Round 494 · R497（第 496 轮 · 2026-10-30）：主侧栏搜索占位符省略号统一（44 旧帧 + 2 新帧、基线 326）

全仓动作文案十余处用单「…」，只有主侧栏搜索占位符写「搜索历史……」两个省略号。改成「搜索历史…」，加缝 `searchPlaceholderForCapture`。44 张旧帧变化（22 content-* + 20 sidebar-* + 2 search-field-*）+ 2 张新帧，基线 324→326；`SEARCH_PLACEHOLDER` 正臂 60.5pt、负臂 71.0pt、差 10.5pt（两档同值）；M1341/M1342 2/2。预检 278/255/684、rot 365/1110、ARM 371/1171。全量 1313/56/1（PerfBudget 本机 flake，单跑过）；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push `2e7828f..1d3179a` success、ahead=0；R496 跑 queued ⇒ NOT-RUN；R495 跑 success（1311/80/0）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 44 张旧帧 + 2 张新帧逐张看过：新占位 3 点、旧帧 6 点，其余几何未动。 |
| 判据有效性 | 15/15 | 正臂 60.5、负臂 71.0、差 10.5；M1341/M1342 2/2。 |
| 假绿防御 | 14/15 | 差必须在 [6,16]、空帧有具名 NOT_RUN；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（占位符省略号）；1 个产品文件；44 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1941…U-1946、D-493、326 帧/1313、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 全量唯一红按 PerfBudget flake 具名并单跑复验；R496 跑 queued 具名 NOT-RUN。 |
| 可复核性 | 15/15 | 60.5/71.0/10.5、M1341/M1342、precheck 278/255/684、基线 326 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-493 主侧栏搜索占位符统一单省略号；占位宽差作结构证人（R497）

- 背景：全仓动作文案十余处用单「…」，只有主侧栏搜索占位符写「搜索历史……」两个省略号 —— 同一 App 两种省略号形态。
- 决定：占位符改「搜索历史…」，加捕获缝 `searchPlaceholderForCapture`（产品默认 nil 用新形态，负向帧给旧文案）。
- 理由：省略号形态应当全 App 一致；旧形态在搜索框里读起来像"六个点"，比动作按钮里的「…」更长更吵。
- 兼容性/迁移：44 张旧帧变化 + 2 张新帧，基线 324→326；判据用两臂总墨宽差 [6,16]pt 当结构证人（不受字体/倍率影响）。
- 边界：runner 1x/2x 未读；其余页面文案的省略号没有源码级守卫（新开 594）。
- 回滚：占位符改回「搜索历史……」、删缝/新帧/判据/两刀，基线回 324。
"""
CS=u"""### 主侧栏搜索占位符省略号与全 App 统一（44 张旧帧变化 + 2 张新帧、基线 326）（R497 / 第 496 轮 / Round 494 / U-1941…U-1946 · 产品 1 文件 + 判据）

"""
BS=u"""**593. SEARCH_PLACEHOLDER 的 runner 1x/2x 未签收**（R497 观察）
    现象：本机 2x 正臂 60.5pt、负臂 71.0pt、差 10.5pt；R497 自身跑推送后仍 queued。
    修法：下一跑读该通道；若 1x 两臂宽差仍落 [6,16]pt 即签收，不降区间。

**594. 全应用文案的省略号只有主侧栏这一处有像素判据**（R497 观察）
    现象：导出历史…/查找…/正在加载预览…/浮层搜索历史记录… 都是单「…」，但只有主侧栏占位符被这条判据钉住。
    修法：若要全量守，需一条源码级清单（扫 `…`/`……`/`...` 字面量）或逐面像素判据；先不加。
"""
SS=u"""## R497 状态（2026-10-30 · 本地 · 第 496 轮 / Round 494）：主侧栏搜索占位符省略号与全 App 统一（44 张旧帧变化 + 2 张新帧、基线 326）；全量 1313/56/1（唯一红 PerfBudget 本机 flake，单跑过）（产品 1 文件 + 判据）

最后更新：2026-10-30（本地 · R497 / 第 496 轮 / Round 494）：全仓动作文案十余处用单「…」（导出历史…、查找…、正在加载预览…、浮层「搜索历史记录…」），只有主侧栏搜索占位符写「搜索历史……」两个省略号 —— 同一 App 两种省略号形态。修法：占位符改成「搜索历史…」，加捕获缝 `searchPlaceholderForCapture`（产品默认 nil 用新形态，负向帧给旧文案）。旧/新：**44 张旧帧变化**（22 张 `content-*`、20 张 `sidebar-*`、2 张 `search-field-*`，各亮暗）、**2 张新帧**（`sidebar-search-placeholder-legacy` 亮暗）、0 缺失；基线 **324→326**；逐张看过：新占位 3 点、旧帧 6 点，搜索框高度/清除 ×/侧栏其余几何未动。读数（`SEARCH_PLACEHOLDER`，2x）：light 正臂 **60.5pt**、负臂 **71.0pt**、差 **10.5pt**；dark 同值。判据要求两臂差 [6,16]pt（恰一个省略号字形），任一臂宽 0 ⇒ 具名 NOT_RUN。`M1341`（回到两个省略号）/`M1342`（去掉省略号）**2/2**。预检 **278/255/684 bad=0**、ARM **371/1171**、HIDDEN **365/1110 rot=0**。⓪：开工一次快进 push **`2e7828f..1d3179a` success**（两笔：`3c64394`/`1d3179a`）、HEAD=origin/main=`1d3179a`、**ahead=0**；最新跑 `40932022750 ↔ 1d3179a` **queued ⇒ NOT-RUN**；R495 跑 `40920092629 ↔ bbfe31c` **success**（`1311/80/0`；`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` 两档、`MAIN_TITLE_ICON` 1x 已签收、`RESET_ICON_NOT_RUN=settings-content-blank`）；R494 主跑 failure 仅 Release（3 条非产品）、补记跑仅 Motion（1 条）；R493 跑 failure 2 步（Release 3 条 + Swift 采样 1 条）；旧跑成对复核；收口 push 见补记。全量 **1313/56/1**（857.8s；唯一红 `PerfBudgetTests.testImageComparisonCostStaysBounded` = `LOCAL_PERF_BUDGET_FLAKE=load`，**单跑原样重跑通过**）；捕获卷 **326 帧**；基线 **326/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 496，`python3 scripts/product_streak.py --streak-for 496`，last=3c64394）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `2e7828f..1d3179a` success、ahead=0；R496 跑 queued ⇒ NOT-RUN；R495 跑 success；R494/R493/旧跑失败步名复核。
② 产品：主侧栏搜索占位符统一单省略号（44 旧帧 + 2 新帧、基线 326）。
③ 判据：正臂 60.5 / 负臂 71.0 / 差 10.5；M1341/M1342 2/2。
④ 预检 278/255/684；rot 365/1110；ARM 371/1171。
⑤ 捕获 326 帧；基线 326/0/0/0；build 0 告警；换装 ok/397=397；全量 1313/56/1（PerfBudget flake，单跑过）。

NOT-RUN / 阻塞（分开写）：① R497 自身跑（推送后取）；② SEARCH_PLACEHOLDER runner 1x/2x；③ QUICKPICK_MATCH_HIGHLIGHT runner 1x；④ SETTINGS_HELPER_FONT runner 1x/2x；⑤ RESET_ICON（settings-content-blank）；⑥ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑦ DEFAULT_BADGE（settings-content-blank）；⑧ 其余 runner 复核；⑨ 已知性能/采样 flake（本跑 PerfBudget）；⑩ 437–594 的其余未结项仍开。

下一轮（R498）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（R497 主笔提交后 ahead=1 起）；成对读 R497 自身跑（推送后才有）、R496 跑 `40932022750`、R495 跑 `40920092629`、R494 两跑、R493 跑及更早各跑的全部失败步骤；**重点读 `SEARCH_PLACEHOLDER`（两臂差 [6,16]pt、1x/2x）、`QUICKPICK_MATCH_HIGHLIGHT`（头 ≤40·s²、尾 ≥200·s²、负臂 0）、`SETTINGS_HELPER_FONT`（正臂极差 ≤0.6、负臂 ≥0.8）、`MAIN_TITLE_ICON`、`RESET_ICON`、`LOGIN_FAILURE_ICON`（no-red-channel）、`DEFAULT_BADGE`（settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做主侧栏搜索占位符省略号/浮层候选行搜索命中高亮/设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R497（搜索占位符省略号位）**：全仓动作文案十余处用单「…」，只有主侧栏搜索占位符写「搜索历史……」两个省略号。改「搜索历史…」，加缝 `searchPlaceholderForCapture`。**44 张旧帧 + 2 张新帧**，基线 **324→326**；`SEARCH_PLACEHOLDER` 正臂 60.5pt、负臂 71.0pt、差 10.5pt；M1341/M1342 2/2。⓪ push `2e7828f..1d3179a` success、ahead=0；R496 跑 queued ⇒ NOT-RUN；R495 跑 success（1311/80/0）。全量 1313/56/1（PerfBudget 本机 flake，单跑过）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 496 轮（R497" in a: raise SystemExit("A")
if u"## Round 494 · R497" in i: raise SystemExit("I")
if u"## D-493" in d: raise SystemExit("D")
if u"主侧栏搜索占位符省略号与全 App 统一" in c: raise SystemExit("C")
if u"**593." in b: raise SystemExit("B")
if st.count(u"## R496 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1940（R496 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R496 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R496 状态",SS+u"## R496 状态",1))
p2=p.replace(U,u"U-31 … U-1946（R497 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R496 节 ②",u"AGENT_STATE.md` 的 R497 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
