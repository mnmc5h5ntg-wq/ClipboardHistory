#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R417 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 415 轮（R416 · 2026-10-27"
AUDIT_SECTION = u"""## 第 416 轮（R417 · 2026-10-27 · U-1508…U-1512）：暂停采集状态补主窗口横幅（横幅带旧 0 橙 → 新 434/386 橙；整窗带变化 141864/141880）；R416 run 唯一红是回执胶片采样窗口（30 帧×1.7ms=41ms < 声明 160ms），只修采样不改门槛（产品 4 文件，暂停状态横幅位）

- **U-1508：⓪ `40420998525 ↔ a51de8d` 的失败步骤与回执命运。** 结论 **failure**，失败步骤 **1 个**：`Motion coverage floor`（Swift tests / Capture gate 等其余步骤全绿）。原文只有一条测试红：`testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 在 **1x 与 2x 都读到 1 个过渡帧（要 ≥2）**（`XCTAssertGreaterThanOrEqual failed: ("1") is less than ("2")`）。**回执 6 帧在 runner 上是绿的**：`COPY_RECEIPT_TOAST light 静置=0/0 已复制=2416/0 失败=2724/187`、`dark 0/0 → 1738/0、1991/177`（同样四行来自 capture 与 Swift tests 两步）。**定位到值**：`MOTION_GRAB glass-pill-copy-receipt-appear 帧数=30 抓帧中位=1.7ms 声明=160ms` ⇒ 30 帧预算在触发后 **≈41ms** 就用完，而这条过渡声明 **160ms** —— 卷子没覆盖到过程，1 帧不是硬切。`COPY_RECEIPT_FADE` 这一跑在 runner 上**没有行**（stdout 通道丢失，断言只在 stderr 里）⇒ 具名 NOT-RUN，不写成绿。修法（**一个门槛都没动**）：`Scenario` 增 `minimumSampleSpacingMilliseconds`（只回执场景设 8ms），触发后按该下限拉开采样；胶片打印 `窗口=NNms` 并前置断言窗口 ≥ 0.8×声明时长。本地修后：出现 2x 27 帧/4 过渡/峰值 0.0971/窗口 484ms、1x 27/3/0.0889/472ms；消失 2x 27/3/0.0829/339ms、1x 27/2/0.0833/321ms。判据仍是 ≥2。
- **U-1509：② 暂停采集状态的主窗口横幅。** `recordingPaused` 以前只在设置页那颗开关上可见：主窗口里复制进不来，界面一句话都不说。新 `StatePresentation.Kind.paused`（`pause.circle.fill`、prominent 墨、橙色图标与 12% 底、动作默认「继续记录」）+ `NoticeTone.paused`；`ContentView` 用 `@AppStorage("recordingPaused")`（与设置页/采集侧同一把钥匙）画第六条横幅，`noticeSignature` 加 `bits |= 32` 驱动 `bannerIn/bannerOut`，动作把开关关回去；取证键 `pausedForCapture`（产品默认 nil）。真看图：亮/暗整窗帧里琥珀带、橙色暂停图标、一句人话与「继续记录」都完好。像素同带（750×560，带宽 750、y=48..96pt）：静置 **0 橙** → 暂停 **434 橙**（亮）/ **386 橙**（暗），整带变化 141864/141880；`@AppStorage` 产品入口那一条（不写取证键、只拨 defaults）读到 **0 → 434**。新增 4 帧（`content-paused-idle/paused` × 亮暗），既有 **206 帧逐字节不变**，基线 **210/0/0/0**。过程胶片：出现 2x 27/5/0.5822/窗口 523ms、1x 27/5/0.5780/444ms；消失 2x 27/5/0.6550/568ms、1x 27/7/0.3539/476ms（声明 150/120ms）。
- **U-1510：判据与刀。** 纯判据（`.paused` 的图标/墨档/动作/`NoticeTone` 映射）+ 源守卫（`@AppStorage` 钥匙、取证键、签名位、暂停分支里的 tone/动作/过渡 —— **第一版用整文件 contains，被 M1089/M1090 当场证明是免检牌**：整文件里还有五条别的横幅的过渡与 `@AppStorage` 初值，删掉暂停分支那两行它照样绿；已收窄到「if isPausedForDrawing … if let recovery」那一段）+ 产品入口判据（只拨 defaults，不写取证键）+ 像素判据（静置 0 橙、暂停 >10 橙）+ 胶片。`M1088…M1092` **5/5 CAUGHT**、`M1093…M1095` **3/3 CAUGHT**、两张表 `RESTORE_CLEAN=yes`；M1088 极性反了 ⇒ 静置橙=386；M1091 钥匙写错 ⇒ 0/0/0；M1092 删签名位 ⇒ 1x 消失卷 1 个过渡帧。预检 `tables=174 covered=156 arms=468 bad=0`、全仓 **267 文件 / 952 把**；`HIDDEN_ARMS 表=261 可判=886 rot=0`。既有派生键守卫（`MotionDriverTests`）从五个横幅更新为六个，`BANNER_DRIVE 调用点 6 个、键 1 条、无驱动 0 个`。
- **U-1511：③ 436 只读新跑。** `40420998525`：`MOTION_FLOOR_FACTS judged=5/5 executed=74 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3 settings-reset-fade=2 红的用例=testCopyReceiptAppearsAndDis…`、`MOTION_FLOOR_SUITE_RED=1`、`MOTION_FLOOR_REDS=1`（红有名字：**就是本轮刚加的回执胶片**）；没有 `MOTION_FLOOR_OK` 行，`MOTION_FLOOR_UNLISTED` 没有行 ⇒ 具名 NOT-RUN；`notice-banner` 是登记放行臂，未重猜 `must_judge`。这条红由 U-1508 的采样修复处理，**下一跑才可能回到 REDS=0**，本轮不写成 436 已绿。
- **U-1512：① 367 rot 与八步。** `HIDDEN_ARMS 表=261 可判=886 rot=0`（R416 259/878，本轮 +2 表 +8 臂）；预检 `tables=174 covered=156 arms=468 bad=0`、`ARM_TOTAL files=267 arms=952 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`。build **0** 告警；全量 **1106/55/0**；捕获 **210 帧 / 126 条 / 4 skip / 0 失败**；基线 `UPDATED=210`、复验 `COMPARED=210 CHANGED=0 MISSING=0 ADDED=0`（既有 206 帧不变，新增暂停 4 帧）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 416，现读 `python3 scripts/product_streak.py --streak-for 416`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（On-screen 步看门狗收掉，R3-D9 边界；本地绿）；② `MOTION_FLOOR_UNLISTED` 与 `SCROLL_FAILURE_COUNT` 通道缺行；③ `COPY_RECEIPT_FADE` 在 runner 上没有行（stdout 丢，断言只在 stderr）—— 回执过程的本轮 runner 签收只能读下一跑；④ 暂停横幅的**真机点击链**（设置开关 → 主窗口横幅）没有录屏/点击证据，只有 defaults 管线与离屏帧；菜单栏那颗图标仍不显示暂停（443）；⑤ 产品 NSTableView 滚动中段像素帧 `table-lazy-rows`；⑥ 设置内容帧能力闸门仍隐式（441）；⑦ 亮档真机腿仍没跑；⑧ macOS 12 紧凑详情头仍走旧截断；⑨ 437/438/439/440/441/442 仍开；⑩ R417 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 414 · R417（第 416 轮 · 2026-10-27）：暂停采集状态补主窗口横幅（旧 0 橙 → 新 434/386；默认键管线 0/0→434）；R416 run 唯一红＝回执胶片采样窗口，修采样不改门槛（产品 4 文件，暂停状态横幅位）

`recordingPaused` 以前只在设置页那颗开关上可见；主窗口里复制进不来，界面一句话都不说。新 `StatePresentation.Kind.paused`（pause 图标、prominent 墨、橙图标/底、动作「继续记录」）+ `NoticeTone.paused`；`ContentView` 用 `@AppStorage("recordingPaused")` 画第六条横幅，签名加 `bits |= 32` 驱动进出，动作关回开关；取证键 `pausedForCapture`。真看图亮/暗整窗：琥珀带、橙色暂停图标、一句人话与「继续记录」完好。同带旧 0 橙 → 新 434/386 橙；整带变化 141864/141880；只拨 defaults 的产品入口 0→434。新增 4 帧、既有 206 帧不变、基线 210。胶片出现 2x 27/5/0.5822/523ms、1x 27/5/0.5780/444ms；消失 2x 27/5/0.6550/568ms、1x 27/7/0.3539/476ms。M1088–M1092 5/5、M1093–M1095 3/3（M1089/M1090 第一版被整文件 contains 放过，收窄到暂停分支后 CAUGHT）。R416 run 唯一红是回执胶片：30 帧×1.7ms=41ms 的卷子去判 160ms 的过渡 ⇒ 1 个过渡帧；修采样窗口（8ms 下限 + 窗口前置断言），门槛未动；回执 6 帧像素在 runner 上绿（0/0→2416/0、2724/187；暗 0/0→1738/0、1991/177）。全量 1106/55/0；捕获 210/126/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162=162；HIDDEN 261/886 rot=0；预检 174/156/468；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 真看暂停/静置亮帧与暂停暗帧整窗：琥珀带、橙色暂停图标、文案与动作都完好；黑带是已登记的侧栏选中材质。 |
| 判据有效性 | 15/15 | 纯 `.paused` 映射 + 暂停分支源守卫 + defaults 产品入口 + 像素橙点 + 专用胶片；M1088–M1095 8/8 CAUGHT。 |
| 假绿防御 | 15/15 | 静置 0 橙；M1088 极性反了读 386；M1091 钥匙错读 0/0/0；M1092 硬切读 1 帧；既有 206 帧 0 变。 |
| 产品面推进 | 14/15 | 真落 Sources 4 文件、补的是持续状态可见性；扣 1：真机点击链与菜单栏状态仍缺（443）。 |
| 台账一致性 | 15/15 | U-1508…U-1512、D-412、436、R416 跑与回执 red 原文、派生键守卫 6 调用点都从日志/CI 解析。 |
| 交付诚实性 | 15/15 | R416 run 的红原文落账并定位到 1.7ms/160ms；只修采样窗口不改门槛；`COPY_RECEIPT_FADE` 缺行与 436 的 REDS=1 都记 NOT-RUN/未绿。 |
| 可复核性 | 15/15 | 旧/新橙点、defaults 管线、四行胶片、两表八刀、precheck/rot/CI 原文都在。 |

均分 = 104/105 ≈ 14.9/15（99）。"""

DECISION_412 = u"""## D-412 暂停采集用状态规范的第六个 kind，不借 warning（R417）

- 背景：`recordingPaused` 只在设置页那颗开关上可见；主窗口里复制进不来，没有一句人话。直接复用 `.warning` 会让图标变成感叹号、动作默认成「知道了」—— 两件事都不是这个状态的意思。
- 决定：`StatePresentation.Kind` 增加 `.paused`（`pause.circle.fill`、prominent 墨、橙色图标与 12% 底、动作默认「继续记录」）；`NoticeTone.paused` 映射到它；`ContentView` 用 `@AppStorage("recordingPaused")` 读与设置页/采集侧同一把钥匙，`noticeSignature` 加 `bits |= 32` 驱动 `bannerIn/bannerOut`，动作把开关关回去；取证键 `pausedForCapture` 只给夹具/胶片。
- 理由：暂停是**持续状态**，需要一句可读的话和一个真能解决问题的动作（继续记录），不是一次性提示的「知道了」；把图标/墨/动作留给状态规范，横幅只是布局；横幅在 `ContentView` 的签名里有一位，进出才不会硬切。既有 206 帧逐字节不变。
- 兼容性/迁移：只在暂停时多一条横幅；`Kind` 加了一个 case，所有 switch 都显式讨论它；`@AppStorage` 与设置页/采集侧同一个键，键名由源守卫钉住。
- 回滚：删 `Kind.paused`/`NoticeTone.paused` 与 `ContentView` 的暂停分支即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 暂停采集状态补主窗口横幅（旧 0 橙 → 新 434/386；默认键管线 0/0→434）；R416 run 唯一红＝回执胶片采样窗口，修采样不改门槛（R417 / 第 416 轮 / Round 414 / U-1508…U-1512 · 产品 4 文件，暂停状态横幅位）

"""

BACKLOG_SECTION = u"""437 追记（R417 · 仍开）：本轮补的是暂停采集状态的主窗口横幅与回执胶片采样窗口；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

**443. 暂停状态在菜单栏那颗图标上仍不可见，真机点击链也还没有录屏证据**（R417 观察）
    现象：主窗口横幅补上了，但 macOS 13+ 的 `MenuBarExtra(_, systemImage:)` 用的是静态 `clipboard` 符号；暂停时菜单栏没有任何变化。设置页的开关 → 主窗口横幅这条链目前由「同一把 UserDefaults 钥匙 + 派生的 defaults 管线帧」证明，没有真机点击/录屏帧。
    修法（下一轮若需要）：① 把 `MenuBarExtra` 换成自定义 label（`Image(systemName:)` + 暂停角标），并且**先证系统菜单栏这条通道能不能拍**（无录屏权限时 `CGWindowListCreateImage` 会返回尺寸正确的全空图，R63 那族）；拍不到就具名 NOT-RUN，只留组件帧。② 真机点击链用一次 20 秒的屏幕录制/在屏探针，把「拨开关 → 横幅进出」落到 runner 之外的证人上。
"""

STATE_SECTION = u"""## R417 状态（2026-10-27 · 本地 · 第 416 轮 / Round 414）：暂停采集状态补主窗口横幅（旧 0 橙 → 新 434/386；默认键管线 0/0→434）；R416 run 唯一红＝回执胶片采样窗口，修采样不改门槛（产品 4 文件，暂停状态横幅位）

最后更新：2026-10-27（本地 · R417 / 第 416 轮 / Round 414）：`recordingPaused` 以前只在设置页可见。新 `StatePresentation.Kind.paused`（pause.circle.fill、prominent 墨、橙图标/12% 底、动作「继续记录」）+ `NoticeTone.paused`；`ContentView` 用 `@AppStorage("recordingPaused")` 画第六条横幅，`noticeSignature` 加 `bits |= 32` 驱动 bannerIn/bannerOut，动作把开关关回去；取证键 `pausedForCapture`。真看图亮/暗整窗：琥珀带、橙色暂停图标、文案与动作完好。同带旧 **0 橙** → 新 **434/386 橙**（亮/暗），整带变化 141864/141880；只拨 defaults 的产品入口 **0→434**。新增 4 帧、既有 **206 帧逐字节不变**、基线 **210/0/0/0**。胶片出现 2x 27/5/0.5822/523ms、1x 27/5/0.5780/444ms；消失 2x 27/5/0.6550/568ms、1x 27/7/0.3539/476ms。`M1088–M1092` **5/5**、`M1093–M1095` **3/3 CAUGHT**（M1089/M1090 第一版被整文件 contains 放过，收窄到暂停分支后 CAUGHT）。R416 run `40420998525 ↔ a51de8d` **failure**：失败步骤 **1 个**（`Motion coverage floor`），红是 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 在 1x/2x 都只有 1 个过渡帧；定位 `MOTION_GRAB 30 帧/中位 1.7ms/声明 160ms` ⇒ 触发后窗口 ≈41ms，卷子没覆盖过程；修 `Scenario.minimumSampleSpacingMilliseconds`（回执 8ms）并打印/前置断言窗口，**门槛未动**。回执 6 帧像素在 runner 上绿（亮 0/0→2416/0、2724/187；暗 0/0→1738/0、1991/177）；`COPY_RECEIPT_FADE` 在 runner 无行记 NOT-RUN。全量 **1106/55/0**；捕获 **210/126/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 261/886 rot=0；预检 174/156/468 bad=0；产品面连续零改动 **1** 轮（as-of 416，现读 `python3 scripts/product_streak.py --streak-for 416`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R416 runner 唯一红是回执胶片；定位到 30 帧×1.7ms=41ms < 声明 160ms，修采样窗口（8ms 下限 + 窗口前置断言），门槛未动。
② 产品：暂停采集补主窗口横幅（旧 0 橙 → 434/386），defaults 管线 0→434；新增 4 帧。
③ 判据：纯/source/defaults/像素/胶片；M1088–M1095 8/8 CAUGHT；派生键守卫 6 调用点；precheck 174/156/468；hidden rot 0。
④ 436：judged=5/5、REDS=1（红有名字：本轮回执胶片）、UNLISTED 缺行记 NOT-RUN；notice-banner 放行，未重猜 must_judge。
⑤ 367：hidden 表 261 / 可判 886 / rot 0 / 上界 0；ARM 267 文件 / 952 把。
⑥ 全量 1106/55/0；捕获 210/126/4/0；换装 ok；清账 162=162；帧基线 210/0/0/0。

NOT-RUN / 阻塞（分开写）：① runner 的真在屏 `REVEAL`/`INTAKE_READING` 通道没有行（本地绿）；② `MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 通道缺行；③ `COPY_RECEIPT_FADE` 在 runner 没有行（stdout 丢）；④ 暂停横幅真机点击链与菜单栏状态缺证（443）；⑤ `table-lazy-rows`；⑥ 设置内容帧能力闸门仍隐式（441）；⑦ 亮档真机腿仍没跑；⑧ macOS 12 紧凑详情头仍走旧截断；⑨ 437/438/439/440/441/442/443 仍开；⑩ R417 新跑待 push 后读。

下一轮（R418）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R417 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看回执胶片修后是否绿、`COPY_RECEIPT_FADE` 是否有行、暂停横幅 4 帧在 runner 上是否绿。① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 416 轮（R417" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R417 节")
if u"## Round 414 · R417" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 414")
if u"## D-412" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-412")
if u"暂停采集状态补主窗口横幅" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**443." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 443")
if state.count(u"## R416 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R416 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_412 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R416 状态", STATE_SECTION + u"## R416 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R417_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
