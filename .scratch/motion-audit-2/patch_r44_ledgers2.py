#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R44 台账的第二段。

第一段（patch_r44_ledgers.py）在 AGENT_BACKLOG.md 的锚点上 assert 失败退出了 ——
它按记忆写的锚文本和账上原文不一致（真实原文在 :1314）。
**已经写进去的两段**（AGENT_UI_AUDIT.md 的第 46 轮、AGENT_DECISIONS.md 的 D-103）
在这个脚本里**不再重写**：追加不是幂等操作，重复跑一遍就是两份 D-103。
剩下的三段：BACKLOG 64（改锚点）、CHANGELOG、VISUAL_ITERATION、STATE。
"""
import io
import os

os.chdir("/Users/wangziyi/Codex_Project0")


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


BACKLOG_NEW = (
    "    好消息是这五条**确实有电**（R22 用像素量过插入位移），所以这不是漏网的缺陷，只是尺的表达能力。\n"
    "    **R44 做掉了一半**：派生键展开已进判据（`drivingStates`，只增不减、读不懂不放行也不报错），\n"
    "    `NoticeBanner` 那五个调用点已进名单 —— 读数"
    "`BANNER_DRIVE 调用点 5 个、键 1 条、展开后状态 13 个、无驱动 0 个`。\n"
    "    **剩下一半**：热图那两处（`DailyCopyHeatmapView:44/50/78`）不是\"组件调用点 + `if let` 门控\"，\n"
    "    而是 `if 布尔 { 一块视图 } else { 另一块 }` 的**分支**形状 ⇒ 扫描器要先会认分支；"
    "`EmptyStateView` 同理还没进名单。\n"
    "    所以这条**仍然开着**，别因为\"NoticeBanner 做完了\"就划掉。"
)
patch("AGENT_BACKLOG.md", [(
    "    好消息是这五条**确实有电**（R22 用像素量过插入位移），所以这不是漏网的缺陷，只是尺的表达能力。",
    BACKLOG_NEW,
)])

CHANGELOG = '''### Added（R44 · 判据会读"派生键"了 —— 调用点级的动效守卫推广到 NoticeBanner）

- 本轮**零产品改动**，改的是尺。R42 那条"调用点级"守卫要推广到 `NoticeBanner` 时被发现读不懂一种合法写法：
  `ContentView:32` 的驱动键是 `noticeSignature`，而它（`:36-44`）把五条回执的存在性压成一个 bitmask
  ⇒ 按名字匹配会把**五条全误报成没电**，而那五条确实有电（R22 量过像素）。
- 新增 `drivingStates(for:in:)`：键里的裸名字若在本文件有 computed property 定义，
  就把 body 点到的标识符并进状态集合（点路径与最后一段都算）。**只展开一跳、只增不减**：
  读不懂 ⇒ 退回按名字匹配，既不放行也不报错 ——
  "读不懂就红"会逼人删守卫（R34 / R21b 那一族），"读不懂就放行"是免检牌（R39b 那一族）。
- 剩下的假阴性风险由变异钉住：**M207** 从签名 body 里删掉一条 ⇒ 只有那一条红。
- 判据 +2 条（`testNoticeBannerCallSitesArePoweredByTheirDerivedKey` + 派生键展开的 5 格真值表）
  与 4 个纯函数；变异 M206–M209 四支全 CAUGHT（needle 全实测抄来，且落在排过序的数组上 ⇒ 顺序稳定）。
- **BACKLOG 64 只做了一半**：热图那两处是 `if 布尔 { … } else { … }` 的**分支**形状，
  现在的扫描器只认"组件调用点 + `if let`" ⇒ 这条继续开着，别当成推广完了。
- 本轮**不换装**（没有任何"只有装上新包才看得见"的东西）；112 张帧逐字节不变。
- 验证：735 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门 `红=0 NOT_RUN=0`、脚本 83 全绿。

'''
patch("CHANGELOG.md", [("## [Unreleased]\n", "## [Unreleased]\n\n" + CHANGELOG)])

print("R44 台账第二段（BACKLOG 64 / CHANGELOG）已写入")
