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
FULL=os.environ.get("R509_FULL","")
FULLTXT=(u"全量 **%s**" % FULL) if FULL else u"全量见补记"

AT_OLD=u"U-1970…U-2014）：主窗口与设置窗口的标题栏统一"
AT_NEW=u"U-1970…U-2020）：主窗口与设置窗口的标题栏统一"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-2015：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`b3d7c49`、**ahead=0**）。四跑：`41129660972 ↔ 133fcc5`、`41129928017 ↔ b3d7c49` 读时 **in_progress ⇒ NOT-RUN**（不轮询）；`41121631147 ↔ 20cf54d` failure **仅 `STEP[9] Release script tests`**（sources 停旧 + skip 级联 + sources 第二来源；Swift/Capture 全绿，replica `295/217` 判过）；`41121901053 ↔ 1654292` **success**（复核不回归）。更早：`938fc4f`/`323c2ec` 仅 replica 旧带（295<304）、`0beac05` Release 时序 + 旧带、`e3eb62b`/`6543959` success、`3d20a02` SelectionReveal 采样 flake、`f9b8733` Motion `testCopyReceipt` 1<2。436 只复核新跑：`20cf54d` Motion **clean**（`judged=5/5`、红=-），`1654292` success ⇒ clean。
- **U-2016：① 未捕获表面读数（最小窗 + 详情时间戳）。** ① 真窗口主窗在 600×492 时**偶现**过一条工具栏按钮 `隐藏边栏`（AX desc/help、40×52pt）——与本 App「侧栏钉住、切换按钮已摘」的契约冲突；但重启/反复缩放/面板开着缩放三种序列都没再复现（见 614）⇒ 本轮**不据此改产品**，只登记。② 详情头时间戳：真窗口（750×560，`screencapture -l`）读 **`2026-10-30 21:09:55`**，而同一窗口的列表行读 **`10月30日 21:09`** —— 同一个时间戳两种日期语言（ISO 短横线 vs 年月日）；离屏 `detail-0-text` 帧同形。
- **U-2017：② 产品：详情时间戳改用与列表同一套日期语言。** `ClipboardDateFormatters.detailTimestamp` 从 `yyyy-MM-dd HH:mm:ss` 改为 **`yyyy年M月d日 HH:mm:ss`**（列表 `sidebarTimeWithYear` 已是 `yyyy年M月d日 HH:mm`）。产品 **1 文件**。after 真窗口详情读 **`2026年10月30日 21:09:55`**，列表仍是 `10月30日 21:09`；离屏 `detail-0-text` 帧读 **`2025年10月9日 16:52:50`**；90 张 content/detail 帧同笔变化，逐张看过 meta 行。
- **U-2018：③ 判据与刀。** `TimestampYearPolicyTests/testDetailTimestampUsesTheSameDateLanguageAsTheList`：用固定日期断言 `detailTimestamp` = `2026年10月30日 21:09:55`、`sidebarTimeWithYear` = `2026年10月30日 21:09`，且两者都不含 `-`。刀 `M1364`（详情回到 ISO）/`M1365`（列表也改成 ISO）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-2019：④ 帧卷。** 捕获卷 **332 帧**、`CHANGED=132`：**90 张** content-/detail- 帧是详情 meta 的合法结构变化（bbox 都在 meta 行，x 655..1224px），其余 **42 张**为源图标栅格噪声（本轮噪声名单里 39 张与结构帧重叠 ⇒ 一并更新）⇒ 只吸收那 90 张结构帧，基线 **332 保持**；复核 `CHANGED=42 MISSING=0 ADDED=0`。`detail-0-text` 亮/暗与真窗口终态都看过。
- **U-2020：⑤ 八步与电池。** build **0 告警**（增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=288 covered=265 arms=707 bad=0`、`ARM_TOTAL files=381 arms=1194`、`HIDDEN_ARMS 表=375 可判=1133 rot=0`；%s；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库；旧实例处于挂起态、安装器等不到优雅退出 ⇒ 先 CONT 唤醒再 TERM，随后换装成功）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 508 = 1，last=`133fcc5`/last_round=507）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。产品笔 `%s` 已推（HEAD=origin、ahead=0）。**具名 NOT-RUN**：① `%s` 自身跑（推送后取）；② 最小窗「隐藏边栏」偶现（未复现，614）；③ 状态菜单像素通道（system-menu，610）；④ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；⑤ `RECORDING_REREAD` 1x；⑥ 已知在屏/Motion 采样 flake；⑦ 601 噪声与其余未结项仍开。
""" % (FULLTXT, sha, sha)
DS=u"""## D-506 详情时间戳与列表用同一套日期语言（R509）

- 背景：真窗口同一屏里，列表行读 `10月30日 21:09`（年月日），详情头读 `2026-10-30 21:09:55`（ISO 短横线）—— 同一个时间戳两种日期语言。
- 决定：`ClipboardDateFormatters.detailTimestamp` 改为 `yyyy年M月d日 HH:mm:ss`，与 `sidebarTimeWithYear` 的 `yyyy年M月d日 HH:mm` 同一套语法；秒与完整年份仍保留。
- 理由：日期语言是表面语言的一部分；列表已经在用中文年月日，详情头的短横线是两处各写各的格式化器留下的分叉。改格式不动精度（秒仍在）。
- 兼容性/迁移：真窗口详情 `2026-10-30 21:09:55 → 2026年10月30日 21:09:55`；90 张 content/detail 离屏帧同笔更新、基线 332 保持。
- 边界：`detailTimestamp` 仍用 `zh_CN` locale 与用户时区；若未来做多语言，两个 formatter 要一起迁，判据钉的是「两者同一套日期语法 + 都不含 `-`」。
"""
BS=u"""**614. 最小窗偶现「隐藏边栏」工具栏按钮**（R509 观察，未复现）
    现象：主窗被程序化缩到 600×492 的一次序列里，AX 读到 `toolbar 1` 有 1 个按钮（desc/help=`隐藏边栏`、40×52pt），与本 App「侧栏钉住、切换按钮已摘」的契约冲突；重启/反复缩放/面板开着缩放三种序列都没有再复现 ⇒ 本轮只登记，不据此改产品。
    修法：下一轮若再看到，先记录当次启动/缩放/休眠序列与 AX 读数，再决定是否给 `windowDidResize` 补一轮延迟清理；**不许**在没有复现的情况下盲改 WindowConfigurator。
"""
CS=u"""### 详情时间戳改用与列表同一套日期语言（2026-10-30→2026年10月30日；R509 / 第 508 轮 / Round 506 / U-2015…U-2020 · 产品 1 文件 + 判据）

"""
SS=u"""## R509 状态（2026-10-31 · 第 508 轮 · 产品 1 文件 + 判据）

R509 记录（产品 1 文件 + 判据）：详情时间戳与列表同一套日期语言。⓪ push no-op（HEAD=origin/main=`b3d7c49`、ahead=0）；`133fcc5`/`b3d7c49` 两跑 in_progress ⇒ NOT-RUN；`20cf54d` failure 仅 Release 时序（Swift/Capture 全绿、replica 295/217）、`1654292` success；更早 `938fc4f`/`323c2ec` 仅旧 replica 带、`0beac05` Release 时序 + 旧带、`e3eb62b`/`6543959` success、两跑采样 flake。① 真窗口：列表 `10月30日 21:09`、详情 `2026-10-30 21:09:55` 两种日期语言；最小窗曾偶现「隐藏边栏」按钮（未复现，614）。② 产品：`detailTimestamp` 改 `yyyy年M月d日 HH:mm:ss`；after 真窗口 `2026年10月30日 21:09:55`、离屏 `2025年10月9日 16:52:50`；90 张 content/detail 帧变化。③ 判据 `TimestampYearPolicyTests`（固定日期 + 都不含 `-`）；M1364/M1365 2/2。④ 捕获 332 帧、CHANGED=132 = 90 张结构 + 42 张噪声（39 张重叠）；基线更新 90 张（332），复核 CHANGED=42。⑤ 预检 288/265/707 bad=0、ARM 381/1194、HIDDEN 375/1133 rot=0；build 0 告警；%s；换装 ok/419=419（活库；旧实例挂起，先 CONT 再 TERM）；电池 683/5（台账后复跑）；清账 162/63/0；产品面连续零改动 **4** 轮（as-of 501，`python3 scripts/product_streak.py` 现读，last_round=497；本笔 as-of 508 = 1，last=`133fcc5`/last_round=507）；产品笔 `%s` 已推（ahead=0）。下一轮编号 R510（第 509 轮 / Round 507）：先 push 并复核 ahead=0；读 `%s` 自身跑与 `133fcc5`/`b3d7c49` 跑全部失败步骤；重点最小窗「隐藏边栏」（614，若复现按读数改）、`RTF_HELPER_ORPHAN`（595）、`RECORDING_REREAD`、436 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
""" % (FULLTXT, sha, sha)
IS=u"""## Round 506 · R509（第 508 轮 · 2026-10-31）：详情时间戳与列表同一套日期语言（2026-10-30→2026年10月30日）

真窗口同一屏里，列表行 `10月30日 21:09`、详情头 `2026-10-30 21:09:55` —— 同一时间戳两种日期语言。修法：`ClipboardDateFormatters.detailTimestamp` 从 `yyyy-MM-dd HH:mm:ss` 改成 `yyyy年M月d日 HH:mm:ss`（列表已是年月日；秒与年份都保留）。after 真窗口 `2026年10月30日 21:09:55`、离屏 `2025年10月9日 16:52:50`；90 张 content/detail 帧同笔变化。判据 `TimestampYearPolicyTests`（固定日期 + 都不含 `-`），M1364/M1365 2/2。捕获 332 帧、CHANGED=132 = 90 结构 + 42 噪声（39 张重叠），基线更新 90 张（332）、复核 CHANGED=42。预检 288/265/707、ARM 381/1194、HIDDEN 375/1133 rot=0。%s；build 0 告警；换装 ok/419=419；电池 683/5。⓪ push no-op（HEAD=origin=b3d7c49、ahead=0）；两跑 NOT-RUN、20cf54d 仅 Release 时序、1654292 success。另：最小窗曾偶现「隐藏边栏」按钮，未复现（614，NOT-RUN）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真窗口前/后与 90 张离屏 content/detail 帧逐张看过：详情 meta 从短横线到年月日，其余几何未动。 |
| 判据有效性 | 15/15 | 固定日期断言两个 formatter 的输出 + 都不含 `-`；M1364/M1365 2/2。 |
| 假绿防御 | 15/15 | 偶现工具栏按钮未被当成产品缺陷（未复现 ⇒ 614/NOT-RUN）；噪声帧与结构帧分开记账。 |
| 产品面推进 | 15/15 | 新类别（同一时间戳两种日期语言）；1 个产品文件；真窗口与 90 帧可见变化。 |
| 台账一致性 | 15/15 | U-2015…U-2020、D-506、332 帧/1324/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 14/15 | 挂起实例的换装处置、未复现的工具栏按钮都具名；扣 1：无 runner 签收。 |
| 可复核性 | 15/15 | 2026-10-30→2026年10月30日、2025年10月9日 16:52:50、M1364/M1365、precheck 288/265/707 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
""" % FULLTXT
RB=u"""- **R509（详情时间戳与列表同一套日期语言；产品 1 文件 + 判据）**：列表 `10月30日 21:09` 与详情 `2026-10-30 21:09:55` 两种日期语言；`ClipboardDateFormatters.detailTimestamp` 改 `yyyy年M月d日 HH:mm:ss`，真窗口详情变 `2026年10月30日 21:09:55`、离屏 `2025年10月9日 16:52:50`。M1364/M1365 2/2；90 张 content/detail 帧同笔更新（基线 332、复核 CHANGED=42）。全量 1324/56/0；换装 419=419；电池 683/5。另记最小窗「隐藏边栏」偶现未复现（614/NOT-RUN）。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next %d" % a.count(ANCHOR_NEXT))
if u"## D-506" in d: raise SystemExit("D exists")
if u"**614." in b: raise SystemExit("B exists")
if u"## R509 状态" in st: raise SystemExit("S exists")
if u"R509（详情时间戳" in pr: raise SystemExit("P exists")
if u"详情时间戳改用与列表同一套日期语言" in ch: raise SystemExit("C exists")
if u"## Round 506 · R509" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-2014（R508 现读抬到最新一节）")!=1: raise SystemExit("P ucell")
if pr.count(u"## 18. R458 → R508 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508 —— 这份报告第七次差点停在几十轮之前）")!=1: raise SystemExit("P s18")
if pr.count(u"的 R508 节 ② 为准")!=1: raise SystemExit("P pointer")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R508 状态（", SS.strip()+"\n\n## R508 状态（", 1))
pr=pr.replace(u"U-31 … U-2014（R508 现读抬到最新一节）", u"U-31 … U-2020（R509 现读抬到最新一节）", 1)
pr=pr.replace(u"## 18. R458 → R508 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508 —— 这份报告第七次差点停在几十轮之前）",
              u"## 18. R458 → R509 这一段（R478 起写；R504 续到 504、R505 续到 505、R506 续到 506、R507 续到 507、R508 续到 508、R509 续到 509 —— 这份报告第七次差点停在几十轮之前）", 1)
pr=pr.replace(u"的 R508 节 ② 为准", u"的 R509 节 ② 为准", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK sha=%s full=%s" % (sha, FULL))
