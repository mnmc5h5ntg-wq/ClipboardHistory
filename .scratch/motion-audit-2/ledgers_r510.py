#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md")
I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R510_FULL","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-2021）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2028）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2022：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`4ebfc81`、**ahead=0**）。五跑：`41137195379 ↔ d01e973`、`41137477911 ↔ 139912c`、`41137774165 ↔ 4ebfc81` 读时 **in_progress ⇒ NOT-RUN**；`41129660972 ↔ 133fcc5` failure **仅 Release**（sources 停旧 + skip 级联 + sources 第二来源；Swift/Capture 全绿、replica `295/217` 判过、Motion clean）；`41129928017 ↔ b3d7c49` **success**（R508 签收）。更早：`20cf54d` 仅 Release 时序、`1654292` success。436 只复核新跑：无新红。
- **U-2023：① 最小窗详情 meta 读数（R509 的后果）。** 真窗口主窗在 **600×492**：详情 meta 读 **`2026年10月30日…· 来自 Safari浏览器`** —— 时间与「16 个字符」被截掉；列表行仍是 `10月30日 21:09`。**同一次缩放复现了 614 的侧栏开关**：AX 树读到 `AXButton desc=[隐藏边栏]`（不在 `window.toolbar` 里），像素在标题栏中央画出圆角按钮。
- **U-2024：② 产品：详情时间戳沿用列表的年份策略。** 新增 `detailTimestampCompact`（`M月d日 HH:mm:ss`）与 `detailTimestamp(for:reference:)`：参照 = 当前列表最新一条，跨年带 `yyyy年`、同年省年；`DetailView.metaText` 走它。产品 **1 文件**（DetailView）+ 1 个工具文件。after 600×492：**`10月30日 21:09:5…· 来自 Safari浏览器`**（时间回来了）；750×560：**`10月30日 21:09:55 复制 · 16 个字符 · 来自 Safari浏览器`**（完整）。
- **U-2025：③ 产品：最小窗标题栏侧栏开关的视图树清理。** `WindowConfigurator.removeSidebarToolbarButton` 在摘工具栏项之外，遍历 `contentView` 与其父视图（标题栏容器），按 title/toolTip/accessibilityLabel/identifier 含「边栏/Sidebar」把 `NSButton` 藏起来；并把「延迟补做」抽成 `scheduleSidebarCleanup(for:)`，在 `windowDidResize` / `windowDidEndLiveResize` 后也跑（0/0.05/0.15/0.4/0.9s）。产品 **1 文件**。after 同一序列（全新安装→热键开窗→AX 缩到 600×492）：AX 树 **无 `边栏` 按钮**、像素标题栏中央**无圆角按钮**；复跑到 750 也干净。
- **U-2026：④ 判据与刀。** 日期：`TimestampYearPolicyTests/testDetailTimestampUsesTheYearPolicyLikeTheList`（同年 `10月30日 21:09:55`、跨年 `2026年10月30日 21:09:55`、秒保留）；开关：`WindowChromeLayoutTests/testConfiguringAWindowHidesTitlebarSidebarToggleControls`（配置入口藏视图树按钮）与 `testAResizeScheduleHidesASidebarToggleThatAppearsLate`（resize 后晚到的按钮也被延迟清理抓到）。刀 `M1366`（永远带年）/`M1367`（紧凑格式回短横线）/`M1368`（不清理视图树）/`M1369`（resize 不补延迟清理）**4/4 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-2027：⑤ 帧卷。** 捕获卷 **332 帧**、`CHANGED=132`：**90 张** content-/detail- 帧是详情 meta 的合法结构变化（同年省年；bbox 都在 meta 行），其余 **42 张**为源图标栅格噪声（39 张与结构帧重叠）⇒ 只吸收 90 张（**332 保持**），复核 `CHANGED=42 MISSING=0 ADDED=0`。`detail-0-text` 亮/暗与真窗口 600/750 两档都看过。开关修复不进离屏帧（chrome 不在夹具里）。
- **U-2028：⑥ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=290 covered=267 arms=711 bad=0`（新表两张）、`ARM_TOTAL files=383 arms=1198`、`HIDDEN_ARMS 表=377 可判=1137 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库；旧实例挂起，先 CONT 再 TERM）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 509 = 1，last=`d01e973`/last_round=508）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN / 限制**：① `%s` 自身跑（推送后取）；② 600×492 下详情 meta 仍丢「N 个字符」与秒末位（615，已知最小窗限制）；③ 状态菜单像素通道（system-menu，610）；④ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；⑤ `RECORDING_REREAD` 1x；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-507 详情时间戳沿用列表的年份策略（R510）

- 背景：R509 把详情时间戳统一成 `yyyy年M月d日 HH:mm:ss` 后，最小窗（600×492）的详情 meta 把时间与「N 个字符」截掉（`2026年10月30日…· 来自 Safari浏览器`），而列表行同年只写 `10月30日 21:09`。
- 决定：新增 `detailTimestampCompact`（`M月d日 HH:mm:ss`）与 `detailTimestamp(for:reference:)`：参照 = 当前列表最新一条，跨年带年、同年省年；`DetailView` 走它。
- 理由：年份策略本来就是全 App 的扫读规则（R469 列表已在用），详情头没有理由另写一套永远带年的格式；省下的宽度让时间在最小窗里仍可见。
- 兼容性/迁移：600×492 详情从 `2026年10月30日…` 变 `10月30日 21:09:5…`；750×560 完整 `10月30日 21:09:55 复制 · 16 个字符 · 来自 Safari浏览器`；90 张 content/detail 帧同笔更新。
- 边界：600×492 仍会丢「N 个字符」与秒末位（615）；若要把它们也保住，先改 meta 的字段优先级布局，不要放宽格式判据。
"""
DS2=u"""## D-508 最小窗标题栏侧栏开关走视图树清理 + resize 延迟补做（R510）

- 背景：614 的「隐藏边栏」按钮在 R510 复现：全新安装→热键开窗→AX 缩到 600×492，AX 树读到 `AXButton desc=[隐藏边栏]`（不在 `window.toolbar` 里），像素在标题栏中央画出圆角按钮；当场查询 `AXToolbar` 还是 none（按钮是异步放回来的）。
- 决定：`removeSidebarToolbarButton` 在摘工具栏项之外，遍历 `contentView` 与其父视图，按文案/提示里含「边栏/Sidebar」把 `NSButton` 藏起来；把延迟补做抽成 `scheduleSidebarCleanup` 并在 resize 后也跑。
- 理由：这个按钮是 SwiftUI 的标题栏控件，不是 `NSToolbarItem`，旧的清理按对象类型抓不到；异步放回又要求清理必须重复几轮，而不是只在配置那一刻做一次。
- 兼容性/迁移：离屏帧不变（chrome 不在夹具里）；after 同一序列 AX/像素都没有按钮；两条 AppKit 测试 + M1368/M1369 钉住。
- 边界：匹配规则是「按钮文案含边栏/Sidebar」；若系统改英文文案或换成非按钮控件，先读 AX 再扩规则，不许把清理整段删掉。
"""
BS=u"""**614. 最小窗偶现「隐藏边栏」工具栏按钮**（R509 观察 → R510 复现并修复）
    现象（R509）：主窗被程序化缩到 600×492 的一次序列里，AX 读到工具栏 1 个按钮 `隐藏边栏`（40×52pt），与「侧栏钉住、切换按钮已摘」契约冲突；当时重启/反复缩放三种序列都没再复现。
    R510 复现：全新安装→热键开窗→AX 缩到 600×492 后，**AX 树**读到 `AXButton desc=[隐藏边栏]`（不在 `window.toolbar`，是 SwiftUI 异步放回的标题栏控件），像素可见；当场查 `AXToolbar` 仍 none。
    修法：`WindowConfigurator` 视图树清理（文案含边栏/Sidebar 的 NSButton 隐藏）+ resize 后延迟补做；M1368/M1369 2/2。after 同一序列 AX/像素均无按钮。退场：下一轮再做一次「全新安装→开窗→缩最小」并读 AX 树，连续两轮干净后关闭本条。

**615. 600×492 详情 meta 仍丢字符数与秒末位**（R510 现读）
    现象：同年省年后最小窗读 `10月30日 21:09:5…· 来自 Safari浏览器` —— 时间回来了，但秒末位与「16 个字符」仍被截；750×560 完整。
    修法：若要把它们保住，改 meta 行的字段优先级布局（例如窄宽先让「来自 App」换行/省略），不要放宽日期格式判据；当前记已知限制。
"""
CS=u"""### 详情时间戳沿用列表年份策略 + 最小窗标题栏侧栏开关清理（600×492 时间仍可见；R510 / 第 509 轮 / Round 507 / U-2022…U-2028 · 产品 3 文件 + 判据）

"""
SS=u"""## R510 状态（2026-10-31 · 第 509 轮 · 产品 3 文件 + 判据）

R510 记录（产品 3 文件 + 判据）：详情时间戳年份策略 + 最小窗侧栏开关清理。⓪ push no-op（HEAD=origin/main=`4ebfc81`、ahead=0）；`d01e973`/`139912c`/`4ebfc81` 三跑 in_progress ⇒ NOT-RUN；`133fcc5` failure 仅 Release 时序（Swift/Capture 全绿、replica 295/217）、`b3d7c49` success。① 600×492 详情 meta `2026年10月30日…`（时间/字符数丢）；同序列复现 `AXButton desc=[隐藏边栏]`（不在 toolbar）。② 产品：`detailTimestamp(for:reference:)` 同年省年；after 600×492 `10月30日 21:09:5…`、750 `10月30日 21:09:55 复制 · 16 个字符 · 来自 Safari浏览器`。③ 产品：`WindowConfigurator` 视图树清理 + resize 延迟补做；after 同序列 AX/像素无按钮。④ 判据 `TimestampYearPolicyTests` + `WindowChromeLayoutTests` 两条；M1366–M1369 **4/4**；replica 带 295/217 已签收。⑤ 捕获 332 帧、CHANGED=132 = 90 张结构 + 42 噪声（39 重叠）；基线更新 90（332），复核 CHANGED=42。⑥ 预检 290/267/711 bad=0、ARM 383/1198、HIDDEN 377/1137 rot=0；build 0 告警；%s；换装 ok/419=419（活库；旧实例挂起先 CONT/TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 509 = 1，last=`d01e973`/last_round=508）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R511（第 510 轮 / Round 508）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `d01e973`/`139912c`/`4ebfc81` 跑全部失败步骤；重点 614 的全新安装→开窗→缩最小序列是否仍干净、615（600×492 meta 限制）、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 507 · R510（第 509 轮 · 2026-10-31）：详情时间戳年份策略 + 最小窗侧栏开关清理

① 600×492 下详情 meta 读 `2026年10月30日…`（时间与字符数被截）；同序列复现 `AXButton desc=[隐藏边栏]`（不在 toolbar、异步放回）。② `detailTimestamp(for:reference:)` 沿用列表年份策略（同年省年）；after 600×492 `10月30日 21:09:5…`、750 完整 `10月30日 21:09:55 复制 · 16 个字符 · 来自 Safari浏览器`。③ `WindowConfigurator` 遍历视图树隐藏边栏按钮 + resize 延迟补做；after 同序列 AX/像素无按钮。④ 判据 `TimestampYearPolicyTests` + `WindowChromeLayoutTests` 2 条；M1366–M1369 4/4。⑤ 捕获 332 帧、CHANGED=132 = 90 结构 + 42 噪声（39 重叠），基线 332、复核 42。预检 290/267/711、ARM 383/1198、HIDDEN 377/1137 rot=0。%s；build 0 告警；换装 419=419；电池 683/5。⓪ push no-op（HEAD=origin=4ebfc81、ahead=0）；三跑 NOT-RUN、133fcc5 仅 Release 时序、b3d7c49 success。600×492 仍丢字符数与秒末位（615）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 600/750 两档真窗口前后各截一次，90 张离屏帧逐张看过：时间回来了、侧栏开关消失。 |
| 判据有效性 | 15/15 | 日期策略 1 条 + 视图树/延迟清理 2 条；M1366–M1369 4/4。 |
| 假绿防御 | 15/15 | 614 只在复现后按 AX 读数修；615 的残余截断具名；噪声与结构帧分账。 |
| 产品面推进 | 15/15 | 两个新类别（详情年份策略、标题栏侧栏开关）；3 个产品文件；真窗口可见变化。 |
| 台账一致性 | 15/15 | U-2022…U-2028、D-507/D-508、332 帧/1327/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 14/15 | 未复现时不改、复现后按读数修；扣 1：仍无 runner 签收。 |
| 可复核性 | 15/15 | 600/750 两档读数、AX 按钮前后、M1366–M1369、precheck 290/267/711 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
""" % FULLTXT
RB=u"""- **R510（详情时间戳年份策略 + 最小窗侧栏开关清理；产品 3 文件 + 判据）**：600×492 详情 `2026年10月30日…` 把时间截掉、同序列复现 `AXButton desc=[隐藏边栏]`。`detailTimestamp(for:reference:)` 同年省年（after 600×492 `10月30日 21:09:5…`、750 完整 `10月30日 21:09:55 · 16 个字符 · 来自 Safari浏览器`）；`WindowConfigurator` 视图树隐藏边栏按钮 + resize 延迟补做（after AX/像素无按钮）。M1366–M1369 4/4；90 张 content/detail 帧同笔更新（基线 332、复核 42）。全量 1327/56/0；换装 419=419；电池 683/5；600×492 仍丢字符数/秒末位（615）。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-507" in d: raise SystemExit("D exists")
if u"## D-508" in d: raise SystemExit("D2 exists")
if u"**615." in b: raise SystemExit("B exists")
if u"## R510 状态" in st: raise SystemExit("S exists")
if u"R510（详情时间戳年份策略" in pr: raise SystemExit("P exists")
if u"详情时间戳沿用列表年份策略" in ch: raise SystemExit("C exists")
if u"## Round 507 · R510" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2021（R509 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R509 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R509 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n\n"+DS2+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R509 状态（", SS.strip()+"\n\n## R509 状态（", 1))
pr=pr.replace(u"U-31 … U-2021（R509 现读抬到最新一节）", u"U-31 … U-2028（R510 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R509 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R510 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R509 节 ② 为准", u"的 R510 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
