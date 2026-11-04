# R569 读数笔记（自存，随台账笔提交）

## ⓪ 三跑（盘上：`/tmp/r569-ci-b.log`=41751994049↔0a9113c、`/tmp/r569-ci-g.log`=41740747168↔a15d1ed）
- `41751994049 ↔ 0a9113c` completed/failure，失败步骤三朵：STEP[15]/[17]/[19]；步骤名可解析。逐步结论 success：STEP[9]、[11]、[16]、**[18]**。
- `41740747168 ↔ a15d1ed` completed/failure，失败步骤四朵：STEP[15]/[17]/**[18]**/[19]；**日志 15259/15259 行全是 `UNKNOWN STEP`** ⇒ 按步骤名切正文不灵，改全文 grep + emit 通道。
- `41752950275 ↔ 1c438ab` in_progress ⇒ 复核未到。
- 上一轮两朵红的签收：`FOLD_GEOMETRY_COLUMNS 侧栏=424.00 详情(算)=423.00 分隔条=1.00 分栏宽=848.00 缝中心=424.50 倍率=1.0x 半格可落=0 列差界=1.000 缝心界=0.500`；`FOLD_SEAM_PIXEL light/dark … 跳变=0.0 左墨=-1 右墨=0` + `FOLD_SEAM_PIXEL_NOT_RUN=runner-1x-frame-blank light/dark`；`CAPTURE_GATE_RESULT=fail 有 1 个用例红了`（只剩 639）。
- STEP[15]：`Executed 1421 tests, with 89 tests skipped and 15 failures in 523.462s`（改动前 `1411/86/4`）。红的 6 个用例：
  1. `TransparencyForensicsTests testOffscreenChannelMatchesTheRegisteredAlphaAnswerForItsScale`（旧名 `…FlattensTransparentToOpaqueBlack` 在 `a15d1ed` 那跑红的就是它）—— `TRANSPARENCY_CHANNEL 通道=离屏 位图=200x120 hasAlpha=1 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a0) 分得出=1`
  2. `testActionableInkStaysAboveTheLegibilityFloor`（`0.0255 < 0.03`、`2.70 < 3.0`，detail-3-files）
  3. `testCaptionTextStaysOnTheSecondaryTier`（`0.0 < 0.03`、`1.01 < 2.60`、`1.05 < 3.85`，detail-0-text）
  4. `testDetailAreaHasASingleLeftAxis`（`54.0 > 2.0`、`57.0 > 2.0`；`头部 meta=21.0 vs 正文=74/77`）
  5. `testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed`（`彩色=0`，light+dark）
  6. `testQuickPickKeyboardHintClearsTheContrastFloor`（639）
- 同跑两批（时间戳）：STEP[5] `01:14:55` `DETAIL_AXIS … spread=1.0pt`、`SOURCE_APP_BADGE … 彩色=59 墨=110/139`；STEP[15] `01:32:54` `spread=57.0/54.0`、`彩色=0 墨=22/10`；`TRANSPARENCY_STATE/HITTEST` 在 `01:31:35`；`FOLD_GEOMETRY_COLUMNS` 在 `01:29:53`。
- STEP[9]（a15d1ed 那跑）`SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=720 内层skip汇总=4 解析=3 名单外=无 名册未跳=无` ⇒ 第五次绿；**那张名册只管 python 电池，swift 的 `XCTSkip` 不在里面**（上一轮 ⓪ 的预判错）。
- STEP[18]（仅 a15d1ed 那跑红）：`FAILED testFrameIntervalsUnderStateChanges：最差帧 190.6ms 超过锚点 120ms，且超锚点的帧有 2 颗（容差 1 颗）` + `PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14 runner可跑=8 runner不可跑=6 本次下结论=7 本次跑过=8 红=1` + `PROBE_QUEUED 6/14` + `PROBE_PULSE_OPEN 1 条有心跳没闭合`。
- STEP[19] 两跑各 1 朵：`红的用例=testEmptyStateStillFadesWhenMotionIsReduced 汇总行报红=1`、`MOTION_FLOOR_BAD_REASON empty-state … witness-snaps-here`、`summary … empty-state=1 … settings-reset-fade=2/4`；crossfade 那朵这轮没露面。
- 639：`light … 3.84:1 … 696 … 1.0x` / `dark … 5.08:1 … 712` 两跑逐字（第七次）。
- 643：`带中位=9.60ms 整窗中位=24.02ms 省=2.50×`（a15d1ed）、`带中位=9.27ms 整窗中位=12.74ms 省=1.37×`（0a9113c）。

## ② 本轮现读（本机）
- 离屏登记表本机那档：`TRANSPARENCY_CHANNEL 通道=离屏 位图=400x240 倍率=2.00x … 分得出=0 实测=涂成不透明黑 登记=涂成不透明黑`
- 扫描：`CHROME_METRIC_GUARD 文件=158 开真窗=5 违规=1 名单=[WindowManagerTests.swift] 豁免=[WindowManagerTests.swift] 未豁免违规=0`
- 合成目录正对照：`CHROME_METRIC_GUARD_SELFTEST 合成文件=3 开真窗=2 违规=[AOpenerWithoutRestore.swift]`
- 材质（含负臂）：`TRANSPARENCY_MATERIAL … 均值差=0.0000 品红漏出=0`、`TRANSPARENCY_MATERIAL_NEG 撤掉底衬 均值=0.6637 字墨=8145 品红漏出=318 均值移动=0.2702 || 放回底衬 均值=0.9339 品红漏出=0`
- 阴影：`正对照 左=右=0.0649 倍率=2.00x`、`半片 左=0.0631 右=0.0017 判=套形状`
- 命中：`TRANSPARENCY_HITTEST 探针=3 空区命中=底衬0/容器3/内容0`
- 645 的现读更正：`≤750` 那道界在 `testSettingsHelperTextIsNotClipped`（现读 `:25580`），只判 `settings-shortcuts`/`settings-min`；`content-with-history-750x560-light.png` = 1500×1120px，**缝列 424.5pt**（跳变 54.0 亮 / 17.0 暗）⇒ 侧栏 423.5、详情 325.5；750×560 调用点 11 处（10 处是基线族 = 20 张帧）；按 750 写死的坐标至少 `:11712`（`pixelsWide / 750.0`）、`:11737`（字面帧名）、`:6861`（同除数 + pt 矩形）。
- 本机不复现实验：并行 `Executed 12 tests, with 3 tests skipped and 0 failures`；`--no-parallel` 串行 `Executed 10 tests … 0 failures`（`DETAIL_AXIS … spread=0.5pt`、`彩色=124`）。

## 验证链
- build：`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`
- 刀：M1486/M1487/M1488 全 CAUGHT、RESTORE_CLEAN=yes（`/var/folders/…/ba7…` 与终端输出）
- 判据卷 / 帧 / 全量 / 预检 / 电池：待跑（`/tmp/r569/capture.log`、`compare.log`、`full.log`、`needles.log`、`hidden.log`、`/tmp/r569-battery*.log`）
- 换装：**不跑** ⇒ `SKIP_INSTALL=no-product-change`
