# -*- coding: utf-8 -*-
"""R560 补记：本轮成对号（含收口前到数的 runner 四格）与 R561 的 ⓪ 读单。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BLOCK = u"""
### R560 补记（2026-11-03 · 第 559 轮 / Round 557 · 成对号 + R561 读单）

① **本轮成对号（一次性 push 的自证）**：⓪ 笔 `0a49b5f`（纯台账开工节）、A 笔 `631f910`（产品 1 + 判据 1 + 两张刀表 + 名册）、生成器笔 `700dee9`（`.scratch` 工具，NUM 未填时 `--check` 会拒绝写账）、台账笔 `8004a42`（七本 + 帧基线同一笔 update + 622 第十四值 + 636 新开）、台账补正笔 `22bd17d`（sources 格排在产品笔与台账笔**之后**派生）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间五笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成「没红」。本补记笔自己的跑取号时尚不存在 ⇒ 具名 NOT-RUN，R561 现读。
② **⓪ 那跑到手了**（`41501679574 ↔ 7260562` = **concluded failure**，已等 2593s；`ci_read.py steps` 全量列出只有一朵红）：
- **唯一失败步骤 = STEP[18] `On-screen probe coverage floor`**，正文 `PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14 runner可跑=8 runner不可跑=6 本次下结论=7 闭合通道=接 本次跑过=8 红=1` + `FAILED testFrameIntervalsUnderStateChanges：最差帧 219.7ms 超过锚点 120ms，且超锚点的帧有 2 颗（容差 1 颗）` ⇒ **622 第十四值 = 219.7ms / 2 颗**。归因对照（同一判据）：`41485625452↔8115ab8` 绿、R557 的 `41467585182↔ff15906` 红（225.3ms/3 颗）⇒ **同族既有红、按抽样出现**，R559 没碰那一卷 ⇒ 不署名为 R559 的回归；120ms 锚点、容差 1 颗、`over_runs` 口径一律不动。
- **⓪(a) 预测被 runner 亲手证实**：`HEAT_LEGEND_NOT_RUN=scale-too-low light/dark 倍率=1.0x 格宽=11px 实心判定 格6px/图例3px`，而 `HEAT_LEGEND_COVERAGE` 在这一跑**没有一行** ⇒ 尺走了具名出口、没有报假红（R559 那次降采样探针量的「一个方块 36→9 个采样点」是对的）。⇒ 图例覆盖这件事**今天仍没有 runner 判据**，账上不许写「runner 也验过」。
- **⓪(b) `过渡帧数=` 的第二个 runner 真数 = 5**：`MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=5 相邻差帧数=2 首末连续差=0.0048 峰值=0.0145 声明=200ms 窗口=676ms 每格=26.0ms` ⇒ 这一跑每格 26.0ms（上一跑 71.5ms）⇒ 新口径在 runner 上已有两个数（**2 与 5**），629 那句「余量随钟漂」被两跑实测钉住；STEP[19] `Motion coverage floor` 不在失败名单 ⇒ 旧口径那朵 `testMarkdownModeLabelChang…` 红这一跑也没回来。
- **⓪(c)** STEP[9] `Release script tests` 不在失败名单 ⇒ 634 的修复**连续第二跑**绿。
- **⓪(d)** `TASK_BOX_SIZE`/`TASK_BOX_NOT_RUN` 在这一跑**没有一行** —— 那条判据属于本轮尚未推的代码 ⇒ 具名「判据不在这跑里（未推）」，**不许读成「没红」**；它的第一次 runner 读数留给 R561。
③ **R561 的 ⓪ 必读**（逐条抄全部失败步骤；`steps` 只列 failure/skipped，success 步骤另读 `gh run view --json jobs` 的 `steps[].conclusion`）：
- **本轮 push 的头笔（= 本补记笔）那一跑**，取号时未创建 ⇒ 现在去读。四格各问什么：
  (a) **`TASK_BOX_SIZE` 在 runner 的 1x 上走哪条**（这条判据**没做 1x 体检**，阈值全按 `scale` 派生）：判到 ⇒ 写清宽差/高差是几 px；报 `TASK_BOX_NOT_RUN=runner-detail-frame-plain` ⇒ 那是那条详情帧在 runner 上是平的空帧（R450 同族），**具名入账，不许降墨下界、不许改期望**。
  (b) `HEAT_LEGEND_NOT_RUN=scale-too-low` 是否仍是 runner 的形状（本轮已实测一次；连续两跑同形 ⇒ 这一格可以升成「按几何派生把 1x 也判起来」的工单，而不是继续具名不判）。
  (c) `过渡帧数=` 的**第三个** runner 真数（已有 2、5；余量随钟漂已实测，掉到 1 就按 629 既有口径具名入账，**不许重开排查**）。
  (d) STEP[9] `SKIP_ROSTER` 是否仍 `名单外=无 名册未跳=无`（连续第三跑）；STEP[18] 622 有没有新值（第十四值 219.7ms/2 颗）。
- 仍挂着、永不重开：`41452722560↔58851c2`、`41455782587↔598b253`（cancelled、0 失败步骤、`log not found`）；`b8949f5`/`1ea1bb7` 与本轮中间五笔（同批无独立跑）。
④ **口径不变**：**633 仍等用户人工回执**（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）—— 本轮没拿到，账里没写任何结论；629 写「(B) 已落地 + 635 已结案 + runner 余量随钟漂（两跑实测 2 与 5）」，**不写完全结案**；**636 = 新开**（depth2 项目符 `▪` 落到冬青黑体，R549 禁碰 ⇒ 只开单，头一格先量"有没有夹具画到 depth2"）；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**禁碰清单 11 面**（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径、R559 热图图例、**R560 任务勾选框标记字体**）；刀号 **M1457** 起（M1456 未用，编号跨表唯一由 `ARM_TOTAL` 的 `dupes/repeats` 守）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%` 一律不动；`.contentFade` 0.20 与声明时长一字未改；全量 skipped **57 连三跑稳定**（R558 57、R559 57、R560 57 ⇒ 只记现读，不动门、不修回 55）。
⑤ **本轮现读（收口时）**：build 告警 0；判据 filter 先红（`宽差=5px 高差=4px`，两档 4 条断言）后绿（`宽差=0 高差=0`）；两把刀 **M1454 / M1455 全 CAUGHT、RESTORE_CLEAN=yes**（⚠ M1455 第一版用 Menlo 是**空刀**：差 1px 正落在 ≤1px 容差内 ⇒ PASSED；换 Arial Unicode MS 差 2px 才红 —— 契约是像素同尺寸，不是字体名相同）；判据卷 `UICaptureTests` **219/4 skipped/0 失败（617.5s）**；帧 `FRAME_BASELINE_COMPARED=354 CHANGED=4 MISSING=0 ADDED=0` ⇒ 名单正好是 `detail-tasks` 与 `detail-markdown-rendered` 两个夹具 × 两档外观，`update` 之后复跑 **CHANGED=0**；全量 **1403/57/0（680.8s）**；预检 **tables=355 covered=295 arms=757 bad=0**（两张新表登记进名册；同形 ⇒ 静态抽不出 needle、不在 `covered` 里，会红性只由真跑证明）、`ARM_TOTAL files=448 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=442 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（三读**串行**）；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→68706，备份 `before-R560`）；清账 **162/63/0**；streak 现读 `PRODUCT_STREAK ledger_round=559 streak=1 last=3a3c9a9 last_round=558 newest=631f910 newest_round=559`（⚠ 本轮自伤：写账时按「动了产品 ⇒ 0」**推**了一格，落盘后 `PRODUCT_STREAK_LEDGER_STALE 报告那一格写的是 0，git 派生是 1` 抓住 ⇒ 改成派生值 1；派生格只能**落盘之后现读**，推和抄都不算）；sources 格 `账上=R560/631f910 git=R560/631f910 一致=是`（排在产品笔与台账笔之后派生，单独一笔 `22bd17d`）；电池：台账之后第一遍 `Ran 696 / FAILED (failures=3, skipped=5)` —— **三朵全是时序红**（sources 格未派生 ×2 + `test_skip_roster` 以 634 的 `inner-red` 形状带内层红名），**没有一朵是格式红**（R559 那三条硬格式这次都守住了）；`--write` 之后复跑 **`Ran 696 / OK (skipped=5)`、退出码 0**。

"""


B622 = u"""    复查（R560）：**第十四值到手 = 219.7ms / 2 颗** —— `41501679574 ↔ 7260562`（R559 那一批的头笔）**failure**，`ci_read.py steps` 全量列出只有一朵红：**STEP[18] `On-screen probe coverage floor`**，正文 `PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14 runner可跑=8 runner不可跑=6 本次下结论=7 闭合通道=接 本次跑过=8 红=1` + `FAILED testFrameIntervalsUnderStateChanges：最差帧 219.7ms 超过锚点 120ms，且超锚点的帧有 2 颗（容差 1 颗）`。归因对照（同一判据、同一卷）：`41485625452↔8115ab8`（R558 批）绿、`41467585182↔ff15906`（R557 批）红 225.3ms/3 颗 ⇒ **同族既有红、按抽样出现**，R559/R560 都没碰那一卷 ⇒ 不署名为本轮回归。120ms 锚点、容差 1 颗、`over_runs` 口径一律不动，frame 半继续开单。

"""


def main():
    check = "--check" in sys.argv
    p = os.path.join(ROOT, "AGENT_STATE.md")
    t = io.open(p, encoding="utf-8").read()
    anchor = (u"不许降墨下界、不许改期望。\n"
              u"## R560 ⓪ 开工")
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD state tail hits=%d\n" % t.count(anchor))
        return 1
    bl = os.path.join(ROOT, "AGENT_BACKLOG.md")
    bt = io.open(bl, encoding="utf-8").read()
    line = u"    复查（R559）：本轮**没有**新值"
    hits = [i for i, ln in enumerate(bt.split(u"\n")) if ln.startswith(line)]
    if len(hits) != 1:
        sys.stderr.write("ANCHOR_BAD backlog622 lines=%d\n" % len(hits))
        return 1
    i = bt.index(line)
    j = bt.find(u"\n", i)
    if not check:
        bt = bt[:j + 1] + B622 + bt[j + 1:]
        io.open(bl, "w", encoding="utf-8").write(bt)
    if not check:
        new = (u"不许降墨下界、不许改期望。\n" + BLOCK.strip(u"\n") + u"\n\n## R560 ⓪ 开工")
        t = t.replace(anchor, new, 1)
        io.open(p, "w", encoding="utf-8").write(t)
    sys.stdout.write("ADDENDUM_R560_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
