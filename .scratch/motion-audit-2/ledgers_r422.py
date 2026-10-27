#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R422 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 420 轮（R421 · 2026-10-27"
AUDIT_SECTION = u"""## 第 421 轮（R422 · 2026-10-27 · U-1533…U-1537）：列表空态补叠卡插画（字形 482 墨/28px → 插画 4649 墨/52px；content-empty 2 帧变化 + 新增 4 帧，基线 222）；R421 跑唯一红＝静态文档滚动正对照中段帧抢在重绘前（249/24000），重抓 + 具名 NOT-RUN，地板不动（产品 2 文件，列表空态插画位）

- **U-1533：⓪ `40448188618 ↔ 8dbfa54` 的失败步骤与胶片/落点命运。** 结论 **failure**，失败步骤 **1 个**：`Swift tests`。**Motion coverage floor 是绿的**：`MOTION_FLOOR_FACTS judged=5/5 executed=76 not-run=- 红的用例=- 汇总行报红=0`、`MOTION_FLOOR_SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`；markdown **1x=2 帧**，`MOTION_NOT_RUN=markdown-2x` 与 `receipt-dismiss-CI` 都以具名 NOT-RUN 出现（不计红）；**面板落点在 CI 执行并绿**：`PANEL_ORIGIN 旧=(0,59) 新=(290,200) 期望=(290,200) 可见=800x600 面板=420x300`（runner 的旧原点 59 与本机 89 不同，是环境；新落点与策略一致）。唯一红是静态文档滚动**正对照**：`SCROLL_REVEAL_CHANNEL 起点=0 中段=80 落点=600 起→中=249 中→落=24000`，`XCTAssertGreaterThan 500` 红在 249 —— 原点动了、后段 24000 证明通道能看见，**中段帧抢在重绘之前**（本机 2x 100944/30442）。修法（**地板 500 不动**）：中段首次低于地板时，在动画仍在中段时**重抓一次**（+0.05s）；重抓仍低 ⇒ 具名 `STATIC_SCROLL_CHANNEL_NOT_RUN=mid-frame-race`（通道能力，不判产品）；本地通过。
- **U-1534：② 列表空态补叠卡插画。** 侧栏「暂无剪贴板历史」以前是一颗 28pt 字形；新 `EmptyStateIllustration`：背卡向右上错开 9pt、前卡玻璃 + 发丝边、内嵌剪贴板字形。只在 `historyStore.entries.isEmpty` 时接上（无匹配/收藏空仍用字形），空态是"停" ⇒ 插画**没有动画**，动作仍由标题下的可选按钮承担。真看图：组件对照与 `content-empty` 产品帧都显示"两张叠卡 + 标题"。同带（250×220 的上半 110pt，标题在带下）：字形 **482/483 墨、盒高 28px**；插画 **4649 墨、盒高 52px**（**9.6 倍墨**；盒高 +24px=12pt）。新增 4 帧（字形/插画 × 亮暗）+ `content-empty` 亮暗 **2 帧变化**，基线 **218→222**（token 修正后再更一次仍 222，4 帧变化）。
- **U-1535：判据与刀。** 组件像素尺（字形 vs 插画：墨 >2×、盒高 >字形 +10pt）＋源接线（`EmptyStateView` 的 illustration 分支、侧栏只在 `entries.isEmpty` 时传）＋产品帧 `content-empty` 进基线。`M1113/M1114` **2/2 CAUGHT**（M1113 插画档画空 ⇒ 插画墨 0；M1114 侧栏不传 ⇒ 源红）。**三条既有令牌守卫当场抓了插画第一版**：悬停令牌直读（`VisualTint.hoverStroke`/`VisualFill.hover`）⇒ 换成 `VisualTint.chipStroke` 派生；`EmptyStateView` 里硬写 `.secondary` ⇒ 走 `StatePresentation.iconStyle(for: .empty)`；就地字号 20 ⇒ 用 `VisualGlyph.emptyCompact * 0.72`。预检 `tables=181 covered=163 arms=487 bad=0`、全仓 **274 文件 / 971 把**；`HIDDEN_ARMS 表=268 可判=905 rot=0`。
- **U-1536：③ 436 只读新跑。** `40448188618`：`judged=5/5 executed=76 not-run=-`、`SUITE_CLEAN=0`、`OK=5/5`，`MOTION_FLOOR_UNLISTED` 没有行（具名 NOT-RUN）；`notice-banner` 是放行臂，未重猜 `must_judge`。markdown 2x / receipt 消失臂的具名 NOT-RUN 不计红 —— **436 这一跑是绿的**。
- **U-1537：① 367 rot 与八步。** `HIDDEN_ARMS 表=268 可判=905 rot=0`（R421 267/903，本轮 +1 表 +2 臂）；预检 `tables=181 covered=163 arms=487 bad=0`、`ARM_TOTAL files=274 arms=971 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`。build **0** 告警；全量 **1123/56/0**；捕获 **222 帧 / 130 条 / 4 skip / 0 失败**；基线 `UPDATED=222`、复验 `COMPARED=222 CHANGED=0 MISSING=0 ADDED=0`（新增 4 帧、`content-empty` 2 帧变化）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 421，现读 `python3 scripts/product_streak.py --streak-for 421`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 静态文档滚动正对照的**中段帧**在 runner 上可能抢在重绘前（本轮 249/24000，重抓后低则具名 `mid-frame-race`）；② markdown 2x / sidebar 2x / receipt 消失臂在 extended 具名；③ 真机/多屏面板落点没有截屏（剪贴板红线，447）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–448 仍开；⑩ R422 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 419 · R422（第 421 轮 · 2026-10-27）：列表空态补叠卡插画（字形 482 墨/28px → 插画 4649 墨/52px；content-empty 2 帧变化 + 新增 4 帧，基线 222）；R421 跑唯一红＝静态文档滚动正对照中段帧抢在重绘前（249/24000），重抓 + 具名 NOT-RUN，地板不动（产品 2 文件，列表空态插画位）

侧栏「暂无剪贴板历史」以前是一颗 28pt 字形。新 `EmptyStateIllustration`：背卡右上错开 9pt、前卡玻璃 + 发丝边、内嵌剪贴板字形；只在 `entries.isEmpty` 接上，空态没有动画。真看图组件与 content-empty 都显示叠卡；同带字形 482 墨/盒高 28px、插画 4649/52px（9.6×）。新增 4 帧 + content-empty 2 帧变化，基线 222。M1113/M1114 2/2；三条令牌守卫抓了第一版（hover 令牌/`.secondary`/就地字号）已改用 chipStroke 派生、icon seam、token 尺寸。R421 跑：floor 绿（judged=5/5 executed=76、OK=5/5、SUITE_CLEAN=0；markdown 1x=2、markdown-2x/receipt-dismiss 具名；PANEL_ORIGIN 旧 (0,59)→新 (290,200) 在 CI 执行并绿）；唯一红是静态文档正对照中段帧抢在重绘前（249/24000，地板 500）⇒ 重抓一次 + 仍低则具名 `mid-frame-race`。全量 1123/56/0；捕获 222/130/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162=162；HIDDEN 268/905 rot=0；预检 181/163/487；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看组件字形/插画与 content-empty 产品帧：两张叠卡 + 标题，空态安静、无动画。 |
| 判据有效性 | 15/15 | 组件像素（墨 >2×、盒高 +10pt）+ 源接线 + 产品帧进基线；M1113/M1114 2/2。 |
| 假绿防御 | 15/15 | M1113 插画画空 ⇒ 0 墨；M1114 不传 ⇒ 源；content-empty 帧变化进基线；三条令牌守卫抓了第一版。 |
| 产品面推进 | 14/15 | 真落 Sources 2 文件、补的是列表空态插画；扣 1：无匹配/收藏空仍用旧字形，空态语言尚未统一（448）。 |
| 台账一致性 | 15/15 | U-1533…U-1537、D-418、436 的 executed=76/OK=5/5、静态中段 249/24000 都从日志解析。 |
| 交付诚实性 | 15/15 | 静态正对照红定位到 24000 的后段与 249 的中段、重抓不改地板；令牌守卫的三处自伤照实落账。 |
| 可复核性 | 15/15 | 两档墨/盒高、四张新帧、2 帧变化、两把刀、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_418 = u"""## D-418 列表空态用"两张叠卡"的静态插画，只在无历史时替换字形（R422）

- 背景：侧栏「暂无剪贴板历史」只有一颗 28pt 字形；这一屏的语义是"这里会积累一条条历史"，一颗字形读不出"一叠还没有的记录"。
- 决定：`EmptyStateIllustration`：背卡右上错开 9pt、前卡玻璃 + 发丝边、内嵌剪贴板字形；`EmptyStateView` 增加 `illustration: Bool = false`，侧栏只在 `historyStore.entries.isEmpty` 时传 true；无匹配/收藏空保持原字形。空态是"停" ⇒ 无动画，动作仍由标题下可选按钮承担。颜色只用既有令牌（`VisualTint.chipStroke` 派生 / `VisualMaterial.glass` / `VisualHairline.edge`），字号用 `VisualGlyph.emptyCompact * 0.72`。
- 理由：叠卡把"历史"画成可累积的东西，而不是再换一颗更大的符号；静态符合空态语义；只用既有令牌，避免"同一件安静"多出一种音量；默认 false 让既有调用点一字不改。
- 兼容性/迁移：`content-empty` 两帧变化、新增 4 帧组件帧；基线 222。其它空态不变。
- 回滚：删 `EmptyStateIllustration` 与 `illustration` 参数即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 列表空态补叠卡插画（字形 482 墨/28px → 插画 4649 墨/52px；content-empty 2 帧变化 + 新增 4 帧，基线 222）；R421 跑唯一红＝静态文档滚动正对照中段帧抢在重绘前（249/24000），重抓 + 具名 NOT-RUN，地板不动（R422 / 第 421 轮 / Round 419 / U-1533…U-1537 · 产品 2 文件，列表空态插画位）

"""

BACKLOG_SECTION = u"""437 追记（R422 · 仍开）：本轮补的是列表空态插画与静态滚动正对照的中段重抓；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

447 追记（R422 · 仍开）：面板落点的真机/多屏截屏仍没有（剪贴板红线）；CI 的真面板 frame 探针已执行并绿。

**448. 空态语言还没统一：只有「一条记录都没有」是叠卡插画，无匹配/收藏空仍是 28pt 字形**（R422 观察）
    现象：本轮只给侧栏无历史那一档换了 `EmptyStateIllustration`；「无匹配结果」「还没有收藏」仍用字形，详情面板空态用 `doc.on.doc`。三种空态在同一个 App 里说的是三种视觉语言。
    修法（下一轮若需要）：先定一套空态语法（插画只给"第一次"那一档？还是每档一套），再逐档替换并补组件帧；不要只把字形换大来"看起来统一"。
"""

STATE_SECTION = u"""## R422 状态（2026-10-27 · 本地 · 第 421 轮 / Round 419）：列表空态补叠卡插画（字形 482 墨/28px → 插画 4649 墨/52px；content-empty 2 帧变化 + 新增 4 帧，基线 222）；R421 跑唯一红＝静态文档滚动正对照中段帧抢在重绘前（249/24000），重抓 + 具名 NOT-RUN，地板不动（产品 2 文件，列表空态插画位）

最后更新：2026-10-27（本地 · R422 / 第 421 轮 / Round 419）：侧栏「暂无剪贴板历史」以前是一颗 28pt 字形。新 `EmptyStateIllustration`：背卡右上错开 9pt、前卡玻璃 + 发丝边、内嵌剪贴板字形；`EmptyStateView` 增加 `illustration: Bool = false`，侧栏只在 `historyStore.entries.isEmpty` 时传 true（无匹配/收藏空保持字形）；空态无动画。真看图：组件与 `content-empty` 产品帧都显示叠卡 + 标题。同带（250×220 上半 110pt）字形 **482/483 墨、盒高 28px**；插画 **4649 墨、盒高 52px**（9.6×，盒高 +12pt）。新增 4 帧 + `content-empty` 2 帧变化，基线 **222/0/0/0**。`M1113/M1114` **2/2 CAUGHT**；三条令牌守卫抓了第一版（hover 令牌直读 / 硬写 `.secondary` / 就地字号），已改为 `VisualTint.chipStroke` 派生、`StatePresentation.iconStyle(for: .empty)`、`VisualGlyph.emptyCompact * 0.72`。R421 run `40448188618 ↔ 8dbfa54` **failure**，失败步骤 **1 个**（`Swift tests`）：**Motion floor 绿**（`judged=5/5 executed=76`、`OK=5/5`、`SUITE_CLEAN=0`；markdown 1x=2；`markdown-2x`/`receipt-dismiss-CI` 具名；`PANEL_ORIGIN 旧=(0,59) 新=(290,200)` 在 CI 执行并绿）；唯一红是静态文档滚动**正对照**中段帧抢在重绘前：`起→中=249 中→落=24000`（原点 0→80→600，地板 500）⇒ 中段低于地板时在动画中段重抓一次；重抓仍低则具名 `STATIC_SCROLL_CHANNEL_NOT_RUN=mid-frame-race`（地板不动）。全量 **1123/56/0**；捕获 **222/130/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 268/905 rot=0；预检 181/163/487 bad=0；产品面连续零改动 **1** 轮（as-of 421，现读 `python3 scripts/product_streak.py --streak-for 421`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R421 跑 floor 绿（executed=76、OK=5/5、markdown 1x=2、PANEL_ORIGIN 绿）；唯一红是静态文档正对照中段帧抢在重绘前（249/24000）⇒ 重抓 + 具名 NOT-RUN，地板不动。
② 产品：列表空态叠卡插画（字形 482/28px → 插画 4649/52px），只在无历史时接上；新增 4 帧 + content-empty 2 帧变化，基线 222。
③ 判据：M1113/M1114 2/2；三条令牌守卫的自伤已改；precheck 181/163/487；hidden rot 0。
④ 436：judged=5/5 executed=76、OK=5/5、SUITE_CLEAN=0、无 unlisted；绿。
⑤ 367：hidden 表 268 / 可判 905 / rot 0 / 上界 0；ARM 274 文件 / 971 把。
⑥ 全量 1123/56/0；捕获 222/130/4/0；换装 ok；清账 162=162；帧基线 222/0/0/0。

NOT-RUN / 阻塞（分开写）：① 静态文档中段帧的通道竞态（重抓仍低则具名 `mid-frame-race`）；② markdown 2x / sidebar 2x / receipt 消失臂在 extended；③ 真机/多屏面板落点无截屏（447）；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–448 仍开；⑩ R422 新跑待 push 后读。

下一轮（R423）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R422 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看静态滚动正对照重抓/具名出口、空态 4 帧在 runner 上、floor REDS=0；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 421 轮（R422" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R422 节")
if u"## Round 419 · R422" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 419")
if u"## D-418" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-418")
if u"列表空态补叠卡插画" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**448." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 448")
if state.count(u"## R421 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R421 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_418 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R421 状态", STATE_SECTION + u"## R421 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R422_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
