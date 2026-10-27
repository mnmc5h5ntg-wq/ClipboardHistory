#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R418 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 416 轮（R417 · 2026-10-27"
AUDIT_SECTION = u"""## 第 417 轮（R418 · 2026-10-27 · U-1513…U-1517）：菜单栏补暂停斜杠（12 图 892→1327 墨 +435；13+ 标签 286→425 Δ182）；R417 跑全步绿但胶片卷被 200s 看门狗收掉（suite-did-not-finish executed=0）⇒ 胶片 NOT-RUN；修套件预算与采样窗口（产品 2 文件，菜单栏状态位）

- **U-1513：⓪ `40429334110 ↔ a6fc65a` 的失败步骤与胶片命运。** 作业结论 **success**、21/21 步全绿，但 **Motion filmstrip 这一卷的裁决是 NOT-RUN**：`MOTION_FLOOR_FACTS judged=4/5 executed=0 not-run=notice-banner`、`MOTION_FLOOR_SKIPPED=suite-did-not-finish 看门狗收掉了进程 ⇒ 不能把「没跑完」判成「验得不够」`、`MOTION_FLOOR_REDS=0`。原文时间戳：胶片步 01:04:44 起、01:08:04 `Killed: 9` —— 200s 看门狗收掉（R416 同一卷 23:48:03→23:51:12 ≈ **189s**，只剩 11s 余量）。被杀前打印的 5 条红（回执 1 过渡帧 ×1x/2x、暂停 1 帧 ×2x、markdown 1 帧 ×1x/2x）**不是产品裁决**：套件没跑完、`executed=0`；`COPY_RECEIPT_FADE` 仍然**没有行** ⇒ 具名 NOT-RUN。**暂停 4 帧在 runner 上是绿的**：`PAUSE_BANNER_BAND light 静置橙=0 暂停变化=26250 暂停橙=112`、`dark 104`，`PAUSE_BANNER_DEFAULTS light 0/0→112`；回执 6 帧像素也仍绿（亮 0/0→2416/0、2724/187；暗 0/0→1738/0、1991/177）。修法（**门槛未动**）：① 撤掉暂停横幅的专用胶片卷（4 次 ContentView 录制）—— 状态已由 4 帧像素 + defaults 管线 + 源守卫钉住，过程由共享的 `notice-banner*` 臂作最近证人；② 把 R417 的"回执采样窗口"推广成**所有声明时长场景的自动下限**（预热间隔 < 1.2×声明/预算时按该下限拉开）：同一跑的 markdown 以 **0.3ms×30=9ms** 的窗口判 160ms，正是同一种病。本地修后：胶片套件 **183s**（不再贴 200s）、回执 2–4 个过渡帧/窗口 329–488ms、markdown 4–6 帧；`testSkeletonSweepIsOneBand` 在套件里偶发 1 次（可用帧 3/行程 12pt），单跑通过（5 可用帧/145.5pt），登记为采样偶发。
- **U-1514：② 菜单栏的暂停状态。** 主窗口有了暂停横幅，但菜单栏那颗 `clipboard` 仍是静态符号 —— 用户在菜单栏上看不出采集关了。新 `MenuBarStatusPresentation`（斜杠端点 3.2→14.8、线宽 1.6、无障碍文案「时间剪史，已暂停记录」）+ `MenuBarStatusLabel`（13+ 的 `MenuBarExtra` 标签闭包；`@AppStorage("recordingPaused")` + `pausedForCapture`；同一颗符号上叠斜杠）+ `makeStatusBarIcon(paused:)`（12 的模板图同一道斜杠）+ `UserDefaults.didChangeNotification` 订阅（12 的图标随开关重画）。真看图：13+ 标签亮/暗两态，静置是完整剪贴板、暂停多一道左上→右下斜杠且 glyph 仍在。读数：12 图 4× 墨像素 **892→1327（+435）**、包围盒仍不出 18×18、模板位两臂都在；13+ 标签 **286→425（Δ182）**（亮暗同）。新增 4 帧（`statusitem-label-idle/paused` 亮暗）、既有 **210 帧逐字节不变**、基线 **214/0/0/0**。**真菜单栏表面由系统合成，离屏拍不到** ⇒ 具名 NOT-RUN；可拍的是标签视图与 12 的素材图。
- **U-1515：判据与刀。** 判据：10 张 `MenuBarPopulationTests`（含新 `testPausedStatusImageAddsTheSlashAndKeepsTheGlyph`、`testMenuBarPauseLabelIsWiredToTheSharedKey`，每一格收窄到自己的函数体）+ 标签像素尺（静置 286、暂停 425、变化 182）+ 既有菜单表面身份/复刻守卫改认标签闭包形状。`M1096…M1102` **7/7 CAUGHT**、`RESTORE_CLEAN=yes`（M1096 斜杠不画 ⇒ 暂停墨=静置墨 892；M1097 暂停分支关掉 ⇒ 变化=0；M1098–M1101 源；M1102 退回静态符号）。**这次改动把两张旧表弄空**：R110 `M601` 的 `MenuBarExtra(systemImage:)` 调用点搬进标签视图 ⇒ 重钉到 `Image(systemName: MenuBarController.statusSymbolName)` 并整表重跑 **4/4 CAUGHT**；R111 `M602` 的 `.receive(on: .main)` 因暂停桥出现第二处而命中 2 次 ⇒ 针带上 `refreshBridge` 上下文并整表重跑 **4/4 CAUGHT**。预检 `tables=176 covered=158 arms=475 bad=0`、全仓 **269 文件 / 959 把**；`HIDDEN_ARMS 表=263 可判=893 rot=0`。
- **U-1516：③ 436 只读新跑。** `40429334110`：`MOTION_FLOOR_FACTS judged=4/5 executed=0 not-run=notice-banner`、`MOTION_FLOOR_SKIPPED=suite-did-not-finish`、`MOTION_FLOOR_REDS=0` —— **REDS=0 不等于绿**：套件被看门狗收掉，裁决是 NOT-RUN；`MOTION_FLOOR_UNLISTED` 没有行，`notice-banner` 是放行臂；未重猜 `must_judge`。下一跑必须 `executed>0` 才能读 436。
- **U-1517：① 367 rot 与八步。** `HIDDEN_ARMS 表=263 可判=893 rot=0`（R417 261/886，本轮 +2 表 +7 臂）；预检 `tables=176 covered=158 arms=475 bad=0`、`ARM_TOTAL files=269 arms=959 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`。build **0** 告警；全量 **1108/54/0**；捕获 **214 帧 / 127 条 / 4 skip / 0 失败**；基线 `UPDATED=214`、复验 `COMPARED=214 CHANGED=0 MISSING=0 ADDED=0`（既有 210 帧不变，新增菜单栏 4 帧）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 417，现读 `python3 scripts/product_streak.py --streak-for 417`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① R417 的胶片套件被 200s 看门狗收掉（`suite-did-not-finish`、`executed=0`）⇒ 回执/markdown 的裁决本跑无效，`COPY_RECEIPT_FADE` 无行；② 真菜单栏表面（系统合成）拍不到，只有标签视图与 12 素材图；③ 暂停横幅的专用胶片卷已撤（套件预算），过程由共享 `notice-banner*` 臂作最近证人；④ 12 的图标实时刷新没有 macOS 12 真机腿；⑤ runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行；⑥ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置内容帧能力闸门仍隐式（441）；⑨ 437/438/439/440/441/442/443/444 仍开；⑩ R418 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 415 · R418（第 417 轮 · 2026-10-27）：菜单栏补暂停斜杠（12 图 892→1327 墨 +435；13+ 标签 286→425 Δ182）；R417 跑全步绿但胶片卷被 200s 看门狗收掉 ⇒ 胶片 NOT-RUN；修套件预算与采样窗口（产品 2 文件，菜单栏状态位）

主窗口有了暂停横幅，菜单栏那颗 `clipboard` 仍是静态符号。新 `MenuBarStatusPresentation` + `MenuBarStatusLabel`（13+ 标签闭包：同一符号 + 暂停斜杠，读 `@AppStorage("recordingPaused")`）+ `makeStatusBarIcon(paused:)`（12 模板图同斜杠）+ defaults 订阅（12 随开关重画）。真看图亮/暗：静置完整剪贴板、暂停多一道斜杠且 glyph 仍在。12 图墨 892→1327（+435）、包围盒不出 18×18；13+ 标签 286→425（Δ182）。新增 4 帧、既有 210 帧不变、基线 214。M1096–M1102 7/7 CAUGHT；改形状弄空 R110 M601（重钉 4/4）、R111 M602（重钉 4/4）。R417 跑 21/21 步绿但胶片卷 200s 被收：`judged=4/5 executed=0 not-run=notice-banner`、`suite-did-not-finish`、`REDS=0` ⇒ NOT-RUN；暂停 4 帧在 runner 绿（0→26250 变化、112/104 橙）；回执像素绿，`COPY_RECEIPT_FADE` 无行。修：撤暂停胶片卷（状态已像素/源钉住）、把采样窗口推广为所有声明时长场景的自动下限（markdown 9ms 窗口同病）；本地套件 183s、回执 2–4 帧/窗口 329–488ms、markdown 4–6 帧。全量 1108/54/0；捕获 214/127/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162=162；HIDDEN 263/893 rot=0；预检 176/158/475；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看 13+ 标签亮/暗两态：静置完整剪贴板、暂停多一道斜杠且 glyph 仍在；12 图由 892→1327 的墨与包围盒量。 |
| 判据有效性 | 15/15 | 图像/像素/两段源守卫 + 既有表面身份/复刻守卫；M1096–M1102 7/7；两张旧表重钉后 4/4、4/4。 |
| 假绿防御 | 15/15 | M1096 斜杠不画=892；M1097 暂停分支关掉=0 变化；M1098–1101 源；M1102 退静态符号；既有 210 帧 0 变。 |
| 产品面推进 | 14/15 | 真落 Sources 2 文件、补的是菜单栏状态；扣 1：真菜单栏表面与 macOS 12 实时腿仍缺（443）。 |
| 台账一致性 | 15/15 | U-1513…U-1517、D-413、436 的 executed=0/suite-did-not-finish、R110/R111 重钉都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R417 胶片被杀读成 NOT-RUN 而不是绿；`REDS=0` 旁边写明 executed=0；撤暂停胶片卷与自动窗口都落账；门槛未动。 |
| 可复核性 | 15/15 | 两态墨量/四张帧、7 把新刀、两张旧表重跑、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_413 = u"""## D-413 菜单栏暂停状态用同一颗符号 + 一道斜杠，两棵表面共用记号（R418）

- 背景：主窗口已有暂停横幅，但菜单栏那颗 `clipboard` 是静态的；13+ 的 `MenuBarExtra(systemImage:)` 不允许按状态换图，12 的 `NSStatusItem` 也只在安装时画一次。
- 决定：`MenuBarStatusPresentation` 只写一次斜杠端点/线宽/无障碍文案；13+ 换成 `MenuBarExtra { … } label: { MenuBarStatusLabel() }`（同一颗 `statusSymbolName` 上叠斜杠，读 `@AppStorage("recordingPaused")`）；12 的 `makeStatusBarIcon(paused:)` 在同一张模板图上画同一道斜杠，安装时读当前状态，并订阅 `UserDefaults.didChangeNotification` 重画。
- 理由：暂停是同一颗图标的状态，不是另一个入口（R110 的"两棵表面同一个入口"继续成立）；换符号会让它在菜单栏里变成另一个 App。斜杠是原生"停用"记号，模板染色下亮暗都成立；两棵表面共用一个记号常量，避免下一次分叉。
- 兼容性/迁移：13+ 的入口形状从 `systemImage:` 换成标签闭包；符号常量仍只在一处声明，两个调用点引用它；既有帧不变，新增 4 帧。12 的实时刷新只在本机 13+ 之外，未跑真机腿（具名 NOT-RUN，见 443）。
- 回滚：删 `MenuBarStatusLabel`/`MenuBarStatusPresentation` 与 `makeStatusBarIcon(paused:)` 的暂停分支，把 `MenuBarExtra` 改回 `systemImage:` 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 菜单栏补暂停斜杠（12 图 892→1327 墨 +435；13+ 标签 286→425 Δ182）；R417 跑全步绿但胶片卷被 200s 看门狗收掉 ⇒ 胶片 NOT-RUN；修套件预算与采样窗口（R418 / 第 417 轮 / Round 415 / U-1513…U-1517 · 产品 2 文件，菜单栏状态位）

"""

BACKLOG_SECTION = u"""437 追记（R418 · 仍开）：本轮补的是菜单栏暂停状态与胶片套件的采样窗口/预算；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

443 追记（R418 · 仍开）：13+ 的标签视图与 12 的素材图已画出暂停斜杠；仍缺的是**真菜单栏表面**（系统合成，离屏拍不到）与 **macOS 12 的实时刷新真机腿**。下一步：给它一条具名的屏幕录制/在屏探针通道，拍不到就继续 NOT-RUN，不许拿标签视图冒充菜单栏。

**444. 胶片套件只剩约 11 秒预算：R416 跑 189s、R417 加了两个新场景就被 200s 看门狗收掉**（R418 读 `40429334110`）
    现象：`Motion filmstrip` 的看门狗是 `( sleep 200; kill -9 )`；R416 同一卷 23:48:03→23:51:12 ≈ 189s。R417 加了暂停横幅的 4 次 ContentView 录制 + 回执 8ms 间距后被杀在 200s，`MOTION_FLOOR_FACTS executed=0 not-run=notice-banner`、`suite-did-not-finish`。R418 已撤暂停胶片卷并把采样窗口改成按声明时长的自动下限，本地套件 183s。
    修法（下一轮）：不要先加看门狗时长；先给套件做一次**逐用例耗时账**，把最贵的几个整窗/ContentView 录制收窄或拆成第二个 CI 步；在预算回到 ≥30s 余量之前，新胶片场景一律先量本地套件总时长。
"""

STATE_SECTION = u"""## R418 状态（2026-10-27 · 本地 · 第 417 轮 / Round 415）：菜单栏补暂停斜杠（12 图 892→1327 墨 +435；13+ 标签 286→425 Δ182）；R417 跑全步绿但胶片卷被 200s 看门狗收掉 ⇒ 胶片 NOT-RUN；修套件预算与采样窗口（产品 2 文件，菜单栏状态位）

最后更新：2026-10-27（本地 · R418 / 第 417 轮 / Round 415）：主窗口有暂停横幅，但菜单栏那颗 `clipboard` 仍是静态符号。新 `MenuBarStatusPresentation`（斜杠端点 3.2→14.8、线宽 1.6、无障碍「时间剪史，已暂停记录」）+ `MenuBarStatusLabel`（13+ 标签闭包，同一符号叠斜杠，读 `@AppStorage("recordingPaused")`）+ `makeStatusBarIcon(paused:)`（12 模板图同斜杠）+ defaults 订阅（12 随开关重画）。真看图：13+ 亮/暗两态，静置完整剪贴板、暂停多一道斜杠且 glyph 仍在。读数：12 图 **892→1327（+435）**、包围盒不出 18×18；13+ 标签 **286→425（Δ182）**。新增 4 帧、既有 **210 帧逐字节不变**、基线 **214/0/0/0**。`M1096–M1102` **7/7 CAUGHT**；改入口形状弄空 R110 `M601` 与 R111 `M602`（与暂停桥重名），已重钉并整表重跑 **4/4、4/4 CAUGHT**。R417 run `40429334110 ↔ a6fc65a` **success（21/21 步）但胶片卷 NOT-RUN**：`MOTION_FLOOR_FACTS judged=4/5 executed=0 not-run=notice-banner`、`suite-did-not-finish`、`REDS=0`；R416 同卷 189s、R417 加场景后被 200s 看门狗收掉。**暂停 4 帧在 runner 上绿**（`PAUSE_BANNER_BAND` 亮 0→26250 变化/112 橙、暗 104 橙；defaults 0→112）；回执 6 帧像素绿（0/0→2416/0、2724/187；暗 1738/0、1991/177）；`COPY_RECEIPT_FADE` 无行。修：撤暂停胶片卷（状态已像素/源钉住）、把采样窗口推广为所有声明时长场景的自动下限（markdown 的 0.3ms×30=9ms 同病）；本地套件 **183s**、回执 2–4 帧/窗口 329–488ms、markdown 4–6 帧。全量 **1108/54/0**；捕获 **214/127/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 263/893 rot=0；预检 176/158/475 bad=0；产品面连续零改动 **1** 轮（as-of 417，现读 `python3 scripts/product_streak.py --streak-for 417`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R417 作业全步绿但胶片卷被 200s 看门狗收掉（executed=0）⇒ 胶片 NOT-RUN；暂停 4 帧绿、回执像素绿、COPY_RECEIPT_FADE 无行。
② 产品：菜单栏暂停斜杠（12 图 +435 墨；13+ 标签 Δ182），新增 4 帧、基线 214。
③ 判据：M1096–M1102 7/7；R110 M601 / R111 M602 重钉后 4/4、4/4；precheck 176/158/475；hidden rot 0。
④ 436：judged=4/5 executed=0 not-run=notice-banner、REDS=0 但 suite-did-not-finish ⇒ NOT-RUN；未重猜 must_judge。
⑤ 367：hidden 表 263 / 可判 893 / rot 0 / 上界 0；ARM 269 文件 / 959 把。
⑥ 全量 1108/54/0；捕获 214/127/4/0；换装 ok；清账 162=162；帧基线 214/0/0/0。

NOT-RUN / 阻塞（分开写）：① R417 胶片套件被 200s 看门狗收掉（suite-did-not-finish、executed=0），回执/markdown 本跑无效；② `COPY_RECEIPT_FADE` 无行；③ 真菜单栏表面系统合成拍不到；④ 暂停胶片卷已撤（过程由共享 notice-banner 臂作最近证人）；⑤ 12 的实时刷新没有 macOS 12 真机腿；⑥ runner 的 `REVEAL`/`INTAKE_READING` 无行；⑦ `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑧ `table-lazy-rows`；⑨ 设置能力闸门仍隐式（441）；⑩ 437–444 仍开；⑪ R418 新跑待 push 后读。

下一轮（R419）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R418 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看胶片套件是否 `executed>0`、回执 2–4 帧/窗口是否 ≥0.8×声明、markdown 是否 ≥2、菜单栏 4 帧是否绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 417 轮（R418" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R418 节")
if u"## Round 415 · R418" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 415")
if u"## D-413" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-413")
if u"菜单栏补暂停斜杠" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**444." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 444")
if state.count(u"## R417 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R417 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_413 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R417 状态", STATE_SECTION + u"## R417 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R418_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
