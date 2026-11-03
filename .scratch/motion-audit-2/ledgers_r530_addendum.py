#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R530 收口后 CI 复读补记：只补台账，不碰产品。"""
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


def main():
    # 1. UI_AUDIT：把复读结论挂在 U-2171 尾部（不新增 U 号，保持 U-2165…U-2171 与产品笔一致）
    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    old = u"下一轮 R531（第 530 轮 / Round 528）：先 push 并复核 ahead=0；继续折叠特性；安全红线不变。\n"
    new = old.rstrip(u"\n") + u" 收口后复读四跑：`1e3cfaa`/`730dc5e`/`9b9cf56`/`2967ce6` 的 STEP[15] 唯一失败仍是 `testSidebarTitleHoverFeedbackIsVisible` 亮/暗 **0/0**（新尺也读到 0）⇒ R528/R529 两次修法都未在 runner 签收，新开 **BACKLOG 623**；`9b9cf56` 的 STEP[18] 帧间隔 **544.1ms**（2 颗超 120ms 锚点、容差 1）⇒ **BACKLOG 622** 进入复现分支；`730dc5e` 的 STEP[9] 五红里三条由本笔台账补齐（指针 R529→R530、STATE streak 格、ITERATION Round 527 让 citations 正对照有对象），skip_roster 结论行缺失记 runner 环境红；`02fa144`/`ac04e2d` 读时 in_progress/queued ⇒ NOT-RUN。\n"
    text = replace_once(text, old, new, u"ui2171")
    wr(name, text)

    # 2. STATE：R530 节加 ③
    name = "AGENT_STATE.md"
    text = rd(name)
    old = u"下一轮编号 R531（第 530 轮 / Round 528）：先 push 并复核 ahead=0；继续折叠特性；4.5 地板与 150 上限不动。\n"
    new = old.rstrip(u"\n") + u"\n③ 收口后 CI 复读：`1e3cfaa`/`730dc5e`/`9b9cf56`/`2967ce6` 四跑 STEP[15] 仍只有 `testSidebarTitleHoverFeedbackIsVisible` 亮/暗 **0/0**（新尺也 0）⇒ R528/R529 两次修法未签收，新开 **BACKLOG 623**；`9b9cf56` STEP[18] 帧间隔 **544.1ms**（2 颗超锚点）⇒ 622 进入复现定位分支；`730dc5e` STEP[9] 五红里三条由本笔台账补齐（FINAL_REPORT 指针、STATE streak 格、ITERATION Round 527），skip_roster 结论行缺失记 runner 环境红；`02fa144`/`ac04e2d` 读时 in_progress/queued ⇒ NOT-RUN。\n"
    text = replace_once(text, old, new, u"state3")
    wr(name, text)

    # 3. BACKLOG：622 复现追记 + 新开 623
    name = "AGENT_BACKLOG.md"
    text = rd(name)
    add622 = u"""    复查（R530 收口）：`9b9cf56` 的 STEP[18] 复现 `testFrameIntervalsUnderStateChanges`：最差 **544.1ms**、2 颗超 120ms 锚点（容差 1）；同一跑 hover 仍 0.0。按本条退场条件进入「复现 ⇒ 开单定位」分支：R531 先定位帧间隔（录制/探针负载）与 hover 的 runner 1x 捕获问题（见 623）；code-block 在 `1e3cfaa`/`730dc5e`/`9b9cf56` 三跑均 passed ⇒ code-block 半仍不销。
"""
    text = append_after_line(text, u"复查（R530）：`2e7272e`/`5fcb482` 两跑的 capture 与 Swift 步里", add622, u"backlog622")
    item623 = u"""
**623. runner 1x 上标题悬停判据仍读 0/0：两次修法都未签收**（R530 收口现读）
    现象：`1e3cfaa`（扩边顺序 + 显式取证值）、`730dc5e`、`9b9cf56`、`2967ce6` 四跑的 STEP[15] 都只有 `testSidebarTitleHoverFeedbackIsVisible` 一项红：`TITLE_HOVER light/dark totalDelta=0 changedPixels=0 region=300x260px`；Capture gate 点名同一条。本机 2x 读数是 118429/5792、88166/5494，说明 hover 在本地能落墨。
    已排除：具名专用取证键已从 ContentView 显式传到 HistorySidebarView；浅底已改显式 labelColor；扩边顺序已改为正 padding→background→外壳负 padding（M1404 在本地 CAUGHT）。
    待判假设：runner 1x 的 `NavigationSplitView` sidebar 在离屏 cacheDisplay 下可能根本不画标题（D 类捕获限制），于是两帧都无标题墨、差恒 0；现有判据只量两帧差，没有「静置帧必须有标题墨」的负臂，分不出「没有 hover 填色」和「整块没画」。
    下一步（R531）：给 hover 判据加静置帧标题墨证人（band ink > floor）；若 runner 静置帧无墨，把夹具从 ContentView 改成独立 `HistorySidebarView`（与 `sidebar-*` 同族）再复跑 runner。不许降地板。
"""
    text = text.rstrip(u"\n") + u"\n" + item623
    wr(name, text)

    # 4. FINAL_REPORT：§18 R530 那一条补复读读数（计数器不变）
    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    old = u"电池 683/5。\n"
    # 只改 §18 里 R530 那一条的结尾，用更长的锚避免撞到别的行
    anchor = u"新增选区跨折叠保持判据与 360×560 `main-collapsed-min`；M1406/M1405 CAUGHT；预检 309/286/747 bad=0、ARM 402/1234、HIDDEN 396/1173 rot=0；帧 344（ADDED=2）；全量 1372/56/0；换装 429=429（PID 80101）；电池 683/5。"
    new = anchor + u" 收口后四跑仍 hover 0.0（新开 BACKLOG 623）、`9b9cf56` 帧间隔 544.1ms（622 复现分支）、`730dc5e` 的 STEP[9] 三条由台账补齐。"
    text = replace_once(text, anchor, new, u"final18")
    wr(name, text)

    sys.stdout.write("LEDGERS_R530_ADDENDUM_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
