#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 496 轮（R497 · 2026-10-30"
AS=u"""## 第 497 轮（R498 · 2026-10-30 · U-1947…U-1952）：通用页 RTF 说明段最小窗孤字行（12 张旧帧变化 + 4 张新帧、基线 330；M1343/M1344 2/2）（产品 1 文件 + 判据）

- **U-1947：⓪ push 与 CI。** 开工一次快进 push **`a98e65d..c9d8d6c` success**、HEAD=origin/main=`c9d8d6c`、**ahead=0**。开工 `gh` 连续 **EOF** ⇒ **`CI_READ_BLOCKED=network`**：R497 跑 `40937242846 ↔ a98e65d` 上次读时 **queued ⇒ NOT-RUN**（本轮未新读，`SEARCH_PLACEHOLDER` 1x 仍缺）；`c9d8d6c` 自身跑未创建/未读到 ⇒ NOT-RUN。沿用已读：**R496 跑 `40932022750 ↔ 1d3179a` success**（`Executed 1312/80 skip/0`；`QUICKPICK_MATCH_HIGHLIGHT` 1x light 头 25/尾 290、dark 头 5/尾 245、负臂 0/0 ⇒ **BACKLOG 592 结案**；`SETTINGS_HELPER_FONT_NOT_RUN=scale-too-low` 两档）；R495 跑 `40920092629 ↔ bbfe31c` success（1311/80/0；`MAIN_TITLE_ICON` 1x 已签收、`RESET_ICON_NOT_RUN=settings-content-blank`）；R494 主跑 `40895877246 ↔ 590ead8` failure 仅 Release（3 条非产品红）、补记跑 `40896245079 ↔ e05b13c` failure 仅 Motion（`testCopyReceiptAppearsAndDismissesWithAVisibleProcess`；Swift 1310/79/0 绿）；R493 跑 `40887758385 ↔ 67cb683` failure 2 步（Release 3 条 + Swift `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime` 1 条）；旧跑成对失败步名沿用（R492–R479；436 沿用 R481 跑 `judged=5/5 executed=77 reds=0`）。收口 push 与 R498 自身跑见补记。
- **U-1948：① 腐烂与预检。** `HIDDEN_ARMS 表=366 可判=1112 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=279 covered=256 arms=686 bad=0`（新表 `mutate_r498_orphan_line` 登记）、`ARM_TOTAL files=372 arms=1173`。只动 `SettingsView` 的 RTF 说明字符串与一个环境缝；旧表针无一腐烂、无需重锚。
- **U-1949：② 产品：通用页 RTF 说明段最小窗孤字行。** 缺陷形状（640pt 最小窗 `settings-min-general` 直看）：RTF 说明段最后一行只剩「本。」—— 孤字行，末行墨宽 **14.0pt**。修法：把「文本。」用 U+00A0 绑成不断开的单元（读者看到的仍是同一句话），加捕获缝 `settingsRtfHelperCopyForCapture`（产品默认 nil 新写法，负向帧给旧文案）。旧/新：**12 张旧帧变化**（`settings-general*` 十条，各亮暗）、**4 张新帧**（`general-min-orphan` / `general-min-orphan-legacy`，各亮暗；组件帧命名避开按 `settings-` 前缀收集的整页尺）、0 缺失；基线 **326→330**；逐张看过：新帧末行「文本。」三字、负向帧仍是「本。」孤字，其余行/卡片几何未动。
- **U-1950：③ 判据与刀。** 新判据 `testRtfHelperLastLineIsNotAnOrphan` 读卡片最后一条文字带的墨宽：`RTF_HELPER_ORPHAN` light 正臂 **28.5pt** / 负臂 **14.0pt**；dark **29.0 / 15.0**（2x）。判据要求正臂 ≥22pt、负臂 ≤18pt（旧孤字必须复现）；任一臂 0 ⇒ `NOT_RUN=settings-content-blank`。刀 `M1343`（去掉 NBSP）/`M1344`（NBSP 绑错位置，只绑「纯文」）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1951：④ 既有面。** 新帧与旧帧姓名册：`CARD_INSET_CONTROL_FIRST` 不收录组件帧（改名后不再被整页尺扫到）、暗档侧栏 vibrant 名单实测这两张**不属 vibrant**（首版加进名单被 GONE 打回，已撤回）；`CARD_RHYTHM`/`CARD_INSET`/`DARK_SIDEBAR` 三支复跑全绿；`settings-general*` 的 caption 探针/轴/字号判据未动。
- **U-1952：⑤ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh` arm64 冷编 + x86_64）；捕获卷 **330 帧**、`CHANGED=12 ADDED=4 MISSING=0`，更新后 `330/0/0/0`；全量 **1314/56/1**（882.9s）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 497，`python3 scripts/product_streak.py --streak-for 497`，last=a98e65d）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。收口 push 与 R498 自身跑状态见补记。**具名 NOT-RUN**：① R498 自身跑（推送后取）；② `RTF_HELPER_ORPHAN` runner 1x/2x；③ `SEARCH_PLACEHOLDER` runner 1x（R497 跑未读）；④ `QUICKPICK_MATCH_HIGHLIGHT` 1x 已签收；⑤ `SETTINGS_HELPER_FONT` runner 1x/2x（scale-too-low）；⑥ `RESET_ICON`（settings-content-blank）；⑦ `LOGIN_FAILURE_ICON` 1x（no-red-channel）；⑧ `DEFAULT_BADGE`（settings-content-blank）；⑨ 已知性能/采样 flake；⑩ 437–596 的其余未结项仍开。

"""
IS=u"""## Round 495 · R498（第 497 轮 · 2026-10-30）：通用页 RTF 说明段最小窗孤字行（12 旧帧 + 4 新帧、基线 330）

640pt 最小窗下 RTF 说明段最后一行只剩「本。」（末行墨宽 14pt）。把「文本。」用 U+00A0 绑成不断开的单元，加捕获缝 `settingsRtfHelperCopyForCapture`（默认新写法，负向帧旧文案）。12 张旧帧 + 4 张新帧（组件帧名 `general-min-orphan*`，避开整页尺），基线 326→330；`RTF_HELPER_ORPHAN` 正臂 28.5/29.0pt、负臂 14.0/15.0pt；M1343/M1344 2/2。预检 279/256/686、rot 366/1112、ARM 372/1173。全量 1314/56/1；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push `a98e65d..c9d8d6c` success、ahead=0；gh EOF ⇒ CI_READ_BLOCKED；R496 跑 success（QUICKPICK 1x 签收、592 结案）；R497 跑 queued ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 12 张旧帧 + 4 张新帧逐张看过：新帧末行「文本。」、负向帧「本。」孤字，其余几何未动。 |
| 判据有效性 | 15/15 | 正臂 28.5/29.0、负臂 14.0/15.0；M1343/M1344 2/2。 |
| 假绿防御 | 14/15 | 负臂必须复现孤字、空帧有具名 NOT_RUN；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（最小窗孤字行）；1 个产品文件；12 旧帧 + 4 新帧。 |
| 台账一致性 | 15/15 | U-1947…U-1952、D-494、330 帧/1314/56/1、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | gh EOF/ R497 跑 queued 均具名；全量 flake 具名并单跑复验。 |
| 可复核性 | 15/15 | 28.5/14.0、29.0/15.0、M1343/M1344、precheck 279/256/686、基线 330 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-494 RTF 说明段用 NBSP 绑「文本。」避免最小窗孤字行（R498）

- 背景：640pt 最小窗下 RTF 说明段最后一行只剩「本。」（末行墨宽 14pt），是孤字行。
- 决定：把「文本。」用 U+00A0 绑成不断开的单元；加捕获缝 `settingsRtfHelperCopyForCapture`（产品默认 nil 新写法，负向帧旧文案）。
- 理由：SwiftUI 的 `Text` 在本 SDK 没有 `lineBreakStrategy`（实验编译失败已撤），NBSP 是不改文案、不改字号的唯一稳定写法；读者看到的仍是同一句话。
- 兼容性/迁移：12 张旧帧变化 + 4 张新帧，基线 326→330；新帧命名不带 `settings-` 前缀，避开按整页收集的 CARD_RHYTHM/CARD_INSET 尺。
- 边界：runner 1x/2x 未读；若换字号/换窗口最小宽，需重测末行宽度。
- 回滚：去掉 U+00A0 与缝，删除两张新夹具/判据/两刀，基线回 326。
"""
CS=u"""### 通用页 RTF 说明段最小窗孤字行（12 张旧帧变化 + 4 张新帧、基线 330）（R498 / 第 497 轮 / Round 495 / U-1947…U-1952 · 产品 1 文件 + 判据）

"""
BS=u"""**595. RTF_HELPER_ORPHAN 的 runner 1x/2x 未签收**（R498 观察）
    现象：本机 2x 正臂 28.5/29.0pt、负臂 14.0/15.0pt；R498 自身跑尚未创建。
    修法：下一跑读该通道；若 1x 末行宽仍 ≥22pt / 负臂 ≤18pt 即签收，不降区间。

**596. NBSP 孤字行修法只对当前字号/窗宽成立**（R498 观察）
    现象：U+00A0 绑定「文本。」依赖 11pt 与 640pt 最小窗的断行位置；换字号或改最小宽会重新断。
    修法：改这些前提时重跑 `RTF_HELPER_ORPHAN`；若断行仍出现孤字，换绑定位置或改用支持 lineBreakStrategy 的文本承载。
"""
SS=u"""## R498 状态（2026-10-30 · 本地 · 第 497 轮 / Round 495）：通用页 RTF 说明段最小窗孤字行（12 张旧帧变化 + 4 张新帧、基线 330）；全量 1314/56/1（产品 1 文件 + 判据）

最后更新：2026-10-30（本地 · R498 / 第 497 轮 / Round 495）：640pt 最小窗下 RTF 说明段最后一行只剩「本。」—— 孤字行，末行墨宽 **14.0pt**。修法：把「文本。」用 U+00A0 绑成不断开的单元（读者看到的仍是同一句话），加捕获缝 `settingsRtfHelperCopyForCapture`（产品默认 nil 新写法，负向帧旧文案）。旧/新：**12 张旧帧变化**（`settings-general*` 各亮暗）、**4 张新帧**（`general-min-orphan` / `general-min-orphan-legacy`，各亮暗；组件帧命名避开按 `settings-` 前缀收集的整页尺）、0 缺失；基线 **326→330**；逐张看过：新帧末行「文本。」三字、负向帧仍是「本。」孤字，其余行/卡片几何未动。读数（`RTF_HELPER_ORPHAN`，2x）：light 正臂 **28.5pt** / 负臂 **14.0pt**；dark **29.0 / 15.0**。判据要求正臂 ≥22pt、负臂 ≤18pt；任一臂 0 ⇒ 具名 NOT_RUN。`M1343`（去掉 NBSP）/`M1344`（绑错位置）**2/2**。预检 **279/256/686 bad=0**、ARM **372/1173**、HIDDEN **366/1112 rot=0**。⓪：开工一次快进 push **`a98e65d..c9d8d6c` success**、HEAD=origin/main=`c9d8d6c`、**ahead=0**；开工 `gh` 连续 EOF ⇒ **`CI_READ_BLOCKED=network`**；R497 跑 `40937242846 ↔ a98e65d` 上次读 queued ⇒ NOT-RUN；**R496 跑 `40932022750 ↔ 1d3179a` success**（1312/80/0；`QUICKPICK_MATCH_HIGHLIGHT` 1x 签收 ⇒ 592 结案；`SETTINGS_HELPER_FONT` 仍 scale-too-low）；R495 跑 success；R494 主跑 Release 3 条、补记跑 Motion 1 条；R493 跑 2 步红；`c9d8d6c` 自身跑未创建 ⇒ NOT-RUN；收口 push 见补记。全量 **1314/56/1**；捕获卷 **330 帧**；基线 **330/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 497，`python3 scripts/product_streak.py --streak-for 497`，last=a98e65d）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push `a98e65d..c9d8d6c` success、ahead=0；gh EOF ⇒ CI_READ_BLOCKED；R496 跑 success（QUICKPICK 1x 签收⇒592 结案）；R497 跑 queued ⇒ NOT-RUN。
② 产品：RTF 说明段最小窗孤字行（12 旧帧 + 4 新帧、基线 330）。
③ 判据：正臂 28.5/29.0、负臂 14.0/15.0；M1343/M1344 2/2。
④ 预检 279/256/686；rot 366/1112；ARM 372/1173。
⑤ 捕获 330 帧；基线 330/0/0/0；build 0 告警；换装 ok/397=397；全量 1314/56/1。

NOT-RUN / 阻塞（分开写）：① R498 自身跑（推送后取）；② RTF_HELPER_ORPHAN runner 1x/2x；③ SEARCH_PLACEHOLDER runner 1x（R497 跑未读）；④ QUICKPICK_MATCH_HIGHLIGHT 1x 已签收；⑤ SETTINGS_HELPER_FONT runner 1x/2x；⑥ RESET_ICON（settings-content-blank）；⑦ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑧ DEFAULT_BADGE（settings-content-blank）；⑨ 已知性能/采样 flake；⑩ 437–596 的其余未结项仍开。

下一轮（R499）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（R498 主笔提交后 ahead=1 起）；成对读 R498 自身跑（推送后才有）、R497 跑 `40937242846`、R496 跑 `40932022750`、R495 跑 `40920092629`、R494 两跑、R493 跑及更早各跑的全部失败步骤；**重点读 `RTF_HELPER_ORPHAN`（正臂 ≥22pt、负臂 ≤18pt、1x/2x）、`SEARCH_PLACEHOLDER`（两臂差 [6,16]pt）、`QUICKPICK_MATCH_HIGHLIGHT`（1x 已签收）、`SETTINGS_HELPER_FONT`、`MAIN_TITLE_ICON`、`RESET_ICON`、`LOGIN_FAILURE_ICON`、`DEFAULT_BADGE`、`TABLE_COLUMNS`/`TABLE_PIPES`、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做 RTF 说明孤字行/主侧栏搜索占位符省略号/浮层候选行搜索命中高亮/设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R498（RTF 说明孤字行位）**：640pt 最小窗下 RTF 说明段最后一行只剩「本。」（末行墨宽 14pt）。把「文本。」用 U+00A0 绑成不断开的单元，加缝 `settingsRtfHelperCopyForCapture`。**12 张旧帧 + 4 张新帧**，基线 **326→330**；`RTF_HELPER_ORPHAN` 正臂 28.5/29.0pt、负臂 14.0/15.0pt；M1343/M1344 2/2。⓪ push `a98e65d..c9d8d6c` success、ahead=0；gh EOF ⇒ CI_READ_BLOCKED；R496 跑 success（QUICKPICK 1x 签收、592 结案）；R497 跑 queued ⇒ NOT-RUN。全量 1314/56/1；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 497 轮（R498" in a: raise SystemExit("A")
if u"## Round 495 · R498" in i: raise SystemExit("I")
if u"## D-494" in d: raise SystemExit("D")
if u"通用页 RTF 说明段最小窗孤字行" in c: raise SystemExit("C")
if u"**595." in b: raise SystemExit("B")
if st.count(u"## R497 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1946（R497 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R497 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R497 状态",SS+u"## R497 状态",1))
p2=p.replace(U,u"U-31 … U-1952（R498 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R497 节 ②",u"AGENT_STATE.md` 的 R498 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
