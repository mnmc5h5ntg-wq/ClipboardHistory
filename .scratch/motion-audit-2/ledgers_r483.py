#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 480 轮（R481 · 2026-10-29"
AS=u"""## 第 481 轮（R483 · 2026-10-29 · U-1857…U-1862）：设置数据页清空按钮补垃圾桶图标（4 张旧帧变化、基线 300；M1311/M1312 2/2）（产品 1 文件 + 判据）

- **U-1857：⓪ push 与 CI。** 开工两次 `git push` 均报 `Please make sure you have the correct access rights and the repository exists.`、`gh` 不可达 ⇒ **`PUSH_BLOCKED=network`（HEAD=`54af93a`、ahead=0）**、**`CI_READ_BLOCKED=network`**；R481 跑 `40812979165 ↔ 2770bfe`、R480 跑、R478 两跑 `40801850707`/`40802042660`、R477 两跑等**均未读到 ⇒ NOT-RUN**；R479 跑的签收读数沿用 R481 账（FALLBACK_PATH 113、INLINE 99/6.0 与 102/5.0、幻影 0、图钉 +20）。436 无新跑。
- **U-1858：① 腐烂与预检。** `HIDDEN_ARMS 表=351 可判=1083 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=264 covered=243 arms=660 bad=0`、`ARM_TOTAL files=357 arms=1145`。
- **U-1859：② 产品：设置数据页清空按钮补垃圾桶图标。** 缺陷形状（`settings-data` 直看）：主窗口批量栏/详情浮层都用垃圾桶说破坏性动作，设置数据页这颗「清空」只有文字；而夹具又注入 `clearHistoryAction: nil`，基线钉住的是用户永远看不到的禁用灰态。修法：Sources 把按钮改成 `Label("清空", systemImage:"trash")`（**标签仍保持「清空」**——旧契约 `testSettingsClearButtonUsesShortDestructiveLabel` 钉着短标签，不改旧期望）；夹具注入非 nil 回执，让启用的售出态进帧。旧/新：**4 张旧帧变化**（settings-data 与 settings-data-no-title-icon 各亮暗）、0 新增/缺失；基线 **300/0/0/0**；逐张看过：垃圾桶在标签左、按钮未压卡片。读数（`CLEAR_LABEL`）：标签墨宽 light **46.0pt**、dark **46.5pt**（旧「清空」文字约 33pt）；**启用红态在离屏 `.borderedProminent` 无彩色通道（红像素 0）⇒ 具名 NOT-RUN，不拿颜色当证人**。
- **U-1860：③ 判据与刀。** 新判据 `testClearHistoryButtonCarriesItsFullDestructiveLabel` 读右下角按钮标签的墨宽（阈值 45pt；内容平涂时打 `CLEAR_LABEL_NOT_RUN` 并 skip）。刀 `M1311`（Label→Text）/`M1312`（labelStyle titleOnly）**2/2 CAUGHT**。第一版把标签改成「清空未收藏」（85.5pt），被旧契约测试当场红 ⇒ **撤回长标签、保留短标签+图标**，不改旧期望。
- **U-1861：④ 既有面。** 既有 `testSettingsClearButtonUsesShortDestructiveLabel` 保持绿；settings-data 的卡片节奏/标题图标/路径行未因按钮变宽而溢出。启用红态的像素通道具名 NOT-RUN。
- **U-1862：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **300 帧**、`CHANGED=4 ADDED=0 MISSING=0`，更新后 `300/0/0/0`；全量 **1299/56/0**（489.7s，轻载；首遍长标签被旧契约红 1 条，撤回后干净）；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 481，`python3 scripts/product_streak.py --streak-for 481`，last=2770bfe）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R481/R480/R478/R477 的跑（CI_READ_BLOCKED）；② 清空按钮启用红态（离屏无彩色通道）；③ 垃圾桶图标的 runner 1x/dark；④ `ROW_LINK_BADGE`/`SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/inline/幻影/图钉/冲突的 runner 复核；⑤ `SETTINGS_DATA_PATH`；⑥ 既有 runner 复核；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–566 的其余未结项仍开。

"""
IS=u"""## Round 479 · R483（第 481 轮 · 2026-10-29）：设置数据页清空按钮补垃圾桶图标（4 张旧帧变化、基线 300）

主窗口/详情浮层用垃圾桶说破坏性动作，设置数据页的「清空」只有文字；夹具又注入 nil，基线钉住禁用灰态。Sources 把按钮改成 `Label("清空", systemImage:"trash")`（**标签保持「清空」**，旧契约钉着短标签，不改期望）；夹具注入非 nil 回执让启用态进帧。4 张旧帧变化、0 新增，基线 300/0/0/0；`CLEAR_LABEL` 标签墨宽 46.0/46.5pt（旧文字约 33pt）；M1311/M1312 2/2。第一版长标签「清空未收藏」被旧契约当场红 ⇒ 撤回，不改旧期望；启用红态在离屏无彩色通道 ⇒ 具名 NOT-RUN。预检 264/243/660、rot 351/1083、ARM 357/1145。全量 1299/56/0；build 0 告警；换装 ok/397=397；电池 683/5。⓪ 网络不可达 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R481/R480/R478/R477 跑未读。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 4 张变化帧逐张看过：垃圾桶在标签左、按钮未压卡片。 |
| 判据有效性 | 15/15 | 标签墨宽 46pt vs 旧 33pt；M1311/M1312 2/2。 |
| 假绿防御 | 14/15 | 长标签被旧契约红后撤回而非改期望；启用红态判不了就具名 NOT-RUN；扣 1：runner 全未读。 |
| 产品面推进 | 15/15 | 新类别（清空按钮破坏性图标）；1 个产品文件；4 张旧帧变化。 |
| 台账一致性 | 15/15 | U-1857…U-1862、D-479、300 帧/1299、397=397 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 红态通道坏具名 NOT-RUN；旧契约不迁就；网络阻塞具名。 |
| 可复核性 | 15/15 | 4 张帧、46/46.5pt、M1311/M1312、precheck 264/243/660、rot 351/1083、基线 300 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-479 清空按钮补垃圾桶图标但保留短标签；启用的红色态在离屏无通道（R483）

- 背景：设置数据页的「清空」只有文字，而主窗口/详情浮层用垃圾桶；夹具注入 nil，基线钉住禁用灰态；第一版把标签改成「清空未收藏」被旧契约测试当场红。
- 决定：Sources 改成 `Label("清空", systemImage:"trash")`（短标签不动）；夹具注入非 nil 回执让启用态进帧；新判据读标签墨宽（46pt），M1311/M1312 2/2；启用红态离屏无彩色通道（红像素 0）⇒ 具名 NOT-RUN，不拿颜色当证人。
- 理由：图标是与其它破坏性动作同一套语言；旧契约（短标签）是既有设计决定，不能为新建模改期望；通道判不了的颜色不冒充证据。
- 兼容性/迁移：4 张旧帧变化、0 新增，基线 300 同笔更新；无 Store/存档变化。
- 边界：runner 1x/dark 与启用红态未签收；R481/R480/R478/R477 跑未读。
- 回滚：恢复纯文字按钮；判据与刀一并撤。
"""
CS=u"""### 设置数据页清空按钮补垃圾桶图标（4 张旧帧变化、基线 300）（R483 / 第 481 轮 / Round 479 / U-1857…U-1862 · 产品 1 文件 + 判据）

"""
BS=u"""**564. 清空按钮启用红态在离屏帧无彩色通道**（R483 观察）
    现象：注入非 nil 后 `.borderedProminent + .tint(.red)` 的帧仍无彩色像素（红 0），只能判标签墨宽。
    修法：要判危险色需换通道（真机/在屏）或自定义填充；下一轮读 `CLEAR_LABEL` 的 runner 1x，不要拿红像素 0 当产品没画。

**565. R481/R480/R478/R477 的跑仍未读**（R483 观察）
    现象：CI_READ_BLOCKED=network，R481/R480/R478/R477 跑的全部失败步骤与 ROW_LINK_BADGE 没拿到。
    修法：网络恢复后成对读；仍红按读数继续。

**566. 设置清空按钮的短标签是既有契约**（R483 观察）
    现象：改成「清空未收藏」被 `testSettingsClearButtonUsesShortDestructiveLabel` 当场红。
    修法：破坏性按钮的可见文案改动要先看契约；不许为新产品位改旧期望。
"""
SS=u"""## R483 状态（2026-10-29 · 本地 · 第 481 轮 / Round 479）：设置数据页清空按钮补垃圾桶图标（4 张旧帧变化、基线 300）；全量 1299/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R483 / 第 481 轮 / Round 479）：主窗口/详情浮层用垃圾桶说破坏性动作，设置数据页的「清空」只有文字；夹具又注入 nil，基线钉住用户看不到的禁用灰态。修法：Sources 把按钮改成 `Label("清空", systemImage:"trash")`（**标签保持「清空」**——旧契约 `testSettingsClearButtonUsesShortDestructiveLabel` 钉着短标签，不改旧期望）；夹具注入非 nil 回执让启用态进帧。旧/新：**4 张旧帧变化**（settings-data 与 settings-data-no-title-icon 各亮暗）、0 新增/缺失；基线 **300/0/0/0**；逐张看过：垃圾桶在标签左、按钮未压卡片。读数（`CLEAR_LABEL`）：标签墨宽 light **46.0pt**、dark **46.5pt**（旧「清空」文字约 33pt）；**启用红态在离屏 `.borderedProminent` 无彩色通道（红像素 0）⇒ 具名 NOT-RUN，不拿颜色当证人**。新判据读标签墨宽（阈值 45pt；内容平涂时 `CLEAR_LABEL_NOT_RUN` 并 skip）；`M1311`（Label→Text）/`M1312`（labelStyle titleOnly）**2/2**。第一版把标签改成「清空未收藏」（85.5pt）被旧契约当场红 ⇒ **撤回长标签、保留短标签+图标**。预检 **264/243/660 bad=0**、ARM **357/1145**、HIDDEN **351/1083 rot=0**。⓪：开工两次 push 报 `correct access rights`、gh 不可达 ⇒ **`PUSH_BLOCKED=network`（HEAD=`54af93a`、ahead=0）**、**`CI_READ_BLOCKED`**；R481/R480/R478/R477 跑未读 ⇒ NOT-RUN；R479 跑签收沿用；436 无新跑。全量 **1299/56/0**（489.7s，轻载；首遍长标签红 1 条，撤回后干净）；捕获卷 **300 帧**；基线 **300/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 397=397`；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 481，`python3 scripts/product_streak.py --streak-for 481`，last=2770bfe）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 网络不可达 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R481/R480/R478/R477 跑 NOT-RUN；436 无新跑。
② 产品：清空按钮补垃圾桶图标（4 张旧帧变化、基线 300）；保留短标签，撤回长标签改法。
③ 判据：标签墨宽 46pt；M1311/M1312 2/2；启用红态具名 NOT-RUN。
④ 预检 264/243/660；rot 351/1083；ARM 357/1145。
⑤ 捕获 300 帧；基线 300/0/0/0；build 0 告警；换装 ok/397=397；全量 1299/56/0。

NOT-RUN / 阻塞（分开写）：① R481/R480/R478/R477 跑（CI_READ_BLOCKED）；② 清空按钮启用红态（离屏无彩色通道）；③ 垃圾桶图标 runner 1x/dark；④ 链接/标题图标/兜底路径/inline/幻影/图钉/冲突 runner 复核；⑤ SETTINGS_DATA_PATH；⑥ 既有 runner 复核；⑦ Capture MATERIAL_BLIND_NOT_RUN；⑧ 已知 Motion 采样红；⑨ 437–566 的其余未结项仍开。

下一轮（R484）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；成对读 R483 自身跑、R481 跑 `40812979165`、R480 跑、R478 两跑、R477 两跑、R479 跑的全部失败步骤；**重点读 `CLEAR_LABEL`（≥45pt 且 1x/dark）、`ROW_LINK_BADGE`、`SETTINGS_TITLE_ICON(_NOT_RUN)`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`/`ROW_RICH_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做清空按钮图标/链接条目标记/富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R483（清空按钮破坏性图标位）**：设置数据页的「清空」只有文字，而主窗口/详情浮层用垃圾桶；夹具注入 nil，基线钉住禁用灰态。Sources 改成 `Label("清空", systemImage:"trash")`（**短标签保持**，旧契约不改），夹具注入非 nil 让启用态进帧。**4 张旧帧变化**、0 新增，基线 **300/0/0/0**；`CLEAR_LABEL` 标签墨宽 46.0/46.5pt（旧文字约 33pt）；M1311/M1312 **2/2**。第一版长标签「清空未收藏」被旧契约当场红 ⇒ 撤回；启用红态离屏无彩色通道 ⇒ 具名 NOT-RUN。⓪ 网络不可达 ⇒ PUSH_BLOCKED/CI_READ_BLOCKED；R481/R480/R478/R477 跑 NOT-RUN。全量 **1299/56/0**（489.7s）；build 0 告警；换装 ok/397=397；电池 683/5。
"""
a=rd(A); i=rd(I); d=rd(D); c=rd(C); b=rd(B); st=rd(S); p=rd(P)
if a.count(AT)!=1 or u"第 481 轮（R483" in a: raise SystemExit("A")
if u"## Round 479 · R483" in i: raise SystemExit("I")
if u"## D-479" in d: raise SystemExit("D")
if u"清空按钮补垃圾桶图标" in c: raise SystemExit("C")
if u"**564." in b: raise SystemExit("B")
if st.count(u"## R481 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1856（R481 现读抬到最新一节）"
if p.count(U)!=1 or p.count(u"AGENT_STATE.md` 的 R481 节 ②")!=1: raise SystemExit("P")
wr(A,a.replace(AT,AS+AT,1)); wr(I,i.rstrip()+"\n\n"+IS+"\n"); wr(D,d.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if c.count(m)!=1: raise SystemExit("C2")
wr(C,c.replace(m,m+"\n"+CS,1)); wr(B,b.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R481 状态",SS+u"## R481 状态",1))
p2=p.replace(U,u"U-31 … U-1862（R483 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R481 节 ②",u"AGENT_STATE.md` 的 R483 节 ②",1)
wr(P,p2.rstrip()+"\n\n"+RB+"\n"); print("OK")
