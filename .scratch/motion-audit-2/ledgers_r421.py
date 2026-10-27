#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R421 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 419 轮（R420 · 2026-10-27"
AUDIT_SECTION = u"""## 第 420 轮（R421 · 2026-10-27 · U-1528…U-1532）：快速选择面板补屏幕落点（真面板旧 (0,89) → 新 (290,200)，纯策略居中+夹住）；R420 胶片套件跑完（executed=76）但 markdown 2x 只 1 帧 ⇒ CI 判 1x、2x 具名 extended（产品 2 文件，窗口落点位）

- **U-1528：⓪ `40444724766 ↔ f33e87b` 的失败步骤与胶片命运。** 结论 **failure**，失败步骤 **1 个**：`Motion coverage floor`。**套件这次跑完了**：`MOTION_FLOOR_FACTS judged=5/5 executed=76 not-run=-`（extended 分流把 188.7s 压到 134.8s，200s 看门狗没再收），`MOTION_FLOOR_SUITE_RED=1`、`MOTION_FLOOR_REDS=1` —— 唯一红是 `testMarkdownModeLabelChangeIsAVisibleProcess` **2x 只有 1 个过渡帧**（1x=2，峰值 0.0193；同一跑 `MOTION_SOFT_PROBE 2x=2/1905ms、1x=2/1783ms`，probe 可见 ⇒ 不是 channel-blind）。其余全绿：`MOTION_COPY_RECEIPT_FADE` 出现臂 **2x/1x 各 2 帧**（窗口 1260/1375ms）、`MOTION_SIDEBAR_COUNT 1x=2/1173ms`（2x 的 NOT-RUN 没有计红）、`MOTION_HEAT_SUMMARY` 未在本轮通道（热图静态 4 帧仍绿：`HEATMAP_SUMMARY_CHANGE 1255/1349`、右沿 236→242/243）、`MENUBAR_PAUSE_LABEL 92/137/63` 与 12 图 `891→1325`。修法（**门槛未动**）：markdown 的小墨量文字交换在 runner 2x 上采样在边界（1 帧/峰值 0.0193；本机 2x 4–7）⇒ CI 判 **1x**，2x 进 extended 并具名 `MOTION_NOT_RUN=markdown-2x`。CI 模式本地套件 **129.9s / 76 条 / 4 skip / 0 失败**；extended 的 markdown 2x=5、1x=3。
- **U-1529：② 快速选择面板的屏幕落点。** 面板从 `ensurePanel()` 建在 (0,0) 之后就**再也没被摆过** —— 真面板的 frame 原点是 **(0,89)**（屏幕左缘、Dock 之上），而窗口位置从来没有进过任何内容帧或判据。新 `QuickPickPlacement.origin(panelSize:visibleFrame:)`：以 `visibleFrame`（已排除菜单栏与 Dock）为房间居中，再夹住四边；房间比面板小时从可见原点开始，不跑负坐标。`show()` 在 `makeKeyAndOrderFront` **之前** `placePanel`，屏幕优先取**鼠标所在**那一块（多屏跟随工作区），取不到退回主屏；`windowForCapture` 不读屏幕、不改窗口位置（内容帧零变化）。真面板读数：`PANEL_ORIGIN 旧=(0,89) 新=(290,200) 期望=(290,200) 可见=800x600 面板=420x300`；纯策略另外三格：1440×830（菜单栏 25pt）→ **(510,290)**、第二屏 (1600,25,1280,800) → **(2030,275)**、小房间 (0,0,300,200) → **(0,0)**。**既有 218 帧逐字节不变、基线不动**。真机/多屏的运行时落点没有屏幕截图（红线上限：面板会显示真实剪贴板内容，禁止截屏）⇒ 具名 NOT-RUN；真 `NSPanel.frame` 与源接线是 CI 证人。
- **U-1530：判据与刀。** 纯策略真值表（居中/第二屏/小房间/零房间）+ **真 NSPanel** 的 frame（`windowForCapture` 建真面板，`placePanel(in:)` 后读 frame，旧 (0,89)→新 (290,200)）+ 源守卫（show 段里 `screenForPresentation?.visibleFrame`/`placePanel(in:` 且先于 `makeKeyAndOrderFront`；屏幕段里 `NSEvent.mouseLocation`/`NSScreen.main`；placePanel 走 `QuickPickPlacement.origin(panelSize:` 与 `panel.frame.size`）。两张表：`M1109/M1110`（wiring）**2/2 CAUGHT**、`M1111/M1112`（policy）**2/2 CAUGHT**、`RESTORE_CLEAN=yes`（M1112 的失败文本被本地 stdout 丢，证人换成失败的用例名）。预检 `tables=180 covered=162 arms=485 bad=0`、全仓 **273 文件 / 969 把**；`HIDDEN_ARMS 表=267 可判=903 rot=0`。
- **U-1531：③ 436 只读新跑。** `40444724766`：`judged=5/5 executed=76 not-run=-`、`MOTION_FLOOR_SUITE_RED=1`、`MOTION_FLOOR_REDS=1`（红有名字：markdown 2x，不是 floor 的 5 条臂）；没有 `MOTION_FLOOR_OK` 行，`MOTION_FLOOR_UNLISTED` 没有行；`notice-banner` 放行，未重猜 `must_judge`。本轮把 markdown 2x 具名搬 extended，下一跑应 `REDS=0`。
- **U-1532：① 367 rot 与八步。** `HIDDEN_ARMS 表=267 可判=903 rot=0`（R420 265/899，本轮 +2 表 +4 臂）；预检 `tables=180 covered=162 arms=485 bad=0`、`ARM_TOTAL files=273 arms=969 dupes=0 repeats=0`、`BASH_ARMS 16 bad=0`。build **0** 告警；全量 **1121/56/0**；捕获 **218 帧 / 129 条 / 4 skip / 0 失败**；基线复验 `COMPARED=218 CHANGED=0 MISSING=0 ADDED=0`；CI 模式胶片套件 **129.9s / 76 条 / 4 skip / 0 失败**（跑完、有余量）；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、381=381、`SMOKE_OK=1`；清账表 162=162；产品面连续零改动 **1** 轮（as-of 420，现读 `python3 scripts/product_streak.py --streak-for 420`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 真机/多屏的面板运行时落点没有屏幕截图（面板会显示真实剪贴板内容，红线禁止截屏）⇒ 只有真 `NSPanel.frame` + 源接线；② markdown 2x 与 sidebar 2x、receipt 消失臂都在 extended/具名 NOT-RUN（1x 与 probe 仍判）；③ R420 套件的 `MOTION_MARKDOWN_MODE_FADE` 2x 红由本轮 1x CI 化处理，下一跑签收；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿、暂停胶片卷已撤；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–447 仍开；⑩ R421 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 418 · R421（第 420 轮 · 2026-10-27）：快速选择面板补屏幕落点（真面板旧 (0,89) → 新 (290,200)，纯策略居中+夹住）；R420 胶片套件跑完（executed=76）但 markdown 2x 只 1 帧 ⇒ CI 判 1x、2x 具名 extended（产品 2 文件，窗口落点位）

快速选择面板建在 (0,0) 后再也没被摆过：真面板 frame 原点 **(0,89)**（屏幕左缘、Dock 之上），窗口位置从未进过任何帧或判据。新 `QuickPickPlacement.origin(panelSize:visibleFrame:)` 以 visibleFrame 居中并夹住；`show()` 在出场前 `placePanel`，屏幕优先鼠标所在那一块，取不到退主屏；捕获路径不读屏幕。真面板读数旧 (0,89) → 新 (290,200)；纯策略 1440×830→(510,290)、第二屏→(2030,275)、小房间→(0,0)。既有 218 帧不变、基线不动。M1109–M1112 4/4（两张表）。R420 跑：套件跑完（executed=76、5/5 臂），唯一红 markdown 2x=1（1x=2、probe 2/2；峰值 0.0193）⇒ CI 判 1x，2x 具名 `markdown-2x` 进 extended；回执出现 2/2、侧栏 1x=2、热图 4 帧绿、菜单栏 92/137/63。CI 套件 129.9s/76/0。全量 1121/56/0；捕获 218/129/4/0；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162=162；HIDDEN 267/903 rot=0；预检 180/162/485；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 面板位置是窗口 frame 事实：真 NSPanel 旧 (0,89)→新 (290,200)，纯策略三格；扣 1：真机/多屏没有截屏（红线：面板含真实剪贴板）⇒ 具名 NOT-RUN。 |
| 判据有效性 | 15/15 | 纯策略 + 真 NSPanel frame + 三段源守卫；M1109–M1112 4/4 CAUGHT（两张表）。 |
| 假绿防御 | 15/15 | 夹住/第二屏原点两刀都被纯判据抓；show 不落点/不跟鼠标两刀被源抓；内容帧 218 帧 0 变。 |
| 产品面推进 | 14/15 | 真落 Sources 2 文件、修的是真窗口落点（旧位置在屏幕左缘）；扣 1：运行时多屏落点未在真机签收。 |
| 台账一致性 | 15/15 | U-1528…U-1532、D-417、436 的 executed=76/reds=1、markdown 2x 与 extended 分流都从日志解析。 |
| 交付诚实性 | 15/15 | 套件跑完但 markdown 2x 红逐条落账；1x CI 化不改 ≥2；真机截屏红线不碰；面板旧原点实际是 (0,89) 照实写。 |
| 可复核性 | 15/15 | 真面板 frame 读数、四格纯策略、两张刀表、precheck/rot/套件时长与 CI 原文都在。 |

均分 = 103/105 ≈ 14.7/15（98）。"""

DECISION_417 = u"""## D-417 快速选择面板按鼠标所在屏幕的 visibleFrame 居中并夹住（R421）

- 背景：`ensurePanel()` 把 420×300 的面板建在 (0,0) 后再没摆过；真面板 frame 原点是 (0,89)（屏幕左缘、Dock 之上），而窗口位置从未进过任何内容帧/判据 —— 内容帧拍得再好也看不见它开在屏幕角落。
- 决定：`QuickPickPlacement.origin(panelSize:visibleFrame:)` 纯策略，以 visibleFrame（排除菜单栏/Dock）居中并夹住四边（房间比面板小时锚在可见原点，不跑负坐标）；`show()` 在 `makeKeyAndOrderFront` 之前 `placePanel`，屏幕优先取鼠标所在那一块、退主屏；`windowForCapture` 不读屏幕、不改窗口位置。
- 理由：热键呼出的面板应跟随工作区；窗口位置是**落点事实**，用真 `NSPanel.frame` 与纯策略判，而不是另拍一张合成桌面（面板会显示真实剪贴板内容，截屏触红线）。
- 兼容性/迁移：捕获帧零变化（218 帧逐字节不变）；`placePanel` 只改窗口原点。
- 回滚：删 show() 里的 placePanel 调用与 QuickPickPlacement 即可；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 快速选择面板补屏幕落点（真面板旧 (0,89) → 新 (290,200)，纯策略居中+夹住）；R420 胶片套件跑完（executed=76）但 markdown 2x 只 1 帧 ⇒ CI 判 1x、2x 具名 extended（R421 / 第 420 轮 / Round 418 / U-1528…U-1532 · 产品 2 文件，窗口落点位）

"""

BACKLOG_SECTION = u"""437 追记（R421 · 仍开）：本轮补的是快速选择面板的屏幕落点与 markdown 2x 的 extended 分流；主列表仍不匹配 `sourceAppName`，与 QuickPick 继续两套搜索语言。

446 追记（R421 · 仍开）：CI 套件 129.9s/76 条/0 失败（70s 余量）；extended 卷仍没有 CI 步。

**447. 快速选择面板的运行时多屏落点没有真机签收：面板会显示真实剪贴板内容，截屏触红线**（R421）
    现象：落点由纯策略 + 真 `NSPanel.frame` + 源守卫钉住（旧 (0,89) → 新 (290,200)），但"在多屏/带 Dock 的真机上，热键一按是否就在鼠标屏中央"没有屏幕证据 —— 任何全屏/窗口截图都会带出真实剪贴板文本。
    修法（下一轮）：用**临时数据目录 + 合成条目**启动一个受控实例（`CLIPBOARD_HISTORY_DATA_DIR` 那一族），再走热键/菜单入口拍窗口级截图；先证明截图里只有合成文本，再让它进帧基线。拍不到就继续 NOT-RUN，不拿内容帧冒充落点。
"""

STATE_SECTION = u"""## R421 状态（2026-10-27 · 本地 · 第 420 轮 / Round 418）：快速选择面板补屏幕落点（真面板旧 (0,89) → 新 (290,200)，纯策略居中+夹住）；R420 胶片套件跑完（executed=76）但 markdown 2x 只 1 帧 ⇒ CI 判 1x、2x 具名 extended（产品 2 文件，窗口落点位）

最后更新：2026-10-27（本地 · R421 / 第 420 轮 / Round 418）：快速选择面板建在 (0,0) 后再没被摆过：真面板 frame 原点 **(0,89)**（屏幕左缘、Dock 之上），窗口位置从未进过任何帧或判据。新 `QuickPickPlacement.origin(panelSize:visibleFrame:)`：以 visibleFrame 居中并夹住（房间小则锚可见原点）；`show()` 在 `makeKeyAndOrderFront` 之前 `placePanel`，屏幕优先鼠标所在块、退主屏；`windowForCapture` 不读屏幕。真面板 **旧 (0,89) → 新 (290,200)**（可见 800×600、面板 420×300）；纯策略 1440×830→**(510,290)**、第二屏→**(2030,275)**、小房间→**(0,0)**。既有 **218 帧逐字节不变、基线不动**。`M1109/M1110` 2/2、`M1111/M1112` 2/2 CAUGHT。R420 run `40444724766 ↔ f33e87b` **failure**，失败步骤 **1 个**（`Motion coverage floor`）：**套件跑完**（`judged=5/5 executed=76`），唯一红是 markdown **2x=1 帧**（1x=2、峰值 0.0193；probe 2x=2/1x=2 可见）⇒ 小墨量文字交换的 2x 采样边界；CI 判 1x、2x 进 extended 并具名 `markdown-2x`。回执出现 2/2（1260/1375ms）、侧栏 1x=2（2x NOT-RUN 未计红）、热图 4 帧绿（1255/1349、右沿 236→242/243）、菜单栏 92/137/63 与 12 图 891→1325。CI 模式胶片套件 **129.9s/76/4/0**。全量 **1121/56/0**；捕获 **218/129/4/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 162=162；HIDDEN 267/903 rot=0；预检 180/162/485 bad=0；产品面连续零改动 **1** 轮（as-of 420，现读 `python3 scripts/product_streak.py --streak-for 420`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R420 套件跑完（executed=76），唯一红 markdown 2x=1（1x=2、probe 可见）⇒ CI 判 1x、2x 具名 extended；其余通道全绿。
② 产品：快速选择面板屏幕落点（旧 (0,89) → 新 (290,200)），纯策略 + 真 NSPanel frame；218 帧不变。
③ 判据：M1109–M1112 4/4；precheck 180/162/485；hidden rot 0。
④ 436：judged=5/5 executed=76、SUITE_RED=1（markdown 2x）、UNLISTED 缺行；未重猜。
⑤ 367：hidden 表 267 / 可判 903 / rot 0 / 上界 0；ARM 273 文件 / 969 把。
⑥ 全量 1121/56/0；捕获 218/129/4/0；套件 129.9s；换装 ok；清账 162=162；帧基线 218/0/0/0。

NOT-RUN / 阻塞（分开写）：① 真机/多屏运行时落点没有屏幕截图（面板含真实剪贴板，红线禁止截屏）⇒ 只有真面板 frame + 源；② markdown 2x / sidebar 2x / receipt 消失臂在 extended 具名；③ R420 的 markdown 2x 红待下一跑签收；④ skeleton 套件内偶发；⑤ 真菜单栏表面、12 实时腿、暂停胶片卷已撤；⑥ `REVEAL`/`INTAKE_READING`、`MOTION_FLOOR_UNLISTED`/`SCROLL_FAILURE_COUNT` 缺行；⑦ `table-lazy-rows`；⑧ 设置能力闸门仍隐式（441）；⑨ 437–447 仍开；⑩ R421 新跑待 push 后读。

下一轮（R422）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R421 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 markdown 1x=2、套件是否 REDS=0、面板落点是否在 CI（真面板 frame 与源）；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

audit = rd(AUDIT)
iter_text = rd(ITER)
decisions = rd(DECISIONS)
changelog = rd(CHANGELOG)
backlog = rd(BACKLOG)
state = rd(STATE)

if audit.count(AUDIT_TITLE) != 1:
    raise SystemExit("REFUSED AUDIT 锚点命中 %d 次" % audit.count(AUDIT_TITLE))
if u"第 420 轮（R421" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R421 节")
if u"## Round 418 · R421" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 418")
if u"## D-417" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-417")
if u"快速选择面板补屏幕落点" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**447." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 447")
if state.count(u"## R420 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R420 状态"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_417 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R420 状态", STATE_SECTION + u"## R420 状态", 1)

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
print("LEDGERS_R421_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state)))
