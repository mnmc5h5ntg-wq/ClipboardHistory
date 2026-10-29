#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 485 轮（R486 · 2026-10-29"
AS=u"""## 第 486 轮（R487 · 2026-10-29 · U-1881…U-1886）：Markdown 渲染态表格去掉源码竖线（8 张旧帧变化、基线 306；M1319/M1320 2/2）（产品 2 文件 + 判据）

- **U-1881：⓪ push 与 CI。** `git push` no-op（Everything up-to-date）、HEAD=origin/main=`04cc517`、**ahead=0**。R486 主跑 `40836764232 ↔ dfbf6f6` **completed failure，唯一失败步骤是 Release script**：3 条非产品红（sources 格×2 + skip roster 嵌套）；Swift/Capture/Motion 全绿，`DATA_ACTION_ICONS_NOT_RUN=settings-content-blank` 两档与 `HEATMAP_TODAY_NOT_RUN=settings-content-blank` 两档都按预期出现，`QUICKPICK_FAVORITE` 1x 54→71/+17、50→63/+13、上移 4px。R486 补记跑 `40837020563 ↔ 04cc517` **success**。R485 跑 `40832860076 ↔ 35ad21a` failure 4 步（HEATMAP 两档 0、Motion 1<2、Release 3 条非产品）；R484 跑 `40826572977 ↔ 6454a93` failure 3 步（同上）；R483/R481/R480/R478 两跑/R477 两跑/R479 沿用。436 无新跑。
- **U-1882：① 腐烂与预检。** `HIDDEN_ARMS 表=355 可判=1091 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=268 covered=245 arms=664 bad=0`（新表登记；M1319/M1320 两针静态可判）、`ARM_TOTAL files=361 arms=1152`。
- **U-1883：② 产品：渲染态表格去掉源码竖线。** 缺陷形状（`detail-table-rows` 直看）：表格在渲染态仍原样带 `|`，R440/R448 只给表头字重与体行线，源码语法一直在正文里。修法：新 `MarkdownTablePresentation.renderedRow` 把每个 `|` 换成**同宽空格**（等宽字体）并只裁首尾空白，`renderedContent` 逐行套用；`MarkdownScanning.collectTable` 用它组装表格块。列的起点一字不挪（不做 R234 的列重排），源码态仍走原始字符串。旧/新：**8 张旧帧变化**（detail-markdown-rendered、detail-table、detail-table-rows、detail-table-wide 各亮暗）、0 新增/缺失；基线 **306/0/0/0**；逐张看过：竖线消失、两列对齐、行分隔线与表头字重仍在。
- **U-1884：③ 判据与刀。** 新判据 `testRenderedTablesHideSourcePipes` 两腿：① 纯函数 `renderedRow("| 名称 | 数量 |")` 不含 `|`、`renderedContent` 行数不变；② 产品帧 `detail-table-rows` 的表格块属性范围里 `|` 计数为 0，表格区墨 **light 4251 / dark 3731**（2x）证明表格真的画出来。刀 `M1319`（不剥竖线）/`M1320`（只剥表头）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。**重锚两把旧尺**：`testWideTablesKeepEachRowOnOneLine` 原来用 `hasPrefix("|")` 认表格行，竖线去掉后没有对象 ⇒ 改读 `tableRowCountAttribute` 的表格块范围；`TableHeaderPresentationTests` 的针从 `甲 | 乙` 改为 `甲   乙`，重跑 **3/3 绿**；宽表容器宽 752.1→**720.0pt**（仍 >611）、行片段 [1,1,1]、短表仍跟踪视图；表头墨比 1.40→**1.17/1.19**（仍 >1.08）。
- **U-1885：④ 既有面。** 源码态（`detail-markdown-source`）的 `|` 原样保留；表格体行分隔线、表头 semibold、宽表横向滚动、短表可读列均未动；纯文本/代码块/引用不用这条路径。
- **U-1886：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **306 帧**、`CHANGED=8 ADDED=0 MISSING=0`，复验 `306/0/0/0`；全量 **1303/56/0**（504.4s，轻载；重锚两把旧尺后重跑）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 486，`python3 scripts/product_streak.py --streak-for 486`，last=dfbf6f6）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R487 自身跑（提交后取）；② `TABLE_PIPES` 的 runner 1x/dark（detail 内容平涂时预期 NOT_RUN）；③ `DATA_ACTION_ICONS`/`HEATMAP_TODAY` 的 1x 出口已由 R486 跑签收；④ `QUICKPICK_FAVORITE` 1x 已签收；⑤ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑥ `SETTINGS_DATA_PATH`；⑦ 既有 runner 复核；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 采样红；⑩ 437–574 的其余未结项仍开。

"""
IS=u"""## Round 484 · R487（第 486 轮 · 2026-10-29）：渲染态表格去掉源码竖线（8 旧帧、基线 306）

表格在渲染态仍带 `|`，R440/R448 只改了表头字重与体行线。新 `MarkdownTablePresentation.renderedRow` 把每个竖线换成同宽空格并只裁首尾空白，`renderedContent` 逐行套用；`collectTable` 用它组装表格块。列起点不挪、源码态不变。8 张旧帧变化、基线 306 不变；`TABLE_PIPES` 表格块竖线 0、表格区墨 4251/3731；M1319/M1320 2/2。重锚两把旧尺（宽表认 `tableRowCountAttribute`、表头针改 `甲   乙`），宽表容器 752.1→720.0pt、表头墨比 1.40→1.17/1.19，均仍过旧地板。预检 268/245/664、rot 355/1091、ARM 361/1152。全量 1303/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push no-op、ahead=0；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；DATA_ACTION_ICONS/HEATMAP_TODAY 的 1x NOT_RUN 出口已签收。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 8 张旧帧逐张看过：竖线消失、两列对齐、行分隔线与表头字重仍在。 |
| 判据有效性 | 15/15 | 纯函数 + 表格块 `|` 计数 0 + 表格区墨 4251/3731；M1319/M1320 2/2。 |
| 假绿防御 | 14/15 | 两把旧尺按新对象重锚并重跑；扣 1：TABLE_PIPES 的 runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（表格竖线）；2 个产品文件；8 旧帧变化。 |
| 台账一致性 | 15/15 | U-1881…U-1886、D-483、306 帧/1303、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 源码态保留竖线；宽表/表头旧地板未降，读数原样登记。 |
| 可复核性 | 15/15 | 竖线 0、墨 4251/3731、M1319/M1320、precheck 268/245/664、基线 306 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-483 渲染态表格去源码竖线，列起点不挪；源码态保留（R487）

- 背景：表格在渲染态仍原样带 `|`；R440/R448 只给表头字重与体行线，源码语法一直在正文里。
- 决定：新 `MarkdownTablePresentation.renderedRow` 把每个 `|` 换成同宽空格并只裁首尾空白，`renderedContent` 逐行套用；`MarkdownScanning.collectTable` 用它组装表格块。源码态仍走原始字符串。
- 理由：等宽字体下竖线与空格同宽，列的起点一字不挪，不需要重排列宽（R234 的列重排仍不做）；只去语法字符，不改内容。
- 兼容性/迁移：8 张旧帧变化，基线 306 不变；宽表容器 752.1→720.0pt（仍 >611）、表头墨比 1.40→1.17/1.19（仍 >1.08），旧地板未降。
- 边界：runner 1x detail 内容平涂时 TABLE_PIPES 预期 NOT_RUN；源码态的竖线仍可见（有意）。
- 回滚：删 MarkdownTablePresentation，`collectTable` 改回 `collected.joined`，恢复两把旧尺的针。
"""
CS=u"""### Markdown 渲染态表格去掉源码竖线（8 张旧帧变化、基线 306）（R487 / 第 486 轮 / Round 484 / U-1881…U-1886 · 产品 2 文件 + 判据）

"""
BS=u"""**573. TABLE_PIPES 的 runner 1x/dark 未签收**（R487 观察）
    现象：本机 2x 表格块竖线 0、表格区墨 4251/3731；runner 1x detail 内容平涂时预期 NOT_RUN，未读。
    修法：下一跑读 `TABLE_PIPES` 两档；若 1x 有内容但表格区墨低于 300·s²，先查捕获通道，不降地板。

**574. 表格渲染仍用等宽空格对列，不是真正的表格布局**（R487 观察）
    现象：去掉竖线后列靠作者源码里的空格对齐；作者没对齐的表格仍会参差。R234 明确列重排不做。
    修法：若要真表格，另立一页用 NSTextTable 或自绘列宽；先不加判据、不声称已解决。
"""
SS=u"""## R487 状态（2026-10-29 · 本地 · 第 486 轮 / Round 484）：Markdown 渲染态表格去掉源码竖线（8 张旧帧变化、基线 306）；全量 1303/56/0（产品 2 文件 + 判据）

最后更新：2026-10-29（本地 · R487 / 第 486 轮 / Round 484）：表格在渲染态仍原样带 `|`，R440/R448 只给表头字重与体行线，源码语法一直在正文里。修法：新 `MarkdownTablePresentation.renderedRow` 把每个 `|` 换成**同宽空格**（等宽字体）并只裁首尾空白，`renderedContent` 逐行套用；`MarkdownScanning.collectTable` 用它组装表格块。列的起点一字不挪（不做 R234 的列重排），源码态仍走原始字符串。旧/新：**8 张旧帧变化**（detail-markdown-rendered、detail-table、detail-table-rows、detail-table-wide 各亮暗）、0 新增/缺失；基线 **306/0/0/0**；逐张看过：竖线消失、两列对齐、行分隔线与表头字重仍在。读数（`TABLE_PIPES`，2x）：表格块竖线 **0**、表格行 5、表格区墨 **light 4251 / dark 3731**。新判据两腿（纯函数无竖线 + 帧内表格块 `|` 计数 0 且表格区有墨）；`M1319`（不剥竖线）/`M1320`（只剥表头）**2/2**。**重锚两把旧尺**：宽表判据改读 `tableRowCountAttribute`（容器宽 752.1→720.0pt、行片段 [1,1,1]，仍 >611）；表头纯判据针改 `甲   乙`，重跑 3/3；表头墨比 1.40→1.17/1.19（仍 >1.08）。预检 **268/245/664 bad=0**、ARM **361/1152**、HIDDEN **355/1091 rot=0**。⓪：push no-op、HEAD=origin/main=`04cc517`、**ahead=0**；R486 主跑 `40836764232 ↔ dfbf6f6` failure 仅 Release script 3 条非产品，Swift/Capture/Motion 全绿，`DATA_ACTION_ICONS_NOT_RUN` 与 `HEATMAP_TODAY_NOT_RUN` 两档按预期出现，QUICKPICK_FAVORITE 1x 54→71/50→63 签收；R486 补记跑 `40837020563 ↔ 04cc517` **success**；R485/R484/R483/R481/R480/R478 两跑/R477 两跑/R479 沿用；436 无新跑。全量 **1303/56/0**（504.4s，轻载；重锚两把旧尺后重跑）；捕获卷 **306 帧**；基线 **306/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 486，`python3 scripts/product_streak.py --streak-for 486`，last=dfbf6f6）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；DATA_ACTION_ICONS/HEATMAP_TODAY 的 1x NOT_RUN 出口签收。
② 产品：渲染态表格去源码竖线（8 旧帧、基线 306）。
③ 判据：表格块竖线 0 + 表格区墨 4251/3731；M1319/M1320 2/2；重锚两把旧尺。
④ 预检 268/245/664；rot 355/1091；ARM 361/1152。
⑤ 捕获 306 帧；基线 306/0/0/0；build 0 告警；换装 ok/397=397；全量 1303/56/0。

NOT-RUN / 阻塞（分开写）：① R487 自身跑（提交后取）；② TABLE_PIPES runner 1x/dark；③ QUICKPICK_FAVORITE 1x 已签收；④ DATA_ACTION_ICONS/HEATMAP_TODAY 1x 出口已签收；⑤ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑥ SETTINGS_DATA_PATH；⑦ 既有 runner 复核；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 采样红；⑩ 437–574 的其余未结项仍开。

下一轮（R488）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R487 自身跑、R486 两跑 `40836764232`/`40837020563`、R485 跑 `40832860076`、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑 `40801850707`/`40802042660`、R477 两跑 `40797827495`/`40797866181`、R479 跑 `40805576917` 的全部失败步骤（R483 唯一红是 Release script 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收；R486 主跑唯一红是 Release 3 条非产品）；**重点读 `TABLE_PIPES`（竖线=0、表格区墨 ≥300·s²、1x/dark）、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`（1x 已签收）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R487（Markdown 表格竖线位）**：表格在渲染态仍原样带 `|`，R440/R448 只改表头字重与体行线。新 `MarkdownTablePresentation.renderedRow` 把每个竖线换成同宽空格并只裁首尾空白，`collectTable` 用它组装表格块；列起点不挪、源码态不变。**8 张旧帧变化、基线 306 不变**；`TABLE_PIPES` 表格块竖线 0、表格区墨 4251/3731；M1319/M1320 **2/2**。重锚两把旧尺（宽表认 `tableRowCountAttribute`、表头针改 `甲   乙`），宽表容器 752.1→720.0pt、表头墨比 1.40→1.17/1.19，均仍过旧地板。⓪ push no-op、ahead=0；R486 主跑唯一红是 Release 3 条非产品、补记跑 success；DATA_ACTION_ICONS/HEATMAP_TODAY 的 1x NOT_RUN 出口签收。全量 **1303/56/0**（504.4s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 486 轮（R487" in a: raise SystemExit("A")
if u"## Round 484 · R487" in i: raise SystemExit("I")
if u"## D-483" in d: raise SystemExit("D")
if u"Markdown 渲染态表格去掉源码竖线" in c: raise SystemExit("C")
if u"**573." in b: raise SystemExit("B")
if st.count(u"## R486 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1880（R486 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R486 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R486 状态",SS+u"## R486 状态",1))
p2=p.replace(U,u"U-31 … U-1886（R487 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R486 节 ②",u"AGENT_STATE.md` 的 R487 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
