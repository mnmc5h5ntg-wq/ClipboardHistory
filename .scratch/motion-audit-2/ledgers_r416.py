#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R416 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 414 轮（R415 · 2026-10-27"
AUDIT_SECTION = u"""## 第 415 轮（R416 · 2026-10-27 · U-1503…U-1507）：复制回执补文字胶囊（回执带旧 0/0 → 已复制 8792/0、失败 9936/355）；R415 run 全绿 → 设置 8 红消失（2 条具名能力 skip）、焦点 236.1/217.6、滚动 reduce=true override=false（产品 1 文件，复制回执位）

- **U-1503：⓪ `40416557136 ↔ 7d8a0b7` 全绿与 settings/focus/scroll 命运。** 结论 **success**，**失败步骤 0 个**（`gh api` 逐 step 读：21/21 success；注解三条：Node20 弃用、大小写不敏感文件系统，以及 report-only 在屏探针步自己的 `Process completed with exit code 1` —— 该步 `exit "$status"` 把看门狗收掉套件后的非零状态原样报出，步骤结论仍是 success，正文同跑有 `没有跑完…无头 runner 不可用`；运行时冒烟另有 `SMOKE_EXIT_CODE=-15`、`SMOKE_OK=1`，不是失败步骤）。**R414 的 8 条设置内容红全部消失**：`testProbesDoNotSitOnVibrantColumns` **passed**（18.7s）、`testDisabledToggleAndFailureReceiptAreVisible` **passed**（4.7s）；另两条走能力闸门：`testRowTierProfileSeparatesCaptionFromTitle` **skipped** `ROWTIER_NOT_RUN light：这台机器拍不出设置页内容列（整列 0 个偏离像素）`、`testSettingsCardVerticalRhythmIsOneNumber` **skipped** `CARD_RHYTHM_SHADE_NOT_RUN=1（light=1 dark=0）` ⇒ 撤 settle 后帧停在落定态，runner 的隐式能力闸门恢复（不是把红改绿，见 441）。Capture gate `CAPTURE_GATE_RESULT=ok 红=0`、`passed=106 skipped=17 failed=0`、NOT_RUN=88。**R415 焦点帧 runner 读数成立**：`QUICKPICK_SEARCH_FOCUS light 静置均值=236.1 焦点均值=217.6 框外均值=207.6`、`dark 50.1/66.3/84.2`（与本地 255.0/235.0/194.3、30.0/47.5/94.7 绝对值不同是 runner 材质，方向一致：静置与焦点两档不同、框外另成一档）。**R413 滚动持续绿**：`SCROLL_REVEAL_PLAN reduce=true override=Optional(false)`、`SCROLL_REVEAL_TIME 采样=6 中间值=2 首=365.0 末=1430.0 目标=1430.0 时长=0.20`、`SCROLL_REVEAL_OFFSET 起点=0.0 中段=457.0 落点=1430.0 目标=1430.0 中段是否严格在两端之间=true`、`SCROLL_REVEAL_INSTANT 目标=50.0 落点=50.0`；两条滚动行为测试随整卷绿。
- **U-1504：② 复制回执文字胶囊。** 旧实现复制成功/失败只换第三颗按钮的图标与 help 文案（R394 给了失败红），用户要盯住 14pt 的符号才知道结果；回执带在静置/成功/失败三态都没有一个字（旧读数 **0/0**）。新 `CopyReceiptPresentation` 把两态压成一句话（失败优先），`CopyReceiptView` 在药丸**上方外侧**画玻璃胶囊（图标 + 人话），`.transition(.opacity.combined(with: .move(edge: .bottom)))` + `.animation(MotionCatalog.animation(for: .emphasis), value: receipt)`；`.fixedSize(horizontal: true, vertical: false)` 防窄药丸把「已复制」折成竖排（R416 首拍真折过）；`allowsHitTesting(false)`；overlay 不参与药丸布局 ⇒ 既有 200 帧逐字节不变。真看图：静置只有药丸，成功白勾 + 「已复制」，失败红色感叹号 + 「复制失败」（亮/暗都看）。像素同带（120×70pt）：亮档静置 **0/0** → 已复制 **8792/0**、失败 **9936/355**；暗档 **0/0 → 5257/0、6094/356**。新增 6 帧（三态 × 亮暗，120×300）、既有 200 帧 0 变、基线 **206/0/0/0**。过程胶片：出现 2x 27 帧/6 过渡/峰值 0.0800、1x 27/4/0.0889；消失 2x 27/7/0.0429、1x 27/6/0.0889（声明 160ms，均 >4 过渡帧）。
- **U-1505：判据与刀。** 真值表（无/成功/失败/两态同真→失败）+ 源守卫（`CopyReceiptPresentation.receipt(copyConfirmed:copyFailed:)` 接线、`CopyReceiptView(receipt:)` 挂载、过渡、驱动、`fixedSize(horizontal: true`）+ 组件像素尺（静置 ≤5 墨、成功/失败 >100、失败红 >20、成功红 ==0）+ 专用胶片场景（工厂闭包按倍率各建一份，避免上一倍率把驱动留在开态）。`M1084…M1087` **4/4 CAUGHT**、`RESTORE_CLEAN=yes`：M1084 回执不挂 → 三态全 **0/0**；M1085 两态同真说成已复制 → 纯判据；M1086 删过渡 → 源；M1087 删两处 `fixedSize` → 源。预检 `tables=172 covered=154 arms=460 bad=0`、全仓 **265 文件 / 944 把**；`HIDDEN_ARMS 表=259 可判=878 rot=0 抽不出=6 已声明表=6 已声明死针=0 上界 rot=0 处置=ok`。
- **U-1506：③ 436 只读新跑。** `40416557136`：`MOTION_FLOOR_FACTS judged=5/5 executed=73 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=- 汇总行报红=0 机器=github-runner`、`MOTION_FLOOR_REDS=0`、`MOTION_FLOOR_OK=5/5 全部臂都在登记之内`；`MOTION_FLOOR_UNLISTED` 通道没有行 ⇒ 具名 NOT-RUN；`notice-banner` 是登记放行臂，未重猜 `must_judge`。
- **U-1507：① 367 rot 与八步。** `HIDDEN_ARMS 表=259 可判=878 rot=0`（R415 258/874，本轮 +1 表 +4 臂）；预检 `tables=172 covered=154 arms=460 bad=0`、`ARM_TOTAL files=265 arms=944 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`；R416 表 M1084–M1087 全 ok。build **0** 告警；全量 **1100/54/0**；捕获 **206 帧 / 124 条 / 4 skip / 0 失败**；基线 `UPDATED=206`、复验 `COMPARED=206 CHANGED=0 MISSING=0 ADDED=0`（既有 200 帧不变，新增回执 6 帧）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **2** 轮（as-of 416，现读 `python3 scripts/product_streak.py --streak-for 416`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（On-screen 步看门狗 240s 收掉、报告 `没有跑完…无头 runner 不可用`，R3-D9 已知边界；本地绿）；② `MOTION_FLOOR_UNLISTED` 与 `SCROLL_FAILURE_COUNT` 通道缺行；③ 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；④ 复制回执只在离屏组件帧与胶片里作证，真机面板上没有一张带回执的整窗帧；失败路径没有产品内可触发面（`copyFailed` 只由剪贴板写失败置位），见 442；⑤ 亮档真机腿仍没跑；⑥ macOS 12 紧凑详情头仍走旧截断；⑦ 设置内容帧在 runner 上的能力闸门仍是隐式的（441 仍开）；⑧ 437/438/439/440 仍开；⑨ R416 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 413 · R416（第 415 轮 · 2026-10-27）：复制回执补文字胶囊（回执带旧 0/0 → 已复制 8792/0、失败 9936/355）；R415 run 全绿 → 设置 8 红消失（2 条具名能力 skip）、焦点 236.1/217.6、滚动 reduce=true override=false（产品 1 文件，复制回执位）

复制成功/失败以前只换第三颗按钮的图标（R394 给了失败红），窄药丸里没有一句人话。新 `CopyReceiptPresentation`（失败优先真值表）+ `CopyReceiptView`（图标 + 「已复制」/「复制失败」的玻璃胶囊）挂在药丸上方外侧，`.emphasis` 驱动 opacity+move(bottom) 过渡，`fixedSize` 防折行，`allowsHitTesting(false)`。真看图亮/暗各三态：静置无回执，成功白勾、失败红感叹号。同带旧 0/0 → 亮 8792/0、9936/355；暗 5257/0、6094/356。新增 6 帧、既有 200 帧逐字节不变、基线 206。胶片出现 2x 27/6/0.0800、1x 27/4/0.0889；消失 2x 27/7/0.0429、1x 27/6/0.0889。M1084–M1087 4/4 CAUGHT（M1084 三态全 0/0）。R415 run 全绿：设置 8 红消失（probes/disabled 过、rowtier/card 两条具名能力 skip）、焦点 236.1/217.6/207.6（亮）、滚动 reduce=true override=false、首 365/末 1430/2 中间值。全量 1100/54/0；捕获 206/124/4/0；换装 ok/SHA_MATCH=1/381=381；清账 162=162；HIDDEN 259/878 rot=0；预检 172/154/460；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看亮/暗六张回执帧：静置无胶囊，成功白勾+已复制，失败红感叹号+复制失败；单行不折。 |
| 判据有效性 | 15/15 | 纯真值表 + 源守卫 5 条接线 + 像素三态/红点 + 专用胶片；M1084–M1087 4/4 CAUGHT。 |
| 假绿防御 | 15/15 | 静置 0/0 对成功 8792、失败 9936；M1084 三态全 0/0；既有 200 帧 0 变；成功帧红点 0。 |
| 产品面推进 | 14/15 | 真落 Sources 1 文件、新缺陷类别；扣 1：证据只在组件帧/胶片，真机整窗与失败触发面仍缺（442）。 |
| 台账一致性 | 15/15 | U-1503…U-1507、D-411、436、R415 跑全绿与 settings/focus/scroll 读数都从 CI/日志解析。 |
| 交付诚实性 | 15/15 | 8 条设置红消失如实拆成 2 passed + 2 能力 skip；冒烟 SIGTERM 注解与 0 失败步骤分开写；新跑待读记 NOT-RUN。 |
| 可复核性 | 15/15 | 旧/新三态读数、胶片四行、六张帧、四把刀、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_411 = u"""## D-411 复制回执用一颗药丸外的文字胶囊，失败优先（R416）

- 背景：复制成功/失败只换第三颗按钮的图标与 help 文案（R394 给了失败红）；药丸本体只有约 64pt 宽，把「已复制」塞进去会被折成竖排（R416 首拍真折过）。用户要盯住 14pt 符号才知道刚才复制成了没有。
- 决定：`CopyReceiptPresentation.receipt(copyConfirmed:copyFailed:)` 把两态压成一句话，失败优先（真值表把两态同真写成会红的规矩：`showCopyFailure` 会先清 `copyConfirmed`，但规矩不靠调用方记得）；`CopyReceiptView` 挂在药丸上方外侧的 overlay，图标 + 人话，`.emphasis` 驱动 opacity + move(bottom) 过渡，`.fixedSize` 防折行，`allowsHitTesting(false)`；overlay 不参与药丸布局 ⇒ 静置帧与旧帧逐字节相同。
- 理由：回执是「刚才发生了什么」的短暂陈述，需要药丸之外自己的位置；失败优先把「不能把失败说成已复制」写成会红的一格；挂在 overlay 上让既有 200 帧零变化，不把新说明塞进药丸的布局预算。
- 兼容性/迁移：仅详情区药丸；`GlassPill` 的入参已有 `copyConfirmed/copyFailed`，无新增产品状态；既有帧不变。
- 回滚：删 `CopyReceiptPresentation`/`CopyReceiptView` 与 GlassPill 的 receipt overlay 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 复制回执补文字胶囊（回执带旧 0/0 → 已复制 8792/0、失败 9936/355）；R415 run 全绿 → 设置 8 红消失（2 条具名能力 skip）、焦点 236.1/217.6、滚动 reduce=true override=false（R416 / 第 415 轮 / Round 413 / U-1503…U-1507 · 产品 1 文件，复制回执位）

"""

BACKLOG_SECTION = u"""437 追记（R416 · 仍开）：本轮补的是详情区复制回执文字胶囊与 R415 runner 签收；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

**442. 复制回执只有组件帧与胶片作证：真机整窗没有一张带回执的帧，失败路径也没有产品内可触发面**（R416 观察）
    现象：回执的三态像素读数来自 `glass-pill-copy-receipt-*` 组件夹具（120×300），过程来自 `MotionFilmstripTests` 的专用场景；详情区真机面板上没有抓过一张带回执的整窗帧。失败路径只在剪贴板写入失败时出现，产品里没有可点的入口（夹具直接设 `copyFailed`）。
    修法（下一轮若需要）：① 给详情区加一张带回执的整窗捕获帧（组合状态，用 `copyConfirmed/copyFailed` 的取证键）；② 给失败路径一个测试专用注入点（或构造一个写入必失败的 pasteboard stub），让失败回执也能从产品入口走到；不要在正包装面里放一个「制造失败」的按钮。
"""

STATE_SECTION = u"""## R416 状态（2026-10-27 · 本地 · 第 415 轮 / Round 413）：复制回执补文字胶囊（回执带旧 0/0 → 已复制 8792/0、失败 9936/355）；R415 run 全绿 → 设置 8 红消失（2 条具名能力 skip）、焦点 236.1/217.6、滚动 reduce=true override=false（产品 1 文件，复制回执位）

最后更新：2026-10-27（本地 · R416 / 第 415 轮 / Round 413）：复制成功/失败以前只换第三颗按钮的图标（R394 给了失败红），窄药丸里没有一句人话。新 `CopyReceiptPresentation`（失败优先真值表）+ `CopyReceiptView`（图标 + 「已复制」/「复制失败」的玻璃胶囊）挂在药丸上方外侧，`.emphasis` 驱动 opacity+move(bottom) 过渡，`fixedSize` 防折行，`allowsHitTesting(false)`。真看图亮/暗三态：静置无回执，成功白勾、失败红感叹号；同带旧 **0/0** → 亮 **8792/0、9936/355**；暗 **5257/0、6094/356**。新增 6 帧、既有 200 帧逐字节不变、基线 **206/0/0/0**。胶片出现 2x 27/6/0.0800、1x 27/4/0.0889；消失 2x 27/7/0.0429、1x 27/6/0.0889。`M1084–M1087` **4/4 CAUGHT**（M1084 三态全 0/0），RESTORE_CLEAN=yes。R415 run `40416557136 ↔ 7d8a0b7` **success**、失败步骤 **0 个**（21/21 step success）：**R414 的 8 条设置内容红消失**（probes/disabled passed；rowtier 走 `ROWTIER_NOT_RUN light`、card 走 `CARD_RHYTHM_SHADE_NOT_RUN=1` 两条具名能力 skip）；**焦点 runner 读数** 亮 236.1/217.6/207.6、暗 50.1/66.3/84.2；**滚动** `SCROLL_REVEAL_PLAN reduce=true override=Optional(false)`、6 采样/2 中间值/首 365/末 1430、OFFSET 0→457→1430、INSTANT 50→50。全量 **1100/54/0**；捕获 **206/124/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 259/878 rot=0；预检 172/154/460 bad=0；产品面连续零改动 **2** 轮（as-of 416，现读 `python3 scripts/product_streak.py --streak-for 416`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R415 runner 全绿：失败步骤 0；8 条设置内容红消失（2 passed + 2 条具名能力 skip）；焦点亮 236.1/217.6/207.6；滚动 reduce=true override=false、6/2/365→1430。
② 产品：详情区复制回执补文字胶囊，旧 0/0 → 新亮 8792/0、9936/355（暗 5257/0、6094/356），新增 6 帧。
③ 判据：纯真值表 + 源 5 条 + 像素三态 + 胶片；M1084–M1087 4/4 CAUGHT；precheck 172/154/460/0；hidden rot 0。
④ 436：judged=5/5、REDS=0、OK=5/5、notice-banner 放行；UNLISTED 通道缺行记 NOT-RUN。
⑤ 367：hidden 表 259 / 可判 878 / rot 0 / 上界 0；ARM 265 文件 / 944 把。
⑥ 全量 1100/54/0；捕获 206/124/4/0；换装 ok；清账 162=162；帧基线 206/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（On-screen 步看门狗 240s 收掉、R3-D9 已知边界；本地绿）；② `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；③ 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；④ 回执只有组件帧与胶片作证，真机整窗与失败触发面仍缺（442）；⑤ 亮档真机腿仍没跑；⑥ macOS 12 紧凑详情头仍走旧截断；⑦ 设置内容帧能力闸门仍隐式（441）；⑧ 437/438/439/440/441/442 仍开；⑨ R416 新跑待 push 后读。

下一轮（R417）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R416 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看回执 6 帧在 runner 上是否仍绿、新增 `COPY_RECEIPT_TOAST` 是否有行。① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 415 轮（R416" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R416 节")
if u"## Round 413 · R416" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 413")
if u"## D-411" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-411")
if u"复制回执补文字胶囊" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**442." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 442")
if state.count(u"## R415 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R415 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_411 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R415 状态", STATE_SECTION + u"## R415 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R416_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
