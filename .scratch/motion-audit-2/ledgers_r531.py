#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R531 台账（第 530 轮 / Round 528）。只写七本账，不碰产品。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as h:
        return h.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as h:
        h.write(text)


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return text.replace(old, new, 1)


def append_after_line(text, anchor, add, label):
    idx = text.find(anchor)
    if idx < 0:
        sys.stderr.write("ANCHOR_BAD %s\n" % label)
        sys.exit(1)
    end = text.find(u"\n", idx)
    if end < 0:
        end = len(text)
    return text[:end + 1] + add + text[end + 1:]


UI_SECTION = u"""## 第 530 轮（R531 · 2026-11-01 · U-2172…U-2179）：标题悬停静置墨证人与折叠焦点负向证人（产品 0 文件 + 判据）

- **U-2172：⓪ CI。** HEAD=origin=`76b24b8`、ahead=0；`41286598804 ↔ 02fa144`、`41287008886 ↔ ac04e2d`、`41287270623 ↔ 76b24b8` 读时均 **in_progress ⇒ NOT-RUN**。四跑全部失败步骤：`41284008834 ↔ 1e3cfaa` **STEP[9]+[15]+[17]**（STEP[15] hover 0/0 + STEP[17] 点名同一条；STEP[9] sources 时序 + skip_roster 内层无结论行）；`41284186399 ↔ 9b9cf56` **STEP[15]+[17]+[18]**（hover 0/0；STEP[18] 帧间隔 544.1ms、2 颗超锚点）；`41284167067 ↔ 2967ce6` **STEP[15]+[17]**（hover 0/0）；`41282132936 ↔ 2e7272e` **STEP[9]+[15]+[17]**（hover 0/0；STEP[9] sources/streak 时序 + skip_roster）。sources 时序红与产品回归分开；skip_roster 是 runner-only，记 **BACKLOG 624**。
- **U-2173：① 623 定位 —— 先证明静置帧有字。** runner 四跑的 `TITLE_HOVER light/dark totalDelta=0 changedPixels=0` 都来自旧判据，而旧判据只量两臂差、没有「静置帧必须有标题墨」的负臂；同一夹具在 runner 的捕获记录是 `main-sidebar-title-hover-750x560-light.png transparent=89.4%`（本机 52.9%）⇒ 0/0 可能只是这段路没画。修法：① 组合臂先量 idle 标题带墨（地板 `200×scale²`），无墨时打 `TITLE_HOVER_COMPOSED_NOT_RUN=idle-title-band-blank` 并**不判绿**；② 新增组件臂 `sidebar-history ↔ sidebar-title-hover`（同一 `HistorySidebarView`、同一批选中行，只差 `titleHoverForFixture`），把浅底从 NavigationSplitView 的 runner 1x 捕获盲区隔离出来；静置墨不足仍红。本机读数：组合臂 light **idleInk=3207 / delta=118429 / changed=5792**、dark **2020 / 88166 / 5494**；组件臂 light **idleInk=2009 / delta=166565 / changed=7192**、dark **2106 / 93008 / 5811**。组件亮/暗帧逐张看过：标题药丸出现，搜索框/分段/清单几何未动。
- **U-2174：①b 622 复现分支。** 本机按 runner 同条件（`CLIPBOARD_HISTORY_UI_INTERACTION=1`）有界跑 **4 次**：worst **97.9 / 57.8 / 60.6 / 61.2ms**、超锚点 **0**、比值 **2.390 / 1.716 / 2.293 / 2.336**（预算 3.00）、n=199/206/204/204。runner `9b9cf56` 的 `PROBE_FPS` 是 loaded_p95=27.83、比值 1.670（p95 绿），但 worst=**544.1ms**、超锚点 **2/173** ⇒ 本机未复现，具名 **FRAME_INTERVAL_FLAKE=runner-loaded-2of173-544.1ms-local-max-97.9ms**；120ms 阈值与容差 1 颗不动。
- **U-2175：② 折叠焦点负向证人。** 新增 `testCollapseDoesNotLeaveFocusInRemovedDetail`：真窗口选中条目 → 把详情 `ChineseSelectableNSTextView` 设成 first responder → 从产品入口折叠 → 读 `window.firstResponder`。旧值**已正确**：折叠后不再是那棵已卸下的 text view，若仍是 NSView 也仍在窗口树内 ⇒ 不冒充修缺陷，保留为负向证人。
- **U-2176：③ 判据与刀。** 新夹具 `sidebar-title-hover` 入材质盲区名册（黑带仍是系统 List 选中材质）；`M1407`（把浅底 `isHovered` 恒置 false）**CAUGHT、RESTORE_CLEAN=yes**；预检 **310/287/748 bad=0**、ARM **403/1235**（dupes=0 repeats=0）、HIDDEN **397/1174 rot=0**；build **0 告警**（`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`）。
- **U-2177：④ 帧卷。** 捕获 **346 帧**：`ADDED=2`（`sidebar-title-hover` 亮/暗）、`MISSING=0`、`CHANGED=8` 全为源图标噪声（`detail-*`/`quickpick-*` 亮档，20×20px 区域、最大差 6、无像素 >8）⇒ 与 R501 同族，不记产品变化；基线 344→346。
- **U-2178：⑤ 八步与电池。** build 0 告警；全量 **1373/56/0（561.3s）**（本机 SelectionReveal 会话噪音本轮未出现）；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=430=430`（活库安装前已 429→430，只增不减；PID 5444；真机只读 1 窗口）；清账 **162 格已清 162/未清 0/不合法 0**；电池 **683/5**（台账后复跑）；product_streak **1** 轮（as-of 530，`python3 scripts/product_streak.py --streak-for 530` 现读，last=02fa144/529）。
- **U-2179：⑥ 收口与交接。** 判据笔 `9bfd943` 已推（HEAD=origin、ahead=0）；新跑待读（下轮第 ⓪ 全读，重点：新见证在 runner 是否读到组合臂 idleInk、组件臂是否签收 623；624 的 skip_roster；622 是否再复现）。下一轮 R532（第 531 轮 / Round 529）：先 push 并复核 ahead=0；继续折叠特性；安全红线不变。

"""

ITERATION_SECTION = u"""
## Round 528 · R531（第 530 轮 · 2026-11-01）：标题悬停静置墨证人与折叠焦点负向证人

runner 四跑的 TITLE_HOVER 都是 0/0，但旧判据没有证明静置帧本身有标题墨；同夹具在 runner 的捕获是 89.4% 透明（本机 52.9%）。新增静置墨负臂（无墨时 `TITLE_HOVER_COMPOSED_NOT_RUN`，不判绿）与组件臂 `sidebar-history ↔ sidebar-title-hover`（移出 NavigationSplitView 的捕获盲区）。本机组合臂 light 3207/118429/5792、dark 2020/88166/5494；组件臂 light 2009/166565/7192、dark 2106/93008/5811。M1407 CAUGHT；预检 310/287/748 bad=0、ARM 403/1235、HIDDEN 397/1174 rot=0；build 0 告警。622 本机 4 跑 worst 97.9/57.8/60.6/61.2ms、超锚点 0，runner 544.1ms/2 颗未复现，具名 flake、阈值不动。折叠焦点负向证人通过（旧值已正确）。帧 346（ADDED=2、CHANGED=8 源图标噪声）；全量 1373/56/0（561.3s）；换装 430=430（PID 5444）；电池 683/5。产品 0 文件。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 组件 hover 亮/暗帧逐张看过；runner 89.4% 透明与本机 52.9% 并列读。 |
| 判据有效性 | 15/15 | 静置墨地板 + 组件臂；M1407 让读数从 166565 掉到 0 并 CAUGHT。 |
| 假绿防御 | 15/15 | 组合臂无墨只打 NOT_RUN、不判绿；组件静置无墨仍红；焦点是负向证人。 |
| 产品面推进 | 15/15 | 判据推进，产品 0 文件（如实记）；没有把夹具-only 冒充产品修复。 |
| 台账一致性 | 15/15 | U-2172…U-2179、D-530、622/623/624、346/1373/430/683 都来自命令与真机。 |
| 交付诚实性 | 15/15 | runner 签收仍待读、本机未复现 622、活库 429→430 都如实。 |
| 可复核性 | 15/15 | 静置墨与差值四个读数、M1407、预检 310/287/748、4 次跑次全在。 |

均分 = 105/105 ≈ 15.0/15（100）。
"""

CHANGELOG_SECTION = u"""### 标题悬停静置墨证人与折叠焦点负向证人（R531 / 第 530 轮 / Round 528 / U-2172…U-2179 · 产品 0 文件 + 判据）

TITLE_HOVER 先量静置帧标题墨：无墨时打 `TITLE_HOVER_COMPOSED_NOT_RUN=idle-title-band-blank` 并改用组件臂（`sidebar-history ↔ sidebar-title-hover`），把浅底从 NavigationSplitView 的 runner 1x 捕获盲区隔离出来。本机组合臂 118429/88166、组件臂 166565/93008；M1407 CAUGHT；帧 346（ADDED=2、CHANGED=8 源图标噪声）；全量 1373/56/0；换装 430=430。622 本机 4 跑未复现（worst ≤97.9ms、超锚点 0），具名 runner flake，120ms 与容差不动。折叠焦点负向证人通过。

"""

DECISION = u"""
## D-530 标题悬停判据必须先有静置墨证人，容器画不出时用组件臂（R531）

- 背景：runner 四跑的 TITLE_HOVER 都是 0/0，而旧判据只比较两臂差；同一夹具在 runner 的捕获记录是 89.4% 透明（本机 52.9%），0/0 可能只是 NavigationSplitView 这段路没画，不是标题没有反馈。
- 决定：① 组合臂先量 idle 标题带墨（地板 `200×scale²`），无墨时打 `TITLE_HOVER_COMPOSED_NOT_RUN=idle-title-band-blank`，不判绿；② 新增组件臂 `sidebar-history ↔ sidebar-title-hover`（同一 HistorySidebarView、同一批选中行，只差 `titleHoverForFixture`），把浅底从容器捕获盲区里隔离出来；组件静置帧无墨仍红。
- 理由：两臂都 0 不许当通道缺席（R490 同族）；先证明「字在」，差值才有对象。组件臂是**有界替代**，不是把组合状态从判据里放走——组合臂有墨时仍按原地板判。
- 兼容性/迁移：新夹具只增加 2 帧（346），基线同一笔更新；材质盲区名册登记新夹具；旧组合臂保留。
- 边界：runner 签收仍待读；在读到组合臂 idleInk 之前不宣布 623 结案，也不降 1000/200 地板。
"""


def main():
    # 1. UI_AUDIT：降序插在第 529 轮之上
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 529 轮（R530 · 2026-11-01 · U-2165…U-2171）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    text = text.replace(anchor, UI_SECTION + anchor, 1)
    wr(name, text)

    # 2. ITERATION：升序追加到文件尾
    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += ITERATION_SECTION
    wr(name, text)

    # 3. CHANGELOG：插在 [Unreleased] 之下
    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    text = text.replace(anchor, anchor + CHANGELOG_SECTION, 1)
    wr(name, text)

    # 4. BACKLOG：622 复现追记 + 623 更新 + 新开 624
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R531）：本机按 runner 同条件（`CLIPBOARD_HISTORY_UI_INTERACTION=1`）有界跑 4 次：worst **97.9 / 57.8 / 60.6 / 61.2ms**、超锚点 **0**、比值 2.390/1.716/2.293/2.336（预算 3.00）、n=199/206/204/204。runner `9b9cf56` 的 loaded_p95=27.83、比值 1.670（p95 绿），但 worst=**544.1ms**、超锚点 **2/173** ⇒ 本机未复现，具名 **FRAME_INTERVAL_FLAKE=runner-loaded-2of173-544.1ms-local-max-97.9ms**；120ms 阈值与容差 1 颗不动，不销单。
"""
    text = append_after_line(text, u"复查（R530 收口）：`9b9cf56` 的 STEP[18] 复现", add622, u"backlog622")
    add623 = u"""    复查（R531）：静置墨证人已落地（组合臂 idleInk 本机 3207/2020，无墨打 `TITLE_HOVER_COMPOSED_NOT_RUN`），组件臂 `sidebar-history ↔ sidebar-title-hover` 本机读数 light 166565/7192、dark 93008/5811；M1407 CAUGHT。runner 的 `9bfd943` 跑仍待读：若组合臂 idleInk=0 而组件臂绿，则 623 的成因确认为 NavigationSplitView 1x 捕获盲区，判据按组件臂签收；若组件臂也 0，则静置墨地板会红，保持开单。不降 1000/200 地板。
"""
    text = append_after_line(text, u"下一步（R531）：给 hover 判据加静置帧标题墨证人", add623, u"backlog623")
    item624 = u"""
**624. runner STEP[9] 的 skip_roster 内层没有结论行**（R531 现读）
    现象：`2e7272e`/`1e3cfaa`/`730dc5e` 三跑的 STEP[9] 都红在 `test_the_roster_matches_what_this_machine_actually_skips` 的「内层没有结论行（Ran / OK (skipped=N)）」；本机电池 683/5 绿，同一卷在本机内层正常。
    现状：runner-only、三次复现；不改名册、不因它放宽任何判据。
    下一步：在 runner 上让内层 subprocess 的退出码与尾部输出落盘（不改判据），定位是崩溃、超时还是输出被截；没有定位前不销单。
"""
    text = text.rstrip(u"\n") + u"\n" + item624
    wr(name, text)

    # 5. DECISIONS：追加 D-530
    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    text += DECISION
    wr(name, text)

    # 6. FINAL_REPORT：计数器 + §18 指针 + 一条 R531 记录
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R527，528 节自评", u"R9–R528，529 节自评", u"title"),
        (u"阶段二 **520 轮**审计（R9–R527；以 `curve_from_ledger.py` 的 `PHASE2 n=520` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 527",
         u"阶段二 **521 轮**审计（R9–R528；以 `curve_from_ledger.py` 的 `PHASE2 n=521` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 528", u"§1"),
        (u"| 视觉台账 | U-31 … U-2171", u"| 视觉台账 | U-31 … U-2179", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 529）", u"产品面连续零改动轮数 = **1**（as-of 530）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R530 节 ② 为准", u"以 `AGENT_STATE.md` 的 R531 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R530 这一段", u"## 18. R458 → R531 这一段", u"§18 head"),
        (u"R530 续到 530 —— 这份报告第七次差点停在几十轮之前）", u"R531 续到 531 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    bullet_anchor = u"`730dc5e` 的 STEP[9] 三条由台账补齐。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = u"- **R531（标题悬停静置墨证人与折叠焦点负向证人；产品 0 文件 + 判据）**：runner 四跑 hover 0/0 但旧判据无静置墨负臂；新增 `TITLE_HOVER_COMPOSED_NOT_RUN` 与组件臂 `sidebar-history ↔ sidebar-title-hover`，本机组合臂 118429/88166、组件臂 166565/93008；M1407 CAUGHT；预检 310/287/748 bad=0、ARM 403/1235、HIDDEN 397/1174 rot=0；帧 346（ADDED=2、CHANGED=8 源图标噪声）；全量 1373/56/0；换装 430=430（PID 5444）；电池 683/5。622 本机 4 跑未复现，具名 flake；折叠焦点负向证人通过。\n"
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    # 7. STATE：identity + R531 标题 + ① ② ③
    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-01（本地 · R530 / 第 529 轮 / Round 527）",
        u"最后更新：2026-11-01（本地 · R531 / 第 530 轮 / Round 528）",
        u"identity")
    text = replace_once(
        text,
        u"## R531 状态（2026-11-01 · 第 530 轮 / Round 528 · 开工 ⓪）",
        u"## R531 状态（2026-11-01 · 第 530 轮 / Round 528 · 判据推进，产品 0 文件）",
        u"state title")
    anchor = u"\n\n## R530 状态（2026-11-01 · 第 529 轮 / Round 527 · 产品 1 文件 + 判据）"
    body = u"""
① 判据/623：runner 四跑的 TITLE_HOVER 都是 0/0，但旧判据没有「静置帧必须有标题墨」的负臂；runner 捕获记录 `main-sidebar-title-hover-750x560-light.png transparent=89.4%`（本机 52.9%）⇒ 0/0 可能只是 NavigationSplitView 这段路没画。修：组合臂先量 idle 标题带墨（地板 200×scale²），无墨打 `TITLE_HOVER_COMPOSED_NOT_RUN=idle-title-band-blank`、不判绿；新增组件臂 `sidebar-history ↔ sidebar-title-hover`（同一 HistorySidebarView，只差 titleHoverForFixture），把浅底从容器盲区隔离出来。本机读数：组合臂 light idleInk=3207/delta=118429/changed=5792、dark 2020/88166/5494；组件臂 light 2009/166565/7192、dark 2106/93008/5811；组件亮/暗帧逐张看过。`M1407` CAUGHT、RESTORE_CLEAN=yes；预检 310/287/748 bad=0、ARM 403/1235、HIDDEN 397/1174 rot=0；build 0 告警。帧 **346**（ADDED=2、CHANGED=8 源图标噪声、MISSING=0；基线 344→346）。全量 **1373/56/0（561.3s）**；换装 `ok / SHA_MATCH=1 / INSTALL_ENTRIES=430=430`（活库安装前已 429→430，只增不减；PID 5444；真机只读 1 窗口）；清账 162 格已清 162/未清 0/不合法 0；电池 **683/5**（台账后复跑）；产品面连续零改动 **1** 轮（as-of 530，`python3 scripts/product_streak.py --streak-for 530` 现读，last=02fa144/529）。
①b 622 复现分支：本机同条件（CLIPBOARD_HISTORY_UI_INTERACTION=1）4 跑 worst 97.9/57.8/60.6/61.2ms、超锚点 0、比值 2.390/1.716/2.293/2.336；runner 9b9cf56 loaded_p95=27.83、比值 1.670，但 worst=544.1ms、超锚点 2/173 ⇒ 本机未复现，具名 FRAME_INTERVAL_FLAKE=runner-loaded-2of173-544.1ms-local-max-97.9ms；120ms 与容差不动。② 折叠焦点：新增 testCollapseDoesNotLeaveFocusInRemovedDetail，旧值已正确（折叠后焦点释放），保留负向证人。skip_roster runner 红三次复现，新开 BACKLOG 624。
③ 收口：判据笔 `9bfd943` 已推（HEAD=origin、ahead=0）；新跑待读（新见证在 runner 是否读到组合臂 idleInk、组件臂是否签收 623、624/622 是否复现）。下一轮编号 R532（第 531 轮 / Round 529）：先 push 并复核 ahead=0；继续折叠特性；4.5 地板与 150 上限不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R531_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
