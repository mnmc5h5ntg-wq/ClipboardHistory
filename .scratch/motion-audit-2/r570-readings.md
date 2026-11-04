# R570 读数笔记（第 569 轮 / Round 567 · 2026-11-04）

## ⓪ 复核（本轮开工时取过一次，收口前再取一次）

- `41762634884 ↔ e92a0b0`（第一跑含 R569 修复的树）：本轮两次取号都 `status=in_progress`、`conclusion` 空、
  逐步结论全空 ⇒ **分岔证人未到数**。按 `read-own-ci-run`：不轮询、不读成绿也不读成红。
- `41763602773 ↔ d5edc16`（本轮 ⓪ 开工笔）：取号时 in_progress ⇒ 未读。
- ⇒ 本轮 ② 的全部结论都**不依赖**那一跑：换成 ①每条全局在拍帧那一刻的直接读数（`CAPTURE_CHROME_INSET`）
  与 ②本机就能做的因果实验（`INSET_CAUSAL`）+ ③两条真窗发布轨迹（`CHROME_PUBLISH_TRACE`）。

## ① 门与身份（现读）

- `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`
- 轮次身份：`R570 = 第 569 轮 / Round 567`
- 刀高水位现读 **M1488**（`mutate_r569` 表尾）⇒ 本轮 M1489–M1494
- `PRODUCT_STREAK ledger_round=568 streak=1`（只抄门）

## ② 本机因果实验（判据卷 `UICaptureHarness.swift`）

兜底值 `detailContentTopInsetFallback = 35`。每一档的发布值都由产品自己的公式算出来
（`noteTrafficLights(titlebarHeight:buttonHeight:)`），实测与公式预测逐档对账
（`XCTAssertEqual(published, rung.inset, accuracy:)`）。

```
INSET_CAUSAL 档=拿不到容器     容器高=0  按钮高=14 发布=10.0 兜底=35.0 差=-25.0 带墨=0.0% 列墨=16144 形状=runnerShapeReproduced
INSET_CAUSAL 档=半高           容器高=24 按钮高=14 发布=20.0 兜底=35.0 差=-15.0 带墨=8.3% 列墨=16144 形状=driftedButStillDrawn
INSET_CAUSAL 档=无工具栏实测档 容器高=32 按钮高=14 发布=28.0 兜底=35.0 差=-7.0  带墨=4.0% 列墨=16144 形状=driftedButStillDrawn
INSET_CAUSAL 档=带工具栏下沿   容器高=39 按钮高=14 发布=35.0 兜底=35.0 差=+0.0 带墨=10.6% 列墨=16144 形状=baselineDrawn
INSET_CAUSAL 档=灯更高-上平台  容器高=45 按钮高=20 发布=41.0 兜底=35.0 差=+6.0 带墨=5.4% 列墨=16144 形状=driftedButStillDrawn
INSET_CAUSAL_MIN_DELTA 最小可坏位移=-25.0 发布=10.0 容器高=0 按钮高=14 带墨=0.0%
```

- 「详情头部 meta」那条带子的墨地板是 `probeInkFraction = 3%`（一字未动）。
- **重现runner那批形状需要 inset ≈ 10（Δ=−25）**，而 10 那一档的输入是「容器高 ≤ 按钮高」= 物理上不成立的实测。
- 真窗实测那一档（28 / Δ=−7）本机只把带墨从 10.6% 压到 **4.0%** ⇒ 仍在地板上 ⇒ **量级不够**。
- 列墨 16144 px 在五个档位逐字相同 ⇒ 那一列一直画着东西，空掉的只有那条带子（这正是"整列被顶走"而不是"这台机器画不出"）。

## ③ 两条真窗发布轨迹（`WindowChromeLayoutTests.swift`）

```
CHROME_PUBLISH_TRACE 哨兵=10.0 发布次数=2 序列=35.0 最小=35.0 可信下界=28.0        （手搭：带工具栏 52/14）
CHROME_PUBLISH_TRACE 路=产品主窗 容器高=32.0 序列=28.0 最小=28.0 可信下界=28.0     （产品入口 WindowManager.showMainWindow()）
```

- 产品自己的建窗路**发布 28.0**（容器高实测 32.0），从没写过 10。
- 于是"某个真窗泄漏了它的实测值"这件事最多只能造出 Δ=−7，而 runner 那批要 Δ=−25 才解释得通。
- 顺带量到一件事：**兜底值 35 ≠ 真窗实测 28** ⇒ 356 张离屏帧画的详情头部比真品低 7pt，
  而真窗在配置那一刻会从 35 跳到 28（这一跳今天没有帧可证 ⇒ 具名未读到）。⇒ **新开 649**。

## ④ 刀（M1489–M1494，六把全 CAUGHT、RESTORE_CLEAN 全 yes）

| 刀 | 打在 | 坏法 | 结果 |
|---|---|---|---|
| M1489 | 尺（`decideNote`） | 读数在非首拍永远沉默 | CAUGHT（真值表两行同红） |
| M1490 | 尺（`insetShape`） | 把「漂了且带子空」说成「还有墨」 | CAUGHT（真值表 + 因果实验同时红 ⇒ 这一把钉的是"重现永远判不出来"） |
| M1491 | 尺（注入驱动） | 注入根本没走产品的发布函数 | CAUGHT（每一档都停在 35 ⇒ 正对照与对账两格红） |
| M1492 | 尺（必经点计数器） | `calls` 不涨 ⇒ 通道没挂在拍帧路上 | CAUGHT |
| M1493 | 尺（轨迹记录器） | 什么都不记 ⇒ 「没发布」与「没记到」混成一件 | CAUGHT（两格轨迹都红） |
| M1494 | **产品**（`noteTrafficLights` 夹到 20） | 发布一个低于可信下界的值 | CAUGHT（轨迹两格都红 ⇒ 钉住"这一格真的在看产品发什么"） |

## ⑤ 那 15 朵红的去向（逐名，三态分开）

runner 主线两跑逐字 `Executed 1421 tests, with 89 tests skipped and 15 failures`
（`41751994049↔0a9113c`、`41756435842↔1968490`），六支用例：

| 用例 | 状态 | 证人 |
|---|---|---|
| `TransparencyForensicsTests/testOffscreenChannelFlattensTransparentToOpaqueBlack` | **修好待签**（R569 按倍率分口径登记） | 只有 `41762634884` 那一跑能签，本轮未到数 ⇒ 不许写"绿了" |
| `UICaptureTests/testCaptionTextStaysOnTheSecondaryTier` | **仍红**（本机绿、runner 未签） | 本轮量到它需要的量级：inset≈10 才造得出 0.0% |
| `UICaptureTests/testDetailAreaHasASingleLeftAxis` | **仍红**（同上） | 同上 |
| `UICaptureTests/testActionableInkStaysAboveTheLegibilityFloor` | **仍红**（同上） | 同上 |
| `UICaptureTests/testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed` | **仍红**（同上） | 彩色/墨那两支症状**本轮没在 Δ=−25 下复现** ⇒ 具名未读到 |
| `UICaptureTests/testQuickPickKeyboardHintClearsTheContrastFloor`（639） | **仍红、归用户口径** | 名义 vs 渲染，本轮一字未动登记 |

- 本轮**没有**用登记表抹掉任何一朵红：`CAPTURE_CHROME_INSET`/`INSET_CAUSAL` 都是新加的**读数**，
  离屏 alpha 那张登记表的两个值（2x/1x）一个字没改。
- 15 这个数是断言条数、6 是用例数，两个口径不混说（`read-own-ci-run` 第 5 步）。

## ⑥ 验证链现读（收口前）

- 判据卷：`Executed 227 tests, with 4 tests skipped and 0 failures (947.336s)`（R569 是 224/4/0 @782.971s ⇒ +3 格 = 本轮新加的三格判据）
- 新通道在判据卷里的行数：`CAPTURE_CHROME_INSET` **1 行**，逐字
  `CAPTURE_CHROME_INSET settings-about light 兜底=35.000 值=35.000 判=与兜底一致 上一次=首拍`
  ⇒ "干净的一跑只 1 行"这句话现在是读数不是设计意图；`CAPTURE_FOREIGN_WINDOW` **0 行**（本机无外来窗）。
- 帧：`FRAME_BASELINE_AGAINST=working COMPARED=356 CHANGED=0 MISSING=0 ADDED=0` ⇒ **不 update 基线**（本轮产品与夹具都不动像素）。
- 那条扫描的读数随本轮改动而变：`CHROME_METRIC_GUARD 文件=158 开真窗=6 违规=1 名单=[WindowManagerTests.swift] 豁免=[WindowManagerTests.swift] 未豁免违规=0`
  ⇒ **开真窗从 5 抬到 6**，多出来的那一个就是本轮新加的产品主窗轨迹那一格（它自己带还原）；断言是 `>= 4` 与"未豁免违规 == 0"，两格都绿。
- 看图：3 支整帧（`detail-0-text-720x520-light/dark` 1440×1040px、`content-with-history-750x560-light` 1500×1120px）
  + 一条像素复核：亮档头部墨带 37–46pt、暗档 36–47pt ⇒ 与探针矩形 `CGRect(x: 40, y: 36, width: 680, height: 12)` 对得上
  ⇒ 这条带子今天贴的是**兜底 35 那一档**的字（真窗发 28 ⇒ 帧与真品差 7pt，写进 649）。

## ⑦ 收口前复核到数：`41762634884 ↔ e92a0b0`（第一跑含 R569 修复）已 completed / failure ⇒ ⓪ 七格到数

失败步骤三朵（`ci_read.py steps` 原样）：STEP[15] Swift tests (executed-count gate)、STEP[17] Capture gate、STEP[19] Motion coverage floor。
逐步结论（success 的也读）：STEP[4] Build=success、STEP[5] Offscreen frame capture=success、STEP[9] Release script tests=success、
STEP[11] Frame baseline vs working manifest=success、STEP[16] Motion gate=success、STEP[18] On-screen probe coverage floor=success。

- **(a①) 离屏那格被 runner 签字：不再红。** 逐字 `TRANSPARENCY_CHANNEL 通道=离屏 位图=200x120 倍率=1.00x hasAlpha=1 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a0) 分得出=1 实测=保留 alpha 登记=保留 alpha`
  ⇒ R569 的按倍率登记表在 1x 那一档与实测一致 ⇒ **修好（已签）**，不再是"待签"。
- **(a②) `CAPTURE_FOREIGN_WINDOW` 在这份日志里出现 0 次** ⇒ 捕获期间屏上没有 app 内容窗 ⇒ **(甲) 的"有真实窗挤坏捕获"这一形态被否**（硬规矩：只凭那一跑的行数下判断）。
- **(a③) 全量卷 `Executed 1424 tests, with 89 tests skipped and 14 failures`**（上一跑 1421/89/15 ⇒ 少的那一朵正是离屏那格）。仍红的用例逐名：
  `testCaptionTextStaysOnTheSecondaryTier`、`testActionableInkStaysAboveTheLegibilityFloor`、`testDetailAreaHasASingleLeftAxis`、
  `testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed`、`testQuickPickKeyboardHintClearsTheContrastFloor`（639）、
  加上动效卷两支 `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`、`testEmptyStateStillFadesWhenMotionIsReduced`。
- **本轮最要紧的一条结构证据：同一棵树、同一台机器，`CAPTURE_GATE_RESULT=fail 有 1 个用例红了`（纯捕获卷）而全量卷 14 failures。**
  ⇒ 那四支 `detail-*` 只在**全量卷的测试集合/顺序**里红，纯捕获卷绿 ⇒ 这是"按测试集合而定"的**确定性**形状，不是随机采样 ⇒ **(乙)「负载/采样」也被削弱**。
  ⇒ 剩下的是 **(丙)**：全量卷里先跑的某格写了一个共享状态，而它**不是窗**（0 行）、**也不是那条全局的量级**（本轮因果实验：真窗发 28 ⇒ 带墨 4.0%，造不出 0.0%；R569 的还原已落地而这四支照红）。
- **runner 那批坏读数的形状里有一条本轮因果实验解释不了的**：`testDetailAreaHasASingleLeftAxis` 逐字
  `detail-0-text/头部 meta=21.0 detail-0-text/正文（原文）=77.0 detail-loading/骨架条带＋那一句=21.0 detail-markdown-rendered/正文（渲染）=20.0 detail-markdown-source/正文（退回原文）=20.0（light）`
  与 dark 的 `74.0` ⇒ **正文那一块的左轴单独跑到 77/74，而同一张帧上别的块仍在 20/21** ⇒ 这是**横向**差异，垂直位移（inset）造不出它 ⇒ 我本轮那句"inset≈10 就同形"只覆盖 `ink=0.0%` 那一支症状，**不覆盖这一支**，账上必须这么写。
- (b) STEP[19]：`MOTION_FLOOR_FACTS judged=4/5 executed=79 not-run=empty-state … 红的用例=testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind,testEmptyStateStillFadesWhenMotionIsReduced 汇总行报红=2 机器=github-runner`
  ⇒ **executed=79 > 0**（连续两跑 `executed=0` 之后第一次有读数）⇒ 这一跑的"绿/红"都是真读数，不再需要写"未读到"。
  crossfade 那朵的红话是**判据自己要求升级**：`新口径 开=3 关=2 / 旧口径 开=3 关=2 线=0.0127 安全=true` ⇒ "这把尺看得见这条交叉淡 ⇒ 把本条改成硬判据"（629/431 那一族，不是产品回归，也不是消红）。
- (c) STEP[9] 第六次绿：`SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=720 内层skip汇总=4 解析=3 名单外=无 名册未跳=无`。
- (d) 全量 skipped 现读 **89**（与上一跑同数；只记现读，不动门）。
- (e) 639 **第八次逐字同值**：`HINT_CONTRAST light 底=236 字芯=(118,118,118) 对比=3.84:1 字芯像素=40 偏差像素=696 地板=4.5 倍率=1.0x`、`dark 底=50 字芯=(163,163,163) 对比=5.08:1 … 712 …` ⇒ 口径仍归用户，4.5 一字未动。
- (f) 643 **第十二个数**：`MOTION_BAND_SAVING 带中位=6.37ms 整窗中位=11.49ms 省=1.81× 线=1.0×` ⇒ 在册十二个数 2.18/1.55/0.98/1.26/1.55/1.86/1.23/2.22/1.26/2.50/1.37/**1.81**。
- (g) STEP[11] = **success**，working manifest 那一格 `FRAME_BASELINE_MISSING=0`。⚠ 同一份日志里另有 `FRAME_BASELINE_MISSING=6`，那是 **"vs previous release v1.4.8"** 那一步（report-only）的数 = v1.4.8 之后新增的 6 张帧（`weights-*` 等），**不是名册缺帧**。两个 MISSING 不同源，读错步骤就会把 report-only 当闸门。
