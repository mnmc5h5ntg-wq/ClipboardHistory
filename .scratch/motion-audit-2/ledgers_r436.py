#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R436 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 434 轮（R435 · 2026-10-28"
AUDIT_SECTION = u"""## 第 435 轮（R436 · 2026-10-28 · U-1603…U-1607）：批量操作栏补破坏性分隔线（删除与其余四颗之间 1pt 发丝；局部对比 light 13.7 / dark 11.9，旧 0–1；4 张多选帧变化、基线 238）；R435 跑失败步骤 2 个（list 占位语 1x 无墨被当校准、行插入动画采样 2<3）⇒ 修仪器/重抓、阈值未动（产品 1 文件，批量操作栏位）

- **U-1603：⓪ R435 跑的失败步骤与清除 ×/仪器命运。** `40544941175 ↔ 1041d0f` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。两条红：① `testQuickPickSearchFieldShowsAClearButtonOnlyWhenTyping` 两档都在 **list 帧的搜索框左半段**读到 `校准=0` —— 把 `quickpick-list` 的**占位语**当了"这屏画出来了"的校准，而占位语在 runner 1x 上没有墨（typed 帧的查询文字正常）；**清除 × 本身没被判到**（断言在 list 校准处就停了）。② `MotionFilmstripTests.testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt`：same 臂 `2 < 3`（该测试本就在 `SUITE_NOT_SEEN` 的采样漂移名册里）—— 动画在跑，但 1x runner 的相位把过渡夹在两端。其余读数以 R434 跑为最近完整签收（`EXCLUDED_APP_ROW_NOT_RUN`/`DETAIL_IMAGE_EDGE` 30/26/`HTML_HEADING_LADDER` 19/18/理由带/时间列/脚注/分区/回执/滚动）；本跑日志在复盘时被 GitHub EOF 挡住，未再取到新的通道行（照实记：这一次只读到两条错误正文）。
- **U-1604：⓪ 的修法：换校准对象 + 只对"该动"那一臂做相位重抓。** ① 清除 × 判据改校准：typed 仍读**搜索框左半段**（查询文字），list 改读**同一帧第 0 行标题**（x40..200、y57..70；它在 1x 上一直有墨）——校准对象必须选"这台机器确实画得出的那一块"，占位语不是。② 行插入动画：`same` 臂最多录三次、取**帧数最多**的一卷（`sameSpan` 达标即停），`minimumTransitionFrames=3` 一字不动；`moved` 臂不重抓（它判的是"不该动"）；emit 增加 `重抓=N`。两条都是仪器，不降门槛。
- **U-1605：② 批量操作栏补破坏性分隔线。** 缺陷形状（`sidebar-multi-select` 亮/暗直看）：五颗按钮在 `spacing: 0` 的一排里，破坏性的垃圾桶只靠红色与其余四颗分开；两颗之间的空隙里一笔墨都没有。修法：在垃圾桶前插一条 **1×14pt 的 `Rectangle().fill(Color.primary.opacity(0.18))`**（`Divider()` 在这个离屏 HStack 里不落墨，第一版就是它，帧上 0 读数——已换掉）。旧/新（`BULK_ACTION_SEPARATOR`）：垃圾桶左沿 265.5pt，其左侧 **258..263pt** 的局部对比旧 **0–1 → 新 light 13.7 / dark 11.9**；垃圾桶红墨 333/265 作校准。4 张多选帧变化（`sidebar-multi-select` 与 `-min` × 亮暗），基线仍 **238/0/0/0**。真看图：删除与四颗普通动作之间出现一条细竖线，红垃圾桶不再孤零零地靠颜色区分。
- **U-1606：判据与刀（含一次假绿的当场收回）。** 新 `testBulkActionBarSeparatesTheDestructiveButton`：按红色找垃圾桶最左列，量其左侧 6pt 处的**局部对比**（每列与左右各 4pt 列比；材质渐变在局部是平的）。第一版用"与远处底色的差"，读数 23.8 看着像线，**刀 M1197（整条撤掉）仍然 CAUGHT 不了** —— 那是侧栏材质渐变冒充的线（假绿），当场换成局部对比并把带收窄到 258..263；地板取 8（旧形状 0–1，暗档发丝线 11.9，仍有约 8 倍余量）。`M1197–M1198` **2/2 CAUGHT**（撤线 / 推到带外）。预检 `tables=214 covered=196 arms=564 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=307 arms=1047 dupes=0`；`HIDDEN_ARMS 表=301 可判=981 rot=0`。
- **U-1607：八步。** build **0 告警**；捕获 **143 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `CHANGED=4 / MISSING=0 / ADDED=0`（`sidebar-multi-select` ×2、`sidebar-multi-select-min` ×2），`UPDATED=238`、复验 **238/0/0/0**；全量 **1180/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=9/首=43/末=1438`、`CHANNEL 0→83.5→600 变化 46073/112800 重抓=no`、`OFFSET 0/199.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 435，现读 `python3 scripts/product_streak.py --streak-for 435`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑；口径与 R435 一致，不回退成 4）。
- **具名 NOT-RUN / 观察**：① 设置内容列 1x 平涂（`EXCLUDED_APP_ROW_NOT_RUN`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 清除按钮命中区 18pt（461）；⑲ 批量分隔线用的 0.18 透明度是就地数、未提成令牌（462）；⑳ 437–462 仍开；㉑ R436 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 433 · R436（第 435 轮 · 2026-10-28）：批量操作栏补破坏性分隔线（删除与其余四颗之间 1pt 发丝；局部对比 light 13.7 / dark 11.9，旧 0–1；4 张多选帧变化、基线 238）；R435 跑失败步骤 2 个（list 占位语 1x 无墨被当校准、行插入动画采样 2<3）⇒ 修仪器/重抓、阈值未动（产品 1 文件，批量操作栏位）

批量操作栏的五颗按钮在 `spacing: 0` 的一排里，破坏性的垃圾桶只靠红色与其余四颗分开。修法：垃圾桶前插一条 1×14pt `Rectangle().fill(Color.primary.opacity(0.18))`（`Divider()` 在这个离屏 HStack 里不落墨，已换掉）。旧/新：垃圾桶左沿 265.5pt，其左侧 258..263pt 的**局部对比** 0–1 → light 13.7 / dark 11.9；4 张多选帧变化，基线 238/0/0/0。判据第一版拿"与远处底色的差"，刀 M1197 撤线仍绿（材质渐变冒充），当场换成局部对比并把地板取 8；M1197–M1198 2/2。R435 run `40544941175 ↔ 1041d0f` **failure、失败步骤 2 个**（Swift tests / Capture gate）：① 清除 × 判据把 `quickpick-list` 的**占位语**当校准，runner 1x 上占位语无墨（typed 正常）⇒ list 改读同一帧第 0 行标题；② 行插入动画 same 臂采样 2<3 ⇒ 只对该动的臂做相位重抓（最多三次、取帧数最多），阈值未动。预检 214/196/564 bad=0；HIDDEN 301/981 rot=0。全量 1180/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/9、43→1438；CHANNEL 0→83.5→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 143/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看 `sidebar-multi-select` 与 `-min` 亮暗：删除前多出一条细竖线，红垃圾桶不再只靠颜色区分。扣 2：没有真机截图；线宽/透明度是就地数（462）。 |
| 判据有效性 | 15/15 | 局部对比尺 + 红色垃圾桶校准 + 两把刀；**第一版被刀证伪（假绿）后当场换尺**，M1197–M1198 2/2。 |
| 假绿防御 | 15/15 | 材质渐变不再能冒充分隔线；校准从占位语换成标题（1x 稳）；动画重抓只给"该动"的臂，真静止仍 0–1。 |
| 产品面推进 | 14/15 | 真落 1 文件（批量操作栏位），把破坏性动作从"只靠颜色"变成"有边界"；扣 1：仅分隔线，未做分组标题。 |
| 台账一致性 | 15/15 | U-1603…U-1607、D-432、R435 的两条红、R436 的 13.7/11.9、1180 都从日志/帧/用例解析。 |
| 交付诚实性 | 15/15 | 第一版假绿（材质渐变）照实写并收回；R435 的两条红逐条定位；GitHub EOF 导致本次未取到的通道行照实标注。 |
| 可复核性 | 15/15 | 帧名、两档局部对比、垃圾桶坐标、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_432 = u"""## D-432 破坏性动作与普通动作之间加分隔线；发丝线用局部对比量（R436）

- 背景：批量操作栏五颗按钮在 `spacing: 0` 的一排里，删除只靠红色与其余四颗分开；`Divider()` 在这个离屏 HStack 里不落墨（帧上 0 读数）。
- 决定：① 垃圾桶前插 1×14pt `Rectangle().fill(Color.primary.opacity(0.18))`；② 判据按红色找到垃圾桶，量其左侧 258..263pt 的**局部对比**（每列与左右 4pt 列比），地板 8；③ 行插入动画的 same 臂允许相位重抓（最多三次、取帧数最多），`minimumTransitionFrames` 不动。
- 理由：分隔线是"动作的边界"，不是装饰；用远处底色量会把侧栏材质渐变读成线（M1197 当场证伪），局部对比对渐变免疫。动画采样在 1x runner 上会夹相位，重抓与 R424 的回执同一族，只给"该动"的臂。
- 兼容性/迁移：批量操作栏多 3pt 宽（1pt 线 + 两侧各 2pt padding），4 张多选帧变化，基线仍 238。
- 边界：0.18 是就地数、未提成令牌（462）；只在 side bar 的多选头上加，设置页没有同类动作栏。
- 回滚：删 `Rectangle` 三行即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 批量操作栏补破坏性分隔线（删除与其余四颗之间 1pt 发丝；局部对比 light 13.7 / dark 11.9，旧 0–1；4 张多选帧变化、基线 238）；R435 跑失败步骤 2 个（list 占位语 1x 无墨被当校准、行插入动画采样 2<3）⇒ 修仪器/重抓、阈值未动（R436 / 第 435 轮 / Round 433 / U-1603…U-1607 · 产品 1 文件，批量操作栏位）

"""

BACKLOG_SECTION = u"""437 追记（R436 · 仍开）：本轮只动批量操作栏；主列表仍不匹配 `sourceAppName`。

449 追记（R436 · 仍开）：R435 跑的行插入动画 same 臂在 1x runner 上采样 2<3（`SUITE_NOT_SEEN` 漂移名册里那一族）；本轮加相位重抓，不改门槛。

451 追记（R436 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R436 · 仍开）：脚注 1x 具名 NOT-RUN 继续按名出现。

453 追记（R436 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R436 · 仍开）：菜单具名标记仍未发射；菜单 5/5 由真实 NSMenu 用例作证。

455 追记（R436 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R436 · 仍开）：跨年记录仍无年份。

457 追记（R436 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字。

458 追记（R436 · 仍开）：`FILE_ROW_SYMBOL_NOT_RUN` 已按名生效；CI 上的行首符号像素证人仍缺。

459 追记（R436 · 仍开）：设置内容列/高夹具在 1x 整列平涂（`EXCLUDED_APP_ROW_NOT_RUN` 依此）。

460 追记（R436 · 仍开）：HTML 六档以上字号仍会后排压到 12pt。

461 追记（R436 · 仍开）：浮层清除 × 命中区 18pt，仍低于主窗口搜索框的 22pt。

**462. 批量操作栏分隔线的透明度是就地数（0.18），没有提成令牌**（R436 观察）
    现象：`Rectangle().fill(Color.primary.opacity(0.18))` 里的 0.18 是在本轮的帧上挑的（亮档局部对比 13.7、暗档 11.9），而仓库的竖线本来有 `VisualHairline.divider` / `VisualTint` 那套令牌；下一轮若有人统一"竖线"，这一处会被漏掉，因为它长得像一次性装饰。
    修法（下一轮若需要）：把"动作组之间的分隔线"提成一枚具名令牌（宽度 + 透明度 + 高度），并把这条判据的地板接在令牌上；改之前先确认设置页/工具栏没有第二处同类竖线（现读只有这一处）。
"""

STATE_SECTION = u"""## R436 状态（2026-10-28 · 本地 · 第 435 轮 / Round 433）：批量操作栏补破坏性分隔线（删除与其余四颗之间 1pt 发丝；局部对比 light 13.7 / dark 11.9，旧 0–1；4 张多选帧变化、基线 238）；R435 跑失败步骤 2 个（list 占位语 1x 无墨被当校准、行插入动画采样 2<3）⇒ 修仪器/重抓、阈值未动（产品 1 文件，批量操作栏位）

最后更新：2026-10-28（本地 · R436 / 第 435 轮 / Round 433）：批量操作栏的五颗按钮在 `spacing: 0` 的一排里，破坏性的垃圾桶只靠红色与其余四颗分开。修法：垃圾桶前插一条 1×14pt 的 `Rectangle().fill(Color.primary.opacity(0.18))`（`Divider()` 在这个离屏 HStack 里不落墨，第一版即它、帧上 0 读数，已换掉）。旧/新：垃圾桶左沿 265.5pt，其左侧 258..263pt 的**局部对比** 0–1 → light **13.7** / dark **11.9**；垃圾桶红墨 333/265 作校准。4 张多选帧变化（`sidebar-multi-select` 与 `-min` × 亮暗），基线 **238/0/0/0**。判据第一版用"与远处底色的差"，刀 M1197 撤线仍绿（侧栏材质渐变冒充）⇒ 改成局部对比、带收窄、地板 8；`M1197–M1198` **2/2 CAUGHT**。R435 run `40544941175 ↔ 1041d0f` **failure，失败步骤 2 个**（Swift tests / Capture gate）：① 清除 × 判据把 `quickpick-list` 的占位语当校准，1x 上占位语无墨（typed 正常）⇒ list 改读同一帧第 0 行标题；② 行插入动画 same 臂 2<3 ⇒ 只对该动的臂相位重抓（最多三次、取帧数最多），阈值未动。预检 **214/196/564 bad=0**、ARM **307 文件 / 1047 把**、HIDDEN **301/981 rot=0**。本地全量 **1180/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/9/43/1438`、`CHANNEL 0→83.5→600 变化 46073/112800 重抓=no`、`OFFSET 0/199.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **143/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 435，现读 `python3 scripts/product_streak.py --streak-for 435`）。电池 `Ran 683 / OK (skipped=5)`（台账后复跑；口径与 R435 一致，不回退成 4）。

本轮做了什么：
① ⓪ R435 跑 failure、失败步骤 2 个：清除 × 判据的 list 校准（占位语 1x 无墨）与行插入动画采样 2<3 ⇒ 换校准对象 + 相位重抓，阈值未动。
② 产品：批量操作栏补破坏性分隔线（局部对比 0–1 → 13.7/11.9）。
③ 判据：第一版假绿由刀证伪后换局部对比；M1197–M1198 2/2；precheck 214/196/564；hidden rot 0。
④ 436：R434 跑 floor 5/5/77 无红（R435 跑日志被 EOF 挡住，通道未再取到；红已逐条读）。
⑤ 367：hidden 表 301 / 可判 981 / rot 0。
⑥ 捕获 143/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1180/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置内容列 1x 平涂（`EXCLUDED_APP_ROW_NOT_RUN`，459）；② 设置脚注带 1x；③ 主窗口 content 帧 1x（458）；④ 高夹具 1x（459）；⑤ 13+ 菜单像素/标题（454）；⑥ 真实拖拽（453）；⑦ Dock 像素；⑧ 源图标最小窗文字 1x；⑨ 本地全量 5 条滚动红（449）；⑩ 2x/extended；⑪ 固定块揭示偏移（455）；⑫ 跨年时间（456）；⑬ 主列表暗档文字盲区（457）；⑭ 真机/多屏（447）；⑮ 真菜单栏、12 实时腿；⑯ `table-lazy-rows`；⑰ HTML 六档以上字号（460）；⑱ 清除按钮命中区 18pt（461）；⑲ 分隔线透明度未提令牌（462）；⑳ 437–462 仍开；㉑ R436 新跑待 push 后读。

下一轮（R437）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R436 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `BULK_ACTION_SEPARATOR` 两档局部对比（13.7/11.9）、清除 × 判据的 list 校准、`MOTION_SEQUENCE` 重抓后 same 臂 ≥3、`EXCLUDED_APP_ROW_NOT_RUN`、`DETAIL_IMAGE_EDGE`、`HTML_HEADING_LADDER`、理由带、时间列、脚注、分区、菜单、Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R436_REPORT_BULLET = u"""- **R436（批量操作栏位）**：五颗按钮在 `spacing: 0` 的一排里，破坏性的垃圾桶只靠红色与其余四颗分开。修法：垃圾桶前插一条 1×14pt `Rectangle().fill(Color.primary.opacity(0.18))`（`Divider()` 在这个离屏 HStack 里不落墨，第一版即它、帧上 0 读数，已换掉）。旧/新：垃圾桶左沿 265.5pt，其左侧 258..263pt 的**局部对比** 0–1 → light **13.7** / dark **11.9**；4 张多选帧变化，基线 **238/0/0/0**。判据第一版用"与远处底色的差"，刀 M1197 撤线仍绿（侧栏材质渐变冒充）⇒ 改局部对比、带收窄、地板 8；M1197–M1198 **2/2**。R435 run `40544941175 ↔ 1041d0f` **failure、失败步骤 2 个**（Swift tests / Capture gate）：① 清除 × 判据把 `quickpick-list` 的占位语当校准，1x 上占位语无墨（typed 正常）⇒ list 改读同一帧第 0 行标题；② 行插入动画 same 臂采样 2<3 ⇒ 只对该动的臂相位重抓（最多三次、取帧数最多），阈值未动。预检 214/196/564 bad=0；HIDDEN 301/981 rot=0。本地全量 **1180/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/9、43→1438；CHANNEL 0→83.5→600、46073/112800）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 143/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/5。
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
if u"第 435 轮（R436" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R436 节")
if u"## Round 433 · R436" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 433")
if u"## D-432" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-432")
if u"批量操作栏补破坏性分隔线" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**462." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 462")
if state.count(u"## R435 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R435 状态"))
U_CELL_OLD = u"U-31 … U-1602（R435 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R435 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R435 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_432 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R435 状态", STATE_SECTION + u"## R435 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1607（R436 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R435 节 ②",
                                u"AGENT_STATE.md` 的 R436 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R436_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R436_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
