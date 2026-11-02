# -*- coding: utf-8 -*-
"""R559 补记：本轮成对号（含收口前到数的 runner 读数）与 R560 的 ⓪ 读单。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BLOCK = u"""
### R559 补记（2026-11-03 · 第 558 轮 / Round 556 · 成对号 + R560 读单）

① **本轮成对号（一次性 push 的自证）**：⓪ 笔 `809b963`（纯台账开工节）、A 笔 `3a3c9a9`（产品 1 + 判据 2 + 四张刀表 + 635 两条腿）、A2 笔 `bad7788`（新判据的 1x 体检 ⇒ 具名不判，不改参数）、台账笔 `73e91f4`（七本 + 帧基线同一笔 update）、更正笔 `2f26d4c`（四朵自造红修完：七维表补第七行、CHANGELOG 换成 `### …（R559 / ` 标题形状、streak 两格改成带命令引用的派生值 2）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，中间五笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成「没红」。本补记笔自己的跑取号时尚不存在 ⇒ 具名 NOT-RUN，R560 现读。
② ** 那跑收口前到数了**（这是本轮头一格的落点，不是推断）：`41485625452 ↔ 8115ab8` = **conclusion=success**，`gh run view --json jobs` 逐条读 STEP[1]–[21] **全 success**（`ci_read.py steps` 这一跑只打 `JOB build-and-test ⇒ success`，因为它只列 failure/skipped）。三条正文读数（`ci_read.py readings`，通道串取自判据自己打印的那行）：
- `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=2 相邻差帧数=2 首末连续差=0.0048 峰值=0.0193 声明=200ms 窗口=1860ms 每格=71.5ms` ⇒ **新口径（两端夹逼）在 runner 上判到 ≥2，但余量 0**；而且 `每格=71.5ms` 比 R557 那三跑的 22.6–28.1ms **粗 2.5–3 倍** ⇒ 200ms 的声明时长在那台机器上只摊到 ~3 格，下一跑掉到 1 完全可能。**629 因此不写结案**，写成「新尺已在 runner 判到、余量 0、随钟漂」。
- STEP[9] `Release script tests` = success，正文 `SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=696 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ **634 的借红被 runner 签掉**（内层 696 与本机电池同数）。
- STEP[19] `MOTION_FLOOR_OK=4/5 全部臂都在登记之内`、`MOTION_FLOOR_REDS=0`、`MOTION_FLOOR_FACTS judged=4/5 executed=78 not-run=notice-banner-dismiss` ⇒ R557 那朵 `MOTION_FLOOR_SUITE_RED=1 … testMarkdownModeLabelChang…` 在含新尺的这一跑**不见了**；STEP[18] success ⇒ 622 这一跑无新值（第十三值 225.3ms/3 颗未复现）。
③ **R560 的 ⓪ 必读**（逐条抄全部失败步骤；success 步骤另读 `gh run view --json jobs`）：
- **本轮 push 的头笔（= 本补记笔）那一跑**，取号时未创建 ⇒ 现在去读。三格各问什么：
  (a) 新判据走哪条通道：`HEAT_LEGEND_COVERAGE … 倍率=1.0x` 还是 `HEAT_LEGEND_NOT_RUN=scale-too-low`？**预期后者**（U-2398 的 1x 体检）。若它反而报 `缺=[…]` ⇒ 那是**尺在 1x 没有对象**，不是图例坏了：按 U-2398 写明的几何派生（`((边长−实心边)/2+1)²` 的一半）修尺，**不许降 `minHits`、不许改期望**。
  (b) `MOTION_MARKDOWN_MODE_FADE … 过渡帧数=` 的**第二个 runner 真数**（本轮首数 = 2、余量 0）⇒ 掉到 1 就按 629 的既有口径具名入账（那是余量问题，不是产品回归），别再花一轮去怀疑产品。
  (c) STEP[9] 的 `SKIP_ROSTER` 是否仍 `名单外=无 名册未跳=无`；本轮台账之前那一遍电池里 `test_skip_roster` 以 **`inner-red`** 形状红过（正文带内层汇总 `FAILED (failures=1, 跳过了=6)` 与内层红名 `test_the_cell_agrees_with_its_own_source`）⇒ 那是 634 修好之后的**正确红法**，根因是 sources 格未派生的时序红，`--write` 之后退场。
- 仍挂着、永不重开：`41452722560↔58851c2`、`41455782587↔598b253`（cancelled、0 失败步骤、`log not found`）；`b8949f5`/`1ea1bb7`（R558 同批无独立跑）。
④ **口径不变**：**633 仍等用户人工回执**（访达授权一次 → 换装后再复制一个桌面文件，不该再弹）；629 写「(B) 已落地 + 635 已结案 + runner 余量 0」，**不写完全结案**；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**禁碰清单 10 面**（R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 项目符 ⦁、R550 提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的倍率口径、**R559 热图图例**）；刀号 **M1454** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%` 一律不动；`.contentFade` 0.20 与声明时长一字未改；全量 skipped **57 连两跑稳定**（R558 57、R559 57 ⇒ 只记现读，不据此动任何门、也不修回 55）。
⑤ **本轮现读（收口时）**：build 告警 0；判据 filter 绿（`Executed 2 tests, with 0 failures`）；四把刀 **M1450–M1453 全 CAUGHT、RESTORE_CLEAN=yes**（判据加 1x 门之后 M1450/M1451 复跑仍 CAUGHT）；判据卷 `UICaptureTests` **218/4 skipped/0 失败（670.8s）**；帧 `FRAME_BASELINE_COMPARED=354 CHANGED=10 MISSING=0 ADDED=0` ⇒ 十个名字全是含热图的五个夹具 × 两档外观，`update` 之后复跑 **CHANGED=0**；全量 **1402/57/0（699.0s）**（skipped 57 连两跑稳定 ⇒ 只记现读，不动门、不修回 55）；预检 **tables=353 covered=295 arms=757 bad=0**（四张新表登记进名册；与前几批同形 ⇒ 静态抽不出 needle、不在 `covered` 里，会红性只由真跑证明）、`ARM_TOTAL files=446 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=440 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（三读**串行**）；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→24131，备份 `before-R559`）；清账 **162/63/0**；streak 现读 `PRODUCT_STREAK ledger_round=558 streak=2 last=2ca9501 last_round=556 newest=3a3c9a9 newest_round=558`（⚠ `--streak-for 559` 读 1，是它把本轮 A 笔按 subject 归进 558 轮 ⇒ 口径差一仍挂 BACKLOG 412，账里用门派生的 2）；sources 格 `账上=R559/3a3c9a9 git=R559/3a3c9a9 一致=是`（排在产品笔与台账笔**之后**派生）；**电池四遍**：① 台账前 `Ran 696 / FAILED (failures=2, skipped=5)`（sources 格未派生 + `test_skip_roster` 以 634 的 `inner-red` 形状红，正文带内层汇总与内层红名）→ ② 台账后第一遍**涨到** `FAILED (failures=6, errors=1, skipped=5)`（多出来的四朵全是本轮写账自造的：七维表只写六行、CHANGELOG 写成 bullet、streak 抄了 `--streak-for` 的 1、那一格还没引用取数命令）→ ③ 修完剩三朵 → ④ **`Ran 696 / OK (skipped=5)`、退出码 0**。⚠ 全程没有放宽任何门、没有加豁免、没有改期望；退场条件写进 U-2403（下一轮写账前先核三条硬格式，别等电池抓）。

"""


def main():
    check = "--check" in sys.argv
    p = os.path.join(ROOT, "AGENT_STATE.md")
    t = io.open(p, encoding="utf-8").read()
    anchor = (u"不许拿降采样代理猜参数。\n"
              u"## R559 ⓪ 开工")
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD state tail hits=%d\n" % t.count(anchor))
        return 1
    if not check:
        new = (u"不许拿降采样代理猜参数。\n" + BLOCK.strip(u"\n") + u"\n\n## R559 ⓪ 开工")
        t = t.replace(anchor, new, 1)
        io.open(p, "w", encoding="utf-8").write(t)
    sys.stdout.write("ADDENDUM_R559_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
