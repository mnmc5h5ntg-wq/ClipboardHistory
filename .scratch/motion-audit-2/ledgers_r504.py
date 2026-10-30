#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io, os
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def rd(p): return io.open(p,encoding="utf-8").read()
def wr(p,t): io.open(p,"w",encoding="utf-8").write(t)
A=os.path.join(R,"AGENT_UI_AUDIT.md"); D=os.path.join(R,"AGENT_DECISIONS.md"); B=os.path.join(R,"AGENT_BACKLOG.md")
S=os.path.join(R,"AGENT_STATE.md"); P=os.path.join(R,"AGENT_FINAL_REPORT.md"); C=os.path.join(R,"CHANGELOG.md")
I=os.path.join(R,"AGENT_VISUAL_ITERATION.md")

AT_OLD=u"## 第 501 轮（R502 · 2026-10-30 · U-1970…U-1981）：主窗口与设置窗口的标题栏统一（真窗口表面；产品 1 文件 + 判据）"
AT_NEW=u"## 第 501 轮（R502 · 2026-10-30 · U-1970…U-1987）：主窗口与设置窗口的标题栏统一（真窗口表面；产品 1 文件 + 判据）"
ANCHOR_NEXT=u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
AS=u"""- **U-1982：⓪ push 与 CI。** 开工 `git push` no-op（HEAD=origin/main=`5d392fb`、**ahead=0**）。成对回读：`41081870670 ↔ 52f4172` **failure 仅 `STEP[9] Release script tests`**（内层 `Ran 683 tests`、`FAILED (failures=4, skipped=2)`）：`test_the_sources_cell_agrees_with_git`（sources 格停旧）、`test_the_lookback_window_is_not_empty`（STATE=R498，而审计节最近标题 `[503, 502, 501, 499]` ⇒ R503 独立开节把 R498 挤出回看窗）、`test_the_roster_matches_what_this_machine_actually_skips`（内层汇总为 FAILED ⇒ 无结论行，前三条的级联）、`test_the_cell_agrees_with_its_own_source`（同一条 stale 的第二侧面）；两条根因已由 `31b21a6`（sources 格改写 + R503 并入 R502 节）修复。`41082826725 ↔ 31b21a6` **failure 仅 `STEP[18] On-screen probe coverage floor`**（`testFrameIntervalsUnderStateChanges` 最差帧 **256.8ms** > 锚点 120ms、超锚点 2 颗 vs 容差 1；`PROBE_NOT_RUN 6/14`；已知在屏采样红）。`41083133180 ↔ 5d392fb` **failure 仅 `STEP[19] Motion coverage floor`**（`MOTION_FLOOR_FACTS judged=5/5 executed=77 not-run=-`、红的用例=`testMarkdownModeLabelChangeIsAVisibleProcess`（1x 只有 1 个过渡帧，要 ≥2）、`MOTION_FLOOR_SUITE_RED=1`；已知采样 flake）。`41077659382 ↔ 2c14a48` **success**。更早：`41077528140 ↔ 58cc884`、`41074949020 ↔ 1633a9d` failure Release（旧产品笔的时序/标签红，已由补记吸收）。436 只复核新跑：`judged=5/5 executed=77`，红的用例见上。
- **U-1983：① 未捕获表面读数。** 两扇窗口的侧栏顶：主侧栏自 R494 有身份头（时钟图标 + 「时间剪史」），设置侧栏只有分类行 —— 720×540 离屏成对帧（负向臂 `settings-general-no-identity` 复现旧布局）侧栏墨带 **负 8 条**、首条即分类行（light 70.5..82.0 / dark 70.0..82.0），窗口顶到首行之间没有任何「我在哪」的锚点。真窗口通道（装新包后 `screencapture -l 623178`，只截设置窗口 720×572）：侧栏墨带 10 条（红绿灯 + 身份头 + 7 分类 + 版本脚），**身份头 90.0..103.5pt、首条导航 121.5..133.0pt**，头在首行之上。
- **U-1984：② 产品：设置侧栏身份头。** `SettingsView.swift` 的 `SettingsSidebarView` 顶部补与主侧栏同一枚身份头：`clock.arrow.circlepath` + 「时间剪史」（`VisualFont.title`、semibold、secondary、`accessibilityHidden`），水平 16 / 上 10 / 下 6；默认 `nil` ⇒ 画（新写法缝 `settingsSidebarIdentityForCapture` 仅供负向帧关掉）。产品 **1 文件**；旧/新：设置侧栏墨带 **8 → 9 条**（light 首带 70.5..82.0 → 71.5..85.5、dark 70.0..82.0 → 72.0..85.5）。
- **U-1985：③ 判据与刀。** 新判据 `testSettingsSidebarCarriesTheAppIdentity`（成对帧 `settings-general` / `settings-general-no-identity`，`sidebarInkBands`）：正臂带数必须 = 负臂 + 1，且首带在次带之上；两档都空 ⇒ `SETTINGS_IDENTITY_HEADER_NOT_RUN=sidebar-blank`。读数 light 正 **9** / 负 **8**、dark **9 / 8**。刀 `M1352`（`if false`：两臂都不画）/`M1353`（`if true`：负向臂照画）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`。两支既有尺的名册按实测登记新负向臂：`CARD_INSET_CONTROL_FIRST`（首墨是复选框，8.0 对文字参照 +2.5/+3.0）、`darkSidebarTextBlindSpots`（同一棵 vibrant 侧栏子树，26/26 一致）。
- **U-1986：④ 帧卷。** 捕获卷 **332 帧**、`CHANGED=62 ADDED=2 MISSING=0`：50 张 `settings-*` + 6 张 `settingssidebar-selection-*` + 4 张 `general-min-orphan-*` + 2 张 `cardprobe-split-groupbox-*`（设置侧栏都在帧里，身份头把整列下移）；新增 `settings-general-no-identity` 两档。基线 **330→332**；更新后 `COMPARED=332 CHANGED=89 MISSING=0 ADDED=0`，余下 89 张在 bbox 尺下 `变了=0`（最大通道差 ≤7/255、16×16 源图标区）为源 App 图标栅格噪声 ⇒ **不吸收**（`FRAME_BASELINE_ENV_NOISE=source-icon-raster`；601）。逐张看过 `settings-general` 亮/暗、负向臂与 `settings-min` 640 最小窗：身份头与分类行同轴（图标 32pt / 字 64pt），无裁切。
- **U-1987：⑤ 八步与电池。** build **0 告警**（`scripts/warning_gate.sh` 增量=0、冷编=0）；预检 `NEEDLE_PRECHECK tables=283 covered=260 arms=695 bad=0`、`ARM_TOTAL files=376 arms=1182`、`HIDDEN_ARMS 表=370 可判=1121 rot=0`；全量 **1318/56/0**（791.4s）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=419=419`（活库）；`STORE-SIZE lines=1108 funcs=52 longest=66`；产品面 streak as-of 503 = **1**（`python3 scripts/product_streak.py --streak-for 503`，last=52f4172/last_round=502）；清账 162/63/0；§1 刷新在生成器后复跑；电池在台账后复跑（683/OK skipped=5）。收口 push `5d392fb..800a45a` success、ahead=0；`800a45a` 自身跑见补记。**具名 NOT-RUN**：① `800a45a` 自身跑（推送后取）；② `SETTINGS_IDENTITY_HEADER` runner 1x（新判据首跑）；③ `RTF_HELPER_ORPHAN`（settings-content-blank/595）；④ `SETTINGS_HELPER_FONT` runner（scale-too-low）；⑤ 已知在屏/Motion 采样 flake（本次红：`testFrameIntervalsUnderStateChanges`、`testMarkdownModeLabelChangeIsAVisibleProcess`）；⑥ 601 的源图标噪声与其余未结项仍开。
"""
DS=u"""## D-500 设置侧栏补身份头：两扇窗口的侧栏顶都要回答「我在哪」（R504）

- 背景：主侧栏自 R494 起有身份头（时钟图标 + 「时间剪史」），设置侧栏只有分类行；720×540 离屏帧与真窗口实拍里，设置侧栏顶都没有任何 App 身份锚点。
- 决定：`SettingsSidebarView` 顶部补与主侧栏同一枚身份头（`clock.arrow.circlepath` + 「时间剪史」、`VisualFont.title` semibold、secondary、水平 16 / 上 10 / 下 6），并留负向缝 `settingsSidebarIdentityForCapture`（默认 nil ⇒ 画）。
- 理由：同一 App 的两扇侧栏要一套身份语言；设置页自己的标题提供页层级，侧栏顶需要稳定的「这是哪个 App 的窗口」锚点。
- 兼容性/迁移：设置侧栏墨带 8→9（light 首带 70.5..82.0 → 71.5..85.5、dark 70.0..82.0 → 72.0..85.5）；62 张旧帧变化 + 2 张新帧、基线 330→332；真窗口 `screencapture -l` 身份头 90.0..103.5pt 在首条导航 121.5..133.0pt 之上。
- 边界：暗档侧栏在离屏通道走 vibrant 合成前极性（D-090），未选中文字结构上看不到；新负向臂已按实测登记进 vibrant 名册，不把它读成产品缺陷。
"""
BS=u"""**607. 设置侧栏身份头在 runner 1x 的读数还没签收**（R504 现读）
    现象：本机 2x 成对帧读出正/负 9 vs 8 带（light 首带 71.5..85.5 / dark 72.0..85.5），但 runner 1x 那一跑还没创建/未读。
    修法：下一跑读 `SETTINGS_IDENTITY_HEADER` 两档 1x；若暗档正臂只多出图标、文字落在盲区，按 D-090 的 vibrant 前提判断，**不许**为了绿放宽 9/8 的带数等式或把负向臂改名。
"""
CS=u"""### 设置侧栏补身份头（62 张旧帧变化 + 2 张新帧、基线 332）（R504 / 第 503 轮 / Round 501 / U-1982…U-1987 · 产品 1 文件 + 判据）

"""
SS=u"""R504 记录（产品 1 文件 + 判据）：设置侧栏补身份头。⓪ push no-op（HEAD=origin/main=`5d392fb`、ahead=0）；成对回读：`41082826725 ↔ 31b21a6` failure 仅 On-screen probe floor（`testFrameIntervalsUnderStateChanges` 256.8ms>120ms，超 2 颗/容差 1）、`41083133180 ↔ 5d392fb` failure 仅 Motion floor（`MOTION_FLOOR_FACTS judged=5/5 executed=77`，红=`testMarkdownModeLabelChangeIsAVisibleProcess` 1<2）、`41081870670 ↔ 52f4172` failure 仅 Release 4 条（sources 格停旧 + R503 独立节把 R498 挤出回看窗 + 两条级联，均已由 31b21a6 修）、`41077659382 ↔ 2c14a48` success。① 设置侧栏只有分类行、主侧栏有身份头；真窗口 `screencapture -l 623178` 只截设置窗口（720×572），身份头 90.0..103.5pt 在首导航 121.5..133.0pt 之上。② 产品：`SettingsSidebarView` 顶部补同一枚身份头（时钟 + 「时间剪史」，默认 nil⇒画，负向缝）；侧栏墨带 8→9（light 首带 70.5..82.0→71.5..85.5、dark 70.0..82.0→72.0..85.5）。③ 新判据 `testSettingsSidebarCarriesTheAppIdentity`；M1352/M1353 **2/2**、RESTORE_CLEAN=yes；CARD_INSET 复选框名册与暗档 vibrant 名册按实测登记新负向臂。④ 捕获 332 帧、62 张旧帧 + 2 张新帧、基线 330→332；89 张源图标噪声不吸收。⑤ 预检 283/260/695 bad=0、ARM 376/1182、HIDDEN 370/1121 rot=0；build 0 告警；全量 **1318/56/0**；换装 ok/419=419（活库）；电池 683/5（台账后复跑）；清账 162/63/0；streak as-of 503 = 1（`python3 scripts/product_streak.py --streak-for 503`，last=52f4172/last_round=502）；产品笔 `800a45a` 已推（ahead=0）。下一轮编号 R505（第 504 轮 / Round 502）：先 push 并复核 ahead=0；读 `800a45a` 自身跑与 `5d392fb`/`31b21a6`/`52f4172` 跑全部失败步骤；重点 `SETTINGS_IDENTITY_HEADER` runner 1x、`RECORDING_REREAD`、`RTF_HELPER_ORPHAN`（仍是 settings-content-blank/595）、436 只复核新跑 Motion floor；② 产品位换未捕获表面；③ 4.5 地板与 150 上限不动。
"""
IS=u"""## Round 501 · R504（第 503 轮 · 2026-10-31）：设置侧栏补身份头（62 旧帧变化 + 2 新帧、基线 332）

主侧栏自 R494 有身份头（时钟图标 + 「时间剪史」），设置侧栏只有分类行 ⇒ 补同一枚身份头（水平 16 / 上 10 / 下 6），负向缝 `settingsSidebarIdentityForCapture`。离屏成对帧正/负 **9 vs 8** 带（light 首带 71.5..85.5 / dark 72.0..85.5）；真窗口 `screencapture -l 623178` 身份头 90.0..103.5pt 在首导航 121.5..133.0pt 之上。62 张旧帧变化 + 2 张新帧，基线 330→332；89 张源图标噪声不吸收。M1352/M1353 2/2。预检 283/260/695、ARM 376/1182、HIDDEN 370/1121 rot=0。全量 1318/56/0；build 0 告警；换装 ok/419=419；电池 683/5。⓪ push no-op（HEAD=origin=5d392fb、ahead=0）；41082826725↔31b21a6 仅 On-screen probe floor、41083133180↔5d392fb 仅 Motion floor、41081870670↔52f4172 Release 4 条（sources/lookback/级联，已由 31b21a6 修）、41077659382↔2c14a48 success。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 62 张旧帧 + 2 张新帧逐张看过（含 640 最小窗与暗档）：身份头与分类行同轴、无裁切；89 张噪声逐张 bbox=0。 |
| 判据有效性 | 15/15 | 正/负 9 vs 8 带两档一致；M1352（永不画）/M1353（负臂照画）2/2。 |
| 假绿防御 | 14/15 | 带数等式 + 首带位置 + 空帧具名 NOT_RUN；扣 1：runner 1x 未读。 |
| 产品面推进 | 15/15 | 新类别（侧栏身份头跨窗口对齐）；1 个产品文件；62 旧帧 + 2 新帧。 |
| 台账一致性 | 15/15 | U-1982…U-1987、D-500、332 帧/1318/56/0、419=419 都来自命令与测试。 |
| 交付诚实性 | 15/15 | 两条 runner 采样红按名字具名；R503 的 4 条 Release 红逐条归成 2 个根因并指到修复笔。 |
| 可复核性 | 15/15 | 9/8、71.5..85.5/70.5..82.0、M1352/M1353、precheck 283/260/695、基线 332 都在。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""
RB=u"""- **R504（设置侧栏身份头；产品 1 文件 + 判据）**：设置侧栏只有分类行、主侧栏有身份头 ⇒ 补同一枚（时钟 + 「时间剪史」）。离屏成对帧正/负 9 vs 8 带（light 71.5..85.5 / dark 72.0..85.5）；真窗口 `screencapture -l` 身份头 90.0..103.5pt 在首导航之上；M1352/M1353 2/2。62 旧帧 + 2 新帧、基线 330→332；全量 1318/56/0；换装 419=419；电池 683/5。
"""
a=rd(A); d=rd(D); b=rd(B); st=rd(S); pr=rd(P); ch=rd(C); it=rd(I)
if a.count(AT_OLD)!=1: raise SystemExit("A title anchor %d" % a.count(AT_OLD))
if a.count(ANCHOR_NEXT)!=1: raise SystemExit("A next anchor %d" % a.count(ANCHOR_NEXT))
if u"## D-500" in d: raise SystemExit("D exists")
if u"**607." in b: raise SystemExit("B exists")
if u"R504 记录" in st: raise SystemExit("S exists")
if u"R504（设置侧栏身份头" in pr: raise SystemExit("P exists")
if u"设置侧栏补身份头" in ch: raise SystemExit("C exists")
if u"## Round 501 · R504" in it: raise SystemExit("I exists")
if pr.count(u"U-31 … U-1981（R503 现读抬到最新一节）")!=1: raise SystemExit("P U cell")
wr(A, a.replace(AT_OLD, AT_NEW, 1).replace(ANCHOR_NEXT, u"\n"+AS+ANCHOR_NEXT, 1))
wr(D, d.rstrip()+"\n\n"+DS+"\n")
wr(B, b.rstrip()+"\n\n"+BS+"\n")
wr(S, st.replace(u"## R498 状态", SS.strip()+"\n\n## R498 状态", 1))
pr=pr.replace(u"U-31 … U-1981（R503 现读抬到最新一节）", u"U-31 … U-1987（R504 现读抬到最新一节）", 1)
wr(P, pr.rstrip()+"\n\n"+RB+"\n")
m=u"## [Unreleased]\n"
if ch.count(m)!=1: raise SystemExit("C anchor")
wr(C, ch.replace(m, m+"\n"+CS, 1))
wr(I, it.rstrip()+"\n\n"+IS+"\n")
print("OK")
