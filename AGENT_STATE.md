# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-17 16:19（本地 · R112 / 第 114 轮收尾：**动效那一卷的红以前没有账** —— CI 那句「唯一的红是 157」只覆盖捕获那一卷（166 的 ① 落地 / U-370…U-373 / D-181 / 脚本电池 230 → 236））

**本轮是工具轮，产品 0 改动**（`git status --short ClipboardHistory/Sources` 计数 0；swift 侧一行未动 ⇒ 帧复用上轮那一份，136 张 `CHANGED=0`）。给 `scripts/ci_capture_gate.py` 加了 `--class-prefix`（按类名**最后一段**切、可重复）、`--label`（结论行按卷打）、`--report-only`（只降级产品那一格，通道坏了照旧红），并且**切片为空必须红**（`MOTION_SCOPE_EMPTY=1`，R99 那一族）；workflow 里新增一步 `Motion gate (report-only census, BACKLOG 166)`，读全量那一卷的 `/tmp/test.log`。

**两条只有真日志能给的发现**：① U-370 —— 第一版只切 `MotionFilmstrip`，而 `testFrameIntervalsUnderStateChanges` 住在 `UIInteractionProbeTests` ⇒ 拿 R109 的真日志跑会读成「0 红」，合成夹具永远给不出这一格；② U-371 —— 那朵红在 CI 日志里只有 `FAILED 方法名：XCTAssert…` 这一种形状，而闸门只认 `error: -[类 方法]` ⇒ **整朵看不见**（`ci_read.py` R105 就会认两种，闸门今天才补）。类名缺失的那种单列成「类未知名单」，于是 R109 = `有名字的红=0 类未知名单=1(testFrameIntervalsUnderStateChanges)`、R110 = `类未知名单=0` —— 166 的「换班」第一次变成两行可 grep 的读数。规矩进 **D-181**。

**为什么不直接升成硬门**：166 自己的判法是「单次读数不配给产品定罪」⇒ 第一版 report-only，升硬门要由**同一 commit 两跑的名单一致**签（`scripts/ci_red_stability.py`），不由印象签。

**另两条工具层的账**：U-372（用 python 生成 python 时把带 ASCII 双引号的 CJK 串写进 `help=` ⇒ 文件写成功而内容语法坏，`py_compile` 才抓到 —— 写盘不校验被写物）、U-373（把结论行字段 `NOT_RUN=` 改名 ⇒ 被自家真值表拦下：字段名是既有契约，口径只能写成附注）。本轮收尾时 U-372 **又犯一次**（同一个坑在一轮里踩两回，见下面 STATE 的下一轮入口）。

**验证**：脚本电池 `Ran 236 tests OK`（+6：切片四格、第二形状一格、空切片一格）；台账守卫 11 例 OK（本轮自己踩到定义行形状：`**U-370**：` 要写成 `**U-370：…**` 才算定义，正对照当场拦下）；曲线 `SCORES_BY_ROUND 109=90 110=91 111=92 112=91`。

**下一轮（R113）的入口**：① 读 R111 / R112 的 CI —— R112 那跑第一次会打 `MOTION_GATE_SCOPE` / `MOTION_GATE_CASES`，那是 166 第一份跨跑可比的账；② 名单在两跑之间一致才去掉 `--report-only`；③ 150 让臂 2 的详情在 runner 上有内容；④ 155 扩第三样本。

**仍然只有用户能做的**：批次 26.x–83.1、84.1、85.1、85.2。


> 上一轮（R111 / 第 113 轮收尾）原文开头：
> 最后更新：2026-10-17 16:04（本地 · R111 / 第 113 轮收尾：**12 的菜单只在两处同步填，而刷新是异步的 ⇒「正在整理推荐…」会挂到关菜单**（结案 165 / U-366…U-369 / D-180 / 变异表 r111 四刀 M602–M605 全 CAUGHT / pass-1 `VERIFY_OK=1`））
> 
> **本轮修的那一条**：`populate` 以前只在 `makeMenu()`（装状态项时一次）与 `menuWillOpen()`（每次要显示之前）被调用，而 `HistoryStore.refreshPredictions()` 是异步的 ⇒ 打开菜单那一刻填的是「正在整理推荐…」，结果落地后**没有人再填一次**。新增 `attachLiveRefresh(to:store:)`：订阅 `isRefreshingPredictions` 落回 false，`removeDuplicates()` 之后**换到下一拍主线程**再重填。判据两格（机制格 + 接线格），修前红在中间那一格、并把当时 9 项名单原样打出来；修后 `MENU_LIVE_REFRESH 修前项数=9 修后项数=13 修前挂着正在整理=true 修后挂着正在整理=false 修后有候选区=true store候选数=2`。
> 
> **最值钱的一格不是「有没有重填」而是「重填读的是哪一刻的值」**（M602）：`HistoryStore` 收尾在同一个 `MainActor.run` 里**先**置 `isRefreshingPredictions = false`、**后**才写候选（`HistoryStore.swift:252-260`），而 `@Published` 的 sink 是同步的 ⇒ 在 sink 里直接填会把「一直挂着正在整理」修成「当场翻成暂无推荐」，那是**另一种更坏的假话**。摘掉 `receive(on:)` 判据就红 ⇒ 这一格有刀。另三刀：M603 摘 `makeMenu` 的接线（防「零调用点的死尺」，R78 的 M416 同族）、M604 把「算完了才填」反成「开始算才填」、M605 让订阅不被属性持有（`AnyCancellable` 一丢就取消，且不会报错）。四刀全 CAUGHT、`RESTORE_CLEAN=yes`。`menuNeedsUpdate:` 判为**不选**并写明理由（它只在要显示之前触发，而这一格要修的是「已经开着、结果后到」；`menuWillOpen` 已经在管「下次打开是新的」，再加一条等于把同一个洞补两遍）。规矩进 **D-180**。
> 
> **边界按实记（U-369）**：`attachLiveRefresh` 由 `makeMenu()` 调用，而 `makeMenu()` 只在 macOS 12 分支里跑 ⇒ 本机（13+）产品运行时不会走这条线。两格判据证的是「机制通 + 接线在」，**「12 上真菜单会不会当场自己变」仍归批次 85.2** —— 与上一轮的 U-359 同形，分开记账、不互相代签。
> 
> **上一轮（R110）的账**：菜单栏 12 那颗图标以前是手画的 `NSBezierPath`、13+ 是 SF Symbol ⇒ 同一个入口两副身体；本轮起两边都引用 `MenuBarController.statusSymbolName`（D-179），帧基线 134 → **136**（两张 `statusitem-glyph-*`），155 拿到第一个答案（同一份构建两次捕获：115 组配对读数全等、最大绝对差 0），162 结案（runner 上详情列自己有 wrapper 且整列无墨 ⇒ 成因是「详情没被实例化」，不是「带子放错」），并新开 166（runner 的动效红在两跑之间换班）+ 仪器 `scripts/ci_red_stability.py`。**R110 的权威那一遍是 pass-2**：pass-1 因 U-365（抄电池时全局改名把 r109 那张表整张吃掉、而自检只数个数不查成员）不算数。
> 
> **验证（R111 pass-1 就是权威那一遍：11 步全跑、无跳步）**：构建 0 告警；`Executed 825 tests, 41 skipped, 0 failures`；在屏 11 例 **2** skip（比上一跑少一条：那条探针这一遍有对象了 ⇒ 覆盖变多，不是变少）；捕获 136 帧 `COMPARED=136 CHANGED=0`（13+ 路径 0 改动 ⇒ 像素中性由这一格证）；脚本 **230** 例 OK；变异 **20 张表合计 84 刀 caught=83**（r111 n=4 caught=4）；台账守卫 11 例 OK；`VIS_EXIT=0 ROUNDS=112 last=111`（本轮均分 **92**）；`CONTAIN_EXIT=0`；`SUMMARY_MISSING=0`；`CLOSEOUT_OK=1`。
> 
> **下一轮（R112）的入口**：① 读 R110 / R111 的 CI（R110 那跑顺带验两张新帧在 runner 上、以及 166 的换班是否再现）；② **150**：让臂 2 的详情在 runner 上保证有内容（162 已把成因钉成①）；③ **166** 的修法选一（把动效那一卷纳入「有名字的红」账，或 CI 上同版两跑取交集）；④ 155 扩第三个样本。
> 
> **仍然只有用户能做的**：批次 26.x–83.1、84.1（侧栏选中在活动/非活动两种时候分别是什么蓝）、**85.1**（12 上真菜单栏里那颗的基线与材质）、**85.2**（12 上开着菜单等刷新落地，会不会自己变）。
> 
> 