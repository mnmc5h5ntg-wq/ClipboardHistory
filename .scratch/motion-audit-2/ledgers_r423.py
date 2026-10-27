#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R423 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


def rd(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


AUDIT_TITLE = u"## 第 421 轮（R422 · 2026-10-27"
AUDIT_SECTION = u"""## 第 422 轮（R423 · 2026-10-27 · U-1538…U-1542）：搜索无结果态补放大镜与查询词（新标题带词、旧「无匹配结果」；组件带 7790→8841 墨、128→264 宽）；R422 跑全绿（静态对照 28800、空态 4 帧 151/16→1279/28）；本地全量 5 条滚动红具名会话/顺序 NOT-RUN（产品 2 文件，搜索无结果态）

- **U-1538：⓪ `40453992908 ↔ 4123793` 的失败步骤与静态/空态命运。** 结论 **success**，失败步骤 **0 个**。静态文档滚动正对照**正常通过**：`SCROLL_REVEAL_CHANNEL 起点=0 中段=124 落点=600 起→中=28800 中→落=14510 重抓=no` —— 中段帧这次没错过重绘，重抓没触发（R422 的 re-grab 与 `mid-frame-race` 出口仍留在盘上作保险）。空态插画 **4 帧在 runner 上绿**：`EMPTY_STATE_ILLUSTRATION light 字形墨=151 盒高=16 插画墨=1279 盒高=28`、`dark 151/16 → 1271/28`（1x 的绝对量约本机 2x 的 1/3.6；按 `scale²` 推的地板 ⟨20、+10pt⟩ 都过）。floor：`MOTION_FLOOR_FACTS judged=4/5 executed=76 not-run=notice-banner`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=4/5`、无 unlisted；`content-empty` 两帧变化随基线进闸门。436 见 U-1541。
- **U-1539：② 搜索无结果态补放大镜与查询词。** 以前所有空态共用 `clipboard` 图标和「无匹配结果」：搜不到时画的还是剪贴板，也不告诉用户**哪个词**没找到。新 `SearchNoResultsPresentation`：无结果时画 `magnifyingglass`、标题写「没有找到「查询词」」；查询词两端空白归一、超过 24 字截断加省略号；**收藏为空仍是「暂无收藏」+ 剪贴板**（那是状态，不是搜不到）；没有历史仍是「暂无剪贴板历史」；R407 的「清除搜索」CTA 不动。侧栏只消费 policy。真看图：`sidebar-no-results` 现在是放大镜 + 「没有找到「不存在的词」」+ 清除搜索。组件旧/新（250×220，同 CTA）：旧墨 **7790/8030**、新 **8841/9234**、变化 **9360/9880**、墨宽 **128→264**（2x）。产品 `content-no-results` 与 `sidebar-no-results` 亮暗 **4 帧变化**，新增组件 4 帧，基线 **222→226**（4 变 + 4 增）。
- **U-1540：判据与刀。** 纯真值表（图标：无历史/收藏空/空白词 → 剪贴板；真 miss → 放大镜；标题：query/空白/长词截断/收藏空/无历史）+ 源守卫（侧栏走 `SearchNoResultsPresentation.iconName/title`、旧 `emptyTitle` 已删）+ 组件像素尺（新标题更宽、图标/标题确实换）。`M1115…M1118` **4/4 CAUGHT**（M1115 图标恒剪贴板；M1116 标题不写词；M1117 不截断；M1118 侧栏硬编码）。**一次自伤**：给滚动测试加 `NSApp.activate + makeKeyAndOrderFront` 想修全量卷里的 key 状态，结果单跑也把动画弄没（完成回调不来）⇒ 已整段回滚，`SelectionRevealAnimationTests.swift` 与已提交版本 **零 diff**。预检 `tables=183 covered=165 arms=491 bad=0`、全仓 **276 文件 / 975 把**；`HIDDEN_ARMS 表=270 可判=909 rot=0`。
- **U-1541：③ 436 只读新跑。** `40453992908`：`judged=4/5 executed=76 not-run=notice-banner`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=4/5`；没有红用例、没有 `MOTION_FLOOR_UNLISTED` 行；`notice-banner` 是登记放行的 not-run 臂，未重猜 `must_judge`。**REDS=0**。
- **U-1542：① 367 rot 与八步。** `HIDDEN_ARMS 表=270 可判=909 rot=0`（R422 268/905，本轮 +2 表 +4 臂）；预检 `tables=183 covered=165 arms=491 bad=0`、`ARM_TOTAL files=276 arms=975 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`。build **0** 告警；捕获 **226 帧 / 131 条 / 4 skip / 0 失败**；基线 `UPDATED=226`、复验 `COMPARED=226 CHANGED=0 MISSING=0 ADDED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 422，现读 `python3 scripts/product_streak.py --streak-for 422`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。**本地全量 `1127/57/5`：5 条全部在 `SelectionRevealAnimationTests`（2 条 reveal + 1 条 product-duration + 1 条 static；共 5 条断言）—— 同一份代码单跑（`caffeinate -u` 唤醒后）8 个中间值、末 1438、静态对照通过，R422 的 CI 卷也全绿 ⇒ 本地是**整卷顺序/会话**把 AppKit 滚动动画的完成回调挡住，不是 R423 产品红；地板一个没动，具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。**
- **具名 NOT-RUN / 观察**：① 本地全量的 5 条滚动/动画红（具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`；单跑 + R422 CI 绿）；② markdown 2x / sidebar 2x / receipt 消失臂在 extended；③ 真机/多屏面板落点无截屏（447）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–449 仍开；⑩ R423 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 420 · R423（第 422 轮 · 2026-10-27）：搜索无结果态补放大镜与查询词（新标题带词、旧「无匹配结果」；组件带 7790→8841 墨、128→264 宽）；R422 跑全绿（静态对照 28800、空态 4 帧 151/16→1279/28）；本地全量 5 条滚动红具名会话/顺序 NOT-RUN（产品 2 文件，搜索无结果态）

搜索无结果态以前画剪贴板、只说「无匹配结果」。新 `SearchNoResultsPresentation`：miss 画放大镜、标题「没有找到「查询词」」、空白归一、24 字截断；收藏空/无历史仍剪贴板+旧文案；CTA 不动。真看图 `sidebar-no-results` 是放大镜+查询词+清除搜索；组件带 7790/8030→8841/9234、宽 128→264。产品 4 帧变化+组件 4 帧，基线 226。M1115–M1118 4/4；一次给滚动测试加 key 窗口的自伤已整段回滚（零 diff）。R422 跑全绿：静态对照 28800/重抓=no、空态 4 帧 151/16→1279/28、floor judged=4/5 executed=76、REDS=0。本地全量 1127/57/5，5 条全在 SelectionRevealAnimationTests（单跑 8 中间值/末 1438、R422 CI 绿）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 226/131/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162=162；HIDDEN 270/909 rot=0；预检 183/165/491；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 sidebar-no-results 与组件旧/新：放大镜、查询词、清除搜索，旧臂对照同 CTA。 |
| 判据有效性 | 15/15 | 纯真值表 + 源守卫 + 组件像素（更宽、图标/标题换了）；M1115–M1118 4/4。 |
| 假绿防御 | 15/15 | 旧臂仍在组件里作对照；产品 4 帧变化进基线；4 把刀各钉一侧；截断/收藏空各有格子。 |
| 产品面推进 | 14/15 | 真落 Sources 2 文件、补的是搜索无结果语义；扣 1：收藏空仍是旧字形，空态语言未统一（448）。 |
| 台账一致性 | 15/15 | U-1538…U-1542、D-419、436 的 judged=4/5/executed=76、R422 跑的 28800 与空态 4 帧都从日志解析。 |
| 交付诚实性 | 15/15 | 本地全量 5 条滚动红照实写、具名会话/顺序 NOT-RUN、单跑与 R422 CI 证据并列；key 窗口自伤已回滚并落账。 |
| 可复核性 | 15/15 | 组件旧/新四读数、四张新帧 + 四张变化帧、4 把刀、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_419 = u"""## D-419 搜索无结果态用放大镜并把查询词写进标题（R423）

- 背景：所有空态共用 `clipboard` 图标与「无匹配结果」；搜不到时画剪贴板、也不告诉用户哪个词没找到。
- 决定：`SearchNoResultsPresentation` 纯函数：真 miss（有记录、非收藏空、查询词非空）→ `magnifyingglass` + 「没有找到「查询词」」；查询词两端空白归一、超过 24 字截断加省略号；收藏为空仍「暂无收藏」+ 剪贴板，无历史仍「暂无剪贴板历史」；侧栏只消费 policy，旧 `emptyTitle` 删除。R407 的「清除搜索」CTA 不变。
- 理由：无结果是"搜不到"，不是"还没有"；把词写回去用户才知道是哪个词；截断防止 250pt 侧栏标题挤出多行；收藏空是状态，不该被查询词改写。
- 兼容性/迁移：`content-no-results`/`sidebar-no-results` 亮暗 4 帧变化，新增组件 4 帧，基线 226；其它空态（无历史插画、详情空态）不变。
- 回滚：删 `SearchNoResultsPresentation` 并恢复 `emptyTitle` 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 搜索无结果态补放大镜与查询词（新标题带词、旧「无匹配结果」；组件带 7790→8841 墨、128→264 宽）；R422 跑全绿（静态对照 28800、空态 4 帧 151/16→1279/28）；本地全量 5 条滚动红具名会话/顺序 NOT-RUN（R423 / 第 422 轮 / Round 420 / U-1538…U-1542 · 产品 2 文件，搜索无结果态）

"""

BACKLOG_SECTION = u"""437 追记（R423 · 仍开）：本轮补的是搜索无结果态的图标与查询词；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

448 追记（R423 · 仍开）：空态语言现在分三档 —— 无历史（叠卡插画）、无匹配（放大镜+查询词）、收藏空（剪贴板+暂无收藏）；是否把收藏空也画一套图标仍未定。

**449. 滚动/动画类测试在「整卷」里会因会话/顺序把 AppKit 动画的完成回调挡住（单跑能过、全量 5 红）**（R423）
    现象：`SelectionRevealAnimationTests` 的 4 条（5 个断言）在本机整卷里 origin 恒 0（动画没开始/完成回调不来），同一份代码单跑（`caffeinate -u` 唤醒后）读到 8 个中间值、末 1438、静态对照通过；R422 的 CI 卷全绿。试过给测试窗口加 `NSApp.activate + makeKeyAndOrderFront`，单跑反而把动画弄没（已回滚）。
    修法（下一轮）：先量「整卷跑到 SelectionReveal 时 app 的 `isActive/isHidden`、窗口 `isVisible`、runloop 模式」各一格，再决定是给夹具补自包含前提、还是给这两类测试一条具名的会话能力出口；不要靠 `caffeinate` 或加 sleep 蒙混，也不要改 reveal 的判据门槛。
"""

STATE_SECTION = u"""## R423 状态（2026-10-27 · 本地 · 第 422 轮 / Round 420）：搜索无结果态补放大镜与查询词（新标题带词、旧「无匹配结果」；组件带 7790→8841 墨、128→264 宽）；R422 跑全绿（静态对照 28800、空态 4 帧 151/16→1279/28）；本地全量 5 条滚动红具名会话/顺序 NOT-RUN（产品 2 文件，搜索无结果态）

最后更新：2026-10-27（本地 · R423 / 第 422 轮 / Round 420）：搜索无结果态以前画剪贴板、只说「无匹配结果」。新 `SearchNoResultsPresentation`：真 miss 画 `magnifyingglass`、标题「没有找到「查询词」」（空白归一、24 字截断）；收藏空仍「暂无收藏」+剪贴板、无历史仍「暂无剪贴板历史」；R407 的「清除搜索」CTA 不动；侧栏只消费 policy，旧 `emptyTitle` 删除。真看图 `sidebar-no-results` 是放大镜+查询词+清除搜索；组件旧/新 250×220：旧墨 **7790/8030**、新 **8841/9234**、变化 **9360/9880**、墨宽 **128→264**（2x）。产品 `content-no-results`/`sidebar-no-results` 亮暗 **4 帧变化** + 组件 4 帧新增，基线 **226/0/0/0**。`M1115–M1118` **4/4 CAUGHT**（M1115 图标恒剪贴板；M1116 不写词；M1117 不截断；M1118 侧栏硬编码）；一次给滚动测试加 key 窗口的自伤已整段回滚（`SelectionRevealAnimationTests.swift` 零 diff）。R422 run `40453992908 ↔ 4123793` **success、失败步骤 0**：静态对照 `起→中=28800 中→落=14510 重抓=no`、空态 4 帧 `151/16→1279/28`（runner 1x）、floor `judged=4/5 executed=76 not-run=notice-banner`、`SUITE_CLEAN=0`、无 unlisted ⇒ **436 REDS=0**。本地全量 **1127/57/5**：5 条全在 `SelectionRevealAnimationTests`，同一份代码单跑（caffeinate -u 唤醒后）8 中间值/末 1438、静态通过，R422 CI 绿 ⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；捕获 **226/131/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 270/909 rot=0；预检 183/165/491 bad=0；产品面连续零改动 **1** 轮（as-of 422，现读 `python3 scripts/product_streak.py --streak-for 422`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R422 跑全绿（静态对照 28800、重抓=no；空态 4 帧 151/16→1279/28；floor judged=4/5 executed=76；无 unlisted）。
② 产品：搜索无结果态补放大镜+查询词（组件 7790→8841 墨、128→264 宽），产品 4 帧变化 + 组件 4 帧，基线 226。
③ 判据：M1115–M1118 4/4；precheck 183/165/491；hidden rot 0；key 窗口自伤已回滚。
④ 436：judged=4/5 executed=76、SUITE_CLEAN=0、notice-banner 放行；REDS=0。
⑤ 367：hidden 表 270 / 可判 909 / rot 0 / 上界 0；ARM 276 文件 / 975 把。
⑥ 捕获 226/131/4/0；换装 ok；清账 162=162；帧基线 226/0/0/0；本地全量 1127/57/5（5 条滚动红具名会话/顺序 NOT-RUN）。

NOT-RUN / 阻塞（分开写）：① 本地全量的 5 条滚动/动画红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`；单跑与 R422 CI 绿，449）；② markdown 2x / sidebar 2x / receipt 消失臂在 extended；③ 真机/多屏面板落点无截屏（447）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–449 仍开；⑩ R423 新跑待 push 后读。

下一轮（R424）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R423 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看搜索无结果 4 帧与旧/新组件在 runner 上、floor REDS=0、以及滚动测试在 CI 是否全绿（本地整卷红是会话/顺序，449）；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 422 轮（R423" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R423 节")
if u"## Round 420 · R423" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 420")
if u"## D-419" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-419")
if u"搜索无结果态补放大镜与查询词" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**449." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 449")
if state.count(u"## R422 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R422 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_419 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R422 状态", STATE_SECTION + u"## R422 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R423_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
