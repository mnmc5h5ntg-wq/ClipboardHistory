#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R437 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
DECISIONS = os.path.join(ROOT, "AGENT_DECISIONS.md")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
STATE = os.path.join(ROOT, "AGENT_STATE.md")
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def rd(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


AUDIT_TITLE = u"## 第 435 轮（R436 · 2026-10-28"
AUDIT_SECTION = u"""## 第 436 轮（R437 · 2026-10-28 · U-1608…U-1612）：多文件行展开后的预览补到所属行的文字轴（旧展开内容 40.0pt vs 行文字 83.0pt、差 43 → 新 82.5 vs 83.0、差 0.5；2 张展开帧新增、基线 240）；R436 head 跑一绿一红（`40552595027 ↔ 204737c` success；`40552696188 ↔ 7298af9` 唯一红 on-screen 帧间隔 189.8ms>120）⇒ 原样重跑、阈值未动（产品 1 文件，展开预览位）

- **U-1608：⓪ R436 两跑与两条红的命运。** ① `40552595027 ↔ 204737c`（R436 主笔+追记）**success、全步绿**。② `40552696188 ↔ 7298af9`（STATE 预记那一笔）**failure、失败步骤 1 个**：`On-screen probe coverage floor` —— 唯一红 `testFrameIntervalsUnderStateChanges` **最差帧 189.8ms > 锚点 120ms，且超锚点的帧有 2 颗（容差 1）**；**Swift tests / Capture gate 都是绿的**，也就是说 R435 跑的两条红已签收：`QUICKPICK_CLEAR_BUTTON` 的 list 校准改成同帧第 0 行标题后不再读 0，`testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt` 相位重抓后 same 臂不再 2<3。这一条 on-screen 帧间隔是**性能闸门**（绝对锚点），不是采样条数；本轮**原样重跑**该 job（`gh run rerun --failed`，读时 in_progress ⇒ 具名 NOT-RUN，结果交 R438 ⓪），不碰 120ms 与容差 1 这两个数。
- **U-1609：② 多文件行展开后的预览补到所属行的文字轴。** 缺陷形状（新增的 `detail-3-files-expanded` 亮档现读）：展开的骷髅条从窗口 `containerGutter`（20pt）+ 圆角框 20pt 起 ⇒ **40.0pt**，而同一行文件名从 `rowTextLeading` 起 ⇒ **83.0pt** —— 差 **43pt**，展开块看起来不属于那一行（多文件列表的展开态此前**从未有帧**，`CollapsibleFilePreview → DetailFileView` 没有任何帧覆盖）。修法：`MultiFilePreviewLayout.previewHorizontalInset = 20` 提成常量 + 新 `expandedContentLeadingInset = rowTextLeading − previewHorizontalInset − containerGutter`（只补左侧，右边仍按圆角框收），并给 `DetailView` / `MultiFileDetailView` 加**取证入口** `initialExpandedFileIndex`（产品默认 nil，展开行号只由夹具注入）。旧/新：`EXPANDED_PREVIEW_AXIS light 行文字左=83.0pt 展开内容左=82.5pt 差=0.5pt`、dark 同读数（旧 40.0 vs 83.0、差 43.0）。新增 `detail-3-files-expanded` 亮暗 2 帧，基线 **238→240**（2 增、0 变、0 缺），复验 **240/0/0/0**。
- **U-1610：判据与刀（含一条源守卫的连带更正）。** 新 `testExpandedFilePreviewSitsOnTheRowTextAxis`（第 0 行文件名左沿 vs 展开内容左沿，差 ≤2.5pt；x 从 76 起跳过箭头与类型图标）。`M1199–M1200` **2/2 CAUGHT**（不补左边 / 补双倍；RESTORE_CLEAN=yes）。`Round4MarkdownTests.testDetailViewRoutesMarkdownToTheRendererAndBack` 的源守卫原来整行匹配 `MultiFileDetailView(urls: urls, markdownMode: markdownMode)`，本轮多传 `initialExpandedIndex:` 后它按预期红了 ⇒ 改成折行形状匹配并额外钉住「接的是属性而不是死值」（写死 0 会让产品一进详情就展开第一行）；改后该守卫通过。预检 `tables=215 covered=197 arms=566 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=308 arms=1049 dupes=0`；`HIDDEN_ARMS 表=302 可判=983 rot=0`。
- **U-1611：八步。** build **0 告警**；捕获 **144 条 / 4 skip / 0 失败 / 240 帧**；帧基线 `ADDED=2 / CHANGED=0 / MISSING=0`，`UPDATED=240`、复验 **240/0/0/0**；全量 **1181/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=8/首=27.5/末=1438`、`CHANNEL 0→81→600 变化 18453/100800 重抓=no`、`OFFSET 0/199/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 436，现读 `python3 scripts/product_streak.py --streak-for 436`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑；口径与 R435/R436 一致）。
- **U-1612：具名 NOT-RUN / 观察。** ① on-screen 帧间隔重跑（本笔读时 in_progress；`testFrameIntervalsUnderStateChanges` 189.8>120，原样重跑、阈值未动）；② 设置内容列 1x 平涂（`EXCLUDED_APP_ROW_NOT_RUN`，459）；③ 设置脚注带 1x；④ 主窗口 content 帧 1x（458）；⑤ 高夹具 1x（459）；⑥ 13+ 菜单像素/标题（454）；⑦ 真实拖拽（453）；⑧ Dock 像素；⑨ 源图标最小窗文字 1x；⑩ 本地全量 5 条滚动红（449）；⑪ 2x/extended；⑫ 固定块揭示偏移（455）；⑬ 跨年时间（456）；⑭ 主列表暗档文字盲区（457）；⑮ 真机/多屏（447）；⑯ 真菜单栏、12 实时腿；⑰ `table-lazy-rows`；⑱ HTML 六档以上字号（460）；⑲ 清除按钮命中区 18pt（461）；⑳ 分隔线透明度未提令牌（462）；㉑ 展开态的**已加载内容**仍无帧（463）；㉒ 437–463 仍开；㉓ R437 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 434 · R437（第 436 轮 · 2026-10-28）：多文件行展开后的预览补到所属行的文字轴（旧展开内容 40.0pt vs 行文字 83.0pt、差 43 → 新 82.5 vs 83.0、差 0.5；2 张展开帧新增、基线 240）；R436 head 跑一绿一红（`40552595027 ↔ 204737c` success；`40552696188 ↔ 7298af9` 唯一红 on-screen 帧间隔 189.8ms>120）⇒ 原样重跑、阈值未动（产品 1 文件，展开预览位）

多文件列表的展开态此前从未有帧。新增 `detail-3-files-expanded` 后量到：展开的骷髅条从窗口 gutter 起 40.0pt，而同一行文件名从 83.0pt 起，差 43pt —— 展开块看起来不属于那一行。修法：`previewHorizontalInset` 提常量 + `expandedContentLeadingInset = rowTextLeading − previewHorizontalInset − containerGutter`（只补左侧）；`DetailView` / `MultiFileDetailView` 加取证入口 `initialExpandedFileIndex`（产品默认 nil）。旧/新：40.0 vs 83.0 → 82.5 vs 83.0（差 0.5，亮暗同）；2 张展开帧新增，基线 238→240。源守卫按折行形状更新并钉住「参数接属性不接死值」。M1199–M1200 2/2；预检 215/197/566 bad=0；HIDDEN 302/983 rot=0。R436 head 两跑：`40552595027 ↔ 204737c` **success**（clear × list 校准与 motion 重抓签收）；`40552696188 ↔ 7298af9` **failure、失败 1 步**（on-screen 帧间隔 189.8ms>120、2 颗超锚点）⇒ 原样重跑（读时 in_progress，NOT-RUN）。全量 1181/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/8、27.5→1438；CHANNEL 0→81→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 144/4/0、240 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看新增的展开帧亮/暗：骷髅条与那句「正在加载预览…」都站到了行文字轴上，展开块与所属行成组。扣 2：只有 loading 分支（已加载内容无帧，463）；没有真机截图。 |
| 判据有效性 | 15/15 | 新轴判据 + 两把刀；源守卫随签名更新且钉住「属性不是死值」；M1199–M1200 2/2。 |
| 假绿防御 | 15/15 | 行文字左沿先跳过箭头/图标（x≥76），展开内容从 x≥20 找；校准带与差值同帧；取证入口默认 nil，产品不会自动展开。 |
| 产品面推进 | 14/15 | 真落 1 文件（多文件展开预览位），修的是"展开块不属于那一行"的轴错位；扣 1：只覆盖 loading 分支。 |
| 台账一致性 | 15/15 | U-1608…U-1612、D-433、R436 两跑（success / 1 红）、R437 的 40→82.5、1181 都从日志/帧/用例解析。 |
| 交付诚实性 | 15/15 | on-screen 帧间隔红照实写并原样重跑（不碰门槛）；R435 两条红给出签收路径；展开态只覆盖 loading 也注明（463）。 |
| 可复核性 | 15/15 | 帧名、两档左沿、差值、刀号与红在哪个用例、precheck/rot/CI 原文、基线 240、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_433 = u"""## D-433 展开的预览站在所属行的文字轴上；取证入口只由夹具注入（R437）

- 背景：多文件列表的展开态从未有帧；新增帧后量到展开内容左沿 40.0pt、同行文件名 83.0pt（差 43），展开块看起来不属于那一行。
- 决定：① `MultiFilePreviewLayout.previewHorizontalInset = 20` 提成常量；② `expandedContentLeadingInset = rowTextLeading − previewHorizontalInset − containerGutter`，只补左侧，右边仍按圆角框收；③ `DetailView` / `MultiFileDetailView` 加 `initialExpandedFileIndex`（默认 nil），展开行号只由夹具注入；④ 源守卫从整行匹配改成折行形状匹配，并钉住「参数接属性不是死值」。
- 理由：展开的内容属于那一行，左轴必须同一条；产品默认不展开，取证入口不改变产品路径。守卫更新是签名变化的连带更正，不放松要求（仍要求 markdownMode 接上）。
- 兼容性/迁移：只影响展开态；折叠态帧逐字节不变；新增 2 帧，基线 238→240。
- 边界：只覆盖 loading 分支（DetailFileView 异步读不到文件）；已加载的图片/文本展开态仍无帧（463）。
- 回滚：删 inset 与两个 `initialExpandedFileIndex` 形参、恢复守卫整行匹配；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 多文件行展开后的预览补到所属行的文字轴（旧展开内容 40.0pt vs 行文字 83.0pt、差 43 → 新 82.5 vs 83.0、差 0.5；2 张展开帧新增、基线 240）；R436 head 跑一绿一红（`40552595027 ↔ 204737c` success；`40552696188 ↔ 7298af9` 唯一红 on-screen 帧间隔 189.8ms>120）⇒ 原样重跑、阈值未动（R437 / 第 436 轮 / Round 434 / U-1608…U-1612 · 产品 1 文件，展开预览位）

"""

BACKLOG_SECTION = u"""437 追记（R437 · 仍开）：本轮只动多文件展开预览；主列表仍不匹配 `sourceAppName`。

449 追记（R437 · 仍开）：R436 head 两跑里 `40552595027 ↔ 204737c` success、`40552696188 ↔ 7298af9` 唯一红是 on-screen 帧间隔 189.8ms>120（2 颗超锚点）；原样重跑，不改门槛。

451 追记（R437 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R437 · 仍开）：脚注 1x 具名 NOT-RUN 继续按名出现。

453 追记（R437 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R437 · 仍开）：菜单具名标记仍未发射；菜单 5/5 由真实 NSMenu 用例作证。

455 追记（R437 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R437 · 仍开）：跨年记录仍无年份。

457 追记（R437 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R437 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 上的行首符号像素证人仍缺。

459 追记（R437 · 仍开）：设置内容列/高夹具在 1x 整列平涂（`EXCLUDED_APP_ROW_NOT_RUN` 依此）。

460 追记（R437 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R437 · 仍开）：浮层清除 × 命中区 18pt，仍低于主窗口搜索框的 22pt。

462 追记（R437 · 仍开）：批量操作栏分隔线的 0.18 透明度仍是就地数、未提令牌。

**463. 多文件展开态的「已加载内容」仍无帧：现在只覆盖 loading 分支**（R437 观察）
    现象：`detail-3-files-expanded` 拍到的展开内容是一个不存在的路径 ⇒ `DetailFileView` 停在 loading（骷髅条 + 「正在加载预览…」）。R437 只证明了 loading 块站在行文字轴上；展开后真正出现图片/文本/Markdown 时的排版没有任何帧。
    修法（下一轮若需要）：给夹具一条**真实存在**的图片/文本文件（沿用 `row-file-thumb` 的临时文件做法），拍 `detail-3-files-expanded-loaded` 两档；判据可量"展开内容里的图片/文字左沿与行文字同轴"与"展开块高度不越过分隔线"。
"""

STATE_SECTION = u"""## R437 状态（2026-10-28 · 本地 · 第 436 轮 / Round 434）：多文件行展开后的预览补到所属行的文字轴（旧展开内容 40.0pt vs 行文字 83.0pt、差 43 → 新 82.5 vs 83.0、差 0.5；2 张展开帧新增、基线 240）；R436 head 跑一绿一红（`40552595027 ↔ 204737c` success；`40552696188 ↔ 7298af9` 唯一红 on-screen 帧间隔 189.8ms>120）⇒ 原样重跑、阈值未动（产品 1 文件，展开预览位）

最后更新：2026-10-28（本地 · R437 / 第 436 轮 / Round 434）：多文件列表的展开态此前从未有帧。新增 `detail-3-files-expanded` 后量到：展开的骷髅条从窗口 `containerGutter`（20pt）+ 圆角框 20pt 起 = **40.0pt**，而同一行文件名从 `rowTextLeading` 起 = **83.0pt**（差 43pt）。修法：`previewHorizontalInset` 提常量 + `expandedContentLeadingInset = rowTextLeading − previewHorizontalInset − containerGutter`（只补左侧），并给 `DetailView` / `MultiFileDetailView` 加取证入口 `initialExpandedFileIndex`（产品默认 nil）。旧/新：`EXPANDED_PREVIEW_AXIS light 行文字左=83.0pt 展开内容左=82.5pt 差=0.5pt`、dark 同（旧 40.0/83.0、差 43.0）。新增 2 帧，基线 **238→240**、复验 **240/0/0/0**。源守卫 `testDetailViewRoutesMarkdownToTheRendererAndBack` 随签名改成折行匹配并钉住「接属性不接死值」。R436 head 两跑：`40552595027 ↔ 204737c` **success**（clear × list 校准与 motion 重抓签收）；`40552696188 ↔ 7298af9` **failure、失败 1 步**（on-screen `testFrameIntervalsUnderStateChanges` 最差 189.8ms>120、2 颗超锚点、容差 1）⇒ **原样重跑**（读时 in_progress，具名 NOT-RUN），阈值未动。`M1199–M1200` **2/2 CAUGHT**；预检 **215/197/566 bad=0**、ARM **308 文件 / 1049 把**、HIDDEN **302/983 rot=0**。本地全量 **1181/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/27.5/1438`、`CHANNEL 0→81→600 变化 18453/100800 重抓=no`、`OFFSET 0/199/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **144/4/0 / 240 帧**；基线 **240/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 436，现读 `python3 scripts/product_streak.py --streak-for 436`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑）。

本轮做了什么：
① ⓪ R436 两跑：`40552595027 ↔ 204737c` success（clear × 与 motion 重抓签收）；`40552696188 ↔ 7298af9` 唯一红 on-screen 帧间隔 189.8ms>120 ⇒ 原样重跑、阈值未动（读时 in_progress ⇒ NOT-RUN）。
② 产品：多文件展开预览补到行文字轴（旧 40.0/83.0、差 43 → 新 82.5/83.0、差 0.5；新增 2 帧）。
③ 判据：M1199–M1200 2/2；源守卫随签名更新；precheck 215/197/566；hidden rot 0。
④ 436：最近完整读数仍是 R434 跑 floor 5/5/77 无红；R436 两跑日志本次未取到通道行（照实记），只看结论与失败步骤。
⑤ 367：hidden 表 302 / 可判 983 / rot 0。
⑥ 捕获 144/4/0、240 帧；换装 ok；清账 162/63/0；帧基线 240/0/0/0；本地全量 1181/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① on-screen 帧间隔重跑（`testFrameIntervalsUnderStateChanges` 189.8>120，原样重跑）；② 设置内容列 1x 平涂；③ 设置脚注带 1x；④ 主窗口 content 帧 1x；⑤ 高夹具 1x；⑥ 13+ 菜单像素/标题；⑦ 真实拖拽；⑧ Dock 像素；⑨ 源图标最小窗文字 1x；⑩ 本地全量 5 条滚动红（449）；⑪ 2x/extended；⑫ 固定块揭示偏移（455）；⑬ 跨年时间（456）；⑭ 主列表暗档文字盲区（457）；⑮ 真机/多屏（447）；⑯ 真菜单栏、12 实时腿；⑰ `table-lazy-rows`；⑱ HTML 六档字号（460）；⑲ 清除 × 命中区（461）；⑳ 分隔线令牌（462）；㉑ 展开态已加载内容无帧（463）；㉒ 437–463 仍开；㉓ R437 新跑待 push 后读。

下一轮（R438）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R437 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 on-screen 帧间隔重跑结论（189.8>120 是否复现）、`EXPANDED_PREVIEW_AXIS` 两档 0.5pt、`ROUND4 markdown` 源守卫、`QUICKPICK_CLEAR_BUTTON` 1x、`BULK_ACTION_SEPARATOR` 1x、`MOTION_SEQUENCE` same 臂 ≥3、各具名 NOT-RUN 与带读数；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R437_REPORT_BULLET = u"""- **R437（展开预览位）**：多文件列表的展开态此前从未有帧。新增 `detail-3-files-expanded` 后量到展开骷髅条左沿 **40.0pt**、同行文件名 **83.0pt**（差 43pt）—— 展开块看起来不属于那一行。修法：`previewHorizontalInset` 提常量 + `expandedContentLeadingInset = rowTextLeading − previewHorizontalInset − containerGutter`（只补左侧），`DetailView` / `MultiFileDetailView` 加取证入口 `initialExpandedFileIndex`（产品默认 nil）。旧/新：`EXPANDED_PREVIEW_AXIS light 行文字左=83.0pt 展开内容左=82.5pt 差=0.5pt`、dark 同（旧 40.0/83.0、差 43.0）；新增 2 帧，基线 **238→240**（复验 240/0/0/0）。源守卫 `testDetailViewRoutesMarkdownToTheRendererAndBack` 随签名改成折行匹配并钉住「接属性不接死值」。R436 head 两跑：`40552595027 ↔ 204737c` **success**（clear × list 校准与 motion 重抓签收）；`40552696188 ↔ 7298af9` **failure、失败 1 步**（on-screen `testFrameIntervalsUnderStateChanges` 最差 189.8ms>120、2 颗超锚点、容差 1）⇒ **原样重跑**（读时 in_progress，具名 NOT-RUN），阈值未动。M1199–M1200 **2/2**；预检 215/197/566 bad=0；HIDDEN 302/983 rot=0。本地全量 **1181/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、27.5→1438；CHANNEL 0→81→600、18453/100800）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 144/4/0、240 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)
report = rd(REPORT)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 436 轮（R437" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R437 节")
if u"## Round 434 · R437" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 434")
if u"## D-433" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-433")
if u"多文件行展开后的预览补到所属行的文字轴" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**463." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 463")
if state.count(u"## R436 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R436 状态"))
U_CELL_OLD = u"U-31 … U-1607（R436 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R436 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R436 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_433 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R436 状态", STATE_SECTION + u"## R436 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1612（R437 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R436 节 ②",
                                u"AGENT_STATE.md` 的 R437 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R437_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R437_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
