#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R432 七本台账一次落盘（只跑一次；先断言所有锚点，全部通过才写）。"""
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


AUDIT_TITLE = u"## 第 430 轮（R431 · 2026-10-27"
AUDIT_SECTION = u"""## 第 431 轮（R432 · 2026-10-27 · U-1583…U-1587）：设置隐私页排除名单改「图标 + 应用名 + bundle ID」行（旧 9 行首段「默认排除：」42.5pt → 新图标段 10–14pt；6 张隐私帧变化、基线 238）；R431 跑失败步骤 2 个（1x 理由带蹭到时间列 11≥10、主窗口 content 帧 1x 整帧不画）⇒ 1x 具名 NOT-RUN、阈值未动（产品 3 文件，排除名单行位）

- **U-1583：⓪ R431 跑的失败步骤与符号/仪器命运。** `40512470409 ↔ 3de5de8` **failure**：20 步里**失败步骤 2 个**（`Swift tests (executed-count gate)`、`Capture gate (unregistered reds must be zero)`）。两条红都是 **R431 的仪器在 1x 上没有对象**：① `testQuickPickSourceMatchReasonExtendsTheTypedRow` 两档都读到 `list 扩展=11`（判 `<10`）—— 固定带右沿 300pt 把 **1x 上从 296pt 开始的时间列**左沿算了进来（本机 2x 时间列 311 起，带子够不着）；typed 扩展 228/259、校准 357/364 与 417/444 都正常。② `testFileRowsShowTheirTypeSymbol` 两档**四格全 0**（`校准=0 文本行=0 file=0 files=0 档=1.00px/pt`）—— 连同一帧的彩色缩略图校准都没墨，说明**主窗口 `ContentView` 整帧在 runner 1x 离屏通道里没画出来**（与设置脚注 1x 带、源图标 1x 带同族），不是行首符号的问题。其余全绿：时间列 1x light 末段宽 `[74.0,71.0,74.0,74.0,74.0]` 起 296–298 止 369–370、dark `[74.0,72.0,74.0,74.0,74.0]` 止 370，校准 395–800；`SETTINGS_FOOTER_BAND_NOT_RUN` 按名出现、脚注用例 passed、不计红；分区带 `13/12`（light）与 `11/10`（dark）；`PINNED_SECTION_ROWS 6/5 选中 [2]/[1]`；菜单 **5/5 passed**；floor `judged=5/5 executed=77 not-run=-`、`SUITE_CLEAN=0`、`MOTION_FLOOR_OK=5/5`、无红、无 unlisted；回执 **2/2**（2x 峰值 0.1333/1191ms、1x 0.1444/1269ms，均 `重抓=no`）；滚动 **4/4 passed**（`CHANNEL 0→51→600 变化 37200/28466`）；Dock 标记已登记。
- **U-1584：⓪ 的修法：两处都只动仪器。** ① 理由固定带从 `x=160..300` 收到 `x=160..290`（1x 时间列 296 起，留 6pt 余量），typed/list 的负臂重新读到 0；② `testFileRowsShowTheirTypeSymbol` 加 1x 分支：`scale < 1.5` 时打 `FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`（四格读数照打）并跳过像素断言，2x 断言一字不动（本机 light 492/209/165/231、dark 475/209/492/492，地板 图标 20·s²/校准 50·s²）；收尾断言改成「每档要么判了、要么具名，且两档同路」。两条都没有改阈值（`<10`、`40`、`scale²` 地板原样）。
- **U-1585：② 设置隐私页排除名单改「图标 + 应用名 + bundle ID」行。** 缺陷形状（`settings-privacy` 亮/暗直看）：默认名单是九行 `默认排除：com.…` 的裸 ID 文本流 —— 行首第一段就是「默认排除：」五个字（逐行同值 **42.5pt**），用户认不出是哪个 App。修法：新 `ExcludedAppPresentation`（九条默认 ID 的公认名字；认不得的原样返回 ID；`app.dashed` 兜底符号）+ `ExcludedAppRow`（16pt 真实 `NSWorkspace` 图标，找不到画兜底符号；应用名 12pt + bundle ID 11pt `.secondary`，行高 20pt，图标与名字间距 6pt）+ `SettingsView` 的默认名单与用户名单都改走这一行。旧/新帧读数（`settings-privacy-tall` 亮/暗）：行首第一段墨宽 **42.5pt（逐行同值）→ 10.0–14.0pt（图标段）**，`EXCLUDED_APP_ROW light 行数=10 判=6 首段宽=[10.0,10.0,10.0,10.0,14.0,14.0] 行墨=[2704,2421,2429,2641,2417,3201]`、dark `[10.0,10.0,10.0,10.0,10.5,12.0]` / `[3055,2748,2757,3035,2125,3061]`。真看图：密码/钥匙串访问出现真实彩色图标，未安装的密码管理器是虚线 App 占位符；名字与 ID 同一行、ID 退到次色。6 张隐私帧变化，基线仍 **238/0/0/0**。
- **U-1586：判据与刀（含一条探针退役）。** 新 `ExcludedAppPresentationTests` 三条（九条默认项都有名字且不等于 ID / 未知 ID 回退 / bundle ID 必须 `.secondary` 的源守卫）+ `testExcludedAppsStartWithAnIconInsteadOfRawIDs`（`settings-privacy-tall` 每行第一段墨宽 5…30pt + 行墨校准）。**退役** `captionInkProbes` 里「默认排除清单第一行」那条：它的对象已从一行纯 `.secondary` 说明变成「主色名字 + 次色 ID」的行，同带两种色阶把 caption 上限顶到 **12.70/11.32 倍参照**（假红）；该页另两段说明仍在表里（`CAPTION_JUDGED` 17 条全判）。`M1183–M1188` **6/6 CAUGHT**（名字映射失效 / 名字空串 / 图标撤掉 / 图标与名字挤成一段 / 默认名单接回带前缀文本 / 接回裸 ID 文本；RESTORE_CLEAN=yes）。预检 `tables=210 covered=192 arms=555 bad=0`、`BASH_ARMS 6/16 bad=0`、`ARM_TOTAL files=303 arms=1038 dupes=0`；`HIDDEN_ARMS 表=297 可判=972 rot=0`。
- **U-1587：八步。** build **0 告警**；捕获 **139 条 / 4 skip / 0 失败 / 238 帧**；帧基线 `CHANGED=6 / MISSING=0 / ADDED=0`（`settings-privacy`、`settings-privacy-tall`、`settings-privacy-excluded` × 亮暗），`UPDATED=238`、复验 **238/0/0/0**；全量 **1167/57/5**（5 个断言全在 `SelectionRevealAnimationTests` 的 3 条用例；单跑 `caffeinate -u` 后 **4/4 passed**，`TIME 采样=18/中间值=9/首=61/末=1438`、`CHANNEL 0→88.5→600 变化 93706/136800 重抓=no`、`OFFSET 0/230.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449，不改门槛）；换装 `INSTALL_RESULT=ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 431，现读 `python3 scripts/product_streak.py --streak-for 431`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。
- **具名 NOT-RUN / 观察**：① 设置侧栏脚注带 runner 1x（`SETTINGS_FOOTER_BAND_NOT_RUN=runner-1x-band-geometry`）；② **主窗口 content 帧 runner 1x 整帧不画**（`FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`，见 458）；③ 13+ MenuBarExtra 系统菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；④ 真实系统拖拽会话（`DRAG_SOURCE_REAL_SESSION_NOT_RUN=no-ui-drag-automation`，453）；⑤ Dock 角标像素/帧（`DOCK_BADGE_PIXEL_NOT_RUN=tile-rendered-by-window-server`）；⑥ 源图标最小窗文字 1x 带（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN=runner-1x-band-geometry`）；⑦ 本地全量 5 条滚动红（`LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`，CI 4/4 绿，449）；⑧ markdown 2x / sidebar 2x / receipt 消失臂在 extended；⑨ 固定块揭示偏移无独立像素验收（455）；⑩ 跨年记录没有年份（456）；⑪ 主列表暗档文字离屏盲区未登记（457）；⑫ 真机/多屏面板落点无截屏（447）；⑬ 真菜单栏表面、12 实时腿；⑭ `table-lazy-rows`；⑮ 437–458 仍开；⑯ R432 新跑待 push 后读。

"""

ITER_SECTION = u"""## Round 429 · R432（第 431 轮 · 2026-10-27）：设置隐私页排除名单改「图标 + 应用名 + bundle ID」行（旧 9 行首段「默认排除：」42.5pt → 新图标段 10–14pt；6 张隐私帧变化、基线 238）；R431 跑失败步骤 2 个（1x 理由带蹭到时间列 11≥10、主窗口 content 帧 1x 整帧不画）⇒ 1x 具名 NOT-RUN、阈值未动（产品 3 文件，排除名单行位）

设置隐私页的默认排除名单以前是九行 `默认排除：com.…` 的裸 ID 文本流，行首第一段就是「默认排除：」五个字（逐行 42.5pt），用户认不出是哪个 App。新 `ExcludedAppPresentation`（九条公认名字 + 未知回退 ID + `app.dashed` 兜底）+ `ExcludedAppRow`（16pt 真实图标 / 兜底符号 + 应用名 12pt + bundle ID 11pt `.secondary`，行高 20）+ `SettingsView` 两处名单接线。旧/新帧读数：首段墨宽 42.5pt → 10.0–14.0pt；`EXCLUDED_APP_ROW light 首段宽=[10.0,10.0,10.0,10.0,14.0,14.0] 行墨=[2704,2421,2429,2641,2417,3201]`、dark `[10.0,10.0,10.0,10.0,10.5,12.0]`。密码/钥匙串访问出现真实彩色图标，未安装的是虚线 App 占位符。6 张隐私帧变化，基线 238/0/0/0。R431 run `40512470409 ↔ 3de5de8` **failure、失败步骤 2 个**（Swift tests / Capture gate）：理由固定带右沿 300 把 1x 时间列（296 起）左沿算进负臂（11≥10）、主窗口 content 帧在 1x 整帧不画（校准也 0）⇒ 带子收到 290、1x 打 `FILE_ROW_SYMBOL_NOT_RUN`，阈值未动。caption 探针「默认排除第一行」退役（对象变成两种色阶）；M1183–M1188 6/6；预检 210/192/555 bad=0；HIDDEN 297/972 rot=0。全量 1167/57/5（5 断言全在 SelectionRevealAnimationTests），单跑 4/4（TIME 18/9、61→1438；CHANNEL 0→88.5→600）⇒ 具名 LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order（449）。捕获 139/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看隐私页亮/暗/tall 三档：九行从裸 ID 变成图标+名字+ID，密码/钥匙串访问有真实彩色图标、未安装的是虚线占位符；同时看到滚动后布局仍成立。扣 2：没有真机截图；虚线占位符在八行里重复，辨识度仍有限。 |
| 判据有效性 | 15/15 | 名字映射/未知回退/次色源守卫 3 条 + 行首第一段墨宽（5…30pt）+ 行墨校准；M1183–M1188 6/6；退役探针有替代证人。 |
| 假绿防御 | 15/15 | 行首第一段宽度不依赖图标颜色（兜底符号也能过）；caption 探针退役时写清假红成因；1x 整帧不画走具名 NOT-RUN 而不是假绿/假红。 |
| 产品面推进 | 14/15 | 真落 3 文件（隐私页排除名单行），修的是"看得见但读不懂"的缺陷；扣 1：未做折叠/搜索/分组，行长与图标占位仍朴素。 |
| 台账一致性 | 15/15 | U-1583…U-1587、D-428、R431 的 11/0、R432 的 42.5→10–14、1167 都从日志/帧/用例解析。 |
| 交付诚实性 | 15/15 | R431 的两条红都写成"仪器没有对象"并给 1x 读数；主窗口 1x 整帧不画进 458；caption 探针退役写清 12.70/11.32 假红。 |
| 可复核性 | 15/15 | 帧名、首段宽/行墨、旧帧 42.5 逐行同值、刀号与红在哪个用例、precheck/rot/CI 原文、基线 238、换装/清账都在。 |

均分 = 102/105 ≈ 14.6/15（96）。"""

DECISION_428 = u"""## D-428 排除名单用「图标 + 应用名 + bundle ID」行；像素证人用行首第一段墨宽（R432）

- 背景：设置隐私页的默认排除名单是九行 `默认排除：com.…` 的裸 ID，用户认不出 App；旧 caption 探针（默认名单第一行）因为对象变成两种色阶而退役。
- 决定：① 新 `ExcludedAppPresentation`：九条已知 ID → 公认名字，未知 ID 原样返回，兜底符号 `app.dashed`；② 新 `ExcludedAppRow`：16pt `NSWorkspace` 图标（找不到画符号）+ 12pt 名字 + 11pt `.secondary` bundle ID，行高 20、图标与名字间距 6；默认名单与用户名单共用；③ 像素判据只读**行首第一段墨宽**（5…30pt，旧形状「默认排除：」42.5pt），不依赖图标颜色。
- 理由：应用名是这一列里唯一能回答"这是哪个 App"的信息；bundle ID 仍有价值（用户可能按 ID 搜索/比对），退到次色而不是删掉。图标颜色随机器/安装情况变化，不能当判据；"行首是不是一枚图标"用几何最稳。
- 兼容性/迁移：默认名单 9 行行高从 caption 行变成 20pt 行，隐私卡片增高、页面滚动位置变化；6 张隐私帧更新，基线仍 238。用户名单的「移除」按钮与行过渡未动。
- 边界：未安装 App 用虚线占位符（不伪造真实图标）；没有折叠/搜索/分组（458 之外的下一轮候选）；1x runner 上主窗口整帧不画，行首符号与名单的像素判据在 CI 上具名 NOT-RUN（458）。
- 回滚：删 `ExcludedAppPresentation.swift` / `ExcludedAppRow.swift`，把默认名单改回 `Text("默认排除：\\(id)")`；或 `git revert` 本轮提交。
"""

CHANGELOG_SECTION = u"""### 设置隐私页排除名单改「图标 + 应用名 + bundle ID」行（旧 9 行首段「默认排除：」42.5pt → 新图标段 10–14pt；6 张隐私帧变化、基线 238）；R431 跑失败步骤 2 个（1x 理由带蹭到时间列 11≥10、主窗口 content 帧 1x 整帧不画）⇒ 1x 具名 NOT-RUN、阈值未动（R432 / 第 431 轮 / Round 429 / U-1583…U-1587 · 产品 3 文件，排除名单行位）

"""

BACKLOG_SECTION = u"""437 追记（R432 · 仍开）：本轮只改了排除名单的呈现；主列表仍不匹配 `sourceAppName`。

449 追记（R432 · 仍开）：R431 CI 跑里 `SelectionRevealAnimationTests` 4/4 passed（CHANNEL 0→51→600、TIME 7/2/582/1430），本机全量仍 5 断言红（3 条用例）、单跑 4/4 绿（TIME 18/9、61→1438）⇒ 会话/顺序再次坐实；不改门槛。

451 追记（R432 · 仍开）：macOS 12 的详情头部阈值本轮未动。

452 追记（R432 · 仍开）：脚注 1x 具名 NOT-RUN 继续生效；版本行布局未动。

453 追记（R432 · 仍开）：真实系统拖拽会话仍无自动化验收。

454 追记（R432 · 仍开）：菜单具名标记仍未发射；菜单 5/5 由真实 NSMenu 用例作证。

455 追记（R432 · 仍开）：固定条目滚动到位的独立偏移验收仍缺。

456 追记（R432 · 仍开）：跨年记录仍无年份。

457 追记（R432 · 仍开）：主列表暗档文字在离屏帧里仍是黑底黑字；本轮的行首符号像素判据在 1x 上因此只能整帧具名 NOT-RUN（458）。

**458. 主窗口 `ContentView` 整帧在 runner 1x 离屏通道里不画：行首符号/名单的像素判据在 CI 上没有对象**（R432 观察）
    现象：R431 跑里 `FILE_ROW_SYMBOL light/dark 校准=0 文本行=0 file=0 files=0 档=1.00px/pt` —— 连同一帧的彩色缩略图校准都 0；同一台机器上 `settings-*` 帧能画（CAPTION_JUDGED 17 条），`content-with-history` 950×560 的主窗口帧画不出。也就是说"主窗口整帧"与"设置整帧"在 1x 是两个通道。
    修法（下一轮若需要）：① 给行首符号找一张**组件级替身帧**（300×74 的 `row-*` 帧在 1x 能画，DRAG_SOURCE 就是 3026/2655 的读数）并把判据搬过去，CI 就有像素证人；② 或把主窗口帧的 `contentMustFit`/渲染路径改成与设置页同一条；在那之前，`FILE_ROW_SYMBOL` 在 1x 是具名 NOT-RUN，不许把"没画"读成"画坏了"。
"""

STATE_SECTION = u"""## R432 状态（2026-10-27 · 本地 · 第 431 轮 / Round 429）：设置隐私页排除名单改「图标 + 应用名 + bundle ID」行（旧 9 行首段「默认排除：」42.5pt → 新图标段 10–14pt；6 张隐私帧变化、基线 238）；R431 跑失败步骤 2 个（1x 理由带蹭到时间列 11≥10、主窗口 content 帧 1x 整帧不画）⇒ 1x 具名 NOT-RUN、阈值未动（产品 3 文件，排除名单行位）

最后更新：2026-10-27（本地 · R432 / 第 431 轮 / Round 429）：设置隐私页的默认排除名单以前是九行 `默认排除：com.…` 的裸 ID，用户认不出是哪个 App；行首第一段就是「默认排除：」五个字（逐行 **42.5pt**）。新 `ExcludedAppPresentation`（九条公认名字、未知回退 ID、`app.dashed` 兜底）+ `ExcludedAppRow`（16pt `NSWorkspace` 图标 / 兜底符号 + 应用名 12pt + bundle ID 11pt `.secondary`，行高 20，间距 6）+ `SettingsView` 两处名单接线。旧/新帧读数：首段墨宽 **42.5pt → 10.0–14.0pt**；`EXCLUDED_APP_ROW light 首段宽=[10.0,10.0,10.0,10.0,14.0,14.0] 行墨=[2704,2421,2429,2641,2417,3201]`、dark `[10.0,10.0,10.0,10.0,10.5,12.0]` / `[3055,2748,2757,3035,2125,3061]`。密码/钥匙串访问出现真实彩色图标，未安装的是虚线 App 占位符。6 张隐私帧变化，基线 **238/0/0/0**；退役「默认排除第一行」caption 探针（对象变成主色名字 + 次色 ID，同带两种色阶把上限顶到 12.70/11.32 倍参照）。R431 run `40512470409 ↔ 3de5de8` **failure，失败步骤 2 个**（Swift tests / Capture gate）：理由固定带右沿 300 把 1x 时间列（296 起）左沿算进负臂（11≥10）、主窗口 content 帧在 1x 整帧不画（校准也 0）⇒ 带子收到 290、1x 打 `FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`，阈值未动；时间列 1x light `[74,71,74,74,74]` 起 296–298 止 369–370、dark `[74,72,74,74,74]` 止 370；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；菜单 5/5；floor 5/5/77 无红；回执 2/2；滚动 4/4（`CHANNEL 0→51→600 37200/28466`）。`M1183–M1188` **6/6 CAUGHT**；预检 **210/192/555 bad=0**、ARM **303 文件 / 1038 把**、HIDDEN **297/972 rot=0**。本地全量 **1167/57/5**：5 断言全在 `SelectionRevealAnimationTests`（3 条用例），单跑（caffeinate-u 后）**4/4 passed**（`TIME 18/9/61/1438`、`CHANNEL 0→88.5→600 变化 93706/136800 重抓=no`、`OFFSET 0/230.5/1438`）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 **139/4/0 / 238 帧**；基线 **238/0/0/0**；换装 `ok / SHA_MATCH=1 / 381=381 / SMOKE_OK=1`；清账 `格=162 声明=63 不成立=0/63`；产品面连续零改动 **1** 轮（as-of 431，现读 `python3 scripts/product_streak.py --streak-for 431`）。电池 `Ran 683 / OK (skipped=4)`（台账后复跑）。

本轮做了什么：
① ⓪ R431 跑 failure、失败步骤 2 个：两条红都是仪器在 1x 没有对象（理由带蹭时间列 11、主窗口整帧不画 0）⇒ 带子收窄到 290、1x 具名 NOT-RUN、阈值未动；时间列/脚注/分区/表格/菜单/floor/回执/滚动全绿。
② 产品：隐私页排除名单改「图标 + 应用名 + bundle ID」行（旧 42.5pt 前缀 → 新 10–14pt 图标段；6 张帧变化）。
③ 判据：M1183–M1188 6/6；caption 探针退役有替代；precheck 210/192/555；hidden rot 0。
④ 436：R431 跑 floor judged=5/5 executed=77、无红、无 unlisted；本轮不重猜 must_judge。
⑤ 367：hidden 表 297 / 可判 972 / rot 0。
⑥ 捕获 139/4/0、238 帧；换装 ok；清账 162/63/0；帧基线 238/0/0/0；本地全量 1167/57/5（5 条滚动红具名会话/顺序 NOT-RUN，CI 4/4 绿）。

NOT-RUN / 阻塞（分开写）：① 设置侧栏脚注带 1x（`SETTINGS_FOOTER_BAND_NOT_RUN`）；② 主窗口 content 帧 1x 整帧不画（`FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`，458）；③ 13+ 菜单像素/标题（`MENU_ITEM_SHORTCUT_PIXEL_NOT_RUN=system-menu`，454）；④ 真实拖拽（453）；⑤ Dock 像素（`DOCK_BADGE_PIXEL_NOT_RUN`）；⑥ 源图标最小窗文字 1x（`SOURCE_APP_BADGE_MIN_TEXT_NOT_RUN`）；⑦ 本地全量 5 条滚动红（449）；⑧ 2x/extended 臂；⑨ 固定块揭示偏移（455）；⑩ 跨年时间（456）；⑪ 主列表暗档文字离屏盲区（457）；⑫ 真机/多屏（447）；⑬ 真菜单栏、12 实时腿；⑭ `table-lazy-rows`；⑮ 437–458 仍开；⑯ R432 新跑待 push 后读。

下一轮（R433）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 R432 主笔+追记 head 跑全部失败步骤（成对 run↔commit），in_progress/0 字节不算绿；重点看 `FILE_ROW_SYMBOL_NOT_RUN` 是否按名出现且不计红、`EXCLUDED_APP_ROW` 在 1x 上的首段宽与行数、搜索框外带/理由固定带/时间列/脚注/分区/菜单/Dock/搜索/滚动是否仍绿；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 继续产品视觉位并落 Sources、换缺陷类别；③ 436 只复核新跑 Motion floor，不重猜 `must_judge`。

"""

R432_REPORT_BULLET = u"""- **R432（排除名单行位）**：设置隐私页的默认排除名单以前是九行 `默认排除：com.…` 的裸 ID，用户认不出是哪个 App；行首第一段就是「默认排除：」五个字（逐行 **42.5pt**）。新 `ExcludedAppPresentation`（九条公认名字、未知回退 ID、`app.dashed` 兜底）+ `ExcludedAppRow`（16pt `NSWorkspace` 图标 / 兜底符号 + 应用名 12pt + bundle ID 11pt `.secondary`，行高 20、间距 6）+ `SettingsView` 两处名单接线。旧/新帧读数：首段墨宽 **42.5pt → 10.0–14.0pt**；`EXCLUDED_APP_ROW light 首段宽=[10.0,10.0,10.0,10.0,14.0,14.0] 行墨=[2704,2421,2429,2641,2417,3201]`、dark `[10.0,10.0,10.0,10.0,10.5,12.0]`。密码/钥匙串访问出现真实彩色图标，未安装的是虚线占位符。6 张隐私帧变化，基线 **238/0/0/0**；退役「默认排除第一行」caption 探针（对象变成两种色阶，上限读到 12.70/11.32 倍参照的假红）。R431 run `40512470409 ↔ 3de5de8` **failure、失败步骤 2 个**（Swift tests / Capture gate）：理由固定带右沿 300 把 1x 时间列（296 起）左沿算进负臂（11≥10）、主窗口 content 帧在 1x 整帧不画（校准也 0）⇒ 带子收到 290、1x 打 `FILE_ROW_SYMBOL_NOT_RUN=runner-1x-content-frame-plain`，阈值未动；时间列 1x 稳定（light 74/71、止 369–370；dark 74/72、止 370）；脚注 NOT-RUN 按名出现；分区 13/12 与 11/10、表格 6/5；菜单 5/5；floor 5/5/77；回执 2/2；滚动 4/4。M1183–M1188 **6/6**；预检 210/192/555 bad=0；HIDDEN 297/972 rot=0。本地全量 **1167/57/5**：5 断言全在 SelectionRevealAnimationTests，单跑 4/4（TIME 18/9、61→1438；CHANNEL 0→88.5→600、93706/136800）⇒ 具名 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449）。捕获 139/4/0、238 帧；换装 ok/SHA_MATCH=1/381=381/SMOKE_OK=1；清账 162/63/0；电池 683/4。
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
if u"第 431 轮（R432" in audit:
    raise SystemExit("REFUSED AUDIT 已有 R432 节")
if u"## Round 429 · R432" in iter_text:
    raise SystemExit("REFUSED ITERATION 已有 Round 429")
if u"## D-428" in decisions:
    raise SystemExit("REFUSED DECISIONS 已有 D-428")
if u"设置隐私页排除名单改" in changelog:
    raise SystemExit("REFUSED CHANGELOG 已有该标题")
if u"**458." in backlog:
    raise SystemExit("REFUSED BACKLOG 已有 458")
if state.count(u"## R431 状态") != 1:
    raise SystemExit("REFUSED STATE 锚点命中 %d 次" % state.count(u"## R431 状态"))
U_CELL_OLD = u"U-31 … U-1582（R431 现读抬到最新一节）"
if report.count(U_CELL_OLD) != 1:
    raise SystemExit("REFUSED REPORT U 格命中 %d 次" % report.count(U_CELL_OLD))
if report.count(u"AGENT_STATE.md` 的 R431 节 ②") != 1:
    raise SystemExit("REFUSED REPORT §13 指针命中 %d 次" % report.count(u"AGENT_STATE.md` 的 R431 节 ②"))

new_audit = audit.replace(AUDIT_TITLE, AUDIT_SECTION + AUDIT_TITLE, 1)
new_iter = iter_text.rstrip() + "\n\n" + ITER_SECTION + "\n"
new_decisions = decisions.rstrip() + "\n\n" + DECISION_428 + "\n"
marker = u"## [Unreleased]\n"
if changelog.count(marker) != 1:
    raise SystemExit("REFUSED CHANGELOG [Unreleased] 命中 %d 次" % changelog.count(marker))
new_changelog = changelog.replace(marker, marker + "\n" + CHANGELOG_SECTION, 1)
new_backlog = backlog.rstrip() + "\n\n" + BACKLOG_SECTION + "\n"
new_state = state.replace(u"## R431 状态", STATE_SECTION + u"## R431 状态", 1)
new_report = report.replace(U_CELL_OLD, u"U-31 … U-1587（R432 现读抬到最新一节）", 1)
new_report = new_report.replace(u"AGENT_STATE.md` 的 R431 节 ②",
                                u"AGENT_STATE.md` 的 R432 节 ②", 1)
new_report = new_report.rstrip() + "\n\n" + R432_REPORT_BULLET + "\n"

wr(AUDIT, new_audit)
wr(ITER, new_iter)
wr(DECISIONS, new_decisions)
wr(CHANGELOG, new_changelog)
wr(BACKLOG, new_backlog)
wr(STATE, new_state)
wr(REPORT, new_report)
print("LEDGERS_R432_OK audit=%d iter=%d decisions=%d changelog=%d backlog=%d state=%d report=%d"
      % (len(new_audit), len(new_iter), len(new_decisions), len(new_changelog),
         len(new_backlog), len(new_state), len(new_report)))
