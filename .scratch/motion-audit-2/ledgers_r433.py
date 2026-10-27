#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R433 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 431 轮（R432 · 2026-10-27"
AUDIT_SECTION = u"""## 第 432 轮（R433 · 2026-10-27 · U-1588…U-1592）：详情大图补 1pt 中性边（白底图在白底详情里旧差 0.0 → 新 32.0/28.0；贴合尺寸只缩不放，240×140 不变；2 张详情帧变化、基线 238）；R432 跑失败步骤 2 个（高夹具 720×1040 在 1x 整帧不画）⇒ 换 540 帧保住 CI 像素证人（产品 1 文件，详情图片预览位）

- **U-1588：⓪ R432 跑的失败步骤与排除名单/仪器命运。** `40519498631 ↔ f39f66c` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。唯一红是 `testExcludedAppsStartWithAnIconInsteadOfRawIDs` 两档都读到 `EXCLUDED_APP_ROW light/dark 行数=0 判=0`（判 ≥6）—— 高夹具 **`settings-privacy-tall`（720×1040）在 runner 1x 上整帧不画**，与 1100pt/900pt 那族同一条通道限制；不是名单行的产品问题。R432 的另一条新仪器**按名生效**：`FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`（light/dark，四格 0）出现且不计红，`testFileRowsShowTheirTypeSymbol` passed；理由固定带收窄到 290 后 `QUICKPICK_MATCH_REASON_BAND light typed 扩展=217 list 扩展=0`、dark 同（不再蹭 1x 时间列 296）。其余全绿：时间列 1x light `[74.0,71.0,74.0,74.0,74.0]` 起 296–298 止 369–370、dark `[74.0,72.0,74.0,74.0,74.0]` 止 370；`SETTINGS_FOOTER_BAND_NOT_RUN` 两档按名出现（light 720 7/6、640 6/6；dark 1/1）；分区 `13/12`（light）与 `11/10`（dark）；`PINNED_SECTION_ROWS 6/5 选中 [2]/[1]`；菜单 **5/5 passed**；floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`、无红、无 unlisted；回执 **2/2**（2x 0.1278/1382ms、1x 0.1333/1252ms，均 `重抓=no`）；滚动 **4/4 passed**（`CHANNEL 0→125→600 变化 30000/17000`）；拖拽源 mass 0.549/0.550；Dock 标记已登记。
- **U-1589：⓪ 的修法：把排除名单的像素证人从「1x 画不出的高夹具」搬到 540 高的同一页。** `settings-privacy-tall` 在 1x 是空白帧（行数 0），而 `settings-privacy`（720×540）在 1x 能画（caption 探针一直在读它）。于是 `testExcludedAppsStartWithAnIconInsteadOfRawIDs` 改用 `settings-privacy`，扫描带 `y=394…528`、要求 ≥3 行；本机 2x 现读 `EXCLUDED_APP_ROW light 行数=5 判=5 首段宽=[10.0,10.0,10.0,10.0,14.0] 行墨=[2704,2421,2429,2641,2417]`、dark `[10.0,10.0,10.0,10.0,10.5]` / `[3055,2748,2757,3035,2125]` —— 旧形状首段 42.5pt 的判别力不变，覆盖从"九行"收成"首屏五行"，换来 CI 上真有像素证人。阈值（5…30pt、行墨>20）一字未动。
- **U-1590：② 详情大图补 1pt 中性边。** 缺陷形状（`detail-1-image` 亮/暗直看 + 现读）：大图周围直接是页面底色 —— 图沿外 1–3pt 的带与 20pt 外的页面底色亮度差 **0.0/0.0**，白底截图在白底详情里整张看不出边界。修法：新 `ImagePreviewLayout.fittedSize`（**只缩不放**，与旧 `scaledToFit` 的行为一致）+ 图外 `1pt` 的 `Color.primary.opacity(VisualTint.chipStroke)` 中性边（挂在贴合图本身的尺寸上，不是挂在上限框上）。修后同一把尺：`DETAIL_IMAGE_EDGE light 图框=480..959×440..719px 页底=255.0 边带最大差=32.0`、dark `页底=30.0 边带最大差=28.0`（旧 0.0/0.0）；图框与旧帧一致（240×140pt，**没有被放大**——第一版漏了 `min(1, …)`，帧上量到 680×397，已当场收回）。2 张 `detail-1-image` 帧变化，基线仍 **238/0/0/0**。
- **U-1591：判据与刀。** 新 `ImagePreviewLayoutTests` 四条（小图不放大 / 只缩时保宽高比 / 高度上限 / 退化输入） + `testDetailImagePreviewHasAVisibleEdge`（按 systemTeal 找图、量图沿外 1–3pt 与页底色的亮度差 >10；扫描从 y=150px 起排除状态条小图标）。`M1189–M1191` **3/3 CAUGHT**（边撤掉 / 边透明 / 又开始放大；RESTORE_CLEAN=yes）。预检 `tables=211 covered=193 arms=558 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=304 arms=1041 dupes=0`；`HIDDEN_ARMS 表=298 可判=975 rot=0`。
- **U-1592：八步。** build **0 告警**；捕获 **140 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `CHANGED=2 / MISSING=0 / ADDED=0`（`detail-1-image` 亮暗），`UPDATED=238`、复验 **238/0/0/0**；全量 **1172/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=8/首=31.5/末=1438`、`CHANNEL 0→96→600 变化 153619/172800 重抓=no`、`OFFSET 0/192.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 432，现读 `python3 scripts/product_streak.py --streak-for 432`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 设置脚注带 1x（`SETTINGS_FOOTER_BAND_NOT_RUN`）；② 主窗口 content 帧 1x 整帧不画（`FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`，458）；③ 高夹具 720×1040 在 1x 整帧不画（459）；④ 13+ 菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；⑤ 真实拖拽（453）；⑥ Dock 像素（`DOCK_BADGE_PIXEL_NOT_RUN`）；⑦ 源图标最小窗文字 1x（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN`）；⑧ 本地全量 5 条滚动红（449）；⑨ 2x/extended 臂；⑩ 固定块揭示偏移（455）；⑪ 跨年时间（456）；⑫ 主列表暗档文字离屏盲区（457）；⑬ 真机/多屏（447）；⑭ 真菜单栏、12 实时腿；⑮ `table-lazy-rows`；⑯ 437–459 仍开；⑰ R433 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 430 · R433（第 432 轮 · 2026-10-27）：详情大图补 1pt 中性边（白底图在白底详情里旧差 0.0 → 新 32.0/28.0；贴合尺寸只缩不放，240×140 不变；2 张详情帧变化、基线 238）；R432 跑失败步骤 2 个（高夹具 720×1040 在 1x 整帧不画）⇒ 换 540 帧保住 CI 像素证人（产品 1 文件，详情图片预览位）

详情大图以前没有任何边/阴影：图沿外 1–3pt 与 20pt 外的页面底色亮度差 0.0（亮/暗），白底截图在白底详情里整张看不出边界。修法：新 `ImagePreviewLayout.fittedSize`（只缩不放，与旧 `scaledToFit` 一致）+ 图外 1pt `Color.primary.opacity(VisualTint.chipStroke)` 中性边，挂在贴合图本身的尺寸上而不是上限框上。旧/新同尺：边带最大差 **0.0/0.0 → 32.0/28.0**；图框 480..959×440..719px（240×140pt）不变。第一版漏了 `min(1, …)`，帧上量到 240×140 被拉到 680×397，已当场收回（单测 `testFittedSizeNeverUpscalesASmallImage` 钉住）。2 张 `detail-1-image` 帧变化，基线 238/0/0/0。R432 run `40519498631 ↔ f39f66c` **failure、失败步骤 2 个**（Swift tests / Capture gate）：唯一红是 `settings-privacy-tall`（720×1040）在 1x 整帧不画（行数 0）⇒ 改用能画的 `settings-privacy` 540 帧、要求 ≥3 行（本机 5 行、首段 10–14pt），阈值未动；`FILE_ROW_SYMBOL_NOT_RUN` 按名生效不计红；理由带 290 后 typed 217 / list 0。时间列/脚注/分区/表格/菜单/floor/回执/滚动全绿。M1189–M1191 3/3；预检 211/193/558 bad=0；HIDDEN 298/975 rot=0。全量 1172/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/8、31.5→1438；CHANNEL 0→96→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 140/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看 `detail-1-image` 亮/暗两档：图外多了一圈中性边，白色块的边界可读；同时确认 240×140 没被放大（第一版放大到 680×397 已收回）。扣 2：没有真机截图；边只有 1pt，缩略图上更弱。 |
| 判据有效性 | 15/15 | 四条贴合尺寸单测（含"不放大"这条自伤守卫）+ 一条按 systemTeal 找图的边带判据；M1189–M1191 3/3。 |
| 假绿防御 | 15/15 | 判据先按色度找图（不靠固定坐标），扫描排除状态条小图标；页底亮度和边带差都打印；"不放大"由单测钉住，像素判据冒充不了。 |
| 产品面推进 | 14/15 | 真落 1 文件（详情图片预览位），修的是"白底图完全看不见边界"的缺陷；扣 1：只有 1pt 边，没做阴影/圆角，视觉增量克制。 |
| 台账一致性 | 15/15 | U-1588…U-1592、D-429、R432 的 0 行、R433 的 32.0/28.0、1172 都从日志/帧/用例解析。 |
| 交付诚实性 | 15/15 | R432 的红写成"高夹具 1x 不画"并换替身帧；放大自伤当场收回并写进单测；文件/内容/脚注/菜单各有具名出口。 |
| 可复核性 | 15/15 | 帧名、图框像素坐标、页底/边带读数、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_429 = u"""## D-429 详情大图补 1pt 中性边；贴合尺寸只缩不放（R433）

- 背景：`ImagePreviewView` 直接画图，没有任何边/阴影；白底截图（或白底海报）在白底详情里与页面同色，图沿外 1–3pt 与页底色差 0.0/0.0，边界不可读。
- 决定：① 新 `ImagePreviewLayout.fittedSize(image:available:)`：`scale = min(1, min(w/iw, h/ih))` —— 与旧 `scaledToFit` 一致，**只缩不放**；② 图外 `1pt` 的 `Color.primary.opacity(VisualTint.chipStroke)` 中性边，挂在贴合尺寸上（不是 `maxWidth/maxHeight` 那块上限框——那会画成一个空框）；③ 判据按 systemTeal 找图、量图沿外 1–3pt 与页底色的亮度差 >10。
- 理由：图片预览的"边界"是内容的一部分（白底图没有边界等于没有预览）；边必须贴在图本身，否则框比图大一圈反而误导。1pt 中性边在亮/暗两档都能读（32.0/28.0），且不改变图的内容表现。
- 兼容性/迁移：图尺寸与位置未变（240×140 仍在 480..959×440..719px），只有 2 张 `detail-1-image` 帧变化；`ImagePreviewLayout` 抽成纯函数后可单测"不放大"。
- 边界：只有 1pt 边，没有阴影/圆角；深色图在白底上的边界靠边而不是阴影；真机未截图。
- 回滚：删 `frame/padding/background` 三行与 `ImagePreviewLayout`，恢复 `scaledToFit`；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 详情大图补 1pt 中性边（白底图在白底详情里旧差 0.0 → 新 32.0/28.0；贴合尺寸只缩不放，240×140 不变；2 张详情帧变化、基线 238）；R432 跑失败步骤 2 个（高夹具 720×1040 在 1x 整帧不画）⇒ 换 540 帧保住 CI 像素证人（R433 / 第 432 轮 / Round 430 / U-1588…U-1592 · 产品 1 文件，详情图片预览位）

"""

BACKLOG_SECTION = u"""437 追记（R433 · 仍开）：本轮只动详情图片预览的边；主列表仍不匹配 `sourceAppName`。

449 追记（R433 · 仍开）：R432 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→125→600、TIME 7/2/582/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/8、31.5→1438）⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R433 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R433 · 仍开）：脚注 1x 具名 NOT-RUN 继续按名出现；版本行布局未动。

453 追记（R433 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R433 · 仍开）：菜单具名标记仍未发射；菜单 5/5 由真实 NSMenu 用例作证。

455 追记（R433 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R433 · 仍开）：跨年记录仍无年份。

457 追记（R433 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R433 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效（R432 跑两档都出现、不计红）；CI 上的行首符号像素证人仍缺。

**459. 高夹具（720×1040）在 runner 1x 整帧不画：依赖 tall 帧的像素判据在 CI 上没有对象**（R433 观察）
    现象：R432 跑里 `settings-privacy-tall` 的 `EXCLUDED_APP_ROW light/dark 行数=0 判=0` —— 同一台机器上 540 高的 `settings-privacy` 能画（caption 探针 17 条全判、排除名单 540 帧 5 行有墨）。与 458 的 `content-with-history` 同族，但触发条件是**帧高度 >1000pt**（1100pt 宽那族 R28b 早已登记）。
    修法（下一轮若需要）：把依赖 tall 帧的判据全部改成"540 帧首屏"或"分段拼帧"，tall 帧只留在本机做整页节奏对照；或者给捕获通道加一条"超尺寸帧在 1x 上自动降级为分块拍摄"的实现（成本高，先登记）。
"""

STATE_SECTION = u"""## R433 状态（2026-10-27 · 本地 · 第 432 轮 / Round 430）：详情大图补 1pt 中性边（白底图在白底详情里旧差 0.0 → 新 32.0/28.0；贴合尺寸只缩不放，240×140 不变；2 张详情帧变化、基线 238）；R432 跑失败步骤 2 个（高夹具 720×1040 在 1x 整帧不画）⇒ 换 540 帧保住 CI 像素证人（产品 1 文件，详情图片预览位）

最后更新：2026-10-27（本地 · R433 / 第 432 轮 / Round 430）：详情大图以前没有任何边/阴影 —— 图沿外 1–3pt 与 20pt 外的页面底色亮度差 **0.0/0.0**，白底截图在白底详情里整张看不出边界。新 `ImagePreviewLayout.fittedSize`（**只缩不放**，与旧 `scaledToFit` 一致）+ 图外 **1pt** `Color.primary.opacity(VisualTint.chipStroke)` 中性边（挂在贴合图本身的尺寸上，不是上限框）。修后 `DETAIL_IMAGE_EDGE light 图框=480..959×440..719px 页底=255.0 边带最大差=32.0`、dark `页底=30.0 边带最大差=28.0`（旧 0.0/0.0）；图框 240×140pt 不变（第一版漏 `min(1, …)` 把图拉到 680×397，已收回并写进单测）。2 张 `detail-1-image` 帧变化，基线 **238/0/0/0**。R432 run `40519498631 ↔ f39f66c` **failure，失败步骤 2 个**（Swift tests / Capture gate）：唯一红是 `settings-privacy-tall`（720×1040）在 1x 整帧不画（行数 0）⇒ 排除名单判据改用 540 帧、要求 ≥3 行（本机 5 行、首段 10–14pt），阈值未动；`FILE_ROW_SYMBOL_NOT_RUN` 按名生效不计红；理由带 290 后 typed 217 / list 0。时间列 1x light `[74,71,74,74,74]`、dark `[74,72,74,74,74]`；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；菜单 5/5；floor 5/5/77 无红；回执 2/2；滚动 4/4（`CHANNEL 0→125→600 30000/17000`）。`M1189–M1191` **3/3 CAUGHT**；预检 **211/193/558 bad=0**、ARM **304 文件 / 1041 把**、HIDDEN **298/975 rot=0**。本地全量 **1172/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/8/31.5/1438`、`CHANNEL 0→96→600 变化 153619/172800 重抓=no`、`OFFSET 0/192.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **140/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 432，现读 `python3 scripts/product_streak.py --streak-for 432`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R432 跑 failure、失败步骤 2 个：唯一红是高夹具 1x 整帧不画（行数 0）⇒ 换 540 帧、≥3 行，阈值未动；`FILE_ROW_SYMBOL_NOT_RUN` 按名生效；时间列/脚注/分区/表格/菜单/floor/回执/滚动全绿。
② 产品：详情大图补 1pt 中性边（旧 0.0 → 新 32.0/28.0；图尺寸不变）。
③ 判据：M1189–M1191 3/3；四条贴合尺寸单测；precheck 211/193/558；hidden rot 0。
④ 436：R432 跑 floor judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 298 / 可判 975 / rot 0。
⑥ 捕获 140/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1172/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置脚注带 1x；② 主窗口 content 帧 1x 整帧不画（458）；③ 高夹具 1x 整帧不画（459）；④ 13+ 菜单像素/标题（454）；⑤ 真实拖拽（453）；⑥ Dock 像素；⑦ 源图标最小窗文字 1x；⑧ 本地全量 5 条滚动红（449）；⑨ 2x/extended；⑩ 固定块揭示偏移（455）；⑪ 跨年时间（456）；⑫ 主列表暗档文字盲区（457）；⑬ 真机/多屏（447）；⑭ 真菜单栏、12 实时腿；⑮ `table-lazy-rows`；⑯ 437–459 仍开；⑰ R433 新跑待 push 后读。

下一轮（R434）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R433 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `DETAIL_IMAGE_EDGE` 在 1x 上的边带差、`EXCLUDED_APP_ROW` 540 帧 5 行、`FILE_ROW_SYMBOL_NOT_RUN`、理由带 290、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R433_REPORT_BULLET = u"""- **R433（详情图片预览边）**：详情大图以前没有任何边/阴影 —— 图沿外 1–3pt 与 20pt 外的页面底色亮度差 **0.0/0.0**，白底截图在白底详情里整张看不出边界。新 `ImagePreviewLayout.fittedSize`（**只缩不放**，与旧 `scaledToFit` 一致）+ 图外 **1pt** `Color.primary.opacity(VisualTint.chipStroke)` 中性边（挂在贴合图本身的尺寸上，不是上限框）。修后同尺：`DETAIL_IMAGE_EDGE light 图框=480..959×440..719px 页底=255.0 边带最大差=32.0`、dark `页底=30.0 边带最大差=28.0`（旧 0.0/0.0）；图框 240×140pt 不变（第一版漏 `min(1, …)` 把图拉到 680×397，当场收回并写进单测）。2 张 `detail-1-image` 帧变化，基线 **238/0/0/0**。R432 run `40519498631 ↔ f39f66c` **failure、失败步骤 2 个**（Swift tests / Capture gate）：唯一红是 `settings-privacy-tall`（720×1040）在 1x 整帧不画（行数 0）⇒ 排除名单判据改用能画的 `settings-privacy` 540 帧、要求 ≥3 行（本机 5 行、首段 10–14pt），阈值未动；`FILE_ROW_SYMBOL_NOT_RUN` 按名生效不计红；理由带 290 后 typed 217 / list 0。时间列 1x light `[74,71,74,74,74]`、dark `[74,72,74,74,74]`；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；菜单 5/5；floor 5/5/77；回执 2/2；滚动 4/4（`CHANNEL 0→125→600`）。M1189–M1191 **3/3**；预检 211/193/558 bad=0；HIDDEN 298/975 rot=0。本地全量 **1172/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/8、31.5→1438；CHANNEL 0→96→600、153619/172800）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 140/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 432 轮（R433" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R433 节")
if u"## Round 430 · R433" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 430")
if u"## D-429" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-429")
if u"详情大图补 1pt 中性边" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**459." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 459")
if state.count(u"## R432 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R432 状态"))
U_CELL_OLD = u"U-31 … U-1587（R432 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R432 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R432 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_429 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R432 状态", STATE_SECTION + u"## R432 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1592（R433 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R432 节 ②",
                                u"AGENT_STATE.md` 的 R433 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R433_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R433_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
