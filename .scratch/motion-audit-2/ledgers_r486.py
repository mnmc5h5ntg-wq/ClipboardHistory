#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 484 轮（R485 · 2026-10-29"
AS=u"""## 第 485 轮（R486 · 2026-10-29 · U-1875…U-1880）：设置数据页导出/导入按钮补图标（4 张旧帧变化 + 2 张新帧、基线 306；M1317/M1318 2/2）+ `HEATMAP_TODAY` 1x 具名出口（产品 1 文件 + 判据）

- **U-1875：⓪ push 与 CI。** 开工一次快进 push **`35ad21a..f04eaef` success**、HEAD=origin/main=`f04eaef`、**ahead=0**。R484 跑 `40826572977 ↔ 6454a93` **completed failure 3 步**已读全：Swift 唯一红 `testHeatmapTodaysCellCarriesACornerMarker` 两档 **`HEATMAP_TODAY` 差异像素=0**（1x 设置内容整列平涂，两臂同形）；Capture gate 同一红；Release script 3 条非产品（sources 格×2 + skip roster 嵌套）。R485 跑 `40832860076 ↔ 35ad21a` 读时 **in_progress ⇒ NOT-RUN**（收口 gh EOF，仍未读）。R483 跑 `40821834371 ↔ a59956c` 唯一红＝Release 3 条非产品；R481 跑签收 ROW_LINK_BADGE 19/18、Capture 红 0；R480 `60d65a4` 无跑；R478 主跑冲突红/补记跑 success；R477 两跑冲突红；R479 沿用；436 无新跑。
- **U-1876：① 腐烂与预检。** `HIDDEN_ARMS 表=354 可判=1089 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=267 covered=244 arms=662 bad=0`（新表登记；M1317/M1318 两针静态可判）、`ARM_TOTAL files=360 arms=1150`。
- **U-1877：② 产品：设置数据页导出/导入补图标。** 缺陷形状（`settings-data` 直看）：同一组数据动作里，清空已有垃圾桶图标，导出/导入却还是纯文字 —— 三颗按钮的图标语言分裂。修法：两颗按钮改用 `Label` + `square.and.arrow.up` / `square.and.arrow.down`，标签一字不改；加捕获缝 `settingsDataActionIconsForCapture`（产品默认 nil 画图标）。旧/新：**4 张旧帧变化**（`settings-data` 与 `settings-data-no-title-icon` 各亮暗）+ **2 张新帧**（`settings-data-no-action-icons` 亮暗）、0 缺失；基线 **304→306**；逐张看过：图标在标签左、清空/卡片几何未动。读数（`DATA_ACTION_ICONS`，2x）：light 按钮行末列 **698→788（右伸 90px=45pt）**、墨 **2020→2499（+479）**、导出差 **+240**、导入差 **+239**；dark 末列同、墨 **2261→2738（+477）**、导出差 **+239**、导入差 **+238**。
- **U-1878：③ 判据与刀。** 新判据 `testDataPageExportImportButtonsCarryIcons` 用成对帧**按每颗按钮自己的窗**读墨（0.24..0.39 / 0.39..0.56）：按钮内容居中，图标只把文字往右推、左沿不动 ⇒ 第一版按左沿写实测 −2px 当场红，改成两窗墨差。刀 `M1317`（撤导出图标）/`M1318`（撤导入图标）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。**同轮修 `HEATMAP_TODAY` 的 runner 1x 出口**：R484 跑两档差异 0 像素是"设置内容整列平涂"；加内容墨证人（热图区 <50·s² ⇒ 具名 `HEATMAP_TODAY_NOT_RUN=settings-content-blank` 并 skip），本机 2x 仍判 60 像素、内容墨 33627。
- **U-1879：④ 既有面。** 数据页其它卡片、清空按钮、设置标题图标、隐私/快捷键/统计页均未动；`settings-data-no-title-icon` 的变化只来自导出/导入图标；旧帧 0 缺失。
- **U-1880：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **306 帧**、`CHANGED=4 ADDED=2 MISSING=0`，更新后 `306/0/0/0`；全量 **1302/56/0**（476.3s，轻载；新增 1 条判据）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 485，`python3 scripts/product_streak.py --streak-for 485`，last=35ad21a）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R485 跑（gh EOF 未读）；② `DATA_ACTION_ICONS` 的 runner 1x/dark（设置内容平涂时预期 NOT_RUN）；③ `QUICKPICK_FAVORITE` 的 runner 1x/dark；④ `HEATMAP_TODAY` 的 runner 1x 修复复验；⑤ `CLEAR_LABEL`/`ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突复核；⑥ `SETTINGS_DATA_PATH`；⑦ 既有 runner 复核；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 采样红；⑩ 437–572 的其余未结项仍开。

"""
IS=u"""## Round 483 · R486（第 485 轮 · 2026-10-29）：数据页导出/导入补图标（4 旧帧 + 2 新帧、基线 306）

同一组数据动作里清空有垃圾桶、导出/导入还是纯文字。两颗按钮改用 Label + square.and.arrow.up/down，标签不改；加捕获缝。4 张旧帧变化 + 2 张新帧，基线 304→306；`DATA_ACTION_ICONS` light 末列 698→788（右伸 90px）、墨 2020→2499（+479）、导出差 +240/导入差 +239；dark 2261→2738（+477）、+239/+238；按每颗按钮自己的窗读墨。M1317/M1318 2/2。同轮修 `HEATMAP_TODAY` 的 runner 1x 出口：R484 跑两档 0 像素是设置内容平涂 ⇒ 加内容墨证人并具名 NOT_RUN。预检 267/244/662、rot 354/1089、ARM 360/1150。全量 1302/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ push 35ad21a..f04eaef success、ahead=0；R484 跑三朵红已读清；R485 跑未读 ⇒ NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 修前 settings-data 与修后 4 张旧帧 + 2 张负向帧逐张看过：图标在标签左、清空/卡片几何未动。 |
| 判据有效性 | 15/15 | 按每颗按钮自己的窗读墨（导出差 +240/导入差 +239）；M1317/M1318 2/2。 |
| 假绿防御 | 14/15 | 左沿第一版 −2px 当场红并改对；HEATMAP 1x 平涂补 NOT_RUN；扣 1：R485 跑未读。 |
| 产品面推进 | 15/15 | 新类别（数据页导出/导入图标）；1 个产品文件；4 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1875…U-1880、D-482、306 帧/1302、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | runner 1x 平涂预期 NOT_RUN 已写明；R485 跑未读不冒充绿。 |
| 可复核性 | 15/15 | 698→788、2020→2499、+240/+239、M1317/M1318、precheck 267/244/662、基线 306 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-482 数据页导出/导入补图标；两枚图标分窗判墨（R486）

- 背景：同一组数据动作里清空已有垃圾桶图标，导出/导入还是纯文字，三颗按钮的图标语言分裂。
- 决定：导出/导入改用 `Label` + `square.and.arrow.up` / `square.and.arrow.down`，标签一字不改；加捕获缝 `settingsDataActionIconsForCapture`（产品默认 nil 画图标）。
- 理由：同一动作组的图标语言要一致；按钮内容居中，图标只把文字往右推，不能按左沿判，改为按每颗按钮自己的窗读墨。
- 兼容性/迁移：4 张旧帧变化 + 2 张新帧，基线 304→306；清空按钮与卡片几何未动。
- 边界：runner 1x 设置内容平涂时两窗都无墨 ⇒ 具名 `DATA_ACTION_ICONS_NOT_RUN=settings-content-blank`，不降地板。
- 回滚：删两枚 Label 图标/捕获缝/新帧与判据。
"""
CS=u"""### 设置数据页导出/导入补图标（4 张旧帧变化 + 2 张新帧、基线 306）（R486 / 第 485 轮 / Round 483 / U-1875…U-1880 · 产品 1 文件 + 判据）

"""
BS=u"""**571. DATA_ACTION_ICONS 的 runner 1x/dark 未签收**（R486 观察）
    现象：本机 2x 两窗墨差 +240/+239；runner 1x 设置内容整列平涂时两窗都无墨（预期 NOT_RUN），未读。
    修法：下一跑读 `DATA_ACTION_ICONS` 两档；若 1x 有内容但墨差低于 20·s²，先查捕获通道，不降地板。

**572. HEATMAP_TODAY 的 1x NOT_RUN 出口未在 runner 上复验**（R486 观察）
    现象：R484 跑两档差异 0 像素（设置内容平涂）被判红；本轮加内容墨证人 + 具名 NOT_RUN，但只在本机 2x 验过。
    修法：下一跑读 `HEATMAP_TODAY_NOT_RUN=settings-content-blank` 是否出现；本机 2x 仍须是 60 像素。
"""
SS=u"""## R486 状态（2026-10-29 · 本地 · 第 485 轮 / Round 483）：设置数据页导出/导入按钮补图标（4 张旧帧变化 + 2 张新帧、基线 306）；全量 1302/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R486 / 第 485 轮 / Round 483）：同一组数据动作里，清空已有垃圾桶图标，导出/导入却还是纯文字 —— 三颗按钮的图标语言分裂。修法：两颗按钮改用 `Label` + `square.and.arrow.up` / `square.and.arrow.down`（标签一字不改），加捕获缝 `settingsDataActionIconsForCapture`（产品默认 nil 画图标）。旧/新：**4 张旧帧变化**（settings-data 与 settings-data-no-title-icon 各亮暗）+ **2 张新帧**（settings-data-no-action-icons 亮暗）、0 缺失；基线 **304→306**；逐张看过：图标在标签左、清空/卡片几何未动。读数（`DATA_ACTION_ICONS`，2x）：light 按钮行末列 **698→788（右伸 90px=45pt）**、墨 **2020→2499（+479）**、导出差 **+240**、导入差 **+239**；dark 墨 **2261→2738（+477）**、导出差 **+239**、导入差 **+238**。新判据按每颗按钮自己的窗读墨；`M1317`（撤导出图标）/`M1318`（撤导入图标）**2/2**。同轮修 `HEATMAP_TODAY` 的 runner 1x 出口：R484 跑两档差异 0 像素是设置内容整列平涂，加内容墨证人（<50·s² ⇒ 具名 `HEATMAP_TODAY_NOT_RUN=settings-content-blank` 并 skip），本机 2x 仍判 60 像素、内容墨 33627。预检 **267/244/662 bad=0**、ARM **360/1150**、HIDDEN **354/1089 rot=0**。⓪：开工一次快进 push **`35ad21a..f04eaef` success**、HEAD=origin/main=`f04eaef`、**ahead=0**；R484 跑 `40826572977 ↔ 6454a93` completed failure 3 步已读清（Swift/Capture 同一 HEATMAP_TODAY 红 0 像素；Release 3 条非产品）；R485 跑 `40832860076 ↔ 35ad21a` 读时 in_progress、收口 gh EOF ⇒ NOT-RUN；R483/R481/R480/R478/R477/R479 沿用；436 无新跑。全量 **1302/56/0**（476.3s，轻载）；捕获卷 **306 帧**；基线 **306/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 485，`python3 scripts/product_streak.py --streak-for 485`，last=35ad21a）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ push 35ad21a..f04eaef success、ahead=0；R484 跑三朵红已读清；R485 跑未读 ⇒ NOT-RUN。
② 产品：数据页导出/导入补图标（4 旧帧 + 2 新帧、基线 306）。
③ 判据：两窗墨差 +240/+239；M1317/M1318 2/2；HEATMAP 1x 补具名 NOT_RUN。
④ 预检 267/244/662；rot 354/1089；ARM 360/1150。
⑤ 捕获 306 帧；基线 306/0/0/0；build 0 告警；换装 ok/397=397；全量 1302/56/0。

NOT-RUN / 阻塞（分开写）：① R485 跑（gh EOF 未读）；② DATA_ACTION_ICONS runner 1x/dark；③ QUICKPICK_FAVORITE runner 1x/dark；④ HEATMAP_TODAY 的 1x 修复复验；⑤ CLEAR_LABEL/ROW_LINK_BADGE/标题图标/兜底路径/inline/幻影/图钉/冲突复核；⑥ SETTINGS_DATA_PATH；⑦ 既有 runner 复核；⑧ Capture MATERIAL_BLIND_NOT_RUN；⑨ 已知 Motion 采样红；⑩ 437–572 的其余未结项仍开。

下一轮（R487）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R486 自身跑、R485 跑 `40832860076`、R484 跑 `40826572977`、R483 跑 `40821834371`、R481 跑 `40812979165`、R480（`60d65a4` 无跑）、R478 两跑 `40801850707`/`40802042660`、R477 两跑 `40797827495`/`40797866181`、R479 跑 `40805576917` 的全部失败步骤（R483 唯一红是 Release script 3 条非产品；R477/R478 冲突 `0≠2` 已由 `7f21720` 跑 success 签收）；**重点读 `DATA_ACTION_ICONS`（两窗各 ≥20·s²、1x/dark）、`QUICKPICK_FAVORITE`（≥8·s²、首墨行上移 ≥2·s）、`HEATMAP_TODAY(_NOT_RUN)`、`CLEAR_LABEL`、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：ROW_OCR/ROW_RICH、QUICKPICK_LIST_RULE、SETTINGS_DATA_PATH、TRUNCATION_NOTE、QUICKPICK_SOURCE_ICON、CROSS_YEAR/MAIN_ROWS、SETTINGS_HELPER_AXIS、CARD_INSET_CONTROL_FIRST、VIDEO_*、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做数据页导出/导入图标/浮层候选行收藏星标/热图今天角标/清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R486（数据页导出/导入图标位）**：同一组数据动作里清空有垃圾桶、导出/导入还是纯文字。两颗按钮改用 Label + square.and.arrow.up/down，标签一字不改；加捕获缝。**4 张旧帧变化 + 2 张新帧**，基线 **304→306**；`DATA_ACTION_ICONS` light 末列 698→788（右伸 90px）、墨 2020→2499（+479）、导出差 +240/导入差 +239；dark 2261→2738（+477）、+239/+238；按每颗按钮自己的窗读墨；M1317/M1318 **2/2**。同轮修 `HEATMAP_TODAY` 的 runner 1x 出口（R484 跑两档 0 像素是设置内容平涂 ⇒ 内容墨证人 + 具名 NOT_RUN）。⓪ push 35ad21a..f04eaef success、ahead=0；R484 跑三朵红已读清；R485 跑未读 ⇒ NOT-RUN。全量 **1302/56/0**（476.3s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 485 轮（R486" in a: raise SystemExit("A")
if u"## Round 483 · R486" in i: raise SystemExit("I")
if u"## D-482" in d: raise SystemExit("D")
if u"设置数据页导出/导入补图标" in c: raise SystemExit("C")
if u"**571." in b: raise SystemExit("B")
if st.count(u"## R485 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1874（R485 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R485 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R485 状态",SS+u"## R485 状态",1))
p2=p.replace(U,u"U-31 … U-1880（R486 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R485 节 ②",u"AGENT_STATE.md` 的 R486 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
