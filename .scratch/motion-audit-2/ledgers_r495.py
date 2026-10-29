#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 493 轮（R494 · 2026-10-29"
AS=u"""## 第 494 轮（R495 · 2026-10-30 · U-1929…U-1934）：设置通用页说明统一到 11pt 下限（14 张旧帧变化 + 2 张新帧、基线 322；M1337/M1338 2/2）（产品 2 文件 + 判据）

- **U-1929：⓪ push 与 CI。** 开工 `git push` no-op（Everything up-to-date）、HEAD=origin/main=`e05b13c`、**ahead=0**。开工现读：R494 补记跑 `40896245079 ↔ e05b13c` **in_progress ⇒ NOT-RUN**；R494 主跑 `40895877246 ↔ 590ead8` 读时未完成（`STEP[9] Release script tests` 已红、其余步空）⇒ **NOT-RUN**。R493 跑 `40887758385 ↔ 67cb683` **failure 2 步**：`STEP[9] Release script tests` = 3 条非产品红（sources 格主笔跑未派生 ×2 + skip roster 嵌套无汇总行；`Ran 683 / FAILED 3, skipped 2`）、`STEP[15] Swift tests` = 1 条采样红 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime`（`Executed 1309/79 skip/1 failure`；同跑 `RESET_ICON_NOT_RUN=settings-content-blank` 两档具名）。旧跑按 `ci_read.py steps` 成对复核失败步名：R492 主跑 `40880105650 ↔ a90b074` = STEP[9]+STEP[19] Motion、补记跑 `40880472552 ↔ e754cf7` = STEP[19]；R491 主跑 `40868743008 ↔ 83e2087` = STEP[9]+STEP[19]、补记跑 `40868988761 ↔ ebc64aa` success；R490 主跑 `40865789755 ↔ c0c08c7` = STEP[9]、补记跑 `40866154839 ↔ 9f987c7` success；R489 主跑 `40858253532 ↔ d8b0712` = STEP[9]、补记跑 `40861168233 ↔ 3d4a03a` success；R488 主跑 `40851078685 ↔ 9487c0f` = STEP[9]+STEP[19]、补记跑 `40851311888 ↔ 2cafe1b` success；R487 `40845483735 ↔ 519b22b` success；R486 主跑 `40836764232 ↔ dfbf6f6` = STEP[9]、补记跑 `40837020563 ↔ 04cc517` success；R485 `40832860076 ↔ 35ad21a` 4 步、R484 `40826572977 ↔ 6454a93` 3 步、R483 `40821834371 ↔ a59956c` 1 步、R481 `40812979165 ↔ 2770bfe` 1 步、R480 `60d65a4` 无跑、R478 主跑 `40801850707 ↔ b64682e` 3 步 / 补记跑 `40802042660 ↔ 7f21720` success、R477 主跑 `40797827495 ↔ 0fd3ec0` 4 步 / 补记跑 `40797866181 ↔ 7a79987` 2 步、R479 `40805576917 ↔ 225e6f8` 3 步。收口时 `gh` 读 `api.github.com` 连续 **EOF** ⇒ **`CI_READ_BLOCKED=network`**（R494 两跑与 R495 自身跑均未读到结论；收口 push 见补记）。436 沿用 R481 跑 `judged=5/5 executed=77 reds=0`。
- **U-1930：① 腐烂与预检。** `HIDDEN_ARMS 表=363 可判=1106 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=276 covered=253 arms=680 bad=0`（新表 `mutate_r495_helper_font` 登记）、`ARM_TOTAL files=369 arms=1167`。**重锚四张旧表并复跑**：R494 `M1335` 改指 `historyStore.selectedCount <= 1` 新条件 ⇒ **2/2**；R29d `M132` 名单行加新帧、`M134` 期望改「落在错误一侧」⇒ **4/4**，`M133`（缩框）在现行守卫下走具名 NOT_RUN、改扩框也改不动被判量（框被侧栏视图裁剪）⇒ **退役具名**（空刀不凑数）；R39 `M177` 回执块字体行改为 `settingsHelperFont` ⇒ **8/8**；R33 `M141` 探针框从 y=200 改到 218.5、`M142/M143/M145` 的 CAPTION/OCR 常量改 `settingsHelperFont` ⇒ **7/7**。四张表 `RESTORE_CLEAN=yes`。
- **U-1931：② 产品：设置通用页说明统一到 11pt 下限。** 缺陷形状（`settings-general` 直看 + 量帧）：同一页四条说明，回执/暂停/OCR 三条是 `.caption`（10pt），最长那条 RTF 是 `VisualFont.meta`（11pt）—— 同一页、同一角色两种字号，而 `VisualFont.meta` 的注释写明 **11 是 App 的下限**（再小暗档 `.secondary` 会糊）。修法：三条改用 `settingsHelperFont`（默认 `VisualFont.meta`=11；捕获缝 `settingsHelperFontForCapture=false` 退回 10pt 作负向臂），RTF 保持 11。旧/新：**14 张旧帧变化**（10 张 `settings-general*` + 4 张 `sidebar-multi-select*`，见 U-1933）、**2 张新帧**（`settings-general-legacy-helper-font` 亮暗）、0 缺失；基线 **320→322**；逐张看过：四条说明同字号、暂停说明在 720pt 折成两行、卡片长高未压底、回执图标与红字同轴、负向帧仍是 10/11 混用。
- **U-1932：③ 判据与刀。** 新判据 `testSettingsHelperFontsShareOneSize` 按块内/块间行距分块，读每条说明的墨带高度：`SETTINGS_HELPER_FONT` light 正臂 **5 带 11.0/10.5/11.0/11.0/11.0（极差 0.5）**、负臂 **4 带 10.0/10.0/11.0/11.0（极差 1.0）**；dark 正臂 **11.5/11.0/11.5/11.5/11.5（极差 0.5）**、负臂 **10.0/10.0/11.5/11.5（极差 1.5）**（2x）。判据要求：正臂最低 ≥10.4pt、正臂极差 ≤0.6、负臂极差 ≥0.8（尺必须分得出 10 与 11）；两臂说明带不足 3 条 ⇒ `SETTINGS_HELPER_FONT_NOT_RUN=settings-content-blank`，倍率 <1.5 ⇒ `NOT_RUN=scale-too-low`。刀 `M1337`（字体永远退回 10）/`M1338`（OCR 说明单独 14pt）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1933：④ 既有面与回归修复。** R494 的标题图标在 250pt 批量态把「已选 3 条」挤成「已选…」（R494/R493 两张成对帧可见）⇒ 图标只在 `selectedCount <= 1` 时画：批量态标题是状态不是应用名，250pt 下完整文案恢复（`sidebar-multi-select-min` 四档帧）。**该格没有稳定的像素判据**（图标墨与省略号墨在固定窗里互相抵消），以成对帧作证并登记 BACKLOG 589。caption-tier 三条探针按新带重锚（暂停 y=160→163、OCR y=200→218.5、RTF y=241→260），`CAPTION_HUG`/`SETTINGS_HELPER_AXIS 200/198/−2`/`CARD_INSET_*` 全绿；新帧补进 `CARD_INSET_CONTROL_FIRST`（+2.5/+3.0）与系统黑带名册。表格/浮层/主列表/视频面未动。
- **U-1934：⑤ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh` arm64 冷编 + x86_64）；捕获卷 **322 帧**、`CHANGED=14 ADDED=2 MISSING=0`，更新后 `322/0/0/0`；全量 **1311/56/0**（828.6s，轻载）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 494，`python3 scripts/product_streak.py --streak-for 494`，last=590ead8）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。收口 push 与 R495 自身跑状态见补记。**具名 NOT-RUN**：① R495 自身跑（推送后取，`CI_READ_BLOCKED=network`）；② R494 两跑（in_progress/读不到）；③ `SETTINGS_HELPER_FONT` runner 1x/2x；④ 其余 runner 复核（网络 EOF）；⑤ `RESET_ICON` runner 仍 `settings-content-blank` 两档；⑥ `LOGIN_FAILURE_ICON` 1x（no-red-channel）；⑦ `DEFAULT_BADGE`（settings-content-blank）；⑧ 批量态标题完整性无像素判据（BACKLOG 589）；⑨ 已知 Motion/采样红；⑩ 437–590 的其余未结项仍开。

"""
IS=u"""## Round 492 · R495（第 494 轮 · 2026-10-30）：通用页说明统一 11pt（14 旧帧 + 2 新帧、基线 322）

同一页四条说明：回执/暂停/OCR 是 10pt `.caption`，RTF 是 11pt `meta`，而 11 是 App 下限。三条改 `settingsHelperFont`（默认 meta=11，缝 false=10 作负向臂），RTF 保持 11。14 张旧帧变化 + 2 张新帧，基线 320→322；`SETTINGS_HELPER_FONT` light 正臂极差 0.5 / 负臂 1.0、dark 0.5 / 1.5；M1337/M1338 2/2。同时修 R494 批量态标题图标挤占（250pt 恢复「已选 3 条」）。重锚 M1335/M132/M177/M141 并复跑 R494 2/2、R29d 4/4（M133 退役）、R39 8/8、R33 7/7。预检 276/253/680、rot 363/1106、ARM 369/1167。全量 1311/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push no-op、ahead=0；R493 跑 2 步红（Release 3 条 + 采样 1 条）；R494 两跑 NOT-RUN；收口 `CI_READ_BLOCKED=network`。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 14 张旧帧 + 2 张新帧逐张看过：同字号、暂停折行、卡片未压底、负向臂 10/11 混用；250pt 批量态完整文案。 |
| 判据有效性 | 15/15 | 正臂极差 0.5、负臂 1.0/1.5；M1337/M1338 2/2。 |
| 假绿防御 | 14/15 | 负臂必须分得出 10/11；内容空/倍率低有具名 NOT_RUN；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（通用页说明字号统一）+ 回归修复；2 个产品文件；14 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1929…U-1934、D-491、322 帧/1311、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | R493 两步红原样登记；R494 两跑/自身跑具名 NOT-RUN；批量态无像素判据具名入 BACKLOG。 |
| 可复核性 | 15/15 | 极差 0.5/1.0/1.5、四张旧表复跑、precheck 276/253/680、基线 322 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-491 设置通用页说明统一 11pt；批量态标题图标只在非批量画（R495）

- 背景：同一页四条说明里三条 10pt `.caption`、最长一条 11pt `meta`；`VisualFont.meta` 注释写明 11 是 App 下限。R494 的标题图标在 250pt 批量态把「已选 3 条」挤成「已选…」。
- 决定：三条说明改用 `settingsHelperFont`（默认 `VisualFont.meta`=11，捕获缝 false 退回 10 作负向臂），RTF 保持 11；`HistorySidebarView.header` 只在 `selectedCount <= 1` 时画标题图标。
- 理由：同页同角色同字号；11pt 是可读下限；批量态标题是状态不是应用名，图标语义不对且挤占最小窗。
- 兼容性/迁移：14 张旧帧变化 + 2 张新帧，基线 320→322；暂停说明在 720pt 折成两行，卡片长高由卡片留白吸收；caption-tier 三条探针按新带重锚。
- 边界：runner 1x/2x 未读；批量态标题完整性没有稳定像素判据（BACKLOG 589）。
- 回滚：三条 `settingsHelperFont` 改回 `.caption`、RTF 不变；标题图标恢复无条件；删缝/新帧/判据/两刀，基线回 320。
"""
CS=u"""### 设置通用页说明统一到 11pt 下限（14 张旧帧变化 + 2 张新帧、基线 322）（R495 / 第 494 轮 / Round 492 / U-1929…U-1934 · 产品 2 文件 + 判据）

"""
BS=u"""**589. 批量态标题完整性没有稳定像素判据**（R495 观察）
    现象：250pt 批量态修复前后，标题窗里图标墨与省略号墨几乎抵消（ink 3195 vs 3324），右缘也被省略号占住；只能靠成对帧人看。
    修法：若要自动化，需从视图树取 SwiftUI Text 的整定宽度或读 AX 值；先不加判据。

**590. R29d 的 M133（缩框）退役**（R495 观察）
    现象：现行守卫在框压不住字时走具名 NOT_RUN（不是静默绿）；缩框/扩框都改不动 roster 判定（框被侧栏视图裁剪）⇒ 这一臂已无法咬。
    修法：按"空刀不凑数"退役，保留 TEXT_SIDE_CAPABILITY 与 NOT_RUN 出口接管其职责；若将来守卫改回静默绿，重开。
"""
SS=u"""## R495 状态（2026-10-30 · 本地 · 第 494 轮 / Round 492）：设置通用页说明统一到 11pt 下限（14 张旧帧变化 + 2 张新帧、基线 322）；全量 1311/56/0（产品 2 文件 + 判据）

最后更新：2026-10-30（本地 · R495 / 第 494 轮 / Round 492）：同一页四条说明，回执/暂停/OCR 用 10pt `.caption`、最长 RTF 用 11pt `meta`，而 `VisualFont.meta` 注释写明 11 是 App 下限 —— 同页同角色两种字号。修法：三条改用 `settingsHelperFont`（默认 `VisualFont.meta`=11；捕获缝 `settingsHelperFontForCapture=false` 退回 10 作负向臂），RTF 保持 11。旧/新：**14 张旧帧变化**（10 张 `settings-general*` + 4 张 `sidebar-multi-select*`）、**2 张新帧**（`settings-general-legacy-helper-font` 亮暗）、0 缺失；基线 **320→322**；逐张看过：四条说明同字号、暂停说明 720pt 折两行、卡片长高未压底、回执红字与图标同轴、负向帧仍 10/11 混用。读数（`SETTINGS_HELPER_FONT`，2x）：light 正臂 5 带 **11.0/10.5/11.0/11.0/11.0（极差 0.5）**、负臂 4 带 **10.0/10.0/11.0/11.0（极差 1.0）**；dark 正臂 **11.5/11.0/11.5/11.5/11.5（0.5）**、负臂 **10.0/10.0/11.5/11.5（1.5）**。判据要求正臂最低 ≥10.4、正臂极差 ≤0.6、负臂极差 ≥0.8；两臂说明带不足 3 条或倍率 <1.5 都有具名 NOT_RUN。`M1337`（永远 10）/`M1338`（OCR 14pt）**2/2**。**修 R494 回归**：标题图标只在 `selectedCount <= 1` 时画，250pt 批量态「已选 3 条」恢复完整（成对帧；无像素判据，见 BACKLOG 589）。**重锚四张旧表并复跑**：R494 M1335 ⇒ 2/2；R29d M132 名单 + M134 期望 ⇒ 4/4（M133 缩框退役具名）；R39 M177 ⇒ 8/8；R33 M141 + CAPTION/OCR 常量 ⇒ 7/7；均 `RESTORE_CLEAN=yes`。caption-tier 三条探针按新带重锚（160→163 / 200→218.5 / 241→260），`CAPTION_HUG`、`SETTINGS_HELPER_AXIS 200/198/−2`、`CARD_INSET_*` 全绿；新帧补进 control-first 与系统黑带名册。预检 **276/253/680 bad=0**、ARM **369/1167**、HIDDEN **363/1106 rot=0**。⓪：开工 push no-op、HEAD=origin/main=`e05b13c`、**ahead=0**；开工现读 R494 补记跑 `40896245079 ↔ e05b13c` **in_progress**、R494 主跑 `40895877246 ↔ 590ead8` 未完成（STEP[9] 已红）⇒ 均 **NOT-RUN**；R493 跑 `40887758385 ↔ 67cb683` failure 2 步（Release 3 条非产品 + Swift 采样红 1 条；`RESET_ICON_NOT_RUN=settings-content-blank`）；旧跑成对失败步名按 `ci_read.py steps` 复核（R492/R491/R490/R489/R488/R487/R486/R485/R484/R483/R481/R480/R478/R477/R479）；收口 `gh` 连续 EOF ⇒ **`CI_READ_BLOCKED=network`**；收口 push 见补记。全量 **1311/56/0**（828.6s，轻载）；捕获卷 **322 帧**；基线 **322/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 494，`python3 scripts/product_streak.py --streak-for 494`，last=590ead8）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push no-op、ahead=0；R493 跑 2 步红；R494 两跑 NOT-RUN；旧跑失败步名复核；收口 CI_READ_BLOCKED=network。
② 产品：通用页说明统一 11pt（14 旧帧 + 2 新帧、基线 322）+ 修 R494 批量态标题图标挤占。
③ 判据：正臂极差 0.5、负臂 1.0/1.5；M1337/M1338 2/2；四张旧表重锚复跑。
④ 预检 276/253/680；rot 363/1106；ARM 369/1167。
⑤ 捕获 322 帧；基线 322/0/0/0；build 0 告警；换装 ok/397=397；全量 1311/56/0。

NOT-RUN / 阻塞（分开写）：① R495 自身跑（推送后取，CI_READ_BLOCKED=network）；② R494 两跑（in_progress/读不到）；③ SETTINGS_HELPER_FONT runner 1x/2x；④ 其余 runner 复核（网络 EOF）；⑤ RESET_ICON runner 仍 settings-content-blank 两档；⑥ LOGIN_FAILURE_ICON 1x（no-red-channel）；⑦ DEFAULT_BADGE（settings-content-blank）；⑧ 批量态标题完整性无像素判据（BACKLOG 589）；⑨ 已知 Motion/采样红；⑩ 437–590 的其余未结项仍开。

下一轮（R496）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0（开工 HEAD=`e05b13c`、ahead=0；R495 主笔提交后 ahead=1 起）；成对读 R495 自身跑（推送后才有）、R494 两跑（`40895877246`/`40896245079`）、R493 跑 `40887758385`、R492 两跑、R491 两跑、R490 两跑、R489 两跑、R488 两跑、R487 跑、R486 两跑、R485 跑、R484 跑、R483 跑、R481 跑、R480（`60d65a4` 无跑）、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `SETTINGS_HELPER_FONT`（正臂极差 ≤0.6、负臂 ≥0.8、1x/2x）、`MAIN_TITLE_ICON`（墨差 ≥40·s²、1x/2x）、`RESET_ICON`（右列墨差、1x/dark）、`LOGIN_FAILURE_ICON`（no-red-channel）、`QUICKPICK_CONTENT_BADGE`、`HISTORY_SOURCE_ICON`、`DEFAULT_BADGE`（runner 仍 NOT_RUN=settings-content-blank）、`TABLE_COLUMNS`/`TABLE_PIPES`、`DATA_ACTION_ICONS(_NOT_RUN)`、`QUICKPICK_FAVORITE`、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`（4.5 不动）、`QUICKPICK_GREY_BAND`（150 不动）、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做设置通用页说明字号/主侧栏标题图标/恢复默认按钮图标/登录失败回执图标/浮层候选行内容标记/主列表来源图标/默认排除项标记/表格列宽/Markdown 表格竖线/数据页导出导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R495（通用页说明字号位）**：回执/暂停/OCR 三条 10pt `.caption`、RTF 11pt `meta`，同页同角色两种字号。三条改 `settingsHelperFont`（默认 11，缝 false=10），RTF 保持 11；并修 R494 批量态标题图标挤占（250pt 恢复「已选 3 条」）。**14 张旧帧 + 2 张新帧**，基线 **320→322**；`SETTINGS_HELPER_FONT` 正臂极差 0.5、负臂 1.0/1.5；M1337/M1338 2/2；重锚 M1335/M132/M177/M141 ⇒ R494 2/2、R29d 4/4（M133 退役）、R39 8/8、R33 7/7。⓪ push no-op、ahead=0；R493 跑 2 步红；R494 两跑 NOT-RUN；收口 CI_READ_BLOCKED=network。全量 1311/56/0；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 494 轮（R495" in a: raise SystemExit("A")
if u"## Round 492 · R495" in i: raise SystemExit("I")
if u"## D-491" in d: raise SystemExit("D")
if u"设置通用页说明统一到 11pt 下限" in c: raise SystemExit("C")
if u"**589." in b: raise SystemExit("B")
if st.count(u"## R494 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1928（R494 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R494 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R494 状态",SS+u"## R494 状态",1))
p2=p.replace(U,u"U-31 … U-1934（R495 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R494 节 ②",u"AGENT_STATE.md` 的 R495 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
