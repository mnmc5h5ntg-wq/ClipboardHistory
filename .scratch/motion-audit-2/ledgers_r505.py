#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md")
I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")

AT_OLD=u"## 第 501 轮（R502 · 2026-10-30 · U-1970…U-1987）：主窗口与设置窗口的标题栏统一（真窗口表面；产品 1 文件 + 判据）"
AT_NEW=u"## 第 501 轮（R502 · 2026-10-30 · U-1970…U-1993）：主窗口与设置窗口的标题栏统一（真窗口表面；产品 1 文件 + 判据）"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-1988：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`e46c29f`、**ahead=0**）。三跑读时均未完成 ⇒ **NOT-RUN**：`41093593814 ↔ 800a45a` **in_progress**、`41095129735 ↔ 79336c7` **in_progress**、`41095547380 ↔ e46c29f` **queued**（不轮询；收口前统一再试一次）。旧跑只归因不重算：`41083133180 ↔ 5d392fb` failure 仅 `STEP[19] Motion coverage floor`（`MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=-`、红的用例=`testMarkdownModeLabelChangeIsAVisibleProcess` 1x 只有 1 个过渡帧、要 ≥2；已知采样 flake）；`41082826725 ↔ 31b21a6` failure 仅 `STEP[18] On-screen probe coverage floor`（`testFrameIntervalsUnderStateChanges` 最差帧 **256.8ms** > 锚点 120ms、超锚点 2 颗 vs 容差 1；`PROBE_NOT_RUN 6/14`；已知在屏采样红）；`41081870670 ↔ 52f4172` failure 仅 Release 4 条（sources 格停旧 + R503 独立节把 R498 挤出回看窗 + 两条级联，已由 31b21a6 修）；`41077659382 ↔ 2c14a48` **success**。436 只复核新跑 Motion floor：三跑都没有 `MOTION_FLOOR_FACTS` ⇒ NOT-RUN，不重算旧结论。
- **U-1989：① 未捕获表面读数（状态菜单）。** 状态菜单（macOS 13+ `MenuBarExtra`，`.menu`）此前没有进过任何帧。走产品入口点开状态栏菜单，用 `screencapture -l <windowID>` 只截它自己的窗口（id=623183、**194×318pt**、layer=101）：AX 标题为 `显示主窗口  ⌘S`、`快速选择…  ⌃⌥⇧V`、`设置`、`清空未收藏`、`退出时间剪史`；像素读数：设置行最右墨 **40.5pt**、退出行 **92.0pt**（内容宽 **193.5pt**）⇒ **右侧快捷键列一个像素都没有**，两条标准键（⌘, / ⌘Q）在菜单里完全不可见。
- **U-1990：② 产品：状态菜单补标准快捷键列。** 新增 `MenuCommandShortcutPresentation.keyEquivalent(for:)`：只给标准键（`.showSettings` → `,`、`.quit` → `q`），全局热键（`.showMainWindow` / `.showQuickPick`）及其余命令返回 nil。`App.swift` 的命令区与退出项各挂 `.modifier(MenuCommandShortcutModifier(command:))`，交给系统画右对齐键列；全局热键继续走标题里的行内提示（`MenuShortcutPresentation.title`），**不给它们挂本地键** —— 同一个组合会有 Carbon 与菜单两条触发路径。产品 **1 文件**（+1 个新工具文件）。after 只截菜单（id=623218、**241×318pt**）：设置行最右墨 **40.5 → 218.5pt**、退出 **92.0 → 222.0pt**，⌘ token 左沿两行同为 **201.5pt** ⇒ 同一右对齐列。**试过并撤回的坏法**：第一版把四条提示都做成 HStack 两列标签，SwiftUI 菜单把它拍平成只剩标题 ⇒ 菜单退回 194×318、四个提示全部消失（实拍可见）⇒ 当场撤回，不交付。
- **U-1991：③ 判据与刀。** 新判据 `MenuShortcutPresentationTests/testStandardShortcutsAreVisibleInTheSwiftUIMenu`：值轴断言设置/退出各拿到 `,`/`q`、其余命令为 nil（全局热键不许有本地等价物）；结构轴读 `App.swift` 源码，要求命令区与退出项各有一处 `.modifier(MenuCommandShortcutModifier(...))`。刀 `M1354`（设置映射改 nil）/`M1355`（退出映射成 `w`）/`M1356`（退出项删掉修饰器）**3/3 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-1992：④ 帧卷。** 捕获卷 **332 帧**、`COMPARED=332 CHANGED=89 MISSING=0 ADDED=0`：89 张仍为源 App 图标栅格噪声（16×16、≤7/255，bbox 尺 `变了=0`）⇒ **不吸收**（`FRAME_BASELINE_ENV_NOISE=source-icon-raster`；601），**0 张合法变化**，基线保持 **332**。状态菜单不进离屏帧 ⇒ 它的像素通道具名 `NOT_RUN=system-menu`（见 608）；本轮真窗口前后帧 `/tmp/r505_menu.png` / `/tmp/r505_menu_final.png` 已逐张看过。
- **U-1993：⑤ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh` 增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=284 covered=261 arms=698 bad=0`、`ARM_TOTAL files=377 arms=1185`、`HIDDEN_ARMS 表=371 可判=1124 rot=0`；全量 **1319/56/0**（749.2s）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 504 = 1，last=`800a45a`/last_round=503）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `f7ea8b4` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN**：① `f7ea8b4` 自身跑（推送后取）；② 状态菜单像素通道（system-menu，仅真窗口可判，608）；③ 三跑 `800a45a`/`79336c7`/`e46c29f`（in_progress/queued）；④ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；⑤ `SETTINGS_IDENTITY_HEADER` runner 1x、`RECORDING_REREAD` 1x；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
"""
DS=u"""## D-501 状态菜单的标准快捷键交给系统右对齐列，全局热键保留行内提示（R505）

- 背景：macOS 13+ 的状态菜单是 SwiftUI `MenuBarExtra`（`.menu`）。真窗口 `screencapture -l` 读数：菜单 194×318pt 里只有两条行内热键提示（`显示主窗口  ⌘S`、`快速选择…  ⌃⌥⇧V`），标准键 ⌘, / ⌘Q 右侧列**一个墨点都没有**（设置行最右墨 40.5pt、退出行 92.0pt，内容宽 193.5pt）。
- 决定：新增 `MenuCommandShortcutPresentation.keyEquivalent(for:)`，只给 `.showSettings`（`,`）与 `.quit`（`q`）返回键；`App.swift` 的命令区与退出项挂 `.modifier(MenuCommandShortcutModifier(command:))`，由系统画右对齐列。全局热键**不挂** `.keyboardShortcut`，继续用 `MenuShortcutPresentation.title` 的行内提示。
- 理由：标准键是菜单的 key equivalent，系统列才是它们该在的位置；全局热键走 Carbon，给它们再挂本地键会造出第二条触发路径（同一组合双触发）。after 菜单 241×318pt、⌘ token 左沿两行同为 201.5pt。
- 兼容性/迁移：离屏帧 0 变化（状态菜单不进夹具）；真窗口约 194→241pt；新增值+接线判据与 M1354–M1356。
- 边界：状态菜单像素通道在 CI 不可判（system-menu，608）；后续改菜单必须在真窗口重拍前后帧，不能拿离屏帧替代。
"""
BS=u"""**608. 状态菜单的像素证据只在真窗口通道**（R505 现读）
    现象：`MenuBarExtra` 的菜单由系统绘制，离屏夹具拍不到；本轮前后读数（194→241pt、⌘ token 左沿 201.5pt）只存在于 `screencapture -l` 真窗口帧。
    修法：下一轮若再动状态菜单，先走同一通道拍前后帧并读右侧键列；CI 里只认值轴（`MenuCommandShortcutPresentation`）与接线轴（`App.swift` 的 modifier），不把「runner 绿」当成菜单像素已验收。
"""
CS=u"""### 状态菜单补标准快捷键列（设置 ⌘, / 退出 ⌘Q 可见）（R505 / 第 504 轮 / Round 502 / U-1988…U-1993 · 产品 1 文件 + 判据）

"""
SS=u"""## R505 状态（2026-10-31 · 第 504 轮 · 产品 1 文件 + 判据）

R505 记录（产品 1 文件 + 判据）：状态菜单补标准快捷键列。⓪ push no-op（HEAD=origin/main=`e46c29f`、ahead=0）；三跑 `41093593814 ↔ 800a45a`/`41095129735 ↔ 79336c7`/`41095547380 ↔ e46c29f` 读时 in_progress/in_progress/queued ⇒ NOT-RUN；旧跑只归因：Motion floor（`testMarkdownModeLabelChangeIsAVisibleProcess` 1<2）、On-screen probe floor（`testFrameIntervalsUnderStateChanges` 256.8ms>120ms）、Release 4 条已由 31b21a6 修。① 真窗口 `screencapture -l` 只截状态菜单（194×318pt）：设置行最右墨 40.5pt、退出 92.0pt（内容宽 193.5pt）⇒ 右侧键列无墨，⌘, / ⌘Q 不可见。② 产品：`MenuCommandShortcutPresentation`（设置 `,`、退出 `q`，全局热键 nil）+ `.modifier(MenuCommandShortcutModifier(command:))` 挂命令区与退出项；after 菜单 241×318pt、设置右墨 218.5、退出 222.0、⌘ token 左沿同为 201.5pt。第一版 HStack 两列标签被 SwiftUI 菜单拍平、四个提示全消失 ⇒ 当场撤回。③ 判据 `testStandardShortcutsAreVisibleInTheSwiftUIMenu`（值 + App.swift 接线）；M1354/M1355/M1356 **3/3**、RESTORE_CLEAN=yes。④ 捕获 332 帧、CHANGED=89 全为源图标噪声、0 合法变化 ⇒ 基线保持 332；状态菜单像素通道 NOT_RUN=system-menu（608）。⑤ 预检 284/261/698 bad=0、ARM 377/1185、HIDDEN 371/1124 rot=0；build 0 告警；全量 **1319/56/0**；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 504 = 1，last=`800a45a`/last_round=503）；产品笔 `f7ea8b4` 已推（ahead=0）。下一轮编号 R506（第 505 轮 / Round 503）：先 push 并复核 ahead=0；读 `f7ea8b4` 自身跑与 `800a45a`/`79336c7`/`e46c29f` 跑全部失败步骤；重点状态菜单键列的 runner 不可判（608）、`SETTINGS_IDENTITY_HEADER` 1x、`RECORDING_REREAD` 1x、`RTF_HELPER_ORPHAN`（仍是 settings-content-blank/595）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
"""
IS=u"""## Round 502 · R505（第 504 轮 · 2026-10-31）：状态菜单补标准快捷键列（设置 ⌘, / 退出 ⌘Q 可见）

状态菜单（macOS 13+ `MenuBarExtra`）此前未进任何帧。真窗口 `screencapture -l` 读数：菜单 194×318pt，只有两条行内热键提示，⌘, / ⌘Q 的右侧列一个墨点都没有（设置行最右墨 40.5pt、退出 92.0pt，内容宽 193.5pt）。修法：`MenuCommandShortcutPresentation` 只给标准键返回 `,`/`q`，`App.swift` 挂 `.modifier(MenuCommandShortcutModifier(command:))`；全局热键保持行内提示，不挂本地键（避免第二条触发路径）。after 菜单 241×318pt、设置右墨 218.5、退出 222.0、⌘ token 左沿同为 201.5pt。判据 `testStandardShortcutsAreVisibleInTheSwiftUIMenu`（值 + 接线），M1354–M1356 3/3。捕获 332 帧、89 张噪声不吸收、0 合法变化、基线保持 332。预检 284/261/698、ARM 377/1185、HIDDEN 371/1124 rot=0。全量 1319/56/0；build 0 告警；换装 ok/419=419；电池 683/5。⓪ push no-op（HEAD=origin=e46c29f、ahead=0）；三跑 NOT-RUN；旧跑 Motion/probe 两条采样红、Release 4 条已由 31b21a6 修。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 状态菜单前后各只截 App 窗口并逐张看过：194→241pt、⌘ token 列出现；第一版拍平坏法也实拍确认后撤回。 |
| 判据有效性 | 15/15 | 值轴 `,`/`q`/nil + 接线轴两处 modifier；M1354/M1355/M1356 3/3。 |
| 假绿防御 | 15/15 | 全局热键显式 nil（不许第二条路径）；菜单像素通道具名 NOT_RUN=system-menu，不拿值判据冒充像素验收。 |
| 产品面推进 | 15/15 | 新类别（菜单快捷键可见性）；1 个产品文件 + 1 个工具文件；真窗口可见变化。 |
| 台账一致性 | 15/15 | U-1988…U-1993、D-501、332 帧/1319/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 14/15 | runner 1x 与三跑均具名 NOT-RUN；扣 1：状态菜单的像素证据只有本机真窗口，CI 无法复核。 |
| 可复核性 | 15/15 | 40.5→218.5、92.0→222.0、201.5 左沿、M1354–M1356、precheck 284/261/698 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""
RB=u"""- **R505（状态菜单标准快捷键列；产品 1 文件 + 判据）**：`MenuBarExtra` 里 ⌘, / ⌘Q 之前完全不显示（菜单 194×318pt、设置行最右墨 40.5pt）；补 `MenuCommandShortcutPresentation` + `.modifier(MenuCommandShortcutModifier(command:))`，全局热键保持行内提示。after 241×318pt、设置右墨 218.5、退出 222.0、⌘ token 左沿同为 201.5pt；M1354–M1356 3/3。帧 332（89 噪声不吸收、0 合法变化）；全量 1319/56/0；换装 419=419；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title anchor %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next anchor %d" % a.count(ANCHOR_NEXT))
if u"## D-501" in d: raise SystemExit("D exists")
if u"**608." in b: raise SystemExit("B exists")
if u"## R505 状态" in st: raise SystemExit("S exists")
if u"R505（状态菜单标准快捷键列" in pr: raise SystemExit("P exists")
if u"状态菜单补标准快捷键列" in ch: raise SystemExit("C exists")
if u"## Round 502 · R505" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-1987（R504 现读抬到最新一节）")!=1: raise SystemExit("P U cell")
if pr.count(u"## 18. R458 → R504 这一段（R478 起写；R504 续到 504 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P section18")
if pr.count(u"的 R504 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R504 状态（", SS.strip()+"\n\n## R504 状态（", 1))
pr=pr.replace(u"U-31 … U-1987（R504 现读抬到最新一节）", u"U-31 … U-1993（R505 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R504 这一段（R478 起写；R504 续到 504 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R505 这一段（R478 起写；R504 续到 504、R505 续到 505 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R504 节 ② 为准", u"的 R505 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK")
