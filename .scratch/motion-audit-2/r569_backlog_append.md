
**645 追记（R569）：两道前提都被现读否掉了 —— 这一单的真实代价不是"改 14 支尺寸"，是"逐支重导按 750 写死的坐标"**
    ① **`≤750` 那道界不在主窗族的路径上。** 上一轮本单写"挡在前面的是 `UICaptureHarness.swift:25436` 那道 `XCTAssertLessThanOrEqual(fixture.size.width, 750, …)`"。R569 现读：那条断言在 **`testSettingsHelperTextIsNotClipped`** 里面，只对 `settings-shortcuts` 与 `settings-min` 两支夹具生效（现读行号 `:25580`，随本轮改动漂了 144 行）⇒ 把主窗族抬到 848 **不会**撞它。那句是抄上一轮的账，没现读 ⇒ 记进 D-569。
    ② **750 宽的主窗帧今天画的是产品做不出来的分栏。** 现读 `content-with-history-750x560-light.png` = `1500×1120px`（= 750×560pt @2x），沿 x 的列中位亮度最大跳变落在 **424.5pt**（跳变 54.0 亮 / 17.0 暗）⇒ 列锁 `423.5 + 1 + 423.5 = 848` 在 750 宽的窗里**不**按 R567 看图时写的"公式给 374.5"缩放，而是侧栏保持 423.5、详情被挤到 **325.5**。⇒ 上一轮那句"中缝目视落在正中"是**目视结论，被本轮的像素尺推翻**（同一张帧、同一个量，两种读数）。
    ③ 名单按现读重数（上一轮写"14 支"）：`NSSize(width: 750, height: 560)` 在 `UICaptureHarness.swift` 里 **11 处调用点**，其中 **10 处是基线帧族**（`content-with-history`、`content-empty`、`content-no-results`、`main-sidebar-title-hover`、`content-with-notice`、`content-with-two-notices`、`content-paused-idle`、`content-paused`、`content-with-dropped-unreadable-notice`、`content-with-copy-failure-notice`）× 明暗 = **20 张**；第 11 处 `content-paused-defaults-<bool>` 只落临时目录、不进基线。
    ④ **每支帧背后都有按 750 写死的东西**（这才是真代价，现读至少三处）：`:11712` 一带 `let scale = Double(rep.pixelsWide) / 750.0` + 固定 pt 矩形（`EMPTY_STATE_HINT` 那条 AA 判据）、`:11737` 的字面帧名 `"content-empty-750x560-\(tag).png"`、`:6861` 同一除数 + 一组 pt 矩形与 `scale²` 推出来的像素地板。**改尺寸不改这些 ⇒ 判据量的就不再是它名字里那张帧**（R98 那一课的形状）。
    本轮为什么一支都没抬：CI 上挂着 15 朵红（见 648），在半坏的 CI 上重录基线 = 把坏读数洗成真值（R565 那条）。
    退场（R570 的执行式）：逐支 = 改尺寸 + 重导它自己那几处 750 坐标 + 同笔 `frame_baseline.py update` + 逐张看图（先确认看的是整帧还是自己切的框）；先抬 `content-with-history`（它背后那处 `:6861` 的除数与矩形必须一起改），再抬 `content-empty`（`:11712`/`:11737` 两处），其余 8 族随同一口径批量搬并给改名名单。

**646 追记（R569）：那条通道不是"不能"，是"依倍率而定"—— 比原判断更麻烦**
    本单原文（R568 开）：离屏 `cacheDisplay` 把透明半区涂成不透明黑 ⇒ D12 那句"透明区 alpha 归零"不能由 356 张帧作证。依据是**本机 2x** 那一次读数。R569 的 runner 首跑给了相反答案：`TRANSPARENCY_CHANNEL 通道=离屏 … 倍率=1.00x … 透明半区=(r0,g0,b0,a0) 分得出=1`，而本机 2x 仍是 `(r0,g0,b0,a255) 分得出=0`。⇒ 同一套判据、同一个属性、两台相反。
    后果分三条：① **第③段的 alpha 证人不是"没有"，是"跨机不一致"** —— runner 那一档其实看得见 alpha=0，本机 2x 看不见；② 判据已按 R555/R568 那条方法改造成**登记表**（`registeredOffscreenVerdict(scale:)` 只有 2x/1x 两个观测值，其余倍率回 nil ⇒ 具名不判并打真数），所以任一台哪天翻了会红，而不是悄悄换答案；③ 本单的阻塞性从"绝对阻塞"降为"**必须先定按哪一档口径验收**"，而那个口径决定仍归用户/第③段（与 644 同一类：不是我能用一次改数替产品定的）。
    退场不变：第③段落地时按选中的那条出路给证人 + 刀；新增一条：若两台将来对齐（同一答案），登记表里那一档必须删掉，不许留着当"以防万一"。

**648. runner 上四支 `detail-*` 旧判据"后一批整体挪 54pt 并丢墨"，本机两种排法都不复现 ⇒ 由 `CAPTURE_FOREIGN_WINDOW` 在下一跑分岔**（R569 现读并新开）
    现象（`41751994049↔0a9113c`，R568 那棵树）：`testActionableInkStaysAboveTheLegibilityFloor`、`testCaptionTextStaysOnTheSecondaryTier`、`testDetailAreaHasASingleLeftAxis`、`testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed` 三跑前全绿、这跑红；改动前 `Executed 1411 … 4 failures` → 本跑 `1421 … 15 failures`。
    同跑内两批读数（这是关键形状）：STEP[5] `01:14:55` 那批 `DETAIL_AXIS light/dark 判了 5 块，spread=1.0pt`、`SOURCE_APP_BADGE … 有来源彩色=59 有来源墨=110/139`；STEP[15] `01:32:54` 那批 `spread=57.0/54.0`、`彩色=0`、`有来源墨=22/10`。`TRANSPARENCY_*` 打在 `01:31:35`（早 79 秒）。
    本机实验（都不复现，这是账不是安慰）：并行同进程 `TransparencyForensicsTests` + 那四格 ⇒ `Executed 12 tests, with 3 tests skipped and 0 failures`；`--no-parallel` 串行（transparency 先跑）⇒ `Executed 10 tests … 0 failures`，读数正常（`spread=0.5pt`、`彩色=124`）。
    两条解释且修法相反：**(甲)** 有测试在捕获期间留着真实 app 窗口，在无头 runner 上挤坏了后续离屏捕获（先例 R525 = 某格没还原 `WindowChromeMetrics` 导致 runner 详情帧红；量级也对得上 ~52pt，但**先例不是证据**）；**(乙)** 与本轮无关的 runner 负载/采样（同跑内前一批正常、后一批坏）。
    本轮落的分岔证人：`render()`（所有拍帧路的必经点）在捕获那一刻数屏上的 app 内容窗，非零才打 —— `CAPTURE_FOREIGN_WINDOW <夹具名> 屏上 app 内容窗=N 尺寸=[…] 外观=…`。⇒ 下一跑：坏的那批这一行**非零** ⇒ (甲)，修窗的生命周期（把建窗的格子改成不外泄，或让捕获不共享同一渲染面）；这一行**为零而读数仍坏** ⇒ (乙)，按采样族登记并给出现率（与 354/622 同一套），**不许**为消红动地板。
    退场：两条里有一条被读数选中并落地（修 + 刀，或登记 + 出现率）。

**639 追记（R569）：第七次逐字同值**
    现读 `41740747168` 与 `41751994049` 两跑：`HINT_CONTRAST light 底=236 字芯=(118,118,118) 对比=3.84:1 字芯像素=40 偏差像素=696 地板=4.5 倍率=1.0x`、`dark 底=50 字芯=(163,163,163) 对比=5.08:1 … 712 …` ⇒ 与前面六次逐字相同；本轮产品 0 文件、只动判据 ⇒ 没有理由挪动它。名义 vs 渲染两口径仍**归用户**，4.5 一字未动。

**640 追记五（R569）：同日第七次读数 —— 又是 0，但这一格的含义与 R568 那次不同**
    现读：`/tmp/r569/frames` 对 working 基线 ⇒ **@@FRAMES@@**。⚠ 与 R568 那次（产品改了 3 个文件而画面逐字节没变）不同，本轮**产品与夹具都没改** ⇒ 这个 0 是"什么都没动所以不该变"的 0，**不能**当漂移的反证，也不能当"捕获通道稳定"的证据（同一棵树在 runner 上正漂着 15 朵，见 648）。历史六个数：138/138/135/105/0/0 ⇒ 本环是第七个。

**643 追记（R569）：第十、第十一个数 —— 2.50× 与 1.37×，`线=1.0×` 未动**
    现读两跑逐字：`41740747168↔a15d1ed` ⇒ `MOTION_BAND_SAVING 带中位=9.60ms 整窗中位=24.02ms 省=2.50×`；`41751994049↔0a9113c` ⇒ `带中位=9.27ms 整窗中位=12.74ms 省=1.37×` ⇒ 在册十一个数 2.18/1.55/0.98/1.26/1.55/1.86/1.23/2.22/1.26/**2.50**/**1.37**。带臂 9.60 / 9.27 落在既有 6.32–11.39 区间内；**整窗那一臂在 24.02 与 12.74 之间摆**（同一台机器两跑差近一倍）⇒ "省"这个比值的主要变动来自整窗臂而不是带臂，这句话本轮只报数不立判据（643 仍只记现读）。
