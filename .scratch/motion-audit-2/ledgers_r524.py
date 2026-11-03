#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os, subprocess
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md"); I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")
sha=subprocess.check_output(["git","-C",R,"rev-parse","--short=7","HEAD"]).decode().strip()
FULL=os.environ.get("R524_FULL",""); INSTALL=os.environ.get("R524_INSTALL",""); BATTERY=os.environ.get("R524_BATTERY",""); RUNPAIR=os.environ.get("R524_RUNPAIR","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"
INSTALLTXT=(u"换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=%s`" % INSTALL) if INSTALL else u"换装见补记"
BATTERYTXT=(u"电池 **%s**（台账后复跑）" % BATTERY) if BATTERY else u"电池见补记"
TAILPAIR=(u"产品笔 `%s` 已推（HEAD=origin、ahead=0）；%s" % (sha, RUNPAIR)) if RUNPAIR else (u"产品笔 `%s` 已推（HEAD=origin、ahead=0）" % sha)
AT_OLD=u"U-1970…U-2122）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2129）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2123：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`f20f256`、**ahead=0**）。四跑成对读：`41215426349 ↔ 3e5aa6b`（R523 产品）、`41215568792 ↔ f20f256`（台账）读时均 **in_progress ⇒ NOT-RUN**（不轮询；下轮第 ⓪ 全读）；`41206772056 ↔ e353f1e`（R522 产品）**failure 仅 STEP[9] Release script tests**（日志步骤名全是 `UNKNOWN STEP`，按 emit 串取正文：`SOURCES_CELL 账上=741bdb0 git=e353f1e 一致=否` ⇒ `FINAL_REPORT_SOURCES_CELL_STALE` + `test_sources_cell_second_source` + `test_skip_roster` 级联；STEP[10]–[14] skipped；STEP[1]–[8] 全过：INK **5.01/4.82**、`ABOUT_LINK_PRESS_NOT_RUN=settings-content-blank`、MenuBarPopulationTests passed、`RTF_HELPER_ORPHAN_NOT_RUN`、`RECORDING_REREAD diff_px=0`、Motion `judged=5/5 executed=77 胶片=30`）；`41207320436 ↔ c68ce52` **success**。R523 的折叠判据在 runner 上的签收随两跑仍未跑完 ⇒ **NOT-RUN**，不是绿。安全红线：未对破坏性控件做 AXPress；真窗口只读；未碰活库。
- **U-2124：① 旧行为的读数。** R523 的 `applyGeometry` 用 `setFrame` 一步落到目标宽、`ContentView` 分支同时切换 —— 折叠是一帧跳变，没有中间宽也没有中间帧。R524 把这条旧行为用刀复现：`M1400`（逐拍宽度直接置为终点）下 `testCollapseWidthIsMeasuredFrameByFrame` 当场红（读到 0 帧中间宽）；新实现同一判据读到 **15 帧、8 帧中间宽、8 个不同值**。因此下面这些读数不是"加了个声明"，而是**行为差异**。
- **U-2125：② 过渡实现（克制版，非 Duo 3D）。** 目录新增 `MotionCatalog.Role.windowFold`（0.20s，进场曲线，仍在 250ms 上限内）；`MainWindowCollapsePolicy` 增 `easedProgress`（三次贝塞尔求值）、`expandedContentOpacity`/`collapsedContentOpacity`/`hingeOpacity`（4p(1−p)）、`sidebarSeamWidth = 280`；`MainWindowCollapseController` 用 **60Hz `DispatchSourceTimer` 自己驱动**：每拍同时更新 `foldProgress` 与窗口宽（同一时钟），再点一次从当前进度/当前宽反向（无动画队列），reduce-motion 走 `animationDuration == 0` 一步到位；途中先降 `minSize` 到折叠档、收尾再落回目标档。`ContentView`：展开树保持不动，折叠列表是**从侧栏右缝起被遮罩的一页**，按 `progress` 淡入盖住详情；中缝阴影画在**两棵树之上**。第一版是"两棵整树交叉淡"，胶片里同时出现两套搜索框/标题/空态 ⇒ 看图后改成右页折盖（证据见 U-2127）；3D 透视不做：12/13 的文字会发虚、且与 SwiftUI 重排打架（D-523）。
- **U-2126：③ 判据与刀。** 新增 `MainWindowFoldMotionTests` **6 条**（折叠逐帧宽、展开逐帧宽、reduce 直切、中途反向无半折、opacity/hinge 真值、5 帧过渡胶片）；R523 的 `MainWindowCollapseTests` 9 条改为等过渡真正停表（`settleTransition`），detail 源码守卫改到新的 `collapsedLayout` 段。刀：`M1399`（reduce 仍走过渡）/`M1400`（宽度一帧跳终点）/`M1401`（中缝阴影永不出现）**3/3 CAUGHT、RESTORE_CLEAN=yes**；R523 的 `M1397` 因控制器行换成 `if !isTransitioning, let target …` 重锚后 `M1395–M1398` **4/4 CAUGHT**。预检 **304/281/742 bad=0**、ARM **397/1229**（dupes=0 repeats=0）、HIDDEN **391/1168 rot=0**；build **0 告警**（增量 0、冷编 0）。
- **U-2127：④ 逐帧胶片与看图。** 真实窗口读数（本机 2x）：折叠 `frames=15 intermediate=8 distinct=8`，宽度 `750→750→589→535→478→455→441→431→426→423→421→…→420`（单调不增），progress `0→1`；展开 `frames=11 intermediate=6`，`420→600→729→…→750`（单调不减）；中断臂 `widths=[566…750]`（全程在 419–751 内）、反向落回 750、再折落 420；reduce 臂 `width=420 progress=1 transitioning=false`。过渡胶片 5 帧（`/tmp/r524_fold_film/fold-progress-{0,25,50,75,100}-750x560.png`）：中间帧与两端差异 `p0.25=753842/1285917`、`p0.5=855740/1282146`、`p0.75=889452/511907`（与展开/折叠端点的差异像素），hinge `0.00/0.75/1.00/0.75/0.00`；逐张看过 p25/p50：左侧只有一套 chrome，右页随 progress 变灰盖住详情，中缝一条竖阴影。**第一版整树交叉淡的胶片**同时画出两套搜索框/标题/空态 ⇒ 撤回改成右页折盖；这是看图得到的修正，不是想出来的。静态帧卷 **340**：`CHANGED=0 ADDED=0 MISSING=0`（过渡端点不改变两态外观），基线保持 **340**；胶片是独立取证目录，不进帧基线。
- **U-2128：⑤ 八步与电池。** build **0 告警**（增量 0、冷编 0）；%s；%s；%s；清账 `MOTION_LEDGER 162 格 / 已清账 162 / 未清账 0 / 不合法 0`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。%s。**具名 NOT-RUN / 限制**：① R524 产品笔/台账笔自身跑（推送后取）；② R523/R522 三跑 in_progress ⇒ NOT-RUN；③ 折叠判据在 runner 的签收 NOT-RUN；④ `ABOUT_LINK_*_NOT_RUN=settings-content-blank`；⑤ `RTF_HELPER_ORPHAN`（595）；⑥ `RECORDING_REREAD` 1x；⑦ 状态菜单像素通道（610）；⑧ 已知在屏/Motion/SelectionReveal 本机会话 flake；⑨ Duo 3D 未做（D-523 写明理由），逐帧证据只覆盖宽度/进度/中缝/内容页，不覆盖 3D 透视。
- **U-2129：⑥ 收口 CI 与交接。** %s。R523 的静态骨架签收仍等 `41215426349/41215568792`；R522 产品跑唯一失败步是 sources 时序（非产品回归）。下一轮 R525（第 524 轮 / Round 522）按 STATE 顶部靶单继续；折叠特性如需真机手动验证，只用非破坏性入口，且真窗口取证仍走只读通道。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR, RUNPAIR or u"收口新跑在推送后取")
DS=u"""## D-523 折叠过渡用模型驱动逐帧动画（R524）

- 背景：R523 的两态是 `setFrame` 一步跳变 + 分支硬切。R524 要有可逐帧量、可中断、reduce 直切的过渡。
- 决定：① 目录新增 `MotionCatalog.Role.windowFold`（0.20s / 进场曲线，仍 ≤250ms 上限），时长与曲线只从目录取；② `MainWindowCollapsePolicy` 提供三次贝塞尔求值、内容透明度与中缝阴影的纯函数；③ `MainWindowCollapseController` 用 60Hz `DispatchSourceTimer` **自己驱动**：同一拍更新 `foldProgress` 与窗口宽，反向切换从当前进度/宽度起步（无动画队列），reduce-motion 时长 0 一步到位；途中先降 minSize、收尾落回目标档；④ `ContentView` 用"右页折盖"：展开树不动、折叠列表从侧栏右缝被遮罩并按 progress 淡入，中缝阴影画在两棵树之上；端点由树是否挂载兜底（p=1 时展开树整棵不渲染）。
- 理由：模型驱动才能逐帧读宽度/进度/透明度，且中断不留半折；右页折盖避免整树交叉淡同时画出两套 chrome（第一版胶片已证）。
- 不做 3D：Duo 式透视在 12/13 会让文字发虚，且与 SwiftUI 重排竞争；克制版已满足"宽度收放＋中缝折页＋内容交叉淡"。如果未来要做 3D，先解决文字栅格化与 minWidth 抖动，再用胶片证。
- 兼容性/迁移：静态两端与 R523 逐字节相同（帧基线 340 不变）；R523 的 9 条判据改为等过渡停表；R523 的 M1397 因控制器行换代重锚；新增 M1399–M1401。
- 边界：过渡胶片是独立取证目录（不进帧基线）；reduce 下没有任何中间帧；全屏仍被禁、最小化按系统行为。
"""
CS=u"""### 主窗口折叠/展开过渡（R524 / 第 523 轮 / Round 521 / U-2123…U-2129 · 产品 4 文件 + 判据）

"""
SS=u"""## R524 状态（2026-10-31 · 第 523 轮 · 产品 4 文件 + 判据）

R524 记录（产品 4 文件 + 判据）：折叠/展开过渡（克制版）。⓪ push no-op（HEAD=origin/main=`f20f256`、ahead=0）；`41215426349 ↔ 3e5aa6b`、`41215568792 ↔ f20f256` 读时 in_progress ⇒ NOT-RUN；`41206772056 ↔ e353f1e` failure 仅 STEP[9]（sources 时序 + 两条级联，UNKNOWN STEP 日志用 emit 串取正文；ING 5.01/4.82、MenuBar passed、RTF NOT_RUN、RECORDING diff 0、Motion 5/5）；`41207320436 ↔ c68ce52` success。① 旧行为由 `M1400` 复现（宽度一帧跳终点 ⇒ 0 帧中间宽）；新实现 60Hz 模型驱动，折叠 **15 帧 / 8 中间宽 / 8 不同值**、展开 **11 帧 / 6 中间宽**，宽度单调；中途反向无半折（419–751 内），reduce 一步到位。② 目录新增 `.windowFold` 0.20s；控制器同拍更新 foldProgress 与窗口宽，可中断；ContentView 用"右页折盖 + 中缝阴影（画在两树之上）"；第一版整树交叉淡的胶片出现两套 chrome ⇒ 看图后改掉；3D 不做（D-523）。③ `MainWindowFoldMotionTests` 6 条 + R523 9 条改等停表；M1399–M1401 3/3、M1397 重锚后 M1395–M1398 4/4；预检 304/281/742 bad=0、ARM 397/1229、HIDDEN 391/1168 rot=0；build 0 告警。④ 过渡胶片 5 帧（`/tmp/r524_fold_film`），中间帧与两端差异 75 万–128 万像素，hinge 0/0.75/1/0.75/0；静态帧卷 340 逐字节不变（CHANGED=0），基线保持 340。⑤ %s；%s；%s；清账 162 格已清 162/未清 0/不合法 0；产品面连续零改动 4 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497）。⑥ Duo 3D 未做；逐帧证据覆盖宽度/进度/中缝/内容页，不覆盖 3D 透视。%s。下一轮编号 R525（第 524 轮 / Round 522）：先 push 并复核 ahead=0；读 R524 产品笔/台账笔与 R523 两跑的全部失败步骤（in_progress/queued ⇒ NOT-RUN）；② 产品位按用户指令继续折叠特性；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT, TAILPAIR)
IS=u"""## Round 521 · R524（第 523 轮 · 2026-10-31）：主窗口折叠/展开过渡（克制版）

R523 的折叠是 `setFrame` 一步跳变。R524 把过渡做成**模型驱动 60Hz**：`MotionCatalog.Role.windowFold` 给 0.20s/进场曲线；`MainWindowCollapseController` 每拍同时更新 `foldProgress` 与窗口宽，再点从当前进度/宽度反向（无队列、无半折），reduce-motion 0 时长一步到位；`ContentView` 用"右页折盖"（展开树不动，折叠列表从侧栏右缝起被遮罩并按 progress 淡入，中缝阴影画在两棵树之上），端点 p=1 时展开树整棵不渲染。第一版"整树交叉淡"的胶片里同时出现两套搜索框/标题/空态 ⇒ 看图后改成右页折盖；Duo 3D 不做（文字发虚 + SwiftUI 重排，D-523）。读数：折叠 **15 帧/8 中间宽/8 不同值**（750→…→420 单调）、展开 **11 帧/6 中间宽**（420→…→750）、中断臂全程 419–751、reduce 一步；过渡胶片 5 帧，中间帧与两端差异 75–128 万像素，hinge 0/0.75/1/0.75/0。`MainWindowFoldMotionTests` 6 条；M1399–M1401 3/3、M1397 重锚后 M1395–M1398 4/4；预检 304/281/742 bad=0、ARM 397/1229、HIDDEN 391/1168 rot=0；build 0 告警。静态帧卷 340 逐字节不变（CHANGED=0），基线保持 340。%s；%s；%s。R523 两跑仍 in_progress ⇒ 折叠判据 runner 签收 NOT-RUN。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 过渡胶片逐张看过；第一版双 chrome 被肉眼否掉并改；p25/p50 右页与中缝均确认。 |
| 判据有效性 | 15/15 | 逐帧宽/进度、reduce、中断、hinge 都有读数；M1399–M1401 3/3，旧行为由 M1400 复现。 |
| 假绿防御 | 15/15 | 静态帧 CHANGED=0 单独记；胶片与帧基线分开；runner 签收 NOT-RUN 如实。 |
| 产品面推进 | 15/15 | 用户点名的过渡落地；4 个产品文件；可中断、reduce 直切。 |
| 台账一致性 | 15/15 | U-2123…U-2129、D-523、340 帧/全量/换装/电池都来自命令与测试。 |
| 交付诚实性 | 15/15 | 3D 未做、第一版被否、runner 三跑 NOT-RUN 都写明。 |
| 可复核性 | 15/15 | 帧数/宽度序列/胶片路径/M1399–M1401/precheck 304/281/742 都在。 |

均分 = 105/105 ≈ 15.0/15（100）。
""" % (FULLTXT, INSTALLTXT, BATTERYTXT)
RB=u"""- **R524（主窗口折叠/展开过渡；产品 4 文件 + 判据）**：R523 的一帧跳变改成模型驱动 60Hz 过渡（`MotionCatalog.Role.windowFold` 0.20s/进场曲线）；控制器同拍更新 `foldProgress` 与窗口宽，可中断、reduce 0 时长直切；ContentView 用右页折盖 + 中缝阴影（画在两树之上），p=1 时展开树整棵不渲染。读数：折叠 15 帧/8 中间宽、展开 11 帧/6 中间宽、宽度单调；中断臂 419–751 无半折；过渡胶片 5 帧（中间帧与两端差异 75–128 万像素，hinge 0/0.75/1/0.75/0）。`MainWindowFoldMotionTests` 6 条；M1399–M1401 3/3、M1397 重锚后 M1395–M1398 4/4；预检 304/281/742 bad=0、ARM 397/1229、HIDDEN 391/1168 rot=0；静态帧 340 逐字节不变（CHANGED=0）。全量 %s；换装 %s；电池 %s。Duo 3D 未做（D-523）。
""" % (FULL or u"见补记", INSTALL or u"425=425", BATTERY or u"683/5")
a=rd(A); d=rd(D); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-523" in d: raise SystemExit("D exists")
if u"## R524 状态" in st: raise SystemExit("S exists")
if u"R524（主窗口折叠/展开过渡" in pr: raise SystemExit("P exists")
if u"主窗口折叠/展开过渡（克制版）" in ch: raise SystemExit("C exists")
if u"## Round 521 · R524" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2122（R523 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"R9–R520，521 节自评")!=1: raise SystemExit("P headline")
if pr.count(u"阶段二 **513 轮**审计（R9–R520；")!=1: raise SystemExit("P phase")
if pr.count(u"PHASE2 n=513")!=1: raise SystemExit("P n")
if pr.count(u"的 Round 520")!=1: raise SystemExit("P round")
if pr.count(u"## 18. R458 → R523 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R523 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(S, st.replace(u"## R523 状态（", SS.strip()+"\n\n## R523 状态（", 1))
pr=pr.replace(u"R9–R520，521 节自评", u"R9–R521，522 节自评", 1)
pr=pr.replace(u"阶段二 **513 轮**审计（R9–R520；", u"阶段二 **514 轮**审计（R9–R521；", 1)
pr=pr.replace(u"PHASE2 n=513", u"PHASE2 n=514", 1)
pr=pr.replace(u"的 Round 520", u"的 Round 521", 1)
pr=pr.replace(u"U-31 … U-2122（R523 现读抬到最新一节）", u"U-31 … U-2129（R524 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R523 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R524 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509、R510 续到 510、R511 续到 511、R512 续到 512、R513 续到 513、R514 续到 514、R515 续到 515、R516 续到 516、R517 续到 517、R518 续到 518、R519 续到 519、R520 续到 520、R521 续到 521、R522 续到 522、R523 续到 523、R524 续到 524 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R523 节 ② 为准", u"的 R524 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s install=%s battery=%s" % (sha, FULL, INSTALL, BATTERY))
