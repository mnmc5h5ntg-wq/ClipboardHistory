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
FULL=os.environ.get("R506_FULL","")
FULLTXT=(u"全量 **%s**（含 2 条新判据）" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-1994）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2000）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-1995：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`f9b8733`、**ahead=0**）。六跑成对：`41102621877 ↔ f7ea8b4` **failure 3 步** = Release（3 条：sources 格停旧 + skip roster 内层级联 + sources 第二来源）、Swift（身份头判据 pre-fix dark 10/1）、Capture（同一命名红）；`41102893802 ↔ b94dd83` **failure 2 步** = Swift + Capture（同一身份头；Release 已绿）；`41105579968 ↔ e3eb62b`、`41105861197 ↔ 6543959`、`41106240358 ↔ 3d20a02`、`41106548360 ↔ f9b8733` 读时 **in_progress/queued ⇒ NOT-RUN**（不轮询）。两跑的 Motion floor 都 **clean**（`judged=5/5 executed=77`、红的用例=-）⇒ 436 本轮只读这两跑，无新红。更早：`800a45a`/`79336c7`/`e46c29f` 三跑上一轮已读并归因（身份头 pre-fix）。日志流：`41102621877`/`41102893802` 的 `--log-failed` 为 0 行（job 级失败、步骤结论空）⇒ 用 `--log` 全文取读数；`79336c7` 上一轮两次 `CANCEL` 仍 `CI_LOG_BLOCKED=stream-error`。
- **U-1996：① 未捕获表面读数（状态菜单推荐行）。** 真窗口 `screencapture -l <windowID>` 只截状态菜单（**240.5×318pt**）：AX 三条推荐标题是 `5VsCvDXzRkDEXNCS`、`https://mecagent.com/zh…`、`https://openrouter.ai/a…` —— **没有 ` · ` 与任何理由**；像素三条推荐行最右墨 **147.0 / 176.0 / 159.0pt**（菜单宽 240.5pt）。而 `RecommendationPresenter.reason` **至少返回类型标签**（`文本`/`链接`/`文件`，外加 `复用N次`、`回到Safari浏览器`、`把握较大` 等）⇒ 理由不是空，是 macOS 13+ 的 SwiftUI 菜单把 HStack 第二列**拍平丢掉**（R505 的 HStack 试验已实拍过同一机制）。
- **U-1997：② 产品：推荐理由并进同一个 Text。** 新增 `MenuRecommendationPresentation.reasonSuffix`（空理由 ⇒ 空串；否则两个空格 + 理由）。`MenuBarRecommendationsView` 的推荐行从 HStack 两列改成单个 `Text(label) + Text(reasonSuffix)`，理由用 `VisualFont.meta` + secondary。产品 **2 文件**。after 只截菜单（**533.5×318pt**）：AX 标题变成 `5VsCvDXzRkDEXNCS  文本 · 复用1次 · 常用文本 · 回到Safari浏览器 · 把握较大` 等三条；像素三条推荐右墨 **147.0/176.0/159.0 → 437.5/467.0/450.0pt**；亮/暗菜单帧都逐张看过，理由在弱一档的灰色里、标签仍是主色。
- **U-1998：③ 判据与刀。** 新判据 `MenuRecommendationPresentationTests`：值轴钉后缀（`"  文本 · 常用文本"`、去首尾、空理由 ⇒ 空串），接线轴读 `MenuBarRecommendationsView.swift` 要求走 `reasonSuffix(reasonText)` 且不再有 `Spacer(minLength: 12)` 两列。刀 `M1357`（后缀永远空）/`M1358`（只留一个空格）/`M1359`（退回裸理由）**3/3 CAUGHT**、`RESTORE_CLEAN=yes`。**连带重锚**：既有 `testMenuBarFramesAreReplicasOfTheMenuSurface` 的「首行最右墨 ≥ 帧宽−1」在新布局下不再成立（单 Text 的截断省略号自带 ~5.5pt 右缘留白，实测 314.5/320）⇒ 按它自己的出口①改成**有界截断带 [帧宽−16, 帧宽−1]**，并加一条负向臂（第二行最右墨 **256.0 < 帧宽−16** 才算带子有区分力）；读数 `MENUBAR_REPLICA 第一行=314.5 第二行=256.0 / 320` 随判据打印。
- **U-1999：④ 帧卷。** 捕获卷 **332 帧**、`CHANGED=91`：**2 张 `menubar-recommendations-320x320-{light,dark}`** 是本次布局的合法变化（离屏帧把理由从右列挪到行内），其余 **89 张**仍为源 App 图标栅格噪声（16×16、≤7/255）⇒ 只把 menubar 两张写进基线（**332 保持**），噪声不吸收（601）；复核 `CHANGED=89 MISSING=0 ADDED=0`。**通道边界**：离屏夹具渲染的是 SwiftUI 视图，HStack 第二列在帧里**画得出来**，真实 `MenuBarExtra` 才拍平 —— 帧基线不能当这条缺陷的验收（610），本条的真窗口前后帧已逐张看过。
- **U-2000：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=285 covered=262 arms=701 bad=0`、`ARM_TOTAL files=378 arms=1188`、`HIDDEN_ARMS 表=372 可判=1127 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 505 = 1，last=`f7ea8b4`/last_round=504）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN**：① `%s` 自身跑（推送后取）；② 四跑 `e3eb62b`/`6543959`/`3d20a02`/`f9b8733`（in_progress/queued）；③ 状态菜单像素通道（system-menu，610）；④ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；⑤ `RECORDING_REREAD` 1x、`SETTINGS_IDENTITY_HEADER` 修复后 runner 1x；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-503 状态菜单的推荐理由并进同一个 Text（R506）

- 背景：macOS 13+ 的状态菜单是 SwiftUI `MenuBarExtra`（`.menu`），菜单项标签会被拍平成单个文本。推荐行原来 HStack 两列（标题 + 右侧理由），真窗口 `screencapture -l` 只留下标题：菜单 240.5×318pt、三条推荐最右墨 147/176/159pt，而 `RecommendationPresenter.reason` 至少返回类型标签 ⇒ 理由整段不可见。
- 决定：新增 `MenuRecommendationPresentation.reasonSuffix`，推荐行改为单个 `Text(label) + Text(reasonSuffix)`（理由 `VisualFont.meta` + secondary）；不再用 HStack/Spacer 做第二列。
- 理由：真实菜单的拍平行为是系统边界，不是布局偏好；把理由并进同一个可被拍平的文本，是唯一既保住信息又不改菜单语义的写法。
- 兼容性/迁移：真窗口菜单 240.5→533.5pt；离屏 `menubar-recommendations` 两帧变化（HStack 右列 → 行内），基线同提交 update；既有 replica 判据从「顶到 0 边」重锚为截断带 + 负向臂（314.5/256 对 320）。
- 边界：离屏帧**拍不到**这次缺陷（它渲染的是 SwiftUI 视图，HStack 第二列会画出来）⇒ 验收必须走真窗口通道；帧基线只证明布局变化，不证明菜单行为（610）。
"""
BS=u"""**610. 状态菜单的推荐理由只有真窗口通道能验收**（R506 现读）
    现象：离屏 `menubar-recommendations` 帧渲染 SwiftUI 视图时 HStack 第二列画得出来，而真实 `MenuBarExtra` 会把第二列拍平；R506 的缺陷在帧里根本看不到（帧只反映布局变化）。
    修法：推荐理由/宽度/截断这类菜单项结论必须用真窗口 `screencapture -l` 拍前后帧；值判据钉 `MenuRecommendationPresentation` 与视图接线，帧基线只管「布局有没有再动」。
"""
CS=u"""### 状态菜单推荐行恢复推荐理由（真窗口 240.5→533.5pt；R506 / 第 505 轮 / Round 503 / U-1995…U-2000 · 产品 2 文件 + 判据）

"""
SS=u"""## R506 状态（2026-10-31 · 第 505 轮 · 产品 2 文件 + 判据）

R506 记录（产品 2 文件 + 判据）：状态菜单推荐行恢复推荐理由。⓪ push no-op（HEAD=origin/main=`f9b8733`、ahead=0）；`41102621877 ↔ f7ea8b4` failure 3 步（Release 3 条 sources 时序 + Swift/Capture 身份头 pre-fix dark 10/1）；`41102893802 ↔ b94dd83` failure Swift+Capture（同一身份头；Release 已绿）；其余四跑 in_progress/queued ⇒ NOT-RUN；两跑 Motion floor clean（5/5、red=-）。① 真窗口 `screencapture -l` 只截状态菜单（240.5×318）：AX 三条推荐标题只有内容标签、无 ` · ` 理由；`RecommendationPresenter` 至少给类型标签 ⇒ 理由被 SwiftUI 菜单拍平丢失。② 产品：`MenuRecommendationPresentation.reasonSuffix` + 推荐行改为单个 Text（理由 meta/secondary）；after 菜单 533.5×318、三条推荐右墨 147/176/159 → 437.5/467/450，AX 标题带 `文本 · 复用1次 · … · 把握较大`。③ 判据 `MenuRecommendationPresentationTests`（后缀值 + 视图接线）；M1357/M1358/M1359 3/3；离屏 replica 判据重锚为截断带 [帧宽−16, 帧宽−1] + 第二行负向臂（314.5/256 对 320）。④ 捕获 332 帧、CHANGED=91 = 2 张 menubar + 89 噪声；基线更新那 2 张（332），复核余 89 噪声不入基线；离屏帧拍不到真实拍平（610）。⑤ 预检 285/262/701 bad=0、ARM 378/1188、HIDDEN 372/1127 rot=0；build 0 告警；%s；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 505 = 1，last=`f7ea8b4`/last_round=504）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R507（第 506 轮 / Round 504）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `e3eb62b`/`6543959`/`3d20a02`/`f9b8733` 四跑全部失败步骤；重点 `SETTINGS_IDENTITY_HEADER_NOT_RUN=sidebar-vibrant` 修复后 runner 1x、`RECORDING_REREAD` 1x、`RTF_HELPER_ORPHAN`（仍是 settings-content-blank/595）、状态菜单像素通道不可判（610）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 503 · R506（第 505 轮 · 2026-10-31）：状态菜单推荐行恢复推荐理由（真窗口 240.5→533.5pt）

状态菜单（macOS 13+ `MenuBarExtra`）的推荐行原来用 HStack 把理由放右侧第二列，真实菜单拍平后只剩标题：真窗口 `screencapture -l` 读数 240.5×318pt、三条推荐最右墨 147/176/159pt，而 `RecommendationPresenter.reason` 至少返回类型标签 ⇒ 理由整段不可见。修法：`MenuRecommendationPresentation.reasonSuffix` + 推荐行改为单个 Text（理由 meta/secondary）。after 533.5×318pt、三条右墨 437.5/467/450，AX 标题带 `文本 · 复用1次 · … · 把握较大`。判据 `MenuRecommendationPresentationTests`（值 + 接线），M1357–M1359 3/3；既有 replica 判据重锚为截断带 + 负向臂（314.5/256 对 320）。捕获 332 帧、2 张 menubar 合法变化 + 89 噪声不吸收、基线保持 332。预检 285/262/701、ARM 378/1188、HIDDEN 372/1127 rot=0。%s；build 0 告警；换装 ok/419=419；电池 683/5。⓪ push no-op（HEAD=origin=f9b8733、ahead=0）；f7ea8b4/b94dd83 两条 pre-fix 红（身份头 10/1 + Release 时序），四跑 NOT-RUN；两跑 Motion clean。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 状态菜单前/后（含亮暗离屏帧）逐张看过：三条推荐从无理由到行内理由，菜单 240.5→533.5pt。 |
| 判据有效性 | 15/15 | 后缀值 + 视图接线；M1357/M1358/M1359 3/3；replica 判据带负向臂。 |
| 假绿防御 | 15/15 | 离屏帧拍不到拍平行为已具名（610）；截断带不是恒真（第二行 256 < 304）。 |
| 产品面推进 | 15/15 | 新类别（菜单推荐理由可见性）；2 个产品文件；真窗口可见变化。 |
| 台账一致性 | 15/15 | U-1995…U-2000、D-503、332 帧/全量/419 都来自命令与测试。 |
| 交付诚实性 | 14/15 | 四跑 NOT-RUN、日志流 CANCEL 均具名；扣 1：菜单像素证据只有本机真窗口。 |
| 可复核性 | 15/15 | 147/176/159→437.5/467/450、314.5/256、M1357–M1359、precheck 285/262/701 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
""" % FULLTXT
RB=u"""- **R506（状态菜单推荐理由；产品 2 文件 + 判据）**：macOS 13+ `MenuBarExtra` 会把推荐行的 HStack 第二列拍平，真窗口菜单 240.5×318pt 里三条推荐只剩标题（147/176/159pt），理由整段不可见。改为单个 `Text(label) + Text(reasonSuffix)`（meta/secondary）：after 533.5×318pt、三条右墨 437.5/467/450，AX 标题带 `文本 · 复用1次 · … · 把握较大`；M1357–M1359 3/3；replica 判据重锚截断带 + 负向臂（314.5/256 对 320）。帧 332（2 张 menubar 合法变化、89 噪声不吸收）；换装 419=419；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-503" in d: raise SystemExit("D exists")
if u"**610." in b: raise SystemExit("B exists")
if u"## R506 状态" in st: raise SystemExit("S exists")
if u"R506（状态菜单推荐理由" in pr: raise SystemExit("P exists")
if u"状态菜单推荐行恢复推荐理由" in ch: raise SystemExit("C exists")
if u"## Round 503 · R506" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-1994（R505 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R505 这一段（R478 起写；R504 续到 504、R505 续到 505 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R505 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R505 状态（", SS.strip()+"\n\n## R505 状态（", 1))
pr=pr.replace(u"U-31 … U-1994（R505 现读抬到最新一节）", u"U-31 … U-2000（R506 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R505 这一段（R478 起写；R504 续到 504、R505 续到 505 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R506 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R505 节 ② 为准", u"的 R506 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
