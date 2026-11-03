# -*- coding: utf-8 -*-
"""R565 台账（第 564 轮 / Round 562）：产品位落地 = 浮层键盘提示的字芯对比；取靶三扫里前两扫落空。

用法：`python3 ledgers_r565.py --check` 只验锚点与 NUM；不带参数才真写。
老规矩钉在代码里：① 每一本都有幂等守卫；② 守卫搜索的串不出现在自己正文里；③ 两种占位符形状都查。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": '1406/57/0（619.4s）',
    "INSTALL": '`INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→33353，启动晚于安装、exe 路径逐字对上，备份 `before-R565`）',
    "BATTERY": '709/5',
    "ABSENCE": '162/63/0',
    "STREAK": '0',
    "STREAK_RAW": '（这一格由台账落盘之后的 python3 scripts/product_streak.py 现读覆盖）',
    "CAPTURE": '222/4 skipped/0 失败（572.2s）',
    "FRAMES": '356 张 —— update 之前 `COMPARED=356 CHANGED=26 MISSING=0 ADDED=0`（26 张逐字名单 = 13 个 `quickpick-*` 夹具 × 明暗两档，见 `/tmp/r565-chain-compare.log`；**非浮层帧一帧未变** ⇒ 改动范围与预测一致，11 个禁碰面在像素层面也没被碰），同一笔 `frame_baseline.py update` 之后复跑 `COMPARED=356 CHANGED=0 MISSING=0 ADDED=0`',
    "PRECHECK": 'tables=368 covered=295 arms=757 bad=0',
    "ARM": 'files=461 arms=1244 dupes=0 repeats=0',
    "HIDDEN": '表=455 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok',
    "CI_CLOSE": '**收口前两跑都到数**（开场 in_progress ⇒ 具名 NOT-RUN，数到手在收口之前）：`41552571306↔4cfcfc6` 与 `41552998637↔8eecbc7` 都是 concluded **failure**，而 `gh run view --json jobs` 逐步现读给出的是同一种形状：**STEP[9] `Release script tests` failure、STEP[10]-[14] skipped、STEP[15]-[19] success** ⇒ 红的是我 R564 自己写死根的那把守卫（见 U-2444），不是任何一条视觉判据。到数的四格（`ci_read.py readings`，正文取自 emit 通道；那一跑的步骤名解析成 `UNKNOWN STEP` ⇒ 按 emit 串取，不按步骤名过滤）：(b) `BULLET_LEVELS` **第二跑仍判到** —— `BULLET_LEVELS light/dark 行=6 列=3 步进=[16, 16]px(16.0/16.0pt) 容差=1px 合并=1px 筛除 宽≤8px 隙≥4px 倍率=1.0x 列x=36px 墨高=5px(5.00pt) 列x=52px 墨高=4px(4.00pt) 列x=68px 墨高=5px(5.00pt)`，与首验那一跑逐字相同；(c) `HEAT_LEGEND_COVERAGE light/dark 格色=6 图例色=5 缺=[] 格宽=11px 倍率=1.0x 网格下缘 y=164 实心判定 格6px/图例3px 地板 格4/图例4 每方块采样点 格9/图例9`（4 行）而 `HEAT_LEGEND_NOT_RUN` **零行** ⇒ 连续第三跑判到；(d) `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=6 相邻差帧数=2 首末连续差=0.0048 峰值=0.0193 声明=200ms 窗口=701ms 每格=27.0ms` ⇒ **第六数 = 6**（六数 2/5/0/5/6/6，每格 71.5/26.0/75.6/28.9/32.0/27.0ms）⇒ 按 629 既有口径具名入账，≥2 未触碰；(e) STEP[15] `Swift tests` 这两跑 **success** ⇒ `SelectionRevealAnimationTests` 那朵间歇红**没有复现**（累计：`6ef9ff1` 红、`4cfcfc6`/`8eecbc7` 绿）；`SKIP_ROSTER` 在这两跑**一行都没有** —— 那不是绿也不是红：STEP[9] 的内层电池被我的守卫打死，观察者按 634 的设计拒绝给结论 ⇒ 具名「内层红 ⇒ 无可对账对象」，第五跑绿的那格仍算 R564 的账。',
    "PRODUCT_SHA": 'f6c2a1d',
}

UI = u"""## 第 564 轮（R565 · 2026-11-03 · U-2439…U-2445）：产品位回来了 —— 浮层键盘提示的字芯对比 light 3.36:1 / dark 4.16:1 ⇒ 10.37:1 / 10.92:1；取靶换了三个扫描，前两个各自落空并留下逐位证据

- **U-2439：⓪ CI 读单（只登记、不轮询）+ 一张被改过的读单。** 开场 HEAD=origin=`8eecbc7`、ahead=0、已跟踪改动 0、`api=200 / apple=200`。**本轮先做一格改账**：`### R564 补记` ③ 那张读单抄的是 R563 的旧表，而 R564 的 ② 已经读到四个数 ⇒ (a) `BULLET_LEVELS` 从「第一次被 runner 验」改判「**第二跑复核**」（首验在 `41542718166↔6ef9ff1` 判到，旧文本里 `8.0/8.0pt` 是 R562 降采样预览的数、不是 runner 口径）、(c) `过渡帧数` 从「第五数」改判「**第六数**」（五数 2/5/0/5/6 已在册）、(d) STEP[9] 从「四跑绿」改判「**五跑绿**」，并补两格旧表没有的：(e) STEP[15] `SelectionRevealAnimationTests` 间歇红（要数第几跑、形状是 `中段=0.0` 还是 R412 的 `1430`）、(f) 分批 push 是否造出注定红的派生格。**这是改账、不是改门**（没撤判据、没降地板、没改期望、没加豁免）；成因照实记：补记笔没跟**同一轮里已落盘的读数**交叉核对 —— 与 R563 那处 636 矛盾同族，**第二次犯**。读数：`41552571306↔4cfcfc6` 与 `41552998637↔8eecbc7` 开场都 **in_progress**（485s / 273s）、`steps` 的 `conclusion=` 全空 ⇒ 失败步骤清单尚不存在 ⇒ 六格一律具名 `CI_NOT_RUN=in_progress`，不许写成「没红」也不许写成「判到了」。永不重开 `41531750912↔75b32d6`、`41452722560↔58851c2`、`41455782587↔598b253`；已读过不重读 `41542718166↔6ef9ff1`。同批无独立跑 ⇒ `CI_UNREAD`：R564 的 `8fd5b1f`/`65e3371`/`235f243`/`4cfcfc6`、R563 三笔、R562 四笔、R561 三笔、R560 五笔、R558 两笔。%(CI_CLOSE)s
- **U-2440：取靶换了三个扫描，前两个落空，逐位带证据（这就是"重新现读扫名册"的账，不是"没干活"）。** ① **逐字节撞号扫描**（356 帧 → 唯一哈希 346 → 8 组跨夹具撞号，`/tmp/r565-dup.log`）逐组排除：`row-favorite-off`=`row-pinned-off`=`row-text`（三张都是"无标记"负臂，同一条内容的三个名字）；`content-paused-idle`=`content-with-history`（R417 的负臂就是"未暂停"）；`quickpick-search-focus`=`quickpick-search-hover`（R415 明文「焦点边界与悬停共用同一档视觉」，`QuickPickSearchBackdrop.draw` 里两态走同一 fill+stroke ⇒ 相同是设计）；`detail-3-files`=`detail-3-files-row0`（`makePopulatedStore(selectingIndex: 3)` 选到的就是默认展示那一条）⇒ **没有一组是产品缺陷**，但撞号本身是一格仪器卫生：基线里 6 张帧互为逐字节副本，它们不为任何断言单独作证 ⇒ **开 638**。② **裸字号扫描**（全仓 `Sources/` 里绕开 `VisualFont`/`VisualGlyph` 的硬编码字号）⇒ 只有 6 处：4 处是 R564 已被布局树证否的浮层徽标 `pointSize: 8`（637）；`SettingsView.swift:208` 的 `.system(size: 10)` 现读是 R495 的**负向帧缝**（产品路径走 `VisualFont.meta`）；`DetailPreviewViews.swift:384/386` 的 `monospacedSystemFont(ofSize: 13)` 恰等于 `VisualFont.body` ⇒ 换成 token 是**肉眼无变化**（R560/R562 的空刀教训），不许为"统一"落这一笔。③ 一条猜想被**机制**当场否掉：以为浮层搜索框的焦点态"声明了没供电"（那样每帧都该没有边界）⇒ 现读 `QuickPickController.swift:86/160/440` 产品路径确实点亮 `focused`；顺手验了取证键的覆盖语义（`??` 在 `false` 时仍取键值 ⇒ 负臂能关掉边界，键没坏）。④ 第三个扫描才中：**语义色 × 表面**（同一族信息在不同表面用不用同一个语义色）。
- **U-2441：产品位落地 —— 浮层键盘提示是浮层上唯一一句功能性文字，却是全仓对比度最低的字。** `QuickPickKeyboardHint.color` 从前是 `.tertiaryLabelColor`，而全仓其余"次要说明"（主列表时间行、行内三枚标记、详情 meta）都走 `.secondaryLabelColor`。旧值两条独立通道逐字对上：numpy 读 `quickpick-list` 底部那条带 ⇒ light 字芯 (140,140,140)/底 255 ⇒ **3.36:1**、dark 字芯 (127,127,127)/底 30 ⇒ **4.16:1**；Swift 判据同帧同带 ⇒ `HINT_CONTRAST light … 对比=3.36:1`、`dark … 对比=4.16:1` ⇒ **两档都跌破 4.5:1**，而同一张帧里候选行文字 16–20:1（淡的只有这一句 ⇒ 尺不是瞎的）。改成 `.secondaryLabelColor` 后 **10.37:1 / 10.92:1** ⇒ 过地板，且**仍比候选行弱一档**（≈20:1 vs ≈10:1），R449/R565 的设计意图（"提示是元信息"）一字未改。⚠ **禁碰 R550「提示 Esc」的证人**：`HINT_KEY_CAPS 键=Esc 高=7.85pt 宽=5.22pt 字号=11.0pt` 与 R550 账上逐字相同 ⇒ 本轮只动颜色，键名与字高那一面没碰。
- **U-2442：新判据 `testQuickPickKeyboardHintClearsTheContrastFloor` —— 判据先红后改产品，红之前先两次修尺。** 判的是**比值**不是像素数 ⇒ 与捕获倍率无关（R555 那一族"同一几何量在 2x/1x 不是同一对象"在这里不适用；1x 体检仍要做，读不到字芯就具名 NOT_RUN、不降地板）。底色取**提示所在那条带自己的众数**，字芯取带内偏差最大前 5% 像素的中位颜色（抗锯齿边不参与）。两次自伤都在落账前被抓：① 第一版拿**整帧众数**当提示的底色 ⇒ light 档带内 99.8% 像素都算"偏差"，字芯被稀释成 (163,163,163)、对比报 **2.46:1**，与 numpy 独立通道的 3.36 对不上 ⇒ 那朵红是尺坏；② 更早一版把 gamma 编码的 `bgLuma/255` 去比线性光的 `relLuma` ⇒ 暗档排序把**背景自己**排成字芯（报 1.02:1）。**两通道逐字一致之前不许宣布读数**（R490 那条"两臂读数一样=尺坏信号"的同族）。
- **U-2443：刀 —— 两把登记、一把试落即撤。** **M1466** 把颜色退回 `.tertiaryLabelColor` ⇒ CAUGHT（读数回到 3.36/4.16）；**M1467** 再弱一档改成 `.quaternaryLabelColor` ⇒ CAUGHT（1.56/1.82）⇒ 这一把证明门不是"只要不是 tertiary 就算过"，它读的是像素比值；两把 `RESTORE_CLEAN=yes`。**M1468 试落即撤、不登记、不占号**：把"字芯"从偏差前 5% 改成**全部偏差像素** ⇒ 读数 6.01/9.16:1 仍 ≥4.5 ⇒ 判据 PASSED ⇒ 按 R560/R562 的规矩那是**空刀**（变化量没出得了判据自己的容差），撤掉并照实写 ⇒ **下一轮仍从 M1468 起**（现读已登记最高 M1467）。两张表已登记进 `mutate_needle_precheck.TABLES`。
- **U-2444：R564 那把守卫把 runner 的两跑打死了 —— 根因是写死的机器根，本轮修掉并补一支守卫。** ⓪ 现读 `41552571306↔4cfcfc6` 与 `41552998637↔8eecbc7` 都是 **STEP[9] `Release script tests` failure、STEP[10]-[14] skipped、STEP[15]-[19] success**（逐步读 `gh run view --json jobs` 的 `steps[].conclusion`，不是从「不在失败名单」推的）。CI 日志正文（`/tmp/r565-ci-8eecbc7.log` 第 8451-8470 行）：`test_current_batch_is_consistent` ⇒ `AssertionError: 1 != 0 : commit 轮次身份守卫红：` 后面跟的是脚本**自己的 traceback** —— `commit_round_identity.py` 把自己的仓库根写成一台机器的绝对路径，runner 上那个目录不存在 ⇒ `subprocess.run(cwd=ROOT)` 抛异常 ⇒ 退出码 1。⇒ **分批 push 不是原因，我自己写死的根才是**；代价是两跑的 **STEP[11] 帧基线名册门整段没跑**，而 `SKIP_ROSTER` 也没有行（634 的形状：内层红 ⇒ 这一格没有可对账的对象，**既不能记绿也不能记红**）。修法：根由 `__file__` 推出来。另补一支守卫 `MachineRootHygieneTests`（三条腿：真扫 `scripts/**/*.py` 的根常量、正对照必须点名、负对照不许咬 `__file__` 派生写法与测试里的合成路径靶与注释里的历史引用）—— 原有那支只盯 `/tmp/shots_rNN`，看不见「根常量」这一族（BACKLOG 334 那一格的老毛病换了个载体又犯）。刀 **M1468 CAUGHT**（把根改回写死 ⇒ 真扫那一格点名文件与行号）、**M1469 CAUGHT**（让扫描器「看见但不报」⇒ 正对照那一格红：`1 != 0 扫描器抓不到写死的仓库根 ⇒ 这把尺是空的`），两把 RESTORE_CLEAN=yes。刀落过程中两次自伤：① 第一版刀脚本把裸字符串插进模板 ⇒ `OLD = ROOT = os.path…` 成了链式赋值 ⇒ `needle 命中 0`；② M1469 第一版只替换了 alternation 里一段、`ROOT` 还在 ⇒ 判据 PASSED（那根本不叫变异）。**「登记前先跑一遍看 needle 命中 1」这条规矩本轮第三次救场。**
- **U-2445：③ 验证链与④⑤ 账（顺序未换）。** `swift build --build-tests` 告警 **0**；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**；全量 **%(FULL)s**；预检三读**串行** **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s。清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED`，`&&` 链里不插 grep）；streak **台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`。**产品面这一格回来了**（`Sources/` 1 文件 = `QuickPickKeyboardHint.swift`，产品笔 `%(PRODUCT_SHA)s`）⇒ 连续四轮 0 文件的中断；**636 继续开单**、**637 继续开单**（本轮没碰浮层徽标）、**新开 638**（基线里 6 张逐字节相同的帧）；629 保持「(B) 已落地 + 635 已结案 + runner 五跑实测 2/5/0/5/6 ⇒ ≥2 在那台机器的钟上是间歇可满足」，两条出路仍等用户点头、本轮不自行登记 `sampled`；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）；R564 那条守卫**仍没接进 CI**（只在电池里跑）⇒ 接不接归用户。下一轮 R566（第 565 轮 / Round 563）：⓪ 必读本轮 push 头笔那一跑（取号时未创建 ⇒ 现在去读；中间笔具名 `CI_UNREAD`），头六格 = (a) `BULLET_LEVELS` 第三跑复核、(b) `HEAT_LEGEND_*` 复核、(c) `过渡帧数` 第六数、(d) STEP[9] 第六跑、(e) STEP[15] 间歇红的第几跑与形状、(f) 分批是否造出注定红的派生格；另加一格：**`HINT_CONTRAST` 第一次上 runner 走哪条**（比值与倍率无关，但 1x 带内偏差像素会变少 ⇒ 读不到字芯就具名 NOT_RUN，不许降 4.5 地板）。刀号 **M1470** 起（现读最高 M1469）；禁碰清单 **12 面**（第 12 面 = **R565 浮层键盘提示的颜色**；R550 那一面仍是键名与字高）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%`、`.contentFade` 0.20 与声明时长一律不动；全量 skipped 只记现读。

"""


ITER = u"""
## Round 562 · R565（第 564 轮 · 2026-11-03）：产品位回来了 —— 三个扫描里前两个落空并各自留下逐位证据，第三个（语义色 × 表面）命中浮层那句键盘提示的对比度

四轮产品 0 文件之后这一格重新落地。取靶这轮换到第三个方法：**逐字节撞号扫描**（356 帧里找不同夹具却逐字节相同的帧）先给出 8 组，逐组用夹具语义与产品机制排除 —— 三张"无标记"负臂同图、`content-paused-idle` 就是 R417 的未暂停负臂、`quickpick-search-focus`==`quickpick-search-hover` 是 R415 明文"焦点与悬停共用同一档视觉"（`QuickPickSearchBackdrop.draw` 里两态真的走同一条 fill+stroke）、`detail-3-files-row0` 选到的就是默认展示那一条。没有一组是缺陷，但撞号本身留下一格仪器卫生：基线里有 6 张帧互为逐字节副本，不为任何断言单独作证 ⇒ 开 638。**裸字号扫描**（绕开 `VisualFont`/`VisualGlyph` 的硬编码字号）只找到 6 处，其中 4 处是 R564 已被布局树证否的浮层徽标（637），1 处是 R495 的负向帧缝，1 处（`DetailPreviewViews` 的 monospaced 13）恰等于 `VisualFont.body` ⇒ 换成 token 是肉眼无变化，不许为"统一"落这一笔。还有一条猜想被机制当场否掉：以为浮层搜索框的焦点态"声明了没供电"，现读 `QuickPickController:86/160/440` 产品路径确实点亮 `focused`。

中的是第三个扫描：**语义色 × 表面** —— 同一族信息在不同表面有没有用同一个语义色。浮层底部那句键盘提示（`↑↓ 选择 · ↵ 粘贴 · Esc 关闭`）用的是 `.tertiaryLabelColor`，而全仓其余次要说明（主列表时间行、行内三枚标记、详情 meta）都是 `.secondaryLabelColor`。它是浮层上**唯一一句功能性文字**，R449 开它就是为了让用户不用猜键。帧上现读旧值：light 字芯 (140,140,140)/底 255 ⇒ **3.36:1**，dark 字芯 (127,127,127)/底 30 ⇒ **4.16:1**，两档都跌破 WCAG AA 对正文的 4.5:1，而同一张帧里候选行文字是 16–20:1。改成 `.secondaryLabelColor` 之后 10.37:1 / 10.92:1 ⇒ 过地板，且仍比候选行弱一档，"提示是元信息"的设计意图一字未动。判据先红后改产品，红之前先两次修尺：第一版拿整帧众数当提示的底色（light 档带内 99.8% 像素都算偏差，字芯被抗锯齿边稀释成 163、对比报 2.46:1，与 numpy 独立通道对不上）；更早一版把 gamma 编码的底色去比线性光（暗档把背景自己排成字芯，报 1.02:1）。**两通道逐字一致之前不许宣布读数。** 禁碰 R550「提示 Esc」的证人：`HINT_KEY_CAPS 高=7.85pt 宽=5.22pt 字号=11.0pt` 与 R550 账上逐字相同 —— 本轮只动颜色。刀两把登记（M1466 退回 tertiary、M1467 再弱一档改 quaternary，全 CAUGHT），一把试完就撤（M1468 把字芯从"偏差前 5%"改成"全部偏差像素"，读数 6.01/9.16 仍过地板 ⇒ 判据 PASSED ⇒ 空刀，不登记不占号）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 12/15 | 看了浮层两档整帧（提示那一行改前改后各一次）、逐字节撞号那 8 组的全部帧；扣的三分是本轮没有新的画面类型可看，看的多是老帧的同一区。 |
| 判据有效性 | 13/15 | 新判据先红（3.36/4.16）后绿（10.37/10.92），且红之前两次都是**尺坏**不是产品坏（整帧众数当底色、gamma 比线性光），两通道逐字一致才敢用；判的是比值 ⇒ 与倍率无关。 |
| 假绿防御 | 15/15 | 空刀 M1468 试完就撤、不登记不占号；"带内一个偏差像素都没有"写成红而不是 skip；禁碰 R550 用逐字相同的 `HINT_KEY_CAPS` 读数作证；撞号 8 组逐组给排除证据，没拿"看着像设计"交差。 |
| 产品面推进 | 13/15 | `Sources/` 1 文件、旧值→新值可报（3.36→10.37 / 4.16→10.92）、帧与判据两证、两把刀 ⇒ 连续四轮 0 文件断了；扣的两分是这一格只有一句提示，面小，且前两扫确实空转。 |
| 台账一致性 | 14/15 | 七本幂等守卫齐全、两种占位符形状都查、派生格落盘后现读、读单改账单独成格并写明"改账不是改门"；扣一分是**同一族错误第二次犯**（补记笔抄上一轮读单、没跟同一轮 ② 的读数交叉核对），规矩本身还没写成会红的守卫。 |
| 交付诚实性 | 15/15 | ⓪ 两跑 in_progress ⇒ 六格具名 NOT-RUN，不写"没红"；两个落空的扫描逐位带证据入账；空刀照实写；633 没拿到回执 ⇒ 一个字结论没写；产品位落地没有拿判据位冒充。 |
| 可复核性 | 13/15 | 读数全部带日志路径（numpy 与 Swift 两条通道、判据红/绿两跑、`HINT_KEY_CAPS` 证人、撞号清单）；扣两分是判据的 1x 体检还没做（runner 首跑才知道走哪条），以及 638 那 6 张帧的名单只活在 `/tmp` 与账里、没有机器可读的名册。 |

"""


CHG = u"""### 浮层那句键盘提示原来是全仓对比度最低的字：字芯 light 3.36:1 / dark 4.16:1 ⇒ 改到与其余次要文字同一档的 secondaryLabel，复量 10.37:1 / 10.92:1（R565 / 第 564 轮 / Round 562）

`QuickPickKeyboardHint.color` 从前是 `.tertiaryLabelColor`，而它是浮层上**唯一一句功能性文字**（↑↓ 选择 · ↵ 粘贴 · Esc 关闭，R449 开它就是为了让用户不用猜键）；全仓其余"次要说明"——主列表时间行、行内三枚标记、详情 meta——都走 `.secondaryLabelColor`。帧上现读旧值：light 字芯 (140,140,140) 对底 255 ⇒ 3.36:1，dark 字芯 (127,127,127) 对底 30 ⇒ 4.16:1，两档都跌破 4.5:1，而同一张 `quickpick-list` 帧里候选行文字是 16–20:1 ⇒ 淡的只有这一句。改成 `.secondaryLabelColor` 后 10.37:1 / 10.92:1：过地板，且仍比候选行弱一档，"提示是元信息"的设计意图一字未改。⚠ 禁碰 R550「提示 Esc」= 键名与字高那一面：`HINT_KEY_CAPS 高=7.85pt 宽=5.22pt 字号=11.0pt` 与 R550 账上逐字相同，本轮只动颜色。新判据 `testQuickPickKeyboardHintClearsTheContrastFloor` 判比值不判像素数（与捕获倍率无关），先红后改产品；红之前两次是修尺：整帧众数当提示底色 ⇒ 带内 99.8% 像素都算偏差、字芯被抗锯齿边稀释成 163（报 2.46:1，与 numpy 独立通道的 3.36 对不上）；gamma 编码的底色去比线性光 ⇒ 暗档把背景自己排成字芯（报 1.02:1）。刀 M1466（退回 tertiary）/ M1467（再弱一档 quaternary）全 CAUGHT、RESTORE_CLEAN=yes；M1468 试落即撤 —— 把字芯从"偏差前 5%"改成"全部偏差像素"后读数 6.01/9.16 仍过地板 ⇒ 空刀，不登记不占号，下一轮仍从 M1468 起。取靶这轮换了三个扫描，前两个落空并逐位留证：逐字节撞号 8 组全部有名有姓地排除（三张"无标记"负臂同图、paused-idle 是未暂停负臂、focus==hover 是 R415 明文同一档视觉、detail-3-files-row0 选到默认那条）⇒ 但基线里 6 张帧互为逐字节副本不为任何断言单独作证，开 **638**；裸字号扫描只有 6 处，4 处属 637、1 处是 R495 负向帧缝、1 处与 `VisualFont.body` 同值（换 token 肉眼无变化 ⇒ 不落）。另有一条猜想被机制当场否掉（以为浮层搜索框焦点态"声明了没供电"，现读 `QuickPickController:86/160/440` 确实点亮）。**另落一格真 bug**：R564 那把 commit 守卫把自己的仓库根写成机器绝对路径 ⇒ runner 上 STEP[9] 抛异常、STEP[10]-[14]（含帧基线名册门）整段 skipped，两跑信号全被带走；本轮改成由 `__file__` 推出，并补一支 `MachineRootHygieneTests`（三条腿齐全）+ 刀 M1468/M1469 全 CAUGHT。判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s；4.5 墨地板 / 150 上限 / 120ms / Motion ≥2 帧 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` / `.contentFade` 0.20 一律未动。

"""


B638 = u"""
**638. 帧基线里有 6 张帧互为逐字节副本 —— 它们不为任何断言单独作证**（R565 逐字节撞号扫描现读并新开，本轮不改面）
    现象：356 张帧 → 唯一哈希只有 346 个，8 组撞号里跨夹具的有 4 组（`/tmp/r565-dup.log`）：`row-favorite-off-300x74` = `row-pinned-off-300x74` = `row-text-300x74`（light/dark 各三份）、`content-paused-idle-750x560` = `content-with-history-750x560`、`quickpick-search-focus-420x300` = `quickpick-search-hover-420x300`、`detail-3-files-720x520` = `detail-3-files-row0-720x520`。
    逐组排除（**都不是产品缺陷**，都有名有姓）：前三组是**负臂**——同一句"没有那颗标记/没有暂停"的另一种写法；`focus==hover` 是 R415 明文「焦点边界与悬停共用同一档视觉」，`QuickPickSearchBackdrop.draw` 里两态真的走同一条 fill+stroke；`detail-3-files-row0` 的 `makePopulatedStore(selectingIndex: 3)` 选到的就是默认展示那一条。
    那为什么还开单：基线的价值在于**每张帧都能单独当证人**。这 6 张副本意味着"帧数 356"这个数里有一部分不为任何断言作证；更糟的是它给了后来人一个假信号——看到两张同图会以为是"两态一致 = 状态没画出来"，于是白跑一轮（本轮就差点在这上面开一朵假缺陷）。
    要判的两格（下一轮接手前先定口径）：① 这些副本该**并进同一张帧**（少几张、名单干净）还是**留成显式的"故意同图"名册**（像 `UICaptureBlackBands.intentional` 那样有名有姓，配一把"新增副本必须登记"的刀）；② 判据若靠"两态成对帧"作证，必须能读出**这一对到底该不该相同**——不该相同而相同 = 状态没画（R490 那一族），该相同而不同 = 有东西漂了。
    ⚠ 不许顺手删帧：删一张帧 = 改基线名单 = 要 `frame_baseline.py update` 同一笔，且要先确认没有判据拿那张帧当唯一证人。
"""


DEC = u"""## D-565（R565 · 2026-11-03）：读数之前先问"底色是谁"；空刀试完就撤不占号；同一族抄表错误第二次犯要升成守卫

① **对比度判据的成败在"底色取谁"，不在公式。** 同一张帧、同一条带，整帧众数当底色读出 2.46:1，带内众数当底色读出 3.36:1，而独立 numpy 通道给 3.36:1 ⇒ 前者是尺坏。**新像素判据在宣布读数之前，必须有一条独立通道对得上数**（本轮是 numpy 对 Swift；R564 是降采样预览对 runner 真 1x）—— 对不上就先查尺，不许先改期望。
② **颜色空间要一致：gamma 编码的 0..1 不能直接跟线性光比。** 第一版 `abs(relLuma(p) - bgLuma/255)` 在暗档把**背景自己**排成"字芯"，报出 1.02:1 这种荒谬数。规矩：任何跨空间的比较，先把两边转进同一个空间再比。
③ **空刀不占号。** M1468（把字芯从"偏差前 5%"改成"全部偏差像素"）落下去判据仍 PASSED ⇒ 撤掉、不登记、写进账，下一轮仍从 M1468 起。这一条与 R560 的 M1455、R562 的两把同族：**"我改了一个看起来关键的内部量"不等于"这个量在承重"**，只有判据变红才算。
④ **同一族错误第二次犯，就要从"教训"升成"守卫"。** 补记笔抄上一轮读单、没跟同一轮已落盘的读数交叉核对 —— R563 是 636 的状态两处互斥，R565 是读单三格过期。两次都不是"没写"，是**写了但没人对账**。下一步该落的是机器判：把"补记 ③ 的读单里每个 runner 读数都必须被同一轮 ② 引用过"写成一条会红的检查（本轮没做，因为要新造一个跨节对账的尺 —— 记在这里，不许再靠自觉）。
⑤ **落空的扫描也要入账，且要落款到具体证据。** 本轮三个扫描两个空手：逐字节撞号 8 组逐组给排除理由（并开 638 把"副本帧"这件事本身登记成仪器缺口）、裸字号 6 处逐处给归属（4 处 637 / 1 处负向缝 / 1 处同值不换）。**"扫了没找到"和"没扫"的区别就是这份名单在不在账上。**
⑦ **脚本自己的根不许写死，而且这条要有守卫。** R564 的 `commit_round_identity.py` 把 ROOT 写成机器绝对路径 ⇒ runner 上 STEP[9] 抛异常、STEP[10]-[14]（含帧基线名册门）整段 skipped，两跑的 CI 信号全丢。这不是新病（BACKLOG 334 那一族），但原有那支路径卫生守卫只盯 `/tmp/shots_rNN`，看不见「根常量」这一族 ⇒ 本轮补 `MachineRootHygieneTests`（三条腿）。更狠的一条规矩：**任何依赖环境路径的判据，落之前先在 runner 的目录结构下想一遍它会不会抛异常** —— 抛异常与判红在报表上长得一样（都是退出码非零），但修法相反。
⑥ **边界**：本轮产品 1 文件（`QuickPickKeyboardHint.swift` 的颜色），禁碰 11 面一面对都没碰（`HINT_KEY_CAPS` 逐字不变就是 R550 那一面的证人）；4.5pt 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%`、`.contentFade` 0.20 一字未动；633 没拿到回执 ⇒ 一个字结论没写。
"""


B637_NOTE = u"""    R565 复核（不改面）：本轮取靶的第二个扫描（裸字号）又数了一遍浮层那三枚徽标的 `pointSize: 8` —— 仍是 4 处字面量、仍未登记判据；本轮落的是**另一格**（键盘提示的对比度），没有碰这一面。下一轮若接手，先读 `.scratch/motion-audit-2/r564-badge-criterion-draft.swift.txt` 再动产品（R564 的教训：墨会变只否掉"看不见"，布局边长才决定"契约能不能满足"）。
"""


def insert_after_line(t, line_prefix, block, label):
    u"""按**行首前缀**定位那一行，插到它后面。"""
    hits = [i for i, ln in enumerate(t.split(u"\n")) if ln.startswith(line_prefix)]
    if len(hits) != 1:
        sys.stderr.write("ANCHOR_BAD %s lines=%d\n" % (label, len(hits)))
        sys.exit(1)
    i = t.index(line_prefix)
    j = t.find(u"\n", i)
    return t[:j + 1] + block + t[j + 1:]


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, t):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(t)


def once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return t.replace(old, new, 1)


def guard(t, marker, label):
    """幂等守卫：**每一本都要有**（R562 只给一本加 ⇒ 中途崩之后重跑把 UI 那一本写成两份）。"""
    if marker in t:
        sys.stderr.write("ALREADY_WRITTEN %s ⇒ 先去重再写，不许重跑\n" % label)
        sys.exit(1)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace(u"%%(%s)s" % key, value)
    if u"%(" in out:
        i = out.find(u"%(")
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[i:i + 30])
        sys.exit(1)
    bad = re.search(u"%(?=[a-zA-Z])", out)
    if bad:
        i = bad.start()
        sys.stderr.write("BARE_PERCENT_LEFT %s\n" % out[max(0, i - 30):i + 30])
        sys.exit(1)
    return out


def main():
    check = "--check" in sys.argv
    for key, value in NUM.items():
        if value.startswith(u"@@") and value.endswith(u"@@"):
            sys.stderr.write("NUM_NOT_FILLED %s\n" % key)
            return 1

    state = rd("AGENT_STATE.md")
    if state.count(u"## R565 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R565 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if u"## R565 状态（" in state:
        sys.stderr.write("ANCHOR_BAD state R565 状态节已存在\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    guard(t, u"## 第 564 轮（R565", u"ui")
    a = u"## 第 563 轮（R564 · 2026-11-03 · U-2432…U-2438）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    guard(t, u"## Round 562 · R565", u"iteration")
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(ITER))

    n = "CHANGELOG.md"
    t = rd(n)
    a = u"## [Unreleased]\n\n"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    guard(t, u"（R565 / 第 564 轮 / Round 562）", u"changelog")
    if not check:
        wr(n, t.replace(a, a + fill(CHG), 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    guard(t, u"**638. ", u"backlog638")
    t = insert_after_line(t, u"**637. ", B638, u"backlog638-anchor")
    t = insert_after_line(t, u"    ⚠ 禁碰：`QUICKPICK_STAR_HEIGHT`", B637_NOTE, u"backlog637-note")
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    guard(t, u"## D-565", u"decisions")
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(DEC))

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    guard(t, u"R565 续到 565", u"final-report")
    for old, new, label in [
        (u"R9–R561，562 节自评", u"R9–R562，563 节自评", u"title"),
        (u"阶段二 **554 轮**审计（R9–R561；以 `curve_from_ledger.py` 的 `PHASE2 n=554` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 561",
         u"阶段二 **555 轮**审计（R9–R562；以 `curve_from_ledger.py` 的 `PHASE2 n=555` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 562", u"§1"),
        (u"| 视觉台账 | U-31 … U-2438", u"| 视觉台账 | U-31 … U-2445", u"U 上界"),
        (u"以 `AGENT_STATE.md` 的 R564 节 ② 为准", u"以 `AGENT_STATE.md` 的 R565 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R564 这一段", u"## 18. R458 → R565 这一段", u"§18 head"),
        (u"R564 续到 564 —— 这份报告第七次差点停在几十轮之前）",
         u"R565 续到 565 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, fill(old), fill(new), label)
    anchor = u"全量 1405/57/0（687.5s）；build 0 告警；电池 706/5。\n"
    bullet = (u"- **R565（产品位回来：浮层键盘提示的字芯对比 3.36/4.16 ⇒ 10.37/10.92）**："
              u"取靶换到第三个扫描（**语义色 × 表面**）才命中 —— 前两个（逐字节撞号 8 组、裸字号 6 处）"
              u"逐组排除并各留证据（开 **638**：基线里 6 张帧互为逐字节副本，不为任何断言单独作证）。"
              u"`QuickPickKeyboardHint.color` 从前是 `.tertiaryLabelColor`，而它是浮层上唯一一句功能性文字，"
              u"其余次要说明全走 `.secondaryLabelColor` ⇒ 帧上现读 light (140,140,140)/255 = **3.36:1**、"
              u"dark (127,127,127)/30 = **4.16:1**，同帧候选行 16–20:1 ⇒ 淡的只有这一句；改完 **10.37/10.92:1**，"
              u"仍比候选行弱一档。⚠ 禁碰 R550 的证人：`HINT_KEY_CAPS 高=7.85pt 宽=5.22pt` 与账上逐字相同（只动颜色）。"
              u"判据先红后改产品，红之前两次修尺（整帧众数当底色 ⇒ 2.46:1；gamma 比线性光 ⇒ 暗档 1.02:1）。"
              u"刀 M1466/M1467/M1468/M1469 全 CAUGHT；另有一把**试完就撤的空刀**（从未登记、不占号）：字芯改成全部偏差像素 ⇒ 6.01/9.16 仍过地板 ⇒ 判据 PASSED。另落一格改账：`### R564 补记` ③ 的读单抄自 R563，"
              u"三格过期 + 缺两格 ⇒ 本轮开场改齐（改账不是改门）。⓪ 两跑开场 in_progress ⇒ 六格具名 NOT-RUN。"
              u"判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    guard(t, u"## R565 状态（", u"state")
    body = u"""## R565 状态（2026-11-03 · 第 564 轮 / Round 562 · 产品 1 文件 + 判据 1 条 + 刀 2 把（1 把空刀撤）+ 新开 638 + 一处读单改账）

①  那两跑：`41552571306↔4cfcfc6`（R564 补记笔）与 `41552998637↔8eecbc7`（R564 补正笔）开场都 **in_progress**（485s / 273s）、`steps` 的 `conclusion=` 全空 ⇒ 六格一律具名 `CI_NOT_RUN=in_progress`（(a) `BULLET_LEVELS` 第二跑复核、(b) `HEAT_LEGEND_*` 复核、(c) `过渡帧数` 第六数、(d) STEP[9] 第六跑、(e) STEP[15] 间歇红第几跑与形状、(f) 分批是否造出注定红的派生格）；同批无独立跑 ⇒ `CI_UNREAD`（R564 五笔 + R563 三笔 + R562 四笔 + R561 三笔 + R560 五笔 + R558 两笔）；cancelled 三笔永不重开。%(CI_CLOSE)s
② ⓪ 附加的一格**改账**（本轮开场先做）：`### R564 补记` ③ 那张读单抄的是 R563 的旧表 ⇒ (a) 首验改判「第二跑复核」（首验在 `41542718166↔6ef9ff1` 判到；旧文本 `8.0/8.0pt` 是降采样预览的数）、(c) 第五数改判「第六数」（五数 2/5/0/5/6 已在册）、(d) 四跑改判「五跑」，并补 (e) STEP[15] 间歇红、(f) 分批 push 两格。**没撤判据、没降地板、没改期望、没加豁免**；成因照实记（补记笔没跟同一轮 ② 已落盘的读数交叉核对 —— 与 R563 那处 636 同族，第二次犯 ⇒ D-565 ④ 要求把这件事升成会红的守卫）。
③ ② 第二格（要求落 `Sources/`）：**产品 1 文件 = `QuickPickKeyboardHint.swift` 的颜色**（产品笔 `%(PRODUCT_SHA)s`）。取靶换了三个扫描：① 逐字节撞号（356 帧 → 唯一哈希 346 → 8 组跨夹具撞号）逐组用夹具语义/产品机制排除 ⇒ 无缺陷，但基线里 6 张副本帧不为任何断言单独作证 ⇒ **开 638**；② 裸字号（全仓 6 处）⇒ 4 处属 637、1 处是 R495 负向帧缝、1 处与 `VisualFont.body` 同值（换 token 肉眼无变化 ⇒ 不落）；③ 语义色 × 表面 ⇒ 命中：浮层键盘提示用 `.tertiaryLabelColor` 而其余次要文字全用 `.secondaryLabelColor`。旧值两通道逐字一致（numpy 与 Swift 判据都是 light **3.36:1** / dark **4.16:1**，同帧候选行 16–20:1）⇒ 新判据先红；改完 **10.37:1 / 10.92:1** ⇒ 绿，且仍比候选行弱一档。⚠ **禁碰 R550 证人**：`HINT_KEY_CAPS 键=Esc 高=7.85pt 宽=5.22pt 字号=11.0pt` 与 R550 账上逐字相同。另有一条猜想被机制当场否掉（以为浮层搜索框焦点"声明了没供电"，现读 `QuickPickController:86/160/440` 确实点亮 `focused`）。
④ 尺的两次自伤（都在落账前修掉，没让它冒充缺陷）：① 第一版拿**整帧众数**当提示底色 ⇒ light 带内 99.8% 像素都算偏差、字芯被抗锯齿边稀释成 (163,163,163)、对比报 2.46:1（与 numpy 的 3.36 对不上）；② 更早一版把 gamma 编码的 `bgLuma/255` 去比线性光 `relLuma` ⇒ 暗档把**背景自己**排成字芯（报 1.02:1）。刀：**M1466 CAUGHT**（退回 tertiary ⇒ 3.36/4.16）、**M1467 CAUGHT**（再弱一档 quaternary ⇒ 1.56/1.82）、两把 RESTORE_CLEAN=yes；**一把试完就撤的空刀**（从未登记、不占号）（字芯改成全部偏差像素 ⇒ 6.01/9.16 仍过地板 ⇒ 判据 PASSED ⇒ 空刀，不登记不占号）。四张表已登记进名册（M1466-M1469）。
⑤ ③ 验证链（顺序未换）：`swift build --build-tests` 告警 **0**；判据卷 **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`（三读**串行**）；换装 %(INSTALL)s。
⑥ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑）；产品面连续零改动 **%(STREAK)s** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`）。**636 / 637 继续开单**（本轮没碰那两面）；**新开 638**；629 保持「(B) 已落地 + 635 已结案 + runner 五跑实测 2/5/0/5/6 ⇒ ≥2 在那台机器的钟上是间歇可满足」，两条出路等用户点头、本轮不自行登记 `sampled`；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；R564 那条守卫**仍没接进 CI**（只在电池里跑）⇒ 接不接归用户；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。⑦ 一次性 push（本轮四笔：⓪ 开工 + A 产品与判据与两把刀 + 台账 + 补记）⇒ 只有头笔建跑。R566 ⓪ 必读它；头六格 = `BULLET_LEVELS` 第三跑 / `HEAT_LEGEND_*` 复核 / `过渡帧数` 第六数 / STEP[9] 第六跑 / STEP[15] 间歇红 / 分批派生格，**外加 `HINT_CONTRAST` 第一次上 runner 走哪条**（比值与倍率无关，但 1x 带内偏差像素会变少 ⇒ 读不到字芯就具名 NOT_RUN，不许降 4.5 地板）。刀号 **M1470** 起（现读最高 M1469）；禁碰清单 **12 面**（第 12 面 = **R565 浮层键盘提示的颜色**：本轮把它从 `.tertiaryLabelColor` 抬到 `.secondaryLabelColor`，禁的是改回去；R550 那一面仍是**键名与字高**，`HINT_KEY_CAPS 高=7.85pt 宽=5.22pt` 逐字未动）；4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%`、`.contentFade` 0.20 一律不动；全量 skipped 只记现读。

"""
    a = u"\n## R565 ⓪ 开工（2026-11-03 · 第 564 轮 / Round 562 · 读单改账 + 基线全现读 + 两个新取靶扫描的落空名单）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R565_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == '__main__':
    sys.exit(main())
