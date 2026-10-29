#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R480 七本台账一次落盘。"""
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
C=os.path.join(R,"CHANGELOG.md"); B=os.path.join(R,"AGENT_BACKLOG.md"); S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md")
AT=u"## 第 478 轮（R479 · 2026-10-29"
AS=u"""## 第 479 轮（R480 · 2026-10-29 · U-1845…U-1850）：主列表补富文本格式标记（2 张新帧、基线 298；M1306/M1307 2/2）（产品 1 文件 + 判据）

- **U-1845：⓪ push 与 CI。** 开工网络被监督者实测为不可达（api=000、`git ls-remote` remote closed）；本轮先本地完成，收口探针与最终 ahead/SHA 见补记。R479 跑 `40805576917 ↔ 225e6f8`、R478 两跑 `40801850707 ↔ b64682e`/`40802042660 ↔ 7f21720`、R477 两跑读时均为 in_progress 或未读 ⇒ **NOT-RUN**；R477 主跑的 inline/幻影/图钉读数沿用 R479 账；436 无新跑（最后 facts 5/5/77）。
- **U-1846：① 腐烂与预检。** `HIDDEN_ARMS 表=349 可判=1079 rot=0 抽不出=6 已声明死针=0 处置=ok`；`NEEDLE_PRECHECK tables=262 covered=243 arms=660 bad=0`、`ARM_TOTAL files=355 arms=1144`。
- **U-1847：② 产品：主列表补富文本格式标记。** 缺陷形状（打开「保留富文本格式」后）：`Entry.richText` 已经保存，但列表行与普通文本行一模一样，用户看不出这条除了纯文本还存了格式。修法：`RowTextColumn` 的时间行在 OCR 标记之后再补一枚 `textformat`（11pt、secondaryLabelColor、helpLabel + accessibilityLabel），只有 `richText` 非空才出现。旧/新：**2 张新帧**（`row-rich-text` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **296→298**；2 张逐张看过：标记在时间行末尾、与来源同一行。读数（`ROW_RICH_BADGE`）：负臂墨 9363→正臂 9593（**+230**）、dark 10477→10727（+250）；标题/行高未动。
- **U-1848：③ 判据与刀。** 新判据 `testRowsWithRichTextCarryAFormatBadge` 用成对帧（`row-text` / `row-rich-text`，同内容/时间/来源，只多 richText）：正臂下半行墨量必须多 ≥8pt·s²；不读"末列"（标题第二行会遮住标记的末列，第一版因此假红，当场改成墨差）。刀 `M1306`（标记永不画）/`M1307`（负向帧也画）**2/2 CAUGHT**、RESTORE_CLEAN。
- **U-1849：④ 自伤与撤回。** 本轮第一版产品位是「浮层外缘 1pt 发丝线」，全量当场 **18 个既有 QuickPick 判据红**（外缘线被药丸/选区尺读进对象）⇒ 撤回产品与判据，不用改 18 条旧期望来迁就它；随后换成富文本标记。`row-rich-text` 是新帧，未改任何旧帧。
- **U-1850：⑤ 八步与电池。** build **0 告警**（arm64+x86_64）；捕获卷 **298 帧**、`CHANGED=0 ADDED=2 MISSING=0`，更新后 `298/0/0/0`；全量 **1297/56/0**（499.4s，轻载；新增 1 条富文本标记判据）；换装 `ok / SHA_MATCH=1 / 395=395`（版本 1.4.8；本轮起安装条目以现读为准）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **1** 轮（as-of 479，`python3 scripts/product_streak.py --streak-for 479`）；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。**具名 NOT-RUN**：① R479/R478/R477 的 in_progress 跑；② 富文本标记的 runner 1x/dark；③ `SETTINGS_TITLE_ICON`/`FALLBACK_PATH`/`INLINE_CODE_PAD`/幻影/图钉/冲突的 runner 复验；④ `SETTINGS_DATA_PATH` 两档；⑤ 既有 runner 复核（无新跑）；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ `LOCAL_PERF_BUDGET_FLAKE=load`（本跑未触发）；⑨ 437–561 的其余未结项仍开。

"""
IS=u"""## Round 477 · R480（第 479 轮 · 2026-10-29）：主列表补富文本格式标记（2 张新帧、基线 298）

打开「保留富文本格式」后，`Entry.richText` 已保存但行里看不出。`RowTextColumn` 时间行在 OCR 标记后再补 `textformat`（11pt、secondary、helpLabel + accessibilityLabel），只有 richText 非空才出现。2 张新帧、0 张既有帧变化，基线 296→298；`ROW_RICH_BADGE` 负臂→正臂墨 9363→9593（+230）、10477→10727（+250）；M1306/M1307 2/2。第一版「浮层外缘线」让 18 个旧 QuickPick 判据红 ⇒ 当场撤回，不改旧期望迁就。预检 262/243/660、rot 349/1079、ARM 355/1144。全量 1297/56/0；build 0 告警；换装 ok/395=395；电池 683/5。⓪ 网络不可达，push 探针与最终 SHA 见补记。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 2 张新帧逐张看过：标记在时间行末尾、与来源同基线、不压标题。 |
| 判据有效性 | 15/15 | 成对帧只差 richText，墨差 +230/+250；M1306/M1307 2/2。 |
| 假绿防御 | 14/15 | 第一版末列判据被标题遮住当场改墨差；外缘线方案被 18 条旧红否掉并撤回；扣 1：runner 复验未读。 |
| 产品面推进 | 15/15 | 新类别（富文本格式标记）；1 个产品文件；2 张新帧、0 旧帧变化。 |
| 台账一致性 | 15/15 | U-1845…U-1850、D-477、298 帧/1297、395=395 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 18 红方案直接撤回而不是改旧期望；网络不可达具名。 |
| 可复核性 | 15/15 | 2 张帧、+230/+250、M1306/M1307、precheck 262/243/660、rot 349/1079、基线 298 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""
DS=u"""## D-477 富文本格式要有行内标记；被旧判据大面积否掉的产品位要撤回而不是改旧期望（R480）

- 背景：打开「保留富文本格式」后 `Entry.richText` 已保存，但列表行与普通文本行同形；第一版产品位「浮层外缘 1pt 线」让 18 个既有 QuickPick 判据红（外缘线进了药丸/选区尺的对象）。
- 决定：`RowTextColumn` 时间行补 `textformat` 小标记（仅 `richText` 非空）；撤回外缘线产品与判据；新判据用成对帧读下半行墨差（标题第二行会遮末列，第一版末列判据当场改掉）。
- 理由：格式保真是用户开过的功能，行里必须有痕迹；一个产品位若让 18 条旧判据同时红，先怀疑它换了尺的对象，撤回比改期望便宜且诚实。
- 兼容性/迁移：2 张新帧、0 张既有帧变化，基线 296→298；无 Store/存档变化。
- 边界：runner 1x/dark 未签收；上一轮标题图标/兜底路径的 runner 读数仍未读到。
- 回滚：删标记与判据；外缘线不保留。
"""
CS=u"""### 主列表补富文本格式标记（2 张新帧、基线 298）（R480 / 第 479 轮 / Round 477 / U-1845…U-1850 · 产品 1 文件 + 判据）

"""
BS=u"""**559. R479/R478/R477 的跑仍未读**（R480 观察）
    现象：R479 跑 40805576917、R478 两跑 40801850707/40802042660、R477 两跑均 in_progress/未读；SETTINGS_TITLE_ICON/FALLBACK_PATH 的 runner 读数没有。
    修法：网络恢复后先读这些跑的全部失败步骤；仍红按读数继续。

**560. 富文本格式标记的 runner 1x/dark 未签收**（R480 观察）
    现象：本机两档下半行墨差 +230/+250；runner 1x 的 11pt 标记可能小于 8px² 地板。
    修法：读新跑 `ROW_RICH_BADGE`；低于地板按 scale² 重算，不改产品字号。

**561. 被旧判据大面积否掉的产品位：先撤回，不改期望**（R480 观察）
    现象：浮层外缘 1pt 线让 18 个既有 QuickPick 判据红（外缘线被药丸/选区尺读进对象）。
    修法：新位上线前先想"它会不会进旧尺的对象"；18 条同红时撤回产品与判据，不逐条放宽旧期望。
"""
SS=u"""## R480 状态（2026-10-29 · 本地 · 第 479 轮 / Round 477）：主列表补富文本格式标记（2 张新帧、基线 298）；全量 1297/56/0（产品 1 文件 + 判据）

最后更新：2026-10-29（本地 · R480 / 第 479 轮 / Round 477）：打开「保留富文本格式」后 `Entry.richText` 已保存，但列表行看不出。修法：`RowTextColumn` 时间行在 OCR 标记后再补 `textformat`（11pt、secondaryLabelColor、helpLabel + accessibilityLabel），只有 richText 非空才出现。旧/新：**2 张新帧**（`row-rich-text` 亮暗）、**0 张既有帧变化**、0 缺失；基线 **296→298**；2 张逐张看过。读数（`ROW_RICH_BADGE`）：负臂墨 9363→正臂 9593（+230）、dark 10477→10727（+250）。判据用成对帧读下半行墨差（末列会被标题第二行遮住，第一版当场改掉）；M1306/M1307 **2/2**。第一版产品位「浮层外缘线」让 18 个既有 QuickPick 判据红 ⇒ 撤回产品与判据，不改旧期望迁就。预检 **262/243/660 bad=0**、ARM **355/1144**、HIDDEN **349/1079 rot=0**。⓪：开工网络不可达（api=000、ls-remote remote closed）；收口 push 探针与最终 ahead/SHA 见补记。R479/R478/R477 的跑读时 in_progress/未读 ⇒ NOT-RUN；436 无新跑。全量 **1297/56/0**（499.4s，轻载）；捕获卷 **298 帧**；基线 **298/0/0/0**；build **0 告警**；换装 `ok / SHA_MATCH=1 / 395=395`；`STORE-SIZE lines=1108 funcs=52 longest=66`；清账 `格=162 声明=63 不成立=0/63`；§1 刷新在生成器后复跑；电池在台账后复跑。

本轮做了什么：
① ⓪ 网络不可达（api=000）；R479/R478/R477 的跑 in_progress/未读 ⇒ NOT-RUN；436 无新跑。
② 产品：主列表补富文本格式标记（2 张新帧、基线 298）。
③ 判据：成对帧墨差 +230/+250；M1306/M1307 2/2；末列判据被标题遮住当场改掉。
④ 自伤：外缘线让 18 条旧 QuickPick 判据红 ⇒ 撤回，不改旧期望。
⑤ 捕获 298 帧；基线 298/0/0/0；build 0 告警；换装 ok/395=395；全量 1297/56/0。

NOT-RUN / 阻塞（分开写）：① R479/R478/R477 的 in_progress 跑；② 富文本标记 runner 1x/dark；③ 标题图标/兜底路径/inline/幻影/图钉/冲突 runner 复验；④ SETTINGS_DATA_PATH；⑤ 既有 runner 复核；⑥ Capture MATERIAL_BLIND_NOT_RUN；⑦ 已知 Motion 采样红；⑧ LOCAL_PERF_BUDGET_FLAKE=load（本跑未触发）；⑨ 437–561 的其余未结项仍开。

下一轮（R481）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R480 自身跑、R479 跑、R478 两跑、R477 两跑、R476 跑、R475 跑、R474 两跑、R473/R472/R471 跑的全部失败步骤；**重点读 `ROW_RICH_BADGE`（≥8px²）、`SETTINGS_TITLE_ICON`、`FALLBACK_PATH`、`INLINE_CODE_PAD`、`QUICKPICK_GREY_BAND`、`QUICKPICK_PIN`、`SHORTCUT_CONFLICT(_NOT_RUN)`**；仍红按读数继续，4.5 与 150 不动；其余重点：`ROW_OCR_BADGE`、`QUICKPICK_LIST_RULE`、`SETTINGS_DATA_PATH`、`TRUNCATION_NOTE`、`QUICKPICK_SOURCE_ICON`、`CROSS_YEAR`/`MAIN_ROWS`、`SETTINGS_HELPER_AXIS`、`CARD_INSET_CONTROL_FIRST`、`VIDEO_*`、Capture MATERIAL_BLIND_NOT_RUN、436（只复核新跑 Motion floor）；in_progress/0 字节不算绿；`gh` 读不到就具名 `CI_READ_BLOCKED=network`（收口前再试一次）；flake 原样重跑；① 现读 rot=0；② 继续产品视觉位并落 Sources、换缺陷类别（不要再做富文本格式标记/设置页标题图标/文件兜底路径/浮层行置顶标记/快捷键冲突提示/图片行可搜索文字标记/浮层分区边界/数据页保存位置/设置存储路径等宽/详情截断提示/浮层行来源图标/跨年时间标注/设置说明文字轴/seek 轨道/播放器/控件对齐/视频播放器实底/视频不可读态/fallback 占位图标/fallback 文件名/行内码底色/纯文本文件列宽/宽表横向滚动/标题字阶/代码块制表位/列表命中高亮/弱化色对比度/删除线/权重刻度/列表悬挂缩进/任务项完成态/浮层键盘提示/表格体行分隔/主题分隔线/代码块语言标签/代码块行号/表格表头/引用导引线/侧栏搜索来源/主列表来源行/设置侧栏文字/设置关于页/录制帮助/多文件展开/批量分隔/浮层搜索/图片/HTML/排除名单/行内符号/时间列/分区头/侧栏脚注/详情头部/Dock/菜单栏/横幅/回执/热图/计数/空态/无结果/焦点/悬停/选中/滚动/CTA）；③ 436 只复核新跑 Motion floor。
"""
RB=u"""- **R480（富文本格式标记位）**：打开「保留富文本格式」后 `Entry.richText` 已保存，但列表行看不出。`RowTextColumn` 时间行在 OCR 标记后再补 `textformat`（11pt、secondary、helpLabel + accessibilityLabel），仅 richText 非空出现。**2 张新帧、0 张既有帧变化**，基线 **296→298**；`ROW_RICH_BADGE` 负臂→正臂墨 9363→9593（+230）、10477→10727（+250）；M1306/M1307 **2/2**。第一版「浮层外缘线」让 18 条旧 QuickPick 判据红 ⇒ 当场撤回，不改旧期望。⓪ 网络不可达，收口 push 探针见补记；R479/R478/R477 的跑 NOT-RUN。全量 **1297/56/0**（499.4s）；build 0 告警；换装 ok/SHA_MATCH=1/395=395；电池 683/5。
"""
at=rd(A); it=rd(I); de=rd(D); ch=rd(C); bl=rd(B); st=rd(S); rp=rd(P)
if at.count(AT)!=1 or u"第 479 轮（R480" in at: raise SystemExit("A")
if u"## Round 477 · R480" in it: raise SystemExit("I")
if u"## D-477" in de: raise SystemExit("D")
if u"富文本格式标记" in ch: raise SystemExit("C")
if u"**559." in bl: raise SystemExit("B")
if st.count(u"## R479 状态")!=1: raise SystemExit("S")
U=u"U-31 … U-1844（R479 现读抬到最新一节）"
if rp.count(U)!=1 or rp.count(u"AGENT_STATE.md` 的 R479 节 ②")!=1: raise SystemExit("P")
wr(A,at.replace(AT,AS+AT,1)); wr(I,it.rstrip()+"\n\n"+IS+"\n"); wr(D,de.rstrip()+"\n\n"+DS+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C2")
wr(C,ch.replace(m,m+"\n"+CS,1)); wr(B,bl.rstrip()+"\n\n"+BS+"\n"); wr(S,st.replace(u"## R479 状态",SS+u"## R479 状态",1))
rp2=rp.replace(U,u"U-31 … U-1850（R480 现读抬到最新一节）",1).replace(u"AGENT_STATE.md` 的 R479 节 ②",u"AGENT_STATE.md` 的 R480 节 ②",1)
wr(P,rp2.rstrip()+"\n\n"+RB+"\n"); print("LEDGERS_R480_OK")
